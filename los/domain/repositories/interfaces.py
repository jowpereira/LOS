"""
📦 Repository Interfaces - Contratos para Persistência
Interfaces que definem contratos para acesso a dados
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from uuid import UUID

from ..entities.expression import Expression


class IExpressionRepository(ABC):
    """
    Interface para repositório de expressões
    Define contrato para persistência de expressões LOS
    """
    
    @abstractmethod
    def save(self, expression: Expression) -> Expression:
        """
        Salva uma expressão
        
        Args:
            expression: Expressão a ser salva
            
        Returns:
            Expressão salva com ID atualizado
        """
        pass
    
    @abstractmethod
    def find_by_id(self, expression_id: UUID) -> Optional[Expression]:
        """
        Busca expressão por ID
        
        Args:
            expression_id: ID da expressão
            
        Returns:
            Expressão encontrada ou None
        """
        pass
    
    @abstractmethod
    def find_by_type(self, expression_type: str) -> List[Expression]:
        """
        Busca expressões por tipo
        
        Args:
            expression_type: Tipo de expressão
            
        Returns:
            Lista de expressões do tipo especificado
        """
        pass
    
    @abstractmethod
    def find_all(self) -> List[Expression]:
        """
        Retorna todas as expressões
        
        Returns:
            Lista com todas as expressões
        """
        pass
    
    @abstractmethod
    def delete(self, expression_id: UUID) -> bool:
        """
        Remove uma expressão
        
        Args:
            expression_id: ID da expressão a ser removida
            
        Returns:
            True se removida com sucesso
        """
        pass
    
    @abstractmethod
    def count(self) -> int:
        """
        Conta total de expressões
        
        Returns:
            Número total de expressões
        """
        pass


class IGrammarRepository(ABC):
    """
    Interface para repositório de gramáticas
    Permite cache e versionamento de gramáticas
    """
    
    @abstractmethod
    def load_grammar(self, grammar_name: str = "los_grammar") -> str:
        """
        Carrega gramática por nome
        
        Args:
            grammar_name: Nome da gramática
            
        Returns:
            Conteúdo da gramática em formato Lark
        """
        pass
    
    @abstractmethod
    def save_grammar(self, grammar_name: str, content: str) -> bool:
        """
        Salva uma gramática
        
        Args:
            grammar_name: Nome da gramática
            content: Conteúdo em formato Lark
            
        Returns:
            True se salva com sucesso
        """
        pass
    
    @abstractmethod
    def list_grammars(self) -> List[str]:
        """
        Lista gramáticas disponíveis
        
        Returns:
            Lista de nomes de gramáticas
        """
        pass


class IDatasetRepository(ABC):
    """
    Interface para repositório de datasets
    Gerencia datasets utilizados nas expressões
    """
    
    @abstractmethod
    def load_dataset(self, dataset_name: str) -> Dict[str, Any]:
        """
        Carrega dataset por nome
        
        Args:
            dataset_name: Nome do dataset
            
        Returns:
            Dados do dataset
        """
        pass
    
    @abstractmethod
    def save_dataset(self, dataset_name: str, data: Dict[str, Any]) -> bool:
        """
        Salva um dataset
        
        Args:
            dataset_name: Nome do dataset
            data: Dados a serem salvos
            
        Returns:
            True se salvo com sucesso
        """
        pass
    
    @abstractmethod
    def list_datasets(self) -> List[str]:
        """
        Lista datasets disponíveis
        
        Returns:
            Lista de nomes de datasets
        """
        pass
    
    @abstractmethod
    def get_dataset_schema(self, dataset_name: str) -> Dict[str, str]:
        """
        Retorna schema de um dataset
        
        Args:
            dataset_name: Nome do dataset
            
        Returns:
            Schema com tipos das colunas
        """
        pass
