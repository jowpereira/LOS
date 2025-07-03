---
applyTo: "**/*"
priority: 80
---
**GATILHO:** Sempre que atualizar **Registro de Progresso**

**AÇÕES OBRIGATÓRIAS:**

1. **ATUALIZAR CHECKLIST:**
   - Abrir seção **☑️ Checklist de Subtarefas**
   - Marcar `[x]` nas subtarefas correspondentes à ação realizada

2. **SE TODAS AS SUBTAREFAS ESTÃO MARCADAS [x]:**
   - Adicionar ao front-matter: `done: true`
   - Criar ou atualizar seção:
     ```md
     ## ✅ Conclusão
     - Todas as subtarefas concluídas em <ISO-datetime>.
     ```

3. **EXECUTAR FLUXO COMPLETO DE FINALIZAÇÃO:**
   - **VALIDAR PLANO:** Verificar estrutura e dependências
   - **SE VALIDAÇÃO OK:** Adicionar `validated: true` + `validation_date`
   - **ARQUIVAR IMEDIATAMENTE:**
     - Copiar para `docs/memory/drafts/YYYYMMDD-<slug>.md`
     - Atualizar `docs/memory/index.md`: PENDENTE → CONCLUÍDO / SEM COMMIT
     - Mover de `/temp-todo/` → `/temp-archive/`
   - **ATUALIZAR CHANGELOG:** Adicionar entrada automática no topo

4. **VERIFICAÇÃO FINAL:**
   - Confirmar que todas as operações foram executadas com sucesso
   - Reportar status completo das operações

**REGRA:** NÃO cole o checklist inteiro no chat; execute e salve apenas nos arquivos.

**SAÍDA:** Plano completamente processado e arquivado em uma única operação