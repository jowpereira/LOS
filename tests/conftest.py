# -*- coding: utf-8 -*-
"""
Configuração base para testes do LOS Parser
Inclui fixtures e utilitários comuns
"""

import pytest
import pandas as pd
import sys
from pathlib import Path

# Adicionar diretório raiz ao path para importar o parser
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

try:
    from los_parser import ParserLOS, ExpressaoLOS, TradutorLOS
    PARSER_DISPONIVEL = True
except ImportError as e:
    print(f"⚠️ LOS Parser não disponível: {e}")
    PARSER_DISPONIVEL = False

@pytest.fixture
def dados_exemplo():
    """Fixture com todos os dados de exemplo carregados"""
    base_dir = Path(__file__).parent.parent / "bases_exemplos"
    
    dados = {}
    
    try:
        # Clientes
        dados['clientes'] = pd.read_csv(base_dir / "clientes_exemplo.csv")
        
        # Produtos  
        dados['produtos'] = pd.read_csv(base_dir / "produtos_exemplo.csv")
        
        # Ordens
        dados['ordens'] = pd.read_csv(base_dir / "ordens_exemplo.csv")
        
        # Estoque
        dados['estoque'] = pd.read_csv(base_dir / "estoque_exemplo.csv")
        
        # Custos
        dados['custos'] = pd.read_csv(base_dir / "custos_exemplo.csv")
    except FileNotFoundError:
        # Dados sintéticos para testes
        dados['produtos'] = pd.DataFrame({
            'ID_Produto': [1, 2, 3],
            'Nome': ['Produto_A', 'Produto_B', 'Produto_C'],
            'Custo_Producao': [10.5, 15.2, 8.7],
            'Preco_Venda': [25.0, 30.0, 20.0]
        })
        
        dados['clientes'] = pd.DataFrame({
            'ID_Cliente': [101, 102, 103],
            'Nome Cliente': ['Cliente A', 'Cliente B', 'Cliente C'],
            'Demanda_Max': [100, 150, 80]
        })
    
    return dados

@pytest.fixture
def parser_los():
    """Fixture com LOS Parser limpo"""
    if not PARSER_DISPONIVEL:
        pytest.skip("LOS Parser não disponível")
    return ParserLOS()

@pytest.fixture
def parser_configurado(dados_exemplo):
    """Fixture com parser já configurado com dados de exemplo"""
    if not PARSER_DISPONIVEL:
        pytest.skip("LOS Parser não disponível")
    parser = ParserLOS()
    parser.carregar_dados_csv(dados_exemplo)
    return parser

@pytest.fixture
def tradutor_los():
    """Fixture com tradutor LOS limpo"""
    if not PARSER_DISPONIVEL:
        pytest.skip("LOS Parser não disponível")
    return TradutorLOS()
