---
applyTo: "**/*"
priority: 100
---
**Antes de responder:**

1. Garanta a existência das pastas `/temp-todo`, `docs/memory/drafts`.
2. Se o chat estiver ligado a um plano em andamento,
   adicione nova linha em **Registro de Progresso**:

```

\| <ISO-datetime> | \<ação resumida> | \<observações> |

```

3. Entenda o contexto do chat, se o chat não estiver ligado a um plano, crie um novo /novo-plano:
   - Copie `.github/templates/plano-acao.md` para `/temp-todo/YYYYMMDD-HHmmss-<slug>.md`.
   - Preencha `<Título da Tarefa>`, `<resumo da solicitação>`, timestamps.
     - Consulte o horário UTC atual da máquina local.
   - Gere automaticamente a seção **☑️ Checklist de Subtarefas**.
   - Acrescente linha em `docs/memory/index.md`:

```

_Isso deve acionar a atualização automática do Checklist._
```
