"""
🏛️ Expression Entity - Entidade Central do Domínio
Representa uma expressão LOS completa com toda sua semântica
"""

from dataclasses import dataclass, field
from typing import Set, Dict, Any, Optional, List
from uuid import uuid4, UUID
from datetime import datetime

from ..value_objects.expression_types import (
    ExpressionType, 
    OperationType,
    Variable,
    DatasetReference,
    ComplexityMetrics
)
from ...shared.errors.exceptions import ValidationError


@dataclass
class Expression:
    """
    Entidade central que representa uma expressão LOS analisada
    
    Implementa invariantes de negócio e encapsula comportamentos essenciais.
    
    NOTA F02: Validation is NOT performed in __post_init__.
    Use Expression.create() factory for validated creation, or set fields
    manually and call validate() explicitly.
    """
    
    # Identificação única
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.now)
    
    # Conteúdo da expressão
    original_text: str = ""
    python_code: str = ""
    
    # Classificação
    expression_type: ExpressionType = ExpressionType.MATHEMATICAL
    operation_type: OperationType = OperationType.ADDITION
    
    # Componentes analisados
    variables: Set[Variable] = field(default_factory=set)
    dataset_references: Set[DatasetReference] = field(default_factory=set)
    
    # Métricas e metadados
    complexity: ComplexityMetrics = field(default_factory=ComplexityMetrics)
    syntax_tree: Optional[Any] = None
    
    # Status de validação
    is_valid: bool = False
    validation_errors: List[str] = field(default_factory=list)
    
    # F02: NO __post_init__ validation. Entity is a data holder.
    # Validation is done explicitly via validate() or by UseCase logic.
    
    @classmethod
    def create(cls, original_text: str, **kwargs) -> 'Expression':
        """
        Factory method that creates and validates an Expression.
        Use this when you want immediate validation.
        """
        expr = cls(original_text=original_text, **kwargs)
        expr.validate()
        return expr
    
    def validate(self) -> bool:
        """
        Validates business invariants and sets is_valid + validation_errors.
        Returns True if valid.
        """
        errors = []
        
        if not self.original_text.strip():
            errors.append("Texto original da expressão não pode estar vazio")
        
        if (self.expression_type == ExpressionType.OBJECTIVE and 
            len(self.variables) == 0):
            errors.append("Objetivos devem conter pelo menos uma variável")
        
        comparison_ops = {
            OperationType.LESS, OperationType.GREATER,
            OperationType.LESS_EQUAL, OperationType.GREATER_EQUAL,
            OperationType.EQUAL, OperationType.NOT_EQUAL
        }
        
        if (self.operation_type in comparison_ops and 
            self.expression_type not in [
                ExpressionType.CONSTRAINT, 
                ExpressionType.CONDITIONAL,
                ExpressionType.MODEL
            ]):
            errors.append(f"Operação {self.operation_type.value} só é válida em restrições e condicionais")
        
        if errors:
            self.validation_errors.extend(errors)
            self.is_valid = False
        else:
            self.is_valid = True
        
        return self.is_valid
    
    def add_variable(self, variable: Variable):
        """Adiciona uma variável à expressão"""
        if not isinstance(variable, Variable):
            raise ValidationError(
                message="Objeto deve ser instância de Variable",
                field="variable"
            )
        self.variables.add(variable)
        self._update_complexity()
    
    def add_dataset_reference(self, reference: DatasetReference):
        """Adiciona referência a dataset"""
        if not isinstance(reference, DatasetReference):
            raise ValidationError(
                message="Objeto deve ser instância de DatasetReference", 
                field="reference"
            )
        self.dataset_references.add(reference)
    
    def _update_complexity(self):
        """Atualiza métricas de complexidade baseado nos componentes"""
        self.complexity = ComplexityMetrics(
            variable_count=len(self.variables),
            nesting_level=self.complexity.nesting_level,
            operation_count=self.complexity.operation_count,
            function_count=self.complexity.function_count,
            conditional_count=self.complexity.conditional_count
        )
    
    def get_variable_names(self) -> Set[str]:
        """Retorna conjunto com nomes das variáveis"""
        return {var.name for var in self.variables}
    
    def get_dataset_names(self) -> Set[str]:
        """Retorna conjunto com nomes dos datasets referenciados"""
        return {ref.dataset_name for ref in self.dataset_references}
    
    def is_objective(self) -> bool:
        return self.expression_type == ExpressionType.OBJECTIVE
    
    def is_constraint(self) -> bool:
        return self.expression_type == ExpressionType.CONSTRAINT
    
    def is_conditional(self) -> bool:
        return self.expression_type == ExpressionType.CONDITIONAL
    
    # F11: Removed dead to_pulp_code(). Translation is handled by Translator.
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte entidade para dicionário para serialização"""
        return {
            'id': str(self.id),
            'created_at': self.created_at.isoformat(),
            'original_text': self.original_text,
            'python_code': self.python_code,
            'expression_type': self.expression_type.value,
            'operation_type': self.operation_type.value,
            'variables': [var.name for var in self.variables],
            'dataset_references': [
                f"{ref.dataset_name}.{ref.column_name}" 
                for ref in self.dataset_references
            ],
            'complexity': {
                'total': self.complexity.total_complexity,
                'level': self.complexity.complexity_level,
                'variables': self.complexity.variable_count,
                'operations': self.complexity.operation_count
            },
            'is_valid': self.is_valid,
            'validation_errors': self.validation_errors
        }
    
    def __str__(self) -> str:
        return f"Expression({self.expression_type.value}: {self.original_text[:50]}...)"
    
    def __repr__(self) -> str:
        return (
            f"Expression(id={self.id}, type={self.expression_type.value}, "
            f"variables={len(self.variables)}, valid={self.is_valid})"
        )
