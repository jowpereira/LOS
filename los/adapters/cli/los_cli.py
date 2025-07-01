"""
💻 LOS CLI - Interface de Linha de Comando
Interface CLI profissional para o sistema LOS modularizado
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Optional, List

import click

from ...application.services.expression_service import ExpressionService
from ...application.dto.expression_dto import (
    ExpressionRequestDTO,
    BatchProcessRequestDTO,
    FileProcessRequestDTO,
    ValidationRequestDTO,
    TranslationRequestDTO
)
from ...infrastructure.parsers.los_parser import LOSParser
from ...infrastructure.translators.pulp_translator import PuLPTranslator
from ...infrastructure.validators.los_validator import LOSValidator
from ...domain.repositories.interfaces import (
    IExpressionRepository,
    IGrammarRepository
)
from ...shared.logging.logger import get_logger


# Mock repositories para demonstração
class MockExpressionRepository:
    """Mock repository para demonstração"""
    async def save(self, expression): return expression
    async def find_by_id(self, expr_id): return None
    async def find_by_type(self, expr_type): return []
    async def find_all(self): return []
    async def delete(self, expr_id): return True
    async def count(self): return 0

class MockGrammarRepository:
    """Mock repository para demonstração"""
    async def load_grammar(self, name="los_grammar"): return ""
    async def save_grammar(self, name, content): return True
    async def list_grammars(self): return ["los_grammar"]


class LOSCli:
    """
    Interface CLI principal para o sistema LOS
    Fornece comandos para parsing, validação, tradução e processamento em lote
    """
    
    def __init__(self):
        self._logger = get_logger('adapters.cli')
        self._service = self._initialize_service()
    
    def _initialize_service(self) -> ExpressionService:
        """Inicializa serviços e dependências"""
        try:
            # Repositórios mock
            expr_repo = MockExpressionRepository()
            grammar_repo = MockGrammarRepository()
            
            # Adaptadores
            parser_adapter = LOSParser()
            translator_adapter = PuLPTranslator()
            validator_adapter = LOSValidator()
            
            # Serviço principal
            service = ExpressionService(
                expression_repository=expr_repo,
                grammar_repository=grammar_repo,
                parser_adapter=parser_adapter,
                translator_adapter=translator_adapter,
                validator_adapter=validator_adapter
            )
            
            self._logger.info("Serviços CLI inicializados com sucesso")
            return service
            
        except Exception as e:
            self._logger.error(f"Erro inicializando serviços CLI: {e}")
            click.echo(f"❌ Erro de inicialização: {e}", err=True)
            sys.exit(1)


# Instância global do CLI
cli_instance = LOSCli()


@click.group()
@click.version_option(version="2.0.0", prog_name="LOS CLI")
def los():
    """
    🚀 LOS - Linguagem de Otimização Simples
    
    Sistema modular para análise e tradução de expressões de otimização matemática.
    """
    pass


@los.command()
@click.argument('expression', type=str)
@click.option('--validate/--no-validate', default=True, help='Validar expressão')
@click.option('--save/--no-save', default=False, help='Salvar resultado')
@click.option('--output', '-o', type=str, help='Arquivo de saída')
@click.option('--format', 'output_format', type=click.Choice(['json', 'text']), 
              default='text', help='Formato de saída')
def parse(expression: str, validate: bool, save: bool, output: Optional[str], 
          output_format: str):
    """
    Analisa uma expressão LOS
    
    EXPRESSION: Expressão LOS para analisar
    """
    async def _parse():
        try:
            click.echo("🔍 Analisando expressão...")
            
            request = ExpressionRequestDTO(
                text=expression,
                validate=validate,
                save_result=save
            )
            
            result = await cli_instance._service.parse_expression(request)
            
            if output_format == 'json':
                output_data = {
                    'success': result.success,
                    'expression': {
                        'id': result.id,
                        'original': result.original_text,
                        'python_code': result.python_code,
                        'type': result.expression_type,
                        'operation': result.operation_type,
                        'variables': result.variables,
                        'datasets': result.dataset_references,
                        'complexity': result.complexity,
                        'valid': result.is_valid
                    },
                    'errors': result.errors,
                    'warnings': result.warnings
                }
                
                output_text = json.dumps(output_data, indent=2, ensure_ascii=False)
            else:
                # Formato texto
                output_lines = []
                
                if result.success:
                    output_lines.append("✅ Análise concluída com sucesso!")
                    output_lines.append(f"📝 Texto original: {result.original_text}")
                    output_lines.append(f"🐍 Código Python: {result.python_code}")
                    output_lines.append(f"🏷️  Tipo: {result.expression_type}")
                    output_lines.append(f"⚙️  Operação: {result.operation_type}")
                    output_lines.append(f"📊 Complexidade: {result.complexity.get('level', 'N/A')}")
                    
                    if result.variables:
                        output_lines.append(f"🔢 Variáveis: {', '.join(result.variables)}")
                    
                    if result.dataset_references:
                        output_lines.append(f"📂 Datasets: {', '.join(result.dataset_references)}")
                    
                else:
                    output_lines.append("❌ Análise falhou!")
                    for error in result.errors:
                        output_lines.append(f"   ⚠️  {error}")
                
                if result.warnings:
                    output_lines.append("⚠️  Avisos:")
                    for warning in result.warnings:
                        output_lines.append(f"   📋 {warning}")
                
                output_text = "\n".join(output_lines)
            
            if output:
                Path(output).write_text(output_text, encoding='utf-8')
                click.echo(f"📄 Resultado salvo em: {output}")
            else:
                click.echo(output_text)
            
        except Exception as e:
            click.echo(f"❌ Erro: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_parse())


@los.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--encoding', default='utf-8', help='Codificação do arquivo')
@click.option('--validate/--no-validate', default=True, help='Validar sintaxe')
@click.option('--save/--no-save', default=False, help='Salvar expressões')
@click.option('--output', '-o', type=str, help='Arquivo de relatório')
def process_file(file_path: str, encoding: str, validate: bool, save: bool, 
                output: Optional[str]):
    """
    Processa arquivo .los
    
    FILE_PATH: Caminho do arquivo .los para processar
    """
    async def _process():
        try:
            click.echo(f"📁 Processando arquivo: {file_path}")
            
            request = FileProcessRequestDTO(
                file_path=file_path,
                encoding=encoding,
                validate_syntax=validate,
                save_expressions=save
            )
            
            result = await cli_instance._service.process_file(request)
            
            # Exibir resumo
            click.echo(f"📊 Resumo do processamento:")
            click.echo(f"   📄 Arquivo: {result.file_path}")
            click.echo(f"   🔍 Expressões encontradas: {result.expressions_found}")
            click.echo(f"   ✅ Processadas: {result.expressions_processed}")
            click.echo(f"   ✔️  Válidas: {result.expressions_valid}")
            
            if result.file_errors:
                click.echo(f"   ❌ Erros: {len(result.file_errors)}")
                for error in result.file_errors:
                    click.echo(f"      ⚠️  {error}")
            
            # Gerar relatório detalhado se solicitado
            if output:
                report = {
                    'summary': {
                        'file_path': result.file_path,
                        'expressions_found': result.expressions_found,
                        'expressions_processed': result.expressions_processed,
                        'expressions_valid': result.expressions_valid,
                        'file_errors': result.file_errors
                    },
                    'expressions': [
                        {
                            'original_text': expr.original_text,
                            'python_code': expr.python_code,
                            'type': expr.expression_type,
                            'valid': expr.is_valid,
                            'errors': expr.errors
                        }
                        for expr in result.expressions
                    ]
                }
                
                Path(output).write_text(
                    json.dumps(report, indent=2, ensure_ascii=False),
                    encoding='utf-8'
                )
                click.echo(f"📄 Relatório salvo em: {output}")
            
        except Exception as e:
            click.echo(f"❌ Erro: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_process())


@los.command()
@click.argument('expression', type=str)
@click.option('--target', type=click.Choice(['python', 'pulp']), 
              default='pulp', help='Linguagem/framework alvo')
@click.option('--output', '-o', type=str, help='Arquivo de saída')
def translate(expression: str, target: str, output: Optional[str]):
    """
    Traduz expressão LOS para linguagem alvo
    
    EXPRESSION: Expressão LOS para traduzir
    """
    async def _translate():
        try:
            click.echo(f"🔄 Traduzindo para {target}...")
            
            # Criar instância do tradutor diretamente para demonstração
            translator = PuLPTranslator()
            
            request = TranslationRequestDTO(
                expression_text=expression,
                target_language="python",
                target_framework=target
            )
            
            result = await translator.translate(request)
            
            if result.translation_success:
                click.echo("✅ Tradução concluída!")
                click.echo(f"📝 Expressão original:")
                click.echo(f"   {result.source_text}")
                click.echo(f"🐍 Código {result.target_framework}:")
                click.echo(result.translated_code)
                
                if output:
                    Path(output).write_text(result.translated_code, encoding='utf-8')
                    click.echo(f"📄 Código salvo em: {output}")
            else:
                click.echo("❌ Tradução falhou!")
                for error in result.translation_errors:
                    click.echo(f"   ⚠️  {error}")
            
        except Exception as e:
            click.echo(f"❌ Erro: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_translate())


@los.command()
@click.argument('expression', type=str)
@click.option('--rules', type=str, help='Regras específicas (separadas por vírgula)')
def validate(expression: str, rules: Optional[str]):
    """
    Valida expressão LOS
    
    EXPRESSION: Expressão LOS para validar
    """
    async def _validate():
        try:
            click.echo("✅ Validando expressão...")
            
            # Criar instância do validador diretamente
            validator = LOSValidator()
            
            validation_rules = rules.split(',') if rules else None
            
            request = ValidationRequestDTO(
                expression_text=expression,
                validation_rules=validation_rules
            )
            
            result = await validator.validate(request)
            
            if result.is_valid:
                click.echo("✅ Expressão válida!")
            else:
                click.echo("❌ Expressão inválida!")
                
                for error in result.errors:
                    click.echo(f"   ❌ {error}")
            
            if result.warnings:
                click.echo("⚠️  Avisos:")
                for warning in result.warnings:
                    click.echo(f"   📋 {warning}")
            
            click.echo(f"🔧 Regras aplicadas: {', '.join(result.applied_rules)}")
            
        except Exception as e:
            click.echo(f"❌ Erro: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_validate())


@los.command()
def stats():
    """Exibe estatísticas do sistema"""
    async def _stats():
        try:
            click.echo("📊 Compilando estatísticas...")
            
            result = await cli_instance._service.get_statistics()
            
            click.echo("📈 Estatísticas do Sistema LOS:")
            click.echo(f"   📄 Total de expressões: {result.total_expressions}")
            click.echo(f"   📊 Taxa de sucesso: {result.parsing_success_rate:.1f}%")
            click.echo(f"   🧮 Complexidade média: {result.average_complexity:.1f}")
            
            if result.expressions_by_type:
                click.echo("📋 Por tipo:")
                for expr_type, count in result.expressions_by_type.items():
                    click.echo(f"   {expr_type}: {count}")
            
            if result.most_used_variables:
                click.echo("🔢 Variáveis mais usadas:")
                for var in result.most_used_variables[:5]:
                    click.echo(f"   {var['name']}: {var['count']} vezes")
            
        except Exception as e:
            click.echo(f"❌ Erro: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_stats())


@los.command()
@click.option('--rules', is_flag=True, help='Listar regras de validação disponíveis')
@click.option('--languages', is_flag=True, help='Listar linguagens de tradução suportadas')
def info(rules: bool, languages: bool):
    """Exibe informações do sistema"""
    try:
        if rules:
            validator = LOSValidator()
            available_rules = validator.get_available_rules()
            
            click.echo("🔧 Regras de validação disponíveis:")
            for rule_name in available_rules:
                rule_info = validator.get_rule_info(rule_name)
                if rule_info:
                    click.echo(f"   {rule_name}: {rule_info['description']} "
                             f"({rule_info['severity']})")
        
        elif languages:
            translator = PuLPTranslator()
            supported = translator.get_supported_languages()
            
            click.echo("🗣️  Linguagens de tradução suportadas:")
            for lang in supported:
                click.echo(f"   {lang}")
        
        else:
            click.echo("ℹ️  Sistema LOS - Linguagem de Otimização Simples")
            click.echo("   Versão: 2.0.0")
            click.echo("   Arquitetura: Clean Architecture + Hexagonal")
            click.echo("   Parser: Lark-based")
            click.echo("   Frameworks suportados: PuLP")
            click.echo("")
            click.echo("Use --help com qualquer comando para mais informações.")
    
    except Exception as e:
        click.echo(f"❌ Erro: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    los()
