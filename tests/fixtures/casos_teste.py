# -*- coding: utf-8 -*-
"""
Casos de teste predefinidos para o Parser LOS
Organiza cenários de teste por categoria
"""

from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class CasoTeste:
    """Representa um caso de teste completo"""
    id: str
    categoria: str
    entrada_los: str
    saida_esperada: str
    descricao: str
    dados_necessarios: List[str] = None
    deve_falhar: bool = False
    observacoes: str = ""
    
    def __post_init__(self):
        if self.dados_necessarios is None:
            self.dados_necessarios = []


class CasosTeste:
    """Repositório centralizado de casos de teste"""
    
    @staticmethod
    def casos_lexer_basicos() -> List[CasoTeste]:
        """Casos básicos para testar o LexerLOS"""
        return [
            CasoTeste(
                id="LEX_001",
                categoria="tokenizacao_basica",
                entrada_los="MINIMIZAR x + y",
                saida_esperada="[MINIMIZAR, IDENTIFICADOR(x), ADICAO(+), IDENTIFICADOR(y)]",
                descricao="Tokenização de expressão matemática simples"
            ),
            CasoTeste(
                id="LEX_002", 
                categoria="tokenizacao_basica",
                entrada_los="produtos.Custo_Producao",
                saida_esperada="[IDENTIFICADOR(produtos), PONTO(.), IDENTIFICADOR(Custo_Producao)]",
                descricao="Tokenização de referência a dataset"
            ),
            CasoTeste(
                id="LEX_003",
                categoria="tokenizacao_avancada",
                entrada_los="produtos.'Nome do Produto'",
                saida_esperada="[IDENTIFICADOR(produtos), PONTO(.), COLUNA_COM_ESPACO('Nome do Produto')]",
                descricao="Tokenização de coluna com espaços"
            ),
            CasoTeste(
                id="LEX_004",
                categoria="operadores",
                entrada_los="x <= 100",
                saida_esperada="[IDENTIFICADOR(x), OPERADOR_REL(<=), NUMERO(100)]",
                descricao="Tokenização de operador relacional composto"
            ),
            CasoTeste(
                id="LEX_005",
                categoria="funcoes",
                entrada_los="soma de (x[i])",
                saida_esperada="[SOMA_DE, ABRE_PAREN, IDENTIFICADOR(x), ABRE_COLCH, IDENTIFICADOR(i), FECHA_COLCH, FECHA_PAREN]",
                descricao="Tokenização de função agregada com variável indexada"
            )
        ]
    
    @staticmethod
    def casos_tradutor_expressoes() -> List[CasoTeste]:
        """Casos para testar tradução de expressões"""
        return [
            CasoTeste(
                id="TRAD_001",
                categoria="matematica_basica",
                entrada_los="x + y * 2",
                saida_esperada="x + y * 2",
                descricao="Tradução de expressão aritmética simples"
            ),
            CasoTeste(
                id="TRAD_002",
                categoria="referencias_dados",
                entrada_los="produtos.Custo_Producao",
                saida_esperada='produtos["Custo_Producao"]',
                descricao="Tradução de referência a dataset"
            ),
            CasoTeste(
                id="TRAD_003",
                categoria="agregacoes",
                entrada_los="soma de x[i]",
                saida_esperada="sum([x[i]])",
                descricao="Tradução de agregação simples"
            ),
            CasoTeste(
                id="TRAD_004",
                categoria="loops",
                entrada_los="x[produto] PARA CADA produto EM produtos",
                saida_esperada="x[produto] for produto in produtos",
                descricao="Tradução de loop simples"
            ),
            CasoTeste(
                id="TRAD_005",
                categoria="condicionais",
                entrada_los="SE x > 0 ENTAO x * 2 SENAO 0",
                saida_esperada="x * 2 if x > 0 else 0",
                descricao="Tradução de condicional SE/ENTAO/SENAO"
            )
        ]
    
    @staticmethod
    def casos_parser_objetivos() -> List[CasoTeste]:
        """Casos para testar análise de objetivos"""
        return [
            CasoTeste(
                id="OBJ_001",
                categoria="objetivo_simples",
                entrada_los="MINIMIZAR: x + y",
                saida_esperada="x + y",
                descricao="Objetivo de minimização simples",
                dados_necessarios=[]
            ),
            CasoTeste(
                id="OBJ_002",
                categoria="objetivo_com_dados",
                entrada_los="MINIMIZAR: produtos.Custo_Producao * x[produto]",
                saida_esperada='produtos["Custo_Producao"] * x[produto]',
                descricao="Objetivo com referência a dados",
                dados_necessarios=["produtos"]
            ),
            CasoTeste(
                id="OBJ_003",
                categoria="objetivo_agregado",
                entrada_los="MINIMIZAR: soma de produtos.Custo_Producao * x[produto] PARA CADA produto EM produtos",
                saida_esperada='sum([produtos["Custo_Producao"] * x[produto] for produto in produtos])',
                descricao="Objetivo com agregação e loop",
                dados_necessarios=["produtos"]
            ),
            CasoTeste(
                id="OBJ_004",
                categoria="objetivo_condicional",
                entrada_los="MAXIMIZAR: soma de produtos.Margem_Lucro * x[produto] PARA CADA produto EM produtos ONDE produtos.Custo_Producao < 30",
                saida_esperada='sum([produtos["Margem_Lucro"] * x[produto] for produto in produtos if produtos["Custo_Producao"] < 30])',
                descricao="Objetivo com condição ONDE",
                dados_necessarios=["produtos"]
            )
        ]
    
    @staticmethod
    def casos_parser_restricoes() -> List[CasoTeste]:
        """Casos para testar análise de restrições"""
        return [
            CasoTeste(
                id="REST_001",
                categoria="restricao_simples",
                entrada_los="x + y <= 100",
                saida_esperada="x + y <= 100",
                descricao="Restrição de desigualdade simples"
            ),
            CasoTeste(
                id="REST_002",
                categoria="restricao_agregada",
                entrada_los="soma de x[produto] PARA CADA produto EM produtos <= 1000",
                saida_esperada="sum([x[produto] for produto in produtos]) <= 1000",
                descricao="Restrição com agregação",
                dados_necessarios=["produtos"]
            ),
            CasoTeste(
                id="REST_003",
                categoria="restricao_condicional",
                entrada_los="soma de ordens.Quantidade PARA CADA ordem EM ordens ONDE ordens.Produto = 'PROD_A' <= estoque.Quantidade_Disponivel",
                saida_esperada='sum([ordens["Quantidade"] for ordem in ordens if ordens["Produto"] == \'PROD_A\']) <= estoque["Quantidade_Disponivel"]',
                descricao="Restrição de balanceamento de estoque",
                dados_necessarios=["ordens", "estoque"]
            ),
            CasoTeste(
                id="REST_004",
                categoria="restricao_igualdade",
                entrada_los="x[cliente] = 1 ONDE clientes.Tipo_Cliente = 'Premium'",
                saida_esperada='x[cliente] == 1 where clientes["Tipo_Cliente"] == \'Premium\'',
                descricao="Restrição de igualdade com condição",
                dados_necessarios=["clientes"]
            )
        ]
    
    @staticmethod
    def casos_integracao_complexos() -> List[CasoTeste]:
        """Casos complexos de integração entre componentes"""
        return [
            CasoTeste(
                id="INT_001",
                categoria="otimizacao_producao",
                entrada_los="MINIMIZAR: soma de produtos.Custo_Producao * x[produto] + custos.Valor_Custo * atraso[cliente] PARA CADA produto EM produtos PARA CADA cliente EM clientes",
                saida_esperada='sum([produtos["Custo_Producao"] * x[produto] + custos["Valor_Custo"] * atraso[cliente] for produto in produtos for cliente in clientes])',
                descricao="Otimização de produção com custos de atraso",
                dados_necessarios=["produtos", "custos", "clientes"]
            ),
            CasoTeste(
                id="INT_002",
                categoria="balanceamento_multiobjetivo",
                entrada_los="MAXIMIZAR: soma de produtos.Margem_Lucro * vendas[produto,cliente] - custos.Valor_Custo * penalidade[cliente] PARA CADA produto EM produtos PARA CADA cliente EM clientes ONDE clientes.Tipo_Cliente = custos.Tipo_Cliente",
                saida_esperada='sum([produtos["Margem_Lucro"] * vendas[produto,cliente] - custos["Valor_Custo"] * penalidade[cliente] for produto in produtos for cliente in clientes if clientes["Tipo_Cliente"] == custos["Tipo_Cliente"]])',
                descricao="Otimização multiobjetivo com joins entre datasets",
                dados_necessarios=["produtos", "clientes", "custos"]
            ),
            CasoTeste(
                id="INT_003",
                categoria="restricao_capacidade",
                entrada_los="soma de ordens.Quantidade * x[ordem] PARA CADA ordem EM ordens ONDE ordens.Planta = planta <= estoque.Quantidade_Disponivel ONDE estoque.Planta = planta",
                saida_esperada='sum([ordens["Quantidade"] * x[ordem] for ordem in ordens if ordens["Planta"] == planta]) <= estoque["Quantidade_Disponivel"] where estoque["Planta"] == planta',
                descricao="Restrição de capacidade por planta",
                dados_necessarios=["ordens", "estoque"]
            )
        ]
    
    @staticmethod
    def casos_extremos_e_edge_cases() -> List[CasoTeste]:
        """Casos extremos e edge cases"""
        return [
            CasoTeste(
                id="EDGE_001",
                categoria="aspas_desbalanceadas",
                entrada_los="produtos.'Nome sem fechamento",
                saida_esperada="",
                descricao="Teste com aspas desbalanceadas",
                deve_falhar=True
            ),
            CasoTeste(
                id="EDGE_002",
                categoria="parenteses_desbalanceados",
                entrada_los="soma de (x[i] + y[j]",
                saida_esperada="",
                descricao="Teste com parênteses desbalanceados",
                deve_falhar=True
            ),
            CasoTeste(
                id="EDGE_003",
                categoria="expressao_vazia",
                entrada_los="",
                saida_esperada="",
                descricao="Teste com entrada vazia",
                deve_falhar=True
            ),
            CasoTeste(
                id="EDGE_004",
                categoria="dataset_inexistente",
                entrada_los="dataset_inexistente.coluna",
                saida_esperada='dataset_inexistente["coluna"]',
                descricao="Referência a dataset não carregado",
                observacoes="Deve traduzir mas pode gerar warning"
            )
        ]
    
    @staticmethod
    def todos_os_casos() -> List[CasoTeste]:
        """Retorna todos os casos de teste organizados"""
        todos = []
        todos.extend(CasosTeste.casos_lexer_basicos())
        todos.extend(CasosTeste.casos_tradutor_expressoes())
        todos.extend(CasosTeste.casos_parser_objetivos())
        todos.extend(CasosTeste.casos_parser_restricoes())
        todos.extend(CasosTeste.casos_integracao_complexos())
        todos.extend(CasosTeste.casos_extremos_e_edge_cases())
        return todos
    
    @staticmethod
    def casos_por_categoria(categoria: str) -> List[CasoTeste]:
        """Filtra casos por categoria"""
        return [caso for caso in CasosTeste.todos_os_casos() if caso.categoria == categoria]
    
    @staticmethod
    def estatisticas() -> Dict[str, int]:
        """Retorna estatísticas dos casos de teste"""
        todos = CasosTeste.todos_os_casos()
        categorias = {}
        
        for caso in todos:
            if caso.categoria not in categorias:
                categorias[caso.categoria] = 0
            categorias[caso.categoria] += 1
        
        return {
            'total_casos': len(todos),
            'casos_que_devem_falhar': len([c for c in todos if c.deve_falhar]),
            'casos_por_categoria': categorias,
            'casos_com_dados': len([c for c in todos if c.dados_necessarios])
        }
