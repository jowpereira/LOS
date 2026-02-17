"""Caso de uso de parsing."""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from ..entities.expression import Expression
from ..value_objects.expression_types import (
    ExpressionType, OperationType, Variable, DatasetReference, ComplexityMetrics
)
from ..repositories.interfaces import IExpressionRepository, IGrammarRepository
from ...application.interfaces.adapters import IParserAdapter
from ...shared.errors.exceptions import ParseError, ValidationError, BusinessRuleError
from ...shared.logging.logger import get_logger


@dataclass
class ParseExpressionRequest:
    """Request de parsing."""
    text: str
    validate: bool = True
    save_result: bool = False


@dataclass 
class ParseExpressionResponse:
    """Response de parsing."""
    expression: Expression
    success: bool
    errors: list
    warnings: list


class ParseExpressionUseCase:
    """Coordena o processo de parsing e validação."""
    
    def __init__(
        self,
        expression_repository: IExpressionRepository,
        grammar_repository: IGrammarRepository,
        parser_adapter: IParserAdapter
    ):
        self._expression_repo = expression_repository
        self._grammar_repo = grammar_repository
        self._parser = parser_adapter
        self._logger = get_logger('use_cases.parse_expression')
    
    def execute(self, request: ParseExpressionRequest) -> ParseExpressionResponse:
        """Executa parsing de expressão."""
        errors = []
        warnings = []
        
        try:
            self._logger.info(f"Iniciando parsing de expressão: {request.text[:50]}...")
            
            # Validações iniciais
            if not request.text or not request.text.strip():
                raise ValidationError(
                    message="Texto da expressão não pode estar vazio",
                    field="text"
                )
            
            # Parsing Real
            try:
                parse_result = self._parser.parse(request.text)
            except Exception as e:
                # Se falhar no parsing, não podemos prosseguir
                self._logger.error(f"Erro no parser: {e}")
                # Criar expressão inválida para retorno consistente
                expr_error = Expression(
                    original_text=request.text,
                    is_valid=False,
                    validation_errors=[str(e)]
                )
                return ParseExpressionResponse(
                    expression=expr_error,
                    success=False,
                    errors=[str(e)],
                    warnings=warnings
                )

            # Criar Entidade
            expression = Expression(original_text=request.text.strip())
            
            # Mapear resultado do parser para a entidade
            self._map_parser_result_to_entity(expression, parse_result)
            
            # Validação
            if request.validate:
                expression.validate()
                if not expression.is_valid:
                    errors.extend(expression.validation_errors)

            # Persistência
            if request.save_result and expression.is_valid:
                result = self._expression_repo.save(expression)
                expression.id = result.id
                self._logger.info(f"Expressão salva com ID: {expression.id}")
            
            success = len(errors) == 0
            
            self._logger.info(
                f"Parsing concluído - Sucesso: {success}, "
                f"Erros: {len(errors)}, Warnings: {len(warnings)}"
            )
            
            return ParseExpressionResponse(
                expression=expression,
                success=success,
                errors=errors,
                warnings=warnings
            )
            
        except (ParseError, ValidationError, BusinessRuleError) as e:
            self._logger.error(f"Erro durante parsing: {e}")
            errors.append(str(e))
            
            return ParseExpressionResponse(
                expression=Expression(
                    original_text=request.text,
                    is_valid=False,
                    validation_errors=[str(e)]
                ),
                success=False,
                errors=errors,
                warnings=warnings
            )
        
        except Exception as e:
            self._logger.error(f"Erro inesperado durante parsing UseCase: {e}")
            errors.append(f"Erro interno: {str(e)}")
            
            return ParseExpressionResponse(
                expression=Expression(
                    original_text=request.text,
                    is_valid=False,
                    validation_errors=[f"Erro interno: {str(e)}"]
                ),
                success=False,
                errors=errors,
                warnings=warnings
            )

    def _map_parser_result_to_entity(self, expression: Expression, parse_result: Dict[str, Any]):
        """Popula a entidade Expression com dados do parser."""
        
        parsed_data = parse_result.get('parsed_result', {})
        expression.syntax_tree = parsed_data
        
        # Determinar tipo
        node_type = parsed_data.get('type')
        
        if node_type == 'model':
            expression.expression_type = ExpressionType.MODEL
            
        elif node_type == 'objective':
            expression.expression_type = ExpressionType.OBJECTIVE
            sense = parsed_data.get('sense', 'minimize')
            expression.operation_type = OperationType.MINIMIZE if sense == 'minimize' else OperationType.MAXIMIZE
            
        elif node_type == 'constraint' or node_type == 'constraint_block':
            expression.expression_type = ExpressionType.CONSTRAINT
            
        # Variáveis
        variables = parse_result.get('variables', [])
        for var in variables:
            if isinstance(var, Variable):
                expression.add_variable(var)
        
        # Datasets
        datasets = parse_result.get('datasets', [])
        for ref in datasets:
            if isinstance(ref, DatasetReference):
                expression.add_dataset_reference(ref)
            
        # Complexidade
        comp_data = parse_result.get('complexity', None)
        if comp_data and isinstance(comp_data, ComplexityMetrics):
             expression.complexity = comp_data
        elif comp_data and isinstance(comp_data, dict):
             expression.complexity = ComplexityMetrics(**comp_data)
