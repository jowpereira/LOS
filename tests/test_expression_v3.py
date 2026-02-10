"""
🧪 Expression Entity Unit Tests — v3.1 (F02 compatible)
Tests Expression.create(), Expression.validate(), and invariant checks.
"""

import pytest
from los.domain.entities.expression import Expression
from los.domain.value_objects.expression_types import (
    ExpressionType, OperationType, Variable, ComplexityMetrics
)


class TestExpressionEntity:
    
    def test_expression_creation_valid(self):
        """Expression created without __post_init__ validation"""
        expr = Expression(original_text="min: x")
        # is_valid defaults to False — must call validate()
        assert expr.is_valid is False
        assert expr.original_text == "min: x"
    
    def test_factory_create_valid(self):
        """Expression.create() validates immediately"""
        expr = Expression.create(original_text="min: x + y")
        # MATHEMATICAL type with non-empty text → valid
        assert expr.is_valid is True
        assert len(expr.validation_errors) == 0
    
    def test_factory_create_empty_text(self):
        """Expression.create() with empty text → invalid, no exception"""
        expr = Expression.create(original_text="   ")
        assert expr.is_valid is False
        assert "Texto original da expressão não pode estar vazio" in expr.validation_errors[0]
    
    def test_validate_objective_without_variables(self):
        """F02: Objective without variables → invalid via validate()"""
        expr = Expression(
            original_text="min: x",
            expression_type=ExpressionType.OBJECTIVE
        )
        result = expr.validate()
        
        assert result is False
        assert expr.is_valid is False
        assert any("variável" in e for e in expr.validation_errors)
    
    def test_validate_objective_with_variables(self):
        """Objective with variables → valid"""
        expr = Expression(
            original_text="min: x",
            expression_type=ExpressionType.OBJECTIVE
        )
        expr.add_variable(Variable(name="x"))
        result = expr.validate()
        
        assert result is True
        assert expr.is_valid is True
    
    def test_validate_comparison_op_in_non_constraint(self):
        """Comparison operations only valid in constraints/conditionals"""
        expr = Expression(
            original_text="x <= 5",
            expression_type=ExpressionType.MATHEMATICAL,
            operation_type=OperationType.LESS_EQUAL
        )
        expr.validate()
        
        assert expr.is_valid is False
        assert any("restrições" in e for e in expr.validation_errors)
    
    def test_add_variable(self):
        expr = Expression(original_text="x + y")
        expr.add_variable(Variable(name="x"))
        assert "x" in expr.get_variable_names()
    
    def test_no_post_init_side_effects(self):
        """Creating Expression with invalid-looking data does NOT raise"""
        # This must NOT raise — no __post_init__ validation
        expr = Expression(
            original_text="",
            expression_type=ExpressionType.OBJECTIVE
            # no variables → would be invalid IF validated
        )
        assert expr is not None
        # is_valid is default False (not validated yet)
        assert expr.is_valid is False

    def test_to_dict(self):
        expr = Expression(original_text="min: x + y")
        expr.validate()
        d = expr.to_dict()
        assert d['original_text'] == "min: x + y"
        assert d['is_valid'] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
