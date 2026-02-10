"""
🔧 LOS Compiler — Orquestra o pipeline parse → translate → LOSModel

A01: Ponto de entrada para `los.compile()`.
Aceita texto LOS ou caminho para arquivo .los.
"""

from pathlib import Path
from typing import Any, Dict, Optional

from ..domain.entities.los_model import LOSModel
from ..domain.entities.expression import Expression
from ..domain.value_objects.expression_types import ExpressionType
from ..infrastructure.parsers.los_parser import LOSParser
from ..infrastructure.translators.pulp_translator import PuLPTranslator
from ..shared.errors.exceptions import LOSError, ParseError
from ..shared.logging.logger import get_logger

_logger = get_logger(__name__)

# Singletons reutilizáveis (thread-safe pois parse() cria transformer novo)
_parser = LOSParser()
_translator = PuLPTranslator()


def compile_model(source: str, data: Optional[Dict[str, Any]] = None) -> LOSModel:
    """
    Compila fonte LOS em um LOSModel pronto para resolver.

    Args:
        source: Texto LOS ou caminho para arquivo .los/.txt
        data: Dicionário de DataFrames para binding (Phase 2, reservado)

    Returns:
        LOSModel compilado com AST e código PuLP gerado

    Raises:
        ParseError: Se o texto LOS contém erros de sintaxe
        LOSError: Se ocorrer erro na compilação
    """
    # Detectar se é arquivo ou texto inline
    source_text = _resolve_source(source)

    # 1. Parse
    _logger.info("Compilando modelo LOS...")
    parse_result = _parser.parse(source_text)

    if not parse_result.get('success'):
        errors = parse_result.get('errors', ['Erro desconhecido no parsing'])
        raise ParseError(f"Falha no parsing: {'; '.join(str(e) for e in errors)}", source_text)

    ast = parse_result['parsed_result']
    variables = parse_result.get('variables', [])
    datasets = parse_result.get('datasets', [])
    complexity = parse_result.get('complexity')

    # 2. Criar Expression intermediária (bridge para o translator)
    expression = Expression(original_text=source_text)
    expression.syntax_tree = ast
    expression.expression_type = ExpressionType.MODEL

    for var in variables:
        expression.add_variable(var)

    # 3. Translate para PuLP
    python_code = _translator.translate_expression(expression)

    # 4. Construir LOSModel
    model_name = ast.get('name', 'LOS_Model')

    model = LOSModel(
        source=source_text,
        ast=ast,
        python_code=python_code,
        variables=variables,
        datasets=datasets,
        complexity=complexity,
        name=model_name
    )

    _logger.info(f"Modelo compilado: {model}")
    return model


def _resolve_source(source: str) -> str:
    """
    Resolve fonte: se for caminho de arquivo, lê o conteúdo.
    Se for texto LOS puro, retorna como está.
    """
    # Multi-line text is NEVER a file path
    if '\n' in source or '\r' in source:
        return source

    # Single-line: check if it looks like a file path
    path = Path(source)

    if path.suffix.lower() in ('.los', '.txt', '.mod'):
        if not path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {source}")
        _logger.info(f"Lendo modelo de: {path}")
        return path.read_text(encoding='utf-8')

    # Try as file if it exists on disk
    try:
        if path.exists() and path.is_file():
            _logger.info(f"Lendo modelo de: {path}")
            return path.read_text(encoding='utf-8')
    except (OSError, ValueError):
        pass  # Not a valid path, treat as inline text

    # Fallback: it's inline text
    return source
