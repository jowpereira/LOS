# 🚀 LOS - Linguagem de Otimização Simples

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> **Uma biblioteca Python moderna e robusta para análise, validação e tradução de expressões de otimização matemática.**

⚠️ **AVISO**: Este é um software proprietário. Uso comercial requer licenciamento. Entre em contato: jonathan@example.com

## ✨ Características

- 🏗️ **Arquitetura Clean**: Baseada em Clean Architecture e Hexagonal Architecture
- 🔧 **Modular**: Componentes desacoplados e extensíveis
- 🧪 **Testável**: 90%+ cobertura de testes com mocks e stubs
- 🚀 **Performance**: Cache inteligente e otimizações de parsing
- 📝 **Type Safe**: 100% tipado com mypy
- 🌐 **Multi-target**: Suporte a PuLP, SciPy, CVXPY e mais
- 🎯 **CLI Profissional**: Interface de linha de comando rica
- 📚 **Documentação Rica**: Guias, API docs e exemplos

## 📦 Uso

Esta é uma biblioteca modular para desenvolvimento e integração local. Não requer instalação via pip.

Para usar a biblioteca:

```python
# Adicione o caminho da biblioteca ao seu projeto
import sys
sys.path.append('caminho/para/los')

from los import ExpressionService, LOSParser
```

## 🚀 Início Rápido

### Uso Básico

```python
from los import LOSParser, PuLPTranslator, ExpressionService

# Inicialização simples
parser = LOSParser()
translator = PuLPTranslator()

# Análise de expressão
result = parser.parse("MINIMIZAR: 2*x + 3*y")
print(f"Tipo: {result.expression_type}")  # objective
print(f"Operação: {result.operation_type}")  # minimize

# Tradução para PuLP
pulp_code = translator.translate(result)
print(pulp_code)
```

### Uso Avançado com Serviços

```python
from los.application.services import ExpressionService
from los.application.dto import ExpressionRequestDTO

# Configuração de serviço completo
service = ExpressionService.create_default()

# Análise completa com validação
request = ExpressionRequestDTO(
    text="MINIMIZAR: soma de custos[i] * x[i] PARA i EM produtos",
    validate=True,
    save_result=True
)

result = await service.parse_expression(request)

if result.success:
    print(f"✅ Expressão válida!")
    print(f"Variáveis: {result.variables}")
    print(f"Datasets: {result.dataset_references}")
    print(f"Complexidade: {result.complexity}")
else:
    print(f"❌ Erros: {result.errors}")
```

### Interface CLI

```bash
# Análise rápida
los parse "MINIMIZAR: x + y"

# Processamento de arquivo
los process-file problema.los --output solucao.py

# Validação
los validate "RESTRINGIR: x >= 0"

# Tradução para diferentes targets
los translate "MAXIMIZAR: lucro" --target pulp --output modelo.py

# Estatísticas do sistema
los stats

# Informações detalhadas
los info
```

## 📊 Exemplos de Uso

### Problema de Otimização Linear

```python
from los import ExpressionService

service = ExpressionService.create_default()

# Definição do problema
objetivo = "MINIMIZAR: soma de custos[produto] * quantidade[produto] PARA produto EM produtos"
restricoes = [
    "RESTRINGIR: soma de quantidade[produto] PARA produto EM produtos >= demanda_total",
    "RESTRINGIR: quantidade[produto] >= 0 PARA TODO produto EM produtos",
    "RESTRINGIR: quantidade[produto] <= capacidade[produto] PARA TODO produto EM produtos"
]

# Processamento
for expressao in [objetivo] + restricoes:
    result = await service.parse_expression(ExpressionRequestDTO(text=expressao))
    print(f"✅ {expressao} → {result.expression_type}")
```

### Integração com Datasets

```python
import pandas as pd
from los.adapters.file import LOSFileProcessor

# Carregamento de dados
dados = {
    'produtos': pd.read_csv('produtos.csv'),
    'custos': pd.read_csv('custos.csv')
}

# Processamento de arquivo .los
processor = LOSFileProcessor()
resultado = processor.process_file('modelo.los', datasets=dados)

print(f"Expressões processadas: {len(resultado.expressions)}")
print(f"Código Python gerado: {resultado.python_code}")
```

## 🏗️ Arquitetura

A biblioteca LOS segue os princípios de Clean Architecture:

```
los/
├── domain/          # 🏛️ Regras de negócio puras
│   ├── entities/    # Entidades principais
│   ├── value_objects/ # Objetos de valor
│   ├── use_cases/   # Casos de uso
│   └── repositories/ # Interfaces de dados
├── application/     # 🔧 Serviços de aplicação
│   ├── services/    # Orquestração
│   ├── dto/         # Data Transfer Objects
│   └── interfaces/  # Contratos externos
├── infrastructure/ # 🏗️ Implementações técnicas
│   ├── parsers/     # Analisadores sintáticos
│   ├── translators/ # Tradutores de código
│   └── validators/  # Validadores especializados
├── adapters/       # 🌐 Adaptadores externos
│   ├── cli/         # Interface de linha de comando
│   └── file/        # Processamento de arquivos
└── shared/         # 🔄 Código compartilhado
    ├── logging/     # Sistema de logging
    ├── errors/      # Tratamento de erros
    └── utils/       # Utilitários comuns
```

## 🎯 Funcionalidades

### Parser Robusto

- ✅ Gramática Lark otimizada
- ✅ Análise sintática e semântica
- ✅ Detecção de erros contextual
- ✅ Suporte a expressões complexas

### Validação Inteligente

- ✅ Regras de negócio configuráveis
- ✅ Validação de tipos e estruturas
- ✅ Detecção de inconsistências
- ✅ Sugestões de correção

### Tradução Multi-target

- ✅ **PuLP**: Programação linear
- ✅ **SciPy**: Otimização científica
- ✅ **CVXPY**: Programação convexa
- ✅ **Extensível**: Interface para novos targets

### CLI Profissional

- ✅ Interface rica com Click
- ✅ Cores e formatação com Rich
- ✅ Processamento em lote
- ✅ Relatórios detalhados

## 📈 Performance

```python
# Benchmark típico (Intel i7, 16GB RAM)
import time
from los import LOSParser

parser = LOSParser()

# Expressão simples
start = time.time()
result = parser.parse("MINIMIZAR: x + y")
simple_time = time.time() - start  # ~0.001s

# Expressão complexa
start = time.time()
result = parser.parse("MINIMIZAR: soma de custos[i,j] * x[i,j] PARA i EM cidades, j EM produtos")
complex_time = time.time() - start  # ~0.005s

print(f"Simples: {simple_time:.3f}s, Complexa: {complex_time:.3f}s")
```

## 🧪 Desenvolvimento

### Configuração do Ambiente

```bash
# Clone do repositório
git clone https://github.com/jonathan/los.git
cd los

# Ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instalação em modo desenvolvimento
pip install -e ".[dev]"

# Pre-commit hooks
pre-commit install
```

### Executando Testes

```bash
# Testes completos
pytest

# Com cobertura
pytest --cov=los --cov-report=html

# Testes específicos
pytest tests/test_parser.py -v

# Tox para múltiplas versões
tox
```

## 📋 Roadmap

### v2.1.0 (Q1 2025)

- [ ] Suporte a CVXPY
- [ ] Interface web com FastAPI
- [ ] Otimizações de performance
- [ ] Plugin system

### v2.2.0 (Q2 2025)

- [ ] Suporte a OR-Tools
- [ ] Machine Learning integration
- [ ] Cloud deployment tools
- [ ] GraphQL API

### v3.0.0 (Q3 2025)

- [ ] Reescrita do core em Rust
- [ ] WebAssembly support
- [ ] Distributed solving
- [ ] Advanced visualization

<div align="center">

**⭐ Se este projeto foi útil, considere dar uma estrela no GitHub! ⭐**

Made with ❤️ by [Jonathan Pereira](https://github.com/jonathan)

</div>
