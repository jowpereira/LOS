# -*- coding: utf-8 -*-
"""
Script para executar testes do Parser LOS
Executa bateria completa de testes e gera relatórios
"""

import sys
import time
import traceback
from pathlib import Path

# Adicionar path do projeto
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Imports de teste
from los_parser import ParserLOS, TradutorLOS
from tests.fixtures.casos_teste import CasosTeste
from tests.utils.validadores import AnalisadorCodigoGerado, criar_relatorio_validacao

# Carregar dados de exemplo
import pandas as pd

def carregar_dados_exemplo():
    """Carrega dados de exemplo"""
    base_dir = Path(__file__).parent.parent / "bases_exemplos"
    
    dados = {}
    dados['clientes'] = pd.read_csv(base_dir / "clientes_exemplo.csv")
    dados['produtos'] = pd.read_csv(base_dir / "produtos_exemplo.csv")
    dados['ordens'] = pd.read_csv(base_dir / "ordens_exemplo.csv")
    dados['estoque'] = pd.read_csv(base_dir / "estoque_exemplo.csv")
    dados['custos'] = pd.read_csv(base_dir / "custos_exemplo.csv")
    
    return dados


class ExecutorTestes:
    """Executor principal dos testes"""
    
    def __init__(self):
        self.dados = carregar_dados_exemplo()
        self.parser = ParserLOS()
        self.parser.carregar_dados_csv(self.dados)
        self.tradutor = TradutorLOS()
        
        self.resultados = {
            'lexer': {'passou': 0, 'falhou': 0, 'erros': []},
            'tradutor': {'passou': 0, 'falhou': 0, 'erros': []},
            'parser': {'passou': 0, 'falhou': 0, 'erros': []},
            'integracao': {'passou': 0, 'falhou': 0, 'erros': []},
            'limitacoes': []
        }
    
    def executar_testes_lexer(self):
        """Executa testes do LexerLOS"""
        print("\n" + "="*50)
        print("TESTANDO LEXER LOS")
        print("="*50)
        
        casos_teste = [
            ("MINIMIZAR x + y", ["MINIMIZAR", "IDENTIFICADOR", "ADICAO", "IDENTIFICADOR"]),
            ("produtos.Custo_Producao", ["IDENTIFICADOR", "PONTO", "IDENTIFICADOR"]),
            ("x <= 100", ["IDENTIFICADOR", "OPERADOR_REL", "NUMERO"]),
            ("soma de (x[i])", ["SOMA_DE", "ABRE_PAREN", "IDENTIFICADOR", "ABRE_COLCH", "IDENTIFICADOR", "FECHA_COLCH", "FECHA_PAREN"]),
            ("PARA CADA produto EM produtos", ["PARA_CADA", "IDENTIFICADOR", "EM", "IDENTIFICADOR"])
        ]
        
        for entrada, tipos_esperados in casos_teste:
            try:
                tokens = self.lexer.tokenize(entrada)
                tipos_obtidos = [t.tipo for t in tokens]
                
                # Verificar se tipos essenciais estão presentes
                tipos_essenciais_presentes = all(tipo in tipos_obtidos for tipo in tipos_esperados[:3])
                
                if tipos_essenciais_presentes:
                    self.resultados['lexer']['passou'] += 1
                    print(f"✅ LEXER: {entrada} -> {len(tokens)} tokens")
                else:
                    self.resultados['lexer']['falhou'] += 1
                    print(f"⚠️ LEXER: {entrada} -> tipos incompletos")
                    
            except Exception as e:
                self.resultados['lexer']['falhou'] += 1
                self.resultados['lexer']['erros'].append(f"{entrada}: {e}")
                print(f"❌ LEXER: {entrada} -> ERRO: {e}")
    
    def executar_testes_tradutor(self):
        """Executa testes do TradutorCompleto"""
        print("\n" + "="*50)
        print("TESTANDO TRADUTOR COMPLETO")
        print("="*50)
        
        casos_teste = [
            ("x + y", "x + y"),
            ("produtos.Custo_Producao", 'produtos["Custo_Producao"]'),
            ("suma de x[i]", "sum([x[i]])"),
            ("x[produto] PARA CADA produto EM produtos", "for produto in produtos"),
            ("SE x > 0 ENTAO x SENAO 0", "if x > 0 else 0")
        ]
        
        for entrada, padrao_esperado in casos_teste:
            try:
                resultado = self.tradutor.traduzir_expressao_completa(entrada)
                
                # Verificar se resultado contém elementos esperados
                if any(elemento in resultado for elemento in padrao_esperado.split()):
                    self.resultados['tradutor']['passou'] += 1
                    print(f"✅ TRADUTOR: {entrada[:30]}... -> {resultado[:40]}...")
                else:
                    self.resultados['tradutor']['falhou'] += 1
                    print(f"⚠️ TRADUTOR: {entrada[:30]}... -> resultado não contém padrão esperado")
                    
            except Exception as e:
                self.resultados['tradutor']['falhou'] += 1
                self.resultados['tradutor']['erros'].append(f"{entrada}: {e}")
                print(f"❌ TRADUTOR: {entrada[:30]}... -> ERRO: {e}")
    
    def executar_testes_parser(self):
        """Executa testes do ParserLOS"""
        print("\n" + "="*50)
        print("TESTANDO PARSER LINGUAGEM SIMPLES")
        print("="*50)
        
        casos_teste = [
            ("MINIMIZAR: x + y", "objetivo", "minimizar"),
            ("MAXIMIZAR: soma de produtos.Custo * x[produto] PARA CADA produto EM produtos", "objetivo", "maximizar"),
            ("x + y <= 100", "restricao", "menor_igual"),
            ("soma de x[i] PARA CADA i EM lista >= 50", "restricao", "maior_igual")
        ]
        
        for entrada, tipo_esperado, operacao_esperada in casos_teste:
            try:
                self.parser.limpar_variaveis()
                expressao = self.parser.analisar_texto(entrada)
                codigo = self.parser.traduzir_para_pulp(expressao)
                
                if expressao.tipo == tipo_esperado and expressao.operacao == operacao_esperada:
                    self.resultados['parser']['passou'] += 1
                    print(f"✅ PARSER: {tipo_esperado}/{operacao_esperada} -> {codigo[:40]}...")
                else:
                    self.resultados['parser']['falhou'] += 1
                    print(f"⚠️ PARSER: esperado {tipo_esperado}/{operacao_esperada}, obtido {expressao.tipo}/{expressao.operacao}")
                    
            except Exception as e:
                self.resultados['parser']['falhou'] += 1
                self.resultados['parser']['erros'].append(f"{entrada}: {e}")
                print(f"❌ PARSER: {entrada[:30]}... -> ERRO: {e}")
    
    def executar_testes_integracao(self):
        """Executa testes de integração com cenários reais"""
        print("\n" + "="*50)
        print("TESTANDO INTEGRAÇÃO - CENÁRIOS REAIS")
        print("="*50)
        
        cenarios = [
            ("Otimização Produção", """
            MINIMIZAR: soma de produtos.Custo_Producao * x[produto] 
            PARA CADA produto EM produtos
            """),
            
            ("Restrição Estoque", """
            soma de ordens.Quantidade * atendimento[ordem]
            PARA CADA ordem EM ordens 
            ONDE ordens.Produto = 'PROD_A'
            <= 1000
            """),
            
            ("Objetivo Multiobjetivo", """
            MAXIMIZAR: soma de produtos.Margem_Lucro * vendas[produto] - 
            0.1 * produtos.Tempo_Producao * vendas[produto]
            PARA CADA produto EM produtos
            """),
            
            ("Priorização Clientes", """
            MINIMIZAR: soma de custos.Valor_Custo * penalidade[cliente]
            PARA CADA cliente EM clientes
            PARA CADA custo EM custos
            ONDE clientes.Tipo_Cliente = custos.Tipo_Cliente
            """)
        ]
        
        for nome, cenario in cenarios:
            try:
                expressao = self.parser.analisar_texto(cenario)
                codigo = self.parser.traduzir_para_pulp(expressao)
                
                # Análise da qualidade do código gerado
                analisador = AnalisadorCodigoGerado(codigo)
                validacao = analisador.validar_completo()
                
                if (validacao['valido_python'] or 
                    validacao['padroes_pulp']['funcao_sum'] or 
                    validacao['padroes_pulp']['compreensao_lista']):
                    
                    self.resultados['integracao']['passou'] += 1
                    print(f"✅ INTEGRAÇÃO {nome}: código válido gerado")
                    print(f"   Complexidade: {validacao['complexidade_estimada']}")
                    print(f"   Datasets: {len(validacao['datasets_referenciados'])}")
                    
                else:
                    self.resultados['integracao']['falhou'] += 1
                    print(f"⚠️ INTEGRAÇÃO {nome}: código com problemas")
                    print(f"   Resultado: {codigo[:50]}...")
                    
            except Exception as e:
                self.resultados['integracao']['falhou'] += 1
                self.resultados['integracao']['erros'].append(f"{nome}: {e}")
                print(f"❌ INTEGRAÇÃO {nome}: ERRO: {e}")
    
    def detectar_limitacoes(self):
        """Detecta limitações que justificariam migração para Lark"""
        print("\n" + "="*50)
        print("DETECTANDO LIMITAÇÕES DO PARSER ATUAL")
        print("="*50)
        
        casos_complexos = [
            ("Precedência Operadores", "a + b * c / d - e"),
            ("Aninhamento Profundo", "soma de soma de x[i,j] PARA CADA j EM lista PARA CADA i EM outra"),
            ("Condicionais Aninhadas", "SE a > 0 ENTAO SE b > 0 ENTAO c SENAO d SENAO e"),
            ("Parênteses Complexos", "((a + b) * (c - d)) / ((e + f) * (g - h))"),
            ("Joins Múltiplos", """
            soma de produtos.Custo * ordens.Quantidade * clientes.Multiplicador
            PARA CADA produto EM produtos
            PARA CADA ordem EM ordens  
            ONDE produtos.ID = ordens.Produto E ordens.Cliente = clientes.ID
            """)
        ]
        
        limitacoes_encontradas = 0
        
        for nome, caso in casos_complexos:
            try:
                expressao = self.parser.analisar_texto(caso)
                codigo = self.parser.traduzir_para_pulp(expressao)
                
                analisador = AnalisadorCodigoGerado(codigo)
                validacao = analisador.validar_completo()
                
                if not (validacao['valido_python'] and validacao['parenteses_balanceados']):
                    limitacoes_encontradas += 1
                    self.resultados['limitacoes'].append(nome)
                    print(f"⚠️ LIMITAÇÃO: {nome}")
                    print(f"   Caso: {caso[:50]}...")
                    print(f"   Resultado: {codigo[:50]}...")
                else:
                    print(f"✅ OK: {nome}")
                    
            except Exception as e:
                limitacoes_encontradas += 1
                self.resultados['limitacoes'].append(nome)
                print(f"❌ FALHA: {nome} -> {e}")
        
        # Análise final
        total_casos = len(casos_complexos)
        taxa_limitacao = limitacoes_encontradas / total_casos
        
        print(f"\n--- ANÁLISE DE LIMITAÇÕES ---")
        print(f"Casos com limitação: {limitacoes_encontradas}/{total_casos} ({taxa_limitacao*100:.1f}%)")
        
        if taxa_limitacao >= 0.5:
            print("🚨 RECOMENDAÇÃO: MIGRAÇÃO PARA LARK ALTAMENTE RECOMENDADA")
            print("Benefícios do Lark:")
            print("- Parsing mais robusto e confiável")
            print("- Melhor tratamento de precedência de operadores")
            print("- Gramática clara e extensível")
            print("- Melhor tratamento de erros")
            print("- Suporte nativo a estruturas complexas")
        elif taxa_limitacao >= 0.3:
            print("⚠️ CONSIDERAÇÃO: Migração para Lark pode ser benéfica")
        else:
            print("✅ Parser atual adequado para casos básicos")
        
        return taxa_limitacao
    
    def gerar_relatorio_final(self):
        """Gera relatório final dos testes"""
        print("\n" + "="*60)
        print("RELATÓRIO FINAL DE TESTES")
        print("="*60)
        
        total_passou = sum(r['passou'] for r in self.resultados.values() if isinstance(r, dict))
        total_falhou = sum(r['falhou'] for r in self.resultados.values() if isinstance(r, dict))
        total_testes = total_passou + total_falhou
        
        print(f"📊 ESTATÍSTICAS GERAIS:")
        print(f"   Total de testes: {total_testes}")
        print(f"   Sucessos: {total_passou}")
        print(f"   Falhas: {total_falhou}")
        print(f"   Taxa de sucesso: {total_passou/total_testes*100:.1f}%")
        
        print(f"\n📋 DETALHAMENTO POR COMPONENTE:")
        for componente, dados in self.resultados.items():
            if isinstance(dados, dict):
                total_comp = dados['passou'] + dados['falhou']
                if total_comp > 0:
                    taxa = dados['passou'] / total_comp * 100
                    print(f"   {componente.upper()}: {dados['passou']}/{total_comp} ({taxa:.1f}%)")
        
        print(f"\n⚠️ LIMITAÇÕES IDENTIFICADAS:")
        if self.resultados['limitacoes']:
            for limitacao in self.resultados['limitacoes']:
                print(f"   - {limitacao}")
        else:
            print("   Nenhuma limitação crítica identificada")
        
        print(f"\n🎯 RECOMENDAÇÕES:")
        
        # Análise baseada nos resultados
        taxa_sucesso_geral = total_passou / total_testes if total_testes > 0 else 0
        numero_limitacoes = len(self.resultados['limitacoes'])
        
        if taxa_sucesso_geral >= 0.8 and numero_limitacoes <= 2:
            print("   ✅ Parser atual está funcionando bem para casos básicos e intermediários")
            print("   ✅ Continuar desenvolvimento com arquitetura atual")
            print("   📝 Focar em correções pontuais e melhorias incrementais")
        elif taxa_sucesso_geral >= 0.6 or numero_limitacoes >= 3:
            print("   ⚠️ Parser atual mostra limitações significativas")
            print("   🔄 CONSIDERAR MIGRAÇÃO PARA LARK")
            print("   📚 Lark ofereceria parsing mais robusto e extensível")
        else:
            print("   🚨 MIGRAÇÃO PARA LARK ALTAMENTE RECOMENDADA")
            print("   ❌ Parser atual inadequado para casos complexos")
            print("   🛠️ Lark é necessário para casos de uso reais")
        
        print(f"\n💾 PRÓXIMOS PASSOS:")
        print("   1. Corrigir erros específicos identificados")
        print("   2. Implementar casos de teste automatizados")
        print("   3. Avaliar migração para Lark se necessário")
        print("   4. Integrar com otimizador PuLP")


def main():
    """Função principal"""
    print("INICIANDO BATERIA COMPLETA DE TESTES DO PARSER LOS")
    print("=" * 60)
    
    inicio_geral = time.time()
    
    executor = ExecutorTestes()
    
    # Executar todos os testes
    executor.executar_testes_lexer()
    executor.executar_testes_tradutor()
    executor.executar_testes_parser()
    executor.executar_testes_integracao()
    
    # Detectar limitações
    taxa_limitacao = executor.detectar_limitacoes()
    
    # Relatório final
    executor.gerar_relatorio_final()
    
    fim_geral = time.time()
    tempo_total = fim_geral - inicio_geral
    
    print(f"\n⏱️ TEMPO TOTAL: {tempo_total:.2f} segundos")
    print("="*60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Testes interrompidos pelo usuário")
    except Exception as e:
        print(f"\n💥 ERRO CRÍTICO: {e}")
        traceback.print_exc()
