"""
🔄 PuLP Translator - Tradutor para biblioteca PuLP
Converte expressões LOS para código Python compatível com PuLP
"""

from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod

from ...application.interfaces.adapters import ITranslatorAdapter
from ...application.dto.expression_dto import (
    TranslationRequestDTO,
    TranslationResponseDTO
)
from ...domain.entities.expression import Expression
from ...domain.value_objects.expression_types import (
    ExpressionType,
    OperationType,
    Variable,
    DatasetReference
)
from ...shared.errors.exceptions import TranslationError
from ...shared.logging.logger import get_logger


class BaseTranslator(ABC):
    """Classe base para tradutores"""
    
    def __init__(self, target_language: str, target_framework: str):
        self.target_language = target_language
        self.target_framework = target_framework
        self._logger = get_logger(f'translators.{target_framework}')
    
    @abstractmethod
    def translate_objective(self, expression: Expression) -> str:
        """Traduz expressão de objetivo"""
        pass
    
    @abstractmethod  
    def translate_constraint(self, expression: Expression) -> str:
        """Traduz restrição"""
        pass
    
    @abstractmethod
    def translate_mathematical(self, expression: Expression) -> str:
        """Traduz expressão matemática"""
        pass
    
    @abstractmethod
    def generate_variable_declarations(self, variables: List[Variable]) -> str:
        """Gera declarações de variáveis"""
        pass


class PuLPTranslator(BaseTranslator, ITranslatorAdapter):
    """
    Tradutor especializado para biblioteca PuLP
    Converte expressões LOS para código Python/PuLP
    """
    
    def __init__(self):
        super().__init__("python", "pulp")
        self._variable_declarations: Dict[str, str] = {}
        self._dataset_imports: List[str] = []
    
    async def translate(self, request: TranslationRequestDTO) -> TranslationResponseDTO:
        """
        Traduz expressão para código PuLP
        
        Args:
            request: Requisição de tradução
            
        Returns:
            Código PuLP gerado
        """
        try:
            self._logger.info(f"Iniciando tradução para {self.target_framework}")
            
            # Para este exemplo, vamos assumir que temos a expressão
            # Em uma implementação real, precisaríamos buscar por ID ou fazer parsing
            if request.expression_text:
                # Simular parsing básico para demonstração
                expression = self._create_mock_expression(request.expression_text)
            else:
                raise TranslationError(
                    message="Texto da expressão ou ID deve ser fornecido",
                    source_expression=""
                )
            
            # Traduzir baseado no tipo
            if expression.expression_type == ExpressionType.OBJECTIVE:
                translated_code = self.translate_objective(expression)
            elif expression.expression_type == ExpressionType.CONSTRAINT:
                translated_code = self.translate_constraint(expression)
            else:
                translated_code = self.translate_mathematical(expression)
            
            # Adicionar imports e declarações se necessário
            full_code = self._build_complete_code(translated_code, expression)
            
            self._logger.info("Tradução concluída com sucesso")
            
            return TranslationResponseDTO(
                source_text=request.expression_text or "",
                translated_code=full_code,
                target_language=self.target_language,
                target_framework=self.target_framework,
                translation_success=True,
                translation_errors=[]
            )
            
        except Exception as e:
            self._logger.error(f"Erro durante tradução: {e}")
            return TranslationResponseDTO(
                source_text=request.expression_text or "",
                translated_code="",
                target_language=self.target_language,
                target_framework=self.target_framework,
                translation_success=False,
                translation_errors=[str(e)]
            )
    
    def get_supported_languages(self) -> List[str]:
        """Retorna linguagens suportadas"""
        return ["python"]
    
    def translate_objective(self, expression: Expression) -> str:
        """
        Traduz objetivo de otimização para PuLP
        
        Args:
            expression: Expressão de objetivo
            
        Returns:
            Código PuLP para objetivo
        """
        try:
            if expression.operation_type == OperationType.MINIMIZE:
                return f"prob += {expression.python_code}, \"Objective Function\""
            elif expression.operation_type == OperationType.MAXIMIZE:
                return f"prob += {expression.python_code}, \"Objective Function\""
            else:
                raise TranslationError(
                    message=f"Operação {expression.operation_type} não suportada para objetivos",
                    source_expression=expression.original_text
                )
        
        except Exception as e:
            raise TranslationError(
                message=f"Erro traduzindo objetivo: {str(e)}",
                source_expression=expression.original_text,
                original_exception=e
            )
    
    def translate_constraint(self, expression: Expression) -> str:
        """
        Traduz restrição para PuLP
        
        Args:
            expression: Expressão de restrição
            
        Returns:
            Código PuLP para restrição
        """
        try:
            # Gerar nome único para a restrição
            constraint_name = f"constraint_{len(self._variable_declarations) + 1}"
            
            return f"prob += {expression.python_code}, \"{constraint_name}\""
        
        except Exception as e:
            raise TranslationError(
                message=f"Erro traduzindo restrição: {str(e)}",
                source_expression=expression.original_text,
                original_exception=e
            )
    
    def translate_mathematical(self, expression: Expression) -> str:
        """
        Traduz expressão matemática
        
        Args:
            expression: Expressão matemática
            
        Returns:
            Código Python da expressão
        """
        return expression.python_code
    
    def generate_variable_declarations(self, variables: List[Variable]) -> str:
        """
        Gera declarações de variáveis PuLP
        
        Args:
            variables: Lista de variáveis
            
        Returns:
            Código de declaração das variáveis
        """
        declarations = []
        declarations.append("# Declaração de variáveis")
        
        for var in variables:
            if var.is_indexed:
                # Variável indexada - criar dicionário
                indices_str = ", ".join(f"'{idx}'" for idx in var.indices)
                declarations.append(
                    f"{var.name} = pulp.LpVariable.dicts('{var.name}', "
                    f"({indices_str}), cat='Continuous')"
                )
            else:
                # Variável escalar
                declarations.append(
                    f"{var.name} = pulp.LpVariable('{var.name}', cat='Continuous')"
                )
        
        return "\n".join(declarations)
    
    def generate_dataset_imports(self, dataset_references: List[DatasetReference]) -> str:
        """
        Gera imports para datasets
        
        Args:
            dataset_references: Referências aos datasets
            
        Returns:
            Código de import/carregamento dos datasets
        """
        imports = []
        imports.append("# Carregamento de datasets")
        imports.append("import pandas as pd")
        
        # Agrupar por dataset
        datasets = set(ref.dataset_name for ref in dataset_references)
        
        for dataset in datasets:
            imports.append(
                f"{dataset} = pd.read_csv('bases_exemplos/{dataset}_exemplo.csv')"
            )
        
        return "\n".join(imports)
    
    def _build_complete_code(self, translated_code: str, expression: Expression) -> str:
        """
        Constrói código completo com imports e declarações
        
        Args:
            translated_code: Código traduzido da expressão
            expression: Expressão original
            
        Returns:
            Código completo
        """
        code_parts = []
        
        # Imports básicos
        code_parts.append("import pulp")
        code_parts.append("import pandas as pd")
        code_parts.append("import math")
        code_parts.append("")
        
        # Carregamento de datasets se necessário
        if expression.dataset_references:
            dataset_code = self.generate_dataset_imports(list(expression.dataset_references))
            code_parts.append(dataset_code)
            code_parts.append("")
        
        # Criar problema de otimização se for objetivo
        if expression.expression_type == ExpressionType.OBJECTIVE:
            if expression.operation_type == OperationType.MINIMIZE:
                code_parts.append("# Criar problema de minimização")
                code_parts.append("prob = pulp.LpProblem('LOS_Problem', pulp.LpMinimize)")
            else:
                code_parts.append("# Criar problema de maximização")
                code_parts.append("prob = pulp.LpProblem('LOS_Problem', pulp.LpMaximize)")
            code_parts.append("")
        
        # Declaração de variáveis se necessário
        if expression.variables:
            var_code = self.generate_variable_declarations(list(expression.variables))
            code_parts.append(var_code)
            code_parts.append("")
        
        # Código traduzido principal
        if expression.expression_type == ExpressionType.OBJECTIVE:
            code_parts.append("# Função objetivo")
        elif expression.expression_type == ExpressionType.CONSTRAINT:
            code_parts.append("# Restrição")
        else:
            code_parts.append("# Expressão matemática")
        
        code_parts.append(translated_code)
        
        # Adicionar resolução se for problema completo
        if expression.expression_type in [ExpressionType.OBJECTIVE, ExpressionType.CONSTRAINT]:
            code_parts.append("")
            code_parts.append("# Resolver o problema")
            code_parts.append("prob.solve()")
            code_parts.append("")
            code_parts.append("# Verificar status da solução")
            code_parts.append("print(f'Status: {pulp.LpStatus[prob.status]}')")
            code_parts.append("")
            code_parts.append("# Exibir valores das variáveis")
            code_parts.append("if prob.status == pulp.LpStatusOptimal:")
            code_parts.append("    for variable in prob.variables():")
            code_parts.append("        print(f'{variable.name} = {variable.varValue}')")
        
        return "\n".join(code_parts)
    
    def _create_mock_expression(self, text: str) -> Expression:
        """
        Cria expressão mock para demonstração
        Em implementação real, usaria o parser
        """
        # Detectar tipo básico
        text_upper = text.upper()
        
        if text_upper.startswith('MINIMIZAR:'):
            expr_type = ExpressionType.OBJECTIVE
            op_type = OperationType.MINIMIZE
        elif text_upper.startswith('MAXIMIZAR:'):
            expr_type = ExpressionType.OBJECTIVE
            op_type = OperationType.MAXIMIZE
        elif any(op in text for op in ['<=', '>=', '==', '!=', '<', '>', '=']):
            expr_type = ExpressionType.CONSTRAINT
            op_type = OperationType.LESS_EQUAL
        else:
            expr_type = ExpressionType.MATHEMATICAL
            op_type = OperationType.ADDITION
        
        return Expression(
            original_text=text,
            python_code=text.replace('MINIMIZAR:', '').replace('MAXIMIZAR:', '').strip(),
            expression_type=expr_type,
            operation_type=op_type
        )
