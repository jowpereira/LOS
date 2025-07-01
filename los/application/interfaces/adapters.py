"""
🔌 Application Interfaces
Interfaces para adaptadores externos e infraestrutura
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ..dto.expression_dto import (
    ExpressionRequestDTO,
    ExpressionResponseDTO,
    TranslationRequestDTO,
    TranslationResponseDTO,
    ValidationRequestDTO,
    ValidationResponseDTO
)


class IParserAdapter(ABC):
    """Interface para adaptadores de parser"""
    
    @abstractmethod
    async def parse(self, text: str) -> Any:
        """
        Realiza parsing de texto
        
        Args:
            text: Texto a ser analisado
            
        Returns:
            Árvore sintática ou estrutura de dados resultante
        """
        pass
    
    @abstractmethod
    async def validate_syntax(self, text: str) -> bool:
        """
        Valida sintaxe do texto
        
        Args:
            text: Texto a ser validado
            
        Returns:
            True se sintaxe válida
        """
        pass


class ITranslatorAdapter(ABC):
    """Interface para adaptadores de tradução"""
    
    @abstractmethod
    async def translate(self, request: TranslationRequestDTO) -> TranslationResponseDTO:
        """
        Traduz expressão para linguagem alvo
        
        Args:
            request: Dados da requisição de tradução
            
        Returns:
            Resultado da tradução
        """
        pass
    
    @abstractmethod
    def get_supported_languages(self) -> List[str]:
        """
        Retorna linguagens suportadas
        
        Returns:
            Lista de linguagens suportadas
        """
        pass


class IValidatorAdapter(ABC):
    """Interface para adaptadores de validação"""
    
    @abstractmethod
    async def validate(self, request: ValidationRequestDTO) -> ValidationResponseDTO:
        """
        Valida expressão segundo regras específicas
        
        Args:
            request: Dados da requisição de validação
            
        Returns:
            Resultado da validação
        """
        pass
    
    @abstractmethod
    def get_available_rules(self) -> List[str]:
        """
        Retorna regras de validação disponíveis
        
        Returns:
            Lista de regras disponíveis
        """
        pass


class ICacheAdapter(ABC):
    """Interface para adaptadores de cache"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """
        Recupera valor do cache
        
        Args:
            key: Chave do cache
            
        Returns:
            Valor armazenado ou None
        """
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Armazena valor no cache
        
        Args:
            key: Chave do cache
            value: Valor a ser armazenado
            ttl: Time to live em segundos
            
        Returns:
            True se armazenado com sucesso
        """
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Remove valor do cache
        
        Args:
            key: Chave a ser removida
            
        Returns:
            True se removida com sucesso
        """
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """
        Limpa todo o cache
        
        Returns:
            True se limpo com sucesso
        """
        pass


class IFileAdapter(ABC):
    """Interface para adaptadores de arquivo"""
    
    @abstractmethod
    async def read_file(self, file_path: str, encoding: str = "utf-8") -> str:
        """
        Lê conteúdo de arquivo
        
        Args:
            file_path: Caminho do arquivo
            encoding: Codificação do arquivo
            
        Returns:
            Conteúdo do arquivo
        """
        pass
    
    @abstractmethod
    async def write_file(
        self, 
        file_path: str, 
        content: str, 
        encoding: str = "utf-8"
    ) -> bool:
        """
        Escreve conteúdo em arquivo
        
        Args:
            file_path: Caminho do arquivo
            content: Conteúdo a ser escrito
            encoding: Codificação do arquivo
            
        Returns:
            True se escrito com sucesso
        """
        pass
    
    @abstractmethod
    async def file_exists(self, file_path: str) -> bool:
        """
        Verifica se arquivo existe
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            True se arquivo existe
        """
        pass


class INotificationAdapter(ABC):
    """Interface para adaptadores de notificação"""
    
    @abstractmethod
    async def send_notification(
        self,
        message: str,
        level: str = "info",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Envia notificação
        
        Args:
            message: Mensagem da notificação
            level: Nível (info, warning, error)
            metadata: Metadados adicionais
            
        Returns:
            True se enviada com sucesso
        """
        pass
