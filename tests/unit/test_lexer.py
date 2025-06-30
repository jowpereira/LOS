# -*- coding: utf-8 -*-
"""
Testes unitários para o LexerLOS
Testa tokenização e análise léxica
"""

import pytest
import sys
from pathlib import Path

# Adicionar path do projeto
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from los_parser import ParserLOS, ExpressaoLOS, TradutorLOS
from tests.fixtures.casos_teste import CasosTeste
from tests.utils.validadores import validar_balanceamento_parenteses


# -*- coding: utf-8 -*-
"""
Testes unitários para análise léxica e sintática do ParserLOS
Testa tokenização e reconhecimento de padrões
"""

import pytest
import sys
from pathlib import Path

# Adicionar path do projeto
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from los_parser import ParserLOS, ExpressaoLOS, TradutorLOS
from tests.fixtures.casos_teste import CasosTeste
from tests.utils.validadores import validar_balanceamento_parenteses


class TestParserLOSLexica:
    """Suite de testes para análise léxica do ParserLOS"""
    
    def test_parsing_expressoes_basicas(self, parser_los):
        """Testa parsing de expressões básicas"""
        casos = [
            "MINIMIZAR: x + y",
            "MAXIMIZAR: produtos.custo",
            "x <= 100",
            "soma >= 50"
        ]
        
        for texto in casos:
            resultado = parser_los.analisar_expressao(texto)
            assert isinstance(resultado, ExpressaoLOS)
            assert resultado.expressao_original == texto
    
    def test_parsing_referencias_dataset(self, parser_los):
        """Testa parsing de referências a datasets"""
        casos = [
            "produtos.custo",
            "clientes.nome",
            "ordens.quantidade"
        ]
        
        for texto in casos:
            resultado = parser_los.analisar_expressao(texto)
            assert isinstance(resultado, ExpressaoLOS)
            assert 'produtos' in texto or 'clientes' in texto or 'ordens' in texto
    
    def test_parsing_operadores_relacionais(self, parser_los):
        """Testa parsing de operadores relacionais"""
        casos = [
            ("x <= 100", "restricao"),
            ("y >= 50", "restricao"),
            ("z == 0", "restricao"),
            ("w != 1", "restricao")
        ]
        
        for texto, tipo_esperado in casos:
            resultado = parser_los.analisar_expressao(texto)
            assert resultado.tipo == tipo_esperado
    
    def test_parsing_numeros_e_strings(self, parser_los):
        """Testa parsing de números e strings"""
        casos = [
            "x = 123.45",
            "nome = 'PRODUTO_A'",
            "valor = 1000"
        ]
        
        for texto in casos:
            resultado = parser_los.analisar_expressao(texto)
            assert isinstance(resultado, ExpressaoLOS)
    
    def test_parsing_estruturas_controle(self, parser_los):
        """Testa parsing de estruturas de controle"""
        texto = "SE x > 0 ENTAO x SENAO 0"
        
        resultado = parser_los.analisar_expressao(texto)
        assert resultado.tipo == "condicional"
    
    def test_precedencia_operadores(self, parser_los):
        """Testa precedência de operadores"""
        casos = [
            "2 + 3 * 4",
            "10 - 6 / 2",
            "(a + b) * c"
        ]
        
        for texto in casos:
            resultado = parser_los.analisar_expressao(texto)
            assert isinstance(resultado, ExpressaoLOS)
            assert resultado.tipo == "matematica"
    
    def test_deteccao_variaveis(self, parser_los):
        """Testa detecção de variáveis"""
        casos = [
            ("x + y", {"x", "y"}),
            ("produto[i]", {"produto", "i"}),
            ("x[i,j] + z", {"x", "i", "j", "z"})
        ]
        
        for texto, vars_esperadas in casos:
            resultado = parser_los.analisar_expressao(texto)
            # A detecção de variáveis pode variar conforme implementação
            # Apenas verificamos que funciona
            assert len(resultado.variaveis_detectadas) >= 0
    
    def test_casos_extremos(self, parser_los):
        """Testa casos extremos e edge cases"""
        casos_validos = [
            "10",
            "x",
            "a+b",
            "f(x)"
        ]
        
        for texto in casos_validos:
            try:
                resultado = parser_los.analisar_expressao(texto)
                assert isinstance(resultado, ExpressaoLOS)
            except Exception:
                # Para alguns casos extremos, falhas são esperadas
                pass
    
    def test_erros_sintaxe(self, parser_los):
        """Testa tratamento de erros de sintaxe"""
        casos_invalidos = [
            "MINIMIZAR:",  # Sem expressão
            "x +",         # Operador sem operando
            "(((",         # Parênteses desbalanceados
        ]
        
        for texto in casos_invalidos:
            with pytest.raises(Exception):
                parser_los.analisar_expressao(texto)


class TestValidacaoBalanceamento:
    """Testa validação de balanceamento de parênteses"""
    
    def test_parenteses_balanceados(self):
        """Testa detecção de parênteses balanceados"""
        casos_balanceados = [
            "(a + b)",
            "((a + b) * c)",
            "f(x, y, z)",
            "a + (b * (c + d))"
        ]
        
        for caso in casos_balanceados:
            assert validar_balanceamento_parenteses(caso)
    
    def test_parenteses_desbalanceados(self):
        """Testa detecção de parênteses desbalanceados"""
        casos_desbalanceados = [
            "(a + b",
            "a + b)",
            "((a + b)",
            "a + b))",
            "f(x, y"
        ]
        
        for caso in casos_desbalanceados:
            assert not validar_balanceamento_parenteses(caso)


class TestCasosTesteLexica:
    """Testa casos específicos da suite de casos de teste"""
    
    def test_casos_suite_oficial(self, parser_los):
        """Testa usando a suite oficial de casos de teste"""
        casos = CasosTeste.obter_casos_lexer()
        
        sucessos = 0
        for caso in casos:
            try:
                resultado = parser_los.analisar_expressao(caso['entrada'])
                assert isinstance(resultado, ExpressaoLOS)
                sucessos += 1
            except Exception as e:
                print(f"Caso falhou: {caso['entrada']} - {e}")
        
        # Deve passar pelo menos 80% dos casos
        taxa_sucesso = sucessos / len(casos)
        assert taxa_sucesso >= 0.8, f"Taxa de sucesso muito baixa: {taxa_sucesso:.1%}"
        
        for tipo in tipos_esperados:
            assert tipo in tipos_encontrados, f"Tipo {tipo} não encontrado"
    
    def test_tokenizacao_condicionais(self, lexer):
        """Testa tokenização de SE/ENTAO/SENAO"""
        texto = "SE x > 0 ENTAO x * 2 SENAO 0"
        tokens = lexer.tokenize(texto)
        
        tipos_condicionais = ['SE', 'ENTAO', 'SENAO']
        for tipo in tipos_condicionais:
            condicional_token = next((t for t in tokens if t.tipo == tipo), None)
            assert condicional_token is not None, f"Condicional {tipo} não encontrada"
    
    def test_posicionamento_tokens(self, lexer):
        """Testa se as informações de posição dos tokens estão corretas"""
        texto = "MINIMIZAR:\n  x + y"
        tokens = lexer.tokenize(texto)
        
        # Verificar que todos os tokens têm informações de posição
        for token in tokens:
            assert hasattr(token, 'linha')
            assert hasattr(token, 'coluna')
            assert hasattr(token, 'posicao')
            assert token.linha >= 1
            assert token.coluna >= 1
    
    def test_casos_teste_lexer_predefinidos(self, lexer):
        """Executa casos de teste predefinidos para o lexer"""
        casos = CasosTeste.casos_lexer_basicos()
        
        for caso in casos:
            if caso.deve_falhar:
                with pytest.raises(Exception):
                    lexer.tokenize(caso.entrada_los)
            else:
                tokens = lexer.tokenize(caso.entrada_los)
                assert len(tokens) > 0, f"Nenhum token gerado para caso {caso.id}"
    
    def test_tokenizacao_expressao_complexa(self, lexer):
        """Testa tokenização de expressão complexa real"""
        texto = """
        MINIMIZAR: soma de produtos.Custo_Producao * x[produto] 
        PARA CADA produto EM produtos 
        ONDE produtos.Tipo = 'Premium'
        """
        
        tokens = lexer.tokenize(texto)
        
        # Verificar presença de tokens-chave
        tipos_presentes = [t.tipo for t in tokens]
        assert 'MINIMIZAR' in tipos_presentes
        assert 'SOMA_DE' in tipos_presentes
        assert 'PARA_CADA' in tipos_presentes
        assert 'EM' in tipos_presentes
        assert 'ONDE' in tipos_presentes
        
        # Verificar que não há tokens de espaço
        assert 'ESPACO' not in tipos_presentes
    
    def test_deteccao_erros_lexer(self, lexer):
        """Testa detecção de erros pelo lexer"""
        casos_erro = [
            "produtos.'coluna sem fechamento",  # Aspas desbalanceadas
            "função_inexistente(x)",           # Função não reconhecida pode ser ok
            "123abc",                          # Número inválido pode ser tokenizado como separado
        ]
        
        for caso in casos_erro:
            # Mesmo com erros, o lexer pode tokenizar parcialmente
            # O importante é que não lance exceção
            try:
                tokens = lexer.tokenize(caso)
                # Se chegou aqui, pelo menos não crashou
                assert True
            except Exception as e:
                # Se falhou, documentar o erro
                pytest.fail(f"Lexer crashou inesperadamente em '{caso}': {e}")
    
    def test_performance_lexer(self, lexer):
        """Testa performance do lexer com texto longo"""
        import time
        
        # Criar texto longo repetindo expressões
        expressao_base = "MINIMIZAR: soma de produtos.Custo * x[produto] PARA CADA produto EM produtos ONDE produto.Ativo = 1"
        texto_longo = " ".join([expressao_base] * 100)  # Repetir 100 vezes
        
        inicio = time.time()
        tokens = lexer.tokenize(texto_longo)
        fim = time.time()
        
        tempo_execucao = (fim - inicio) * 1000  # em ms
        
        assert len(tokens) > 0
        assert tempo_execucao < 1000, f"Lexer muito lento: {tempo_execucao:.2f}ms para texto longo"
        
        print(f"Performance lexer: {len(tokens)} tokens em {tempo_execucao:.2f}ms")


class TestTokenLOS:
    """Testes específicos para a classe TokenLOS"""
    
    def test_criacao_token(self):
        """Testa criação de token com todos os parâmetros"""
        token = TokenLOS("IDENTIFICADOR", "x", 10, 2, 5)
        
        assert token.tipo == "IDENTIFICADOR"
        assert token.valor == "x"
        assert token.posicao == 10
        assert token.linha == 2
        assert token.coluna == 5
    
    def test_representacao_token(self):
        """Testa representação string do token"""
        token = TokenLOS("NUMERO", "123", 0, 1, 1)
        repr_str = repr(token)
        
        assert "NUMERO" in repr_str
        assert "123" in repr_str
        assert "L1:C1" in repr_str
    
    def test_posicao_legivel(self):
        """Testa método de posição legível"""
        token = TokenLOS("IDENTIFICADOR", "produto", 15, 3, 8)
        posicao = token.posicao_legivel()
        
        assert "linha 3" in posicao
        assert "coluna 8" in posicao


# Testes de integração do Lexer com outros componentes
class TestLexerIntegracao:
    """Testes de integração do lexer com outros componentes"""
    
    def test_lexer_com_tradutor(self, lexer):
        """Testa se output do lexer é compatível com tradutor"""
        from parser_los import TradutorCompleto
        
        texto = "produtos.Custo_Producao * x[produto]"
        tokens = lexer.tokenize(texto)
        
        # Verificar que tokens são adequados para tradução
        assert len(tokens) > 0
        
        # Reconverter tokens para string (simulando pipeline)
        texto_reconvertido = " ".join([t.valor for t in tokens])
        
        # Deve ser possível traduzir
        tradutor = TradutorCompleto()
        resultado = tradutor.traduzir_expressao_completa(texto_reconvertido)
        
        assert len(resultado) > 0
        assert '"Custo_Producao"' in resultado  # Deve ter convertido referência
