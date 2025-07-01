# 📚 Documentação da Gramática LOS (Linguagem de Otimização Simples)

## 📋 Introdução

Este documento detalha a gramática formal da Linguagem de Otimização Simples (LOS), implementada usando o framework Lark para Python. A gramática define a sintaxe e estrutura permitidas na linguagem LOS, que é projetada para expressar problemas de otimização matemática em um formato próximo da linguagem natural.

## 🔄 Visão Geral da Gramática

A gramática LOS é definida no arquivo `los_grammar.lark` e consiste em regras para expressões matemáticas, objetivos de otimização, restrições, operadores e elementos básicos. A implementação utiliza o método LALR (Look-Ahead LR) de parsing para eficiência e precisão.

## 📊 Estruturas Básicas

### Expressões Principais
```lark
?start: expressao

?expressao: objetivo | restricao | expressao_condicional | expressao_matematica
```

- `expressao`: Ponto de entrada da gramática
- Pode ser um objetivo, restrição, expressão condicional ou expressão matemática

### Objetivos de Otimização
```lark
objetivo: "MINIMIZAR" ":" expressao_matematica -> objetivo_minimizar
        | "MAXIMIZAR" ":" expressao_matematica -> objetivo_maximizar
```

- Define objetivos de minimização ou maximização
- Seguido por dois-pontos e uma expressão matemática

### Restrições
```lark
restricao: expressao_matematica operador_relacional expressao_matematica
```

- Compara duas expressões matemáticas com um operador relacional
- Exemplo: `x + y <= 100`

### Expressões Condicionais
```lark
expressao_condicional: "SE" expressao_comparacao "ENTAO" expressao_matematica "SENAO" expressao_matematica
```

- Estrutura de decisão condicional
- Exemplo: `SE x > 0 ENTAO x SENAO 0`

## 📐 Expressões Matemáticas

### Operações Matemáticas
```lark
?expressao_matematica: soma | agregacao | loop

?soma: soma op_aditivo produto -> operacao_aditiva
     | produto

?produto: produto op_multiplicativo fator -> operacao_multiplicativa  
        | fator

op_aditivo: "+" | "-"
op_multiplicativo: "*" | "/"
```

- Implementa precedência correta de operadores
- Multiplicação/divisão tem precedência sobre adição/subtração

### Fatores
```lark
?fator: numero
      | string
      | IDENTIFICADOR
      | IDENTIFICADOR "." IDENTIFICADOR -> referencia_dataset
      | IDENTIFICADOR "[" indices "]" -> variavel_indexada
      | nome_funcao "(" argumentos ")" -> funcao_matematica
      | "(" expressao_matematica ")"
```

- Elementos básicos de expressões matemáticas
- Inclui números, identificadores, referências a datasets, variáveis indexadas, etc.

## 🔄 Agregações e Loops

### Agregação
```lark
?agregacao: "SOMA" "DE" expressao_matematica loop?
```

- Implementa funções de agregação como `soma de`
- Pode ser seguido por um loop opcional

### Loops
```lark
?loop: "PARA" "CADA" IDENTIFICADOR "EM" IDENTIFICADOR condicao_onde?

?condicao_onde: "ONDE" expressao_comparacao
```

- Define iteração sobre conjuntos
- Exemplo: `PARA CADA produto EM produtos`
- Pode incluir condição de filtro com `ONDE`

## 🔣 Operadores e Tokens

### Operadores Relacionais
```lark
operador_relacional: MENOR_IGUAL | MAIOR_IGUAL | IGUAL_IGUAL | DIFERENTE | IGUAL | MENOR | MAIOR

MENOR_IGUAL: "<="
MAIOR_IGUAL: ">="
IGUAL_IGUAL: "=="
DIFERENTE: "!="
IGUAL: "="
MENOR: "<"
MAIOR: ">"
```

- Define operadores para comparações
- Suporta operadores padrão e compostos

### Tokens Básicos
```lark
NUMERO: /\d+(\.\d+)?/
STRING: /'[^']*'/ | /"[^"]*"/
IDENTIFICADOR: /[a-zA-Z_][a-zA-Z0-9_]*/
```

- Define padrões para números, strings e identificadores
- Números podem ser inteiros ou decimais
- Strings podem usar aspas simples ou duplas
- Identificadores seguem convenção padrão

## 🔄 Exemplos de Uso da Gramática

### Exemplo 1: Objetivo de Minimização
```
MINIMIZAR: soma de produtos.Custo_Producao * x[produto] PARA CADA produto EM produtos
```

### Exemplo 2: Restrição com Agregação
```
soma de x[produto] PARA CADA produto EM produtos <= 1000
```

### Exemplo 3: Expressão Condicional
```
SE estoque.Disponivel > demanda ENTAO estoque.Disponivel - demanda SENAO 0
```

## 🛠️ Processamento da Gramática

O parser Lark utiliza esta gramática para:

1. **Tokenização**: Quebrar a entrada em tokens
2. **Parsing**: Construir uma árvore sintática
3. **Transformação**: Converter a árvore em código Python usando o `TradutorLOS`

## 📝 Notas sobre Extensibilidade

A gramática é altamente extensível:

- Novos operadores podem ser adicionados nas seções relevantes
- Funções matemáticas adicionais podem ser incluídas em `nome_funcao`
- Estruturas mais complexas podem ser adicionadas seguindo o padrão

## 🎯 Capacidades Completas da Linguagem LOS

### ✅ Funcionalidades Implementadas e Testadas

#### **Tipos de Expressões**
- ✅ **Objetivos**: `MINIMIZAR:` e `MAXIMIZAR:` com expressões matemáticas
- ✅ **Restrições**: Comparações com operadores relacionais (`<=`, `>=`, `==`, `!=`, `<`, `>`, `=`)
- ✅ **Condicionais**: `SE ... ENTAO ... SENAO` para lógica condicional
- ✅ **Matemáticas**: Expressões aritméticas com precedência correta

#### **Operações e Funções**
- ✅ **Aritméticas**: `+`, `-`, `*`, `/` com precedência correta
- ✅ **Funções**: `abs()`, `max()`, `min()`, `sum()`, `sqrt()`
- ✅ **Agregações**: `SOMA DE` com loops opcionais
- ✅ **Parênteses**: Para agrupamento e precedência explícita

#### **Estruturas de Dados**
- ✅ **Variáveis simples**: `x`, `custo`, `receita`
- ✅ **Variáveis indexadas**: `x[produto]`, `transporte[origem,destino]`, `alocacao[i,j,k]`
- ✅ **Referências a datasets**: `produtos.Preco`, `clientes.Nome`
- ✅ **Strings e números**: `'texto'`, `"texto"`, `123`, `45.67`

#### **Controle de Fluxo**
- ✅ **Loops**: `PARA CADA variavel EM dataset`
- ✅ **Filtros**: `ONDE condicao` para filtrar iterações
- ✅ **Combinações**: Agregações com loops e filtros

### 🔄 Funcionalidades Parcialmente Implementadas

#### **No Código mas Não na Gramática Atual**
- 🔄 **Declaração de tipos**: `VAR CONTINUA x`, `VAR INTEIRA y`, `VAR BINARIA z`
- 🔄 **Operadores lógicos**: `E`, `OU`, `NAO` (implementados no tradutor)
- 🔄 **JOINs de datasets**: `dataset1 JOIN dataset2 ON condicao`
- 🔄 **Operadores especiais**: `IN`, `NOT IN`, `LIKE`, `BETWEEN`, `EXISTS`
- 🔄 **Loops avançados**: `PARA`, `ENQUANTO`, loops aninhados
- 🔄 **Expressões ternárias**: `condicao ? verdadeiro : falso`

### 📊 Exemplos de Uso Validados

```lark
# Objetivo básico
MINIMIZAR: x + y + z

# Restrição com agregação
soma de x[produto] PARA CADA produto EM produtos <= 100

# Condicional
SE x > 0 ENTAO x SENAO 0

# Expressão complexa
MAXIMIZAR: soma de produtos.Preco * vendas[produto] PARA CADA produto EM produtos ONDE produtos.Ativo == 1
```

### 📁 Documentação de Exemplos

Criada pasta `exemplos_los/` com:
- `00_guia_sintaxe.los` - Guia completo de sintaxe
- `01_objetivos.los` - Exemplos de objetivos de otimização  
- `02_restricoes.los` - Exemplos de restrições
- `03_operacoes_matematicas.los` - Operações e funções matemáticas
- `04_condicionais.los` - Expressões condicionais
- `05_agregacoes_loops.los` - Agregações e loops
- `06_datasets_variaveis.los` - Datasets e variáveis indexadas
- `07_operadores_relacionais.los` - Operadores de comparação
- `08_exemplos_complexos.los` - Casos de uso complexos

## 🔄 Considerações de Manutenção

Ao modificar a gramática:

- Manter a precedência correta de operadores
- Garantir que tokens não entrem em conflito
- Atualizar o `TradutorLOS` correspondente em `los_parser.py`
- Adicionar testes para novas construções
- Validar exemplos na pasta `exemplos_los/`

---

*Última atualização: 30 de junho de 2025*
*Análise completa das capacidades: 30 de junho de 2025*
