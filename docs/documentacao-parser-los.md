# 📝 Documentação do Parser LOS

## 📋 Visão Geral

O parser LOS (Linguagem de Otimização Simples) é implementado no arquivo `los_parser.py` e utiliza o framework Lark para analisar e traduzir expressões de otimização matemática escritas em uma linguagem próxima do natural para código Python executável, compatível com bibliotecas como PuLP.

## 🧩 Componentes Principais

### 1. ExpressaoLOS (Dataclass)
Representa uma expressão analisada da linguagem LOS.

**Atributos:**
- `tipo`: String que indica o tipo de expressão (objetivo, restrição, condicional, matemática)
- `operacao`: String que descreve a operação específica (minimizar, maximizar, menor_igual, etc.)
- `expressao_original`: Texto original da expressão
- `arvore_sintaxe`: Árvore sintática gerada pelo Lark
- `codigo_python`: Código Python gerado
- `variaveis_detectadas`: Conjunto de variáveis utilizadas
- `datasets_referenciados`: Conjunto de datasets referenciados
- `complexidade`: Número que indica a complexidade da expressão

### 2. TradutorLOS (Transformer)
Classe que herda de `lark.Transformer` para converter a árvore sintática do Lark em código Python.

**Métodos principais:**
- `objetivo_minimizar/maximizar`: Traduz objetivos de otimização
- `restricao`: Traduz restrições matemáticas
- `operacao_aditiva`: Traduz operações de adição e subtração
- `operacao_multiplicativa`: Traduz operações de multiplicação e divisão
- `agregacao`: Traduz funções de agregação como "soma de"
- `loop`: Traduz loops "PARA CADA"
- `variavel_indexada`: Traduz variáveis com índices
- `referencia_dataset`: Traduz referências a datasets

### 3. ParserLOS (Classe Principal)
Classe principal que gerencia todo o processo de parsing e tradução.

**Métodos principais:**
- `analisar_expressao`: Analisa uma expressão LOS completa
- `analisar_restricoes`: Analisa múltiplas restrições de um texto
- `gerar_variaveis_decisao`: Gera estrutura de variáveis para uso com PuLP
- `traduzir_para_pulp`: Traduz expressões para código compatível com PuLP
- `_preprocessar_texto`: Realiza o preprocessamento do texto de entrada

## 🔄 Fluxo de Processamento

1. **Pré-processamento**
   ```python
   texto_limpo = self._preprocessar_texto(texto)
   ```
   Normaliza o texto e converte palavras-chave para maiúsculas.

2. **Parsing com Lark**
   ```python
   arvore = self.parser.parse(texto_limpo)
   ```
   Utiliza a gramática definida em `los_grammar.lark` para gerar a árvore sintática.

3. **Transformação**
   ```python
   resultado = self.tradutor.transform(arvore)
   ```
   Converte a árvore em uma representação Python usando o `TradutorLOS`.

4. **Extração de informações**
   ```python
   tipo = self._detectar_tipo_expressao(resultado)
   operacao = self._extrair_operacao(resultado)
   codigo_python = self._extrair_codigo(resultado)
   ```
   Determina o tipo, operação e código Python resultante.

5. **Criação da expressão**
   ```python
   return ExpressaoLOS(
       tipo=tipo,
       operacao=operacao,
       expressao_original=texto,
       arvore_sintaxe=arvore,
       codigo_python=codigo_python,
       variaveis_detectadas=self.tradutor.variaveis_encontradas.copy(),
       datasets_referenciados=self.tradutor.datasets_referenciados.copy(),
       complexidade=self.tradutor.nivel_complexidade
   )
   ```
   Retorna um objeto `ExpressaoLOS` completo.

## 🔍 Funcionalidades Específicas

### Preprocessamento de Texto
```python
def _preprocessar_texto(self, texto: str) -> str:
    # Normaliza espaços e converte palavras-chave
    texto = ' '.join(texto.split())
    
    # Tratamento especial para "soma de"
    texto = re.sub(r'\b(soma)\s+(?:de)\b', 'SOMA DE', texto, flags=re.IGNORECASE)
    
    # Converte outras palavras-chave
    palavras_chave = [
        'minimizar', 'maximizar', 'se', 'entao', 'senao',
        'para', 'cada', 'em', 'onde', 'e', 'ou', 'nao',
        'de', 'soma'
    ]
    for palavra in palavras_chave:
        texto = re.sub(r'\b' + palavra + r'\b', palavra.upper(), texto, flags=re.IGNORECASE)
    
    return texto
```

### Geração de Variáveis de Decisão
```python
def gerar_variaveis_decisao(self) -> Dict[str, Dict[str, Any]]:
    variaveis = {}
    
    for nome_var in self.tradutor.variaveis_encontradas:
        if ' ' in nome_var or '(' in nome_var or ')' in nome_var or '+' in nome_var:
            continue
        
        if '[' in nome_var and ']' in nome_var:
            nome_base = nome_var.split('[')[0].strip()
            indices_str = nome_var.split('[')[1].split(']')[0].strip()
            indices = [idx.strip() for idx in indices_str.split(',')]
            
            variaveis[nome_base] = {
                'tipo': 'continua',
                'indices': indices,
                'dimensoes': len(indices)
            }
        else:
            variaveis[nome_var] = {
                'tipo': 'continua',
                'dimensoes': 0
            }
    
    return variaveis
```

### Tradução para PuLP
```python
def traduzir_para_pulp(self, expressao: ExpressaoLOS) -> str:
    if not expressao:
        return ""
    
    codigo_python = expressao.codigo_python
    
    if expressao.tipo == "objetivo":
        if expressao.operacao == "minimizar":
            return f"prob += {codigo_python}"
        elif expressao.operacao == "maximizar":
            return f"prob += {codigo_python}"
    
    elif expressao.tipo == "restricao":
        return f"prob += {codigo_python}"
    
    return codigo_python
```

## 📊 Exemplos de Uso

### Análise de uma Expressão
```python
parser = ParserLOS()
expressao = parser.analisar_expressao("MINIMIZAR: soma de produtos.Custo * x[produto] PARA CADA produto EM produtos")

print(f"Tipo: {expressao.tipo}")
print(f"Operação: {expressao.operacao}")
print(f"Código Python: {expressao.codigo_python}")
print(f"Variáveis detectadas: {expressao.variaveis_detectadas}")
```

### Análise de Múltiplas Restrições
```python
restricoes_texto = """
# Capacidade máxima
soma de x[produto] PARA CADA produto EM produtos <= 1000
# Demanda mínima
x[produto] >= 10 PARA CADA produto EM produtos
"""

restricoes = parser.analisar_restricoes(restricoes_texto)
for restricao in restricoes:
    print(f"Restrição: {restricao.expressao_original}")
    print(f"Código: {restricao.codigo_python}")
    print("---")
```

### Geração de Variáveis para PuLP
```python
parser = ParserLOS()
parser.analisar_expressao("MINIMIZAR: x[produto] + y[cliente,planta] + z")
variaveis = parser.gerar_variaveis_decisao()

for nome, detalhes in variaveis.items():
    if detalhes['dimensoes'] == 0:
        print(f"Variável escalar: {nome}")
    else:
        print(f"Variável indexada: {nome} com {detalhes['dimensoes']} dimensões")
        print(f"Índices: {detalhes['indices']}")
```

## 🔧 Considerações de Manutenção e Extensão

### Adição de Novos Tokens ou Regras
1. Adicionar definições ao arquivo `los_grammar.lark`
2. Implementar métodos correspondentes no `TradutorLOS`
3. Atualizar métodos auxiliares como `_preprocessar_texto` se necessário

### Melhoria da Detecção de Variáveis
O método `gerar_variaveis_decisao` pode ser estendido para:
- Detectar tipos diferentes de variáveis (contínuas, inteiras, binárias)
- Extrair limites de variáveis
- Identificar variáveis dependentes

### Integração com Outros Solvers
O método `traduzir_para_pulp` pode ser generalizado para outros solvers:
- Criar métodos específicos para cada solver
- Implementar adaptadores para sintaxes específicas
- Manter compatibilidade com APIs existentes

---

*Última atualização: 30 de junho de 2025*
