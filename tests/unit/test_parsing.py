
import unittest
import sys
import os

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from los.infrastructure.parsers.los_parser import LOSParser
from los.shared.errors.exceptions import ParseError

class TestLOSParser(unittest.TestCase):
    def setUp(self):
        self.parser = LOSParser()

    def test_empty_model(self):
        code = ""
        with self.assertRaises(ParseError):
            self.parser.parse(code)

    def test_basic_sets(self):
        code = """
        set Products
        set Factories = {"F1", "F2"}
        set Time = 1..10
        """
        result = self.parser.parse(code)
        self.assertTrue(result['success'])
        stmts = result['parsed_result']['statements']
        self.assertEqual(len(stmts), 3)
        self.assertEqual(stmts[0]['type'], 'set')
        self.assertEqual(stmts[0]['name'], 'Products')
        # Value is {'type': 'set_literal', 'elements': [...]}
        elements_struct = stmts[1]['value']['elements']
        # Value is {'type': 'set_range', 'start': {'value': 1.0}, 'end': {'value': 10.0}}
        range_val = stmts[2]['value']
        self.assertEqual(range_val['type'], 'set_range')
        self.assertEqual(range_val['start']['value'], 1.0)
        self.assertEqual(range_val['end']['value'], 10.0)

    def test_params(self):
        code = """
        param Cost[Products]
        param MaxCap = 100
        param Distance[Factories, Customers]
        """
        result = self.parser.parse(code)
        self.assertTrue(result['success'])
        stmts = result['parsed_result']['statements']
        self.assertEqual(len(stmts), 3)
        self.assertEqual(stmts[0]['indices'], ['Products'])
        # Value is a dict {'type': 'number', 'value': 100.0}
        self.assertEqual(stmts[1]['value']['value'], 100.0)

    def test_variables(self):
        code = """
        var qty[Products] >= 0
        var active[Factories] : bin
        var workers : int >= 10
        """
        result = self.parser.parse(code)
        self.assertTrue(result['success'])
        stmts = result['parsed_result']['statements']
        self.assertEqual(len(stmts), 3)
        self.assertEqual(stmts[0]['var_type'], 'continuous')
        self.assertEqual(stmts[1]['var_type'], 'bin')
        self.assertEqual(stmts[2]['var_type'], 'int')

    def test_objective(self):
        # Adding newline to ensure statement termination if grammar requires it
        code = "minimize: sum(x[i] for i in I)\n"
        result = self.parser.parse(code)
        # Debug
        if 'statements' not in result.get('parsed_result', {}):
             print(f"DEBUG OBJECTIVE: {result}")
        
        self.assertTrue(result['success'])
        obj = result['parsed_result']['statements'][0]
        self.assertEqual(obj['type'], 'objective')
        self.assertEqual(obj['sense'], 'minimize')

    def test_constraints(self):
        code = """
        subject to:
            c1: x + y <= 10
            c2: sum(z[i] for i in I) >= 5
        """
        result = self.parser.parse(code)
        # Debug
        if 'statements' not in result.get('parsed_result', {}):
             print(f"DEBUG CONSTRAINTS: {result}")

        self.assertTrue(result['success'])
        constrs = result['parsed_result']['statements'][0]['constraints']
        self.assertEqual(len(constrs), 2)
        self.assertEqual(constrs[0]['name'], 'c1')

    def test_syntax_error(self):
        code = "var x [" # Missing bracket
        with self.assertRaises(ParseError):
            self.parser.parse(code)

if __name__ == '__main__':
    unittest.main()
