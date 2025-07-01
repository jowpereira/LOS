"""
🔧 LOS Parser - Implementação Lark
Parser modularizado baseado em Lark para a linguagem LOS
"""

import re
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
    """
    Transformer Lark especializado para LOS
    Converte árvore sintática em estruturas de dados
    """
    
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
    
    def objetivo_minimizar(self, items):
        """MINIMIZAR: expressão"""
        expression = str(items[0]) if items else ""
        self.complexity_metrics['operation_count'] += 1
        
        return {
            'type': 'objective',
            'operation': 'minimize',
            'expression': expression,
            'code': expression
        }
    
    def objetivo_maximizar(self, items):
        """MAXIMIZAR: expressão"""
        expression = str(items[0]) if items else ""
        self.complexity_metrics['operation_count'] += 1
        
        return {
            'type': 'objective',
            'operation': 'maximize',
            'expression': expression,
            'code': expression
        }
    
    def expressao_condicional(self, items):
        """SE condição ENTAO expr1 SENAO expr2"""
        if len(items) < 3:
            raise ValueError(f"Expressão condicional malformada: {items}")
        
        condition = str(items[0])
        expr_then = str(items[1])
        expr_else = str(items[2])
        
        self.complexity_metrics['conditional_count'] += 1
        self.complexity_metrics['nesting_level'] += 1
        
        code = f"{expr_then} if {condition} else {expr_else}"
        return {
            'type': 'conditional',
            'operation': 'if_then_else',
            'expression': code,
            'code': code
        }
    
    def operacao_aditiva(self, items):
        """Operações + e -"""
        if len(items) < 3:
            return str(items[0]) if items else ""
        
        left = str(items[0])
        operator = str(items[1])
        right = str(items[2])
        
        self.complexity_metrics['operation_count'] += 1
        
        # Adicionar parênteses se necessário para operações aninhadas
        if ' - ' in right and operator == '-':
            right = f"({right})"
        
        return f"{left} {operator} {right}"
    
    def operacao_multiplicativa(self, items):
        """Operações *, /, //, %"""
        if len(items) < 3:
            return str(items[0]) if items else ""
        
        left = str(items[0])
        operator = str(items[1])
        right = str(items[2])
        
        self.complexity_metrics['operation_count'] += 1
        
        # Adicionar parênteses se necessário para divisão aninhada
        if ' / ' in right and operator == '/':
            right = f"({right})"
        
        return f"{left} {operator} {right}"
    
    def variavel_indexada(self, items):
        """x[i], y[j], transporte[origem,destino]"""
        if len(items) < 2:
            return str(items[0]) if items else ""
        
        name = str(items[0])
        indices_tree = items[1]
        
        # Processar índices
        if hasattr(indices_tree, 'children'):
            indices = []
            for token in indices_tree.children:
                if hasattr(token, 'value'):
                    indices.append(token.value)
                else:
                    indices.append(str(token))
            indices_tuple = tuple(indices)
        else:
            indices_tuple = (str(indices_tree),)
        
        # Criar objeto Variable
        variable = Variable(name=name, indices=indices_tuple)
        self.variables_found.add(variable)
        
        return variable.to_python_code()
    
    def referencia_dataset(self, items):
        """dataset.coluna"""
        if len(items) < 2:
            return str(items[0]) if items else ""
        
        dataset_name = str(items[0])
        column_name = str(items[1])
        
        # Criar referência ao dataset
        dataset_ref = DatasetReference(
            dataset_name=dataset_name,
            column_name=column_name
        )
        self.datasets_found.add(dataset_ref)
        
        return dataset_ref.to_python_code()
    
    def agregacao(self, items):
        """SOMA DE expressao [loops]"""
        if not items:
            return ""
        
        expression = str(items[0])
        loops = str(items[1]) if len(items) > 1 else ""
        
        self.complexity_metrics['function_count'] += 1
        self.complexity_metrics['operation_count'] += 2  # Agregação é mais complexa
        
        if loops:
            return f"sum({expression} {loops})"
        else:
            return f"sum({expression})"
    
    def loop(self, items):
        """PARA CADA var EM dataset [ONDE condicao]"""
        if len(items) < 3:
            return ""
        
        var_name = str(items[0])
        dataset_name = str(items[1])
        condition = str(items[2]) if len(items) > 2 else ""
        
        self.complexity_metrics['operation_count'] += 1
        
        if condition:
            return f"for {var_name} in {dataset_name} if {condition}"
        else:
            return f"for {var_name} in {dataset_name}"
    
    def funcao_matematica(self, items):
        """abs(x), max(a,b), etc."""
        if not items:
            return ""
        
        function_name = str(items[0])
        arguments = str(items[1]) if len(items) > 1 else ""
        
        self.complexity_metrics['function_count'] += 1
        
        # Mapear funções LOS para Python
        function_map = {
            'abs': 'abs',
            'max': 'max',
            'min': 'min',
            'sum': 'sum',
            'sqrt': 'math.sqrt'
        }
        
        python_function = function_map.get(function_name.lower(), function_name)
        return f"{python_function}({arguments})"
    
    def operador_relacional(self, items):
        """Operadores relacionais"""
        if not items:
            return ""
        
        operator = str(items[0])
        
        # Mapear operadores LOS para Python
        operator_map = {
            '<=': '<=',
            '>=': '>=',
            '==': '==',
            '!=': '!=',
            '=': '==',  # LOS usa = como comparação
            '<': '<',
            '>': '>'
        }
        
        return operator_map.get(operator, operator)
    
    def expressao_comparacao(self, items):
        """expr operador expr"""
        if len(items) < 3:
            return str(items[0]) if items else ""
        
        left = str(items[0])
        operator = str(items[1])
        right = str(items[2])
        
        self.complexity_metrics['operation_count'] += 1
        
        return f"{left} {operator} {right}"
    
    def numero(self, items):
        """Números"""
        return str(items[0]) if items else "0"
    
    def string(self, items):
        """Strings"""
        return str(items[0]) if items else '""'
    
    def argumentos(self, items):
        """Lista de argumentos"""
        return ", ".join(str(item) for item in items)
    
    def IDENTIFICADOR(self, token):
        """Identificadores simples"""
        name = str(token)
        
        # Se for um identificador isolado, considerar como variável
        if name.isalpha():
            variable = Variable(name=name)
            self.variables_found.add(variable)
        
        return name
    
    def NUMERO(self, token):
        """Tokens de número"""
        return str(token)
    
    def STRING(self, token):
        """Tokens de string"""
        return str(token)


class LOSParser(IParserAdapter):
    """
    Parser principal para linguagem LOS
    Implementa interface IParserAdapter usando Lark
    """
    
    def __init__(self, grammar_file: Optional[str] = None):
        self._grammar_file = grammar_file or self._get_default_grammar_path()
        self._parser = None
        self._transformer = None
        self._logger = get_logger('infrastructure.parser.los')
        self._initialize_parser()
    
    def _get_default_grammar_path(self) -> str:
        """Retorna caminho padrão da gramática"""
        # Gramática está na pasta los/
        current_dir = Path(__file__).parent
        los_root = current_dir.parent.parent  # los/
        return str(los_root / "los_grammar.lark")
    
    def _initialize_parser(self):
        """Inicializa o parser Lark"""
        try:
            self._logger.info(f"Carregando gramática de: {self._grammar_file}")
            
            if not Path(self._grammar_file).exists():
                raise FileNotFoundError(f"Arquivo de gramática não encontrado: {self._grammar_file}")
            
            with open(self._grammar_file, 'r', encoding='utf-8') as f:
                grammar_content = f.read()
            
            self._parser = Lark(
                grammar_content,
                start='start',
                parser='lalr',
                transformer=None  # Aplicaremos o transformer separadamente
            )
            
            self._transformer = LOSTransformer()
            self._logger.info("Parser LOS inicializado com sucesso")
            
        except Exception as e:
            self._logger.error(f"Erro inicializando parser: {e}")
            raise LOSParseError(
                message=f"Falha ao inicializar parser: {str(e)}",
                expression="",
                original_exception=e
            )
    
    async def parse(self, text: str) -> Dict[str, Any]:
        """
        Realiza parsing do texto LOS
        
        Args:
            text: Texto em linguagem LOS
            
        Returns:
            Resultado do parsing com metadata
        """
        try:
            self._logger.debug(f"Iniciando parsing: {text[:100]}...")
            
            # Preprocessar texto
            cleaned_text = self._preprocess_text(text)
            
            # Fazer parsing com Lark
            syntax_tree = self._parser.parse(cleaned_text)
            
            # Aplicar transformer
            result = self._transformer.transform(syntax_tree)
            
            # Compilar resultado final
            parse_result = {
                'original_text': text,
                'cleaned_text': cleaned_text,
                'syntax_tree': syntax_tree,
                'transformed_result': result,
                'variables': self._transformer.variables_found.copy(),
                'datasets': self._transformer.datasets_found.copy(),
                'complexity': ComplexityMetrics(
                    nesting_level=self._transformer.complexity_metrics['nesting_level'],
                    variable_count=len(self._transformer.variables_found),
                    operation_count=self._transformer.complexity_metrics['operation_count'],
                    function_count=self._transformer.complexity_metrics['function_count'],
                    conditional_count=self._transformer.complexity_metrics['conditional_count']
                ),
                'success': True,
                'errors': []
            }
            
            # Limpar estado do transformer para próxima execução
            self._transformer.variables_found.clear()
            self._transformer.datasets_found.clear()
            self._transformer.complexity_metrics = {
                'nesting_level': 1,
                'operation_count': 0,
                'function_count': 0,
                'conditional_count': 0
            }
            
            self._logger.debug(f"Parsing concluído com sucesso")
            return parse_result
            
        except (ParseError, LexError) as e:
            self._logger.error(f"Erro de sintaxe: {e}")
            raise LOSParseError(
                message=f"Erro de sintaxe na expressão: {text}",
                expression=text,
                original_exception=e
            )
        
        except Exception as e:
            self._logger.error(f"Erro inesperado durante parsing: {e}")
            raise LOSParseError(
                message=f"Erro interno do parser: {str(e)}",
                expression=text,
                original_exception=e
            )
    
    async def validate_syntax(self, text: str) -> bool:
        """
        Valida apenas sintaxe sem fazer transformação completa
        
        Args:
            text: Texto para validar
            
        Returns:
            True se sintaxe válida
        """
        try:
            cleaned_text = self._preprocess_text(text)
            self._parser.parse(cleaned_text)
            return True
        
        except (ParseError, LexError):
            return False
        
        except Exception as e:
            self._logger.warning(f"Erro durante validação de sintaxe: {e}")
            return False
    
    def _preprocess_text(self, text: str) -> str:
        """
        Preprocessa texto antes do parsing
        
        Args:
            text: Texto original
            
        Returns:
            Texto limpo e normalizado
        """
        # Normalizar espaços
        text = ' '.join(text.split())
        
        # Converter palavras-chave para maiúsculas
        keywords = [
            'minimizar', 'maximizar', 'se', 'entao', 'senao',
            'para', 'cada', 'em', 'onde', 'e', 'ou', 'nao', 'soma', 'de'
        ]
        
        # Tratamento especial para "SOMA DE"
        text = re.sub(r'\bsoma\s+de\b', 'SOMA DE', text, flags=re.IGNORECASE)
        
        # Converter outras palavras-chave
        for keyword in keywords:
            pattern = r'\b' + keyword + r'\b'
            text = re.sub(pattern, keyword.upper(), text, flags=re.IGNORECASE)
        
        return text
    
    def get_grammar_content(self) -> str:
        """Retorna conteúdo da gramática carregada"""
        try:
            with open(self._grammar_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self._logger.error(f"Erro lendo gramática: {e}")
            return ""
    
    def reload_grammar(self, grammar_file: Optional[str] = None):
        """Recarrega gramática do arquivo"""
        if grammar_file:
            self._grammar_file = grammar_file
        
        self._initialize_parser()
        self._logger.info("Gramática recarregada com sucesso")
