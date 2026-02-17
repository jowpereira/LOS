
import unittest
import sys
import os
import pandas as pd

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from los import solve, compile
from los.shared.errors.exceptions import ParseError, ValidationError

class TestEndToEnd(unittest.TestCase):
    def setUp(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        self.model_path = os.path.join(self.data_dir, 'integration_model.los')

    def _run_in_dir(self, directory, func):
        """Helper to run code in a specific directory"""
        cwd = os.getcwd()
        os.chdir(directory)
        try:
            func()
        finally:
            os.chdir(cwd)

    def test_solve_from_file(self):
        # Solve the model that imports the CSV
        # Must run in data_dir so pd.read_csv finds integration_products.csv
        def run():
            result = solve('integration_model.los') # Relative path now valid
            self.assertEqual(result.status, 'Optimal')
            self.assertAlmostEqual(result.objective, 10.0) 
        
        self._run_in_dir(self.data_dir, run)

    def test_solve_with_override(self):
        # Override Products with new data
        df = pd.DataFrame({'Products': ['C'], 'Cost': [5]})
        data = {'Products': df}
        
        def run():
            result = solve('integration_model.los', data=data)
            self.assertEqual(result.status, 'Optimal')
            self.assertAlmostEqual(result.objective, 5.0) 
            
        self._run_in_dir(self.data_dir, run)
        
    def test_syntax_error_file(self):
        # Create invalid file
        bad_path = os.path.join(self.data_dir, 'bad.los')
        with open(bad_path, 'w') as f:
            f.write("maximize x # syntax error")
            
        try:
            with self.assertRaises(ParseError):
                compile(bad_path)
        finally:
            if os.path.exists(bad_path):
                os.remove(bad_path)

    def test_solve_supply_chain_example(self):
        # Solve the complex supply chain model reused from user examples
        examples_dir = os.path.join(self.data_dir, 'examples')
        model_file = 'supply_chain_network.los'
        
        # Ensure it exists
        if not os.path.exists(os.path.join(examples_dir, model_file)):
             self.fail(f"Example model not found: {model_file} in {examples_dir}")
             
        def run():
            # Solve
            # The model uses relative imports, so base_dir must be resolved correctly.
            # AND generated code uses pd.read_csv, so CWD must be correct.
            result = solve(model_file)
            
            # Expect Optimal or Feasible
            self.assertIn(result.status, ['Optimal', 'Feasible'])
            self.assertIsNotNone(result.objective)
            self.assertGreater(result.objective, 0)
            
        self._run_in_dir(examples_dir, run)

if __name__ == '__main__':
    unittest.main()
