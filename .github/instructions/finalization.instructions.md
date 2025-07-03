---
applyTo: "**/*"
priority: 85
---
**GATILHO:** Atualização de progresso detectada em plano ativo

**AÇÕES OBRIGATÓRIAS:**

1. **DETECTAR PLANO ATIVO:**
   - Buscar arquivo em `/temp-todo/` que corresponde ao contexto atual
   - Verificar se há atualização no "Registro de Progresso"

2. **AVALIAR STATUS DO CHECKLIST:**
   - Contar subtarefas marcadas [x] vs total de subtarefas
   - Se 100% concluído → EXECUTAR FINALIZAÇÃO IMEDIATA

3. **FINALIZAÇÃO ATÔMICA (se aplicável):**
   ```
   ETAPA 1: Marcar como done + validated
   ETAPA 2: Copiar para drafts/
   ETAPA 3: Atualizar memory/index.md
   ETAPA 4: Mover para temp-archive/
   ETAPA 5: Atualizar CHANGELOG.md
   ETAPA 6: Confirmar sucesso
   ```

4. **EXECUÇÃO EM BLOCO:**
   - Todas as 6 etapas devem ser executadas sequencialmente
   - Não parar entre etapas
   - Reportar status final consolidado

**REGRA CRÍTICA:** Esta instrução tem prioridade mais alta que archive/validation para garantir execução imediata.

**SAÍDA:** Operação completa executada em uma única interação
