"""
📊 LOSResult — Resultado da resolução de um modelo de otimização

Encapsula status, objective, variables, e tempo de resolução.
"""

from typing import Dict, Optional


class LOSResult:
    """
    Resultado da resolução de um modelo de otimização LOS.
    
    Attributes:
        status: Status textual do solver ("Optimal", "Infeasible", "Unbounded", etc)
        objective: Valor da função objetivo (None se não resolvido)
        variables: Dicionário nome_variável → valor
        time: Tempo de resolução em segundos
        solver_name: Nome do solver/backend utilizado
    """

    __slots__ = ('status', 'objective', 'variables', 'time', 'solver_name')

    def __init__(
        self,
        status: str,
        objective: Optional[float] = None,
        variables: Optional[Dict[str, float]] = None,
        time: float = 0.0,
        solver_name: str = "PuLP/CBC"
    ):
        self.status = status
        self.objective = objective
        self.variables = variables or {}
        self.time = time
        self.solver_name = solver_name

    @property
    def is_optimal(self) -> bool:
        """True se o solver encontrou solução ótima."""
        return self.status == "Optimal"

    @property
    def is_infeasible(self) -> bool:
        """True se o problema é inviável."""
        return self.status == "Infeasible"

    @property
    def is_unbounded(self) -> bool:
        """True se o problema é ilimitado."""
        return self.status == "Unbounded"

    @property
    def non_zero_variables(self) -> Dict[str, float]:
        """Retorna apenas variáveis com valor != 0."""
        return {k: v for k, v in self.variables.items() if abs(v) > 1e-8}

    def __repr__(self) -> str:
        obj_str = f"{self.objective:.4f}" if self.objective is not None else "N/A"
        return (
            f"LOSResult(status={self.status}, "
            f"objective={obj_str}, "
            f"vars={len(self.variables)}, "
            f"time={self.time:.3f}s)"
        )

    def get_variable(self, name: str, as_df: bool = True):
        """
        Retorna os valores de uma variável específica de forma estruturada.
        
        Args:
            name: Nome base da variável (ex: "envio", "fabrica").
            as_df: Se True, retorna como pandas Series/DataFrame (requer pandas).
                   Se False, retorna como dicionário aninhado ou simples.
        """
        # Prefix check
        prefix = f"{name}_"
        filtered = {}
        
        for k, v in self.variables.items():
            if k == name:
                # Scalar
                return v
            elif k.startswith(prefix):
                # Indexed
                idx_part = k[len(prefix):]
                # Simplistic split by underscore. 
                # Assumption: parameter names don't have underscores or are handled by prefix.
                # Assumption: index values don't have underscores.
                parts = tuple(idx_part.split('_'))
                if len(parts) == 1:
                    filtered[parts[0]] = v
                else:
                    filtered[parts] = v
                    
        if not filtered:
            return {}
            
        if as_df:
            try:
                import pandas as pd
                # Handle multi-index
                first_key = next(iter(filtered))
                if isinstance(first_key, tuple):
                    # Create MultiIndex
                    tuples = list(filtered.keys())
                    index = pd.MultiIndex.from_tuples(tuples, names=[f"idx_{i}" for i in range(len(tuples[0]))])
                    return pd.Series(list(filtered.values()), index=index, name=name)
                else:
                    # Simple Index
                    return pd.Series(filtered, name=name)
            except ImportError:
                pass 
                
        return filtered

    def __bool__(self) -> bool:
        """LOSResult é truthy se o status é Optimal."""
        return self.is_optimal
