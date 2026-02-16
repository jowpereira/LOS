"""
🏗️ LOSModel — Modelo de otimização compilado, pronto para resolver

Encapsula o pipeline parse→translate e executa via PuLP.
"""

import time as _time
from typing import Any, Dict, List, Optional

import pulp

from ..value_objects.expression_types import Variable, DatasetReference, ComplexityMetrics
from .los_result import LOSResult


class LOSModel:
    """
    Modelo LOS compilado. Contém AST, código PuLP gerado,
    e expõe .solve() para execução direta.

    Uso:
        model = LOSModel(source, ast, python_code, ...)
        result = model.solve()
        print(result.objective)
    """

    __slots__ = (
        'source', 'ast', 'python_code', 'variables',
        'datasets', 'complexity', '_name'
    )

    def __init__(
        self,
        source: str,
        ast: Dict[str, Any],
        python_code: str,
        variables: Optional[List[Variable]] = None,
        datasets: Optional[List[DatasetReference]] = None,
        complexity: Optional[ComplexityMetrics] = None,
        name: str = "LOS_Model"
    ):
        self.source = source
        self.ast = ast
        self.python_code = python_code
        self.variables = variables or []
        self.datasets = datasets or []
        self.complexity = complexity or ComplexityMetrics()
        self._name = name

    def solve(
        self,
        backend: str = 'pulp',
        time_limit: Optional[int] = None,
        msg: bool = False
    ) -> LOSResult:
        """
        Executa o modelo compilado e retorna LOSResult.

        Args:
            backend: Solver backend ('pulp' por enquanto)
            time_limit: Tempo máximo em segundos (None = sem limite)
            msg: Se True, mostra output do solver

        Returns:
            LOSResult com status, objective, variables, time
        """
        if backend != 'pulp':
            raise NotImplementedError(
                f"Backend '{backend}' não suportado. Use 'pulp'."
            )

        # Namespace isolado para execução segura
        exec_namespace = {}

        t0 = _time.perf_counter()

        try:
            # Executar o código PuLP gerado
            exec(self.python_code, exec_namespace)
        except Exception as e:
            elapsed = _time.perf_counter() - t0
            return LOSResult(
                status=f"ExecutionError: {e}",
                objective=None,
                variables={},
                time=elapsed,
                solver_name="PuLP/CBC"
            )

        elapsed = _time.perf_counter() - t0

        # Extrair o objeto `prob` do namespace
        prob = exec_namespace.get('prob')

        if prob is None or not isinstance(prob, pulp.LpProblem):
            return LOSResult(
                status="Error: LpProblem 'prob' não encontrado no código gerado",
                objective=None,
                variables={},
                time=elapsed,
                solver_name="PuLP/CBC"
            )

        # Extrair resultados
        # Extrair resultados
        status_str = pulp.LpStatus.get(prob.status, "Unknown")
        
        if prob.status == pulp.constants.LpStatusOptimal:
            obj_value = pulp.value(prob.objective)
            # Se for None mas é Optimal, assume 0.0 (problema de viabilidade ou custo zero)
            if obj_value is None:
                obj_value = 0.0
        else:
            obj_value = None

        # Extrair variáveis com seus valores
        var_dict = {}
        for v in prob.variables():
            if v.varValue is not None:
                var_dict[v.name] = v.varValue

        return LOSResult(
            status=status_str,
            objective=obj_value,
            variables=var_dict,
            time=elapsed,
            solver_name="PuLP/CBC"
        )

    def code(self) -> str:
        """Retorna o código PuLP gerado (para inspeção/debug)."""
        return self.python_code

    @property
    def var_count(self) -> int:
        """Número de variáveis declaradas no modelo."""
        return len(self.variables)

    @property
    def name(self) -> str:
        return self._name

    def __repr__(self) -> str:
        return (
            f"LOSModel(name='{self._name}', "
            f"vars={len(self.variables)}, "
            f"datasets={len(self.datasets)})"
        )
