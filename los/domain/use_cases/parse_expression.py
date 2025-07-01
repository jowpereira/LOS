"""
🎯 Parse Expression Use Case
Caso de uso para análise e parsing de expressões LOS
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass

from ..entities.expression import Expression
from ..value_objects.expression_types import ExpressionType, OperationType
from ..repositories.interfaces import IExpressionRepository, IGrammarRepository
from ...shared.errors.exceptions import ParseError, ValidationError, BusinessRuleError
from ...shared.logging.logger import get_logger


@dataclass
class ParseExpressionRequest:
    """Request para parsing de expressão"""
    text: str
    validate: bool = True
    save_result: bool = False


@dataclass 
class ParseExpressionResponse:
    """Response do parsing de expressão"""
    expression: Expression
    success: bool
    errors: list
    warnings: list


class ParseExpressionUseCase:
    """
    Use case para parsing de expressões LOS
    
    Responsabilidades:
    - Coordenar o processo de parsing
    - Aplicar regras de negócio
    - Validar resultado
    - Opcionalmente persistir
    """
    
    def __init__(
        self,
        expression_repository: IExpressionRepository,
        grammar_repository: IGrammarRepository
    ):
        self._expression_repo = expression_repository
        self._grammar_repo = grammar_repository
        self._logger = get_logger('use_cases.parse_expression')
    
    async def execute(self, request: ParseExpressionRequest) -> ParseExpressionResponse:
        """
        Executa o parsing de uma expressão
        
        Args:
            request: Dados da requisição
            
        Returns:
            Resultado do parsing
        """
        errors = []
        warnings = []
        
        try:
            self._logger.info(f"Iniciando parsing de expressão: {request.text[:50]}...")
            
            # Validações iniciais
            if not request.text.strip():
                raise ValidationError(
                    message="Texto da expressão não pode estar vazio",
                    field="text"
                )
            
            # Criar expressão base
            expression = Expression(original_text=request.text.strip())
            
            # Determinar tipo de expressão (regra de negócio)
            expression_type = self._detect_expression_type(request.text)
            expression.expression_type = expression_type
            
            # Determinar operação (regra de negócio)
            operation_type = self._detect_operation_type(request.text, expression_type)
            expression.operation_type = operation_type
            
            # Aplicar regras de validação se solicitado
            if request.validate:
                validation_errors = self._validate_expression_rules(expression)
                if validation_errors:
                    errors.extend(validation_errors)
                    expression.validation_errors.extend(validation_errors)
                    expression.is_valid = False
            
            # Salvar se solicitado e válido
            if request.save_result and expression.is_valid:
                expression = await self._expression_repo.save(expression)
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
            
            # Retornar expressão com erro
            expression = Expression(
                original_text=request.text,
                is_valid=False,
                validation_errors=[str(e)]
            )
            
            return ParseExpressionResponse(
                expression=expression,
                success=False,
                errors=errors,
                warnings=warnings
            )
        
        except Exception as e:
            self._logger.error(f"Erro inesperado durante parsing: {e}")
            errors.append(f"Erro interno: {str(e)}")
            
            expression = Expression(
                original_text=request.text,
                is_valid=False,
                validation_errors=[f"Erro interno: {str(e)}"]
            )
            
            return ParseExpressionResponse(
                expression=expression,
                success=False,
                errors=errors,
                warnings=warnings
            )
    
    def _detect_expression_type(self, text: str) -> ExpressionType:
        """
        Detecta tipo de expressão baseado no texto
        Implementa regras de negócio para classificação
        """
        text_upper = text.upper().strip()
        
        # Objetivos
        if text_upper.startswith('MINIMIZAR:') or text_upper.startswith('MAXIMIZAR:'):
            return ExpressionType.OBJECTIVE
        
        # Condicionais  
        if 'SE ' in text_upper and ' ENTAO ' in text_upper:
            return ExpressionType.CONDITIONAL
        
        # Agregações
        if 'SOMA DE' in text_upper or 'PARA CADA' in text_upper:
            return ExpressionType.AGGREGATION
        
        # Restrições (tem operadores relacionais)
        comparison_operators = ['<=', '>=', '==', '!=', '<', '>', '=']
        if any(op in text for op in comparison_operators):
            return ExpressionType.CONSTRAINT
        
        # Default: matemática
        return ExpressionType.MATHEMATICAL
    
    def _detect_operation_type(self, text: str, expr_type: ExpressionType) -> OperationType:
        """
        Detecta tipo de operação baseado no texto e tipo de expressão
        """
        text_upper = text.upper()
        
        if expr_type == ExpressionType.OBJECTIVE:
            if text_upper.startswith('MINIMIZAR:'):
                return OperationType.MINIMIZE
            elif text_upper.startswith('MAXIMIZAR:'):
                return OperationType.MAXIMIZE
        
        elif expr_type == ExpressionType.CONSTRAINT:
            if '<=' in text:
                return OperationType.LESS_EQUAL
            elif '>=' in text:
                return OperationType.GREATER_EQUAL
            elif '==' in text:
                return OperationType.EQUAL
            elif '!=' in text:
                return OperationType.NOT_EQUAL
            elif '<' in text:
                return OperationType.LESS
            elif '>' in text:
                return OperationType.GREATER
            elif '=' in text:
                return OperationType.EQUAL
        
        elif expr_type == ExpressionType.CONDITIONAL:
            return OperationType.IF_THEN_ELSE
        
        # Default para matemáticas
        if '+' in text:
            return OperationType.ADDITION
        elif '-' in text:
            return OperationType.SUBTRACTION
        elif '*' in text:
            return OperationType.MULTIPLICATION
        elif '/' in text:
            return OperationType.DIVISION
        
        return OperationType.ADDITION  # Default
    
    def _validate_expression_rules(self, expression: Expression) -> list:
        """
        Valida regras de negócio específicas da expressão
        
        Returns:
            Lista de erros encontrados
        """
        errors = []
        
        # Regra: Objetivos devem ter palavras-chave corretas
        if expression.expression_type == ExpressionType.OBJECTIVE:
            text_upper = expression.original_text.upper()
            if not (text_upper.startswith('MINIMIZAR:') or text_upper.startswith('MAXIMIZAR:')):
                errors.append("Objetivos devem começar com 'MINIMIZAR:' ou 'MAXIMIZAR:'")
        
        # Regra: Restrições devem ter operadores relacionais
        elif expression.expression_type == ExpressionType.CONSTRAINT:
            comparison_ops = ['<=', '>=', '==', '!=', '<', '>', '=']
            if not any(op in expression.original_text for op in comparison_ops):
                errors.append("Restrições devem conter operadores relacionais")
        
        # Regra: Condicionais devem ter estrutura SE...ENTAO
        elif expression.expression_type == ExpressionType.CONDITIONAL:
            text_upper = expression.original_text.upper()
            if not ('SE ' in text_upper and ' ENTAO ' in text_upper):
                errors.append("Condicionais devem ter estrutura 'SE ... ENTAO ...'")
        
        return errors
