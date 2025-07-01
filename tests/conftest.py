"""
Configuração dos testes para LOS - Linguagem de Otimização Simples
Fixtures e configurações globais para todos os testes
"""
import sys
import os
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock
from typing import Dict, List, Any

# Adicionar o diretório raiz do projeto ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configurar pytest
pytest_plugins = []


# ========================= FIXTURES GLOBAIS =========================

@pytest.fixture(scope="session")
def project_root_path():
    """Fixture que retorna o caminho raiz do projeto"""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def sample_datasets():
    """Fixture com datasets de exemplo para testes"""
    return {
        'produtos': [
            {'id': 1, 'nome': 'Produto A', 'custo': 10.0, 'preco': 15.0, 'capacidade': 100},
            {'id': 2, 'nome': 'Produto B', 'custo': 20.0, 'preco': 30.0, 'capacidade': 150},
            {'id': 3, 'nome': 'Produto C', 'custo': 15.0, 'preco': 25.0, 'capacidade': 200}
        ],
        'clientes': [
            {'id': 1, 'nome': 'Cliente Alpha', 'demanda': 100, 'prioridade': 'alta'},
            {'id': 2, 'nome': 'Cliente Beta', 'demanda': 200, 'prioridade': 'media'},
            {'id': 3, 'nome': 'Cliente Gamma', 'demanda': 150, 'prioridade': 'baixa'}
        ],
        'fornecedores': [
            {'id': 1, 'nome': 'Fornecedor X', 'capacidade': 500, 'custo_fixo': 1000},
            {'id': 2, 'nome': 'Fornecedor Y', 'capacidade': 800, 'custo_fixo': 1500},
            {'id': 3, 'nome': 'Fornecedor Z', 'capacidade': 300, 'custo_fixo': 800}
        ],
        'materiais': [
            {'id': 1, 'nome': 'Material M1', 'custo_unitario': 5.0, 'estoque': 1000},
            {'id': 2, 'nome': 'Material M2', 'custo_unitario': 8.0, 'estoque': 800},
            {'id': 3, 'nome': 'Material M3', 'custo_unitario': 12.0, 'estoque': 600}
        ]
    }


@pytest.fixture(scope="session")
def sample_expressions():
    """Fixture com expressões de exemplo categorizadas"""
    return {
        'objectives': [
            "MINIMIZAR: x + y",
            "MAXIMIZAR: 2*a - 3*b",
            "MINIMIZAR: SOMA DE custos[i] * quantidade[i] PARA i EM produtos",
            "MAXIMIZAR: SOMA DE lucros[j] * vendas[j] PARA j EM servicos",
            "MINIMIZAR: SOMA DE SE custos[i] > limite ENTAO custos[i] * 2 SENAO custos[i] PARA i EM produtos"
        ],
        'constraints': [
            "RESTRINGIR: x >= 0",
            "RESTRINGIR: y <= 100",
            "RESTRINGIR: x + y <= capacidade_total",
            "RESTRINGIR: SOMA DE quantidade[i] PARA i EM produtos >= demanda_minima",
            "RESTRINGIR: quantidade[i] >= 0 PARA TODO i EM produtos",
            "RESTRINGIR: quantidade[i] <= capacidade[i] PARA TODO i EM produtos"
        ],
        'assignments': [
            "x = 5",
            "y = x + 10",
            "total = SOMA DE valores[k] PARA k EM itens",
            "lucro = receita - custos",
            "media = SOMA DE notas[i] PARA i EM alunos / total_alunos"
        ],
        'complex': [
            "MINIMIZAR: SOMA DE (custos_fixos[i] + custos_variaveis[i] * quantidade[i]) PARA i EM produtos",
            "RESTRINGIR: SOMA DE materiais[i][j] * quantidade[i] PARA i EM produtos <= estoque[j] PARA TODO j EM materiais",
            "MAXIMIZAR: SOMA DE SE demanda[i] > 0 ENTAO min(capacidade[i], demanda[i]) * preco[i] SENAO 0 PARA i EM produtos"
        ],
        'invalid': [
            "MINIMIZAR:",
            "INVALID_KEYWORD: x + y",
            "MINIMIZAR: x + + y",
            "SOMA DE PARA EM",
            "",
            "   ",
            "RESTRINGIR PARA EM ONDE"
        ]
    }


@pytest.fixture
def mock_expression_service():
    """Fixture com mock do serviço de expressões"""
    service = Mock()
    
    # Configurar métodos principais
    service.parse_expression = Mock()
    service.validate_expression = Mock()
    service.process_batch = Mock()
    service.get_statistics = Mock()
    
    # Configurar retorno padrão do parse_expression
    mock_response = Mock()
    mock_response.success = True
    mock_response.expression_id = "mock-expr-001"
    mock_response.expression_type = "objective"
    mock_response.operation_type = "minimize"
    mock_response.variables = []
    mock_response.dataset_references = []
    mock_response.complexity = 1
    mock_response.processing_time = 0.01
    mock_response.errors = []
    
    service.parse_expression.return_value = mock_response
    
    return service


@pytest.fixture
def mock_parser():
    """Fixture com mock do parser LOS"""
    parser = Mock()
    
    # Configurar método parse
    mock_result = Mock()
    mock_result.expression_type = "objective"
    mock_result.operation_type = "minimize"
    mock_result.variables = []
    mock_result.dataset_references = []
    mock_result.is_valid = Mock(return_value=True)
    mock_result.calculate_complexity = Mock(return_value=1)
    
    parser.parse = Mock(return_value=mock_result)
    
    return parser


@pytest.fixture
def mock_translator():
    """Fixture com mock do tradutor"""
    translator = Mock()
    
    # Configurar método translate
    sample_pulp_code = """
# Código PuLP gerado automaticamente
from pulp import *

# Definir problema
prob = LpProblem("LOS_Problem", LpMinimize)

# Definir variáveis
x = LpVariable("x", lowBound=0)
y = LpVariable("y", lowBound=0)

# Função objetivo
prob += x + y

# Resolver
prob.solve()
"""
    
    translator.translate = Mock(return_value=sample_pulp_code)
    
    return translator


@pytest.fixture
def mock_validator():
    """Fixture com mock do validador"""
    validator = Mock()
    
    # Configurar método validate
    validator.validate = Mock(return_value=(True, []))
    
    return validator


@pytest.fixture
def temp_los_files(tmp_path, sample_expressions):
    """Fixture que cria arquivos .los temporários para teste"""
    files = {}
    
    # Criar arquivo de objetivos
    objectives_file = tmp_path / "objectives.los"
    objectives_content = "\n".join(sample_expressions['objectives'])
    objectives_file.write_text(objectives_content, encoding='utf-8')
    files['objectives'] = objectives_file
    
    # Criar arquivo de restrições
    constraints_file = tmp_path / "constraints.los"
    constraints_content = "\n".join(sample_expressions['constraints'])
    constraints_file.write_text(constraints_content, encoding='utf-8')
    files['constraints'] = constraints_file
    
    # Criar arquivo complexo
    complex_file = tmp_path / "complex.los"
    complex_content = "\n".join(sample_expressions['complex'])
    complex_file.write_text(complex_content, encoding='utf-8')
    files['complex'] = complex_file
    
    # Criar arquivo com problemas
    invalid_file = tmp_path / "invalid.los"
    invalid_content = "\n".join(sample_expressions['invalid'])
    invalid_file.write_text(invalid_content, encoding='utf-8')
    files['invalid'] = invalid_file
    
    return files


@pytest.fixture
def performance_timer():
    """Fixture para medir performance dos testes"""
    import time
    
    class PerformanceTimer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            self.measurements = {}
        
        def start(self, label="default"):
            self.start_time = time.time()
            self.measurements[label] = {'start': self.start_time}
        
        def stop(self, label="default"):
            self.end_time = time.time()
            if label in self.measurements:
                self.measurements[label]['end'] = self.end_time
                self.measurements[label]['duration'] = self.end_time - self.measurements[label]['start']
        
        def get_duration(self, label="default"):
            if label in self.measurements and 'duration' in self.measurements[label]:
                return self.measurements[label]['duration']
            return None
        
        def assert_performance(self, label, max_duration):
            duration = self.get_duration(label)
            assert duration is not None, f"Medição '{label}' não encontrada"
            assert duration <= max_duration, f"Performance insuficiente: {duration:.3f}s > {max_duration}s"
    
    return PerformanceTimer()


@pytest.fixture
def error_collector():
    """Fixture para coletar e analisar erros durante testes"""
    class ErrorCollector:
        def __init__(self):
            self.errors = []
            self.warnings = []
        
        def add_error(self, error, context=None):
            self.errors.append({
                'error': error,
                'context': context,
                'type': type(error).__name__
            })
        
        def add_warning(self, message, context=None):
            self.warnings.append({
                'message': message,
                'context': context
            })
        
        def has_errors(self):
            return len(self.errors) > 0
        
        def has_warnings(self):
            return len(self.warnings) > 0
        
        def get_error_summary(self):
            if not self.has_errors():
                return "Nenhum erro encontrado"
            
            error_types = {}
            for error_info in self.errors:
                error_type = error_info['type']
                error_types[error_type] = error_types.get(error_type, 0) + 1
            
            return f"Erros encontrados: {error_types}"
        
        def assert_no_critical_errors(self):
            critical_error_types = ['ParseError', 'ValidationError', 'SystemError']
            critical_errors = [e for e in self.errors if e['type'] in critical_error_types]
            
            assert len(critical_errors) == 0, f"Erros críticos encontrados: {[e['type'] for e in critical_errors]}"
    
    return ErrorCollector()


# ========================= CONFIGURAÇÕES DE TESTE =========================

def pytest_configure(config):
    """Configuração global do pytest"""
    # Adicionar marcadores customizados
    config.addinivalue_line(
        "markers", "slow: marca testes como lentos"
    )
    config.addinivalue_line(
        "markers", "integration: marca testes de integração"
    )
    config.addinivalue_line(
        "markers", "unit: marca testes unitários"
    )
    config.addinivalue_line(
        "markers", "performance: marca testes de performance"
    )


def pytest_collection_modifyitems(config, items):
    """Modifica a coleta de testes"""
    # Adicionar marcadores automaticamente baseado nos nomes dos arquivos
    for item in items:
        # Marcar testes de integração
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Marcar testes unitários
        if "unit" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        
        # Marcar testes de performance
        if "performance" in item.name.lower() or "benchmark" in item.name.lower():
            item.add_marker(pytest.mark.performance)


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Fixture que roda automaticamente antes de cada teste"""
    # Setup
    original_path = sys.path.copy()
    
    yield
    
    # Teardown
    sys.path = original_path


# ========================= HELPERS PARA TESTES =========================

class TestHelper:
    """Classe com métodos auxiliares para testes"""
    
    @staticmethod
    def create_mock_expression(expr_type="objective", operation="minimize"):
        """Cria mock de expressão para testes"""
        mock_expr = Mock()
        mock_expr.expression_type = expr_type
        mock_expr.operation_type = operation
        mock_expr.variables = []
        mock_expr.dataset_references = []
        mock_expr.complexity = 1
        mock_expr.is_valid = Mock(return_value=True)
        return mock_expr
    
    @staticmethod
    def create_mock_response(success=True, expr_id="test-001"):
        """Cria mock de resposta para testes"""
        mock_response = Mock()
        mock_response.success = success
        mock_response.expression_id = expr_id
        mock_response.errors = [] if success else ["Mock error"]
        return mock_response
    
    @staticmethod
    def assert_expression_structure(expression_result):
        """Valida estrutura básica de resultado de expressão"""
        assert hasattr(expression_result, 'expression_type')
        assert hasattr(expression_result, 'variables')
        assert hasattr(expression_result, 'dataset_references')


@pytest.fixture
def test_helper():
    """Fixture para acessar métodos auxiliares"""
    return TestHelper
