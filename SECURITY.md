# Segurança no Projeto LOS

Este documento descreve a política de segurança e as medidas de proteção implementadas no compilador LOS.

## Modelo de Ameaça

O LOS funciona como um **transpilador**: ele converte código `.los` (que é seguro por design) em código Python (que é poderoso e perigoso). 

O principal vetor de ataque é a **Injeção de Código (RCE)** através de:
1.  Strings maliciosas que tentam escapar das aspas no código gerado.
2.  Chamadas de função não autorizadas (ex: `__import__('os')`) inseridas como expressões.

## Medidas de Mitigação Implementadas

### 1. Sandbox de Execução (`los_model.py`)
Desde a versão 3.3.1, a execução do código gerado (via `exec()`) ocorre em um ambiente restrito ("sandbox").
*   **Builtins Desativados**: O acesso a `open`, `__import__`, `eval`, `exec` e outros builtins perigosos é bloqueado.
*   **Whitelist Estrita**: Apenas bibliotecas matemáticas e de otimização são permitidas (`pulp`, `pandas`, `numpy`, `math`).

### 2. Escaping de Strings (`pulp_translator.py`)
Todas as strings literais do modelo LOS são tratadas com `repr()` durante a tradução, garantindo que caracteres de escape (`'`, `"`, `\`) sejam neutralizados corretamente.

## Limitações

*   **Não use com input não confiável**: Embora tenhamos endurecido a segurança, **nunca execute modelos LOS recebidos de fontes desconhecidas ou não confiáveis** sem auditoria prévia. Compiladores são alvos complexos e novas técnicas de bypass de sandbox podem surgir.
*   **DoS (Denial of Service)**: O modelo ainda pode consumir recursos excessivos (CPU/RAM) se contiver loops gigantes ou matrizes enormes. Defina timeouts no solver (`time_limit`).

## Reportando Vulnerabilidades

Se você encontrar uma falha de segurança (ex: bypass do sandbox), por favor **NÃO** abra uma Issue pública.
Envie um email diretamente para o mantenedor (contact@los-lang.org) ou reporte confidencialmente.
