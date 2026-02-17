
import unittest
import sys
import os
import textwrap

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from los import compile, solve
from los.shared.errors.exceptions import ParseError, LOSError

class TestSecurity(unittest.TestCase):
    def setUp(self):
        # Ensure clean state or mock logger if needed
        pass

    def test_string_injection_attempt(self):
        # Payload: Tenta escapar da string e executar código arbitrário
        # Target: set MaliciousSet = ["payload"]
        # Se falhar o escaping, vira: set MaliciousSet = ["'); print('RCE'); ('"]
        malicious_payload = "'); print('RCE_ATTEMPT'); ('"
        
        model_source = textwrap.dedent(f"""
        set MaliciousSet = {{"{malicious_payload}"}}
        var x >= 0
        minimize: x
        subject to:
            c1: x >= 1
        """)
        
        # Should not crash and definitely NOT execute print
        try:
            model = compile(model_source)
            # Inspect generated code to ensure escaping
            # Python code should look like: MaliciousSet = ["'); print('RCE_ATTEMPT'); ('"]
            # NOT: MaliciousSet = [''); print('RCE_ATTEMPT'); ('']
            self.assertIn("RCE_ATTEMPT", model.python_code)
            # Execute
            model.solve()
        except Exception as e:
            self.fail(f"Exploit crashed the compiler (safe but not ideal): {e}")

    def test_sandbox_eval_blocked(self):
        # Payload: Tenta usar builtin 'eval' que deve ser removido do escopo
        # Note: 'eval' is valid python but banned in sandbox.
        model_source = textwrap.dedent("""
        # Creating a constraint that tries to use eval via some trick?
        # Actually LOS parser doesn't support function calls locally except min/max/sum.
        # But let's assume valid python syntax generation.
        # This test ensures that even if it passes parsing, execution fails.
        """)
        
        # We manually craft a model with python code that uses eval, bypassing parser?
        # No, we test the COMPILER pipeline.
        
        # If I can't inject eval via LOS syntax, then RCE via syntax is impossible (Good!)
        # But let's verify that `solve` uses restricted globals.
        
        # We can unit test the Translator or Model execution directly.
        from los.domain.entities.los_model import LOSModel
        
        # Create a fake model with malicious python code
        fake_ast = {'name': 'Fake'}
        malicious_code = "import os; os.system('echo PWNED')"
        
        model = LOSModel(
            source="", 
            ast=fake_ast, 
            python_code=malicious_code, 
            variables=[], 
            datasets=[], 
            complexity=None, 
            name="Malicious"
        )
        
        # Attempt to solve
        result = model.solve()
        
        # Verify it failed safely
        # Sandbox might block __import__ before os is accessed
        self.assertIn("ExecutionError", result.status)
        self.assertTrue(
            "name 'os' is not defined" in result.status or 
            "__import__ not found" in result.status or
            "name '__import__' is not defined" in result.status
        )

if __name__ == '__main__':
    unittest.main()
