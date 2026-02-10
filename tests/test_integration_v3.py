
import sys
import os
# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from los.infrastructure.parsers.los_parser import LOSParser
from los.infrastructure.translators.pulp_translator import PuLPTranslator
from los.domain.entities.expression import Expression

# Sample Model to test
MODEL_V3 = """
import "data.csv"

set P = {A, B, C}
param demand[P] = 100

var x[P] >= 0

min: sum(x[p] * 2 for p in P)

st:
    limit: sum(x[p] for p in P) <= 1000
    demand_met: x[p] >= demand[p] for p in P
"""

class TestTranslatorV3:
    
    def setup_method(self):
        self.parser = LOSParser()
        self.translator = PuLPTranslator()

    def test_full_translation_flow(self):
        # 1. Parse
        parse_result = self.parser.parse(MODEL_V3)
        assert parse_result['success'] is True
        
        # 2. Create Entity logic (similar to UseCase)
        expr = Expression(original_text=MODEL_V3)
        expr.syntax_tree = parse_result['parsed_result']
        expr.expression_type = "model" # Simplified assignment
        
        # 3. Translate
        code = self.translator.translate_expression(expr)
        
        # 4. Assertions
        print(code) # For debug
        
        assert "import pulp" in code
        assert "prob =" in code
        assert "pulp.LpProblem" in code
        
        # Sets — F08: identifiers inside sets are quoted
        assert "P = ['A', 'B', 'C']" in code
        
        # Vars
        assert "x = pulp.LpVariable.dicts('x', (P)" in code
        
        # Objective
        assert "prob += pulp.lpSum" in code
        assert "* 2" in code
        
        # Constraints
        assert "prob += pulp.lpSum" in code
        assert "<= 1000" in code
        
        # Loops in constraints
        assert "for p in P:" in code
        assert ">= demand[p]" in code
        
        # Solve
        assert "prob.solve()" in code

    def test_simple_objective(self):
        text = "min: 2 * x + y"
        parse_result = self.parser.parse(text)
        expr = Expression(original_text=text)
        expr.syntax_tree = parse_result['parsed_result']
        
        code = self.translator.translate_expression(expr)
        # F06: objective is just "prob += expr, 'Objective'"
        # Binary op produces parens: (2 * x) or ((2 * x) + y)
        assert "prob +=" in code
        assert "Objective" in code

if __name__ == "__main__":
    t = TestTranslatorV3()
    t.setup_method()
    t.test_full_translation_flow()
    t.test_simple_objective()
    print("Tests passed")
