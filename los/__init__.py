"""
🚀 LOS - Linguagem de Otimização Simples
Arquitetura modular baseada em Clean Architecture
"""

__version__ = "2.0.0"
__author__ = "Jonathan Pereira"
__email__ = "jonathan@example.com"

# Principais interfaces públicas
from .domain.entities.expression import Expression
from .domain.value_objects.expression_types import (
    ExpressionType, 
    OperationType,
    Variable,
    DatasetReference
)
from .application.services.expression_service import ExpressionService
from .application.dto.expression_dto import (
    ExpressionRequestDTO,
    ExpressionResponseDTO
)

# Adaptadores principais
from .infrastructure.parsers.los_parser import LOSParser
from .infrastructure.translators.pulp_translator import PuLPTranslator
from .infrastructure.validators.los_validator import LOSValidator
from .adapters.file.los_file_processor import LOSFileProcessor

# Utilitários
from .shared.logging.logger import get_logger
from .shared.errors.exceptions import (
    LOSError,
    ParseError,
    ValidationError,
    TranslationError
)

__all__ = [
    # Core entities
    "Expression",
    "ExpressionType",
    "OperationType", 
    "Variable",
    "DatasetReference",
    
    # Services
    "ExpressionService",
    
    # DTOs
    "ExpressionRequestDTO",
    "ExpressionResponseDTO",
    
    # Infrastructure
    "LOSParser",
    "PuLPTranslator", 
    "LOSValidator",
    "LOSFileProcessor",
    
    # Utilities
    "get_logger",
    "LOSError",
    "ParseError",
    "ValidationError",
    "TranslationError"
]
