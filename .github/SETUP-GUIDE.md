# Guia de Setup - Sistema de Instruções Universais

## 📋 Pré-requisitos
- GitHub Copilot habilitado no workspace
- VS Code ou IDE compatível
- Nenhuma dependência externa

## 🚀 Instalação em Novo Projeto (< 5 minutos)

### Passo 1: Estrutura Base
```bash
mkdir -p .github/instructions
mkdir -p .github/templates
mkdir -p docs/memory/drafts
mkdir -p temp-todo
mkdir -p temp-archive
```

### Passo 2: Copiar Arquivos de Instrução
Copiar todos os arquivos de `.github/instructions/` para o novo projeto:
- `base.instructions.md` (priority 100)
- `planning.instructions.md` (priority 90)
- `checklist.instructions.md` (priority 80)
- `validation.instructions.md` (priority 78)
- `archive.instructions.md` (priority 75)
- `changelog.instructions.md` (priority 72)
- `commit.instructions.md` (priority 70)
- `backlog.instructions.md` (priority 68)
- `memory.instructions.md` (priority 60)
- `review.instructions.md` (sem priority - modo específico)

### Passo 3: Template de Plano
Copiar `.github/templates/plano-acao.md` para o novo projeto.

### Passo 4: Inicializar Arquivos de Controle
```bash
# Criar docs/memory/index.md
echo "| Data | Tarefa | Status | Arquivo |" > docs/memory/index.md
echo "|------|--------|--------|---------|" >> docs/memory/index.md

# Criar CHANGELOG.md (opcional)
touch CHANGELOG.md

# Criar BACKLOG.md (opcional)  
touch BACKLOG.md
```

### Passo 5: Configurar Copilot
Verificar se `github.copilot.chat.codeGeneration.useInstructionFiles` está habilitado.

## ✅ Verificação da Instalação
1. Abrir chat do Copilot
2. Digitar: "criar um plano para teste"
3. Verificar se novo arquivo é criado em `/temp-todo/`
4. Verificar se `docs/memory/index.md` é atualizado

## 🎯 Convenções e Padrões

### Nomenclatura de Arquivos
- Planos: `YYYYMMDD-HHmmss-<slug-da-tarefa>.md`
- Drafts: `YYYYMMDD-<slug-da-tarefa>.md`

### Estrutura de Prioridades
- 100: Base/Inicialização
- 90-99: Planejamento
- 80-89: Execução
- 70-79: Finalização
- 60-69: Consulta

### Estados Válidos
- `PENDENTE`: Tarefa ativa em desenvolvimento
- `CONCLUÍDO / SEM COMMIT`: Tarefa finalizada, aguardando commit
- `CONCLUÍDO`: Tarefa commitada com hash
- `PAUSADO`: Tarefa interrompida temporariamente
- `ENCERRADO - FALHOU`: Tarefa cancelada

## 🔧 Customização por Projeto

### Adaptar Base Instructions
Editar `base.instructions.md` para incluir estruturas específicas do projeto.

### Adaptar Planning Template  
Editar `.github/templates/plano-acao.md` para incluir seções específicas do domínio.

### Adaptar Changelog Format
Editar `changelog.instructions.md` para seguir padrões específicos do projeto.

## 🚨 Troubleshooting

### Problema: Instruções não são seguidas
- Verificar prioridades não conflitantes
- Confirmar sintaxe YAML válida no front-matter
- Verificar se pastas existem

### Problema: Arquivos não são criados
- Verificar permissões de escrita
- Confirmar estrutura de pastas
- Verificar logs do Copilot

### Problema: Estados inconsistentes
- Executar limpeza manual em `/temp-todo/`
- Verificar `docs/memory/index.md` para entradas órfãs
- Recriar estrutura se necessário

## 📚 Exemplo de Fluxo Completo

1. **Usuário:** "Preciso refatorar o módulo de autenticação"
2. **Sistema:** Cria plano em `/temp-todo/20250701-140000-refatoracao-auth.md`
3. **Sistema:** Atualiza `docs/memory/index.md` com status PENDENTE
4. **Desenvolvimento:** Usuário executa tarefas, sistema atualiza progresso
5. **Conclusão:** Sistema marca `done: true`, executa validação
6. **Arquivamento:** Move para `/temp-archive/`, cria draft, atualiza memória
7. **Documentação:** Atualiza `CHANGELOG.md` automaticamente
8. **Commit:** Sistema gera mensagem de commit, atualiza hash na memória

## 🎉 Benefícios

- ✅ **100% Offline:** Funciona sem internet
- ✅ **Portável:** Copia facilmente entre projetos  
- ✅ **Auditável:** Todo histórico preservado
- ✅ **Determinístico:** Fluxo sempre consistente
- ✅ **Escalável:** Funciona em projetos pequenos e grandes
