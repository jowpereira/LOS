"""
🧪 Testes de Integração com Dados Reais - LOS
Testes usando os dados reais de bases_exemplos para validar toda a biblioteca
"""

import pytest
import pandas as pd
import sys
from pathlib import Path
from typing import Dict, Any
from unittest.mock import patch, MagicMock

# Adicionar o path para los
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from los import (
        Expression, ExpressionType, OperationType, Variable, DatasetReference,
        ExpressionService, LOSParser, PuLPTranslator, LOSValidator,
        LOSFileProcessor, ExpressionRequestDTO, ExpressionResponseDTO,
        get_logger, LOSError, ParseError, ValidationError
    )
except ImportError as e:
    print(f"Erro na importação: {e}")
    # Imports alternativos para compatibilidade
    from los.domain.entities.expression import Expression
    from los.domain.value_objects.expression_types import ExpressionType, OperationType, Variable, DatasetReference


class TestLOSComDadosReais:
    """Suite de testes usando dados reais de bases_exemplos"""
    
    @pytest.fixture(scope="class")
    def bases_dados_reais(self):
        """Carrega os dados reais de bases_exemplos"""
        bases_path = Path(__file__).parent.parent / "bases_exemplos"
        
        # Carregar todos os CSVs
        dados = {}
        
        try:
            dados['clientes'] = pd.read_csv(bases_path / "clientes_exemplo.csv")
            dados['produtos'] = pd.read_csv(bases_path / "produtos_exemplo.csv")
            dados['ordens'] = pd.read_csv(bases_path / "ordens_exemplo.csv")
            dados['estoque'] = pd.read_csv(bases_path / "estoque_exemplo.csv")
            dados['custos'] = pd.read_csv(bases_path / "custos_exemplo.csv")
        except FileNotFoundError as e:
            pytest.skip(f"Arquivos de exemplo não encontrados: {e}")
        
        return dados
    
    def test_validacao_dados_bases_exemplos(self, bases_dados_reais):
        """Testa se os dados das bases exemplos estão válidos"""
        # Verificar estrutura dos dados
        assert 'clientes' in bases_dados_reais
        assert 'produtos' in bases_dados_reais
        assert 'ordens' in bases_dados_reais
        assert 'estoque' in bases_dados_reais
        assert 'custos' in bases_dados_reais
        
        # Verificar colunas obrigatórias
        assert 'Codigo_Cliente' in bases_dados_reais['clientes'].columns
        assert 'Produto' in bases_dados_reais['produtos'].columns
        assert 'Custo_Producao' in bases_dados_reais['produtos'].columns
        assert 'Numero_OV' in bases_dados_reais['ordens'].columns
        assert 'Quantidade' in bases_dados_reais['ordens'].columns
        
        # Verificar que não há dados vazios nos campos críticos
        assert not bases_dados_reais['produtos']['Produto'].isnull().any()
        assert not bases_dados_reais['ordens']['Numero_OV'].isnull().any()
    
    def test_criacao_expression_com_dados_reais(self, bases_dados_reais):
        """Testa criação de Expression usando nomes reais dos dados"""
        produtos_df = bases_dados_reais['produtos']
        
        # F02: Create expression, then populate, then validate
        expression = Expression(
            original_text="MINIMIZAR: soma de produtos.Custo_Producao * x[produto] para cada produto",
            expression_type=ExpressionType.OBJECTIVE,
            operation_type=OperationType.MINIMIZE
        )
        
        # Adicionar variáveis baseadas nos produtos reais
        for produto in produtos_df['Produto']:
            var = Variable(name="x", indices=(produto,))
            expression.add_variable(var)
        
        # Adicionar referência ao dataset real
        dataset_ref = DatasetReference(
            dataset_name="produtos",
            column_name="Custo_Producao"
        )
        expression.add_dataset_reference(dataset_ref)
        
        # Validate after populating
        expression.validate()
        
        # Validações
        assert expression.is_valid
        assert expression.is_objective()
        assert len(expression.variables) == len(produtos_df)
        assert "produtos" in expression.get_dataset_names()
    
    def test_variable_com_indices_multiplos_dados_reais(self, bases_dados_reais):
        """Testa variáveis com múltiplos índices usando dados reais"""
        ordens_df = bases_dados_reais['ordens']
        
        # Criar variáveis x[produto, planta] baseadas nos dados reais
        variables = set()
        for _, row in ordens_df.iterrows():
            var = Variable(
                name="x",
                indices=(row['Produto'], row['Planta']),
                variable_type="binary"
            )
            variables.add(var)
        
        # Verificar que as variáveis foram criadas corretamente
        assert len(variables) > 0
        
        # Testar uma variável específica
        var_exemplo = Variable(name="x", indices=("PROD_A", "PLANTA_1"))
        assert var_exemplo.is_indexed
        assert var_exemplo.dimensions == 2
        assert var_exemplo.to_python_code() == "x[PROD_A,PLANTA_1]"
    
    def test_dataset_reference_com_colunas_reais(self, bases_dados_reais):
        """Testa DatasetReference com nomes de colunas reais"""
        # Testar todas as combinações de dataset.coluna dos dados reais
        test_cases = [
            ("produtos", "Custo_Producao"),
            ("produtos", "Margem_Lucro"),
            ("produtos", "Tempo_Producao"),
            ("ordens", "Quantidade"),
            ("estoque", "Quantidade_Disponivel"),
            ("custos", "Valor_Custo")
        ]
        
        for dataset, coluna in test_cases:
            ref = DatasetReference(dataset_name=dataset, column_name=coluna)
            
            # Validar que a referência foi criada corretamente
            assert ref.dataset_name == dataset
            assert ref.column_name == coluna
            
            # Testar conversão para código Python
            expected_code = f"{dataset}.{coluna}"
            assert ref.to_python_code() == expected_code
    
    def test_expression_complexa_com_dados_reais(self, bases_dados_reais):
        """Testa criação de expressão complexa usando múltiplos datasets"""
        produtos_df = bases_dados_reais['produtos']
        ordens_df = bases_dados_reais['ordens']
        
        # F02: Create, populate, validate
        expression = Expression(
            original_text=(
                "MINIMIZAR: soma de produtos.Custo_Producao * x[produto, planta] "
                "+ soma de custos.Valor_Custo * atraso[cliente] "
                "para cada produto, planta, cliente"
            ),
            expression_type=ExpressionType.OBJECTIVE,
            operation_type=OperationType.MINIMIZE
        )
        
        # Adicionar variáveis de produção
        for produto in produtos_df['Produto'].unique():
            for planta in ordens_df['Planta'].unique():
                var_producao = Variable(name="x", indices=(produto, planta))
                expression.add_variable(var_producao)
        
        # Adicionar variáveis de atraso
        for cliente in ordens_df['Codigo_Cliente'].unique():
            var_atraso = Variable(name="atraso", indices=(cliente,))
            expression.add_variable(var_atraso)
        
        # Adicionar referências aos datasets
        refs = [
            DatasetReference("produtos", "Custo_Producao"),
            DatasetReference("custos", "Valor_Custo")
        ]
        for ref in refs:
            expression.add_dataset_reference(ref)
        
        expression.validate()
        
        # Validações
        assert expression.is_valid
        assert len(expression.variables) > 10
        assert len(expression.dataset_references) == 2
        assert expression.complexity.complexity_level in ["MÉDIA", "ALTA", "MUITO_ALTA"]
    
    def test_restricao_capacidade_com_dados_reais(self, bases_dados_reais):
        """Testa criação de restrição de capacidade usando dados reais"""
        estoque_df = bases_dados_reais['estoque']
        
        # F02: No variables in init, add after
        expression = Expression(
            original_text=(
                "soma de x[produto, planta] <= estoque.Quantidade_Disponivel "
                "para cada produto, planta"
            ),
            expression_type=ExpressionType.CONSTRAINT,
            operation_type=OperationType.LESS_EQUAL
        )
        
        for _, row in estoque_df.iterrows():
            var = Variable(name="x", indices=(row['Produto'], row['Planta']))
            expression.add_variable(var)
        
        dataset_ref = DatasetReference("estoque", "Quantidade_Disponivel")
        expression.add_dataset_reference(dataset_ref)
        
        expression.validate()
        
        assert expression.is_valid
        assert expression.is_constraint()
        assert expression.operation_type == OperationType.LESS_EQUAL
    
    @pytest.mark.integration
    def test_fluxo_completo_com_dados_reais(self, bases_dados_reais):
        """Teste de integração completo usando todos os dados reais"""
        
        # F02: Create, populate, validate
        objetivo = Expression(
            original_text="MINIMIZAR: custos totais de produção e atendimento",
            expression_type=ExpressionType.OBJECTIVE,
            operation_type=OperationType.MINIMIZE
        )
        
        # Adicionar variáveis de decisão baseadas nos dados
        produtos = bases_dados_reais['produtos']['Produto'].unique()
        plantas = bases_dados_reais['ordens']['Planta'].unique()
        clientes = bases_dados_reais['clientes']['Codigo_Cliente'].unique()
        
        for produto in produtos:
            for planta in plantas:
                var = Variable(name="x", indices=(produto, planta))
                objetivo.add_variable(var)
        
        for cliente in clientes:
            var = Variable(name="y", indices=(cliente,))
            objetivo.add_variable(var)
        
        referencias = [
            DatasetReference("produtos", "Custo_Producao"),
            DatasetReference("custos", "Valor_Custo"),
            DatasetReference("ordens", "Quantidade")
        ]
        for ref in referencias:
            objetivo.add_dataset_reference(ref)
        
        objetivo.validate()
        
        assert objetivo.is_valid
        assert len(objetivo.variables) >= 20
        assert len(objetivo.dataset_references) == 3
        assert objetivo.complexity.total_complexity > 20
        
        # Serialização
        modelo_dict = objetivo.to_dict()
        assert 'original_text' in modelo_dict
        assert 'variables' in modelo_dict
        assert 'dataset_references' in modelo_dict
        assert modelo_dict['is_valid'] == True
    
    def test_validacao_business_rules_com_dados_reais(self, bases_dados_reais):
        """F02: Testa regras de negócio via validate() — no exceptions from constructor"""
        
        # Cenário 1: Objetivo sem variáveis → invalid via validate()
        expr = Expression(
            original_text="MINIMIZAR: custo fixo",
            expression_type=ExpressionType.OBJECTIVE,
            operation_type=OperationType.MINIMIZE
        )
        expr.validate()
        assert expr.is_valid is False
        assert any("variável" in e for e in expr.validation_errors)
        
        # Cenário 2: Comparação em expressão matemática → invalid
        expr2 = Expression(
            original_text="x <= y",
            expression_type=ExpressionType.MATHEMATICAL,
            operation_type=OperationType.LESS_EQUAL
        )
        expr2.add_variable(Variable(name="x"))
        expr2.add_variable(Variable(name="y"))
        expr2.validate()
        assert expr2.is_valid is False
        assert any("restrições" in e for e in expr2.validation_errors)
    
    def test_metricas_complexidade_dados_reais(self, bases_dados_reais):
        """Testa cálculo de métricas de complexidade com dados reais"""
        ordens_df = bases_dados_reais['ordens']
        
        # Criar expressão com complexidade crescente
        expression = Expression(
            original_text="Expressão complexa com múltiplos componentes",
            expression_type=ExpressionType.MATHEMATICAL
        )
        
        # Adicionar muitas variáveis (simulando problema real)
        for _, row in ordens_df.iterrows():
            var1 = Variable(name="x", indices=(row['Produto'], row['Planta']))
            var2 = Variable(name="y", indices=(row['Codigo_Cliente'],))
            expression.add_variable(var1)
            expression.add_variable(var2)
        
        # Verificar que a complexidade foi calculada
        assert expression.complexity.variable_count > 0
        assert expression.complexity.total_complexity > 0
        assert expression.complexity.complexity_level in [
            "BAIXA", "MÉDIA", "ALTA", "MUITO_ALTA"
        ]
    
    def test_to_pulp_code_com_dados_reais(self, bases_dados_reais):
        """F11: to_pulp_code() removed — test translation via PuLPTranslator"""
        from los.infrastructure.translators.pulp_translator import PuLPTranslator
        
        objetivo = Expression(
            original_text="MINIMIZAR: soma dos custos",
            expression_type=ExpressionType.OBJECTIVE,
            operation_type=OperationType.MINIMIZE
        )
        objetivo.add_variable(Variable(name="x", indices=("dummy",)))
        objetivo.syntax_tree = {'type': 'objective', 'sense': 'minimize', 'expression': {'type': 'var_ref', 'name': 'x'}}
        objetivo.validate()
        
        translator = PuLPTranslator()
        code = translator.translate_expression(objetivo)
        
        assert "import pulp" in code
        assert "prob =" in code
        assert "prob.solve()" in code
