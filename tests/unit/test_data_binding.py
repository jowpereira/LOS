
import unittest
import sys
import os
import pandas as pd
import numpy as np

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from los.application.services.data_binding_service import DataBindingService

class TestDataBinding(unittest.TestCase):
    def setUp(self):
        self.service = DataBindingService()

    def test_bind_simple_set(self):
        # Set I from list
        ast = {'statements': [{'type': 'set', 'name': 'I'}]}
        data = {'I': [1, 2, 3]}
        bound = self.service.bind_data(ast, data)
        self.assertEqual(bound['I'], [1, 2, 3])

    def test_bind_set_from_dataframe(self):
        # Set Products from df['Products']
        df = pd.DataFrame({'Products': ['A', 'B'], 'Cost': [10, 20]})
        ast = {'statements': [{'type': 'set', 'name': 'Products'}]}
        data = {'Products': df}
        bound = self.service.bind_data(ast, data)
        self.assertEqual(bound['Products'], ['A', 'B'])

    def test_non_destructive_binding(self):
        # Critical test: Bind Set AND Param from SAME DataFrame
        df = pd.DataFrame({'Products': ['A', 'B'], 'Cost': [10, 20]})
        ast = {
            'statements': [
                {'type': 'set', 'name': 'Products'},
                {'type': 'param', 'name': 'Cost', 'indices': ['Products']}
            ]
        }
        # Pass DF as 'Products' (source for set)
        data = {'Products': df}
        
        bound = self.service.bind_data(ast, data)
        
        # Verify Set
        self.assertEqual(bound['Products'], ['A', 'B'])
        
        # Verify Param found in 'Products' DF (D03 logic)
        self.assertIn('Cost', bound)
        # Check structure: {'A': 10, 'B': 20} (simple index) or nested?
        # Service returns nested dict. For 1D: {'A': 10, ...}
        self.assertEqual(bound['Cost']['A'], 10)
        self.assertEqual(bound['Cost']['B'], 20)

    def test_multi_index_binding(self):
        # Param Distance[Source, Dest]
        df = pd.DataFrame({
            'Source': ['S1', 'S1', 'S2', 'S2'],
            'Dest':   ['D1', 'D2', 'D1', 'D2'],
            'Distance': [10, 20, 30, 40]
        })
        ast = {
            'statements': [
                {'type': 'set', 'name': 'Source'},
                {'type': 'set', 'name': 'Dest'},
                {'type': 'param', 'name': 'Distance', 'indices': ['Source', 'Dest']}
            ]
        }
        # Provide sets explicitly or implicitly? 
        # Let's provide DF as 'Distance_Source' just to test extraction logic?
        # Or implicitly via sets. Service needs sets in context for densification.
        
        data = {
            'Source': ['S1', 'S2'],
            'Dest': ['D1', 'D2'],
            'Distance': df
        }
        
        bound = self.service.bind_data(ast, data)
        
        self.assertEqual(bound['Distance']['S1']['D1'], 10)
        self.assertEqual(bound['Distance']['S2']['D2'], 40)

if __name__ == '__main__':
    unittest.main()
