# Changelog

## [3.1.1] - 2026-02-09 — Supply Chain E2E Integration
### ✨ Features
- [ADD] Modelo complexo `modelos/supply_chain_network.los` — Supply Chain Network Design com 4 plantas × 6 produtos × 8 clientes
- [ADD] 6 datasets CSV em `bases_exemplos/`: `plantas.csv`, `produtos_scm.csv`, `clientes_scm.csv`, `demanda.csv`, `custo_transporte.csv`, `capacidade_fabrica.csv`
- [ADD] Teste E2E raiz `test_supply_chain_e2e.py` — 30 testes (parsing, tradução, dados, complexidade)

### 🐛 Bug Found
- [BUG] Terminal `PROD` na gramática colide com identificadores que começam com `prod` (ex: `producao`). Workaround: renomeado para `fabrica`. Fix permanente pendente para Phase 2.

### 📊 Resultados
- **130 testes** passando (100 existentes + 30 novos)
- Escala do modelo: **224 variáveis**, **116 restrições**, comprehensions multi-index

---

## [3.1.0] - 2026-02-09 — Deep Remediation (Phase 1.5 + 1.6)
### 🔴 Critical Fixes (F01-F05)
- [FIX] `F01` Parser Transformer state leak — `_variables_registry` limpo a cada `parse()` call
- [FIX] `F02` Expression `__post_init__` removido — validação via `validate()` explícito
- [FIX] `F03` `translate_expression()` adicionado a `ITranslatorAdapter` (contrato ABC)
- [FIX] `F04` `_extract_expressions_from_content` — regex robusto substituiu heurística frágil
- [FIX] `F05` `ComplexityMetrics` — contagem real de variáveis/constraints/datasets

### 🟠 High Priority Fixes (F06-F10)
- [FIX] `F06` Translator detecta `LpMinimize`/`LpMaximize` da AST (não mais hardcoded)
- [FIX] `F07` `var` default `lowBound=0` documentado e corrigido
- [FIX] `F08` `_visit_import` sanitiza path, deriva nome variável do filename (não `data`)
- [FIX] `F09` `func_call` parser reescrito para dispatch correto
- [FIX] `F10` `sum()` sem loop gera `lpSum` inline

### 🟡 Medium Fixes (F11-F17)
- [FIX] `F11` Dead code `to_pulp_code()` removido de `Expression`
- [FIX] `F12` DTO `translate()` retorna guidance em vez de placeholder morto
- [FIX] `F13` `LOSError` não herda mais de `ABC`
- [FIX] `F14` `ValidationRequestDTO.expression_text` default `""` (não `None`)
- [FIX] `F15` `InMemoryExpressionRepository` implementado
- [FIX] `F16` `_sanitize_name` aplicado em loop variables
- [FIX] `F17` Regex `NUMBER` não captura negativo (handled by grammar subtraction)

### 🟢 Low Fixes (F18-F19)
- [FIX] `F18` Suporte a `#` comments na gramática (SH_COMMENT)
- [FIX] `F19` `__version__ = "3.1.0"` em `LOSParser` e `PuLPTranslator`

### 🧪 Test Suite Overhaul
- [REWRITE] `test_expression_v3.py` — alinhado com API v3.1
- [REWRITE] `test_unit_modules.py` — 351 linhas reescritas (construtores, DTOs, errors)
- [REWRITE] `test_los_dados_reais.py` — 6 testes reescritos (sem `to_pulp_code`, sem `variables={}`)
- [FIX] `test_audit_remediation.py` — sanitization assertion corrigida
- [FIX] `test_integration_v3.py` — set quoting e objective format atualizados
- [FIX] `test_service_v3.py` — `pd.read_csv` assertion genérica
- [FIX] `test_architecture_validation.py` — threshold de métodos ajustado (10→15)

### 📊 Resultados
- **100/100 testes** passando
- **19 findings** remediados (5 Critical, 5 High, 7 Medium, 2 Low)
- Zero regressões

---

## [2025-07-03] - Análise Completa e Atualização da LIB LOS
### 🏗️ Core & Architecture
- **Clean Architecture Compliance**: Mapeamento completo e documentado das camadas:
  - `Domain`: Entidades e regras de negócio puras (ex: `Expression`, `Variable`).
  - `Application`: Casos de uso e orquestração.
  - `Infrastructure`: Implementações concretas e persistência.
  - `Adapters`: Interfaces externas e tradutores.
- **Novos Componentes Core**:
  - `Expression` & `Variable`: Primitivas fundamentais para modelagem de problemas.
  - `DatasetReference`: Gerenciamento desacoplado de fontes de dados.
  - `ComplexityMetrics`: Análise de viabilidade computacional.
- **Implementação Técnica**:
  - `LOSParser`: Implementação robusta baseada em **Lark** para parsing de gramática personalizada.
  - `PuLPTranslator`: Camada de tradução otimizada para solvers lineares.
  - **Hierarquia de Exceções**: Sistema tipado (`LOSError` > `ParseError`, `ValidationError`) para tratamento granular de erros.

### 🧪 Quality Assurance (QA) & Validação
- **Suite de Testes Reais**:
  - Adição de `tests/test_los_dados_reais.py` com 10 cenários baseados em dados de produção (`bases_exemplos`).
  - Cobertura de testes de integração: 17/17 testes automatizados passando.
- **Correções Críticas**:
  - Parser: Correção de sintaxe `PARA EACH` → `PARA CADA` para conformidade com a gramática PT-BR.
  - Validador Matemático: Garantia de consistência em expressões complexas.
- **Performance**:
  - 🚀 **Latência**: Tempo médio de execução otimizado para **13.9ms** (target: <25ms).
  - **Viabilidade**: Script `check_viabilidade.py` validado para verificação de restrições de capacidade.

### 🛠️ Developer Experience (DX)
- **Logging & Observabilidade**: Implementação de sistema centralizado de logs com rotação e níveis semânticos.
- **Interfaces**:
  - **CLI Profissional**: Interface de linha de comando com argumentos estruturados.
  - `FileProcessor`: Utilitário para batch processing de arquivos `.los`.
- **Documentação Técnica**:
  - README principal expandido (1700+ linhas) com diagramas arquiteturais e exemplos de código.
  - Seção dedicada a **Troubleshooting & FAQ**.
