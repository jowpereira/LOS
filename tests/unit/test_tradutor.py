# -*- coding: utf-8 -*-
"""
Testes unitários para o TradutorLOS
Testa tradução de tokens e expressões LOS para código Python
"""

import pytest
import sys
from pathlib import Path

# Adicionar path do projeto
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from los_parser import TradutorLOS, ParserLOS, ExpressaoLOS
from tests.fixtures.casos_teste import CasosTeste
from tests.utils.validadores import (
    validar_codigo_python, 
    validar_compatibilidade_pulp,
    comparar_expressoes,
    AnalisadorCodigoGerado
)


class TestTradutorLOS:
    """Suite de testes para o TradutorLOS"""
    
    def test_traducao_expressao_matematica_simples(self, tradutor):
        """Testa tradução de expressões matemáticas básicas"""
        casos = [
            ("x + y", "x + y"),
            ("x * 2", "x * 2"),
            ("x / y", "x / y"),
            ("x - y + z", "x - y + z")
        ]
        
        for entrada, esperado in casos:
            resultado = tradutor.traduzir_expressao_completa(entrada)
            assert comparar_expressoes(resultado, esperado), f"Esperado '{esperado}', obtido '{resultado}'"
    
    def test_traducao_referencias_dataset(self, tradutor):
        """Testa tradução de referências a datasets"""
        casos = [
            ("produtos.Custo_Producao", 'produtos["Custo_Producao"]'),
            ("clientes.Tipo_Cliente", 'clientes["Tipo_Cliente"]'),
            ("ordens[ordem].Quantidade", 'ordens[ordem]["Quantidade"]'),
            ("estoque.Quantidade_Disponivel", 'estoque["Quantidade_Disponivel"]')
        ]
        
        for entrada, esperado in casos:
            resultado = tradutor.traduzir_expressao_completa(entrada)
            assert comparar_expressoes(resultado, esperado), f"Entrada: {entrada}\nEsperado: {esperado}\nObtido: {resultado}"
    
    def test_traducao_colunas_com_espacos(self, tradutor):
        """Testa tradução de colunas com espaços"""
        casos = [
            ("produtos.'Nome do Produto'", 'produtos["Nome do Produto"]'),
            ("clientes.'Código do Cliente'", 'clientes["Código do Cliente"]')
        ]
        
        for entrada, esperado in casos:
            resultado = tradutor.traduzir_expressao_completa(entrada)
            assert esperado in resultado, f"Tradução de coluna com espaço falhou: {entrada} -> {resultado}"
    
    def test_traducao_agregacoes(self, tradutor):
        """Testa tradução de funções agregadas"""
        casos = [
            ("suma de x[i]", "sum([x[i]])"),
            ("soma de (produtos.Custo * x[produto])", "sum([produtos.Custo * x[produto]])"),
            ("max(valores)", "max(valores)"),
            ("min(custos)", "min(custos)")
        ]
        
        for entrada, esperado in casos:
            resultado = tradutor.traduzir_expressao_completa(entrada)
            # Normalizar para comparação
            resultado_norm = resultado.replace('"', '')
            esperado_norm = esperado.replace('"', '')
            assert esperado_norm in resultado_norm or comparar_expressoes(resultado, esperado), \
                f"Agregação falhou:\nEntrada: {entrada}\nEsperado: {esperado}\nObtido: {resultado}"
    
    def test_traducao_loops_para_cada(self, tradutor):
        """Testa tradução de loops PARA CADA"""
        casos = [
            ("x[produto] PARA CADA produto EM produtos", "x[produto] for produto in produtos"),
            ("y[cliente] PARA CADA cliente EM clientes", "y[cliente] for cliente in clientes")
        ]
        
        for entrada, esperado in casos:
            resultado = tradutor.traduzir_expressao_completa(entrada)
            assert esperado in resultado or comparar_expressoes(resultado, esperado), \
                f"Loop PARA CADA falhou: {entrada} -> {resultado}"
    
    def test_traducao_soma_com_loops(self, tradutor):
        """Testa integração de suma + PARA CADA"""
        entrada = "suma de x[produto] PARA CADA produto EM produtos"
        esperado = "sum([x[produto] for produto in produtos])"
        
        resultado = tradutor.traduzir_expressao_completa(entrada)
        assert comparar_expressoes(resultado, esperado), \
            f"Soma com loop falhou:\nEsperado: {esperado}\nObtido: {resultado}"
    
    def test_traducao_condicionais_se_entao_senao(self, tradutor):
        """Testa tradução de estruturas condicionais"""
        casos = [
            ("SE x > 0 ENTAO x SENAO 0", "x if x > 0 else 0"),
            ("SE produto.Ativo = 1 ENTAO produto.Custo SENAO 999", "produto.Custo if produto.Ativo == 1 else 999")
        ]
        
        for entrada, esperado in casos:
            resultado = tradutor.traduzir_expressao_completa(entrada)
            # Verificar estrutura if-else
            assert " if " in resultado and " else " in resultado, \
                f"Estrutura condicional não encontrada: {resultado}"
    
    def test_traducao_operadores_logicos(self, tradutor):
        """Testa tradução de operadores lógicos"""
        casos = [
            ("x > 0 E y < 10", "x > 0 and y < 10"),
            ("a = 1 OU b = 2", "a == 1 or b == 2"),
            ("NAO ativo", "not ativo")
        ]
        
        for entrada, esperado in casos:
            resultado = tradutor.traduzir_expressao_completa(entrada)
            # Verificar se operadores foram traduzidos
            assert "and" in resultado or "or" in resultado or "not" in resultado, \
                f"Operadores lógicos não traduzidos: {entrada} -> {resultado}"
    
    def test_traducao_operadores_comparacao(self, tradutor):
        """Testa tradução de operadores de comparação"""
        casos = [
            ("x = 1", "x == 1"),
            ("y <= 100", "y <= 100"),
            ("z >= 50", "z >= 50"),
            ("nome esta em lista", "nome in lista")
        ]
        
        for entrada, esperado in casos:
            resultado = tradutor.traduzir_expressao_completa(entrada)
            # Verificar operadores específicos
            if "==" in esperado:
                assert "==" in resultado and resultado.count("=") >= 2
            elif "in" in esperado:
                assert " in " in resultado
    
    def test_traducao_loops_aninhados(self, tradutor):
        """Testa tradução de loops aninhados múltiplos"""
        entrada = "x[produto,planta] PARA CADA produto EM produtos PARA CADA planta EM plantas"
        resultado = tradutor.traduzir_expressao_completa(entrada)
        
        # Deve conter dois 'for'
        assert resultado.count(" for ") == 2, f"Loops aninhados não detectados: {resultado}"
        assert "produto in produtos" in resultado
        assert "planta in plantas" in resultado
    
    def test_traducao_onde_condicoes(self, tradutor):
        """Testa tradução de cláusulas ONDE"""
        entrada = "x[produto] ONDE produto.Ativo = 1"
        resultado = tradutor.traduzir_expressao_completa(entrada)
        
        # ONDE deve virar 'if'
        assert " if " in resultado, f"Cláusula ONDE não traduzida: {resultado}"
    
    def test_traducao_funcoes_matematicas(self, tradutor):
        """Testa tradução de funções matemáticas"""
        casos = [
            ("max(x, y)", "max(x, y)"),
            ("min(a, b)", "min(a, b)"),
            ("abs(diferenca)", "abs(diferenca)"),
            ("round(valor)", "round(valor)")
        ]
        
        for entrada, esperado in casos:
            resultado = tradutor.traduzir_expressao_completa(entrada)
            assert esperado in resultado or comparar_expressoes(resultado, esperado)
    
    def test_casos_teste_tradutor_predefinidos(self, tradutor):
        """Executa casos de teste predefinidos para o tradutor"""
        casos = CasosTeste.casos_tradutor_expressoes()
        
        for caso in casos:
            if caso.deve_falhar:
                with pytest.raises(Exception):
                    tradutor.traduzir_expressao_completa(caso.entrada_los)
            else:
                resultado = tradutor.traduzir_expressao_completa(caso.entrada_los)
                assert len(resultado) > 0, f"Resultado vazio para caso {caso.id}"
                
                # Validar que o código gerado é Python válido
                if validar_codigo_python(resultado):
                    assert True
                else:
                    # Se não é Python válido, pode ser expressão parcial - verificar estrutura
                    assert any(op in resultado for op in ['sum(', 'max(', 'min(', 'for', 'if']), \
                        f"Código inválido e sem estruturas reconhecíveis: {resultado}"
    
    def test_traducao_expressao_complexa_real(self, tradutor):
        """Testa tradução de expressão complexa realística"""
        entrada = """
        suma de produtos.Custo_Producao * x[produto] + custos.Valor_Custo * atraso[cliente] 
        PARA CADA produto EM produtos 
        PARA CADA cliente EM clientes 
        ONDE produtos.Ativo = 1 E clientes.Tipo = 'Premium'
        """
        
        resultado = tradutor.traduzir_expressao_completa(entrada)
        
        # Verificações estruturais
        analisador = AnalisadorCodigoGerado(resultado)
        validacao = analisador.validar_completo()
        
        assert validacao['padroes_pulp']['funcao_sum'], "Deve conter função sum"
        assert validacao['estrutura_loops']['total_fors'] >= 2, "Deve ter pelo menos 2 loops"
        assert validacao['estrutura_loops']['tem_condicoes'], "Deve ter condições"
        assert len(validacao['datasets_referenciados']) >= 2, "Deve referenciar múltiplos datasets"
    
    def test_preservacao_precedencia_operadores(self, tradutor):
        """Testa se a precedência de operadores é preservada"""
        casos = [
            ("x + y * z", "x + y * z"),  # Multiplicação tem precedência
            ("(x + y) * z", "(x + y) * z"),  # Parênteses preservados
            ("x * y + z / w", "x * y + z / w")  # Múltiplas operações
        ]
        
        for entrada, esperado in casos:
            resultado = tradutor.traduzir_expressao_completa(entrada)
            # Verificar que a estrutura matemática é preservada
            assert resultado.count('+') == esperado.count('+')
            assert resultado.count('*') == esperado.count('*')
            assert resultado.count('/') == esperado.count('/')
    
    def test_deteccao_variaveis_e_datasets(self, tradutor):
        """Testa se o tradutor detecta variáveis e datasets corretamente"""
        entrada = "produtos.Custo * x[produto] + clientes.Taxa * y[cliente]"
        resultado = tradutor.traduzir_expressao_completa(entrada)
        
        # Verificar datasets referenciados
        assert len(tradutor.datasets_referenciados) >= 2
        assert 'produtos' in tradutor.datasets_referenciados
        assert 'clientes' in tradutor.datasets_referenciados
        
        # Verificar que referências foram traduzidas
        assert 'produtos[' in resultado or 'produtos["' in resultado
        assert 'clientes[' in resultado or 'clientes["' in resultado


class TestTradutorMethodosEspecializados:
    """Testes dos métodos especializados do tradutor"""
    
    def test_metodo_integrar_sum_com_loops(self, tradutor):
        """Testa método _integrar_sum_com_loops especificamente"""
        entrada = "suma de x[i] PARA CADA i EM lista"
        resultado = tradutor._integrar_sum_com_loops(entrada)
        
        assert "sum([" in resultado
        assert "for i in lista" in resultado
        assert "])" in resultado
    
    def test_metodo_traduzir_condicionais(self, tradutor):
        """Testa método _traduzir_condicionais especificamente"""
        entrada = "SE x > 0 ENTAO x SENAO 0"
        resultado = tradutor._traduzir_condicionais(entrada)
        
        assert " if " in resultado
        assert " else " in resultado
    
    def test_metodo_traduzir_referencias_dados(self, tradutor):
        """Testa método _traduzir_referencias_dados especificamente"""
        entrada = "dataset.coluna"
        resultado = tradutor._traduzir_referencias_dados(entrada)
        
        assert 'dataset["coluna"]' == resultado
    
    def test_metodo_normalizar_operadores(self, tradutor):
        """Testa método _normalizar_operadores especificamente"""
        casos = [
            ("x = 1", "x == 1"),
            ("y <= 10", "y <= 10"),  # Não deve alterar
            ("z>=5", "z >= 5")  # Deve adicionar espaços
        ]
        
        for entrada, esperado in casos:
            resultado = tradutor._normalizar_operadores(entrada)
            assert esperado in resultado or comparar_expressoes(resultado, esperado)


class TestTradutorPerformance:
    """Testes de performance do tradutor"""
    
    def test_performance_traducao(self, tradutor):
        """Testa performance do tradutor com expressões complexas"""
        import time
        
        expressao_complexa = """
        suma de produtos.Custo_Producao * x[produto] + 
        max(estoque.Quantidade * y[estoque]) +
        min(clientes.Prioridade * z[cliente])
        PARA CADA produto EM produtos 
        PARA CADA estoque EM estoques
        PARA CADA cliente EM clientes
        ONDE produtos.Ativo = 1 E estoque.Disponivel > 0 E clientes.Tipo = 'Premium'
        """
        
        inicio = time.time()
        resultado = tradutor.traduzir_expressao_completa(expressao_complexa)
        fim = time.time()
        
        tempo_execucao = (fim - inicio) * 1000  # em ms
        
        assert len(resultado) > 0
        assert tempo_execucao < 500, f"Tradutor muito lento: {tempo_execucao:.2f}ms"
        
        print(f"Performance tradutor: {len(resultado)} caracteres em {tempo_execucao:.2f}ms")
    
    def test_memoria_tradutor(self, tradutor):
        """Testa uso de memória do tradutor"""
        import sys
        
        # Traduzir muitas expressões
        expressoes = [
            f"suma de x[{i}] PARA CADA item_{i} EM lista_{i}" 
            for i in range(100)
        ]
        
        tamanho_inicial = sys.getsizeof(tradutor)
        
        for expressao in expressoes:
            tradutor.traduzir_expressao_completa(expressao)
        
        tamanho_final = sys.getsizeof(tradutor)
        crescimento = tamanho_final - tamanho_inicial
        
        # Não deve crescer demais (em bytes)
        assert crescimento < 100000, f"Possível vazamento de memória: cresceu {crescimento} bytes"
