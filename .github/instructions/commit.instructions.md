---
applyTo: ".git/**"
mode: commitMessageGeneration
---
• Use Conventional Commits em PT-BR, imperativo, máx. 72 chars.  
• Inclua `close #<id>` ou referência equivalente.  
• NÃO comite sem consentimento.

**Pré-commit:**

1. Se `.git/` não existir, execute `git init`.
2. Localize plano ativo em `/temp-todo/`; exija `done: true`.
3. Copie para `docs/memory/snapshots/YYYYMMDD-<slug>.md`.
4. Gere hash atual com `git rev-parse --short HEAD`
   (após `git add`, antes do commit):
   * Atualize `docs/memory/index.md` linha correspondente:
     `CONCLUÍDO / SEM COMMIT` → `CONCLUÍDO` e preencha hash.
5. Adicione snapshot e index ao stage (`git add`).

**Pós-commit (opcional):**  
remova o plano de `/temp-todo/` ou mova para `/temp-archive/`.
