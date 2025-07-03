# 📚 Exemplos LOS com Dados Reais

Esta pasta contém exemplos práticos da Linguagem de Otimização Simples (LOS) baseados nos dados reais de `bases_exemplos/`.

## 📊 Datasets Utilizados

Todos os exemplos são baseados nos seguintes datasets reais:

- **`clientes_exemplo.csv`**: 5 clientes com tipos Premium, Standard e Basic
- **`produtos_exemplo.csv`**: 5 produtos (PROD_A a PROD_E) com custos, margens e tempos
- **`ordens_exemplo.csv`**: 12 ordens de venda com produtos, plantas, quantidades e datas
- **`estoque_exemplo.csv`**: Estoque disponível por produto e planta
- **`custos_exemplo.csv`**: Custos de atraso e não atendimento por tipo de cliente

## 🎯 Exemplos Disponíveis

### 1. **01_minimizar_custos_producao.los**
**Problema**: Minimização de custos de produção
- **Objetivo**: Minimizar custos totais considerando custo por produto
- **Variáveis**: x[produto, planta] = quantidade a produzir
- **Restrições**: Atender demanda, respeitar capacidades, não negatividade
- **Dados reais**: Custos de R$18,75 a R$45,80 por produto

### 2. **02_maximizar_lucro.los** 
**Problema**: Maximização de lucro com limitação de tempo
- **Objetivo**: Maximizar lucro baseado nas margens reais (25% a 40%)
- **Variáveis**: y[produto] = quantidade total a produzir
- **Restrições**: Tempo de produção, demanda máxima, produção mínima
- **Análise**: PROD_D tem maior eficiência (R$4,58/hora)

### 3. **03_alocacao_com_penalidades.los**
**Problema**: Minimização com penalidades diferenciadas por cliente
- **Objetivo**: Minimizar custos + penalidades baseadas no tipo de cliente
- **Variáveis**: z[produto, cliente], atraso[cliente]
- **Restrições**: Prioridade para Premium (95% atendimento), penalidades reais
- **Dados reais**: Penalidades de R$5 a R$15 por dia de atraso

### 4. **04_planejamento_multi_periodo.los**
**Problema**: Planejamento temporal baseado nas datas das ordens
- **Objetivo**: Minimizar custos + custos de estoque ao longo do tempo
- **Variáveis**: w[produto, planta, periodo], estoque_final[produto, planta, periodo]
- **Restrições**: Balanço de estoque, atender prazos, capacidade por período
- **Períodos**: 4 períodos baseados nas datas reais (Jan 15 - Fev 10)

### 5. **05_otimizacao_condicional.los**
**Problema**: Decisões condicionais complexas
- **Objetivo**: Minimizar custos com decisões SE/ENTÃO
- **Variáveis**: v[produto, planta], ativa_planta[planta], hora_extra[planta]
- **Condicionais**: Ativação de planta, hora extra, produtos premium
- **Lógica**: Decisões baseadas em volume, tipo de cliente, capacidade

### 6. **06_transporte_distribuicao.los**
**Problema**: Otimização de transporte e distribuição
- **Objetivo**: Minimizar custos de transporte + distribuição
- **Variáveis**: t[produto, planta, cliente] = quantidade transportada
- **Restrições**: Capacidade de rota, preferência Premium, economia de escala
- **Custos**: R$2,10 a R$6,80 por unidade conforme distância

## 🔍 Como Usar os Exemplos

### Pré-requisitos
```bash
# Certifique-se de que os datasets estão disponíveis
ls ../bases_exemplos/
# Deve mostrar: clientes_exemplo.csv, produtos_exemplo.csv, ordens_exemplo.csv, etc.
```

### Execução com LOS
```python
from los import LOSParser, ExpressionService

# Carregar arquivo .los
parser = LOSParser()
with open('01_minimizar_custos_producao.los', 'r') as f:
    modelo_texto = f.read()

# Processar com datasets
import pandas as pd
datasets = {
    'produtos': pd.read_csv('../bases_exemplos/produtos_exemplo.csv'),
    'ordens': pd.read_csv('../bases_exemplos/ordens_exemplo.csv'),
    'estoque': pd.read_csv('../bases_exemplos/estoque_exemplo.csv'),
    'clientes': pd.read_csv('../bases_exemplos/clientes_exemplo.csv'),
    'custos': pd.read_csv('../bases_exemplos/custos_exemplo.csv')
}

# Analisar e gerar código
resultado = parser.parse_with_datasets(modelo_texto, datasets)
print(resultado.python_code)
```

## 📈 Características dos Problemas

### Complexidade
- **Simples**: Exemplos 1 e 2 (linear, sem condicionais)
- **Média**: Exemplos 3 e 6 (múltiplas restrições, penalidades)
- **Alta**: Exemplos 4 e 5 (multi-período, condicionais complexas)

### Tipos de Variáveis
- **Contínuas**: Quantidades de produção, transporte
- **Binárias**: Ativação de plantas, decisões de produto premium
- **Inteiras**: Períodos de tempo, dias de atraso

### Domínios de Aplicação
- **Manufatura**: Planejamento de produção, alocação de recursos
- **Logística**: Transporte, distribuição, gestão de estoque
- **Financeiro**: Minimização de custos, maximização de lucro
- **Operacional**: Decisões condicionais, múltiplos objetivos

## 🎯 Resultados Esperados

### Solução Ótima Estimada para Exemplo 1:
- **Custo total**: ~R$45.000-50.000
- **Alocação principal**: PLANTA_1 para produtos de menor custo
- **Estratégia**: Balancear custos vs capacidades

### Solução Ótima Estimada para Exemplo 2:
- **Lucro total**: ~R$12.000-15.000  
- **Foco em**: PROD_D (maior eficiência R$4,58/hora)
- **Limitação**: Tempo total de produção (120 horas)

### Insights Gerais:
- Clientes Premium justificam custos maiores
- PROD_D é mais lucrativo, mas consome mais tempo
- PLANTA_2 tem menor capacidade média
- Penalidades incentivam atendimento no prazo

## 🛠️ Extensões Possíveis

1. **Incerteza**: Adicionar demanda estocástica
2. **Multi-objetivo**: Balancear custo vs qualidade vs tempo  
3. **Sustentabilidade**: Incluir pegada de carbono
4. **Robustez**: Considerar cenários pessimistas
5. **Integração**: Conectar com sistemas ERP/MES

---

*Criado automaticamente baseado na análise dos dados reais de bases_exemplos/*
*Data: 2025-07-03*
