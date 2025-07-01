---
applyTo: "**/*"
priority: 80
---
Sempre que atualizar **Registro de Progresso**:

1. Abra a seção **☑️ Checklist de Subtarefas**; marque `[x]`
   nas subtarefas correspondentes.
2. Se **todas** estiverem `[x]`, acrescente ao front-matter:

   ```yaml
   done: true
   ```

e crie ou atualize:

```md
## ✅ Conclusão
- Todas as subtarefas concluídas em <ISO-datetime>.
```

3. Não cole o checklist inteiro no chat; salve apenas no arquivo.