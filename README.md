# 🚀 LOS - Linguagem de Otimização Simples

Uma linguagem de domínio específico (DSL) para expressar problemas de otimização matemática em linguagem quase natural.

## 📋 Visão Geral

A **Linguagem de Otimização Simples (LOS)** permite escrever modelos de otimização de forma intuitiva, próxima da linguagem natural, que são automaticamente traduzidos para código Python compatível com bibliotecas como PuLP e SciPy.

## ✨ Características

- ✅ **Sintaxe intuitiva** próxima da linguagem natural
- ✅ **Objetivos** de minimização e maximização
- ✅ **Restrições** com operadores relacionais completos
- ✅ **Expressões condicionais** (SE/ENTAO/SENAO)
- ✅ **Agregações e loops** (SOMA DE/PARA CADA)
- ✅ **Referências a datasets** (DataFrames)
- ✅ **Funções matemáticas** (abs, max, min, sqrt)
- ✅ **Operadores lógicos** (E, OU, NÃO)

## 🚀 Instalação

```bash
# Clone o repositório
git clone <repo-url>
cd temp

# Instale as dependências
pip install -r requirements.txt
```

## 📖 Uso Rápido

```python
from los_parser import ParserLOS

# Inicializar o parser
parser = ParserLOS()

# Exemplo de objetivo
objetivo = parser.analisar_expressao("MINIMIZAR: soma de custos[produto] * x[produto] PARA CADA produto EM produtos")

# Exemplo de restrição
restricao = parser.analisar_expressao("soma de x[produto] PARA CADA produto EM produtos <= capacidade_maxima")

print(f"Código Python: {objetivo.codigo_python}")
```

## 📚 Exemplos

Veja a pasta `exemplos_los/` para exemplos completos de todas as funcionalidades:

- `00_guia_sintaxe.los` - Guia completo de sintaxe
- `01_objetivos.los` - Objetivos de otimização
- `02_restricoes.los` - Restrições com operadores
- `08_exemplos_complexos.los` - Casos de uso avançados

## 🧪 Testes

```bash
# Executar todos os testes
python -m pytest tests/ -v

# Executar testes específicos
cd tests && python -m pytest teste_exemplos_los.py -v

# Resultado esperado: 16 passed, 0 failed
```

## 📊 Status do Projeto

- ✅ **Funcionalidade**: 95% completa para v1.0
- ✅ **Robustez**: 85% (bem testado)
- ✅ **Cobertura de testes**: 100% dos exemplos validados
- ✅ **Performance**: <10ms para expressões complexas

## 📖 Documentação

- [Documentação da Gramática](docs/documentacao-gramatica-los.md)
- [Documentação do Parser](docs/documentacao-parser-los.md)
- [Relatório Executivo](docs/relatorio-los.md)

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Faça commit das mudanças
4. Abra um Pull Request

## 📝 Licença

[Definir licença apropriada]

## 👤 Autor

**Jonathan Pereira** - Engenheiro de Software Sênior
