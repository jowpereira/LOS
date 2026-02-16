"""
🔄 PuLP Translator - Tradutor para biblioteca PuLP
Converte expressões LOS v3 para código Python compatível com PuLP
"""

from typing import Dict, List, Any, Optional
import pulp
import re

from ...application.interfaces.adapters import ITranslatorAdapter
from ...application.dto.expression_dto import (
    TranslationRequestDTO,
    TranslationResponseDTO
)
from ...domain.entities.expression import Expression
from ...domain.value_objects.expression_types import (
    ExpressionType,
    OperationType
)
from ...shared.errors.exceptions import TranslationError
from ...shared.logging.logger import get_logger


class PuLPTranslator(ITranslatorAdapter):
    """
    Tradutor especializado para biblioteca PuLP
    Converte AST do LOS v3 para código Python/PuLP
    """
    
    __version__ = "3.1.0"  # F19
    
    def __init__(self):
        self.target_language = "python"
        self.target_framework = "pulp"
        self._logger = get_logger('translators.pulp')
    
    # --- ITranslatorAdapter compliance ---
    
    def translate(self, request: TranslationRequestDTO) -> TranslationResponseDTO:
        """
        M2: DTO-based translation — returns guidance to use translate_expression().
        Kept for ITranslatorAdapter ABC compliance.
        """
        return TranslationResponseDTO(
            source_text=request.expression_text or "",
            translated_code="# Use translate_expression() com objeto Expression parsed",
            target_language=self.target_language,
            target_framework=self.target_framework,
            translation_success=False,
            translation_errors=["Tradução via DTO não suportada em v3. Use ExpressionService."]
        )
            
    def translate_expression(self, expression: Expression) -> str:
        """
        F03/F06: Traduz entidade Expression (com AST) para código Python/PuLP completo.
        Detecta objective sense ANTES de criar o problema.
        """
        try:
            if not expression.syntax_tree:
                 if expression.original_text:
                     return f"# AST não disponível. Texto original: {expression.original_text}"
                 return "# Erro: Expressão vazia e sem AST"
            
            ast = expression.syntax_tree
            
            # F06: Detect objective sense from AST BEFORE generating code
            sense = self._detect_sense(ast)
            sense_str = "pulp.LpMaximize" if sense == "max" else "pulp.LpMinimize"
            
            code = []
            
            # Header
            code.append("import pulp")
            code.append("import pandas as pd")
            code.append("import numpy as np")
            code.append("")
            
            model_name = self._sanitize_name(ast.get('name', 'LOS_Model'))
            code.append("# --- Inicialização do Modelo ---")
            code.append(f"prob = pulp.LpProblem('{model_name}', {sense_str})")
            code.append("")
            
            # Process statements
            node_type = ast.get('type')
            
            if node_type == 'model':
                statements = ast.get('statements', [])
                for stmt in statements:
                    stmt_code = self._visit(stmt)
                    if stmt_code:
                        code.append(stmt_code)
            else:
                 code.append(self._visit(ast))
            
            # Footer
            code.append("")
            code.append("# --- Resolução ---")
            code.append("prob.solve()")
            code.append("")
            code.append("# --- Resultados ---")
            code.append("print(f'Status: {pulp.LpStatus[prob.status]}')")
            code.append("if prob.status == pulp.LpStatusOptimal:")
            code.append("    print(f'Objective Value: {pulp.value(prob.objective)}')")
            code.append("    for v in prob.variables():")
            code.append("        if v.varValue is not None and abs(v.varValue) > 1e-5:")
            code.append("            print(f'{v.name} = {v.varValue}')")
            
            full_code = "\n".join(code)
            expression.python_code = full_code
            return full_code
            
        except Exception as e:
            self._logger.error(f"Erro traduzindo expressão: {e}")
            raise TranslationError(f"Erro de tradução: {str(e)}", expression.original_text, e)
            
    def get_supported_languages(self) -> List[str]:
        return ["python"]

    # --- Internal helpers ---

    def _detect_sense(self, ast: Dict) -> str:
        """
        F06: Walk AST to find objective and detect sense (min/max).
        Returns 'min' or 'max'. Default: 'min'.
        """
        if ast.get('type') == 'objective':
            sense = str(ast.get('sense', 'min')).lower()
            return 'max' if sense in ['max', 'maximize', 'maximizar'] else 'min'
        
        if ast.get('type') == 'model':
            for stmt in ast.get('statements', []):
                if isinstance(stmt, dict) and stmt.get('type') == 'objective':
                    sense = str(stmt.get('sense', 'min')).lower()
                    return 'max' if sense in ['max', 'maximize', 'maximizar'] else 'min'
        
        return 'min'

    def _sanitize_name(self, name: str) -> str:
        """Sanitiza nomes para evitar code injection"""
        if not name: return ""
        clean = re.sub(r'[^a-zA-Z0-9_]', '', str(name))
        if not clean: return "var_unnamed"
        if clean[0].isdigit():
            clean = "_" + clean
        return clean

    # --- Visitor Pattern ---
    
    def _visit(self, node: Any) -> str:
        if isinstance(node, dict):
            node_type = node.get('type')
            if not node_type:
                return str(node)
                
            method_name = f"_visit_{node_type}"
            visitor = getattr(self, method_name, self._visit_default)
            return visitor(node)
        elif isinstance(node, list):
            return ", ".join([self._visit(x) for x in node])
        else:
            return str(node)

    def _visit_default(self, node):
        return f"# TODO: Implement visitor for node type '{node.get('type')}'"

    # --- Specific Visitors ---

    def _visit_import(self, node):
        path = node.get('path', '')
        safe_path = path.replace("'", "").replace('"', "")
        
        # F08: Use a sanitized dataset variable name derived from the filename
        if safe_path.endswith('.csv'):
            # Extract dataset name from filename (e.g., "vendas.csv" -> "vendas")
            import os
            basename = os.path.splitext(os.path.basename(safe_path))[0]
            var_name = self._sanitize_name(basename)
            return f"{var_name} = pd.read_csv('{safe_path}')"
        return f"# Import não suportado: {safe_path}"

    def _visit_set(self, node):
        name = self._sanitize_name(node['name'])
        value = node.get('value')
        
        if not value:
            return f"{name} = [] # Set indefinido"
            
        val_type = value.get('type')
        if val_type == 'set_literal':
            elements = [self._visit_set_element(e) for e in value.get('elements', [])]
            return f"{name} = [{', '.join(elements)}]"
        elif val_type == 'set_range':
            start = self._visit(value.get('start'))
            end = self._visit(value.get('end'))
            step = self._visit(value.get('step')) if 'step' in value else None
            step_str = f", {step}" if step else ""
            return f"{name} = list(range({start}, {end} + 1{step_str}))"
        elif val_type == 'set_ref':
            return f"{name} = {self._visit(value)}"
        elif val_type == 'set_op':
            return f"{name} = {self._visit_set_op(value)}"
        elif val_type == 'set_filter':
            source = self._sanitize_name(value.get('source'))
            expr_node = value.get('expression')
            iterator = self._visit(expr_node)
            condition = value.get('condition')
            cond_str = f" if {self._visit(condition)}" if condition else ""
            return f"{name} = [{iterator} for {iterator} in {source}{cond_str}]"
            
        return f"{name} = [] # Tipo de set desconhecido: {val_type}"

    def _visit_set_element(self, node):
        """Helper to handle set elements, quoting strings/identifiers"""
        if isinstance(node, dict):
            if node['type'] == 'var_ref':
                return f"'{node['name']}'"
            elif node['type'] == 'string':
                return f"'{node['value']}'"
            return self._visit(node)
        return str(node)

    def _visit_set_ref(self, node):
        return self._sanitize_name(node['name'])

    def _visit_set_op(self, node):
        left = self._visit(node.get('left'))
        op = node.get('op')
        right = self._visit(node.get('right'))
        
        if op == '*':
             return f"[(x,y) for x in {left} for y in {right}]"
        
        op_map = {
            '|': '|', 'union': '|', 'uniao': '|',
            '&': '&', 'inter': '&', 'intersection': '&',
            '\\': '-', 'diff': '-', 'diferenca': '-',
        }
        
        py_op = op_map.get(op, '|')
        return f"set({left}) {py_op} set({right})"

    def _visit_param(self, node):
        name = self._sanitize_name(node['name'])
        value = node.get('value')
        indices = node.get('indices')
        
        if value:
             val_str = self._visit(value)
             if indices:
                 idx_sets = [(self._sanitize_name(f"i_{k}"), self._sanitize_name(idx))
                             for k, idx in enumerate(indices)]
                 
                 # Build nested dict comprehension from inside out
                 # For [Plantas, Produtos]: {i_0: {i_1: 0 for i_1 in Produtos} for i_0 in Plantas}
                 inner = val_str
                 for loop_var, idx_set in reversed(idx_sets):
                     inner = f"{{{loop_var}: {inner} for {loop_var} in {idx_set}}}"
                 
                 return f"{name} = {inner}"
             return f"{name} = {val_str}"
        return f"{name} = {{}} # Param undefined"

    def _visit_var(self, node):
        name = self._sanitize_name(node['name'])
        var_type = node.get('var_type', 'continuous')
        indices = node.get('indices', [])
        bounds = node.get('bounds', {})
        
        # Map type
        vtype_str = str(var_type).lower()
        if 'int' in vtype_str: cat = 'pulp.LpInteger'
        elif 'bin' in vtype_str: cat = 'pulp.LpBinary'
        else: cat = 'pulp.LpContinuous'
        
        # F07: Default bounds depend on category
        # Binary: [0, 1] (PuLP handles automatically)
        # Integer/Continuous with no explicit bounds: lowBound=0 (standard LP convention)
        # Documentation comment added for clarity
        if cat == 'pulp.LpBinary':
            low = "0"
            up = "1"
        else:
            low = "0"  # LP convention: non-negative by default
            up = "None"
        
        if bounds:
            if bounds.get('lower') is not None: low = self._visit(bounds['lower'])
            if bounds.get('upper') is not None: up = self._visit(bounds['upper'])
            if bounds.get('equal') is not None:
                val = self._visit(bounds['equal'])
                low = val
                up = val
            if bounds.get('free'):
                # F07: Explicit free variable: x can be negative
                low = "None"
                up = "None"

        if indices:
            idx_list = [self._sanitize_name(str(i)) for i in indices]
            idx_args = ", ".join(idx_list)
            return (f"{name} = pulp.LpVariable.dicts('{name}', "
                    f"({idx_args}), lowBound={low}, upBound={up}, cat={cat})")
        else:
            return (f"# F07: lowBound={low} (LP convention, use 'free' for unrestricted)\n"
                    f"{name} = pulp.LpVariable('{name}', "
                    f"lowBound={low}, upBound={up}, cat={cat})")

    def _visit_objective(self, node):
        # F06: Sense is already set at problem creation time
        # No need for post-hoc prob.sense override
        expr = self._visit(node.get('expression'))
        return f"prob += {expr}, 'Objective'"

    def _visit_constraint_block(self, node):
        constraints = node.get('constraints', [])
        return "\n".join([self._visit(c) for c in constraints])

    def _visit_constraint(self, node):
        expr_node = node.get('expression')
        name = self._sanitize_name(node.get('name', ''))
        loops = node.get('loops')
        
        comparison = self._visit(expr_node)
        
        if loops:
            lines = []
            indent = ""
            loop_vars = []
            
            for loop in loops:
                loop_var = self._sanitize_name(loop.get('var'))  # F16
                loop_in = self._visit(loop.get('source'))
                condition = loop.get('condition')
                cond_str = f" if {self._visit(condition)}" if condition else ""
                
                lines.append(f"{indent}for {loop_var} in {loop_in}{cond_str}:")
                indent += "    "
                loop_vars.append(loop_var)
            
            # Dynamic naming: append loop vars to name to ensure uniqueness
            # e.g. f'atendimento_{c}_{j}'
            name_expr = ""
            if name:
                if loop_vars:
                    suffix = "_".join([f"{{{v}}}" for v in loop_vars])
                    name_expr = f", f'{name}_{suffix}'"
                else:
                    name_expr = f", '{name}'"
            
            lines.append(f"{indent}prob += {comparison}{name_expr}")
            return "\n".join(lines)
        else:
            name_part = f", '{name}'" if name else ""
            return f"prob += {comparison}{name_part}"

    def _visit_comparison(self, node):
        left = self._visit(node['left'])
        right = self._visit(node['right'])
        op = str(node['op'])
        
        op_map = {
            'le': '<=', 'leq': '<=', '<=': '<=',
            'ge': '>=', 'geq': '>=', '>=': '>=',
            'eq': '==', '==': '==', '=': '=='
        }
        
        if op in ['<', 'lt']: py_op = '<='
        elif op in ['>', 'gt']: py_op = '>='
        elif op in ['!=', 'ne']: 
             return f"# ERRO: Operador != não suportado em LP ({left} != {right})"
        else:
             py_op = op_map.get(op, '==')
        
        return f"{left} {py_op} {right}"

    def _visit_binary_op(self, node):
        left = self._visit(node['left'])
        right = self._visit(node['right'])
        op = node['op']
        return f"({left} {op} {right})"
    
    def _visit_var_ref(self, node):
        name = self._sanitize_name(node['name'])
        indices = node.get('indices', [])
        if indices:
            idx_str = "][".join([self._visit(i) for i in indices])
            return f"{name}[{idx_str}]"
        return name

    def _visit_indexed_var(self, node):
        return self._visit_var_ref(node)

    def _visit_dataset_col(self, node):
        """F08: Visit dataset.column references"""
        dataset = self._sanitize_name(node.get('dataset', ''))
        col = self._sanitize_name(node.get('col', ''))
        return f"{dataset}['{col}']"

    def _visit_sum(self, node):
        expression = self._visit(node.get('expression'))
        loops = node.get('loops', [])
        
        # F10: sum() without loop — expression must be iterable context
        if not loops:
            # If expression looks like a variable reference, wrap as list for safety
            return f"pulp.lpSum([{expression}])"
            
        loop_comprehension = []
        for loop in loops:
            var = self._sanitize_name(loop.get('var'))  # F16
            source = self._visit(loop.get('source'))
            condition = loop.get('condition')
            cond_str = f" if {self._visit(condition)}" if condition else ""
            loop_comprehension.append(f"for {var} in {source}{cond_str}")
        
        comp_str = " ".join(loop_comprehension)
        return f"pulp.lpSum({expression} {comp_str})"

    def _visit_prod(self, node):
        expression = self._visit(node.get('expression'))
        loops = node.get('loops', [])
        
        loop_comprehension = []
        for loop in loops:
            var = self._sanitize_name(loop.get('var'))  # F16
            source = self._visit(loop.get('source'))
            loop_comprehension.append(f"for {var} in {source}")
            
        comp_str = " ".join(loop_comprehension)
        return f"# PRODUCT (Non-Linear): \n# warning: prod({expression} {comp_str})" 

    def _visit_function(self, node):
        name = node.get('name')
        args = [self._visit(a) for a in node.get('args', [])]
        arg_str = ", ".join(args)
        if name in ['min', 'max', 'abs']:
             return f"{name}({arg_str})"
        return f"math.{name}({arg_str})"

    def _visit_if(self, node):
        cond = self._visit(node.get('condition'))
        then_expr = self._visit(node.get('then'))
        else_expr = self._visit(node.get('else'))
        return f"({then_expr} if {cond} else {else_expr})"

    def _visit_logic_op(self, node):
        op = node.get('op')
        if 'expr' in node:
             return f"not ({self._visit(node['expr'])})"
        left = self._visit(node.get('left'))
        right = self._visit(node.get('right'))
        return f"({left} {op} {right})"

    def _visit_number(self, node):
        val = node.get('value')
        if val == int(val):
            return str(int(val))
        return str(val)
        
    def _visit_string(self, node):
        return f"'{node.get('value')}'"
