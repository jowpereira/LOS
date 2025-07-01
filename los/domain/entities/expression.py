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
from ...shared.errors.exceptions import ValidationError, BusinessRuleError


@dataclass
class Expression:
    """
    Entidade central que representa uma expressão LOS analisada
    
    Implementa invariantes de negócio e encapsula comportamentos essenciais
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
    syntax_tree: Optional[Any] = None  # Árvore sintática do Lark
    
    # Status de validação
    is_valid: bool = False
    validation_errors: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validações pós-inicialização"""
        self._validate_invariants()
    
    def _validate_invariants(self):
        """Valida invariantes de negócio da entidade"""
        errors = []
        
        # Texto original deve estar presente
        if not self.original_text.strip():
            errors.append("Texto original da expressão não pode estar vazio")
        
        # Para objetivos, deve ter pelo menos uma variável
        if (self.expression_type == ExpressionType.OBJECTIVE and 
            len(self.variables) == 0):
            errors.append("Objetivos devem conter pelo menos uma variável")
        
        # Operações de comparação só em restrições
        comparison_ops = {
            OperationType.LESS, OperationType.GREATER,
            OperationType.LESS_EQUAL, OperationType.GREATER_EQUAL,
            OperationType.EQUAL, OperationType.NOT_EQUAL
        }
        
        if (self.operation_type in comparison_ops and 
            self.expression_type not in [ExpressionType.CONSTRAINT, ExpressionType.CONDITIONAL]):
            errors.append(f"Operação {self.operation_type.value} só é válida em restrições e condicionais")
        
        if errors:
            self.validation_errors.extend(errors)
            self.is_valid = False
            raise BusinessRuleError(
                message=f"Violação de regras de negócio: {'; '.join(errors)}",
                rule_name="expression_invariants",
                violated_constraints=errors
            )
        else:
            self.is_valid = True
    
    def add_variable(self, variable: Variable):
        """
        Adiciona uma variável à expressão
        
        Args:
            variable: Variável a ser adicionada
        """
        if not isinstance(variable, Variable):
            raise ValidationError(
                message="Objeto deve ser instância de Variable",
                field="variable"
            )
        
        self.variables.add(variable)
        self._update_complexity()
    
    def add_dataset_reference(self, reference: DatasetReference):
        """
        Adiciona referência a dataset
        
        Args:
            reference: Referência ao dataset
        """
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
            # Outros campos serão atualizados durante o parsing
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
        """Verifica se é expressão de objetivo"""
        return self.expression_type == ExpressionType.OBJECTIVE
    
    def is_constraint(self) -> bool:
        """Verifica se é restrição"""
        return self.expression_type == ExpressionType.CONSTRAINT
    
    def is_conditional(self) -> bool:
        """Verifica se é expressão condicional"""
        return self.expression_type == ExpressionType.CONDITIONAL
    
    def to_pulp_code(self) -> str:
        """
        Converte para código compatível com PuLP
        
        Returns:
            Código Python/PuLP
        """
        if not self.is_valid:
            raise BusinessRuleError(
                message="Não é possível gerar código para expressão inválida",
                rule_name="code_generation",
                violated_constraints=self.validation_errors
            )
        
        if self.is_objective():
            return f"prob += {self.python_code}"
        elif self.is_constraint():
            return f"prob += {self.python_code}"
        else:
            return self.python_code
    
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
        """Representação string da expressão"""
        return f"Expression({self.expression_type.value}: {self.original_text[:50]}...)"
    
    def __repr__(self) -> str:
        """Representação detalhada para debug"""
        return (
            f"Expression(id={self.id}, type={self.expression_type.value}, "
            f"variables={len(self.variables)}, valid={self.is_valid})"
        )
