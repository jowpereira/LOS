"""Interfaces para repositórios."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from uuid import UUID

from ..entities.expression import Expression


class IExpressionRepository(ABC):
    """Interface para repositório de expressões."""
    
    @abstractmethod
    def save(self, expression: Expression) -> Expression:
        """Salva uma expressão."""
        pass
    
    @abstractmethod
    def find_by_id(self, expression_id: UUID) -> Optional[Expression]:
        """Busca expressão por ID."""
        pass
    
    @abstractmethod
    def find_by_type(self, expression_type: str) -> List[Expression]:
        """Busca expressões por tipo."""
        pass
    
    @abstractmethod
    def find_all(self) -> List[Expression]:
        """Retorna todas as expressões."""
        pass
    
    @abstractmethod
    def delete(self, expression_id: UUID) -> bool:
        """Remove uma expressão."""
        pass
    
    @abstractmethod
    def count(self) -> int:
        """Conta total de expressões."""
        pass


class IGrammarRepository(ABC):
    """Interface de repositório de gramáticas."""
    
    @abstractmethod
    def load_grammar(self, grammar_name: str = "los_grammar") -> str:
        """Carrega gramática por nome."""
        pass
    
    @abstractmethod
    def save_grammar(self, grammar_name: str, content: str) -> bool:
        """Salva uma gramática."""
        pass
    
    @abstractmethod
    def list_grammars(self) -> List[str]:
        """Lista gramáticas disponíveis."""
        pass


class IDatasetRepository(ABC):
    """Interface de repositório de datasets."""
    
    @abstractmethod
    def load_dataset(self, dataset_name: str) -> Dict[str, Any]:
        """Carrega dataset por nome."""
        pass
    
    @abstractmethod
    def save_dataset(self, dataset_name: str, data: Dict[str, Any]) -> bool:
        """Salva um dataset."""
        pass
    
    @abstractmethod
    def list_datasets(self) -> List[str]:
        """Lista datasets disponíveis."""
        pass
    
    @abstractmethod
    def get_dataset_schema(self, dataset_name: str) -> Dict[str, str]:
        """Retorna schema de um dataset."""
        pass
