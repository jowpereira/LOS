"""
🔗 Data Binding Service - Conecta dados reais aos parâmetros do modelo
D01-D04: Validação e mapeamento de DataFrames/dicts para parâmetros AST.
"""

from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import pandas as pd
import numpy as np

from ...shared.errors.exceptions import ValidationError
from ...shared.logging.logger import get_logger

_logger = get_logger(__name__)


class DataBindingService:
    """
    Serviço responsável por validar e preparar dados de entrada para o modelo.
    Garante que os dados fornecidos (data) correspondem à estrutura esperada pelos parâmetros (ast).
    """

    def bind_data(self, ast: Dict[str, Any], data: Optional[Dict[str, Any]] = None, base_dir: Optional[Path] = None) -> Dict[str, Any]:
        """
        Valida e prepara os dados para injeção no modelo.

        Args:
            ast: Árvore sintática do modelo
            data: Dados explícitos (override)
            base_dir: Diretório base do modelo para resolver imports
        """
        # S01: Separate input sources (DataFrames) from bound output (Lists/Dicts)
        # to prevents overwriting source DFs when extracting Sets.
        input_sources = {}
        
        # 1. Carregar imports (baixa prioridade)
        if base_dir:
             imported_data = self._load_imports(ast, base_dir)
             input_sources.update(imported_data)

        # 2. Carregar dados explícitos (alta prioridade - override)
        if data:
            input_sources.update(data)
            
        bound_data = {}

        # Bind Sets
        sets = self._extract_sets(ast)
        for set_name, set_def in sets.items():
            vals = None
            # 1. Direct match (file name == set name) in input_sources
            if set_name in input_sources:
                data_val = input_sources[set_name]
                if isinstance(data_val, pd.DataFrame):
                    if set_name in data_val.columns:
                        vals = data_val[set_name].dropna().unique().tolist()
                    elif data_val.index.name == set_name:
                         vals = data_val.index.unique().tolist()
                    else:
                        vals = data_val.iloc[:, 0].dropna().unique().tolist()
                elif isinstance(data_val, pd.Series):
                    vals = data_val.unique().tolist()
                elif isinstance(data_val, (set, tuple, list)):
                    vals = list(data_val)
            
            # 2. D03: Search in other DataFrames within input_sources
            if not vals:
                 for key, val in input_sources.items():
                    if isinstance(val, pd.DataFrame) and set_name in val.columns:
                        vals = val[set_name].dropna().unique().tolist()
                        _logger.debug(f"Set '{set_name}' encontrado no DataFrame '{key}'")
                        break
            
            if vals:
                bound_data[set_name] = vals

        parameters = self._extract_parameters(ast)

        for param_name, param_def in parameters.items():
            # Check input_sources first
            if param_name in input_sources:
                raw_value = input_sources[param_name]
                validated_value = self._validate_and_transform(param_name, param_def, raw_value, bound_data)
                bound_data[param_name] = validated_value
            else:
                # D03: Tentar encontrar o parâmetro como coluna em outros DataFrames importados (input_sources)
                found_in_df = False
                for key, val in input_sources.items():
                    # DEBUG PRINT
                    # print(f"Checking DF '{key}' for param '{param_name}'. Columns: {val.columns if isinstance(val, pd.DataFrame) else 'Not DF'}")
                    if isinstance(val, pd.DataFrame) and param_name in val.columns:
                        try:
                            _logger.debug(f"Parâmetro '{param_name}' encontrado no DataFrame '{key}'")
                            # Copia o DataFrame para evitar efeitos colaterais
                            # O _validate_and_transform vai lidar com set_index e extração
                            validated_value = self._validate_and_transform(param_name, param_def, val.copy(), bound_data)
                            bound_data[param_name] = validated_value
                            found_in_df = True
                            break
                        except Exception as e:
                            _logger.warning(f"Falha ao extrair '{param_name}' do DataFrame '{key}': {e}")
                
                if not found_in_df:
                    _logger.warning(f"Parâmetro '{param_name}' não encontrado nos dados importados. Usará valor padrão. DICA: Verifique se o nome da coluna no CSV corresponde exatamente ao nome do parâmetro.")

        return bound_data

    def _load_imports(self, ast: Dict[str, Any], base_dir: Path) -> Dict[str, Any]:
        """Lê arquivos importados no AST (ex: import "file.csv")"""
        loaded = {}
        for stmt in ast.get('statements', []):
            if stmt.get('type') == 'import':
                path_str = stmt.get('path')
                if not path_str: continue
                
                safe_path = Path(path_str)
                # Resolve relative path
                full_path = base_dir / safe_path
                
                if full_path.exists() and full_path.suffix.lower() == '.csv':
                    try:
                        # Assume filename stem is the variable name (e.g. demanda.csv -> demanda)
                        var_name = safe_path.stem
                        _logger.info(f"Carregando import: {var_name} de {full_path}")
                        loaded[var_name] = pd.read_csv(full_path)
                    except Exception as e:
                        _logger.warning(f"Falha ao carregar import {full_path}: {e}")
        return loaded

    def _extract_parameters(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        """Extrai definições de parâmetros da AST."""
        params = {}
        # AST estrutura: {'statements': [...]}
        for stmt in ast.get('statements', []):
            if stmt.get('type') == 'param':
                name = stmt['name']
                params[name] = stmt
        return params

    def _validate_and_transform(self, name: str, definition: Dict[str, Any], value: Any, context: Dict[str, Any] = None) -> Any:
        """
        Valida se o valor corresponde à definição do parâmetro e transforma se necessário.
        Args:
            context: bound_data atual (para acesso a Sets)
        """
        indices = definition.get('indices')
        
        # Caso 1: Escalar (sem índices)
        if not indices:
            if isinstance(value, (pd.DataFrame, pd.Series, dict, list)):
                 raise ValidationError(f"Parâmetro '{name}' é escalar, mas recebeu dados estruturados.")
            try:
                return float(value)
            except (ValueError, TypeError):
                raise ValidationError(f"Parâmetro '{name}' espera valor numérico, recebeu {type(value)}")

        # Caso 2: Indexado (Array/Matriz)
        if isinstance(value, pd.DataFrame):
            return self._process_dataframe(name, indices, value, context)
        elif isinstance(value, pd.Series):
            return self._process_series(name, indices, value)
        elif isinstance(value, dict):
            return self._process_dict(name, indices, value)
        else:
            raise ValidationError(f"Parâmetro '{name}' indexado espera DataFrame/Series/dict, recebeu {type(value)}")

    def _process_dataframe(self, name: str, indices: List[str], df: pd.DataFrame, context: Dict[str, Any] = None) -> Dict:
        """Transforma DataFrame em dicionário aninhado, garantindo densidade se possível."""
        expected_levels = len(indices)
        
        # Tenta setar índice se as colunas existirem
        available_cols = set(df.columns)
        indices_to_set = [idx for idx in indices if idx in available_cols]
        
        if len(indices_to_set) > 0:
            # Se encontrou todos ou alguns, seta.
            # Se for parcial, depois verifica levels.
            try:
                df = df.set_index(indices_to_set)
            except Exception as e:
                _logger.warning(f"Falha ao definir índice {indices_to_set} para parâmetro '{name}': {e}. Usando índice padrão.")
        
        # Seleciona a coluna de valor
        value_col = None
        if name in df.columns:
            value_col = name
        elif len(df.columns) == 1:
            value_col = df.columns[0]
        else:
            # Fallback: primeira coluna numérica? ou error
            # Tenta achar 'value', 'valor'
            for c in ['value', 'valor', 'val']:
                if c in df.columns:
                    value_col = c
                    break
            if not value_col:
                # Last resort: first column that is not index
                value_col = df.columns[0]
                _logger.warning(f"Aviso: Inferindo coluna '{value_col}' como valor para parâmetro '{name}'. Se incorreto, renomeie a coluna no CSV.")

        series = df[value_col]

        # Auto-Densification Logic
        if context:
            # Verifica se podemos reconstruir o índice completo
            # Precisamos que TODOS os índices estejam no context (como Sets/Lists)
            can_reindex = True
            levels = []
            for idx_name in indices:
                if idx_name in context:
                    # Assume que é uma lista de ids
                    vals = context[idx_name]
                    if isinstance(vals, (list, tuple, set)):
                         levels.append(list(vals))
                    else:
                        can_reindex = False
                        break
                else:
                    can_reindex = False
                    break
            
            if can_reindex and len(levels) == len(indices):
                # S06: Fix 1-level MultiIndex issue.
                # MultiIndex.from_product creates tuples even for 1 level. Use Index for 1 level.
                if len(indices) == 1:
                    full_idx = pd.Index(levels[0], name=indices[0])
                else:
                    full_idx = pd.MultiIndex.from_product(levels, names=indices)
                
                # D05: Heuristic - If the source DF has NO overlap with the target index, it's likely the wrong DF.
                # Unless the target index is empty (which shouldn't happen here).
                if not full_idx.empty:
                    # Normalize indices for comparison (types might differ, e.g. str vs int)
                    # But loose intersection is safer.
                    intersection = series.index.intersection(full_idx)
                    if intersection.empty:
                            raise ValueError(f"DataFrame source has no overlap with target indices {indices}. Skipping.")

                try:
                    # Reindex com fill_value=0 (Assunção: default=0)
                    # TODO: Pegar default do AST se possível
                    series = series.reindex(full_idx, fill_value=0)
                    _logger.debug(f"Densificado parâmetro '{name}' com {len(series)} entradas.")
                except Exception as e:
                    _logger.warning(f"Falha na densificação automática de '{name}': {e}")
        
        # DEBUG PRINT
        # print(f"Processing DF for '{name}'. Series:\n{series}\nNested Dict:\n{self._to_nested_dict(series)}")
        return self._to_nested_dict(series)

    def _process_series(self, name: str, indices: List[str], series: pd.Series) -> Dict:
        """Processa Series para dict aninhado."""
        if series.index.nlevels != len(indices):
             raise ValidationError(f"Parâmetro '{name}' espera {len(indices)} índices, Series tem {series.index.nlevels}.")
        
        return self._to_nested_dict(series)

    def _process_dict(self, name: str, indices: List[str], data: Dict) -> Dict:
        """Valida dict. Assume que já está no formato correto (aninhado ou tuple keys?)."""
        # Se for tuple keys {(i,j): val}, converter para aninhado?
        # O Translator gera acesso `param[i][j]`.
        # Se o dict for {(i,j): val}, `param[i]` falha.
        # TEM QUE SER ANINHADO.
        
        if not data:
            return {}
            
        sample_key = next(iter(data))
        if isinstance(sample_key, tuple):
            # Converter flat dict {(i,j): v} -> nested {i: {j: v}}
            return self._unflatten_dict(data)
        
        return data

    def _to_nested_dict(self, series: pd.Series) -> Dict:
        """Converte pandas Series (com MultiIndex) para dict aninhado."""
        if series.index.nlevels == 1:
            return series.to_dict()
            
        # Para MultiIndex, é mais chato.
        # Ex: (A, B) -> val
        # {A: {B: val}}
        
        # Groupby no primeiro nível e recursão? Lento.
        # Iterar? Lento.
        
        # Melhor abordagem:
        # Loop sobre o índice.
        d = {}
        for idx, val in series.items():
            if not isinstance(idx, tuple):
                idx = (idx,)
            
            current = d
            for i in idx[:-1]:
                if i not in current:
                    current[i] = {}
                current = current[i]
            current[idx[-1]] = val
            
        return d

    def _unflatten_dict(self, flat_dict: Dict) -> Dict:
        """Converte {(i,j): val} para {i: {j: val}}."""
        d = {}
        for idx, val in flat_dict.items():
            if not isinstance(idx, tuple):
                d[idx] = val # Should not happen if detected as tuple
                continue
                
            current = d
            for i in idx[:-1]:
                if i not in current:
                    current[i] = {}
                current = current[i]
            current[idx[-1]] = val
        return d

    def _extract_sets(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        """Extrai definições de conjuntos (sets) da AST."""
        sets = {}
        for stmt in ast.get('statements', []):
            if stmt.get('type') == 'set':
                name = stmt['name']
                sets[name] = stmt
        return sets
