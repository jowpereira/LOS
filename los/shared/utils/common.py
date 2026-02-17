"""Funções Utilitárias Compartilhadas."""

import re
import hashlib
import time
from typing import Any, Dict, List, Optional, Set, Union
from datetime import datetime, timezone
from pathlib import Path


class TextUtils:
    """Utilitários de texto."""
    
    @staticmethod
    def normalize_expression_text(text: str) -> str:
        """Normaliza texto de expressão LOS."""
        # Remover espaços extras
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
    
    @staticmethod
    def extract_variables_from_text(text: str) -> Set[str]:
        """Extrai variáveis do texto."""
        variables = set()
        
        # Padrão para variáveis indexadas: var[index]
        indexed_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\['
        matches = re.findall(indexed_pattern, text)
        variables.update(matches)
        
        # Padrão para variáveis simples (mais restritivo)
        # Deve começar com letra, pode conter números e underscore
        simple_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b'
        matches = re.findall(simple_pattern, text)
        
        # Filtrar palavras-chave e tokens especiais
        reserved_words = {
            'MINIMIZAR', 'MAXIMIZAR', 'SE', 'ENTAO', 'SENAO',
            'PARA', 'CADA', 'EM', 'ONDE', 'E', 'OU', 'NAO', 
            'SOMA', 'DE', 'abs', 'max', 'min', 'sum', 'sqrt'
        }
        
        for match in matches:
            if match.upper() not in reserved_words and match.isalpha():
                variables.add(match)
        
        return variables
    
    @staticmethod
    def extract_dataset_references(text: str) -> Set[tuple]:
        """Extrai referências a datasets."""
        references = set()
        
        # Padrão para dataset.coluna
        pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)\b'
        matches = re.findall(pattern, text)
        
        for dataset, column in matches:
            references.add((dataset, column))
        
        # Padrão para dataset['coluna com espaços']
        quoted_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\[[\'"](.*?)[\'"]\]'
        quoted_matches = re.findall(quoted_pattern, text)
        
        for dataset, column in quoted_matches:
            references.add((dataset, column))
        
        return references
    
    @staticmethod
    def is_valid_identifier(name: str) -> bool:
        """Verifica se nome é identificador válido."""
        if not name:
            return False
        
        # Deve ser identificador Python válido
        if not name.isidentifier():
            return False
        
        # Não deve ser palavra reservada Python
        python_keywords = {
            'and', 'as', 'assert', 'break', 'class', 'continue', 'def',
            'del', 'elif', 'else', 'except', 'finally', 'for', 'from',
            'global', 'if', 'import', 'in', 'is', 'lambda', 'nonlocal',
            'not', 'or', 'pass', 'raise', 'return', 'try', 'while',
            'with', 'yield'
        }
        
        return name.lower() not in python_keywords


class ValidationUtils:
    """Utilitários de validação."""
    
    @staticmethod
    def check_balanced_parentheses(text: str) -> bool:
        """Verifica se parênteses estão balanceados."""
        stack = []
        pairs = {'(': ')', '[': ']', '{': '}'}
        
        for char in text:
            if char in pairs:
                stack.append(char)
            elif char in pairs.values():
                if not stack:
                    return False
                if pairs[stack.pop()] != char:
                    return False
        
        return len(stack) == 0
    
    @staticmethod
    def check_balanced_quotes(text: str) -> bool:
        """Verifica se aspas estão balanceadas."""
        single_quotes = text.count("'")
        double_quotes = text.count('"')
        return single_quotes % 2 == 0 and double_quotes % 2 == 0
    
    @staticmethod
    def validate_expression_type(text: str) -> Optional[str]:
        """Detecta tipo de expressão."""
        text_upper = text.upper().strip()
        
        # Objetivos
        if text_upper.startswith('MINIMIZAR:') or text_upper.startswith('MAXIMIZAR:'):
            return 'objective'
        
        # Condicionais
        if 'SE ' in text_upper and ' ENTAO ' in text_upper:
            return 'conditional'
        
        # Agregações
        if 'SOMA DE' in text_upper or 'PARA CADA' in text_upper:
            return 'aggregation'
        
        # Restrições (tem operadores relacionais)
        comparison_operators = ['<=', '>=', '==', '!=', '<', '>', '=']
        if any(op in text for op in comparison_operators):
            return 'constraint'
        
        # Matemática (contém operadores ou funções)
        if any(op in text for op in ['+', '-', '*', '/', '^']):
             return 'mathematical'
        
        return 'unknown'


class HashUtils:
    """Utilitários de hash."""
    
    @staticmethod
    def generate_expression_hash(text: str) -> str:
        """Gera hash SHA-256 para expressão."""
        # Normalizar texto antes do hash
        normalized = TextUtils.normalize_expression_text(text)
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()
    
    @staticmethod
    def generate_cache_key(prefix: str, *args) -> str:
        """Gera chave de cache consistente."""
        content = f"{prefix}:{':'.join(str(arg) for arg in args)}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()


class TimeUtils:
    """Utilitários de tempo."""
    
    @staticmethod
    def get_iso_timestamp() -> str:
        """Retorna timestamp ISO atual."""
        return datetime.now(timezone.utc).isoformat()
    
    @staticmethod
    def measure_execution_time(func):
        """Decorator para medir tempo de execução."""
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Adicionar tempo de execução ao resultado se for dict
            if isinstance(result, dict):
                result['execution_time'] = execution_time
            
            return result
        
        return wrapper


class FileUtils:
    """Utilitários de arquivo."""
    
    @staticmethod
    def ensure_directory_exists(file_path: Union[str, Path]) -> Path:
        """Garante que diretório existe."""
        path = Path(file_path)
        directory = path.parent if path.suffix else path
        directory.mkdir(parents=True, exist_ok=True)
        return directory
    
    @staticmethod
    def get_file_extension(file_path: str) -> str:
        """Retorna extensão do arquivo."""
        return Path(file_path).suffix.lower()
    
    @staticmethod
    def is_supported_file(file_path: str, supported_extensions: Set[str]) -> bool:
        """Verifica se extensão é suportada."""
        extension = FileUtils.get_file_extension(file_path)
        return extension in supported_extensions
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitiza nome de arquivo."""
        # Remover caracteres não permitidos
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Limitar tamanho
        if len(filename) > 255:
            name, ext = Path(filename).stem, Path(filename).suffix
            max_name_length = 255 - len(ext)
            filename = name[:max_name_length] + ext
        
        return filename


class DataStructureUtils:
    """Utilitários de estrutura de dados."""
    
    @staticmethod
    def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
        """Merge profundo de dicionários."""
        result = dict1.copy()
        
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = DataStructureUtils.deep_merge_dicts(result[key], value)
            else:
                result[key] = value
        
        return result
    
    @staticmethod
    def flatten_list(nested_list: List[Any]) -> List[Any]:
        """Achata lista aninhada."""
        result = []
        
        for item in nested_list:
            if isinstance(item, list):
                result.extend(DataStructureUtils.flatten_list(item))
            else:
                result.append(item)
        
        return result
    
    @staticmethod
    def remove_duplicates_preserve_order(items: List[Any]) -> List[Any]:
        """Remove duplicatas preservando ordem."""
        seen = set()
        result = []
        
        for item in items:
            if item not in seen:
                seen.add(item)
                result.append(item)
        
        return result


class MathUtils:
    """Utilitários matemáticos."""
    
    @staticmethod
    def calculate_complexity_score(
        variables: int,
        operations: int,
        functions: int,
        conditionals: int,
        nesting_level: int
    ) -> int:
        """Calcula score de complexidade."""
        return (
            variables +
            operations * 2 +
            functions * 3 +
            conditionals * 4 +
            nesting_level
        )
    
    @staticmethod
    def normalize_score(score: float, min_val: float = 0, max_val: float = 100) -> float:
        """Normaliza score."""
        if max_val <= min_val:
            return min_val
        
        return max(min_val, min(max_val, score))
