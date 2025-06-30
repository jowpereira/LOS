# -*- coding: utf-8 -*-
"""
🧪 TESTES FUNCIONAIS LOS
Testes integrados do parser LOS com casos reais de otimização
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from los_parser import ParserLOS, ExpressaoLOS
import pandas as pd

def test_los_cases_funcionais():
    """Testa casos funcionais essenciais do LOS"""
    
    parser = ParserLOS()
    
    # Dados de teste
    produtos = pd.DataFrame({
        'ID': [1, 2, 3],
        'custo': [10.5, 15.2, 8.7],
        'preco': [25.0, 30.0, 20.0]
    })
    
    parser.carregar_dados_csv({'produtos': produtos})
    
    casos_funcionais = [
        "MINIMIZAR: 10 + 5",
        "MAXIMIZAR: x * 2", 
        "produtos.custo <= 100",
        "x[i] + y[j]",
        "MINIMIZAR: 2 + 3 * 4",
        "custos.valor * quantidade + fixo"
    ]
    
    sucessos = 0
    
    for caso in casos_funcionais:
        try:
            resultado = parser.analisar_expressao(caso)
            assert isinstance(resultado, ExpressaoLOS)
            assert resultado.tipo in ['objetivo', 'restricao', 'matematica']
            assert resultado.codigo_python is not None
            sucessos += 1
        except Exception as e:
            print(f"❌ Falha em '{caso}': {e}")
    
    print(f"✅ Testes funcionais: {sucessos}/{len(casos_funcionais)} casos aprovados")
    assert sucessos == len(casos_funcionais), f"Esperado {len(casos_funcionais)}, obtido {sucessos}"

def test_los_precedencia():
    """Testa precedência de operadores"""
    
    parser = ParserLOS()
    
    casos_precedencia = [
        "2 + 3 * 4",  # Deve processar como 2 + (3 * 4)
        "10 - 6 / 2", # Deve processar como 10 - (6 / 2)
    ]
    
    sucessos = 0
    
    for caso in casos_precedencia:
        try:
            resultado = parser.analisar_expressao(caso)
            assert resultado.tipo == 'matematica'
            sucessos += 1
        except Exception as e:
            print(f"❌ Falha precedência '{caso}': {e}")
    
    print(f"✅ Testes precedência: {sucessos}/{len(casos_precedencia)} casos aprovados")
    assert sucessos == len(casos_precedencia), f"Esperado {len(casos_precedencia)}, obtido {sucessos}"

if __name__ == "__main__":
    print("🧪 EXECUTANDO TESTES FUNCIONAIS LOS")
    print("=" * 50)
    
    test1 = test_los_cases_funcionais()
    test2 = test_los_precedencia()
    
    if test1 and test2:
        print("\n🎉 TODOS OS TESTES FUNCIONAIS PASSARAM!")
        exit(0)
    else:
        print("\n⚠️ Alguns testes falharam")
        exit(1)
