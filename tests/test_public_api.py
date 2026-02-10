"""
🧪 test_public_api.py — Testes da API Pública LOS v3.2
Cobre A01 (los.compile), A02 (LOSModel.solve), A03 (LOSResult), A04 (los.solve)
"""

import os
import sys
import pytest

# Garantir que o diretório raiz está no path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import los
from los.domain.entities.los_model import LOSModel
from los.domain.entities.los_result import LOSResult
from los.shared.errors.exceptions import ParseError


# ═══════════════════════════════════════════════════════════════════
# Modelos inline para testes
# ═══════════════════════════════════════════════════════════════════

SIMPLE_LP = """
var x >= 0
var y >= 0
min: x + y
st:
    c1: x + y >= 10
"""

BOUNDED_LP = """
var x >= 0
var y >= 0
min: 2 * x + 3 * y
st:
    r1: x + y >= 10
    r2: x >= 3
"""

MAXIMIZATION = """
var x >= 0
var y >= 0
max: x + y
st:
    r1: x + y <= 100
    r2: x <= 60
    r3: y <= 50
"""

BINARY_LP = """
var escolha : bin
min: 10 * escolha
st:
    r1: escolha >= 1
"""


# ═══════════════════════════════════════════════════════════════════
# A01: los.compile()
# ═══════════════════════════════════════════════════════════════════

class TestCompile:
    """Testes para los.compile() — A01"""

    def test_compile_returns_model(self):
        """los.compile() deve retornar LOSModel"""
        model = los.compile(SIMPLE_LP)
        assert isinstance(model, LOSModel)

    def test_compile_has_ast(self):
        """Modelo compilado deve conter AST"""
        model = los.compile(SIMPLE_LP)
        assert model.ast is not None
        assert isinstance(model.ast, dict)

    def test_compile_has_code(self):
        """Modelo compilado deve conter código PuLP gerado"""
        model = los.compile(SIMPLE_LP)
        code = model.code()
        assert isinstance(code, str)
        assert "import pulp" in code
        assert "pulp.LpProblem" in code

    def test_compile_has_variables(self):
        """Modelo compilado deve extrair variáveis"""
        model = los.compile(SIMPLE_LP)
        assert model.var_count >= 1

    def test_compile_from_file(self):
        """los.compile() deve aceitar caminhos de arquivo .los"""
        model_path = os.path.join(
            os.path.dirname(__file__), "modelos", "supply_chain_network.los"
        )
        if os.path.exists(model_path):
            model = los.compile(model_path)
            assert isinstance(model, LOSModel)
            assert model.var_count > 0

    def test_compile_invalid_raises(self):
        """los.compile() deve lançar ParseError para sintaxe inválida"""
        with pytest.raises((ParseError, Exception)):
            los.compile("!!! this is not valid LOS !!!")

    def test_compile_repr(self):
        """LOSModel deve ter __repr__ legível"""
        model = los.compile(SIMPLE_LP)
        r = repr(model)
        assert "LOSModel" in r
        assert "vars=" in r


# ═══════════════════════════════════════════════════════════════════
# A02: LOSModel.solve()
# ═══════════════════════════════════════════════════════════════════

class TestModelSolve:
    """Testes para LOSModel.solve() — A02"""

    def test_solve_returns_result(self):
        """solve() deve retornar LOSResult"""
        model = los.compile(SIMPLE_LP)
        result = model.solve()
        assert isinstance(result, LOSResult)

    def test_solve_optimal(self):
        """Problema simples deve ser Optimal"""
        model = los.compile(SIMPLE_LP)
        result = model.solve()
        assert result.is_optimal

    def test_solve_objective_value(self):
        """Objetivo deve ser 10 (min x+y s.t. x+y>=10)"""
        model = los.compile(SIMPLE_LP)
        result = model.solve()
        assert result.objective == pytest.approx(10.0, abs=1e-4)

    def test_solve_bounded(self):
        """min 2x+3y s.t. x+y>=10, x>=3 → objetivo = 20"""
        model = los.compile(BOUNDED_LP)
        result = model.solve()
        assert result.is_optimal
        assert result.objective == pytest.approx(20.0, abs=1e-4)

    def test_solve_maximization(self):
        """max x+y s.t. x<=60, y<=50, x+y<=100"""
        model = los.compile(MAXIMIZATION)
        result = model.solve()
        assert result.is_optimal
        assert result.objective == pytest.approx(100.0, abs=1e-4)

    def test_solve_binary(self):
        """Variável binária = 1"""
        model = los.compile(BINARY_LP)
        result = model.solve()
        assert result.is_optimal
        assert result.objective == pytest.approx(10.0, abs=1e-4)

    def test_solve_time_positive(self):
        """Tempo de resolução deve ser > 0"""
        model = los.compile(SIMPLE_LP)
        result = model.solve()
        assert result.time > 0

    def test_solve_unsupported_backend(self):
        """Backend não suportado deve lançar NotImplementedError"""
        model = los.compile(SIMPLE_LP)
        with pytest.raises(NotImplementedError):
            model.solve(backend='gurobi')


# ═══════════════════════════════════════════════════════════════════
# A03: LOSResult
# ═══════════════════════════════════════════════════════════════════

class TestResult:
    """Testes para LOSResult — A03"""

    def test_result_status(self):
        result = los.solve(SIMPLE_LP)
        assert result.status == "Optimal"

    def test_result_objective(self):
        result = los.solve(SIMPLE_LP)
        assert isinstance(result.objective, float)

    def test_result_variables_dict(self):
        """Variables deve ser um dict nome→valor"""
        result = los.solve(SIMPLE_LP)
        assert isinstance(result.variables, dict)
        assert len(result.variables) > 0

    def test_result_time(self):
        result = los.solve(SIMPLE_LP)
        assert isinstance(result.time, float)
        assert result.time > 0

    def test_result_solver_name(self):
        result = los.solve(SIMPLE_LP)
        assert "PuLP" in result.solver_name

    def test_result_is_optimal(self):
        result = los.solve(SIMPLE_LP)
        assert result.is_optimal is True

    def test_result_bool_true(self):
        """LOSResult deve ser truthy quando Optimal"""
        result = los.solve(SIMPLE_LP)
        assert bool(result) is True

    def test_result_non_zero_variables(self):
        """non_zero_variables deve filtrar zeros"""
        result = los.solve(SIMPLE_LP)
        nz = result.non_zero_variables
        for v in nz.values():
            assert abs(v) > 1e-8

    def test_result_repr(self):
        result = los.solve(SIMPLE_LP)
        r = repr(result)
        assert "LOSResult" in r
        assert "Optimal" in r


# ═══════════════════════════════════════════════════════════════════
# A04: los.solve() shortcut
# ═══════════════════════════════════════════════════════════════════

class TestSolveShortcut:
    """Testes para los.solve() — A04"""

    def test_solve_shortcut_works(self):
        """los.solve() deve funcionar como compile+solve"""
        result = los.solve(SIMPLE_LP)
        assert result.is_optimal
        assert result.objective == pytest.approx(10.0, abs=1e-4)

    def test_solve_shortcut_returns_result(self):
        result = los.solve(SIMPLE_LP)
        assert isinstance(result, LOSResult)

    def test_solve_shortcut_maximization(self):
        result = los.solve(MAXIMIZATION)
        assert result.is_optimal
        assert result.objective == pytest.approx(100.0, abs=1e-4)

    def test_solve_shortcut_invalid_raises(self):
        with pytest.raises((ParseError, Exception)):
            los.solve("!!! invalid !!!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
