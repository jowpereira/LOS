# -*- coding: utf-8 -*-
"""
Utilitários para validação de código gerado pelos testes
"""

import re
import ast
from typing import Dict, Set, List, Optional


def validar_codigo_python(codigo: str) -> bool:
    """Valida se o código Python gerado é sintaticamente correto"""
    try:
        compile(codigo, '<string>', 'eval')
        return True
    except SyntaxError:
        return False


def validar_compatibilidade_pulp(codigo: str) -> bool:
    """Valida se o código é compatível com PuLP (básico)"""
    # Verificações básicas de compatibilidade
    incompatibilidades = [
        'exec(',
        'eval(',
        'import ',
        '__'
    ]
    
    for incomp in incompatibilidades:
        if incomp in codigo:
            return False
    
    return True


def normalizar_expressao(expressao: str) -> str:
    """Normaliza uma expressão Python removendo espaços extras"""
    return ' '.join(expressao.split())


def comparar_expressoes(expr1: str, expr2: str, normalize: bool = True) -> bool:
    """Compara duas expressões Python normalizando espaços"""
    if normalize:
        expr1 = normalizar_expressao(expr1)
        expr2 = normalizar_expressao(expr2)
    return expr1 == expr2


def extrair_variaveis(codigo: str) -> Set[str]:
    """Extrai variáveis que parecem ser de decisão do código"""
    variaveis = set()
    # Padrão para x[...], y[...], etc.
    padrao = r'([a-zA-Z_]\w*)\['
    matches = re.findall(padrao, codigo)
    variaveis.update(matches)
    return variaveis


def contar_operadores(codigo: str) -> Dict[str, int]:
    """Conta operadores no código gerado"""
    operadores = {
        'sum': codigo.count('sum('),
        'max': codigo.count('max('),
        'min': codigo.count('min('),
        'for': codigo.count(' for '),
        'if': codigo.count(' if '),
        'and': codigo.count(' and '),
        'or': codigo.count(' or '),
        'not': codigo.count(' not '),
        'in': codigo.count(' in '),
        'list_comp': codigo.count('[') - codigo.count('sum([')  # Compreensões de lista independentes
    }
    return operadores


def extrair_datasets_referenciados(codigo: str) -> Set[str]:
    """Extrai nomes de datasets referenciados no código"""
    datasets = set()
    # Padrão para dataset["coluna"] ou dataset['coluna']
    padrao = r'([a-zA-Z_]\w*)\[[\"\']'
    matches = re.findall(padrao, codigo)
    datasets.update(matches)
    return datasets


def analisar_estrutura_loops(codigo: str) -> Dict[str, any]:
    """Analisa a estrutura de loops no código gerado"""
    info = {
        'total_fors': codigo.count(' for '),
        'loops_aninhados': 0,
        'tem_condicoes': ' if ' in codigo,
        'nivel_aninhamento': 0
    }
    
    # Detectar loops aninhados (contando for...for consecutivos)
    padrao_aninhado = r'for\s+\w+\s+in\s+\w+\s+for\s+\w+\s+in\s+\w+'
    matches_aninhados = re.findall(padrao_aninhado, codigo)
    info['loops_aninhados'] = len(matches_aninhados)
    
    # Estimar nível de aninhamento por contagem de 'for'
    if info['total_fors'] > 1:
        info['nivel_aninhamento'] = info['total_fors']
    
    return info


def validar_balanceamento_parenteses(codigo: str) -> bool:
    """Valida se parênteses estão balanceados"""
    stack = []
    pares = {'(': ')', '[': ']', '{': '}'}
    
    for char in codigo:
        if char in pares:
            stack.append(char)
        elif char in pares.values():
            if not stack:
                return False
            ultimo = stack.pop()
            if pares[ultimo] != char:
                return False
    
    return len(stack) == 0


def detectar_padroes_pulp(codigo: str) -> Dict[str, bool]:
    """Detecta padrões específicos compatíveis com PuLP"""
    padroes = {
        'compreensao_lista': bool(re.search(r'\[[^\]]+\]', codigo)),
        'funcao_sum': 'sum(' in codigo,
        'funcao_max': 'max(' in codigo,
        'funcao_min': 'min(' in codigo,
        'operadores_relacionais': bool(re.search(r'[<>=!]=?', codigo)),
        'variaveis_indexadas': bool(re.search(r'\w+\[\w+\]', codigo)),
        'referencias_datasets': bool(re.search(r'\w+\[[\"\'].+?[\"\']', codigo))
    }
    
    return padroes


class AnalisadorCodigoGerado:
    """Classe para análise completa do código gerado"""
    
    def __init__(self, codigo: str):
        self.codigo = codigo
        self.normalizado = normalizar_expressao(codigo)
    
    def validar_completo(self) -> Dict[str, any]:
        """Executa validação completa do código"""
        resultado = {
            'valido_python': validar_codigo_python(self.codigo),
            'compativel_pulp': validar_compatibilidade_pulp(self.codigo),
            'parenteses_balanceados': validar_balanceamento_parenteses(self.codigo),
            'variaveis_encontradas': extrair_variaveis(self.codigo),
            'datasets_referenciados': extrair_datasets_referenciados(self.codigo),
            'operadores': contar_operadores(self.codigo),
            'estrutura_loops': analisar_estrutura_loops(self.codigo),
            'padroes_pulp': detectar_padroes_pulp(self.codigo),
            'tamanho_codigo': len(self.codigo),
            'complexidade_estimada': self._calcular_complexidade()
        }
        
        return resultado
    
    def _calcular_complexidade(self) -> int:
        """Calcula complexidade estimada baseada em estruturas presentes"""
        complexidade = 1  # Base
        
        # Adicionar por estruturas
        complexidade += self.codigo.count(' for ') * 2  # Loops
        complexidade += self.codigo.count(' if ') * 1   # Condicionais
        complexidade += self.codigo.count(' and ') * 1  # Operadores lógicos
        complexidade += self.codigo.count(' or ') * 1
        complexidade += len(re.findall(r'\w+\(', self.codigo))  # Chamadas de função
        
        return complexidade


def criar_relatorio_validacao(codigo: str, esperado: str = None) -> str:
    """Cria relatório detalhado de validação"""
    analisador = AnalisadorCodigoGerado(codigo)
    resultado = analisador.validar_completo()
    
    relatorio = f"""
=== RELATÓRIO DE VALIDAÇÃO ===
Código: {codigo[:100]}{'...' if len(codigo) > 100 else ''}

✅ VALIDAÇÕES BÁSICAS:
- Python válido: {resultado['valido_python']}
- Compatível PuLP: {resultado['compativel_pulp']}
- Parênteses balanceados: {resultado['parenteses_balanceados']}

📊 ANÁLISE ESTRUTURAL:
- Variáveis: {', '.join(resultado['variaveis_encontradas']) if resultado['variaveis_encontradas'] else 'Nenhuma'}
- Datasets: {', '.join(resultado['datasets_referenciados']) if resultado['datasets_referenciados'] else 'Nenhum'}
- Complexidade: {resultado['complexidade_estimada']}

🔄 LOOPS & OPERADORES:
- Total FORs: {resultado['estrutura_loops']['total_fors']}
- Aninhados: {resultado['estrutura_loops']['loops_aninhados']}
- Operadores: {resultado['operadores']}

🎯 PADRÕES PULP:
- Compreensão de lista: {resultado['padroes_pulp']['compreensao_lista']}
- Função sum(): {resultado['padroes_pulp']['funcao_sum']}
- Variáveis indexadas: {resultado['padroes_pulp']['variaveis_indexadas']}
"""
    
    if esperado:
        relatorio += f"\n🔍 COMPARAÇÃO:\n- Esperado: {esperado}\n- Obtido: {codigo}\n- Igual: {comparar_expressoes(codigo, esperado)}"
    
    return relatorio
