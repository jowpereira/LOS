---
applyTo: "**/*"
priority: 75
---
Quando detectar `done: true` **e** ainda não existir hash de commit:

1. Copie o plano de `/temp-todo/` → `docs/memory/drafts/`
   (nome `YYYYMMDD-<slug>.md`).
2. Em `docs/memory/index.md`, troque **PENDENTE** → **CONCLUÍDO / SEM COMMIT**
   e adicione o caminho do draft.
3. Opcional: remova plano de `/temp-todo/` ou mova para `/temp-archive/`.
