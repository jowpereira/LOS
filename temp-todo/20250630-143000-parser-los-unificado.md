# Plano de Ação: Unificação do Parser LOS
**Timestamp:** 2025-06-30 14:30:00  
**Contexto recebido:** "Reestruturar e consolidar o parser da Linguagem de Otimização Simples (LOS) para um único parser moderno baseado em Lark, garantir que todos os testes utilizem esse novo parser, limpar o workspace e gerar um relatório executivo."

## 🗺️ Visão Geral
- **Objetivo de negócio:** Unificar o parser LOS para melhorar a manutenibilidade, extensibilidade e confiabilidade do sistema
- **Restrições:** Manter compatibilidade com testes existentes e garantir desempenho
- **Critérios de sucesso:** Todos os testes de integração passam, código unificado, gramática completa

## 🧩 Quebra Granular de Subtarefas
  - 1. Consolidar o parser Lark
    - 1.1 Consolidar código em los_parser.py
    - 1.2 Extrair gramática para los_grammar.lark
    - 1.3 Remover parsers antigos/duplicados
  - 2. Atualizar referências dos testes
    - 2.1 Atualizar imports em todos os arquivos de teste
    - 2.2 Corrigir fixtures de teste
    - 2.3 Adaptar chamadas ao parser
  - 3. Corrigir funcionalidades críticas
    - 3.1 Corrigir parsing de expressões matemáticas
    - 3.2 Corrigir parsing de agregações ("soma de...")
    - 3.3 Garantir compatibilidade com toda a sintaxe LOS
  - 4. Limpeza e documentação
    - 4.1 Remover arquivos temporários e duplicados
    - 4.2 Documentar gramática e métodos
    - 4.3 Gerar relatório executivo sobre LOS

## ☑️ Checklist de Subtarefas

[x] 1. Consolidar o parser Lark
  [x] 1.1 Consolidar código em los_parser.py
  [x] 1.2 Extrair gramática para los_grammar.lark
  [x] 1.3 Remover parsers antigos/duplicados
[x] 2. Atualizar referências dos testes
  [x] 2.1 Atualizar imports em todos os arquivos de teste
  [x] 2.2 Corrigir fixtures de teste
  [x] 2.3 Adaptar chamadas ao parser
[x] 3. Corrigir funcionalidades críticas
  [x] 3.1 Corrigir parsing de expressões matemáticas
  [x] 3.2 Corrigir parsing de agregações ("soma de...")
  [x] 3.3 Garantir compatibilidade com toda a sintaxe LOS
[ ] 4. Limpeza e documentação
  [ ] 4.1 Remover arquivos temporários e duplicados
  [ ] 4.2 Documentar gramática e métodos
  [ ] 4.3 Gerar relatório executivo sobre LOS

## ✅ Conclusão
* Todas as tarefas de consolidação e compatibilidade concluídas em 2025-06-30 14:30:00.
* Restam apenas limpeza final e documentação.

## Métricas de aceite
- Todos os testes de integração devem passar
- O parser deve reconhecer corretamente expressões com "soma de"
- A estrutura do projeto deve estar limpa e organizada

## 🔬 Testes Planejados
- Testar parsing de expressões matemáticas com diferentes níveis de complexidade
- Testar parsing de "soma de..." em diversos contextos
- Testar integração com PuLP para problemas de otimização reais
- Benchmarks de performance comparando com parser antigo

## 🛡️ Riscos & Mitigações
- Incompatibilidade com testes legados → Adaptar testes ou criar camada de compatibilidade
- Performance inferior → Otimizar gramática e algoritmos de parsing
- Falhas em casos específicos → Implementar testes abrangentes

## 📊 Métricas de Sucesso
- 100% dos testes de integração passando
- Tempo de parsing ≤ 2x tempo do parser anterior
- Cobertura de gramática para todos os casos da especificação LOS

## 📌 Registro de Progresso
| Data-hora | Ação | Observações |
|-----------|------|-------------|
| 2025-06-30 09:15:00 | Análise inicial do parser existente | Identificadas duplicações e inconsistências |
| 2025-06-30 10:30:00 | Consolidação inicial do parser em los_parser.py | Extração da gramática para arquivo separado |
| 2025-06-30 11:45:00 | Atualização dos imports nos testes | Modificados para apontar para novo parser |
| 2025-06-30 13:00:00 | Correção do parsing de expressões matemáticas | Ajustes na gramática para precedência correta |
| 2025-06-30 13:45:00 | Debug do problema com "soma de" | Identificada falha no reconhecimento dos tokens |
| 2025-06-30 14:15:00 | Correção do parsing de "soma de" | Modificação da gramática e preprocessamento |
| 2025-06-30 14:30:00 | Testes de integração passando | Todos os testes de integração funcionando |
| 2025-06-30 14:45:00 | Criação do plano de ação retrospectivo | Documentação do que foi feito |

## 💾 Commit / CHANGELOG / TODO
- feat: parser LOS unificado baseado em Lark
- fix: correção do parsing de "soma de" nas agregações
- refactor: gramática extraída para arquivo externo
- test: adaptação dos testes para novo parser
- docs: documentação da gramática e API do parser
