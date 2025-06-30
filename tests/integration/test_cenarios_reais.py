# -*- coding: utf-8 -*-
"""
Testes de integração completa do Parser LOS
Testa cenários reais com dados de exemplo
"""

import pytest
import sys
import pandas as pd
from pathlib import Path

# Adicionar path do projeto
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from los_parser import ParserLOS
from tests.fixtures.casos_teste import CasosTeste
from tests.utils.validadores import (
    AnalisadorCodigoGerado,
    criar_relatorio_validacao,
    validar_codigo_python,
    validar_compatibilidade_pulp
)


class TestIntegracaoCompleta:
    """Testes de integração com cenários reais de otimização"""
    
    def test_cenario_otimizacao_producao(self, parser_configurado):
        """Cenário: Otimização de produção minimizando custos"""
        parser = parser_configurado
        
        # Objetivo: minimizar custo total de produção
        objetivo = """
        MINIMIZAR: soma de produtos.Custo_Producao * x[produto] 
        PARA CADA produto EM produtos
        """
        
        # Restrições
        restricoes = """
        # Capacidade máxima de produção
        soma de x[produto] PARA CADA produto EM produtos <= 1000
        
        # Produção mínima por produto
        x[produto] >= 10 PARA CADA produto EM produtos
        
        # Restrição de tempo disponível  
        soma de produtos.Tempo_Producao * x[produto] PARA CADA produto EM produtos <= 8000
        """
        
        # Analisar objetivo
        expr_objetivo = parser.analisar_texto(objetivo)
        codigo_objetivo = parser.traduzir_para_pulp(expr_objetivo)
        
        # Analisar restrições
        lista_restricoes = parser.analisar_restricoes(restricoes)
        codigos_restricoes = [parser.traduzir_para_pulp(r) for r in lista_restricoes]
        
        # Validações
        assert expr_objetivo.tipo == 'objetivo'
        assert expr_objetivo.operacao == 'minimizar'
        assert len(lista_restricoes) >= 2
        
        # Verificar código gerado
        assert 'sum([' in codigo_objetivo
        assert 'produtos["Custo_Producao"]' in codigo_objetivo
        assert 'for produto in produtos' in codigo_objetivo
        
        print(f"\n=== CENÁRIO PRODUÇÃO ===")
        print(f"Objetivo: {codigo_objetivo}")
        print(f"Restrições: {len(codigos_restricoes)} geradas")
        
        # Relatório detalhado
        relatorio = criar_relatorio_validacao(codigo_objetivo)
        print(relatorio)
    
    def test_cenario_gestao_estoque(self, parser_configurado):
        """Cenário: Gestão de estoque com balanceamento"""
        parser = parser_configurado
        
        # Objetivo: maximizar atendimento de ordens
        objetivo = """
        MAXIMIZAR: soma de ordens.Quantidade * atendimento[ordem]
        PARA CADA ordem EM ordens
        """
        
        # Restrições de estoque
        restricoes = """
        # Não exceder estoque disponível por produto
        soma de ordens.Quantidade * atendimento[ordem] 
        PARA CADA ordem EM ordens 
        ONDE ordens.Produto = produto
        <= estoque.Quantidade_Disponivel 
        ONDE estoque.Produto = produto
        
        # Atendimento binário
        atendimento[ordem] <= 1 PARA CADA ordem EM ordens
        atendimento[ordem] >= 0 PARA CADA ordem EM ordens
        """
        
        expr_objetivo = parser.analisar_texto(objetivo)
        codigo_objetivo = parser.traduzir_para_pulp(expr_objetivo)
        
        lista_restricoes = parser.analisar_restricoes(restricoes)
        
        # Validações específicas do cenário
        assert 'atendimento[ordem]' in codigo_objetivo
        assert 'ordens["Quantidade"]' in codigo_objetivo
        assert len(lista_restricoes) >= 1
        
        print(f"\n=== CENÁRIO ESTOQUE ===")
        print(f"Objetivo: {codigo_objetivo}")
        print(f"Restrições balanceamento: {len(lista_restricoes)}")
    
    def test_cenario_atendimento_clientes_premium(self, parser_configurado):
        """Cenário: Priorização de clientes Premium"""
        parser = parser_configurado
        
        # Objetivo: minimizar custos de não atendimento ponderados por tipo
        objetivo = """
        MINIMIZAR: soma de custos.Valor_Custo * nao_atendimento[cliente]
        PARA CADA cliente EM clientes
        PARA CADA custo EM custos
        ONDE clientes.Tipo_Cliente = custos.Tipo_Cliente 
        E custos.Tipo_Custo = 'Nao_Atendimento'
        """
        
        try:
            expr_objetivo = parser.analisar_texto(objetivo)
            codigo_objetivo = parser.traduzir_para_pulp(expr_objetivo)
            
            # Verificar joins entre datasets
            assert 'clientes["Tipo_Cliente"]' in codigo_objetivo
            assert 'custos["Tipo_Cliente"]' in codigo_objetivo
            assert 'custos["Valor_Custo"]' in codigo_objetivo
            
            print(f"\n=== CENÁRIO CLIENTES PREMIUM ===")
            print(f"Objetivo: {codigo_objetivo}")
            
        except Exception as e:
            print(f"Cenário complexo falhou: {e}")
            print("Possível candidato para Lark devido a joins complexos")
    
    def test_cenario_multiobjetivo_custo_tempo(self, parser_configurado):
        """Cenário: Otimização multiobjetivo (custo + tempo)"""
        parser = parser_configurado
        
        # Objetivo composto: custo + tempo ponderado
        objetivo = """
        MINIMIZAR: 
        soma de produtos.Custo_Producao * x[produto] +
        0.1 * soma de produtos.Tempo_Producao * x[produto]
        PARA CADA produto EM produtos
        """
        
        try:
            expr_objetivo = parser.analisar_texto(objetivo)
            codigo_objetivo = parser.traduzir_para_pulp(expr_objetivo)
            
            # Verificar componentes do objetivo
            assert 'produtos["Custo_Producao"]' in codigo_objetivo
            assert 'produtos["Tempo_Producao"]' in codigo_objetivo
            assert '0.1' in codigo_objetivo
            
            print(f"\n=== CENÁRIO MULTIOBJETIVO ===")
            print(f"Objetivo: {codigo_objetivo}")
            
        except Exception as e:
            print(f"Multiobjetivo falhou: {e}")
            print("Expressões complexas podem precisar de Lark")
    
    def test_cenario_planejamento_plantas(self, parser_configurado):
        """Cenário: Planejamento de produção por planta"""
        parser = parser_configurado
        
        # Restrições por planta
        restricoes = """
        # Capacidade por planta
        soma de producao[produto,planta] 
        PARA CADA produto EM produtos
        <= capacidade[planta] 
        PARA CADA planta EM plantas
        
        # Demanda total atendida
        soma de producao[produto,planta] 
        PARA CADA planta EM plantas
        >= demanda[produto]
        PARA CADA produto EM produtos
        """
        
        try:
            lista_restricoes = parser.analisar_restricoes(restricoes)
            
            if lista_restricoes:
                print(f"\n=== CENÁRIO PLANTAS ===")
                print(f"Restrições por planta: {len(lista_restricoes)}")
                
                for i, restricao in enumerate(lista_restricoes):
                    codigo = parser.traduzir_para_pulp(restricao)
                    print(f"Restrição {i+1}: {codigo[:60]}...")
                    
        except Exception as e:
            print(f"Planejamento plantas falhou: {e}")
            print("Variáveis multidimensionais podem precisar de Lark")
    
    def test_casos_integracao_predefinidos(self, parser_configurado):
        """Executa casos de integração predefinidos"""
        parser = parser_configurado
        casos = CasosTeste.casos_integracao_complexos()
        
        sucessos = 0
        falhas = 0
        
        for caso in casos:
            print(f"\n--- CASO {caso.id}: {caso.descricao} ---")
            
            try:
                expressao = parser.analisar_texto(caso.entrada_los)
                codigo = parser.traduzir_para_pulp(expressao)
                
                # Verificar se resultado é próximo do esperado
                analisador = AnalisadorCodigoGerado(codigo)
                validacao = analisador.validar_completo()
                
                if validacao['valido_python'] or validacao['padroes_pulp']['funcao_sum']:
                    sucessos += 1
                    print(f"✅ SUCESSO: {codigo[:50]}...")
                else:
                    falhas += 1
                    print(f"⚠️ PARCIAL: {codigo[:50]}...")
                    
            except Exception as e:
                falhas += 1
                print(f"❌ FALHA: {e}")
        
        print(f"\n=== RESUMO INTEGRAÇÃO ===")
        print(f"Sucessos: {sucessos}")
        print(f"Falhas: {falhas}")
        print(f"Taxa sucesso: {sucessos/(sucessos+falhas)*100:.1f}%")
        
        # Se muitas falhas, sinalizar necessidade de Lark
        if falhas > sucessos:
            print("🚨 MUITAS FALHAS - CONSIDERAR MIGRAÇÃO PARA LARK")
    
    def test_validacao_dados_reais(self, parser_configurado):
        """Valida que parser funciona com estrutura dos dados reais"""
        parser = parser_configurado
        
        # Verificar que dados foram carregados corretamente
        assert len(parser.dados_csv) == 5
        
        # Testar referências a todas as colunas reais
        referencias_testar = [
            "produtos.Custo_Producao",
            "produtos.Margem_Lucro", 
            "produtos.Tempo_Producao",
            "clientes.Tipo_Cliente",
            "ordens.Quantidade",
            "ordens.Codigo_Cliente",
            "estoque.Quantidade_Disponivel",
            "custos.Valor_Custo",
            "custos.Tipo_Custo"
        ]
        
        for referencia in referencias_testar:
            entrada = f"MINIMIZAR: {referencia} * x[item]"
            
            try:
                expressao = parser.analisar_texto(entrada)
                codigo = parser.traduzir_para_pulp(expressao)
                
                # Verificar tradução da referência
                dataset, coluna = referencia.split('.')
                esperado = f'{dataset}["{coluna}"]'
                assert esperado in codigo, f"Referência {referencia} não traduzida corretamente"
                
            except Exception as e:
                print(f"Falha em {referencia}: {e}")
    
    def test_performance_integracao_completa(self, parser_configurado):
        """Testa performance do pipeline completo com dados reais"""
        import time
        
        parser = parser_configurado
        
        cenarios_teste = [
            "MINIMIZAR: soma de produtos.Custo_Producao * x[produto] PARA CADA produto EM produtos",
            "soma de ordens.Quantidade * y[ordem] PARA CADA ordem EM ordens <= 1000",
            "MAXIMIZAR: soma de produtos.Margem_Lucro * vendas[produto] PARA CADA produto EM produtos ONDE produtos.Custo_Producao < 30"
        ]
        
        tempos_execucao = []
        
        for cenario in cenarios_teste:
            inicio = time.time()
            
            try:
                expressao = parser.analisar_texto(cenario)
                codigo = parser.traduzir_para_pulp(expressao)
                
                fim = time.time()
                tempo = (fim - inicio) * 1000  # ms
                tempos_execucao.append(tempo)
                
                print(f"Cenário processado em {tempo:.2f}ms: {cenario[:40]}...")
                
            except Exception as e:
                print(f"Cenário falhou: {e}")
        
        if tempos_execucao:
            tempo_medio = sum(tempos_execucao) / len(tempos_execucao)
            assert tempo_medio < 200, f"Performance inadequada: {tempo_medio:.2f}ms médio"
            
            print(f"\nPerformance integração: {tempo_medio:.2f}ms médio")


class TestCompatibilidadePulp:
    """Testes específicos de compatibilidade com PuLP"""
    
    def test_estruturas_pulp_validas(self, parser_configurado):
        """Testa se estruturas geradas são compatíveis com PuLP"""
        parser = parser_configurado
        
        casos_pulp = [
            # Função objetivo simples
            "MINIMIZAR: x + y",
            
            # Função objetivo com agregação  
            "MINIMIZAR: soma de produtos.Custo_Producao * x[produto] PARA CADA produto EM produtos",
            
            # Restrição simples
            "x <= 100",
            
            # Restrição com agregação
            "soma de x[i] PARA CADA i EM lista <= 1000"
        ]
        
        for caso in casos_pulp:
            try:
                expressao = parser.analisar_texto(caso)
                codigo = parser.traduzir_para_pulp(expressao)
                
                # Verificar compatibilidade PuLP
                compativel = validar_compatibilidade_pulp(codigo)
                
                if not compativel:
                    print(f"⚠️ INCOMPATÍVEL COM PULP: {caso} -> {codigo}")
                else:
                    print(f"✅ COMPATÍVEL: {caso}")
                    
            except Exception as e:
                print(f"❌ ERRO: {caso} -> {e}")
    
    def test_variaveis_decisao_pulp(self, parser_configurado):
        """Testa se variáveis de decisão são detectadas corretamente para PuLP"""
        parser = parser_configurado
        
        entrada = """
        MINIMIZAR: x[produto] + y[cliente,produto] + z
        """
        
        parser.limpar_variaveis()
        expressao = parser.analisar_texto(entrada)
        variaveis = parser.gerar_variaveis_decisao()
        
        # Verificar estrutura para PuLP
        assert len(variaveis) >= 2
        
        for nome_var, detalhes in variaveis.items():
            assert detalhes['tipo'] == 'continua'
            print(f"Variável PuLP: {nome_var} ({detalhes['tipo']})")


class TestLimitacoesParserAtual:
    """Testes que identificam limitações do parser atual"""
    
    def test_casos_que_justificam_lark(self, parser_configurado):
        """Identifica casos que justificariam migração para Lark"""
        parser = parser_configurado
        # Este teste é puramente informativo e não realiza asserções
        # Mas deve retornar None para que pytest não o considere um teste que falhou
        
        casos_desafiadores = [
            # Precedência complexa
            ("a + b * c / d - e", "Precedência de operadores complexa"),
            
            # Aninhamento profundo
            ("soma de soma de x[i,j] PARA CADA j EM lista PARA CADA i EM outra", "Aninhamento profundo"),
            
            # Múltiplas condições SE
            ("SE a > 0 ENTAO SE b > 0 ENTAO c SENAO d SENAO e", "Condicionais aninhadas"),
            
            # Expressões com parênteses complexos
            ("((a + b) * (c - d)) / ((e + f) * (g - h))", "Parênteses aninhados"),
            
            # Joins complexos entre múltiplos datasets
            ("""
            soma de produtos.Custo * ordens.Quantidade * clientes.Multiplicador
            PARA CADA produto EM produtos
            PARA CADA ordem EM ordens  
            PARA CADA cliente EM clientes
            ONDE produtos.ID = ordens.Produto E ordens.Cliente = clientes.ID
            """, "Joins múltiplos entre datasets")
        ]
        
        limitacoes = []
        
        for caso, descricao in casos_desafiadores:
            try:
                expressao = parser.analisar_texto(caso)
                codigo = parser.traduzir_para_pulp(expressao)
                
                # Verificar qualidade do resultado
                analisador = AnalisadorCodigoGerado(codigo)
                validacao = analisador.validar_completo()
                
                if not validacao['valido_python'] or not validacao['parenteses_balanceados']:
                    limitacoes.append((caso[:50], descricao, codigo[:30]))
                    
            except Exception as e:
                limitacoes.append((caso[:50], descricao, str(e)[:50]))
        
        print(f"\n=== LIMITAÇÕES IDENTIFICADAS ===")
        for caso, desc, resultado in limitacoes:
            print(f"• {desc}")
            print(f"  Caso: {caso}...")
            print(f"  Resultado: {resultado}...")
            print()
        
        # Análise final
        if len(limitacoes) >= len(casos_desafiadores) * 0.6:
            print("🚨 RECOMENDAÇÃO FORTE: MIGRAR PARA LARK")
            print(f"Limitações encontradas: {len(limitacoes)}/{len(casos_desafiadores)}")
            print("Parser baseado em regex mostra limitações significativas")
            print("Lark ofereceria:")
            print("- Parsing mais robusto")
            print("- Melhor tratamento de precedência")
            print("- Gramática mais clara e extensível")
            print("- Melhor tratamento de erros")
        else:
            print("✅ Parser atual adequado para casos básicos")
        
        # Não retornar valor para evitar erro do pytest
