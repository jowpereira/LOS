# 🧪 Testes do Parser LOS

Estrutura completa de testes para validação do Parser LOS (Linguagem de Otimização Simples).

## 📁 Estrutura de Diretórios

```
tests/
├── conftest.py                     # Configurações e fixtures do pytest
├── executar_testes.py             # Script principal para execução dos testes
├── unit/                          # Testes unitários
│   ├── test_lexer.py             # Testes do LexerLOS
│   ├── test_tradutor.py          # Testes do TradutorCompleto
│   └── test_parser.py            # Testes do ParserLinguagemSimples
├── integration/                   # Testes de integração
│   └── test_cenarios_reais.py    # Cenários reais de otimização
├── fixtures/                     # Dados e casos de teste
│   └── casos_teste.py           # Casos de teste predefinidos
├── utils/                        # Utilitários de teste
│   └── validadores.py           # Validadores de código gerado
└── performance/                  # Testes de performance (futuro)
```

## 🚀 Execução Rápida

### Executar Todos os Testes
```bash
cd tests/
python executar_testes.py
```

### Executar com pytest (se instalado)
```bash
cd tests/
pytest -v
```

## 📊 Cobertura de Testes

### Componentes Testados

#### 🔤 LexerLOS (`test_lexer.py`)
- ✅ Tokenização básica (números, strings, identificadores)
- ✅ Operadores relacionais compostos (<=, >=, !=)
- ✅ Palavras-chave da linguagem LOS
- ✅ Colunas com espaços ('Nome do Cliente')
- ✅ Estruturas de controle (PARA CADA, ONDE, SE/ENTAO)
- ✅ Funções agregadas (soma de, max, min)
- ✅ Posicionamento e informações de linha/coluna
- ✅ Performance com textos longos

#### 🔄 TradutorCompleto (`test_tradutor.py`)
- ✅ Tradução de expressões matemáticas
- ✅ Referências a datasets (dataset.coluna → dataset["coluna"])
- ✅ Agregações (suma de → sum([...]))
- ✅ Loops (PARA CADA → for...in)
- ✅ Condicionais (SE/ENTAO/SENAO → if...else)
- ✅ Operadores lógicos (E/OU/NAO → and/or/not)
- ✅ Integração soma + loops
- ✅ Funções matemáticas (max, min, abs, etc.)
- ✅ Preservação de precedência de operadores

#### 📝 ParserLinguagemSimples (`test_parser.py`)
- ✅ Análise de objetivos (MINIMIZAR/MAXIMIZAR)
- ✅ Análise de restrições (<=, >=, =)
- ✅ Detecção automática de variáveis de decisão
- ✅ Carregamento e mapeamento de dados CSV
- ✅ Tradução completa para código PuLP
- ✅ Preprocessamento de texto (comentários, espaços)
- ✅ Análise de múltiplas restrições
- ✅ Filtragem de palavras reservadas e datasets

#### 🏗️ Integração (`test_cenarios_reais.py`)
- ✅ Cenário: Otimização de produção
- ✅ Cenário: Gestão de estoque
- ✅ Cenário: Priorização de clientes Premium
- ✅ Cenário: Otimização multiobjetivo
- ✅ Cenário: Planejamento por plantas
- ✅ Validação com dados reais (5 CSVs)
- ✅ Compatibilidade com PuLP
- ✅ Detecção de limitações do parser atual

## 🎯 Casos de Teste Críticos

### Objetivos
```python
# Objetivo simples
"MINIMIZAR: x + y"

# Objetivo com agregação
"MINIMIZAR: soma de produtos.Custo_Producao * x[produto] PARA CADA produto EM produtos"

# Objetivo com condição
"MAXIMIZAR: soma de produtos.Margem_Lucro * x[produto] PARA CADA produto EM produtos ONDE produtos.Ativo = 1"
```

### Restrições
```python
# Restrição simples
"x + y <= 100"

# Restrição com agregação
"soma de x[produto] PARA CADA produto EM produtos <= 1000"

# Restrição de balanceamento
"soma de ordens.Quantidade PARA CADA ordem EM ordens ONDE ordens.Produto = 'PROD_A' <= estoque.Quantidade_Disponivel"
```

### Expressões Complexas
```python
# Loops aninhados
"soma de x[produto,planta] PARA CADA produto EM produtos PARA CADA planta EM plantas"

# Condicionais aninhadas
"SE produtos.Ativo = 1 ENTAO produtos.Custo * x[produto] SENAO 999"

# Joins entre datasets
"clientes.Tipo_Cliente = custos.Tipo_Cliente E custos.Tipo_Custo = 'Atraso'"
```

## 📈 Métricas de Qualidade

### Validações Automáticas
- **Sintaxe Python**: Código gerado é Python válido
- **Compatibilidade PuLP**: Estruturas compatíveis com PuLP
- **Balanceamento**: Parênteses e colchetes balanceados
- **Estrutura**: Presença de padrões esperados (sum, for, if)

### Análise de Complexidade
- **Contagem de operadores**: sum, max, min, for, if, and, or
- **Detecção de datasets**: Referências automáticas
- **Variáveis encontradas**: Extração de variáveis de decisão
- **Nível de aninhamento**: Loops e condições aninhadas

## ⚠️ Limitações Identificadas

### Casos que Podem Falhar
1. **Precedência complexa**: `a + b * c / d - e`
2. **Aninhamento profundo**: Múltiplos loops aninhados
3. **Condicionais aninhadas**: `SE...ENTAO SE...ENTAO...SENAO...SENAO`
4. **Joins complexos**: Múltiplos datasets com várias condições
5. **Parênteses aninhados**: `((a + b) * (c - d)) / ((e + f) * (g - h))`

### Indicadores para Migração Lark
- Taxa de falha > 50% em casos complexos
- Problemas de precedência de operadores
- Dificuldade em estender gramática
- Tratamento inadequado de erros

## 🛠️ Executando Testes Específicos

### Apenas Lexer
```python
from tests.unit.test_lexer import TestLexerLOS
test_lexer = TestLexerLOS()
# Execute métodos específicos
```

### Apenas Tradutor
```python
from tests.unit.test_tradutor import TestTradutorCompleto
test_tradutor = TestTradutorCompleto()
# Execute métodos específicos
```

### Cenários de Integração
```python
from tests.integration.test_cenarios_reais import TestIntegracaoCompleta
test_integracao = TestIntegracaoCompleta()
# Execute cenários específicos
```

## 📊 Relatórios de Validação

O sistema gera relatórios detalhados para cada código traduzido:

```
=== RELATÓRIO DE VALIDAÇÃO ===
Código: sum([produtos["Custo_Producao"] * x[produto] for produto in produtos])

✅ VALIDAÇÕES BÁSICAS:
- Python válido: True
- Compatível PuLP: True
- Parênteses balanceados: True

📊 ANÁLISE ESTRUTURAL:
- Variáveis: x
- Datasets: produtos
- Complexidade: 5

🔄 LOOPS & OPERADORES:
- Total FORs: 1
- Aninhados: 0
- Operadores: {'sum': 1, 'for': 1, 'if': 0}

🎯 PADRÕES PULP:
- Compreensão de lista: True
- Função sum(): True
- Variáveis indexadas: True
```

## 🎮 Dados de Exemplo

Os testes utilizam 5 CSVs realísticos:

- **produtos_exemplo.csv**: Custo_Producao, Margem_Lucro, Tempo_Producao
- **clientes_exemplo.csv**: Codigo_Cliente, Tipo_Cliente
- **ordens_exemplo.csv**: Numero_OV, Produto, Quantidade, Cliente
- **estoque_exemplo.csv**: Produto, Planta, Quantidade_Disponivel
- **custos_exemplo.csv**: Tipo_Cliente, Tipo_Custo, Valor_Custo

## 🏁 Interpretação dos Resultados

### ✅ Parser Funcional (Taxa > 80%)
- Continuar com arquitetura atual
- Focar em melhorias incrementais
- Implementar casos específicos que falharam

### ⚠️ Parser com Limitações (Taxa 60-80%)
- Considerar migração para Lark
- Avaliar custo-benefício
- Implementar casos críticos primeiro

### 🚨 Parser Inadequado (Taxa < 60%)
- Migração para Lark altamente recomendada
- Parser atual insuficiente para uso real
- Lark necessário para robustez

## 🔮 Próximos Passos

1. **Automatização**: Integrar testes ao CI/CD
2. **Coverage**: Atingir 95% de cobertura de código
3. **Performance**: Benchmarks com datasets grandes
4. **Lark**: Implementar parser alternativo se necessário
5. **PuLP**: Validação real com otimizador

---

**Estrutura de testes criada para garantir qualidade e robustez do Parser LOS** 🎯
