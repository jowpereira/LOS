"""
📊 LOSResult — Resultado da resolução de um modelo de otimização

A03: Encapsula status, objective, variables, e tempo de resolução.
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

    def __bool__(self) -> bool:
        """LOSResult é truthy se o status é Optimal."""
        return self.is_optimal
