"""
🚀 LOS - Linguagem de Otimização Simples
Arquitetura modular baseada em Clean Architecture
"""

__version__ = "3.3.1"
__author__ = "Jonathan Pereira"
__email__ = "lethanconsultoria@gmail.com"

# ═══════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════

from typing import Any, Dict, Optional

from .application.compiler import compile_model
from .domain.entities.los_model import LOSModel
from .domain.entities.los_result import LOSResult


def compile(source: str, data: Optional[Dict[str, Any]] = None) -> LOSModel:
    """
    Compila um modelo LOS.
    
    Args:
        source: Texto do modelo ou caminho para arquivo .los
        data: Dicionário de dados (DataFrames, dicts) para preencher parâmetros
        
    Returns:
        LOSModel pronto para execução
    """
    return compile_model(source, data)


def solve(source: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> LOSResult:
    """
    Compila e resolve um modelo LOS em um passo.
    
    Args:
        source: Texto do modelo ou caminho para arquivo .los
        data: Dados para preencher parâmetros
        **kwargs: Argumentos para o solver (time_limit, msg, etc)
        
    Returns:
        LOSResult com a solução
    """
    return compile_model(source, data).solve(**kwargs)


# ═══════════════════════════════════════════════════════════════════
# DOMAIN ENTITIES & VALUE OBJECTS
# ═══════════════════════════════════════════════════════════════════

from .domain.entities.expression import Expression
from .domain.value_objects.expression_types import (
    ExpressionType, 
    OperationType,
    Variable,
    DatasetReference
)

# ═══════════════════════════════════════════════════════════════════
# APPLICATION SERVICES
# ═══════════════════════════════════════════════════════════════════

from .application.services.expression_service import ExpressionService
from .application.dto.expression_dto import (
    ExpressionRequestDTO,
    ExpressionResponseDTO
)

# ═══════════════════════════════════════════════════════════════════
# INFRASTRUCTURE (advanced usage)
# ═══════════════════════════════════════════════════════════════════

from .infrastructure.parsers.los_parser import LOSParser
from .infrastructure.translators.pulp_translator import PuLPTranslator
from .infrastructure.validators.los_validator import LOSValidator
from .adapters.file.los_file_processor import LOSFileProcessor

# ═══════════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════════

from .shared.logging.logger import get_logger
from .shared.errors.exceptions import (
    LOSError,
    ParseError,
    ValidationError,
    TranslationError
)

__all__ = [
    # Public API
    "compile",
    "solve",
    "LOSModel",
    "LOSResult",
    
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
