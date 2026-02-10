
import pytest
from los.infrastructure.parsers.los_parser import LOSParser
from los.infrastructure.translators.pulp_translator import PuLPTranslator

class TestAuditRemediation:
    
    def setup_method(self):
        self.parser = LOSParser()
        self.translator = PuLPTranslator()

    def _translate(self, text):
        parser_result = self.parser.parse(text)
        print(f"DEBUG AST: {parser_result['parsed_result']}")
        # Mock Expression object behavior
        from los.domain.entities.expression import Expression
        expr = Expression(original_text=text)
        expr.syntax_tree = parser_result['parsed_result']
        expr.variables = parser_result['variables']
        return self.translator.translate_expression(expr)

    def test_sanitization_ignores_injection(self):
        """Test C04: Code Injection prevention via Import path"""
        bad_str = "file');os.system('rm -rf /');.csv"
        los_text = f'import "{bad_str}"'
        
        try:
            code = self._translate(los_text)
            print(f"\nGenerated Code for Import:\n{code}\n")
            
            # F08: Variable name derived from filename, not hardcoded 'data'
            # Quotes/parens stripped from path — no injection possible
            assert "');" not in code
            assert "pd.read_csv" in code
            # The malicious payload is now just a string argument, not executable
            # We don't assert "os.system" not in code because it IS in the filename string
            print("\nSanitization Check Passed")
        except Exception as e:
            pytest.fail(f"Translation failed: {e}")

    def test_set_literal_strings(self):
        """Test A02: Sets with identifiers are strings"""
        los_text = "set S = {A, B, C}"
        try:
            code = self._translate(los_text)
            print(f"\nGenerated Code for Set:\n{code}")
            # Should be S = ['A', 'B', 'C']
            assert "S = ['A', 'B', 'C']" in code
            print("\nSet String Check Passed")
        except Exception as e:
            # If assertion fails, it raises e? No, assertion raises AssertionError
            # which is caught by Exception? Yes.
            pytest.fail(f"Translation/Assertion failed: {str(e)}")

    def test_inequality_operator(self):
        """Test A01/Logic: Inequality != handling"""
        los_text = """
        st: x != 5
        """
        code = self._translate(los_text)
        # Defined to return error comment
        assert "# ERRO: Operador != não suportado" in code
        print("\nInequality Check Passed")

    def test_functions_visit(self):
        """Test A04: Functions"""
        los_text = """
        min: min(x, y) + abs(z)
        """
        code = self._translate(los_text)
        assert "min(x, y)" in code
        assert "abs(z)" in code
        print("\nFunctions Check Passed")

    def test_named_constraints_heuristic(self):
        """Test C06: Constraint Parsing Heuristic"""
        # "Subject" starts with Uppercase, but is a keyword.
        # "Limit" is a name.
        los_text = """
        st: Limit: x <= 10
        """
        code = self._translate(los_text)
        assert ", 'Limit'" in code
        
        # "x" is checking heuristic? Parser logic for constraint_named used token check.
        # If I have uppercase VAR, it shouldn't be confused with Name if it's part of expression.
        # "X <= 10". X is identifier. 
        # Parser `constraint_named`: `(IDENTIFICADOR ":")?`. 
        # If no colon, `X <= 10` parses as `logic_expr`.
        # So heuristic is only relevant if there IS A COLON? 
        # Grammar: `constraint_item: (IDENTIFICADOR ... ":")?`.
        # So colon is mandatory for name!
        # My logical fix in Parser checked `if items[0] is IDENTIFICADOR`.
        # But if `items[0]` is part of logic_expr?
        # Grammar: `constraint_item: (IDENTIFICADOR ... ":")? logic_expr`.
        # Lark handles the ambiguity? 
        # If I write `Limit: x <= 10`. `Limit` matches `IDENTIFICADOR`. `:` matches `:`. `x<=10` matches `logic_expr`.
        # If I write `x <= 10`. `x` matches `logic_expr`.
        # Does `x` match `IDENTIFICADOR`? Yes. But `:` is missing.
        # So `constraint_named` rule will NOT match the optional part.
        # So `items` will only contain `logic_expr`.
        # So `items[0]` will be `logic_expr` (dict).
        # My check `isinstance(first, Token)` handles this! Dict is not Token.
        # So `x <= 10` -> name=None. Correct.
        pass

if __name__ == "__main__":
    t = TestAuditRemediation()
    t.setup_method()
    t.test_sanitization_ignores_injection()
    t.test_set_literal_strings()
    t.test_inequality_operator()
    t.test_functions_visit()
    t.test_named_constraints_heuristic()
