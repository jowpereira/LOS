"""Parser modularizado baseado em Lark."""

import re
import ast
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from lark import Lark, Transformer, Tree, Token
from lark.exceptions import LarkError, ParseError, LexError

from ...application.interfaces.adapters import IParserAdapter
from ...domain.entities.expression import Expression
from ...domain.value_objects.expression_types import (
    ExpressionType,
    OperationType,
    Variable,
    DatasetReference,
    ComplexityMetrics
)
from ...shared.errors.exceptions import ParseError as LOSParseError
from ...shared.logging.logger import get_logger


class LOSTransformer(Transformer):
    """Transformer Lark para LOS v3."""
    
    def __init__(self):
        super().__init__()
        self.variables_found: Set[Variable] = set()
        self.datasets_found: Set[DatasetReference] = set()
        self.complexity_metrics = {
            'nesting_level': 1,
            'operation_count': 0,
            'function_count': 0,
            'conditional_count': 0
        }
        self._logger = get_logger('infrastructure.parser.transformer')

    def start(self, items):
        """Retorna lista de statements."""
        return {
            'type': 'model',
            'statements': items
        }

    # --- IMPORTS ---
    def import_model(self, items):
        path_node = items[0]
        path = path_node.get('value') if isinstance(path_node, dict) else str(path_node).strip('"\'')
        return {'type': 'import', 'path': path}

    # --- SETS ---
    def set_declaration(self, items):
        name = str(items[0])
        value = items[1] if len(items) > 1 else None
        return {'type': 'set', 'name': name, 'value': value}

    def set_literal(self, items):
        elements = items[0] if items and items[0] else []
        return {'type': 'set_literal', 'elements': elements}

    def set_range(self, items):
        return {'type': 'set_range', 'start': items[0], 'end': items[1]}
    
    def set_range_step(self, items):
        return {'type': 'set_range', 'start': items[0], 'end': items[1], 'step': items[2]}

    def set_filter(self, items):
        return {'type': 'set_filter', 'expression': items[0], 'source': str(items[1]), 'condition': items[2] if len(items) > 2 else None}
    
    def set_ref(self, items):
        return {'type': 'set_ref', 'name': str(items[0])}

    def set_operation(self, items):
        return {'type': 'set_op', 'left': str(items[0]), 'op': str(items[1]), 'right': str(items[2])}
        
    def set_elements(self, items):
        return items

    def set_op(self, items):
        return str(items[0])

    def _extract_indices(self, indices_item):
        """Extrai nomes dos índices."""
        if not indices_item:
            return None
        
        cleaned = []
        for item in indices_item:
            if isinstance(item, dict) and 'name' in item:
                cleaned.append(item['name'])
            elif hasattr(item, 'value'): # Token?
                cleaned.append(str(item.value))
            else:
                cleaned.append(str(item))
        return cleaned

    # --- PARAMETERS ---
    def param_declaration(self, items):
        name = str(items[0])
        indices = None
        value = None
        
        for item in items[1:]:
            if isinstance(item, list): 
                indices = self._extract_indices(item)
            else: 
                value = item
        
        return {'type': 'param', 'name': name, 'indices': indices, 'value': value}

    # --- VARIABLES ---
    def var_declaration(self, items):
        name = str(items[0])
        indices = None
        var_type = 'continuous'
        bounds = None

        current_idx = 1
        # Check for indices (list)
        if current_idx < len(items) and isinstance(items[current_idx], list):
            indices = self._extract_indices(items[current_idx])
            current_idx += 1
        
        # Check for type (string from var_type)
        if current_idx < len(items) and isinstance(items[current_idx], str) and items[current_idx] in ['int', 'bin', 'continuous', 'inteiro', 'binario', 'continua']:
            var_type = items[current_idx]
            current_idx += 1
            
        # Check for bounds (dict)
        if current_idx < len(items):
            bounds = items[current_idx]

        # Register variable
        self.variables_found.add(Variable(name=name, indices=tuple(indices) if indices else ()))
        
        return {'type': 'var', 'name': name, 'indices': indices, 'var_type': var_type, 'bounds': bounds}

    def var_type(self, items):
        return str(items[0])

    def bounds_ge_le(self, items):
        # items: [GE, expr, (LE, expr)?]
        # or [GE, expr]
        # Filter out tokens to get expressions
        exprs = [x for x in items if not isinstance(x, Token)]
        return {'lower': exprs[0], 'upper': exprs[1] if len(exprs) > 1 else None}
    
    def bounds_le_ge(self, items):
        # items: [LE, expr, (GE, expr)?]
        exprs = [x for x in items if not isinstance(x, Token)]
        return {'upper': exprs[0], 'lower': exprs[1] if len(exprs) > 1 else None}
    
    def bounds_eq(self, items):
        # items: [EQ, expr]
        exprs = [x for x in items if not isinstance(x, Token)]
        return {'equal': exprs[0]}
    
    def bounds_in_set(self, items):
        return {'set': items[0]}

    # --- OBJECTIVE ---
    def objective_decl(self, items):
        self.complexity_metrics['operation_count'] += 1
        return {'type': 'objective', 'sense': items[0], 'expression': items[1]}

    def obj_sense(self, items):
        sense_map = {
            'min': 'minimize', 'minimize': 'minimize', 'minimizar': 'minimize',
            'max': 'maximize', 'maximize': 'maximize', 'maximizar': 'maximize'
        }
        return sense_map.get(str(items[0]).lower(), 'minimize')

    # --- CONSTRAINTS ---
    def constraint_block(self, items):
        return {'type': 'constraint_block', 'constraints': items}

    def constraint_single(self, items):
        return {'type': 'constraint_block', 'constraints': [items[0]]}

    def constraint_named(self, items):
        name = None
        indices = None
        expr = None
        loops = None
        
        idx = 0
        # Verificar nome opcional
        first = items[0]
        if isinstance(first, Token) and first.type == 'IDENTIFICADOR':
             name = str(first)
             idx += 1
             if idx < len(items) and isinstance(items[idx], list): # indices
                 indices = self._extract_indices(items[idx])
                 idx += 1
        
        if idx < len(items):
            expr = items[idx]
            idx += 1
        if idx < len(items):
            loops = items[idx]
            
        return {'type': 'constraint', 'name': name, 'indices': indices, 'expression': expr, 'loops': loops}

    # --- EXPRESSIONS & LOGIC ---
    def add(self, items):
        self.complexity_metrics['operation_count'] += 1
        return {'type': 'binary_op', 'op': '+', 'left': items[0], 'right': items[1]}
    def sub(self, items):
        self.complexity_metrics['operation_count'] += 1
        return {'type': 'binary_op', 'op': '-', 'left': items[0], 'right': items[1]}
    def mul(self, items):
        self.complexity_metrics['operation_count'] += 1
        return {'type': 'binary_op', 'op': '*', 'left': items[0], 'right': items[1]}
    def div(self, items):
        self.complexity_metrics['operation_count'] += 1
        return {'type': 'binary_op', 'op': '/', 'left': items[0], 'right': items[1]}
    def mod(self, items):
        self.complexity_metrics['operation_count'] += 1
        return {'type': 'binary_op', 'op': '%', 'left': items[0], 'right': items[1]}
    def pow(self, items):
        self.complexity_metrics['operation_count'] += 1
        return {'type': 'binary_op', 'op': '^', 'left': items[0], 'right': items[1]}
    
    def number(self, items): return {'type': 'number', 'value': float(items[0])}
    
    def string_literal(self, items): 
        # F21: Use ast.literal_eval
        try:
            val = ast.literal_eval(str(items[0]))
        except:
             # Fallback if literal_eval fails (e.g. unexpected format), though parser should guarantee string
             val = str(items[0])[1:-1]
        return {'type': 'string', 'value': val}
    
    def var_or_param(self, items):
        name = str(items[0])
        return {'type': 'var_ref', 'name': name}
        
    def dataset_coluna(self, items):
        ref = DatasetReference(dataset_name=str(items[0]), column_name=str(items[1]))
        self.datasets_found.add(ref)
        return {'type': 'dataset_col', 'dataset': str(items[0]), 'col': str(items[1])}

    def indexed_var(self, items):
        name = str(items[0])
        indices = items[1]
        return {'type': 'indexed_var', 'name': name, 'indices': indices}

    def or_op(self, items): return {'type': 'logic_op', 'op': 'or', 'left': items[0], 'right': items[1]}
    def and_op(self, items): return {'type': 'logic_op', 'op': 'and', 'left': items[0], 'right': items[1]}
    def not_op(self, items): return {'type': 'logic_op', 'op': 'not', 'expr': items[0]}
    
    def logic_comp(self, items):
        if len(items) == 3:
            return {'type': 'comparison', 'op': items[1], 'left': items[0], 'right': items[2]}
        return items[0]

    def rel_op(self, items): return str(items[0])

    # --- SPECIAL ---
    def sum(self, items):
        expr = None
        loops = None
        for item in items:
            if isinstance(item, dict):
                expr = item
            elif isinstance(item, list):
                loops = item
        return {'type': 'sum', 'expression': expr, 'loops': loops}
    
    def prod(self, items):
        expr = None
        loops = None
        for item in items:
            if isinstance(item, dict):
                expr = item
            elif isinstance(item, list):
                loops = item
        return {'type': 'prod', 'expression': expr, 'loops': loops}
        
    def min_func(self, items): 
        args = [x for x in items if isinstance(x, dict)]
        return {'type': 'function', 'name': 'min', 'args': args}

    def max_func(self, items): 
        args = [x for x in items if isinstance(x, dict)]
        return {'type': 'function', 'name': 'max', 'args': args}
    
    def func_call(self, items):
        # F09: items[0] is identifier, items[1] is args
        self.complexity_metrics['function_count'] += 1
        name = str(items[0])
        args = []
        for item in items[1:]:
            if isinstance(item, list):
                args = item
                break
        return {'type': 'function', 'name': name, 'args': args}
    
    def if_inline(self, items):
        self.complexity_metrics['conditional_count'] += 1
        args = [x for x in items if isinstance(x, dict)]
        if len(args) == 3:
             return {'type': 'if', 'condition': args[0], 'then': args[1], 'else': args[2]}
        return {'type': 'if', 'error': 'Invalid arguments'}

    def loop_multiplo(self, items): 
        return [item for item in items if isinstance(item, dict)]
    
    def loop_simple(self, items):
        var = str(items[0])
        source = items[1]
        condition = items[2] if len(items) > 2 else None
        return {'var': var, 'source': source, 'condition': condition}

    def indices(self, items): return items
    def arguments(self, items): return items


class LOSParser(IParserAdapter):
    """Parser principal para linguagem LOS v3."""
    
    __version__ = "3.3.6"  # F19: Version tracking
    
    def __init__(self, grammar_file: Optional[str] = None):
        self._grammar_file = grammar_file or self._get_default_grammar_path()
        self._parser = None
        self._logger = get_logger('infrastructure.parser.los')
        self._initialize_parser()
    
    def _get_default_grammar_path(self) -> str:
        current_dir = Path(__file__).parent
        los_root = current_dir.parent.parent
        return str(los_root / "los_grammar.lark")
    
    def _initialize_parser(self):
        try:
            if not Path(self._grammar_file).exists():
                raise FileNotFoundError(f"Arquivo de gramática não encontrado: {self._grammar_file}")
            
            with open(self._grammar_file, 'r', encoding='utf-8') as f:
                grammar_content = f.read()
            
            self._parser = Lark(
                grammar_content,
                start='start',
                parser='lalr',
                transformer=None
            )
            
        except Exception as e:
            self._logger.error(f"Erro inicializando parser: {e}")
            raise LOSParseError(f"Falha ao inicializar parser: {str(e)}", "", e)
    
    def parse(self, text: str) -> Dict[str, Any]:
        # F01: Fresh transformer per call
        transformer = LOSTransformer()
        try:
            cleaned_text = text.strip()
            
            syntax_tree = self._parser.parse(cleaned_text)
            result = transformer.transform(syntax_tree)
            
            parse_result = {
                'original_text': text,
                'parsed_result': result,
                'variables': list(transformer.variables_found),
                'datasets': list(transformer.datasets_found),
                'complexity': transformer.complexity_metrics,
                'success': True
            }
            
            return parse_result
            
        except (ParseError, LexError) as e:
            raise LOSParseError(f"Erro de sintaxe: {e}", text, e)
        except Exception as e:
            raise LOSParseError(f"Erro interno: {str(e)}", text, e)
    
    def validate_syntax(self, text: str) -> bool:
        try:
            self._parser.parse(text.strip())
            return True
        except (ParseError, LexError):
            return False
        except Exception:
            return False

    def get_grammar_content(self) -> str:
        try:
            with open(self._grammar_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return ""
    
    def get_version(self) -> str:
        return self.__version__
