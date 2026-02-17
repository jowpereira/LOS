"""Validadores Especializados."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Set
from enum import Enum

from ...application.interfaces.adapters import IValidatorAdapter
from ...application.dto.expression_dto import (
    ValidationRequestDTO,
    ValidationResponseDTO
)
from ...domain.entities.expression import Expression
from ...domain.value_objects.expression_types import ExpressionType, OperationType
from ...shared.errors.exceptions import ValidationError
from ...shared.logging.logger import get_logger


class ValidationSeverity(Enum):
    """Severidade da validação."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationRule(ABC):
    """Classe base para regras de validação."""
    
    def __init__(self, name: str, description: str, severity: ValidationSeverity):
        self.name = name
        self.description = description
        self.severity = severity
    
    @abstractmethod
    def validate(self, expression: Expression) -> List[str]:
        """Valida expressão segundo a regra."""
        pass


class SyntaxValidationRule(ValidationRule):
    """Validação de sintaxe básica."""
    
    def __init__(self):
        super().__init__(
            "syntax_validation",
            "Valida sintaxe básica da expressão",
            ValidationSeverity.ERROR
        )
    
    def validate(self, expression: Expression) -> List[str]:
        errors = []
        
        # Texto não pode estar vazio
        if not expression.original_text.strip():
            errors.append("Expressão não pode estar vazia")
        
        # Verificar parênteses balanceados
        if not self._check_balanced_parentheses(expression.original_text):
            errors.append("Parênteses desbalanceados")
        
        # Verificar aspas balanceadas
        if not self._check_balanced_quotes(expression.original_text):
            errors.append("Aspas desbalanceadas")
        
        return errors
    
    def _check_balanced_parentheses(self, text: str) -> bool:
        """Verifica se parênteses estão balanceados."""
        stack = []
        pairs = {'(': ')', '[': ']', '{': '}'}
        
        for char in text:
            if char in pairs:
                stack.append(char)
            elif char in pairs.values():
                if not stack:
                    return False
                if pairs[stack.pop()] != char:
                    return False
        
        return len(stack) == 0
    
    def _check_balanced_quotes(self, text: str) -> bool:
        """Verifica se aspas estão balanceadas."""
        single_quotes = text.count("'")
        double_quotes = text.count('"')
        
        return single_quotes % 2 == 0 and double_quotes % 2 == 0


class ObjectiveValidationRule(ValidationRule):
    """Validação específica para objetivos."""
    
    def __init__(self):
        super().__init__(
            "objective_validation",
            "Valida estrutura de objetivos de otimização",
            ValidationSeverity.ERROR
        )
    
    def validate(self, expression: Expression) -> List[str]:
        errors = []
        
        if expression.expression_type != ExpressionType.OBJECTIVE:
            return errors
        
        text_upper = expression.original_text.upper()
        
        # Deve começar com MINIMIZAR: ou MAXIMIZAR:
        if not (text_upper.startswith('MINIMIZAR:') or text_upper.startswith('MAXIMIZAR:')):
            errors.append("Objetivos devem começar com 'MINIMIZAR:' ou 'MAXIMIZAR:'")
        
        # Deve ter pelo menos uma variável
        if len(expression.variables) == 0:
            errors.append("Objetivos devem conter pelo menos uma variável")
        
        # Operação deve ser coerente
        if text_upper.startswith('MINIMIZAR:') and expression.operation_type != OperationType.MINIMIZE:
            errors.append("Inconsistência: texto indica minimização mas operação é diferente")
        elif text_upper.startswith('MAXIMIZAR:') and expression.operation_type != OperationType.MAXIMIZE:
            errors.append("Inconsistência: texto indica maximização mas operação é diferente")
        
        return errors


class ConstraintValidationRule(ValidationRule):
    """Validação específica para restrições."""
    
    def __init__(self):
        super().__init__(
            "constraint_validation",
            "Valida estrutura de restrições",
            ValidationSeverity.ERROR
        )
    
    def validate(self, expression: Expression) -> List[str]:
        errors = []
        
        if expression.expression_type != ExpressionType.CONSTRAINT:
            return errors
        
        # Deve conter operador relacional
        relational_ops = ['<=', '>=', '==', '!=', '<', '>', '=']
        if not any(op in expression.original_text for op in relational_ops):
            errors.append("Restrições devem conter operadores relacionais (<=, >=, ==, etc.)")
        
        # Verificar se há expressões em ambos os lados do operador
        # Assume-se que o parser já garantiu que é um `constraint_block`.
        # Se for constraint, deve ter um operador principal.
        
        found_op = False
        for op in relational_ops:
            if op in expression.original_text:
                found_op = True
                break
        
        if not found_op:
             errors.append("Constraint expression missing relational operator")
        
        return errors


class VariableValidationRule(ValidationRule):
    """Validação de variáveis."""
    
    def __init__(self):
        super().__init__(
            "variable_validation",
            "Valida nomes e uso de variáveis",
            ValidationSeverity.WARNING
        )
    
    def validate(self, expression: Expression) -> List[str]:
        warnings = []
        
        # Verificar nomes de variáveis
        for variable in expression.variables:
            # Nome deve ser válido
            if not variable.name.isidentifier():
                warnings.append(f"Nome de variável inválido: '{variable.name}'")
            
            # Nome não deve ser palavra reservada Python
            python_keywords = [
                'and', 'as', 'assert', 'break', 'class', 'continue', 'def',
                'del', 'elif', 'else', 'except', 'finally', 'for', 'from',
                'global', 'if', 'import', 'in', 'is', 'lambda', 'nonlocal',
                'not', 'or', 'pass', 'raise', 'return', 'try', 'while',
                'with', 'yield'
            ]
            if variable.name.lower() in python_keywords:
                warnings.append(f"Variável '{variable.name}' é palavra reservada Python")
        
        # Verificar variáveis não utilizadas (se houver muitas declaradas)
        declared_vars = {var.name for var in expression.variables}
        used_vars = set()
        
        # Extrair variáveis usadas no código (análise simples)
        for var_name in declared_vars:
            if var_name in expression.python_code:
                used_vars.add(var_name)
        
        unused_vars = declared_vars - used_vars
        if unused_vars:
            warnings.append(f"Variáveis declaradas mas não utilizadas: {', '.join(unused_vars)}")
        
        return warnings


class ComplexityValidationRule(ValidationRule):
    """Validação de complexidade."""
    
    def __init__(self, max_complexity: int = 50):
        super().__init__(
            "complexity_validation",
            "Valida complexidade da expressão",
            ValidationSeverity.WARNING
        )
        self.max_complexity = max_complexity
    
    def validate(self, expression: Expression) -> List[str]:
        warnings = []
        
        total_complexity = expression.complexity.total_complexity
        
        if total_complexity > self.max_complexity:
            warnings.append(
                f"Expressão muito complexa (complexidade: {total_complexity}, "
                f"máximo recomendado: {self.max_complexity})"
            )
        
        # Aninhamento muito profundo
        if expression.complexity.nesting_level > 5:
            warnings.append(
                f"Aninhamento muito profundo (nível: {expression.complexity.nesting_level})"
            )
        
        # Muitas variáveis
        if expression.complexity.variable_count > 20:
            warnings.append(
                f"Muitas variáveis ({expression.complexity.variable_count}). "
                "Considere quebrar em expressões menores."
            )
        
        return warnings


class LOSValidator(IValidatorAdapter):
    """Validador principal do sistema LOS."""
    
    def __init__(self):
        self._rules: Dict[str, ValidationRule] = {}
        self._logger = get_logger('infrastructure.validators.los')
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """Inicializa regras padrão."""
        self.add_rule(SyntaxValidationRule())
        self.add_rule(ObjectiveValidationRule())
        self.add_rule(ConstraintValidationRule())
        self.add_rule(VariableValidationRule())
        self.add_rule(ComplexityValidationRule())
    
    def add_rule(self, rule: ValidationRule):
        """Adiciona regra de validação."""
        self._rules[rule.name] = rule
        self._logger.debug(f"Regra de validação adicionada: {rule.name}")
    
    def remove_rule(self, rule_name: str):
        """Remove regra de validação."""
        if rule_name in self._rules:
            del self._rules[rule_name]
            self._logger.debug(f"Regra de validação removida: {rule_name}")
    
    async def validate(self, request: ValidationRequestDTO) -> ValidationResponseDTO:
        """Valida expressão usando regras configuradas."""
        try:
            self._logger.info("Iniciando validação de expressão")
            
            # Para demonstração
            if request.expression_text:
                expression = self._create_mock_expression(request.expression_text)
            else:
                raise ValidationError(
                    message="Texto da expressão ou ID deve ser fornecido",
                    field="expression"
                )
            
            errors = []
            warnings = []
            applied_rules = []
            
            # Aplicar regras selecionadas ou todas
            rules_to_apply = request.validation_rules or list(self._rules.keys())
            
            for rule_name in rules_to_apply:
                if rule_name in self._rules:
                    rule = self._rules[rule_name]
                    
                    try:
                        messages = rule.validate(expression)
                        
                        if rule.severity == ValidationSeverity.ERROR:
                            errors.extend(messages)
                        elif rule.severity == ValidationSeverity.WARNING:
                            warnings.extend(messages)
                        
                        applied_rules.append(rule_name)
                        
                    except Exception as e:
                        self._logger.error(f"Erro aplicando regra {rule_name}: {e}")
                        errors.append(f"Erro interno na regra {rule_name}: {str(e)}")
            
            is_valid = len(errors) == 0
            
            self._logger.info(
                f"Validação concluída - Válida: {is_valid}, "
                f"Erros: {len(errors)}, Warnings: {len(warnings)}"
            )
            
            return ValidationResponseDTO(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings,
                applied_rules=applied_rules
            )
            
        except Exception as e:
            self._logger.error(f"Erro durante validação: {e}")
            return ValidationResponseDTO(
                is_valid=False,
                errors=[str(e)],
                warnings=[],
                applied_rules=[]
            )
    
    def get_available_rules(self) -> List[str]:
        """Retorna regras disponíveis."""
        return list(self._rules.keys())
    
    def get_rule_info(self, rule_name: str) -> Optional[Dict[str, Any]]:
        """Retorna informações sobre uma regra."""
        if rule_name in self._rules:
            rule = self._rules[rule_name]
            return {
                'name': rule.name,
                'description': rule.description,
                'severity': rule.severity.value
            }
        return None
    
    def _create_mock_expression(self, text: str) -> Expression:
        """Cria expressão mock para demonstração."""
        # Detectar tipo básico
        text_upper = text.upper()
        
        if text_upper.startswith('MINIMIZAR:'):
            expr_type = ExpressionType.OBJECTIVE
            op_type = OperationType.MINIMIZE
        elif text_upper.startswith('MAXIMIZAR:'):
            expr_type = ExpressionType.OBJECTIVE
            op_type = OperationType.MAXIMIZE
        elif any(op in text for op in ['<=', '>=', '==', '!=', '<', '>', '=']):
            expr_type = ExpressionType.CONSTRAINT
            op_type = OperationType.LESS_EQUAL
        else:
            expr_type = ExpressionType.MATHEMATICAL
            op_type = OperationType.ADDITION
        
        return Expression(
            original_text=text,
            python_code=text.replace('MINIMIZAR:', '').replace('MAXIMIZAR:', '').strip(),
            expression_type=expr_type,
            operation_type=op_type
        )
