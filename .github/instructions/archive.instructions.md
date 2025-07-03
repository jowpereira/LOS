---
applyTo: "**/*"
priority: 65
mode: disabled
---
**NOTA:** Esta instrução foi DESABILITADA. A funcionalidade foi movida para finalization.instructions.md (priority 85) para garantir execução síncrona.

**FUNÇÃO ORIGINAL:** Arquivamento após validação
**NOVA IMPLEMENTAÇÃO:** finalization.instructions.md executa todo o fluxo atomicamente

Esta instrução permanece como backup/referência, mas não será executada devido ao `mode: disabled`.
