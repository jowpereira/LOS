#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 Script de Teste para Validação dos Exemplos LOS
Testa cada expressão nos arquivos .los e identifica problemas
"""

import os
import sys
from pathlib import Path

# Adicionar o diretório atual ao path para importar los_parser
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from los_parser import ParserLOS

def testar_arquivo_los(caminho_arquivo):
    """Testa todas as expressões de um arquivo .los"""
    print(f"\n📁 Testando arquivo: {caminho_arquivo.name}")
    print("=" * 60)
    
    parser = ParserLOS()
    sucessos = 0
    falhas = 0
    
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            linhas = f.readlines()
        
        for i, linha in enumerate(linhas, 1):
            linha = linha.strip()
            
            # Pular comentários e linhas vazias
            if not linha or linha.startswith('#') or linha.startswith('```'):
                continue
            
            try:
                resultado = parser.analisar_expressao(linha)
                print(f"✅ Linha {i}: {linha[:50]}{'...' if len(linha) > 50 else ''}")
                sucessos += 1
                
            except Exception as e:
                print(f"❌ Linha {i}: {linha[:50]}{'...' if len(linha) > 50 else ''}")
                print(f"   Erro: {str(e)[:100]}{'...' if len(str(e)) > 100 else ''}")
                falhas += 1
    
    except Exception as e:
        print(f"❌ Erro ao ler arquivo: {e}")
        return 0, 1
    
    print(f"\n📊 Resultado: {sucessos} sucessos, {falhas} falhas")
    return sucessos, falhas

def main():
    """Função principal de teste"""
    print("🚀 VALIDAÇÃO COMPLETA DOS EXEMPLOS LOS")
    print("=" * 60)
    
    # Caminho para a pasta de exemplos
    pasta_exemplos = Path("exemplos_los")
    
    if not pasta_exemplos.exists():
        print("❌ Pasta exemplos_los não encontrada!")
        return
    
    # Encontrar todos os arquivos .los
    arquivos_los = list(pasta_exemplos.glob("*.los"))
    
    if not arquivos_los:
        print("❌ Nenhum arquivo .los encontrado!")
        return
    
    total_sucessos = 0
    total_falhas = 0
    
    # Testar cada arquivo
    for arquivo in sorted(arquivos_los):
        sucessos, falhas = testar_arquivo_los(arquivo)
        total_sucessos += sucessos
        total_falhas += falhas
    
    # Resultado final
    print(f"\n🎯 RESULTADO FINAL:")
    print(f"✅ Total de sucessos: {total_sucessos}")
    print(f"❌ Total de falhas: {total_falhas}")
    print(f"📊 Taxa de sucesso: {(total_sucessos/(total_sucessos+total_falhas)*100):.1f}%")
    
    if total_falhas == 0:
        print("🎉 TODOS OS EXEMPLOS FUNCIONAM PERFEITAMENTE!")
    else:
        print("⚠️  Algumas expressões precisam de correção.")

if __name__ == "__main__":
    main()
