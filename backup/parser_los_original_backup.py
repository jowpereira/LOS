# -*- coding: utf-8 -*-
"""
Linguagem de Otimização Simples (LOS) - Versão Completamente Reescrita e Corrigida
Parser robusto e tradutor para uma linguagem intuitiva de otimização
Versão 3.2 - Todos os métodos avançados implementados corretamente
"""

import re
import pandas as pd
from typing import Dict, List, Any, Tuple, Optional, Union
from dataclasses import dataclass
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ExpressaoSimples:
    """Representa uma expressão na linguagem simples"""
    tipo: str  # 'objetivo', 'restricao', 'variavel'
    operacao: str  # 'minimizar', 'maximizar', 'igual', 'menor_igual', 'maior_igual'
    expressao: str
    condicoes: List[str] = None
    para_cada: Optional[str] = None
    onde: Optional[str] = None
    
    def __post_init__(self):
        if self.condicoes is None:
            self.condicoes = []

class TokenLOS:
    """Representa um token da linguagem LOS com informações completas de posição"""
    def __init__(self, tipo: str, valor: str, posicao: int = 0, linha: int = 1, coluna: int = 1):
        self.tipo = tipo
        self.valor = valor
        self.posicao = posicao  # Índice absoluto de caractere
        self.linha = linha     # Número da linha (começa em 1)
        self.coluna = coluna   # Número da coluna (começa em 1)
    
    def __repr__(self):
        return f"Token({self.tipo}, '{self.valor}', L{self.linha}:C{self.coluna})"
    
    def posicao_legivel(self) -> str:
        """Retorna posição em formato legível para mensagens de erro"""
        return f"linha {self.linha}, coluna {self.coluna}"

class LexerLOS:
    """Lexer (analisador léxico) para LOS - Versão Extremamente Versátil"""
    
    TOKENS = {
        # Palavras-chave de controle
        'MINIMIZAR': r'\b(?:MINIMIZAR|minimizar)\b',
        'MAXIMIZAR': r'\b(?:MAXIMIZAR|maximizar)\b',
        'SOMA_DE': r'\b(?:soma\s+de|SOMA\s+DE)\b',
        'PARA_CADA': r'\b(?:PARA\s+CADA|para\s+cada)\b',
        'EM': r'\b(?:EM|em)\b',
        'ONDE': r'\b(?:ONDE|onde)\b',
        
        # Operadores lógicos expandidos
        'E': r'\b(?:E|e|AND|and)\b',
        'OU': r'\b(?:OU|ou|OR|or)\b',
        'NAO': r'\b(?:NAO|nao|NOT|not)\b',
        
        # Condicionais
        'SE': r'\b(?:SE|se|IF|if)\b',
        'ENTAO': r'\b(?:ENTAO|entao|THEN|then)\b',
        'SENAO': r'\b(?:SENAO|senao|ELSE|else)\b',
        'CASO': r'\b(?:CASO|caso|CASE|case)\b',
        'QUANDO': r'\b(?:QUANDO|quando|WHEN|when)\b',
        
        # Funções matemáticas
        'ABS': r'\b(?:abs|ABS)\b',
        'MAX': r'\b(?:max|MAX|maximo|MAXIMO)\b',
        'MIN': r'\b(?:min|MIN|minimo|MINIMO)\b',
        'ROUND': r'\b(?:round|ROUND|arredondar|ARREDONDAR)\b',
        'SQRT': r'\b(?:sqrt|SQRT|raiz|RAIZ)\b',
        'POW': r'\b(?:pow|POW|potencia|POTENCIA)\b',
        'LOG': r'\b(?:log|LOG)\b',
        'EXP': r'\b(?:exp|EXP)\b',
        
        # Funções agregadas
        'SOMA': r'\b(?:soma|SOMA|sum|SUM)\b',
        'MEDIA': r'\b(?:media|MEDIA|mean|MEAN|avg|AVG)\b',
        'MEDIANA': r'\b(?:mediana|MEDIANA|median|MEDIAN)\b',
        'CONTAR': r'\b(?:contar|CONTAR|count|COUNT)\b',
        'PRIMEIRO': r'\b(?:primeiro|PRIMEIRO|first|FIRST)\b',
        'ULTIMO': r'\b(?:ultimo|ULTIMO|last|LAST)\b',
          # Operadores de comparação expandidos - CORREÇÃO: Reconhecer compostos como tokens únicos
        'OPERADOR_REL': r'(<=|>=|!=|<>|==|=|<|>)',
        'ESTA_EM': r'\b(?:esta\s+em|ESTA\s+EM|in|IN)\b',
        'NAO_ESTA_EM': r'\b(?:nao\s+esta\s+em|NAO\s+ESTA\s+EM|not\s+in|NOT\s+IN)\b',
        'CONTEM': r'\b(?:contem|CONTEM|contains|CONTAINS)\b',
        'INICIA_COM': r'\b(?:inicia\s+com|INICIA\s+COM|starts\s+with|STARTS\s+WITH)\b',
        'TERMINA_COM': r'\b(?:termina\s+com|TERMINA\s+COM|ends\s+with|ENDS\s+WITH)\b',
        
        # Tipos de dados
        'NUMERO': r'\d+(?:\.\d+)?',
        'STRING': r'"[^"]*"|\'[^\']*\'',
        'BOOLEANO': r'\b(?:verdadeiro|VERDADEIRO|falso|FALSO|true|TRUE|false|FALSE)\b',
        'NULL': r'\b(?:nulo|NULO|null|NULL|none|NONE)\b',
        
        # Estruturas
        'IDENTIFICADOR': r'[a-zA-Z_][a-zA-Z0-9_]*',
        'COLUNA_COM_ESPACO': r"'[^']+'\s*",  # Para colunas com espaços em aspas
        'PONTO': r'\.',
        'VIRGULA': r',',
        'ABRE_PAREN': r'\(',
        'FECHA_PAREN': r'\)',
        'ABRE_COLCH': r'\[',
        'FECHA_COLCH': r'\]',
        'ABRE_CHAVES': r'\{',
        'FECHA_CHAVES': r'\}',
        
        # Operadores matemáticos
        'POTENCIA': r'\*\*|\^',
        'MULTIPLICACAO': r'\*',
        'DIVISAO': r'/',
        'DIVISAO_INT': r'//',
        'MODULO': r'%',
        'ADICAO': r'\+',
        'SUBTRACAO': r'-',
        
        # Delimitadores
        'PONTO_VIRGULA': r';',
        'DOIS_PONTOS': r':',
        'PIPE': r'\|',
        'ESPACO': r'\s+'    }
    
    def __init__(self):
        self.token_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in self.TOKENS.items())
        self.compiled_regex = re.compile(self.token_regex)
    
    def tokenize(self, texto: str) -> List[TokenLOS]:
        """Converte texto em lista de tokens com informações completas de posição"""
        tokens = []
        linha_atual = 1
        inicio_linha = 0  # Índice onde a linha atual começou
        
        for match in self.compiled_regex.finditer(texto):
            tipo = match.lastgroup
            valor = match.group()
            posicao = match.start()
            
            # Calcular linha e coluna baseado na posição
            # Contar quebras de linha até a posição atual
            linhas_ate_aqui = texto[:posicao].count('\n')
            linha_atual = linhas_ate_aqui + 1
            
            # Encontrar o início da linha atual
            ultimo_newline = texto.rfind('\n', 0, posicao)
            if ultimo_newline == -1:
                # Estamos na primeira linha
                coluna_atual = posicao + 1
            else:
                # Calcular coluna baseada na distância do último \n
                coluna_atual = posicao - ultimo_newline
            
            # Filtrar tokens de espaço em branco (opcional para limpeza)
            if tipo != 'ESPACO':
                tokens.append(TokenLOS(tipo, valor, posicao, linha_atual, coluna_atual))
                
        return tokens

class TradutorCompleto:
    """Tradutor completo de LOS para Python/PuLP - Versão Extremamente Versátil"""
    
    def __init__(self):
        self.variaveis_encontradas = set()
        self.datasets_referenciados = set()
        # Lexer para processamento token-based
        self.lexer = LexerLOS()
        
        # Mapas de tradução para funcionalidades avançadas
        self.funcoes_matematicas = {
            'max': 'max', 'min': 'min', 'abs': 'abs', 'round': 'round',
            'sqrt': 'math.sqrt', 'pow': 'pow', 'log': 'math.log', 'exp': 'math.exp',
            'maximo': 'max', 'minimo': 'min', 'arredondar': 'round', 'raiz': 'math.sqrt',
            'potencia': 'pow'
        }
        
        self.funcoes_agregadas = {
            'soma': 'sum', 'sum': 'sum', 'media': 'statistics.mean', 'mean': 'statistics.mean',
            'avg': 'statistics.mean', 'mediana': 'statistics.median', 'median': 'statistics.median',
            'contar': 'len', 'count': 'len', 'primeiro': 'first', 'ultimo': 'last',
            'first': 'first', 'last': 'last'
        }
        
        self.operadores_logicos = {
            'e': ' and ', 'and': ' and ', 'ou': ' or ', 'or': ' or ',
            'nao': ' not ', 'not': ' not '
        }
        
        self.operadores_comparacao = {
            'esta_em': ' in ', 'esta em': ' in ', 'in': ' in ',
            'nao_esta_em': ' not in ', 'nao esta em': ' not in ', 'NAO ESTA EM': ' not in ', 
            'not in': ' not in ', 'not_in': ' not in ',
            'contem': '.contains(', 'contains': '.contains(',            'inicia_com': '.startswith(', 'inicia com': '.startswith(', 'starts with': '.startswith(',
            'termina_com': '.endswith(', 'termina com': '.endswith(', 'ends with': '.endswith('
        }
        
    def traduzir_expressao_completa(self, expressao: str) -> str:
        """
        Traduz uma expressão LOS completa para Python, lidando com construções complexas
        Suporta: loops, condicionais, operadores lógicos, funções matemáticas, etc.
        """        # Pipeline de tradução integrado que utiliza todos os métodos especializados
        expressao_processada = expressao
        
        # 1. CORREÇÃO: Integrar soma + PARA CADA em compreensões corretas primeiro
        expressao_processada = self._integrar_sum_com_loops(expressao_processada)
        
        # 2. Traduzir estruturas condicionais primeiro (SE/ENTAO/SENAO)
        expressao_processada = self._traduzir_condicionais(expressao_processada)
        
        # 3. Traduzir loops múltiplos aninhados
        expressao_processada = self._traduzir_loops_multiplos(expressao_processada)
        
        # 4. Traduzir somas agregadas restantes (soma de (...)) 
        expressao_processada = self._traduzir_somas(expressao_processada)
        
        # 5. Traduzir PARA CADA simples restantes
        expressao_processada = self._traduzir_para_cada(expressao_processada)
        
        # 5. Traduzir ONDE
        expressao_processada = self._traduzir_onde(expressao_processada)
        
        # 6. Traduzir referências a datasets (dataset.coluna)
        expressao_processada = self._traduzir_referencias_dados(expressao_processada)
        
        # 7. Traduzir funções matemáticas e agregadas
        expressao_processada = self._traduzir_funcoes(expressao_processada)
        
        # 8. Traduzir operadores lógicos
        expressao_processada = self._traduzir_operadores_logicos(expressao_processada)
          # 9. Traduzir operadores de comparação
        expressao_processada = self._traduzir_operadores_comparacao(expressao_processada)
        
        # 10. Normalizar operadores finais
        expressao_processada = self._normalizar_operadores(expressao_processada)
        
        return expressao_processada
    
    def _integrar_sum_com_loops(self, expressao: str) -> str:
        """
        CORREÇÃO: Integra corretamente 'suma de EXPR PARA CADA var EM dataset' 
        em compreensões de lista válidas: sum([EXPR for var in dataset])
        """
        # Padrão para capturar construções do tipo:
        # "suma de EXPRESSAO PARA CADA var EM dataset [ONDE condição]"
        padrao_completo = r'suma\s+de\s+([^()]+?)\s+PARA\s+CADA\s+(\w+)\s+EM\s+(\w+)(?:\s+ONDE\s+(.+?))?(?=\s*$|\s*<=|\s*>=|\s*==|\s*<|\s*>|\s*=)'
        
        def substituir_sum_completo(match):
            expressao_soma = match.group(1).strip()
            var_loop = match.group(2)
            dataset = match.group(3)
            condicao_onde = match.group(4) if match.group(4) else None
            
            # Construir compreensão de lista correta
            if condicao_onde:
                # Traduzir a condição ONDE
                condicao_traduzida = self._processar_expressao_booleana(condicao_onde)
                return f"sum([{expressao_soma} for {var_loop} in {dataset} if {condicao_traduzida}])"
            else:
                return f"sum([{expressao_soma} for {var_loop} in {dataset}])"
        
        # Aplicar correção
        resultado = re.sub(padrao_completo, substituir_sum_completo, expressao, flags=re.IGNORECASE)
        
        return resultado
    
    def _traduzir_somas(self, expressao: str) -> str:
        """Traduz 'soma de (...)' para sum([...]) com tratamento robusto incluindo aspas"""
        # Primeiro, tratar casos com parênteses explícitos
        while 'soma de (' in expressao.lower():
            match = re.search(r'soma\s+de\s*\(', expressao, re.IGNORECASE)
            if not match:
                break
            inicio = match.start()
            pos_abre = match.end() - 1
            pos_fecha = -1
            i = pos_abre
            stack = []
            in_string = False
            string_char = None
            
            while i < len(expressao):
                c = expressao[i]
                
                # Controle de strings (aspas simples ou duplas)
                if c in ['"', "'"]:
                    if not in_string:
                        in_string = True
                        string_char = c
                    elif c == string_char:
                        in_string = False
                        string_char = None
                    i += 1
                    continue
                
                # Se estamos dentro de uma string, pular caracteres especiais
                if in_string:
                    i += 1
                    continue
                
                # Balanceamento de parênteses, colchetes e chaves
                if c in '([{':
                    stack.append(c)
                elif c == ')':
                    if stack and stack[-1] == '(': 
                        stack.pop()
                        if not stack:
                            pos_fecha = i
                            break
                    else:
                        # Se o topo não for '(', pode ser ')' sem '(' correspondente
                        # Em casos complexos, vamos continuar buscando
                        pass
                elif c == ']':
                    if stack and stack[-1] == '[': 
                        stack.pop()
                elif c == '}':
                    if stack and stack[-1] == '{': 
                        stack.pop()
                i += 1
            
            if pos_fecha == -1:
                # Fallback mais inteligente: buscar ')' que não está dentro de string
                in_string = False
                string_char = None
                for j in range(pos_abre+1, len(expressao)):
                    c = expressao[j]
                    if c in ['"', "'"]:
                        if not in_string:
                            in_string = True
                            string_char = c
                        elif c == string_char:
                            in_string = False
                            string_char = None
                        continue
                    
                    if not in_string and c == ')':
                        pos_fecha = j
                        break
                
                if pos_fecha == -1:
                    raise ValueError(f"Parênteses desbalanceados em: {expressao}")
            
            conteudo = expressao[pos_abre + 1:pos_fecha]
            if 'soma de (' in conteudo.lower():
                conteudo_traduzido = self._traduzir_somas(conteudo)
            else:
                conteudo_traduzido = conteudo
            nova_parte = f"sum([{conteudo_traduzido}])"
            expressao = expressao[:inicio] + nova_parte + expressao[pos_fecha + 1:]
        
        # Segundo, tratar casos sem parênteses explícitos: "soma de EXPRESSAO"
        # Padrão para capturar "soma de" seguido de expressão sem parênteses
        padrao_soma_simples = r'soma\s+de\s+([^()]+?)(?=\s+PARA\s+CADA|\s+ONDE|$)'
        match = re.search(padrao_soma_simples, expressao, re.IGNORECASE)
        if match:
            inicio = match.start()
            expressao_soma = match.group(1).strip()
            nova_parte = f"sum([{expressao_soma}])"
            # Substituir apenas esta ocorrência
            expressao = expressao[:inicio] + nova_parte + expressao[match.end():]
        
        return expressao
    
    def _traduzir_para_cada(self, expressao: str) -> str:
        """Traduz 'PARA CADA var EM dataset' para 'for var in dataset'"""
        padrao = r'PARA\s+CADA\s+(\w+)\s+EM\s+(\w+)'
        expressao = re.sub(padrao, r'for \1 in \2', expressao, flags=re.IGNORECASE)
        return expressao
    
    def _traduzir_onde(self, expressao: str) -> str:
        """Traduz 'ONDE condição' para 'if condição' com melhor tratamento"""
        # Primeiro, tratar múltiplas condições com E
        expressao = re.sub(r'\bE\b', ' and ', expressao, flags=re.IGNORECASE)
          # Traduzir ONDE para if, preservando espaçamento
        expressao = re.sub(r'\bONDE\s+', ' if ', expressao, flags=re.IGNORECASE)
        
        return expressao

    def _traduzir_referencias_dados(self, expressao: str) -> str:
        """Traduz referências como 'dataset.coluna' para 'dataset["coluna"]' melhorado"""
        # Padrão mais robusto para capturar dataset.coluna 
        # Inclui casos com índices: dataset[idx].coluna E casos simples: dataset.coluna
        padrao = r'(\w+(?:\[\w+\])?)\.(\w+|\'[^\']+\')'
        
        def substituir_referencia(match):
            dataset_com_indice = match.group(1)  # ex: ordens[ordem] ou ordens
            coluna = match.group(2)              # ex: Codigo_do_Cliente ou 'Nome do Cliente'
            
            # Preservar aspas se existirem para colunas com espaços
            if coluna.startswith("'") and coluna.endswith("'"):
                # Manter as aspas para colunas com espaços, mas converter para duplas
                coluna_final = f'"{coluna[1:-1]}"'
            else:
                # Adicionar aspas duplas para colunas sem espaços
                coluna_final = f'"{coluna}"'
            
            # Extrair o nome do dataset para registro
            dataset_base = dataset_com_indice.split('[')[0]
            self.datasets_referenciados.add(dataset_base)
            
            return f'{dataset_com_indice}[{coluna_final}]'
        
        return re.sub(padrao, substituir_referencia, expressao)

    def _normalizar_operadores(self, expressao: str) -> str:
        """Normaliza operadores e funções"""
        # Primeiro, preservar funções corrigendo espaçamento
        expressao = re.sub(r'\b(abs|max|min|sum)\s+\(', r'\1(', expressao, flags=re.IGNORECASE)
        
        # Preservar divisão explicitamente
        expressao = re.sub(r'\s*/\s*', ' / ', expressao)
        
        # Normalizar comparações - CUIDADO: apenas converter = simples para ==
        # Não alterar >=, <=, ou == já existentes
        expressao = re.sub(r'(?<![><=])=(?![=])', ' == ', expressao)
        
        # Normalizar outros operadores relacionais (preservando os existentes)
        expressao = re.sub(r'(?<![>])>=(?![=])', ' >= ', expressao)
        expressao = re.sub(r'(?<![<])<=(?![=])', ' <= ', expressao)
        
        return expressao

    def _traduzir_condicionais(self, expressao: str) -> str:
        """Traduz estruturas condicionais IF/ELSE para Python"""
        # Processar condicionais múltiplas vezes para capturar aninhamentos
        alteracoes = True
        while alteracoes:
            expressao_anterior = expressao
            
            # Padrão: SE (condição) ENTAO (expressão) SENAO (expressão)
            padrao_if = r'SE\s+(.+?)\s+ENTAO\s+(.+?)(?:\s+SENAO\s+(.+?))?(?=\s*$|\s*;|\s*,|\s*\))'
            
            def substituir_condicional(match):
                condicao = match.group(1).strip()
                then_expr = match.group(2).strip()
                else_expr = match.group(3).strip() if match.group(3) else '0'
                
                # Traduzir a condição
                condicao = self._processar_expressao_booleana(condicao)
                
                # Não adicionar parênteses extras se já estamos dentro de uma estrutura
                return f"{then_expr} if {condicao} else {else_expr}"
            
            # Aplicar transformação (case insensitive)
            expressao = re.sub(padrao_if, substituir_condicional, expressao, flags=re.IGNORECASE)
            
            alteracoes = (expressao != expressao_anterior)
        
        return expressao
    
    def _traduzir_operadores_logicos(self, expressao: str) -> str:
        """Traduz operadores lógicos E, OU, NAO para and, or, not"""
        for op_original, op_python in self.operadores_logicos.items():
            # Usar palavra completa para evitar substituições parciais
            padrao = r'\b' + re.escape(op_original) + r'\b'
            expressao = re.sub(padrao, op_python, expressao, flags=re.IGNORECASE)
        
        return expressao
    
    def _traduzir_funcoes(self, expressao: str) -> str:
        """Traduz funções matemáticas e agregadas"""
        # Primeiro, funções matemáticas
        for func_original, func_python in self.funcoes_matematicas.items():
            padrao = r'\b' + re.escape(func_original) + r'\('
            expressao = re.sub(padrao, f'{func_python}(', expressao, flags=re.IGNORECASE)
        
        # Depois, funções agregadas
        for func_original, func_python in self.funcoes_agregadas.items():
            padrao = r'\b' + re.escape(func_original) + r'\('
            if func_python in ['first', 'last']:
                # Tratamento especial para first/last
                if func_python == 'first':
                    expressao = re.sub(padrao, 'next(iter(', expressao, flags=re.IGNORECASE)
                else:  # last
                    expressao = re.sub(padrao, 'list(', expressao, flags=re.IGNORECASE)
                    expressao = re.sub(r'list\(([^)]+)\)', r'list(\1)[-1]', expressao)
            else:
                expressao = re.sub(padrao, f'{func_python}(', expressao, flags=re.IGNORECASE)
        
        return expressao
    
    def _traduzir_operadores_comparacao(self, expressao: str) -> str:
        """Traduz operadores de comparação avançados"""
        for op_original, op_python in self.operadores_comparacao.items():
            if op_python.endswith('('):
                # Operadores que são métodos (como .contains(, .startswith(, etc.)
                padrao = r'\b' + re.escape(op_original) + r'\b'
                expressao = re.sub(padrao, op_python, expressao, flags=re.IGNORECASE)
            else:
                # Operadores regulares (como in, not in)
                padrao = r'\b' + re.escape(op_original) + r'\b'
                expressao = re.sub(padrao, op_python, expressao, flags=re.IGNORECASE)
        
        # Normalizar espaços múltiplos
        expressao = re.sub(r'\s+', ' ', expressao)
        
        return expressao
    
    def _traduzir_loops_multiplos(self, expressao: str) -> str:
        """Traduz loops aninhados PARA CADA...EM...PARA CADA...EM"""
        # Padrão para loops aninhados
        padrao_loop_aninhado = r'PARA\s+CADA\s+(\w+)\s+EM\s+(\w+)\s+PARA\s+CADA\s+(\w+)\s+EM\s+(\w+)'
        
        def substituir_loop_aninhado(match):
            var1, dataset1, var2, dataset2 = match.groups()
            return f"for {var1} in {dataset1} for {var2} in {dataset2}"
        
        expressao = re.sub(padrao_loop_aninhado, substituir_loop_aninhado, expressao, flags=re.IGNORECASE)
        
        return expressao
    
    def _processar_expressao_booleana(self, expressao: str) -> str:
        """Processa expressões booleanas complexas"""
        # Primeiro, traduzir operadores de comparação
        expressao = self._traduzir_operadores_comparacao(expressao)
        
        # Traduzir operadores lógicos
        expressao = self._traduzir_operadores_logicos(expressao)
        
        # Normalizar comparações (= para ==)
        expressao = re.sub(r'(?<![><=!])=(?![=])', ' == ', expressao)
        
        # Traduzir palavras especiais
        expressao = re.sub(r'\bVERDADEIRO\b', 'True', expressao, flags=re.IGNORECASE)
        expressao = re.sub(r'\bFALSO\b', 'False', expressao, flags=re.IGNORECASE)
        expressao = re.sub(r'\bNULO\b', 'None', expressao, flags=re.IGNORECASE)
        
        return expressao


class ParserLinguagemSimples:
    """Parser completamente reescrito para a Linguagem de Otimização Simples"""
    
    def __init__(self):
        self.dados_csv = {}
        self.variaveis_detectadas = set()
        self.lexer = LexerLOS()
        self.tokens = []
        self.posicao_atual = 0
        self.tradutor = TradutorCompleto()
        self.mapeamento_colunas = {}
    
    def carregar_dados_csv(self, dados_csv: Dict[str, pd.DataFrame]):
        """Carrega os DataFrames dos CSVs para referência"""
        self.dados_csv = dados_csv
        logger.info(f"Carregados {len(dados_csv)} DataFrames: {list(dados_csv.keys())}")
        
        # Criar mapeamento de colunas
        for nome_df, df in self.dados_csv.items():
            for coluna in df.columns:                # Mapeamento direto
                self.mapeamento_colunas[f"{nome_df}.{coluna}"] = f'{nome_df}["{coluna}"]'
                # Mapeamento normalizado
                coluna_normalizada = coluna.replace(' ', '_').replace('ç', 'c').replace('ã', 'a')
                self.mapeamento_colunas[f"{nome_df}.{coluna_normalizada}"] = f'{nome_df}["{coluna}"]'

    def token_atual(self) -> Optional[TokenLOS]:
        """Retorna o token atual na posição"""
        if self.posicao_atual < len(self.tokens):
            return self.tokens[self.posicao_atual]
        return None
    
    def consumir_token(self, tipo_esperado: str = None) -> TokenLOS:
        """Consome e retorna o próximo token"""
        if self.posicao_atual >= len(self.tokens):
            raise ValueError("Fim inesperado da expressão")
        
        token = self.tokens[self.posicao_atual]
        if tipo_esperado and token.tipo != tipo_esperado:
            raise ValueError(f"Esperado {tipo_esperado}, encontrado {token.tipo}")
        
        self.posicao_atual += 1
        return token
    
    def detectar_variaveis_decisao(self, texto: str, tokens: List[TokenLOS]):
        """Detecta variáveis de decisão no texto usando análise mais robusta"""
        for i, token in enumerate(tokens):
            if token.tipo == 'IDENTIFICADOR':
                # Verificar se é seguido por colchetes (variável indexada)
                if i + 1 < len(tokens) and tokens[i + 1].tipo == 'ABRE_COLCH':
                    self.variaveis_detectadas.add(token.valor)
                # Verificar se é uma variável simples (não palavra reservada)
                elif not self._e_palavra_reservada(token.valor) and not self._e_dataset(token.valor):
                    # Verificar se não é parte de uma referência a coluna (dataset.coluna)
                    if not (i + 1 < len(tokens) and tokens[i + 1].tipo == 'PONTO'):
                        # Verificar se não é coluna sendo referenciada
                        if not (i > 0 and tokens[i - 1].tipo == 'PONTO'):
                            self.variaveis_detectadas.add(token.valor)
    
    def limpar_variaveis(self):
        """Limpa o conjunto de variáveis detectadas para começar nova análise"""
        self.variaveis_detectadas.clear()

    def _e_palavra_reservada(self, palavra: str) -> bool:
        """Verifica se a palavra é reservada da linguagem LOS"""
        palavras_reservadas = {
            'minimizar', 'maximizar', 'soma', 'de', 'para', 'cada', 'em', 'onde', 
            'abs', 'e', 'ou', 'sum', 'for', 'in', 'if', 'and', 'or'
        }
        return palavra.lower() in palavras_reservadas

    def _e_dataset(self, palavra: str) -> bool:
        """Verifica se a palavra é nome de um dataset carregado"""
        return palavra in self.dados_csv.keys()
    
    def gerar_variaveis_decisao(self) -> List[Dict]:
        """Gera lista de variáveis de decisão baseada no que foi detectado"""
        variaveis = []
        for nome in self.variaveis_detectadas:
            variaveis.append({
                'nome': nome,
                'tipo': 'continua',
                'limite_inferior': 0
            })
        return variaveis
    
    def preprocessar_texto(self, texto: str) -> str:
        """Preprocessa o texto removendo comentários e normalizando - PRESERVANDO ASPAS"""
        if not texto:
            return ""
        # Remover comentários e linhas vazias
        linhas = []
        for linha in texto.split('\n'):
            linha = linha.strip()
            if linha:
                # Remover comentário inline (após #)
                if '#' in linha:
                    linha = linha.split('#', 1)[0].strip()
                if linha and not linha.startswith('#'):
                    linhas.append(linha)        # Juntar todas as linhas em uma expressão única
        texto_processado = ' '.join(linhas)
        # Normalizar espaços múltiplos
        texto_processado = re.sub(r'\s+', ' ', texto_processado)
        # NÃO normalizar aspas automáticamente - preservar o formato original
        # Isso permite que o parser trate adequadamente colunas com espaços
        return texto_processado.strip()
    
    def analisar_texto(self, texto: str) -> 'ExpressaoSimples':
        """
        Analisa um texto na linguagem simples e retorna uma expressão estruturada
        """
        # Preprocessar o texto (remover comentários, normalizar)
        texto = self.preprocessar_texto(texto)
        if not texto:
            raise ValueError("Texto vazio após preprocessamento")
        # Tokenizar o texto
        self.tokens = self.lexer.tokenize(texto)
        self.posicao_atual = 0
        if not self.tokens:
            raise ValueError("Nenhum token válido encontrado")        # Detectar variáveis de decisão
        self.detectar_variaveis_decisao(texto, self.tokens)
        # Analisar baseado no primeiro token ou na estrutura geral
        primeiro_token = self.tokens[0]
        # Verificar se é objetivo (MINIMIZAR/MAXIMIZAR)
        if primeiro_token.tipo in ['MINIMIZAR', 'MAXIMIZAR']:
            return self._analisar_objetivo()
        # Verificar se é condicional (SE)
        elif primeiro_token.tipo == 'SE':
            return self._analisar_expressao_condicional()
        # Verificar se contém operador relacional (restrição)
        elif any(token.tipo == 'OPERADOR_REL' for token in self.tokens):
            return self._analisar_restricao()
        # Verificar se contém operadores de conjunto ou lógicos (ESTA EM, NAO ESTA EM, E, OU)
        elif any(token.tipo in ['ESTA_EM', 'NAO_ESTA_EM', 'E', 'OU'] for token in self.tokens):
            return self._analisar_restricao()
        # Verificar se é expressão com funções matemáticas/agregadas
        elif any(token.tipo in ['MAX', 'MIN', 'SOMA', 'MEDIA', 'ABS'] for token in self.tokens):
            return self._analisar_expressao_funcional()
        # Verificar se expressão começa com agregação (soma de (, media(, max(, min(, abs()
        elif texto.strip().lower().startswith(('soma de (', 'media(', 'max(', 'min(', 'abs(')):
            return self._analisar_expressao_funcional()
        # Verificar se contém loops aninhados múltiplos
        elif texto.count('PARA CADA') > 1:
            return self._analisar_loops_multiplos()
        else:
            raise ValueError(f"Não foi possível interpretar a expressão: {texto}")
    
    def _analisar_objetivo(self) -> ExpressaoSimples:
        """Analisa expressão de objetivo (MINIMIZAR/MAXIMIZAR)"""
        token_operacao = self.consumir_token()  # MINIMIZAR ou MAXIMIZAR
        operacao = token_operacao.valor.lower()
        
        # Consumir ':' se existir
        if self.token_atual() and self.token_atual().tipo == 'DOIS_PONTOS':
            self.consumir_token()
        
        # Converter todos os tokens restantes de volta para string
        tokens_restantes = self.tokens[self.posicao_atual:]
        expressao_completa = self._tokens_para_string(tokens_restantes)
        
        # Usar regex para separar expressão, PARA CADA e ONDE
        para_cada = None
        onde = None
        expressao = expressao_completa
        
        # Extrair PARA CADA (pegar o último, que é o mais externo)
        padrao_para_cada = r'PARA\s+CADA\s+(\w+)\s+EM\s+(\w+)'
        matches_para_cada = list(re.finditer(padrao_para_cada, expressao, re.IGNORECASE))
        if matches_para_cada:
            ultimo_match = matches_para_cada[-1]
            para_cada = f"{ultimo_match.group(1)} EM {ultimo_match.group(2)}"
            # Remover apenas este PARA CADA da expressão
            expressao = expressao[:ultimo_match.start()] + expressao[ultimo_match.end():]
        
        # Extrair ONDE
        match_onde = re.search(r'ONDE\s+(.+)', expressao, re.IGNORECASE)
        if match_onde:
            onde = match_onde.group(1).strip()
            expressao = expressao[:match_onde.start()].strip()
        
        if not expressao.strip():
            raise ValueError("Expressão de objetivo vazia")
        
        return ExpressaoSimples(
            tipo='objetivo',
            operacao=operacao,
            expressao=expressao.strip(),
            para_cada=para_cada,
            onde=onde
        )
    
    def _analisar_restricao(self) -> ExpressaoSimples:
        """Analisa expressão de restrição"""
        expressao_completa = self._tokens_para_string(self.tokens)
        # Encontrar operador relacional
        match_restricao = re.search(r'(.+?)\s*(<=|>=|=)\s*(.+)', expressao_completa)
        if not match_restricao:
            # Se não houver operador relacional, tratar como restrição booleana/conjunto
            return ExpressaoSimples(
                tipo='restricao',
                operacao='booleana',
                expressao=expressao_completa.strip(),
                para_cada=None,
                onde=None
            )
        lado_esquerdo = match_restricao.group(1).strip()
        operador = match_restricao.group(2)
        lado_direito = match_restricao.group(3).strip()
        # Extrair PARA CADA e ONDE do lado direito (onde normalmente aparecem)
        para_cada = None
        onde = None
        texto_completo = lado_direito
        match_para_cada = re.search(r'PARA\s+CADA\s+(\w+)\s+EM\s+(\w+)', texto_completo, re.IGNORECASE)
        if match_para_cada:
            para_cada = f"{match_para_cada.group(1)} EM {match_para_cada.group(2)}"
            lado_direito = re.sub(r'PARA\s+CADA\s+\w+\s+EM\s+\w+', '', lado_direito, flags=re.IGNORECASE).strip()
        match_onde = re.search(r'ONDE\s+(.+)', texto_completo, re.IGNORECASE)
        if match_onde:
            onde = match_onde.group(1).strip()
            lado_direito = re.sub(r'ONDE\s+.+', '', lado_direito, flags=re.IGNORECASE).strip()
        
        operacao_map = {'<=': 'menor_igual', '>=': 'maior_igual', '=': 'igual'}
        return ExpressaoSimples(
            tipo='restricao',
            operacao=operacao_map[operador],
            expressao=f"{lado_esquerdo} {operador} {lado_direito}",
                    para_cada=para_cada,
            onde=onde
        )
    
    def _tokens_para_string(self, tokens: List[TokenLOS]) -> str:
        """Converte lista de tokens de volta para string preservando espaçamento correto"""
        if not tokens:
            return ""
        
        # Reconstruir string com espaçamento apropriado
        resultado = []
        for i, token in enumerate(tokens):
            if i > 0:
                token_anterior = tokens[i-1]
                skip_space = False
                
                # CORREÇÃO: Casos onde NÃO adicionar espaço
                # Antes de pontuação: . ( ) [ ] , ;
                if token.valor in ['.', '(', ')', '[', ']', ',', ';']:
                    skip_space = True
                
                # Depois de . ( [ 
                elif token_anterior.valor in ['.', '(', '[']:
                    skip_space = True
                
                # CORREÇÃO: Operadores compostos já vêm como tokens únicos do lexer
                # Não precisamos formar <=, >=, == aqui porque já são reconhecidos
                
                if not skip_space:
                    resultado.append(' ')
                    
            resultado.append(token.valor)
        
        return ''.join(resultado)
    
    def traduzir_para_pulp(self, expressao: ExpressaoSimples) -> str:
        """
        Traduz uma expressão simples para código PuLP/Python completamente
        """
        if expressao.tipo == 'objetivo':
            return self._traduzir_objetivo_completo(expressao)
        elif expressao.tipo == 'restricao':
            return self._traduzir_restricao_completo(expressao)
        elif expressao.tipo == 'condicional':
            return self._traduzir_restricao_completo(expressao)
        elif expressao.tipo == 'loops_multiplos':
            return self._traduzir_restricao_completo(expressao)
        else:
            raise ValueError(f"Tipo de expressão não suportado: {expressao.tipo}")
    
    def _traduzir_objetivo_completo(self, expressao: ExpressaoSimples) -> str:
        """Traduz objetivo para código PuLP usando o novo tradutor"""
        # Construir expressão completa incluindo PARA CADA e ONDE
        expr_completa = expressao.expressao
        
        if expressao.para_cada:
            expr_completa += f" PARA CADA {expressao.para_cada}"
        
        if expressao.onde:
            expr_completa += f" ONDE {expressao.onde}"
        
        # Traduzir usando o tradutor completo
        resultado = self.tradutor.traduzir_expressao_completa(expr_completa)
        
        # Se há PARA CADA, garantir que tenha estrutura de compreensão correta
        if expressao.para_cada:
            # Se o resultado já está na estrutura correta de sum([...]), mantê-lo
            if resultado.startswith('sum([') and resultado.endswith('])'):
                # Já está correto
                pass
            elif 'sum([' in resultado:
                # Tem sum mas estrutura pode estar errada
                # Verificar se tem 'for' e 'if' na estrutura
                if ' for ' in resultado and (not expressao.onde or ' if ' in resultado):
                    # Está correto, não mexer
                    pass
                else:
                    # Precisa reconstruir
                    var, dataset = expressao.para_cada.split(' EM ')
                    match = re.search(r'sum\(\[(.+)\]\)', resultado)
                    if match:
                        conteudo = match.group(1)
                        if expressao.onde:
                            resultado = f"sum([{conteudo} for {var} in {dataset} if {expressao.onde}])"
                        else:
                            resultado = f"sum([{conteudo} for {var} in {dataset}])"
            else:
                # Não tem sum, adicionar estrutura completa
                var, dataset = expressao.para_cada.split(' EM ')
                if expressao.onde:
                    resultado = f"sum([{resultado} for {var} in {dataset} if {expressao.onde}])"
                else:
                    resultado = f"sum([{resultado} for {var} in {dataset}])"
        
        return resultado
    
    def _traduzir_restricao_completo(self, expressao: ExpressaoSimples) -> str:
        """Traduz restrição para código PuLP usando o novo tradutor"""
        # Construir expressão completa incluindo PARA CADA e ONDE
        expr_completa = expressao.expressao
        
        if expressao.para_cada:
            expr_completa += f" PARA CADA {expressao.para_cada}"
        
        if expressao.onde:
            expr_completa += f" ONDE {expressao.onde}"
        
        # Traduzir usando o tradutor completo
        resultado = self.tradutor.traduzir_expressao_completa(expr_completa)
        
        # Para restrições com PARA CADA, envolver em lista
        if expressao.para_cada:
            resultado = f"[{resultado}]"
        
        return resultado
    
    def analisar_restricoes(self, texto_restricoes: str) -> List[ExpressaoSimples]:
        """
        Analisa um texto com múltiplas restrições e retorna uma lista de expressões estruturadas
        """
        if not texto_restricoes:
            return []
        
        # Filtrar comentários e separar por linhas
        linhas = [linha.strip() for linha in texto_restricoes.split('\n') 
                 if linha.strip() and not linha.strip().startswith('#')]
        
        restricoes = []
        for linha in linhas:
            try:
                restricao = self.analisar_texto(linha)
                if restricao.tipo == 'restricao':
                    restricoes.append(restricao)
                else:
                    logger.warning(f"Linha ignorada (não é restrição): {linha}")
            except Exception as e:
                logger.error(f"Erro ao analisar restrição '{linha}': {e}")
                raise ValueError(f"Erro ao processar restrição: {linha}. Erro: {str(e)}")
        
        return restricoes

    def _analisar_expressao_condicional(self) -> ExpressaoSimples:
        """Analisa expressões condicionais (SE/ENTAO/SENAO)"""
        expressao_completa = self._tokens_para_string(self.tokens)
        
        return ExpressaoSimples(
            tipo='condicional',
            operacao='se_entao_senao',
            expressao=expressao_completa
        )
    
    def _analisar_expressao_funcional(self) -> ExpressaoSimples:
        """Analisa expressões com funções matemáticas/agregadas"""
        expressao_completa = self._tokens_para_string(self.tokens)
        
        # Detectar se é objetivo ou restrição baseado na presença de operadores
        if any(token.tipo == 'OPERADOR_REL' for token in self.tokens):
            return ExpressaoSimples(
                tipo='restricao',
                operacao='funcional',
                expressao=expressao_completa
            )
        else:
            return ExpressaoSimples(
                tipo='objetivo',
                operacao='funcional',
                expressao=expressao_completa
            )
    
    def _analisar_loops_multiplos(self) -> ExpressaoSimples:
        """Analisa expressões com loops aninhados múltiplos"""
        expressao_completa = self._tokens_para_string(self.tokens)
        
        # Extrair todos os PARA CADA
        para_cada_matches = list(re.finditer(r'PARA\s+CADA\s+(\w+)\s+EM\s+(\w+)', 
                                           expressao_completa, re.IGNORECASE))
        
        # Construir lista de loops
        loops = [f"{m.group(1)} EM {m.group(2)}" for m in para_cada_matches]
        
        # Remover todos os PARA CADA da expressão base
        expressao_base = expressao_completa
        for match in reversed(para_cada_matches):
            expressao_base = expressao_base[:match.start()] + expressao_base[match.end():]
        
        # Extrair ONDE se existir
        onde_match = re.search(r'ONDE\s+(.+)', expressao_base, re.IGNORECASE)
        onde = None
        if onde_match:
            onde = onde_match.group(1).strip()
            expressao_base = expressao_base[:onde_match.start()].strip()
        
        return ExpressaoSimples(
            tipo='loops_multiplos',
            operacao='aninhados',
            expressao=expressao_base.strip(),
            condicoes=loops,  # Usar condicoes para armazenar os loops
            onde=onde
        )
    
    def _detectar_expressoes_complexas(self, texto: str) -> Dict[str, Any]:
        """Detecta e categoriza expressões complexas"""
        info = {
            'tem_condicionais': bool(re.search(r'\b(SE|ENTAO|SENAO|CASO|QUANDO)\b', texto, re.IGNORECASE)),
            'tem_operadores_logicos': bool(re.search(r'\b(E|OU|NAO|AND|OR|NOT)\b', texto, re.IGNORECASE)),
            'tem_funcoes_matematicas': bool(re.search(r'\b(MAX|MIN|ABS|SQRT|POW|LOG|EXP)\b', texto, re.IGNORECASE)),            'tem_funcoes_agregadas': bool(re.search(r'\b(SOMA|MEDIA|MEDIANA|CONTAR)\b', texto, re.IGNORECASE)),
            'tem_loops_multiplos': texto.count('PARA CADA') > 1,
            'tem_operadores_expandidos': bool(re.search(r'\b(ESTA\s+EM|CONTEM|INICIA\s+COM|TERMINA\s+COM)\b', texto, re.IGNORECASE))
        }
        
        return info
