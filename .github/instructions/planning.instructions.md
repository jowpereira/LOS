---
applyTo: "**/*"
priority: 90
---
Quando o usuário pedir um **plano**, ou ao detectar que não há
arquivo de plano para a tarefa corrente:

1. Copie `.github/templates/plano-acao.md`
   para `/temp-todo/` com nome `YYYYMMDD-HHmmss-<slug>.md`;
2. Substitua `<Título da Tarefa>`, `<resumo da solicitação>` e timestamps
   pelo contexto real.
3. Gere a seção **☑️ Checklist de Subtarefas** (ver template).
4. Adicione entrada provisória em `docs/memory/index.md`:

```

* YYYY-MM-DD | \<Título da Tarefa> | PENDENTE

```

5. Siga o fluxo de Planejamento Ultra-Detalhado descrito no template.
