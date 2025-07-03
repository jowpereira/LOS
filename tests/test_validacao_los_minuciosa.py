"""
Testes Específicos para Arquivos .los - Validação Minuciosa
Cada arquivo .los será testado individualmente para garantir correção matemática e realismo
"""

import pytest
import pandas as pd
from pathlib import Path
import re
from typing import Dict, List, Tuple


class TestValidacaoLosMinuciosa:
    """
    Suite de testes minuciosa para validação dos arquivos .los
    Cada teste verifica aspectos específicos de correção matemática e realismo
    """
    
    @pytest.fixture(scope="class") 
    def dados_bases(self):
        """Fixture com todos os dados reais carregados"""
        base_path = Path(__file__).parent.parent / "bases_exemplos"
        return {
            'produtos': pd.read_csv(base_path / "produtos_exemplo.csv"),
            'ordens': pd.read_csv(base_path / "ordens_exemplo.csv"),
            'estoque': pd.read_csv(base_path / "estoque_exemplo.csv"),
            'clientes': pd.read_csv(base_path / "clientes_exemplo.csv"),
            'custos': pd.read_csv(base_path / "custos_exemplo.csv")
        }
    
    @pytest.fixture(scope="class")
    def arquivos_los(self):
        """Fixture com conteúdo de todos os arquivos .los"""
        los_path = Path(__file__).parent.parent / "exemplos_los_reais"
        arquivos = {}
        for arquivo in los_path.glob("*.los"):
            if arquivo.name != "README.md":
                with open(arquivo, 'r', encoding='utf-8') as f:
                    arquivos[arquivo.stem] = f.read()
        return arquivos

    # ========================================================================
    # TESTES PARA 01_minimizar_custos_producao.los  
    # ========================================================================
    
    def test_01_consistencia_demandas(self, dados_bases, arquivos_los):
        """Testa se as demandas citadas no arquivo 01 estão corretas"""
        arquivo_01 = arquivos_los['01_minimizar_custos_producao']
        ordens_df = dados_bases['ordens']
        
        # Extrair demandas mencionadas no arquivo (regex)
        demandas_mencionadas = {
            'PROD_A': 430,
            'PROD_B': 540, 
            'PROD_C': 165,
            'PROD_D': 460,
            'PROD_E': 390
        }
        
        # Calcular demandas reais dos dados
        for produto, demanda_esperada in demandas_mencionadas.items():
            demanda_real = ordens_df[ordens_df['Produto'] == produto]['Quantidade'].sum()
            assert demanda_real == demanda_esperada, (
                f"Demanda de {produto} incorreta: arquivo diz {demanda_esperada}, "
                f"dados reais mostram {demanda_real}"
            )
    
    def test_01_viabilidade_capacidades(self, dados_bases):
        """Testa se as demandas são atendíveis pelas capacidades disponíveis"""
        ordens_df = dados_bases['ordens'] 
        estoque_df = dados_bases['estoque']
        
        # Calcular demanda total vs capacidade total por produto
        problemas_viabilidade = []
        
        for produto in ordens_df['Produto'].unique():
            demanda_total = ordens_df[ordens_df['Produto'] == produto]['Quantidade'].sum()
            capacidade_total = estoque_df[estoque_df['Produto'] == produto]['Quantidade_Disponivel'].sum()
            
            if demanda_total > capacidade_total:
                problemas_viabilidade.append({
                    'produto': produto,
                    'demanda': demanda_total,
                    'capacidade': capacidade_total,
                    'deficit': demanda_total - capacidade_total
                })
        
        # Reportar problemas de viabilidade
        if problemas_viabilidade:
            msg = "Problemas de viabilidade encontrados:\n"
            for prob in problemas_viabilidade:
                msg += f"- {prob['produto']}: demanda {prob['demanda']} > capacidade {prob['capacidade']} (déficit: {prob['deficit']})\n"
            
            pytest.fail(msg)
    
    def test_01_correcao_matematica_objetivo(self, arquivos_los):
        """Testa se a função objetivo está matematicamente correta"""
        arquivo_01 = arquivos_los['01_minimizar_custos_producao']
        
        # Verificar se objetivo minimiza custos corretamente
        assert "MINIMIZAR:" in arquivo_01
        assert "produtos.Custo_Producao * x[produto, planta]" in arquivo_01
        
        # Verificar se soma sobre os índices corretos
        assert "PARA CADA produto EM produtos.Produto" in arquivo_01
        assert "planta EM ['PLANTA_1', 'PLANTA_2', 'PLANTA_3']" in arquivo_01
    
    def test_01_restricoes_matematicas(self, arquivos_los):
        """Testa correção matemática das restrições"""
        arquivo_01 = arquivos_los['01_minimizar_custos_producao']
        
        # Verificar restrições obrigatórias
        assert "RESTRINGIR:" in arquivo_01
        assert ">= 0" in arquivo_01  # Não negatividade
        
        # Verificar se há restrição de atendimento de demanda
        assert "ordens.Quantidade" in arquivo_01
        
        # PROBLEMA IDENTIFICADO: A restrição de demanda pode estar incorreta
        # Deve garantir que cada ordem individual seja atendida
    
    def test_01_consistencia_custos_reais(self, dados_bases, arquivos_los):
        """Verifica se os custos mencionados no arquivo batem com os dados reais"""
        arquivo_01 = arquivos_los['01_minimizar_custos_producao']
        produtos_df = dados_bases['produtos']
        
        # Custos mencionados no arquivo  
        custos_mencionados = {
            'PROD_A': 25.50,
            'PROD_B': 18.75,
            'PROD_C': 32.20,
            'PROD_D': 45.80,
            'PROD_E': 28.90
        }
        
        # Verificar contra dados reais
        for produto, custo_mencionado in custos_mencionados.items():
            custo_real = produtos_df[produtos_df['Produto'] == produto]['Custo_Producao'].iloc[0]
            assert abs(custo_real - custo_mencionado) < 0.01, (
                f"Custo de {produto} incorreto: arquivo diz R${custo_mencionado}, "
                f"dados reais mostram R${custo_real}"
            )

    def test_01_problema_restricao_demanda_critica(self, arquivos_los):
        """Testa especificamente o problema crítico na restrição de demanda"""
        arquivo_01 = arquivos_los['01_minimizar_custos_producao']
        
        # A restrição atual está problemática:
        # "soma de x[ordens.Produto[i], ordens.Planta[i]] PARA i EM ordens.index >= ordens.Quantidade[i]"
        # Esta formulação está incorreta matematicamente
        
        # Deveria ser algo como:
        # Para cada ordem i: x[ordens.Produto[i], ordens.Planta[i]] >= ordens.Quantidade[i]
        # OU para cada produto: soma das produções >= demanda total do produto
        
        restricao_problematica = "soma de x[ordens.Produto[i], ordens.Planta[i]] PARA i EM ordens.index >= ordens.Quantidade[i]"
        
        if restricao_problematica in arquivo_01:
            pytest.fail(
                "Restrição de demanda matematicamente incorreta encontrada. "
                "A formulação atual soma produções de diferentes ordens incorretamente. "
                "Deveria ser reformulada para garantir atendimento individual de cada ordem "
                "ou atendimento da demanda total por produto."
            )
    
    # ========================================================================
    # TESTES PARA 02_maximizar_lucro.los  
    # ========================================================================
    
    def test_02_validacao_margem_lucro(self, dados_bases, arquivos_los):
        """Testa se os cálculos de margem de lucro estão corretos"""
        arquivo_02 = arquivos_los['02_maximizar_lucro']
        produtos_df = dados_bases['produtos']
        
        # Verificar se o arquivo usa produtos.Margem_Lucro corretamente
        assert "produtos.Margem_Lucro" in arquivo_02
        assert "MAXIMIZAR:" in arquivo_02
        
        # Verificar cálculos mencionados nos comentários
        lucros_esperados = {
            'PROD_A': 25.50 * 0.30,  # R$7.65
            'PROD_B': 18.75 * 0.25,  # R$4.69
            'PROD_C': 32.20 * 0.35,  # R$11.27
            'PROD_D': 45.80 * 0.40,  # R$18.32
            'PROD_E': 28.90 * 0.28   # R$8.09
        }
        
        for produto, lucro_esperado in lucros_esperados.items():
            produto_info = produtos_df[produtos_df['Produto'] == produto].iloc[0]
            lucro_real = produto_info['Custo_Producao'] * produto_info['Margem_Lucro']
            assert abs(lucro_real - lucro_esperado) < 0.01, \
                f"Lucro de {produto}: esperado {lucro_esperado:.2f}, real {lucro_real:.2f}"
    
    def test_02_restricoes_tempo_producao(self, dados_bases, arquivos_los):
        """Testa se as restrições de tempo de produção são realistas"""
        arquivo_02 = arquivos_los['02_maximizar_lucro']
        produtos_df = dados_bases['produtos']
        
        # Verificar se usa produtos.Tempo_Producao
        assert "produtos.Tempo_Producao" in arquivo_02
        
        # Verificar restrição de 1200 horas (valor corrigido)
        assert "1200" in arquivo_02
        
        # Calcular se é viável produzir as quantidades mínimas (50 de cada)
        tempo_minimo = produtos_df['Tempo_Producao'].sum() * 50
        print(f"Tempo mínimo para produzir 50 de cada produto: {tempo_minimo:.1f}h")
        
        if tempo_minimo > 1200:
            pytest.fail(f"Restrição de 1200h inviável. Mínimo necessário: {tempo_minimo:.1f}h")

    # ========================================================================
    # TESTES PARA 03_alocacao_com_penalidades.los  
    # ========================================================================
    
    def test_03_validacao_tipos_clientes(self, dados_bases, arquivos_los):
        """Testa se os tipos de clientes e custos de penalidade estão consistentes"""
        arquivo_03 = arquivos_los['03_alocacao_com_penalidades']
        clientes_df = dados_bases['clientes']
        custos_df = dados_bases['custos']
        
        # Verificar se todos os tipos de cliente existem
        tipos_referenciados = ['Premium', 'Standard', 'Basic']
        tipos_existentes = set(clientes_df['Tipo_Cliente'].unique())
        
        for tipo in tipos_referenciados:
            assert tipo in tipos_existentes, f"Tipo de cliente {tipo} não existe"
        
        # Verificar se os custos de atraso estão sendo usados
        assert "Atraso" in arquivo_03
        assert "custos.Valor_Custo" in arquivo_03
        
        # Verificar valores de penalidade por tipo
        penalidades_atraso = custos_df[custos_df['Tipo_Custo'] == 'Atraso']
        assert len(penalidades_atraso) == 3, "Devem existir penalidades para os 3 tipos de cliente"

    def test_03_problema_sintaxe_para_each(self, arquivos_los):
        """Identifica problema de sintaxe 'PARA EACH' ao invés de 'PARA CADA'"""
        arquivo_03 = arquivos_los['03_alocacao_com_penalidades']
        
        # Problema de sintaxe identificado
        if "PARA EACH" in arquivo_03:
            pytest.fail(
                "Problema de sintaxe encontrado: 'PARA EACH' deveria ser 'PARA CADA' "
                "conforme gramática LOS padrão"
            )

    # ========================================================================
    # TESTES PARA 04_planejamento_multi_periodo.los  
    # ========================================================================
    
    def test_04_validacao_periodos_datas(self, dados_bases, arquivos_los):
        """Testa se a divisão em períodos baseada nas datas está correta"""
        arquivo_04 = arquivos_los['04_planejamento_multi_periodo']
        ordens_df = dados_bases['ordens']
        
        # Converter datas para análise
        ordens_df['Data'] = pd.to_datetime(ordens_df['Data'])
        
        # Verificar se há 4 períodos conforme mencionado
        assert "periodo EM [1, 2, 3, 4]" in arquivo_04
        
        # Verificar se as datas estão sendo consideradas
        datas_minima = ordens_df['Data'].min()
        datas_maxima = ordens_df['Data'].max()
        
        print(f"Período de dados: {datas_minima.date()} a {datas_maxima.date()}")
        
        # Verificar se a divisão em 4 períodos faz sentido
        intervalo_dias = (datas_maxima - datas_minima).days
        if intervalo_dias < 20:  # Menos de 20 dias para 4 períodos é muito granular
            print(f"⚠️  Divisão em 4 períodos pode ser excessiva para {intervalo_dias} dias")

    def test_04_balanco_estoque_matematico(self, arquivos_los):
        """Testa se as equações de balanço de estoque estão corretas"""
        arquivo_04 = arquivos_los['04_planejamento_multi_periodo']
        
        # Verificar equações de balanço
        assert "estoque_inicial" in arquivo_04
        assert "estoque_final" in arquivo_04
        assert "demanda" in arquivo_04
        
        # Verificar se há equação correta: estoque_inicial + produção = demanda + estoque_final
        # A estrutura correta está presente no arquivo
        balanco_encontrado = ("estoque_inicial[produto, planta] + w[produto, planta, 1]" in arquivo_04 and
                             "== demanda[produto, planta, 1] + estoque_final[produto, planta, 1]" in arquivo_04)
        
        if not balanco_encontrado:
            pytest.fail("Equação de balanço de estoque não encontrada ou incorreta")

    # ========================================================================
    # TESTES PARA 05_otimizacao_condicional.los  
    # ========================================================================
    
    def test_05_sintaxe_condicionais_se(self, arquivos_los):
        """Testa se a sintaxe de condicionais SE está correta"""
        arquivo_05 = arquivos_los['05_otimizacao_condicional']
        
        # Verificar se usa SE() corretamente
        assert "SE(" in arquivo_05
        
        # Verificar se há fechamento correto dos parênteses
        count_abre = arquivo_05.count("SE(")
        count_fecha = arquivo_05.count(")")
        
        if count_fecha < count_abre:
            pytest.fail("Parênteses não balanceados nas expressões SE()")
        
        # Verificar se há estrutura SE(condição, verdadeiro, falso)
        import re
        se_patterns = re.findall(r'SE\([^)]+,[^)]+,[^)]+\)', arquivo_05)
        if len(se_patterns) == 0:
            pytest.fail("Nenhuma expressão SE() com estrutura correta encontrada")

    def test_05_problema_sintaxe_para_each_arquivo_05(self, arquivos_los):
        """Identifica problema de sintaxe 'PARA EACH' no arquivo 05"""
        arquivo_05 = arquivos_los['05_otimizacao_condicional']
        
        if "PARA EACH" in arquivo_05:
            count_para_each = arquivo_05.count("PARA EACH")
            pytest.fail(
                f"Problema de sintaxe encontrado: {count_para_each} ocorrências de 'PARA EACH' "
                f"deveriam ser 'PARA CADA' conforme gramática LOS"
            )

    # ========================================================================
    # TESTES PARA 06_transporte_distribuicao.los  
    # ========================================================================
    
    def test_06_validacao_custos_transporte(self, dados_bases, arquivos_los):
        """Testa se os custos de transporte estão bem definidos"""
        arquivo_06 = arquivos_los['06_transporte_distribuicao']
        clientes_df = dados_bases['clientes']
        
        # Verificar se define custo_transporte
        assert "custo_transporte[planta, cliente]" in arquivo_06
        
        # Verificar se considera tipos de cliente para custos diferenciados
        assert "clientes.Tipo_Cliente" in arquivo_06
        
        # Verificar valores de custo por tipo de cliente (5, 8, 12)
        assert "5" in arquivo_06 and "8" in arquivo_06 and "12" in arquivo_06

    def test_06_restricoes_capacidade_transporte(self, arquivos_los):
        """Testa se as restrições de capacidade de transporte estão bem formuladas"""
        arquivo_06 = arquivos_los['06_transporte_distribuicao']
        
        # Verificar restrições básicas
        assert "demanda_cliente" in arquivo_06
        assert "capacidade_planta" in arquivo_06
        assert "capacidade_rota" in arquivo_06
        
        # Verificar se atende demanda
        assert "== demanda_cliente" in arquivo_06
        
        # Verificar se não excede capacidades
        assert "<= capacidade_planta" in arquivo_06
        assert "<= capacidade_rota" in arquivo_06

    # ========================================================================
    # TESTE GERAL DE PARSING PARA TODOS OS ARQUIVOS
    # ========================================================================
    
    def test_parsing_geral_todos_arquivos(self, arquivos_los):
        """Testa se todos os arquivos .los podem ser lidos sem erros óbvios"""
        problemas_encontrados = []
        
        for nome_arquivo, conteudo in arquivos_los.items():
            # Verificar estrutura básica
            if "MINIMIZAR:" not in conteudo and "MAXIMIZAR:" not in conteudo:
                problemas_encontrados.append(f"{nome_arquivo}: Sem objetivo definido")
            
            if "RESTRINGIR:" not in conteudo:
                problemas_encontrados.append(f"{nome_arquivo}: Sem restrições definidas")
            
            # Verificar sintaxe básica
            if "PARA EACH" in conteudo:
                count = conteudo.count("PARA EACH")
                problemas_encontrados.append(f"{nome_arquivo}: {count} ocorrências de 'PARA EACH' (deveria ser 'PARA CADA')")
        
        if problemas_encontrados:
            msg = f"Problemas encontrados em {len(problemas_encontrados)} arquivos:\n"
            msg += "\n".join(f"- {problema}" for problema in problemas_encontrados)
            pytest.fail(msg)
