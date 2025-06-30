# -*- coding: utf-8 -*-
"""
Parser LOS Avançado usando Lark
Suporta expressões complexas com precedência correta e aninhamento profundo
SEMPRE utiliza gramática externa gramatica_los.lark
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
CAMINHO_GRAMATICA = Path(__file__).parent / "gramatica_los.lark"

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


class TradutorLarkLOS(Transformer):
    """Tradutor que converte árvore sintática Lark para código Python/PuLP"""
    
    def __init__(self):
        super().__init__()
        self.variaveis_encontradas = set()
        self.datasets_referenciados = set()
        self.nivel_complexidade = 1
    
    # === EXPRESSÕES PRINCIPAIS ===
    
    def objetivo(self, items):
        """MINIMIZAR/MAXIMIZAR: expressão"""
        if len(items) < 1:
            raise ValueError(f"Objetivo malformado: {items}")
        
        # O primeiro item é a expressão, o tipo de objetivo vem do token
        expressao = str(items[0])
        
        # Como não temos acesso direto ao token aqui, vamos assumir 'minimizar'
        # Isso será melhorado quando tivermos mais contexto
        return {
            'tipo': 'objetivo',
            'operacao': 'objetivo',  # Será refinado depois
            'expressao': expressao,
            'codigo': str(expressao)
        }
    
    def restricao(self, items):
        """expressão operador expressão"""
        if len(items) < 3:
            raise ValueError(f"Restrição malformada: {items}")
            
        esquerda = str(items[0])
        operador = self._traduzir_operador_relacional(str(items[1]))
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
        condicao = items[0]
        expr_entao = items[1]
        expr_senao = items[2] if len(items) > 2 else "0"
        
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
            return str(items[0]) if items else ""
        esquerda = str(items[0])
        operador = str(items[1])
        direita = str(items[2])
        return f"{esquerda} {operador} {direita}"
    
    def operacao_multiplicativa(self, items):
        """Operações *, /, //, %"""
        if len(items) < 3:
            return str(items[0]) if items else ""
        esquerda = str(items[0])
        operador = str(items[1])
        direita = str(items[2])
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
    
    def loop_para_cada(self, items):
        """PARA CADA var EM dataset [PARA CADA var2 EM dataset2]"""
        loops = []
        i = 0
        while i < len(items):
            if i + 1 < len(items):
                variavel = str(items[i])
                dataset = str(items[i + 1])
                loops.append(f"for {variavel} in {dataset}")
                self.datasets_referenciados.add(dataset)
                i += 2
            else:
                break
        
        return " ".join(loops)
    
    def condicao_onde(self, items):
        """ONDE condição"""
        return items[0]  # A condição já foi processada
    
    # === FUNÇÕES ===
    
    def funcao_matematica(self, items):
        """abs(x), max(a,b), etc."""
        if len(items) < 2:
            return str(items[0]) if items else ""
        nome_funcao = str(items[0])
        argumentos = str(items[1]) if len(items) > 1 else ""
        
        funcao_python = self._mapear_funcao_matematica(nome_funcao)
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
        indice = str(items[1])
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
        return ",".join(str(item) for item in items)
    
    def referencia_dataset(self, items):
        """produtos.Custo_Producao"""
        dataset = str(items[0])
        coluna = str(items[1])
        
        self.datasets_referenciados.add(dataset)
        
        # Remover aspas se for coluna com espaços
        if coluna.startswith("'") and coluna.endswith("'"):
            coluna = coluna[1:-1]
        
        return f'{dataset}["{coluna}"]'
    
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


# === PARSER LOS AVANÇADO ===

class ParserLOSAvancado:
    """Parser LOS avançado usando Lark para expressões complexas"""
    
    def __init__(self, arquivo_gramatica: str = None):
        """Inicializa parser com gramática Lark"""
        if arquivo_gramatica is None:
            arquivo_gramatica = Path(__file__).parent / "gramatica_los.lark"
        
        try:
            with open(arquivo_gramatica, 'r', encoding='utf-8') as f:
                gramatica = f.read()
            
            self.parser = Lark(
                gramatica,
                parser='lalr',  # Parser LR eficiente
                start='expressao',  # Corrigido: usar 'expressao' em vez de 'start'
                transformer=TradutorLarkLOS()
            )
            
            self.dados_csv = {}
            self.tradutor = TradutorLarkLOS()
            
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
            
            # Transformar em código Python
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
    
    def analisar_multiplas_expressoes(self, texto: str) -> List[ExpressaoLOS]:
        """Analisa múltiplas expressões separadas por linha"""
        linhas = [linha.strip() for linha in texto.split('\n') 
                 if linha.strip() and not linha.strip().startswith('#')]
        
        expressoes = []
        for linha in linhas:
            try:
                expressao = self.analisar_expressao(linha)
                expressoes.append(expressao)
            except Exception as e:
                logger.warning(f"Falha ao analisar linha '{linha}': {e}")
        
        return expressoes
    
    def validar_expressao(self, texto: str) -> Dict[str, Any]:
        """Valida uma expressão e retorna informações detalhadas"""
        try:
            expressao = self.analisar_expressao(texto)
            
            return {
                'valida': True,
                'tipo': expressao.tipo,
                'operacao': expressao.operacao,
                'codigo_python': expressao.codigo_python,
                'variaveis': list(expressao.variaveis_detectadas),
                'datasets': list(expressao.datasets_referenciados),
                'complexidade': expressao.complexidade,
                'erro': None
            }
        
        except Exception as e:
            return {
                'valida': False,
                'tipo': None,
                'operacao': None,
                'codigo_python': '',
                'variaveis': [],
                'datasets': [],
                'complexidade': 0,
                'erro': str(e)
            }
    
    def gerar_codigo_pulp_completo(self, expressoes: List[ExpressaoLOS]) -> str:
        """Gera código PuLP completo a partir de múltiplas expressões"""
        codigo_lines = []
        codigo_lines.append("# Código PuLP gerado automaticamente")
        codigo_lines.append("import pulp")
        codigo_lines.append("import math")
        codigo_lines.append("import statistics")
        codigo_lines.append("")
        
        # Separar objetivos e restrições
        objetivos = [e for e in expressoes if e.tipo == 'objetivo']
        restricoes = [e for e in expressoes if e.tipo == 'restricao']
        
        # Detectar todas as variáveis
        todas_variaveis = set()
        for expr in expressoes:
            todas_variaveis.update(expr.variaveis_detectadas)
        
        # Gerar variáveis de decisão
        codigo_lines.append("# Variáveis de decisão")
        for var in sorted(todas_variaveis):
            codigo_lines.append(f"{var} = pulp.LpVariable.dicts('{var}', indices, lowBound=0)")
        codigo_lines.append("")
        
        # Gerar modelo
        codigo_lines.append("# Modelo de otimização")
        codigo_lines.append("modelo = pulp.LpProblem('Modelo_LOS', pulp.LpMinimize)")
        codigo_lines.append("")
        
        # Adicionar objetivo
        if objetivos:
            obj = objetivos[0]  # Primeiro objetivo
            sentido = "pulp.LpMinimize" if obj.operacao == "minimizar" else "pulp.LpMaximize"
            codigo_lines.append(f"# Função objetivo")
            codigo_lines.append(f"modelo += {obj.codigo_python}")
            codigo_lines.append("")
        
        # Adicionar restrições
        if restricoes:
            codigo_lines.append("# Restrições")
            for i, rest in enumerate(restricoes):
                codigo_lines.append(f"modelo += {rest.codigo_python}  # Restrição {i+1}")
            codigo_lines.append("")
        
        # Resolver
        codigo_lines.append("# Resolver modelo")
        codigo_lines.append("modelo.solve()")
        codigo_lines.append("print(f'Status: {pulp.LpStatus[modelo.status]}')")
        codigo_lines.append("")
        
        return "\n".join(codigo_lines)
    
    # === MÉTODOS AUXILIARES ===
    
    def _preprocessar_texto(self, texto: str) -> str:
        """Preprocessa o texto antes do parsing"""
        # Remover comentários e linhas vazias
        linhas = []
        for linha in texto.split('\n'):
            linha = linha.strip()
            if linha and not linha.startswith('#'):
                # Remover comentário inline
                if '#' in linha:
                    linha = linha.split('#', 1)[0].strip()
                if linha:
                    linhas.append(linha)
        
        return ' '.join(linhas)
    
    def _detectar_tipo_expressao(self, resultado) -> str:
        """Detecta o tipo da expressão a partir do resultado do parser"""
        if isinstance(resultado, dict):
            return resultado.get('tipo', 'matematica')
        return 'matematica'
    
    def _extrair_operacao(self, resultado) -> str:
        """Extrai a operação da expressão"""
        if isinstance(resultado, dict):
            return resultado.get('operacao', 'desconhecida')
        return 'desconhecida'
    
    def _extrair_codigo(self, resultado) -> str:
        """Extrai o código Python gerado"""
        if isinstance(resultado, dict):
            return resultado.get('codigo', str(resultado))
        return str(resultado)


# === FUNÇÕES DE UTILIDADE ===

def testar_parser_avancado():
    """Função para testar o parser avançado"""
    parser = ParserLOSAvancado()
    
    casos_teste = [
        # Casos básicos
        "MINIMIZAR: x + y",
        "MAXIMIZAR: x * 2 + y / 3",
        
        # Casos com precedência
        "x + y * z - w / v",
        "a * (b + c) / (d - e)",
        
        # Casos com agregação
        "MINIMIZAR: soma de produtos.Custo * x[produto] PARA CADA produto EM produtos",
        
        # Casos complexos
        """MINIMIZAR: soma de produtos.Custo * x[produto] + 
           max(clientes.Prioridade * atraso[cliente]) 
           PARA CADA produto EM produtos 
           PARA CADA cliente EM clientes
           ONDE produtos.Ativo = 1 E clientes.Tipo = 'Premium'""",
        
        # Condicionais aninhadas
        "SE a > 0 ENTAO SE b > 0 ENTAO c * 2 SENAO d SENAO e"
    ]
    
    print("=== TESTE DO PARSER LOS AVANÇADO (LARK) ===")
    
    sucessos = 0
    falhas = 0
    
    for i, caso in enumerate(casos_teste, 1):
        print(f"\n--- CASO {i} ---")
        print(f"Entrada: {caso[:60]}{'...' if len(caso) > 60 else ''}")
        
        try:
            validacao = parser.validar_expressao(caso)
            
            if validacao['valida']:
                print(f"✅ SUCESSO")
                print(f"   Tipo: {validacao['tipo']}")
                print(f"   Código: {validacao['codigo_python'][:50]}...")
                print(f"   Complexidade: {validacao['complexidade']}")
                sucessos += 1
            else:
                print(f"❌ FALHA: {validacao['erro']}")
                falhas += 1
                
        except Exception as e:
            print(f"💥 ERRO: {e}")
            falhas += 1
    
    print(f"\n=== RESULTADO ===")
    print(f"Sucessos: {sucessos}")
    print(f"Falhas: {falhas}")
    print(f"Taxa de sucesso: {sucessos/(sucessos+falhas)*100:.1f}%")


if __name__ == "__main__":
    testar_parser_avancado()
