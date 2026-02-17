"""Interface CLI do sistema LOS."""

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
from ...infrastructure.repositories.json_repository import JsonExpressionRepository
from ...infrastructure.repositories.in_memory import InMemoryGrammarRepository
from ...adapters.file.los_file_processor import LOSFileProcessor
from ...shared.logging.logger import get_logger


class LOSCli:
    """Interface CLI principal."""
    
    def __init__(self):
        self._logger = get_logger('adapters.cli')
        self._service = self._initialize_service()
    
    def _initialize_service(self) -> ExpressionService:
        """Inicializa serviços com implementações reais."""
        try:
            # Repositories
            # Persistência em JSON na home do usuário
            expr_repo = JsonExpressionRepository()
            
            # Gramática pode manter em memória (carrega do arquivo .lark se disponível)
            # Como o parser já carrega o arquivo, o repo de gramática é secundário aqui
            grammar_repo = InMemoryGrammarRepository()
            
            # Adapters
            parser_adapter = LOSParser()
            translator_adapter = PuLPTranslator()
            validator_adapter = LOSValidator()
            file_adapter = LOSFileProcessor()
            
            # Service
            service = ExpressionService(
                expression_repository=expr_repo,
                grammar_repository=grammar_repo,
                parser_adapter=parser_adapter,
                translator_adapter=translator_adapter,
                validator_adapter=validator_adapter,
                file_adapter=file_adapter
            )
            
            self._logger.info("Serviços CLI inicializados com sucesso (Mode: Real)")
            return service
            
        except Exception as e:
            self._logger.error(f"Erro inicializando serviços CLI: {e}")
            click.echo(f"❌ Erro de inicialização: {e}", err=True)
            sys.exit(1)


# Instância global do CLI
cli_instance = LOSCli()


@click.group()
@click.version_option(version="2.1.0", prog_name="LOS CLI")
def los():
    """Sistema modular para análise e tradução de expressões."""
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
    """Analisa uma expressão LOS."""
    async def _parse():
        try:
            click.echo("🔍 Analisando expressão...")
            
            request = ExpressionRequestDTO(
                text=expression,
                validate=validate,
                save_result=save
            )
            
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, cli_instance._service.parse_expression, request)
            
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
                    
                    if save and result.id:
                        output_lines.append(f"💾 Salvo no DB com ID: {result.id}")
                    
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
    """Processa arquivo .los."""
    async def _process():
        try:
            click.echo(f"📁 Processando arquivo: {file_path}")
            
            request = FileProcessRequestDTO(
                file_path=file_path,
                encoding=encoding,
                validate_syntax=validate,
                save_expressions=save
            )
            
            # O serviço faz parsing síncrono internamente na v3, mas vamos manter async wrapper se necessário
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, cli_instance._service.process_file, request)
            
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
    """Traduz expressão LOS para linguagem alvo."""
    async def _translate():
        try:
            click.echo(f"🔄 Traduzindo para {target}...")
            
            # Usar o serviço para garantir fluxo correto de parsing -> entity -> translation
            request = ExpressionRequestDTO(
                text=expression,
                validate=True,
                save_result=False
            )
            
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, cli_instance._service.parse_expression, request)
            
            if result.success and result.is_valid:
                click.echo("✅ Tradução concluída!")
                click.echo(f"📝 Expressão original:")
                click.echo(f"   {result.original_text}")
                click.echo(f"🐍 Código {target}:")
                click.echo(result.python_code)
                
                if output:
                    Path(output).write_text(result.python_code, encoding='utf-8')
                    click.echo(f"📄 Código salvo em: {output}")
            else:
                click.echo("❌ Tradução falhou (Expressão inválida)!")
                for error in result.errors:
                    click.echo(f"   ⚠️  {error}")
            
        except Exception as e:
            click.echo(f"❌ Erro: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_translate())


@los.command()
@click.argument('expression', type=str)
def validate(expression: str):
    """Valida expressão LOS."""
    async def _validate():
        try:
            click.echo("✅ Validando expressão...")
            
            # Usar o serviço completo
            request = ExpressionRequestDTO(
                text=expression,
                validate=True,
                save_result=False
            )
            
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, cli_instance._service.parse_expression, request)
            
            if result.is_valid:
                click.echo("✅ Expressão válida!")
                click.echo(f"🏷️  Tipo: {result.expression_type}")
                click.echo(f"📊 Complexidade: {result.complexity.get('level', 'N/A')}")
            else:
                click.echo("❌ Expressão inválida!")
                
                for error in result.validation_errors:
                    click.echo(f"   ❌ {error}")
            
            if result.warnings:
                click.echo("⚠️  Avisos:")
                for warning in result.warnings:
                    click.echo(f"   📋 {warning}")
            
        except Exception as e:
            click.echo(f"❌ Erro: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_validate())


@los.command()
def stats():
    """Exibe estatísticas do sistema."""
    async def _stats():
        try:
            click.echo("📊 Compilando estatísticas...")
            
            # Agora busca do repo JSON real
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, cli_instance._service.get_statistics)
            
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
    """Exibe informações do sistema."""
    try:
        # Acessa adaptadores via serviço protegido (embora _hacky, é prático para CLI info)
        # Numa arquitetura pura, o Service deveria expor metadados.
        if rules:
            validator = cli_instance._service._validator_adapter
            available_rules = validator.get_available_rules()
            
            click.echo("🔧 Regras de validação disponíveis:")
            for rule_name in available_rules:
                rule_info = validator.get_rule_info(rule_name)
                if rule_info:
                    click.echo(f"   {rule_name}: {rule_info['description']} "
                             f"({rule_info['severity']})")
        
        elif languages:
            translator = cli_instance._service._translator_adapter
            supported = translator.get_supported_languages()
            
            click.echo("🗣️  Linguagens de tradução suportadas:")
            for lang in supported:
                click.echo(f"   {lang}")
        
        else:
            parser_ver = cli_instance._service._parser_adapter.get_version()
            
            click.echo("ℹ️  Sistema LOS - Linguagem de Otimização Simples")
            click.echo("   Versão CLI: 2.1.0 (Functional)")
            click.echo(f"   Parser Core: {parser_ver}")
            click.echo("   Arquitetura: Clean Architecture + Hexagonal")
            click.echo("   Persistência: JSON")
            click.echo("")
            click.echo("Use --help com qualquer comando para mais informações.")
    
    except Exception as e:
        click.echo(f"❌ Erro: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    los()
