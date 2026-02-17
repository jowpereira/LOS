"""Objetos de Valor do Domínio."""

from enum import Enum
from dataclasses import dataclass
from typing import Set, FrozenSet
from abc import ABC


class ExpressionType(Enum):
    """Tipos de expressão."""
    OBJECTIVE = "objective"
    CONSTRAINT = "constraint"  
    CONDITIONAL = "conditional"
    MATHEMATICAL = "mathematical"
    AGGREGATION = "aggregation"
    MODEL = "model"


class OperationType(Enum):
    """Tipos de operação."""
    MINIMIZE = "minimize"
    MAXIMIZE = "maximize"
    LESS_EQUAL = "less_equal"
    GREATER_EQUAL = "greater_equal"
    EQUAL = "equal"
    NOT_EQUAL = "not_equal"
    LESS = "less"
    GREATER = "greater"
    ADDITION = "addition"
    SUBTRACTION = "subtraction"
    MULTIPLICATION = "multiplication"
    DIVISION = "division"
    POWER = "power"
    IF_THEN_ELSE = "if_then_else"
    AND_LOGIC = "and"
    OR_LOGIC = "or"
    NOT_LOGIC = "not"


class FunctionType(Enum):
    """Funções matemáticas."""
    ABS = "abs"
    MAX = "max"
    MIN = "min"
    SUM = "sum"
    SQRT = "sqrt"
    
    
@dataclass(frozen=True)
class Variable:
    """Variável de decisão."""
    name: str
    indices: tuple = ()
    variable_type: str = "continuous"
    
    def __post_init__(self):
        if not self.name or not self.name.isidentifier():
            raise ValueError(f"Nome de variável inválido: {self.name}")
    
    @property
    def is_indexed(self) -> bool:
        """Verifica se variável é indexada."""
        return len(self.indices) > 0
    
    @property 
    def dimensions(self) -> int:
        """Número de dimensões."""
        return len(self.indices)
    
    def to_python_code(self) -> str:
        """Converte para string Python."""
        if self.is_indexed:
            indices_str = ",".join(str(idx) for idx in self.indices)
            return f"{self.name}[{indices_str}]"
        return self.name


@dataclass(frozen=True)
class DatasetReference:
    """Referência a dataset externo."""
    dataset_name: str
    column_name: str
    
    def __post_init__(self):
        if not self.dataset_name or not self.column_name:
            raise ValueError("Dataset e coluna devem ser especificados")
    
    def to_python_code(self) -> str:
        """Converte para string Python."""
        # Tratar colunas com espaços
        if ' ' in self.column_name or "'" in self.column_name:
            return f"{self.dataset_name}['{self.column_name}']"
        return f"{self.dataset_name}.{self.column_name}"


@dataclass(frozen=True)
class ComplexityMetrics:
    """Métricas de complexidade."""
    nesting_level: int = 1
    variable_count: int = 0
    operation_count: int = 0
    function_count: int = 0
    conditional_count: int = 0
    
    @property
    def total_complexity(self) -> int:
        """Calcula complexidade total."""
        return (
            self.nesting_level +
            self.variable_count + 
            self.operation_count * 2 +
            self.function_count * 3 +
            self.conditional_count * 4
        )
    
    @property
    def complexity_level(self) -> str:
        """Nível de complexidade (BAIXA, MÉDIA, ALTA...)."""
        if self.total_complexity <= 5:
            return "BAIXA"
        elif self.total_complexity <= 15:
            return "MÉDIA"
        elif self.total_complexity <= 30:
            return "ALTA"
        else:
            return "MUITO_ALTA"
