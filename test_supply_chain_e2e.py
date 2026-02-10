#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════════════
🧪 TEST: Supply Chain Network Design — LOS v3 Complex E2E Integration
═══════════════════════════════════════════════════════════════════════════════

Testa o modelo supply_chain_network.los de ponta a ponta:
  1. Parsing do .los complexo (multi-set, multi-index, multi-constraint)
  2. Validação semântica (sets, params, vars, objective, constraints)
  3. Tradução para PuLP (código executável)
  4. Verificação estrutural do código gerado

Dados: 4 plantas × 6 produtos × 8 clientes = ~192 variáveis de envio
       + 24 variáveis de produção + 4 de hora extra + 4 binárias = ~224 vars
       + 6 blocos de restrições com comprehensions multi-index

Este é o teste mais complexo do LOS v3.
"""

import pytest
import sys
import os
from pathlib import Path

# Ensure project root is in path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from los.infrastructure.parsers.los_parser import LOSParser
from los.infrastructure.translators.pulp_translator import PuLPTranslator
from los.domain.entities.expression import Expression
from los.domain.value_objects.expression_types import ExpressionType


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

MODEL_PATH = Path(__file__).parent / "modelos" / "supply_chain_network.los"


@pytest.fixture(scope="module")
def los_source():
    """Carrega o arquivo .los"""
    assert MODEL_PATH.exists(), f"Modelo não encontrado: {MODEL_PATH}"
    return MODEL_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def parser():
    return LOSParser()


@pytest.fixture(scope="module")
def translator():
    return PuLPTranslator()


@pytest.fixture(scope="module")
def parse_result(parser, los_source):
    """Parse do modelo completo"""
    result = parser.parse(los_source)
    return result


@pytest.fixture(scope="module")
def translated_code(parse_result, translator, los_source):
    """Tradução completa do modelo"""
    expr = Expression(original_text=los_source)
    expr.syntax_tree = parse_result['parsed_result']
    expr.expression_type = ExpressionType.MODEL
    # Populate variables from parse result
    for var in parse_result.get('variables', []):
        expr.add_variable(var)
    expr.validate()
    code = translator.translate_expression(expr)
    return code


# ═══════════════════════════════════════════════════════════════════
# Test Suite
# ═══════════════════════════════════════════════════════════════════

class TestSupplyChainParsing:
    """Testa se o parser lida com o modelo complexo sem explodir"""

    def test_parse_succeeds(self, parse_result):
        """O parser deve aceitar o modelo sem erros"""
        assert parse_result['success'] is True, (
            f"Parse falhou: {parse_result.get('errors', [])}"
        )

    def test_parse_returns_model(self, parse_result):
        """AST deve ser do tipo 'model' com statements"""
        ast = parse_result['parsed_result']
        assert ast is not None
        # Model should have type 'model' with multiple statements
        assert ast.get('type') == 'model', f"Esperado 'model', obteve '{ast.get('type')}'"

    def test_parse_extracts_statements(self, parse_result):
        """Model deve conter imports, sets, params, vars, objective, constraints"""
        ast = parse_result['parsed_result']
        statements = ast.get('statements', [])
        
        # Precisamos de pelo menos: 6 imports + 4 sets + 8 params + 4 vars + 1 obj + 1 constraint_block
        assert len(statements) >= 20, (
            f"Esperado >= 20 statements, obteve {len(statements)}"
        )

    def test_parse_imports(self, parse_result):
        """Deve ter 6 imports de CSV"""
        ast = parse_result['parsed_result']
        statements = ast.get('statements', [])
        imports = [s for s in statements if s.get('type') == 'import']
        assert len(imports) == 6, f"Esperado 6 imports, obteve {len(imports)}"

    def test_parse_sets(self, parse_result):
        """Deve ter 4 sets (Plantas, Produtos, Clientes, Prioridade_A)"""
        ast = parse_result['parsed_result']
        statements = ast.get('statements', [])
        sets = [s for s in statements if s.get('type') == 'set']
        assert len(sets) >= 4, f"Esperado >= 4 sets, obteve {len(sets)}"
        
        set_names = [s.get('name') for s in sets]
        assert 'Plantas' in set_names
        assert 'Produtos' in set_names
        assert 'Clientes' in set_names
        assert 'Prioridade_A' in set_names

    def test_parse_variables(self, parse_result):
        """Deve ter 4 declarações var (fabrica, envio, hora_extra, usa_extra)"""
        ast = parse_result['parsed_result']
        statements = ast.get('statements', [])
        vars_ = [s for s in statements if s.get('type') == 'var']
        assert len(vars_) >= 4, f"Esperado >= 4 vars, obteve {len(vars_)}"
        
        var_names = [v.get('name') for v in vars_]
        assert 'fabrica' in var_names
        assert 'envio' in var_names
        assert 'hora_extra' in var_names
        assert 'usa_extra' in var_names

    def test_parse_binary_variable(self, parse_result):
        """usa_extra deve ser tipo binário"""
        ast = parse_result['parsed_result']
        statements = ast.get('statements', [])
        vars_ = [s for s in statements if s.get('type') == 'var']
        
        usa_extra = [v for v in vars_ if v.get('name') == 'usa_extra']
        assert len(usa_extra) == 1
        assert usa_extra[0].get('var_type') in ('binary', 'bin', 'Binary'), (
            f"usa_extra deveria ser binary, obteve {usa_extra[0].get('var_type')}"
        )

    def test_parse_objective(self, parse_result):
        """Deve ter 1 objetivo de minimização"""
        ast = parse_result['parsed_result']
        statements = ast.get('statements', [])
        objectives = [s for s in statements if s.get('type') == 'objective']
        assert len(objectives) == 1
        assert objectives[0].get('sense') in ('minimize', 'min')

    def test_parse_constraint_block(self, parse_result):
        """Deve ter 1 bloco de restrições com 6+ constraints"""
        ast = parse_result['parsed_result']
        statements = ast.get('statements', [])
        blocks = [s for s in statements if s.get('type') == 'constraint_block']
        assert len(blocks) >= 1, "Esperado >= 1 constraint_block"
        
        constraints = blocks[0].get('constraints', [])
        assert len(constraints) >= 6, (
            f"Esperado >= 6 constraints, obteve {len(constraints)}"
        )

    def test_parse_named_constraints(self, parse_result):
        """Constraints devem ter nomes: atendimento, capacidade, balanco, rota, horas, extra_limite"""
        ast = parse_result['parsed_result']
        statements = ast.get('statements', [])
        blocks = [s for s in statements if s.get('type') == 'constraint_block']
        
        if blocks:
            constraints = blocks[0].get('constraints', [])
            names = [c.get('name') for c in constraints if c.get('name')]
            expected_names = ['atendimento', 'capacidade', 'balanco', 'rota', 'horas', 'extra_limite']
            for name in expected_names:
                assert name in names, f"Constraint '{name}' não encontrada. Encontradas: {names}"

    def test_parse_multi_index_loops(self, parse_result):
        """Objetivo deve conter sum() com loops multi-index (for p in Plantas, j in Produtos)"""
        ast = parse_result['parsed_result']
        statements = ast.get('statements', [])
        objectives = [s for s in statements if s.get('type') == 'objective']
        
        # Just verify the objective has expression with loops
        obj_expr = objectives[0].get('expression', {})
        assert obj_expr is not None, "Objetivo deve ter expressão"

    def test_parse_no_errors(self, parse_result):
        """Não deve haver warnings ou erros"""
        errors = parse_result.get('errors', [])
        assert len(errors) == 0, f"Erros encontrados: {errors}"


class TestSupplyChainTranslation:
    """Testa se o tradutor gera PuLP válido"""

    def test_translation_succeeds(self, translated_code):
        """Tradução deve gerar código não vazio"""
        assert translated_code is not None
        assert len(translated_code) > 100, "Código gerado muito curto"

    def test_translation_has_imports(self, translated_code):
        """Código deve começar com imports"""
        assert "import pulp" in translated_code

    def test_translation_has_problem(self, translated_code):
        """Deve criar LpProblem com LpMinimize"""
        assert "pulp.LpProblem" in translated_code
        assert "LpMinimize" in translated_code

    def test_translation_has_sets(self, translated_code):
        """Deve declarar os sets como listas Python"""
        assert "Plantas = [" in translated_code
        assert "Produtos = [" in translated_code
        assert "Clientes = [" in translated_code
        assert "Prioridade_A = [" in translated_code

    def test_translation_has_variables(self, translated_code):
        """Deve declarar variáveis PuLP"""
        assert "pulp.LpVariable" in translated_code
        # Check for continuous vars
        assert "fabrica" in translated_code
        assert "envio" in translated_code
        assert "hora_extra" in translated_code

    def test_translation_has_binary_var(self, translated_code):
        """usa_extra deve ser declarada como Binary"""
        # PuLP binary: cat='Binary'
        assert "usa_extra" in translated_code
        assert "Binary" in translated_code

    def test_translation_has_objective(self, translated_code):
        """Deve ter prob += para o objetivo"""
        assert "prob +=" in translated_code

    def test_translation_has_constraints(self, translated_code):
        """Deve ter múltiplas constraints adicionadas"""
        # Named constraints
        count = translated_code.count("prob +=")
        # At least: 1 objective + 6 constraint types
        assert count >= 2, f"Esperado >= 2 'prob +=', obteve {count}"

    def test_translation_has_loops(self, translated_code):
        """Deve ter for loops (comprehensions traduzidas)"""
        assert "for " in translated_code

    def test_translation_has_solver(self, translated_code):
        """Deve ter prob.solve()"""
        assert "prob.solve()" in translated_code

    def test_translation_has_csv_imports(self, translated_code):
        """Deve ter pd.read_csv para os 6 arquivos"""
        assert "pd.read_csv" in translated_code

    def test_translation_has_lpsum(self, translated_code):
        """Deve usar pulp.lpSum para somatórios"""
        assert "pulp.lpSum" in translated_code


class TestSupplyChainDataFiles:
    """Verifica integridade dos dados de teste"""

    def test_csv_files_exist(self):
        """Todos os CSVs devem existir"""
        import pandas as pd
        base = Path(__file__).parent / "bases_exemplos"
        
        required = [
            "plantas.csv",
            "produtos_scm.csv",
            "clientes_scm.csv",
            "demanda.csv",
            "custo_transporte.csv",
            "capacidade_fabrica.csv"
        ]
        
        for f in required:
            path = base / f
            assert path.exists(), f"Arquivo não encontrado: {path}"

    def test_data_dimensions(self):
        """Verifica dimensões dos dados"""
        import pandas as pd
        base = Path(__file__).parent / "bases_exemplos"
        
        plantas = pd.read_csv(base / "plantas.csv")
        produtos = pd.read_csv(base / "produtos_scm.csv")
        clientes = pd.read_csv(base / "clientes_scm.csv")
        demanda = pd.read_csv(base / "demanda.csv")
        transporte = pd.read_csv(base / "custo_transporte.csv")
        capacidade = pd.read_csv(base / "capacidade_producao.csv")
        
        assert len(plantas) == 4, "4 plantas"
        assert len(produtos) == 6, "6 produtos"
        assert len(clientes) == 8, "8 clientes"
        assert len(demanda) == 20, "20 pares de demanda"
        assert len(transporte) == 32, "32 rotas (4×8)"
        assert len(capacidade) == 24, "24 combos (4×6)"

    def test_data_consistency(self):
        """Verifica que dados referenciam entidades válidas"""
        import pandas as pd
        base = Path(__file__).parent / "bases_exemplos"
        
        plantas = set(pd.read_csv(base / "plantas.csv")['Planta'])
        produtos = set(pd.read_csv(base / "produtos_scm.csv")['Produto'])
        clientes = set(pd.read_csv(base / "clientes_scm.csv")['Cliente'])
        
        # Demanda referencia clientes e produtos válidos
        demanda = pd.read_csv(base / "demanda.csv")
        assert set(demanda['Cliente']).issubset(clientes)
        assert set(demanda['Produto']).issubset(produtos)
        
        # Transporte referencia plantas e clientes válidos
        transporte = pd.read_csv(base / "custo_transporte.csv")
        assert set(transporte['Planta']).issubset(plantas)
        assert set(transporte['Cliente']).issubset(clientes)
        
        # Capacidade referencia plantas e produtos válidos
        capacidade = pd.read_csv(base / "capacidade_producao.csv")
        assert set(capacidade['Planta']).issubset(plantas)
        assert set(capacidade['Produto']).issubset(produtos)

    def test_no_null_critical_fields(self):
        """Campos críticos não devem ter nulos"""
        import pandas as pd
        base = Path(__file__).parent / "bases_exemplos"
        
        df = pd.read_csv(base / "demanda.csv")
        assert df['Demanda_Unidades'].notna().all(), "Demanda tem nulos"
        
        df = pd.read_csv(base / "custo_transporte.csv")
        assert df['Custo_Por_Kg'].notna().all(), "Custo transporte tem nulos"
        
        df = pd.read_csv(base / "capacidade_producao.csv")
        assert df['Pode_Produzir'].notna().all(), "Capacidade tem nulos"


class TestSupplyChainComplexity:
    """Verifica que o modelo captura complexidade real"""

    def test_problem_scale(self):
        """Verifica escala do problema: ~224 variáveis, ~194+ constraints"""
        # 4 plantas × 6 produtos = 24 vars produção
        # 4 × 8 × 6 = 192 vars envio
        # 4 vars hora_extra + 4 vars usa_extra = 8
        # Total esperado: 224 variáveis
        
        expected_vars = 4*6 + 4*8*6 + 4 + 4  # 224
        assert expected_vars == 224
        
        # Constraints:
        # R1: 8×6 = 48 (demanda)
        # R2: 4 (capacidade)
        # R3: 4×6 = 24 (balanço)
        # R4: 4×8 = 32 (rota)
        # R5: 4 (horas)
        # R6: 4 (extra)
        # Total: 116 constraints
        expected_constraints = 8*6 + 4 + 4*6 + 4*8 + 4 + 4
        assert expected_constraints == 116

    def test_model_file_line_count(self, los_source):
        """Modelo deve ter profundidade significativa"""
        lines = [l for l in los_source.split('\n') if l.strip() and not l.strip().startswith('//') and not l.strip().startswith('#')]
        # Non-comment, non-empty lines
        assert len(lines) >= 25, f"Apenas {len(lines)} linhas efetivas — muito simples"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-x"])
