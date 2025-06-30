# -*- coding: utf-8 -*-
"""
Configuração base para testes do LOS Parser
"""

import pytest
import pandas as pd
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from los_parser import ParserLOS, ExpressaoLOS
    PARSER_DISPONIVEL = True
except ImportError as e:
    print(f"⚠️ LOS Parser não disponível: {e}")
    PARSER_DISPONIVEL = False

@pytest.fixture
def parser_los():
    """Fixture que fornece uma instância do ParserLOS"""
    if not PARSER_DISPONIVEL:
        pytest.skip("LOS Parser não disponível")
    return ParserLOS()

@pytest.fixture
def dados_exemplo():
    """Fixture com dados de exemplo para testes"""
    return {
        'produtos': pd.DataFrame({
            'ID': [1, 2, 3],
            'custo': [10.5, 15.2, 8.7],
            'preco': [25.0, 30.0, 20.0]
        }),
        'clientes': pd.DataFrame({
            'ID': [101, 102, 103],
            'nome': ['Cliente A', 'Cliente B', 'Cliente C'],
            'demanda': [100, 150, 80]
        })
    }
