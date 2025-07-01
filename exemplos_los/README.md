# 📚 Exemplos da Linguagem LOS

Esta pasta contém exemplos abrangentes demonstrando todas as capacidades da Linguagem de Otimização Simples (LOS).

## 📁 Estrutura dos Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `00_guia_sintaxe.los` | 📋 Guia completo de sintaxe e referência rápida |
| `01_objetivos.los` | 🎯 Objetivos de otimização (MINIMIZAR/MAXIMIZAR) |
| `02_restricoes.los` | 🚧 Restrições com operadores relacionais |
| `03_operacoes_matematicas.los` | 🔢 Operações e funções matemáticas |
| `04_condicionais.los` | 🔄 Expressões condicionais (SE/ENTAO/SENAO) |
| `05_agregacoes_loops.los` | 🔄 Agregações e loops (SOMA DE/PARA CADA) |
| `06_datasets_variaveis.los` | 📊 Datasets e variáveis indexadas |
| `07_operadores_relacionais.los` | 🔍 Operadores de comparação |
| `08_exemplos_complexos.los` | 🧩 Casos de uso complexos combinando funcionalidades |

## 🚀 Como Usar

1. **Comece pelo guia**: Leia `00_guia_sintaxe.los` para entender a sintaxe básica
2. **Explore por categoria**: Navegue pelos arquivos para ver exemplos específicos
3. **Teste no parser**: Use o `ParserLOS` para validar e traduzir as expressões
4. **Combine funcionalidades**: Use os exemplos complexos como inspiração

## 🧪 Testando os Exemplos

```python
from los_parser import ParserLOS

parser = ParserLOS()

# Teste uma expressão simples
resultado = parser.analisar_expressao("MINIMIZAR: x + y + z")
print(f"Tipo: {resultado.tipo}")
print(f"Código: {resultado.codigo_python}")

# Teste uma restrição
restricao = parser.analisar_expressao("x + y <= 100")
print(f"Restrição: {restricao.codigo_python}")
```

## ✅ Capacidades Demonstradas

### **Expressões Básicas**
- ✅ Objetivos de minimização e maximização
- ✅ Restrições com todos os operadores relacionais
- ✅ Expressões condicionais simples e complexas
- ✅ Operações matemáticas com precedência correta

### **Estruturas Avançadas**
- ✅ Variáveis indexadas uni e multidimensionais
- ✅ Referências a datasets e colunas
- ✅ Agregações com loops e filtros
- ✅ Combinações complexas de funcionalidades

### **Casos de Uso Reais**
- ✅ Problemas de transporte e alocação
- ✅ Otimização de produção e estoque
- ✅ Portfólio de investimentos
- ✅ Cronogramas e roteamento

## 📖 Sintaxe Rápida

```
# Objetivo
MINIMIZAR: expressao
MAXIMIZAR: expressao

# Restrição  
expressao <= expressao
expressao >= expressao
expressao == expressao

# Condicional
SE condicao ENTAO expr1 SENAO expr2

# Agregação
SOMA DE expressao PARA CADA var EM dataset ONDE condicao

# Variáveis
x                    # Variável simples
x[produto]           # Variável indexada
dataset.coluna       # Referência a dataset
```

## 🔗 Documentação Relacionada

- [Documentação da Gramática](../docs/documentacao-gramatica-los.md)
- [Documentação do Parser](../docs/documentacao-parser-los.md)
- [Relatório LOS](../docs/relatorio-los.md)

---
*Criado em: 30 de junho de 2025*
*Validado com Parser LOS v1.0*
