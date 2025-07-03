---
applyTo: "**/*"
priority: 90
---
Quando o usuário pedir um **plano** (ou não existir plano ativo):

1. Copie `.github/templates/plano-acao.md`
   → `/temp-todo/YYYYMMDD-HHmmss-<slug>.md`.
2. Preencha `<Título da Tarefa>`, `<resumo da solicitação>`, timestamps.
   - Consulte o horário UTC atual da máquina local.
3. Gere automaticamente a seção **☑️ Checklist de Subtarefas**.
4. Acrescente linha em `docs/memory/index.md`:

```

\| YYYY-MM-DD | \<Título da Tarefa> | PENDENTE | — |

```

5. Siga o fluxo de Planejamento Ultra-Detalhado descrito no template.
