"""Interfaces para adaptadores."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ...domain.entities.expression import Expression

from ..dto.expression_dto import (
    ExpressionRequestDTO,
    ExpressionResponseDTO,
    TranslationRequestDTO,
    TranslationResponseDTO,
    ValidationRequestDTO,
    ValidationResponseDTO
)


class IParserAdapter(ABC):
    """Interface de parser."""
    
    @abstractmethod
    def parse(self, text: str) -> Any:
        """Realiza parsing de texto."""
        pass
    
    @abstractmethod
    def validate_syntax(self, text: str) -> bool:
        """Valida sintaxe do texto."""
        pass


class ITranslatorAdapter(ABC):
    """Interface de tradução."""
    
    @abstractmethod
    def translate(self, request: TranslationRequestDTO) -> TranslationResponseDTO:
        """Traduz expressão via DTO (legacy)"""
        pass
    
    @abstractmethod
    def translate_expression(self, expression: 'Expression') -> str:
        """Traduz entidade Expression para código alvo."""
        pass
    
    @abstractmethod
    def get_supported_languages(self) -> List[str]:
        """Retorna linguagens suportadas."""
        pass


class IValidatorAdapter(ABC):
    """Interface de validação."""
    
    @abstractmethod
    def validate(self, request: ValidationRequestDTO) -> ValidationResponseDTO:
        """Valida expressão segundo regras específicas."""
        pass
    
    @abstractmethod
    def get_available_rules(self) -> List[str]:
        """Retorna regras de validação disponíveis."""
        pass


class ICacheAdapter(ABC):
    """Interface de cache."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Recupera valor do cache."""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Armazena valor no cache (ttl opcional)."""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Remove valor do cache."""
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        """Limpa todo o cache."""
        pass


class IFileAdapter(ABC):
    """Interface de arquivos."""
    
    @abstractmethod
    def read_file(self, file_path: str, encoding: str = "utf-8") -> str:
        """Lê conteúdo de arquivo."""
        pass
    
    @abstractmethod
    def write_file(
        self, 
        file_path: str, 
        content: str, 
        encoding: str = "utf-8"
    ) -> bool:
        """Escreve conteúdo em arquivo."""
        pass
    
    @abstractmethod
    def file_exists(self, file_path: str) -> bool:
        """Verifica se arquivo existe."""
        pass


class INotificationAdapter(ABC):
    """Interface de notificação."""
    
    @abstractmethod
    def send_notification(
        self,
        message: str,
        level: str = "info",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Envia notificação."""
        pass
