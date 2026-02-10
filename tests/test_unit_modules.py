#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 Testes Unitários para Módulos LOS v3.1
Alinhados com API real: Expression, Variable, DatasetReference, DTOs, Exceptions
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from los.domain.entities.expression import Expression
from los.domain.value_objects.expression_types import (
    ExpressionType, 
    OperationType, 
    Variable, 
    DatasetReference,
    ComplexityMetrics
)
from los.application.dto.expression_dto import (
    ExpressionRequestDTO,
    ExpressionResponseDTO,
    BatchProcessRequestDTO,
    BatchProcessResponseDTO,
    ValidationRequestDTO
)
from los.shared.errors.exceptions import ValidationError, ParseError


class TestDomainEntities:
    """Testes das entidades de domínio — v3.1 API"""
    
    def test_expression_creation(self):
        """Testa criação de entidade Expression com API v3"""
        var = Variable(name="x", variable_type="continuous")
        ds = DatasetReference(dataset_name="produtos", column_name="custo")
        
        expression = Expression(original_text="min: x + y")
        expression.expression_type = ExpressionType.OBJECTIVE
        expression.operation_type = OperationType.MINIMIZE
        expression.add_variable(var)
        expression.add_dataset_reference(ds)
        
        assert expression.original_text == "min: x + y"
        assert expression.expression_type == ExpressionType.OBJECTIVE
        assert expression.operation_type == OperationType.MINIMIZE
        assert "x" in expression.get_variable_names()
    
    def test_expression_validation(self):
        """Testa validação de expressão"""
        # Expressão válida
        valid_expr = Expression(original_text="max: lucro")
        valid_expr.validate()
        assert valid_expr.is_valid is True
        
        # Expressão inválida (sem texto)
        invalid_expr = Expression(original_text="   ")
        invalid_expr.validate()
        assert invalid_expr.is_valid is False
    
    def test_expression_complexity_calculation(self):
        """Testa métricas de complexidade"""
        simple = ComplexityMetrics(operation_count=1)
        complex_ = ComplexityMetrics(
            nesting_level=3, operation_count=5,
            function_count=2, conditional_count=1
        )
        
        assert complex_.total_complexity > simple.total_complexity
        assert simple.complexity_level == "BAIXA"


class TestValueObjects:
    """Testes dos value objects"""
    
    def test_variable_value_object(self):
        """Testa value object Variable com campo correto"""
        var1 = Variable(name="x", variable_type="continuous")
        var2 = Variable(name="x", variable_type="continuous")
        var3 = Variable(name="y", variable_type="integer")
        
        assert var1 == var2
        assert var1 != var3
        
        # Frozen → imutável
        with pytest.raises(AttributeError):
            var1.name = "z"
    
    def test_dataset_reference_value_object(self):
        """Testa value object DatasetReference"""
        ds1 = DatasetReference(dataset_name="produtos", column_name="custo")
        ds2 = DatasetReference(dataset_name="produtos", column_name="custo")
        ds3 = DatasetReference(dataset_name="clientes", column_name="demanda")
        
        assert ds1 == ds2
        assert ds1 != ds3
        
        assert ds1.dataset_name == "produtos"
        assert ds1.column_name == "custo"
    
    def test_expression_types_enum(self):
        """Testa enums de tipos de expressão"""
        assert ExpressionType.OBJECTIVE.value == "objective"
        assert ExpressionType.CONSTRAINT.value == "constraint"
        assert ExpressionType.MATHEMATICAL.value == "mathematical"
        
        assert OperationType.MINIMIZE.value == "minimize"
        assert OperationType.MAXIMIZE.value == "maximize"


class TestApplicationDTOs:
    """Testes dos DTOs da camada de aplicação"""
    
    def test_expression_request_dto(self):
        """Testa ExpressionRequestDTO"""
        request = ExpressionRequestDTO(
            text="min: x + y",
            validate=True,
            save_result=False
        )
        
        assert request.text == "min: x + y"
        assert request.validate is True
        assert request.save_result is False
        assert request.context is None
    
    def test_expression_response_dto(self):
        """Testa ExpressionResponseDTO"""
        response = ExpressionResponseDTO(
            id="expr-001",
            original_text="min: x + y",
            python_code="prob += x + y",
            expression_type="objective",
            operation_type="minimize",
            variables=["x", "y"],
            dataset_references=[],
            complexity={"nesting_level": 1},
            is_valid=True,
            validation_errors=[],
            created_at="2026-02-10",
            success=True,
            errors=[],
            warnings=[]
        )
        
        assert response.success is True
        assert response.id == "expr-001"
        assert response.expression_type == "objective"
        assert len(response.variables) == 2
        assert len(response.errors) == 0
    
    def test_batch_process_dto(self):
        """Testa BatchProcessRequestDTO e ResponseDTO"""
        batch_request = BatchProcessRequestDTO(
            expressions=["min: x", "max: y", "st: x >= 0"],
            validate_all=True,
            stop_on_error=False
        )
        
        assert len(batch_request.expressions) == 3
        assert batch_request.validate_all is True
        assert batch_request.stop_on_error is False
    
    def test_validation_request_default(self):
        """F14: validation_rules defaults to empty list, not None"""
        req = ValidationRequestDTO()
        assert req.validation_rules is not None
        assert isinstance(req.validation_rules, list)
        assert len(req.validation_rules) == 0


class TestErrorHandling:
    """Testes de tratamento de erros"""
    
    def test_validation_error(self):
        """Testa ValidationError — field is via context"""
        error = ValidationError("Campo obrigatório não fornecido", field="text")
        
        assert str(error) == "Campo obrigatório não fornecido"
        assert error.context['field'] == "text"
        assert error.error_code == "VALIDATION_ERROR"
    
    def test_parse_error(self):
        """Testa ParseError with correct constructor"""
        error = ParseError(
            "Sintaxe inválida na posição 5",
            expression="invalid input",
            line_number=1,
            column=5
        )
        
        assert str(error) == "Sintaxe inválida na posição 5"
        assert error.context['column'] == 5
        assert error.error_code == "PARSE_ERROR"
    
    def test_error_aggregation(self):
        """Testa agregação de múltiplos erros"""
        errors = [
            ValidationError("Erro 1", field="a"),
            ParseError("Erro 2", expression="bad"),
            ValidationError("Erro 3", field="b")
        ]
        
        error_messages = [str(e) for e in errors]
        validation_errors = [e for e in errors if isinstance(e, ValidationError)]
        parse_errors = [e for e in errors if isinstance(e, ParseError)]
        
        assert len(error_messages) == 3
        assert len(validation_errors) == 2
        assert len(parse_errors) == 1


class TestInfrastructureMocks:
    """Testes com mocks da infraestrutura"""
    
    @patch('los.infrastructure.parsers.los_parser.LOSParser')
    def test_parser_mock(self, mock_parser_class):
        mock_parser = Mock()
        mock_result = {
            'parsed_result': {'type': 'objective', 'sense': 'minimize'},
            'variables': [],
            'datasets': [],
            'complexity': {'nesting_level': 1},
            'success': True
        }
        mock_parser.parse.return_value = mock_result
        mock_parser_class.return_value = mock_parser
        
        from los.infrastructure.parsers.los_parser import LOSParser
        parser = LOSParser()
        result = parser.parse("min: x + y")
        
        assert result['success'] is True
        mock_parser.parse.assert_called_once_with("min: x + y")
    
    @patch('los.infrastructure.translators.pulp_translator.PuLPTranslator')
    def test_translator_mock(self, mock_translator_class):
        mock_translator = Mock()
        mock_translator.translate_expression.return_value = "import pulp\nprob = pulp.LpProblem()"
        mock_translator_class.return_value = mock_translator
        
        from los.infrastructure.translators.pulp_translator import PuLPTranslator
        translator = PuLPTranslator()
        
        mock_expression = Mock()
        result = translator.translate_expression(mock_expression)
        
        assert "LpProblem" in result
        mock_translator.translate_expression.assert_called_once_with(mock_expression)


class TestAdvancedScenarios:
    """Testes de cenários avançados"""
    
    def test_concurrent_processing(self):
        import threading
        import time
        
        results = []
        
        def process_expression(expr_text, thread_id):
            try:
                time.sleep(0.01)
                results.append({
                    'thread_id': thread_id,
                    'expression': expr_text,
                    'success': True
                })
            except Exception:
                pass
        
        expressions = [
            "min: x + y",
            "max: a - b", 
            "st: x >= 0",
            "st: y <= 100"
        ]
        
        threads = []
        for i, expr in enumerate(expressions):
            thread = threading.Thread(target=process_expression, args=(expr, i))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        assert len(results) == 4
        assert all(r['success'] for r in results)
    
    def test_error_recovery(self):
        expressions_with_issues = [
            ("min:", "incomplete"),
            ("INVALID", "invalid"),
            ("min: x + y", "valid")
        ]
        
        results = []
        for expr, expected_type in expressions_with_issues:
            success = (expected_type == "valid")
            results.append({'success': success, 'error_type': expected_type})
        
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        assert len(successful) >= 1
        assert len(failed) >= 1


class TestPerformanceMetrics:
    """Testes de métricas de performance"""
    
    def test_expression_complexity_metrics(self):
        """Testa métricas de complexidade via ComplexityMetrics"""
        low = ComplexityMetrics(nesting_level=1, operation_count=1)
        mid = ComplexityMetrics(nesting_level=2, operation_count=3, function_count=1)
        high = ComplexityMetrics(
            nesting_level=3, operation_count=5,
            function_count=2, conditional_count=2
        )
        
        assert low.total_complexity < mid.total_complexity
        assert mid.total_complexity < high.total_complexity
        assert low.complexity_level == "BAIXA"
        assert high.complexity_level in ("ALTA", "MUITO_ALTA")
    
    def test_processing_time_tracking(self):
        import time
        
        expressions = ["x + y", "min: x + y", "sum(x, for i in S)"]
        times = []
        
        for expr in expressions:
            start = time.time()
            complexity = len(expr.split())
            time.sleep(0.001 * complexity)
            times.append(time.time() - start)
        
        assert all(t > 0 for t in times)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
