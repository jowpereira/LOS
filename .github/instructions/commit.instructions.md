---
applyTo: ".git/**"
mode: commitMessageGeneration
---
• Use Conventional Commits em PT-BR (imperativo, máx. 72 chars).  
• Inclua referência à tarefa (ex.: `close #123`).  
• Não comite sem OK do usuário.

• **Antes** de gerar a mensagem de commit:

  1. Se não existir `.git/`, execute `git init`.  
  2. Identifique o plano ativo em `/temp-todo/`.  
  3. Copie-o para `docs/memory/snapshots/` com nome  
     `YYYYMMDD-<slug>.md`.  
  4. Edite `docs/memory/index.md`, trocando o status **PENDENTE** por  
     **CONCLUÍDO** e adicionando o caminho do snapshot.  
  5. Adicione ambos os arquivos (`git add`) além dos arquivos de código  
     alterados.
