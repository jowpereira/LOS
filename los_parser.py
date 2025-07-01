# -*- coding: utf-8 -*-
"""
🚀 LOS - Linguagem de Otimização Simples
Parser inteligente baseado em Lark para expressões de otimização matemática
Suporta expressões complexas, precedência correta e aninhamento profundo
SEMPRE utiliza gramática externa los_grammar.lark
"""

import re
import pandas as pd
from typing import Dict, List, Any, Tuple, Optional, Union
from dataclasses import dataclass
import logging
from pathlib import Path
import os

from lark import Lark, Transformer, Tree, Token
from lark.exceptions import LarkError, ParseError, LexError

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Caminho para a gramática externa
CAMINHO_GRAMATICA = Path(__file__).parent / "los_grammar.lark"

@dataclass
class ExpressaoLOS:
    """Representa uma expressão LOS analisada"""
    tipo: str  # 'objetivo', 'restricao', 'condicional', 'matematica'
    operacao: str  # 'minimizar', 'maximizar', 'menor_igual', etc.
    expressao_original: str
    arvore_sintaxe: Tree
    codigo_python: str = ""
    variaveis_detectadas: set = None
    datasets_referenciados: set = None
    complexidade: int = 1
    
    def __post_init__(self):
        if self.variaveis_detectadas is None:
            self.variaveis_detectadas = set()
        if self.datasets_referenciados is None:
            self.datasets_referenciados = set()


class TradutorLOS(Transformer):
    """Tradutor que converte árvore sintática Lark para código Python/PuLP"""
    
    def __init__(self):
        super().__init__()
        self.variaveis_encontradas = set()
        self.datasets_referenciados = set()
        self.nivel_complexidade = 1
    
    # === EXPRESSÕES PRINCIPAIS ===
    
    def objetivo_minimizar(self, items):
        """MINIMIZAR: expressão"""
        expressao = str(items[0]) if items else ""
        
        return {
            'tipo': 'objetivo',
            'operacao': 'minimizar',
            'expressao': expressao,
            'codigo': expressao
        }
    
    def objetivo_maximizar(self, items):
        """MAXIMIZAR: expressão"""
        expressao = str(items[0]) if items else ""
        
        return {
            'tipo': 'objetivo',
            'operacao': 'maximizar',
            'expressao': expressao,
            'codigo': expressao
        }
    
    def restricao(self, items):
        """expressão operador expressão"""
        if len(items) < 3:
            raise ValueError(f"Restrição malformada: {items}")
            
        esquerda = str(items[0])
        operador = str(items[1])  # Já vem processado pelo método operador_relacional
        direita = str(items[2])
        
        codigo = f"{esquerda} {operador} {direita}"
        return {
            'tipo': 'restricao',
            'operacao': self._operador_para_tipo(operador),
            'expressao': codigo,
            'codigo': codigo
        }
    
    def expressao_condicional(self, items):
        """SE condição ENTAO expr1 SENAO expr2"""
        if len(items) < 3:
            raise ValueError(f"Expressão condicional malformada: {items}")
        
        condicao = str(items[0])
        expr_entao = str(items[1])
        expr_senao = str(items[2])
        
        codigo = f"{expr_entao} if {condicao} else {expr_senao}"
        return {
            'tipo': 'condicional',
            'operacao': 'se_entao_senao',
            'expressao': codigo,
            'codigo': codigo
        }
    
    # === OPERAÇÕES MATEMÁTICAS ===
    
    def operacao_logica(self, items):
        """Operações E, OU, and, or"""
        esquerda = items[0]
        operador = self._traduzir_operador_logico(str(items[1]))
        direita = items[2]
        return f"{esquerda} {operador} {direita}"
    
    def operacao_aditiva(self, items):
        """Operações + e -"""
        if len(items) < 3:
            # Se tiver apenas um item, retorna ele mesmo
            return str(items[0]) if items else ""
        
        # Processar operação com 3 elementos (esquerda, operador, direita)
        esquerda = str(items[0])
        operador = str(items[1])
        direita = str(items[2])
        
        # Para operações aninhadas, verificar se precisamos adicionar parênteses
        if ' + ' in direita or ' - ' in direita:
            # Operações aninhadas à direita podem precisar de parênteses
            if operador == '-':
                direita = f"({direita})"
        
        # Registrar variáveis se forem identificadores
        for item in [esquerda, direita]:
            if item.isalpha():
                self.variaveis_encontradas.add(item)
        
        return f"{esquerda} {operador} {direita}"
    
    def operacao_multiplicativa(self, items):
        """Operações *, /, //, %"""
        if len(items) < 3:
            # Se tiver apenas um item, retorna ele mesmo
            return str(items[0]) if items else ""
        
        # Processar operação com 3 elementos (esquerda, operador, direita)
        esquerda = str(items[0])
        operador = str(items[1])
        direita = str(items[2])
        
        # Registrar variáveis se forem identificadores
        for item in [esquerda, direita]:
            if item.isalpha():
                self.variaveis_encontradas.add(item)
        
        # Para operações aninhadas, verificar se precisamos adicionar parênteses
        if ' * ' in esquerda or ' / ' in esquerda:
            # Operações aninhadas à esquerda geralmente não precisam de parênteses
            # devido à associatividade da esquerda para a direita
            pass
        
        if ' * ' in direita or ' / ' in direita:
            # Operações aninhadas à direita podem precisar de parênteses
            if operador == '/':
                direita = f"({direita})"
        
        return f"{esquerda} {operador} {direita}"
    
    def potencia(self, items):
        """Operações ** e ^"""
        base = items[0]
        operador = "**" if str(items[1]) in ["**", "^"] else str(items[1])
        expoente = items[2]
        return f"{base} {operador} {expoente}"
    
    def operacao_unaria(self, items):
        """Operações unárias: +, -, NAO, not"""
        operador = self._traduzir_operador_unario(str(items[0]))
        operando = items[1]
        return f"{operador}{operando}" if operador in ["+", "-"] else f"{operador} {operando}"
    
    def comparacao(self, items):
        """Comparações relacionais"""
        if len(items) == 1:
            return items[0]
        esquerda = items[0]
        operador = self._traduzir_operador_relacional(str(items[1]))
        direita = items[2]
        return f"{esquerda} {operador} {direita}"
    
    # === OPERADORES LÓGICOS ===
    
    def operacao_ou(self, items):
        """Operador lógico OU"""
        if len(items) >= 2:
            return f"({items[0]} or {items[1]})"
        return str(items[0]) if items else ""
    
    def operacao_e(self, items):
        """Operador lógico E"""
        if len(items) >= 2:
            return f"({items[0]} and {items[1]})"
        return str(items[0]) if items else ""
    
    def operacao_nao(self, items):
        """Operador lógico NAO"""
        if items:
            return f"(not {items[0]})"
        return ""

    # === AGREGAÇÕES COMPLEXAS ===
    
    def agregacao_complexa(self, items):
        """soma de expr PARA CADA var EM dataset ONDE condição"""
        funcao = str(items[0]).lower()
        expressao = items[1]
        loop_info = items[2]
        condicao = items[3] if len(items) > 3 and items[3] is not None else None
        
        # Construir compreensão de lista
        if condicao:
            codigo = f"{self._mapear_funcao_agregada(funcao)}([{expressao} {loop_info} if {condicao}])"
        else:
            codigo = f"{self._mapear_funcao_agregada(funcao)}([{expressao} {loop_info}])"
        
        self.nivel_complexidade += 2
        return codigo
    
    def expressao_comparacao(self, items):
        """Expressão de comparação para uso em condicionais"""
        if len(items) < 3:
            raise ValueError(f"Comparação malformada: {items}")
            
        esquerda = str(items[0])
        operador_node = items[1]
        direita = str(items[2])
        
        # Processar o nó operador_relacional manualmente se necessário
        if hasattr(operador_node, 'children') and operador_node.children:
            operador = self.operador_relacional(operador_node.children)
        else:
            operador = str(operador_node)
        
        return f"{esquerda} {operador} {direita}"
    
    def agregacao(self, items):
        """soma de expressão [PARA CADA ...]"""
        if len(items) < 1:
            raise ValueError(f"Agregação malformada: {items}")
        
        # Após a mudança para "SOMA" "DE" na gramática, o primeiro item já é a expressão
        expressao = str(items[0])
        loop_info = str(items[1]) if len(items) > 1 else ""
        
        if loop_info:
            # Combinar expressão com loop
            return f"sum([{expressao} {loop_info}])"
        else:
            return f"sum({expressao})"
    
    def loop(self, items):
        """PARA CADA var EM dataset [ONDE condição]"""
        if len(items) < 2:
            raise ValueError(f"Loop malformado: {items}")
        
        # Extrair variável e dataset diretamente dos tokens, se possível
        variavel = items[0].value if hasattr(items[0], 'value') else str(items[0])
        dataset = items[1].value if hasattr(items[1], 'value') else str(items[1])
        condicao = str(items[2]) if len(items) > 2 else ""
        
        self.datasets_referenciados.add(dataset)
        
        loop_str = f"for {variavel} in {dataset}"
        if condicao:
            loop_str += f" if {condicao}"
        
        return loop_str
    
    def condicao_onde(self, items):
        """ONDE condição"""
        if len(items) < 1:
            return ""
        return str(items[0])
    
    def loop_multiplo(self, items):
        """Múltiplos loops aninhados: PARA CADA ... PARA CADA"""
        if not items:
            return ""
        
        # Construir loops aninhados
        loops = []
        for loop_item in items:
            loops.append(str(loop_item))
        
        # Concatenar todos os loops
        return " ".join(loops)
    
    # === OPERAÇÕES COM AGREGAÇÕES ===
    
    def operacao_aditiva_agregacao(self, items):
        """Operações + e - entre agregações"""
        if len(items) < 3:
            return str(items[0]) if items else ""
        
        esquerda = str(items[0])
        operador = str(items[1])
        direita = str(items[2])
        
        return f"({esquerda} {operador} {direita})"
    
    def operacao_multiplicativa_agregacao(self, items):
        """Operações * e / entre agregações"""
        if len(items) < 3:
            return str(items[0]) if items else ""
        
        esquerda = str(items[0])
        operador = str(items[1])
        direita = str(items[2])
        
        return f"({esquerda} {operador} {direita})"

    # === FUNÇÕES ===
    
    def funcao_matematica(self, items):
        """abs(x), max(a,b), etc."""
        if len(items) < 1:
            return ""
        
        nome_funcao = str(items[0])
        argumentos = str(items[1]) if len(items) > 1 else ""
        
        # Usar o método nome_funcao existente para mapear funções
        funcao_python = self.nome_funcao([nome_funcao])
        return f"{funcao_python}({argumentos})"
    
    def argumentos(self, items):
        """arg1, arg2, arg3 ou lista vazia"""
        if not items:
            return ""
        return ", ".join(str(item) for item in items)
    
    def variavel_indexada(self, items):
        """x[i], y[j]"""
        if len(items) < 2:
            return str(items[0]) if items else ""
        
        nome = str(items[0])
        
        # Processar a árvore de índices
        indices_tree = items[1]
        if hasattr(indices_tree, 'children'):
            # Extrair os tokens de índice da árvore
            indices_tokens = indices_tree.children
            indices = []
            for token in indices_tokens:
                if hasattr(token, 'value'):
                    indices.append(token.value)
                else:
                    indices.append(str(token))
            indice = ",".join(indices)
        else:
            indice = str(indices_tree)
        
        # Registrar a variável encontrada
        self.variaveis_encontradas.add(nome)
        
        return f"{nome}[{indice}]"
    
    def funcao_agregada(self, items):
        """sum(lista), max(valores)"""
        funcao = str(items[0]).lower()
        argumento = items[1]
        
        funcao_python = self._mapear_funcao_agregada(funcao)
        return f"{funcao_python}({argumento})"
    
    def lista_argumentos(self, items):
        """arg1, arg2, arg3"""
        return ", ".join(str(item) for item in items)
    
    # === VARIÁVEIS E REFERÊNCIAS ===
    
    def variavel(self, items):
        """x[produto], y[cliente,planta], z"""
        nome = str(items[0])
        self.variaveis_encontradas.add(nome)
        
        if len(items) > 1:
            indices = items[1]
            return f"{nome}[{indices}]"
        else:
            return nome
    
    def lista_indices(self, items):
        """produto, cliente,planta"""
        # Extrair apenas os valores dos tokens, não os tokens inteiros
        indices_valores = []
        for item in items:
            if hasattr(item, 'value'):
                indices_valores.append(item.value)
            else:
                indices_valores.append(str(item))
        
        return ",".join(indices_valores)
    
    def referencia_dataset(self, items):
        """produtos.Custo_Producao ou produtos.'Custo de Producao'"""
        dataset = str(items[0])
        coluna = str(items[1])
        
        self.datasets_referenciados.add(dataset)
        
        # Tratar diferentes formatos de coluna
        if coluna.startswith("'") and coluna.endswith("'"):
            # String com aspas simples: 'Custo de Producao'
            coluna_limpa = coluna[1:-1]
            return f'{dataset}["{coluna_limpa}"]'
        elif coluna.startswith('"') and coluna.endswith('"'):
            # String com aspas duplas: "Custo de Producao"
            coluna_limpa = coluna[1:-1]
            return f'{dataset}["{coluna_limpa}"]'
        else:
            # Identificador simples: Custo_Producao
            return f'{dataset}["{coluna}"]'
    
    def dataset_coluna(self, items):
        """Processa colunas de dataset (IDENTIFICADOR ou STRING)"""
        if not items:
            return ""
        
        valor = str(items[0])
        
        # Se for uma string com aspas, retornar apenas o conteúdo
        if (valor.startswith("'") and valor.endswith("'")) or (valor.startswith('"') and valor.endswith('"')):
            return valor[1:-1]
        
        # Se for identificador simples, retornar como está
        return valor

    # === EXPRESSÕES BOOLEANAS ===
    
    def booleano_logico(self, items):
        """Operações lógicas booleanas"""
        esquerda = items[0]
        operador = self._traduzir_operador_logico(str(items[1]))
        direita = items[2]
        return f"{esquerda} {operador} {direita}"
    
    def booleano_negacao(self, items):
        """NAO, not"""
        operador = "not"
        operando = items[1]
        return f"{operador} {operando}"
    
    def comparacao_booleana(self, items):
        """Comparações booleanas"""
        if len(items) == 1:
            return items[0]
        
        esquerda = items[0]
        operador = self._traduzir_operador_relacional(str(items[1]))
        direita = items[2]
        return f"{esquerda} {operador} {direita}"
    
    def operador_in(self, items):
        """esta em, in"""
        esquerda = items[0]
        direita = items[1]
        return f"{esquerda} in {direita}"
    
    def operador_not_in(self, items):
        """nao esta em, not in"""
        esquerda = items[0]
        direita = items[1]
        return f"{esquerda} not in {direita}"
    
    # === ELEMENTOS BÁSICOS ===
    
    def numero(self, items):
        """Números inteiros e decimais"""
        return str(items[0])
    
    def string(self, items):
        """Strings com aspas"""
        return str(items[0])
    
    def booleano(self, items):
        """Valores booleanos"""
        valor = str(items[0]).lower()
        if valor in ['verdadeiro', 'true']:
            return 'True'
        elif valor in ['falso', 'false']:
            return 'False'
        return valor
    
    # === NOVAS FUNCIONALIDADES DA GRAMÁTICA ULTRA-COMPLETA ===
    
    def programa(self, items):
        """Múltiplas declarações em um programa"""
        declaracoes = [str(item) for item in items if item is not None]
        return "\n".join(declaracoes)
    
    def declaracao_variavel(self, items):
        """VAR tipo nome = valor"""
        tipo = str(items[0])
        variaveis = items[1]
        valor = items[2] if len(items) > 2 and items[2] is not None else None
        
        codigo = f"# Declaração de variáveis {tipo}: {variaveis}"
        if valor:
            codigo += f" = {valor}"
        return codigo
    
    def tipo_variavel(self, items):
        """Tipos: CONTINUA, INTEIRA, BINARIA, etc."""
        tipo = str(items[0]).upper()
        mapeamento = {
            'CONTINUA': 'LpContinuous',
            'REAL': 'LpContinuous', 
            'INTEIRA': 'LpInteger',
            'INT': 'LpInteger',
            'BINARIA': 'LpBinary',
            'BIN': 'LpBinary',
            'SEMICONTINUA': 'LpSemiContinuous'
        }
        return mapeamento.get(tipo, 'LpContinuous')
    
    def lista_nomes_variaveis(self, items):
        """Lista de definições de variáveis"""
        nomes = [str(item) for item in items]
        return ", ".join(nomes)
    
    def definicao_variavel(self, items):
        """nome[dimensões] onde condição"""
        nome = str(items[0])
        self.variaveis_encontradas.add(nome)
        
        if len(items) > 1 and items[1] is not None:
            dimensoes = items[1]
            return f"{nome}[{dimensoes}]"
        return nome
    
    def dimensoes(self, items):
        """Dimensões de variáveis multidimensionais"""
        dims = [str(item) for item in items]
        return ", ".join(dims)
    
    def dimensao(self, items):
        """Uma dimensão individual"""
        return str(items[0])
    
    def range_valores(self, items):
        """Range de valores: 1..10, 1:10, 1 ate 10"""
        inicio = items[0]
        fim = items[1]
        return f"range({inicio}, {fim}+1)"
    
    def declaracao_dataset(self, items):
        """DATASET nome = arquivo"""
        nome = str(items[0])
        arquivo = items[1]
        self.datasets_referenciados.add(nome)
        return f"# Dataset {nome} = {arquivo}"
    
    def importacao_dataset(self, items):
        """IMPORTAR arquivo COMO nome"""
        arquivo = items[0]
        nome = str(items[1])
        self.datasets_referenciados.add(nome)
        return f"{nome} = pd.read_csv({arquivo})"
    
    def referencia_arquivo(self, items):
        """Referência a arquivo CSV/Excel"""
        return str(items[0])
    
    def condicional_simples(self, items):
        """SE condição ENTAO expr1 SENAO expr2"""
        condicao = items[0]
        entao = items[1]
        senao = items[2] if len(items) > 2 and items[2] is not None else "0"
        return f"({entao} if {condicao} else {senao})"
    
    def condicional_multipla(self, items):
        """ESCOLHER expr ENTRE casos FIM"""
        expr = items[0]
        casos = items[1]
        return f"# ESCOLHER {expr}: {casos}"
    
    def ramos_escolha(self, items):
        """Múltiplos ramos de escolha"""
        ramos = [str(item) for item in items]
        return " | ".join(ramos)
    
    def ramo_escolha(self, items):
        """CASO valor: resultado"""
        valor = items[0]
        resultado = items[1]
        return f"({resultado} if expr == {valor})"
    
    def condicional_aninhada(self, items):
        """SE...ENTAO...SENAO SE...FIM"""
        return "# Condicional aninhada complexa"
    
    def bloco_comandos(self, items):
        """Bloco de comandos"""
        comandos = [str(item) for item in items if item is not None]
        return "; ".join(comandos)
    
    def comando(self, items):
        """Um comando individual"""
        return str(items[0])
    
    def loop_para_cada(self, items):
        """PARA CADA var EM fonte ONDE condição FAÇA comandos FIM"""
        variavel = str(items[0])
        fonte = str(items[1])
        condicao = items[2] if len(items) > 2 and items[2] is not None else None
        comandos = items[3] if len(items) > 3 else None
        
        resultado = f"for {variavel} in {fonte}"
        if condicao:
            resultado += f" if {condicao}"
        return resultado
    
    def loop_para(self, items):
        """PARA var DE inicio ATE fim PASSO incremento"""
        variavel = str(items[0])
        inicio = items[1]
        fim = items[2]
        passo = items[3] if len(items) > 3 and items[3] is not None else "1"
        return f"for {variavel} in range({inicio}, {fim}+1, {passo})"
    
    def loop_enquanto(self, items):
        """ENQUANTO condição FAÇA comandos FIM"""
        condicao = items[0]
        comandos = items[1]
        return f"while {condicao}: {comandos}"
    
    def loop_aninhado(self, items):
        """Loops aninhados"""
        loops = [str(item) for item in items]
        return " ".join(loops)
    
    def fonte_iteracao(self, items):
        """Fonte para iteração"""
        return str(items[0])
    
    def operador_ternario(self, items):
        """condição ? verdadeiro : falso"""
        condicao = items[0]
        verdadeiro = items[1]
        falso = items[2]
        return f"({verdadeiro} if {condicao} else {falso})"
    
    def restricao_conjunto(self, items):
        """var EM conjunto ou var NAO EM conjunto"""
        variavel = items[0]
        operador = "in" if "EM" in str(items[1]) else "not in"
        conjunto = items[2]
        return f"{variavel} {operador} {conjunto}"
    
    def conjunto_valores(self, items):
        """[valor1, valor2, ...] ou {valor1, valor2, ...}"""
        valores = items[0]
        return f"[{valores}]"
    
    def lista_valores(self, items):
        """Lista de valores separados por vírgula"""
        valores = [str(item) for item in items]
        return ", ".join(valores)
    
    def restricao_condicional(self, items):
        """SE condição ENTAO restrição SENAO restrição"""
        condicao = items[0]
        entao = items[1]
        senao = items[2] if len(items) > 2 and items[2] is not None else None
        
        resultado = f"# SE {condicao} ENTAO {entao}"
        if senao:
            resultado += f" SENAO {senao}"
        return resultado
    
    def restricao_logica(self, items):
        """restrição E/OU restrição"""
        esquerda = items[0]
        operador = self._traduzir_operador_logico(str(items[1]))
        direita = items[2]
        return f"{esquerda} {operador} {direita}"
    
    def join_complexo(self, items):
        """dataset1 JOIN dataset2 ON condição"""
        dataset_principal = items[0]
        joins = items[1:]
        
        resultado = str(dataset_principal)
        for join in joins:
            resultado += f".merge({join})"
        return resultado
    
    def dataset_principal(self, items):
        """Dataset principal com alias opcional"""
        nome = str(items[0])
        alias = str(items[1]) if len(items) > 1 and items[1] is not None else None
        self.datasets_referenciados.add(nome)
        return f"{nome}" + (f" as {alias}" if alias else "")
    
    def join_clausula(self, items):
        """Cláusula de join"""
        tipo = str(items[0])
        dataset = str(items[1])
        alias = str(items[2]) if len(items) > 2 and items[2] is not None else None
        condicao = items[3] if len(items) > 3 else None
        
        self.datasets_referenciados.add(dataset)
        resultado = f"{dataset}"
        if alias:
            resultado += f" as {alias}"
        if condicao:
            resultado += f", on={condicao}"
        return resultado
    
    def tipo_join(self, items):
        """Tipo de join"""
        return str(items[0]).lower()
    
    def condicao_join(self, items):
        """Condição de join"""
        return str(items[0])
    
    def operador_in(self, items):
        """Operador IN"""
        esquerda = items[0]
        direita = items[1]
        return f"{esquerda} in {direita}"
    
    def operador_not_in(self, items):
        """Operador NOT IN"""
        esquerda = items[0]
        direita = items[1]
        return f"{esquerda} not in {direita}"
    
    def operador_like(self, items):
        """Operador LIKE"""
        esquerda = items[0]
        direita = items[1]
        return f"{esquerda}.str.contains({direita})"
    
    def operador_between(self, items):
        """Operador BETWEEN"""
        valor = items[0]
        minimo = items[1]
        maximo = items[2]
        return f"({valor} >= {minimo}) & ({valor} <= {maximo})"
    
    def operador_exists(self, items):
        """Operador EXISTS"""
        expressao = items[0]
        return f"any({expressao})"
    
    def booleano_logico(self, items):
        """Operadores lógicos E/OU"""
        esquerda = items[0]
        operador = self._traduzir_operador_logico(str(items[1]))
        direita = items[2]
        return f"({esquerda} {operador} {direita})"
    
    def booleano_negacao(self, items):
        """Operador NAO/NOT"""
        operando = items[1] if len(items) > 1 else items[0]
        return f"not ({operando})"
    
    def lista_expressoes(self, items):
        """Lista de expressões [expr1, expr2, ...]"""
        expressoes = [str(item) for item in items]
        return f"[{', '.join(expressoes)}]"
    
    def fonte_agregacao(self, items):
        """Fonte para agregação"""
        return str(items[0])
    
    def filtros(self, items):
        """Múltiplos filtros"""
        filtros_lista = [str(item) for item in items]
        return " & ".join(filtros_lista)
    
    def comentario_bloco(self, items):
        """Comentário de bloco"""
        return f"# {items[0]}"
        
    # === FUNÇÕES MATEMÁTICAS EXPANDIDAS ===
    
    def nome_funcao(self, items):
        """Nomes de funções matemáticas expandidas"""
        if not items:
            return "unknown_function"
            
        nome = str(items[0]).lower()
        
        # Mapeamento de funções
        mapeamento = {
            # Básicas
            'abs': 'abs', 'max': 'max', 'min': 'min', 'round': 'round',
            'sqrt': 'math.sqrt', 'pow': 'pow', 'log': 'math.log', 'exp': 'math.exp',
            # Trigonométricas
            'sin': 'math.sin', 'cos': 'math.cos', 'tan': 'math.tan',
            'asin': 'math.asin', 'acos': 'math.acos', 'atan': 'math.atan', 'atan2': 'math.atan2',
            # Especiais
            'ceil': 'math.ceil', 'floor': 'math.floor', 'sign': 'math.copysign',
            'mod': 'operator.mod', 'gcd': 'math.gcd', 'lcm': 'math.lcm',
            # Condicionais
            'if': 'if', 'iif': 'if', 'switch': 'switch',
            # Estatísticas
            'median': 'statistics.median', 'mode': 'statistics.mode',
            'percentile': 'numpy.percentile', 'rank': 'scipy.stats.rankdata'
        }
        
        return mapeamento.get(nome, nome)
    
    # === TOKENS EXPANDIDOS ===
    
    def numero(self, items):
        """Números em todos os formatos"""
        valor = str(items[0])
        # Números científicos, decimais, inteiros, hexadecimais
        if 'e' in valor.lower() or 'E' in valor:
            return float(valor)
        elif '0x' in valor.lower() or '0X' in valor:
            return int(valor, 16)
        elif '.' in valor:
            return float(valor)
        else:
            return int(valor)
    
    def booleano(self, items):
        """Valores booleanos expandidos"""
        valor = str(items[0]).lower()
        verdadeiros = ['verdadeiro', 'true', 'sim', '1']
        return str(valor in verdadeiros).lower()

    # === MÉTODOS AUXILIARES ===
    
    def _traduzir_operador_relacional(self, op: str) -> str:
        """Traduz operadores relacionais"""
        mapeamento = {
            '<=': '<=',
            '>=': '>=', 
            '==': '==',
            '=': '==',
            '!=': '!=',
            '<>': '!=',
            '<': '<',
            '>': '>'
        }
        return mapeamento.get(op, op)
    
    def _traduzir_operador_logico(self, op: str) -> str:
        """Traduz operadores lógicos"""
        mapeamento = {
            'E': 'and',
            'OU': 'or',
            'AND': 'and',
            'OR': 'or',
            'and': 'and',
            'or': 'or'
        }
        return mapeamento.get(op, op)
    
    def _traduzir_operador_unario(self, op: str) -> str:
        """Traduz operadores unários"""
        mapeamento = {
            'NAO': 'not',
            'NOT': 'not',
            'not': 'not',
            '+': '+',
            '-': '-'
        }
        return mapeamento.get(op, op)
    
    def _mapear_funcao_matematica(self, nome: str) -> str:
        """Mapeia função LOS para Python"""
        mapeamento = {
            'abs': 'abs',
            'max': 'max', 
            'min': 'min',
            'sum': 'sum',
            'sqrt': 'math.sqrt',
            'pow': 'pow',
            'log': 'math.log',
            'exp': 'math.exp',
            'round': 'round'
        }
        return mapeamento.get(nome, nome)
    
    def _mapear_funcao_agregada(self, nome: str) -> str:
        """Mapeia função agregada LOS para Python"""
        mapeamento = {
            'soma': 'sum',
            'sum': 'sum',
            'max': 'max',
            'maximo': 'max', 
            'min': 'min',
            'minimo': 'min',
            'media': 'sum(...)/len(...)',
            'mean': 'sum(...)/len(...)',
            'contar': 'len',
            'count': 'len'
        }
        return mapeamento.get(nome, nome)
    
    def _operador_para_tipo(self, op: str) -> str:
        """Converte operador para tipo de restrição"""
        mapeamento = {
            '<=': 'menor_igual',
            '>=': 'maior_igual',
            '==': 'igual',
            '!=': 'diferente',
            '<': 'menor',
            '>': 'maior'
        }
        return mapeamento.get(op, 'desconhecido')
    
    def operador_relacional(self, items):
        """Traduz operadores relacionais (<=, >=, ==, !=, <, >, =)"""
        if not items:
            return "=="
        
        # Pegar o primeiro token/item
        operador = items[0]
        
        # Se for um Token do Lark, extrair o valor
        if hasattr(operador, 'value'):
            valor_op = operador.value
        elif hasattr(operador, 'type'):
            valor_op = str(operador)  # Para tokens sem .value
        else:
            valor_op = str(operador)
        
        return self._traduzir_operador_relacional(valor_op)
    
    def op_aditivo(self, items):
        """Operador + ou -"""
        return str(items[0]) if items else "+"
    
    def op_multiplicativo(self, items):
        """Operador * ou /"""
        return str(items[0]) if items else "*"
    

# === PARSER LOS AVANÇADO ===

class ParserLOS:
    """Parser LOS usando Lark para expressões complexas"""
    
    def __init__(self, arquivo_gramatica: str = None):
        """Inicializa parser com gramática Lark"""
        if arquivo_gramatica is None:
            arquivo_gramatica = Path(__file__).parent / "los_grammar.lark"
        
        try:
            with open(arquivo_gramatica, 'r', encoding='utf-8') as f:
                gramatica = f.read()
            
            self.parser = Lark(
                gramatica,
                parser='lalr',  # Parser LR eficiente
                start='expressao'  # Não usar transformer aqui
            )
            
            self.dados_csv = {}
            self.variaveis_detectadas = set()
            self.tradutor = TradutorLOS()
            
            logger.info("Parser LOS Avançado (Lark) inicializado com sucesso")
            
        except FileNotFoundError:
            logger.error(f"Arquivo de gramática não encontrado: {arquivo_gramatica}")
            raise
        except Exception as e:
            logger.error(f"Erro ao inicializar parser Lark: {e}")
            raise
    
    def carregar_dados_csv(self, dados_csv: Dict[str, pd.DataFrame]):
        """Carrega dados CSV para referência"""
        self.dados_csv = dados_csv
        logger.info(f"Carregados {len(dados_csv)} DataFrames: {list(dados_csv.keys())}")
    
    def analisar_expressao(self, texto: str) -> ExpressaoLOS:
        """Analisa uma expressão LOS usando Lark"""
        try:
            # Preprocessar texto
            texto_limpo = self._preprocessar_texto(texto)
            
            # Parse com Lark
            arvore = self.parser.parse(texto_limpo)
            
            # Transformar em código Python usando o transformer separadamente
            resultado = self.tradutor.transform(arvore)
            
            # Extrair informações
            tipo = self._detectar_tipo_expressao(resultado)
            operacao = self._extrair_operacao(resultado)
            codigo_python = self._extrair_codigo(resultado)
            
            return ExpressaoLOS(
                tipo=tipo,
                operacao=operacao,
                expressao_original=texto,
                arvore_sintaxe=arvore,
                codigo_python=codigo_python,
                variaveis_detectadas=self.tradutor.variaveis_encontradas.copy(),
                datasets_referenciados=self.tradutor.datasets_referenciados.copy(),
                complexidade=self.tradutor.nivel_complexidade
            )
            
        except (ParseError, LexError) as e:
            logger.error(f"Erro de parsing: {e}")
            raise ValueError(f"Erro de sintaxe na expressão: {texto}\nDetalhes: {e}")
        except Exception as e:
            logger.error(f"Erro inesperado ao analisar expressão: {e}")
            raise
    
    def analisar_texto(self, texto: str) -> ExpressaoLOS:
        """Método alias para compatibilidade com testes existentes"""
        return self.analisar_expressao(texto)
    
    def analisar_restricoes(self, texto: str) -> List[ExpressaoLOS]:
        """Analisa múltiplas restrições de um texto"""
        restricoes = []
        # Remover comentários e linhas vazias
        linhas = []
        for linha_original in texto.split('\n'):
            linha = linha_original.strip()
            if not linha or linha.startswith('#'):
                continue
            # Verificar se é uma linha de continuação (indentada)
            if linha.startswith(' ') and linhas:
                # Adicionar à linha anterior, preservando espaço
                linhas[-1] += ' ' + linha
            else:
                linhas.append(linha)
        
        # Processar as linhas agrupadas
        for linha in linhas:
            try:
                restricao = self.analisar_express_expressao(linha)
                restricoes.append(restricao)
            except Exception as e:
                logger.warning(f"Erro ao analisar restrição '{linha}': {e}")
                continue
        
        return restricoes
    
    def limpar_variaveis(self):
        """Limpa variáveis detectadas - para compatibilidade com testes"""
        self.tradutor.variaveis_encontradas.clear()
        self.tradutor.datasets_referenciados.clear()
        self.tradutor.nivel_complexidade = 1
    
    def _preprocessar_texto(self, texto: str) -> str:
        """Preprocessa o texto antes do parsing"""
        # Normalizar espaços em branco
        texto = ' '.join(texto.split())
        
        # Converter palavras-chave para maiúsculas
        palavras_chave = [
            'minimizar', 'maximizar', 'se', 'entao', 'senao',
            'para', 'cada', 'em', 'onde', 'e', 'ou', 'nao'
        ]
        
        # Tratamento especial para "SOMA DE" - converte sempre em contextos apropriados
        texto = re.sub(r'\bsoma\s+de\b', 'SOMA DE', texto, flags=re.IGNORECASE)
        
        # Usar regex para substituir apenas palavras inteiras e não partes de palavras
        for palavra in palavras_chave:
            texto = re.sub(r'\b' + palavra + r'\b', palavra.upper(), texto, flags=re.IGNORECASE)
        
        return texto
    
    def _detectar_tipo_expressao(self, resultado) -> str:
        """Detecta o tipo de expressão baseado no resultado"""
        if isinstance(resultado, dict):
            return resultado.get('tipo', 'matematica')
        elif isinstance(resultado, str):
            if any(op in resultado for op in ['<=', '>=', '==', '!=', '<', '>']):
                return 'restricao'
            elif 'if' in resultado and 'else' in resultado:
                return 'condicional'
            else:
                return 'matematica'
        else:
            return 'matematica'
    
    def _extrair_operacao(self, resultado) -> str:
        """Extrai a operação da expressão"""
        if isinstance(resultado, dict):
            return resultado.get('operacao', 'expressao')
        else:
            return 'expressao'
    
    def _extrair_codigo(self, resultado) -> str:
        """Extrai o código Python da expressão"""
        if isinstance(resultado, dict):
            return resultado.get('codigo', str(resultado))
        else:
            return str(resultado)
    
    def gerar_variaveis_decisao(self) -> Dict[str, Dict[str, Any]]:
        """Gera estrutura de variáveis para uso com PuLP"""
        variaveis = {}
        
        # Processa todas as variáveis encontradas pelo tradutor
        for nome_var in self.tradutor.variaveis_encontradas:
            # Ignorar variáveis que são resultado de algum processamento
            # e não são nomes reais de variáveis (como o resultado de operações)
            if ' ' in nome_var or '(' in nome_var or ')' in nome_var or '+' in nome_var:
                continue
                
            # Verifica se é uma variável indexada pelo padrão do nome
            if '[' in nome_var and ']' in nome_var:
                # Caso indexado: extrai nome base e índices
                nome_base = nome_var.split('[')[0].strip()
                indices_str = nome_var.split('[')[1].split(']')[0].strip()
                indices = [idx.strip() for idx in indices_str.split(',')]
                
                # Adiciona à estrutura com informação de índices
                variaveis[nome_base] = {
                    'tipo': 'continua',  # Padrão é variável contínua
                    'indices': indices,
                    'dimensoes': len(indices)
                }
            else:
                # Variável escalar simples
                variaveis[nome_var] = {
                    'tipo': 'continua',  # Padrão é variável contínua
                    'dimensoes': 0
                }
        
        return variaveis
    
    def traduzir_para_pulp(self, expressao: ExpressaoLOS) -> str:
        """Traduz expressão LOS para código compatível com PuLP"""
        if not expressao:
            return ""
        
        # Usar código Python gerado
        codigo_python = expressao.codigo_python
        
        # Para objetivos, adicionar prefixo adequado
        if expressao.tipo == "objetivo":
            if expressao.operacao == "minimizar":
                return f"prob += {codigo_python}"
            elif expressao.operacao == "maximizar":
                return f"prob += {codigo_python}"
        
        # Para restrições
        elif expressao.tipo == "restricao":
            return f"prob += {codigo_python}"
        
        # Para expressões simples
        return codigo_python
