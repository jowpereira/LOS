"""
🚀 LOS - Linguagem de Otimização Simples
Arquitetura modular baseada em Clean Architecture
"""

__version__ = "3.2.0"
__author__ = "Jonathan Pereira"
__email__ = "lethanconsultoria@gmail.com"

# ═══════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════

from .application.compiler import compile_model
from .domain.entities.los_model import LOSModel
from .domain.entities.los_result import LOSResult


def compile(source, data=None):
    """
    Compila um modelo LOS a partir de texto ou caminho de arquivo.

    Args:
        source: Texto LOS ou caminho para .los file
        data: Dicionário de DataFrames (reservado Phase 2)

    Returns:
        LOSModel compilado, pronto para .solve()

    Example:
        >>> model = los.compile("min: x\\nst:\\n  c1: x >= 5\\nvar x >= 0")
        >>> model = los.compile("modelos/supply_chain_network.los")
    """
    return compile_model(source, data)


def solve(source, data=None, **kwargs):
    """
    Atalho: compila e resolve em um passo.

    Args:
        source: Texto LOS ou caminho para .los file
        data: Dicionário de DataFrames (reservado Phase 2)
        **kwargs: Argumentos passados para LOSModel.solve()

    Returns:
        LOSResult com status, objective, variables, time

    Example:
        >>> result = los.solve("min: x\\nst:\\n  c1: x >= 5\\nvar x >= 0")
        >>> print(result.objective)  # 5.0
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
