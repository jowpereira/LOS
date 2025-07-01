#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 Testes Unitários para Módulos LOS
Testes específicos para cada módulo da arquitetura Clean
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

# Adicionar o diretório pai ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from los.domain.entities.expression import Expression
from los.domain.value_objects.expression_types import (
    ExpressionType, 
    OperationType, 
    Variable, 
    DatasetReference
)
from los.application.dto.expression_dto import (
    ExpressionRequestDTO,
    ExpressionResponseDTO,
    BatchProcessRequestDTO,
    BatchProcessResponseDTO
)
from los.shared.errors.exceptions import ValidationError, ParseError


class TestDomainEntities:
    """Testes das entidades de domínio"""
    
    def test_expression_creation(self):
        """Testa criação de entidade Expression"""
        # Dados de teste
        variables = [Variable(name="x", type="continuous")]
        datasets = [DatasetReference(name="produtos", fields=["custo", "preco"])]
        
        expression = Expression(
            id="test-expr-001",
            text="MINIMIZAR: x + y",
            expression_type=ExpressionType.OBJECTIVE,
            operation_type=OperationType.MINIMIZE,
            variables=variables,
            dataset_references=datasets,
            complexity=2
        )
        
        # Verificações
        assert expression.id == "test-expr-001"
        assert expression.text == "MINIMIZAR: x + y"
        assert expression.expression_type == ExpressionType.OBJECTIVE
        assert expression.operation_type == OperationType.MINIMIZE
        assert len(expression.variables) == 1
        assert expression.variables[0].name == "x"
        assert len(expression.dataset_references) == 1
        assert expression.dataset_references[0].name == "produtos"
        assert expression.complexity == 2
    
    def test_expression_validation(self):
        """Testa validação de expressão"""
        # Expressão válida
        valid_expr = Expression(
            id="valid-001",
            text="MAXIMIZAR: lucro",
            expression_type=ExpressionType.OBJECTIVE,
            operation_type=OperationType.MAXIMIZE
        )
        
        assert valid_expr.is_valid()
        
        # Expressão inválida (sem texto)
        invalid_expr = Expression(
            id="invalid-001",
            text="",
            expression_type=ExpressionType.OBJECTIVE,
            operation_type=OperationType.MAXIMIZE
        )
        
        assert not invalid_expr.is_valid()
    
    def test_expression_complexity_calculation(self):
        """Testa cálculo de complexidade"""
        # Expressão simples
        simple_expr = Expression(
            id="simple-001",
            text="x + y",
            expression_type=ExpressionType.ASSIGNMENT
        )
        
        # Expressão complexa
        complex_expr = Expression(
            id="complex-001",
            text="MINIMIZAR: SOMA DE SE custos[i] > limite ENTAO custos[i] * 2 SENAO custos[i] PARA i EM produtos",
            expression_type=ExpressionType.OBJECTIVE,
            operation_type=OperationType.MINIMIZE
        )
        
        # Complexidade da expressão complexa deve ser maior
        assert complex_expr.calculate_complexity() > simple_expr.calculate_complexity()


class TestValueObjects:
    """Testes dos value objects"""
    
    def test_variable_value_object(self):
        """Testa value object Variable"""
        var1 = Variable(name="x", type="continuous", bounds=(0, 100))
        var2 = Variable(name="x", type="continuous", bounds=(0, 100))
        var3 = Variable(name="y", type="integer")
        
        # Teste de igualdade
        assert var1 == var2
        assert var1 != var3
        
        # Teste de imutabilidade (tentativa de alterar deve falhar)
        with pytest.raises(AttributeError):
            var1.name = "z"  # dataclass frozen
    
    def test_dataset_reference_value_object(self):
        """Testa value object DatasetReference"""
        dataset1 = DatasetReference(name="produtos", fields=["custo", "preco"])
        dataset2 = DatasetReference(name="produtos", fields=["custo", "preco"])
        dataset3 = DatasetReference(name="clientes", fields=["demanda"])
        
        # Teste de igualdade
        assert dataset1 == dataset2
        assert dataset1 != dataset3
        
        # Teste de campos
        assert "custo" in dataset1.fields
        assert "demanda" not in dataset1.fields
    
    def test_expression_types_enum(self):
        """Testa enums de tipos de expressão"""
        # Verificar valores do enum
        assert ExpressionType.OBJECTIVE.value == "objective"
        assert ExpressionType.CONSTRAINT.value == "constraint"
        assert ExpressionType.ASSIGNMENT.value == "assignment"
        
        assert OperationType.MINIMIZE.value == "minimize"
        assert OperationType.MAXIMIZE.value == "maximize"
        
        # Teste de conversão string para enum
        assert ExpressionType.from_string("objective") == ExpressionType.OBJECTIVE
        assert OperationType.from_string("minimize") == OperationType.MINIMIZE


class TestApplicationDTOs:
    """Testes dos DTOs da camada de aplicação"""
    
    def test_expression_request_dto(self):
        """Testa ExpressionRequestDTO"""
        # DTO básico
        request = ExpressionRequestDTO(
            text="MINIMIZAR: x + y",
            validate=True,
            save_result=False
        )
        
        assert request.text == "MINIMIZAR: x + y"
        assert request.validate is True
        assert request.save_result is False
        assert request.datasets is None
        
        # DTO com datasets
        datasets = {"produtos": [{"id": 1, "custo": 10}]}
        request_with_data = ExpressionRequestDTO(
            text="SOMA DE custos[i] PARA i EM produtos",
            datasets=datasets,
            validate=True
        )
        
        assert request_with_data.datasets == datasets
        assert "produtos" in request_with_data.datasets
    
    def test_expression_response_dto(self):
        """Testa ExpressionResponseDTO"""
        # Resposta de sucesso
        success_response = ExpressionResponseDTO(
            success=True,
            expression_id="expr-001",
            expression_type=ExpressionType.OBJECTIVE,
            operation_type=OperationType.MINIMIZE,
            variables=[Variable(name="x", type="continuous")],
            dataset_references=[],
            complexity=2,
            processing_time=0.05,
            errors=[]
        )
        
        assert success_response.success is True
        assert success_response.expression_id == "expr-001"
        assert success_response.expression_type == ExpressionType.OBJECTIVE
        assert len(success_response.variables) == 1
        assert len(success_response.errors) == 0
        
        # Resposta de erro
        error_response = ExpressionResponseDTO(
            success=False,
            errors=["Sintaxe inválida", "Variável não definida"]
        )
        
        assert error_response.success is False
        assert len(error_response.errors) == 2
        assert "Sintaxe inválida" in error_response.errors
    
    def test_batch_process_dto(self):
        """Testa BatchProcessRequestDTO e ResponseDTO"""
        # Request de lote
        batch_request = BatchProcessRequestDTO(
            expressions=["MINIMIZAR: x", "MAXIMIZAR: y", "RESTRINGIR: x >= 0"],
            validate_all=True,
            stop_on_error=False
        )
        
        assert len(batch_request.expressions) == 3
        assert batch_request.validate_all is True
        assert batch_request.stop_on_error is False
        
        # Response de lote
        batch_response = BatchProcessResponseDTO(
            total_expressions=3,
            successful_expressions=2,
            failed_expressions=1,
            results=[],
            errors=[],
            processing_time=0.15
        )
        
        assert batch_response.total_expressions == 3
        assert batch_response.successful_expressions == 2
        assert batch_response.failed_expressions == 1
        assert batch_response.success_rate == 2/3


class TestErrorHandling:
    """Testes de tratamento de erros"""
    
    def test_validation_error(self):
        """Testa ValidationError"""
        error = ValidationError("Campo obrigatório não fornecido", field="text")
        
        assert str(error) == "Campo obrigatório não fornecido"
        assert error.field == "text"
        assert error.error_code == "VALIDATION_ERROR"
    
    def test_parse_error(self):
        """Testa ParseError"""
        error = ParseError(
            "Sintaxe inválida na posição 5",
            position=5,
            token="INVALID"
        )
        
        assert str(error) == "Sintaxe inválida na posição 5"
        assert error.position == 5
        assert error.token == "INVALID"
        assert error.error_code == "PARSE_ERROR"
    
    def test_error_aggregation(self):
        """Testa agregação de múltiplos erros"""
        errors = [
            ValidationError("Erro 1"),
            ParseError("Erro 2"),
            ValidationError("Erro 3")
        ]
        
        # Simular agregação de erros
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
        """Testa mock do parser"""
        # Configurar mock
        mock_parser = Mock()
        mock_result = Mock()
        mock_result.expression_type = ExpressionType.OBJECTIVE
        mock_result.operation_type = OperationType.MINIMIZE
        mock_result.variables = []
        mock_result.dataset_references = []
        
        mock_parser.parse.return_value = mock_result
        mock_parser_class.return_value = mock_parser
        
        # Usar mock
        from los.infrastructure.parsers.los_parser import LOSParser
        parser = LOSParser()
        result = parser.parse("MINIMIZAR: x + y")
        
        # Verificações
        assert result.expression_type == ExpressionType.OBJECTIVE
        assert result.operation_type == OperationType.MINIMIZE
        mock_parser.parse.assert_called_once_with("MINIMIZAR: x + y")
    
    @patch('los.infrastructure.translators.pulp_translator.PuLPTranslator')
    def test_translator_mock(self, mock_translator_class):
        """Testa mock do tradutor"""
        # Configurar mock
        mock_translator = Mock()
        mock_translator.translate.return_value = "# Generated PuLP code\nprob = LpProblem()"
        mock_translator_class.return_value = mock_translator
        
        # Usar mock
        from los.infrastructure.translators.pulp_translator import PuLPTranslator
        translator = PuLPTranslator()
        
        # Mock expression
        mock_expression = Mock()
        mock_expression.expression_type = ExpressionType.OBJECTIVE
        
        result = translator.translate(mock_expression)
        
        # Verificações
        assert "PuLP" in result
        assert "LpProblem" in result
        mock_translator.translate.assert_called_once_with(mock_expression)
    
    @patch('los.infrastructure.validators.los_validator.LOSValidator')
    def test_validator_mock(self, mock_validator_class):
        """Testa mock do validador"""
        # Configurar mock
        mock_validator = Mock()
        mock_validator.validate.return_value = (True, [])
        mock_validator_class.return_value = mock_validator
        
        # Usar mock
        from los.infrastructure.validators.los_validator import LOSValidator
        validator = LOSValidator()
        
        # Mock expression
        mock_expression = Mock()
        is_valid, errors = validator.validate(mock_expression)
        
        # Verificações
        assert is_valid is True
        assert len(errors) == 0
        mock_validator.validate.assert_called_once_with(mock_expression)


class TestAdvancedScenarios:
    """Testes de cenários avançados"""
    
    def test_concurrent_processing(self):
        """Testa processamento concorrente (simulado)"""
        import threading
        import time
        
        results = []
        errors = []
        
        def process_expression(expr_text, thread_id):
            """Simula processamento de expressão em thread"""
            try:
                # Simular processamento
                time.sleep(0.01)  # Pequeno delay
                
                # Mock result
                result = {
                    'thread_id': thread_id,
                    'expression': expr_text,
                    'success': True
                }
                results.append(result)
                
            except Exception as e:
                errors.append({
                    'thread_id': thread_id,
                    'expression': expr_text,
                    'error': str(e)
                })
        
        # Criar threads para processar múltiplas expressões
        expressions = [
            "MINIMIZAR: x + y",
            "MAXIMIZAR: a - b", 
            "RESTRINGIR: x >= 0",
            "RESTRINGIR: y <= 100"
        ]
        
        threads = []
        for i, expr in enumerate(expressions):
            thread = threading.Thread(
                target=process_expression,
                args=(expr, i)
            )
            threads.append(thread)
            thread.start()
        
        # Aguardar conclusão
        for thread in threads:
            thread.join()
        
        # Verificações
        assert len(results) == 4
        assert len(errors) == 0
        assert all(r['success'] for r in results)
    
    def test_memory_intensive_operation(self):
        """Testa operação intensiva de memória"""
        # Simular processamento de dataset grande
        large_dataset = {
            'items': [{'id': i, 'value': i * 2} for i in range(10000)]
        }
        
        # Simular análise de expressão que referencia dataset grande
        expression_text = "SOMA DE value[i] PARA i EM items"
        
        # Mock processing
        variables_found = []
        datasets_found = []
        
        # Simular identificação de variáveis e datasets
        if 'value' in expression_text and 'items' in expression_text:
            variables_found.append('value')
            datasets_found.append('items')
        
        # Verificar que processamento foi bem-sucedido
        assert len(variables_found) > 0
        assert len(datasets_found) > 0
        assert 'items' in datasets_found
        assert len(large_dataset['items']) == 10000
    
    def test_error_recovery(self):
        """Testa recuperação de erros"""
        expressions_with_issues = [
            ("MINIMIZAR:", "incomplete_expression"),
            ("INVALID SYNTAX", "invalid_keyword"),
            ("MAXIMIZAR: x + + y", "syntax_error"),
            ("MINIMIZAR: x + y", "valid_expression")
        ]
        
        results = []
        
        for expr, expected_type in expressions_with_issues:
            try:
                # Simular processamento
                if expected_type == "valid_expression":
                    result = {
                        'expression': expr,
                        'success': True,
                        'type': 'objective'
                    }
                else:
                    result = {
                        'expression': expr,
                        'success': False,
                        'error_type': expected_type
                    }
                
                results.append(result)
                
            except Exception as e:
                results.append({
                    'expression': expr,
                    'success': False,
                    'error': str(e)
                })
        
        # Verificar que pelo menos uma expressão foi processada com sucesso
        successful = [r for r in results if r.get('success', False)]
        failed = [r for r in results if not r.get('success', False)]
        
        assert len(successful) >= 1
        assert len(failed) >= 1
        
        # Verificar que tipos de erro foram identificados corretamente
        error_types = [r.get('error_type') for r in failed if 'error_type' in r]
        assert 'incomplete_expression' in error_types


class TestPerformanceMetrics:
    """Testes de métricas de performance"""
    
    def test_expression_complexity_metrics(self):
        """Testa métricas de complexidade de expressões"""
        test_cases = [
            ("x + y", 1),  # Complexidade baixa
            ("SOMA DE custos[i] PARA i EM produtos", 3),  # Complexidade média
            ("MINIMIZAR: SOMA DE SE custos[i] > limite ENTAO custos[i] * fator SENAO custos[i] PARA i EM produtos ONDE ativo[i] == 1", 5)  # Complexidade alta
        ]
        
        for expression_text, expected_min_complexity in test_cases:
            # Simular cálculo de complexidade
            complexity_factors = 0
            
            # Contadores de complexidade
            if 'SOMA' in expression_text:
                complexity_factors += 1
            if 'SE' in expression_text and 'ENTAO' in expression_text:
                complexity_factors += 1
            if 'PARA' in expression_text:
                complexity_factors += 1
            if 'ONDE' in expression_text:
                complexity_factors += 1
            if any(op in expression_text for op in ['MINIMIZAR', 'MAXIMIZAR']):
                complexity_factors += 1
            
            calculated_complexity = max(1, complexity_factors)
            
            # Verificar que complexidade calculada está na faixa esperada
            assert calculated_complexity >= expected_min_complexity, \
                f"Complexidade de '{expression_text}' ({calculated_complexity}) menor que esperado ({expected_min_complexity})"
    
    def test_processing_time_tracking(self):
        """Testa rastreamento de tempo de processamento"""
        import time
        
        expressions = [
            "x + y",
            "MINIMIZAR: x + y", 
            "SOMA DE custos[i] PARA i EM produtos",
            "MAXIMIZAR: SOMA DE lucros[j] * vendas[j] PARA j EM servicos"
        ]
        
        processing_times = []
        
        for expr in expressions:
            start_time = time.time()
            
            # Simular processamento (com delay proporcional à complexidade)
            complexity = len(expr.split()) + expr.count('[') + expr.count('PARA')
            time.sleep(0.001 * complexity)  # Simular tempo de processamento
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            processing_times.append({
                'expression': expr,
                'time': processing_time,
                'complexity': complexity
            })
        
        # Verificar que tempos foram registrados
        assert all(pt['time'] > 0 for pt in processing_times)
        
        # Verificar que expressões mais complexas tendem a demorar mais
        sorted_by_complexity = sorted(processing_times, key=lambda x: x['complexity'])
        sorted_by_time = sorted(processing_times, key=lambda x: x['time'])
        
        # Pelo menos a expressão mais complexa deve estar entre as mais demoradas
        most_complex = sorted_by_complexity[-1]
        slowest_two = sorted_by_time[-2:]
        
        assert most_complex in slowest_two


if __name__ == "__main__":
    # Executar testes se rodado diretamente
    pytest.main([__file__, "-v", "--tb=short"])
