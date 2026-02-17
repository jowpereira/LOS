"""Orquestra o pipeline parse → translate → LOSModel."""

from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..domain.entities.los_model import LOSModel
from ..domain.entities.expression import Expression
from ..domain.value_objects.expression_types import ExpressionType
from ..infrastructure.parsers.los_parser import LOSParser
from ..infrastructure.translators.pulp_translator import PuLPTranslator
from ..application.services.data_binding_service import DataBindingService
from ..shared.errors.exceptions import LOSError, ParseError
from ..shared.logging.logger import get_logger

_logger = get_logger(__name__)

# Singletons
_parser = LOSParser()
_translator = PuLPTranslator()
_binding_service = DataBindingService()


def compile_model(source: str, data: Optional[Dict[str, Any]] = None) -> LOSModel:
    """Compila fonte LOS em um LOSModel (com dados opcionais)."""
    source_text, base_dir = _resolve_source_and_path(source)


    _logger.info("Compilando modelo LOS...")
    parse_result = _parser.parse(source_text)

    if not parse_result.get('success'):
        errors = parse_result.get('errors', ['Erro desconhecido no parsing'])
        raise ParseError(f"Falha no parsing: {'; '.join(str(e) for e in errors)}", source_text)

    ast = parse_result['parsed_result']
    variables = parse_result.get('variables', [])
    datasets = parse_result.get('datasets', [])
    complexity = parse_result.get('complexity')


    bound_data = _binding_service.bind_data(ast, data, base_dir=base_dir)

    # Bridge para translator
    expression = Expression(original_text=source_text)
    expression.syntax_tree = ast
    expression.expression_type = ExpressionType.MODEL

    for var in variables:
        expression.add_variable(var)

    # Traduzir para PuLP
    python_code = _translator.translate_expression(expression)

    # Construir LOSModel
    model_name = ast.get('name', 'LOS_Model')

    model = LOSModel(
        source=source_text,
        ast=ast,
        python_code=python_code,
        variables=variables,
        datasets=datasets,
        complexity=complexity,
        name=model_name,
        bound_data=bound_data
    )

    _logger.info(f"Modelo compilado: {model}")
    return model


def _resolve_source_and_path(source: str) -> Tuple[str, Path]:
    """Resolve fonte: lê arquivo ou retorna texto inline."""
    path = Path(source)
    

    if '\n' in source or '\r' in source:
        return source, Path.cwd()

    # Verificar se arquivo existe (tenta extensões conhecidas)
    is_file = False
    if path.suffix.lower() in ('.los', '.txt', '.mod'):
        if path.exists(): is_file = True
    elif path.exists() and path.is_file():
        is_file = True
        
    if is_file:
         _logger.info(f"Lendo modelo de: {path}")
         return path.read_text(encoding='utf-8'), path.parent.absolute()

    # Fallback: assume que é texto inline (ex: oneliner "min: x")
    return source, Path.cwd()
