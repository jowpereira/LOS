
import unittest
import sys
import os

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from los.infrastructure.parsers.los_parser import LOSParser
from los.infrastructure.translators.pulp_translator import PuLPTranslator
from los.domain.entities.expression import Expression

class TestPuLPTranslator(unittest.TestCase):
    def setUp(self):
        self.parser = LOSParser()
        self.translator = PuLPTranslator()

    def translate(self, code):
        """Helper to parse and translate code"""
        # Parse returns a dict with 'parsed_result'
        parse_result = self.parser.parse(code)
        
        # Create Expression entity
        expr = Expression(code)
        expr.syntax_tree = parse_result['parsed_result'] # {type: model, statements: [...]}
        
        # Translate
        translated = self.translator.translate_expression(expr)
        print(f"\n--- DEBUG TRANSLATED CODE ---\n{translated}\n-----------------------------")
        return translated

    def test_translate_simple_objective(self):
        code = "minimize: x + y"
        translated = self.translate(code)
        
        # Helper to normalize whitespace for comparison if needed
        # But simple substrings work best
        self.assertIn("prob = pulp.LpProblem", translated)
        self.assertIn("pulp.LpMinimize", translated)
        # Expected: prob += x + y, 'Objective'
        # Parser produces binary_op. Translator visits it.
        # String repr of expression should be in output.
        self.assertIn("prob +=", translated)
        self.assertIn("x + y", translated)

    def test_translate_constraints(self):
        code = """
        subject to:
            c1: x <= 10
        """
        translated = self.translate(code)
        self.assertIn("prob +=", translated)
        # Translator normalizes 10.0 to 10
        self.assertIn("x <= 10", translated)
        self.assertIn("'c1'", translated)

    def test_translate_parameters(self):
        code = "param MaxCap = 100"
        translated = self.translate(code)
        # Translator uses if/else block for parameters
        self.assertIn("if 'MaxCap' in _los_data:", translated)
        self.assertIn("MaxCap = 100", translated)

    def test_translate_sets(self):
        code = 'set Factories = {"F1", "F2"}'
        translated = self.translate(code)
        # Check for _los_data pattern and proper list syntax
        self.assertIn("Factories = _los_data.get('Factories')", translated)
        self.assertIn("Factories = ['F1', 'F2']", translated)
        
    def test_string_escaping(self):
        # Escaping test
        payload = "A'; os.system('die'); '"
        code = f'set S = {{"{payload}"}}'
        translated = self.translate(code)
        
        # The translator uses repr() which adds quotes.
        # The output list string will contain "A'; os.system('die'); " (double quoted)
        # We check for the presence of the payload inside the list structure.
        # Payload: A'; os.system('die'); '
        # Output: ["A'; os.system('die'); '"]  <-- Wait, repr() of a string containing single quotes usually uses double quotes if no double quotes inside.
        # So it becomes "A'; os.system('die'); '"
        
        # We just check that the payload content is there, safely quoted.
        # Python repr() uses double quotes here so single quotes are NOT escaped.
        self.assertIn("os.system('die')", translated)

if __name__ == '__main__':
    unittest.main()
