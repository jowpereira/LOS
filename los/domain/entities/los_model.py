"""Modelo de otimização compilado."""

import time as _time
from typing import Any, Dict, List, Optional

import pulp

from ..value_objects.expression_types import Variable, DatasetReference, ComplexityMetrics
from .los_result import LOSResult


class LOSModel:
    """Contém AST e código PuLP gerado. Executa via .solve()."""

    __slots__ = (
        'source', 'ast', 'python_code', 'variables',
        'datasets', 'complexity', '_name', 'bound_data'
    )

    def __init__(
        self,
        source: str,
        ast: Dict[str, Any],
        python_code: str,
        variables: Optional[List[Variable]] = None,
        datasets: Optional[List[DatasetReference]] = None,
        complexity: Optional[ComplexityMetrics] = None,
        name: str = "LOS_Model",
        bound_data: Optional[Dict[str, Any]] = None
    ):
        self.source = source
        self.ast = ast
        self.python_code = python_code
        self.variables = variables or []
        self.datasets = datasets or []
        self.complexity = complexity or ComplexityMetrics()
        self._name = name
        self.bound_data = bound_data or {}

    def solve(
        self,
        backend: str = 'pulp',
        time_limit: Optional[int] = None,
        msg: bool = False
    ) -> LOSResult:
        """Executa o modelo compilado e retorna LOSResult."""


        # Sandbox Execution: Restrict globals to prevent dangerous access
        safe_globals = {
            '__builtins__': {},  # Empty builtins prevents default access
            'pulp': pulp,
            'pd': __import__('pandas'),
            'np': __import__('numpy'),
            'math': __import__('math'),
            '_los_data': self.bound_data,
            # Safe builtins needed for generated code
            'range': range,
            'list': list,
            'set': set,
            'dict': dict,
            'len': len,
            'str': str,
            'int': int,
            'float': float,
            'tuple': tuple,
            'bool': bool,
            'enumerate': enumerate,
            'zip': zip,
            'min': min,
            'max': max,
            'abs': abs,
            'sum': sum, # Python sum, though pulp.lpSum is mostly used
        }

        # Local namespace to capture variables defined in the script
        # Unified namespace to avoid class-scope issues in exec
        exec_context = safe_globals.copy()

        t0 = _time.perf_counter()

        try:
            # Executar código no sandbox
            exec(self.python_code, exec_context)
        except Exception as e:
            elapsed = _time.perf_counter() - t0
            import traceback
            return LOSResult(
                status=f"ExecutionError: {e}\n{traceback.format_exc()}",
                objective=None,
                variables={},
                time=elapsed,
                solver_name="PuLP/CBC"
            )

        elapsed_build = _time.perf_counter() - t0

        # Extrair o objeto `prob` do namespace local
        prob = exec_context.get('prob')

        if prob is None or not isinstance(prob, pulp.LpProblem):
            return LOSResult(
                status="Error: LpProblem 'prob' não encontrado no código gerado",
                objective=None,
                variables={},
                time=elapsed_build,
                solver_name="None"
            )

        # Configurar solver (backend 'library:solver')
        
        if ':' in backend:
            parts = backend.split(':')
            lib = parts[0]
            solver_type = parts[1]
        else:
            lib = backend
            solver_type = 'cbc'
        
        if lib != 'pulp':
             raise NotImplementedError(f"Backend library '{lib}' não suportada. Use 'pulp'.")

        solver_map = {
            'cbc': pulp.PULP_CBC_CMD(timeLimit=time_limit, msg=msg),
            'glpk': pulp.GLPK_CMD(timeLimit=time_limit, msg=msg),
            'coin': pulp.COIN_CMD(timeLimit=time_limit, msg=msg),
            # Adicionar outros conforme necessário, instanciando on-demand para evitar imports pesados se não usados
        }
        
        solver = solver_map.get(solver_type.lower())
        if not solver:
             raise ValueError(f"Solver '{solver_type}' desconhecido ou não suportado explicitamente. Solvers disponíveis: {list(solver_map.keys())}")
        
        t1 = _time.perf_counter()
        try:
            prob.solve(solver)
        except Exception as e:
            return LOSResult(
                status=f"SolverError: {e}",
                objective=None,
                variables={},
                time=_time.perf_counter() - t1,
                solver_name="PuLP/CBC"
            )
            
        elapsed_solve = _time.perf_counter() - t1

        # Extrair resultados
        status_str = pulp.LpStatus.get(prob.status, "Unknown")
        
        if prob.status == pulp.constants.LpStatusOptimal:
            if prob.objective is not None:
                try:
                    obj_value = pulp.value(prob.objective)
                    if obj_value is None:
                        obj_value = 0.0
                except AttributeError:
                    obj_value = 0.0
            else:
                obj_value = 0.0
        else:
            # Tentar pegar valor mesmo se não for ótimo (ex: Infeasible mas com bound)
            try:
                if prob.objective is not None:
                    obj_value = pulp.value(prob.objective)
                else:
                    obj_value = None
            except:
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
            time=elapsed_solve + elapsed_build,
            solver_name=solver.name if hasattr(solver, 'name') else "PuLP/CBC"
        )

    def code(self) -> str:
        """Retorna código gerado."""
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
