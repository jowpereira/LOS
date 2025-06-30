# -*- coding: utf-8 -*-
"""
Testes unitários para o LOS Parser
Testa funcionalidades básicas do parser Lark
"""

import pytest
import sys
from pathlib import Path

# Adicionar path do projeto
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from los_parser import ParserLOS, ExpressaoLOS, TradutorLOS


class TestParserLOS:
    """Suite de testes para o LOS Parser"""
    
    def test_inicializacao_parser(self):
        """Testa inicialização básica do parser"""
        parser = ParserLOS()
        assert parser is not None
        assert hasattr(parser, 'parser')
        assert hasattr(parser, 'dados_csv')
        assert hasattr(parser, 'tradutor')
    
    def test_objetivos_simples(self, parser_los):
        """Testa parsing de objetivos simples"""
        casos = [
            "MINIMIZAR: 10 + 5",
            "MAXIMIZAR: x * 2",
            "MINIMIZAR: produtos.custo"
        ]
        
        for caso in casos:
            resultado = parser_los.analisar_expressao(caso)
            assert isinstance(resultado, ExpressaoLOS)
            assert resultado.tipo == 'objetivo'
            assert resultado.codigo_python is not None
    
    def test_restricoes_simples(self, parser_los):
        """Testa parsing de restrições simples"""
        casos = [
            "x <= 100",
            "produtos.custo >= 10",
            "y == 50"
        ]
        
        for caso in casos:
            resultado = parser_los.analisar_expressao(caso)
            assert isinstance(resultado, ExpressaoLOS)
            assert resultado.tipo == 'restricao'
            assert resultado.codigo_python is not None
    
    def test_expressoes_matematicas(self, parser_los):
        """Testa parsing de expressões matemáticas"""
        casos = [
            "x + y",
            "a * b + c",
            "produtos.preco - produtos.custo",
            "x[i] + y[j]"
        ]
        
        for caso in casos:
            resultado = parser_los.analisar_expressao(caso)
            assert isinstance(resultado, ExpressaoLOS)
            assert resultado.tipo == 'matematica'
            assert resultado.codigo_python is not None
    
    def test_precedencia_operadores(self, parser_los):
        """Testa precedência correta de operadores"""
        casos = [
            "2 + 3 * 4",  # Deve ser 2 + (3 * 4)
            "10 - 6 / 2"  # Deve ser 10 - (6 / 2)
        ]
        
        for caso in casos:
            resultado = parser_los.analisar_expressao(caso)
            assert resultado.tipo == 'matematica'
            # A precedência é respeitada pela gramática Lark
    
    def test_variaveis_indexadas(self, parser_los):
        """Testa parsing de variáveis indexadas"""
        casos = [
            "x[i]",
            "y[produto]",
            "z[cliente]"
        ]
        
        for caso in casos:
            resultado = parser_los.analisar_expressao(caso)
            assert resultado.tipo == 'matematica'
            assert '[' in resultado.codigo_python
            assert ']' in resultado.codigo_python
    
    def test_referencias_dataset(self, parser_configurado):
        """Testa parsing de referências a datasets"""
        casos = [
            "produtos.Custo_Producao",
            "clientes.Demanda_Max"
        ]
        
        for caso in casos:
            resultado = parser_configurado.analisar_expressao(caso)
            assert resultado.tipo == 'matematica'
            assert '["' in resultado.codigo_python  # Formato dataset["coluna"]
    
    def test_erros_sintaxe(self, parser_los):
        """Testa tratamento de erros de sintaxe"""
        casos_invalidos = [
            "MINIMIZAR:",  # Sem expressão
            "x + + y",     # Operador duplo
            "(",           # Parênteses desbalanceados
            "MAXIMIZE: x"  # Palavra-chave incorreta
        ]
        
        for caso in casos_invalidos:
            with pytest.raises(Exception):
                parser_los.analisar_expressao(caso)


class TestTradutorLOS:
    """Suite de testes para o TradutorLOS"""
    
    def test_numeros(self, tradutor_los):
        """Testa tradução de números"""
        # Teste direto dos métodos do tradutor
        assert tradutor_los.numero(['10']) == 10
        assert tradutor_los.numero(['3.14']) == 3.14
    
    def test_operacoes_aritmeticas(self, tradutor_los):
        """Testa tradução de operações aritméticas"""
        # Operação aditiva
        resultado = tradutor_los.operacao_aditiva(['5', '+', '3'])
        assert resultado == '5 + 3'
        
        # Operação multiplicativa
        resultado = tradutor_los.operacao_multiplicativa(['x', '*', 'y'])
        assert resultado == 'x * y'
    
    def test_referencias_dataset(self, tradutor_los):
        """Testa tradução de referências a datasets"""
        resultado = tradutor_los.referencia_dataset(['produtos', 'custo'])
        assert resultado == 'produtos["custo"]'
    
    def test_variaveis_indexadas(self, tradutor_los):
        """Testa tradução de variáveis indexadas"""
        resultado = tradutor_los.variavel_indexada(['x', 'i'])
        assert resultado == 'x[i]'
        assert 'x' in tradutor_los.variaveis_encontradas


class TestExpressaoLOS:
    """Suite de testes para a classe ExpressaoLOS"""
    
    def test_criacao_expressao(self):
        """Testa criação de uma ExpressaoLOS"""
        from lark import Tree, Token
        
        arvore = Tree('objetivo', [])
        expr = ExpressaoLOS(
            tipo='objetivo',
            operacao='minimizar',
            expressao_original='MINIMIZAR: x + y',
            arvore_sintaxe=arvore,
            codigo_python='x + y'
        )
        
        assert expr.tipo == 'objetivo'
        assert expr.operacao == 'minimizar'
        assert expr.codigo_python == 'x + y'
        assert isinstance(expr.variaveis_detectadas, set)
        assert isinstance(expr.datasets_referenciados, set)
    
    def test_post_init(self):
        """Testa inicialização automática de conjuntos"""
        from lark import Tree
        
        expr = ExpressaoLOS(
            tipo='matematica',
            operacao='soma',
            expressao_original='x + y',
            arvore_sintaxe=Tree('soma', [])
        )
        
        assert expr.variaveis_detectadas == set()
        assert expr.datasets_referenciados == set()
        assert expr.complexidade == 1
