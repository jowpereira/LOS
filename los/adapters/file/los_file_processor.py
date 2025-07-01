"""
📂 File Processor - Processador de Arquivos LOS
Adaptador para processamento de arquivos .los com suporte a múltiplos formatos
"""

import asyncio
import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from ...application.interfaces.adapters import IFileAdapter
from ...application.dto.expression_dto import (
    FileProcessRequestDTO,
    FileProcessResponseDTO,
    ExpressionRequestDTO
)
from ...shared.errors.exceptions import FileError
from ...shared.logging.logger import get_logger


class LOSFileProcessor(IFileAdapter):
    """
    Processador de arquivos para sistema LOS
    Suporta .los, .txt, .csv e outros formatos
    """
    
    def __init__(self):
        self._logger = get_logger('adapters.file.los_processor')
        self._supported_extensions = {'.los', '.txt', '.csv', '.json'}
    
    async def read_file(self, file_path: str, encoding: str = "utf-8") -> str:
        """
        Lê conteúdo de arquivo
        
        Args:
            file_path: Caminho do arquivo
            encoding: Codificação do arquivo
            
        Returns:
            Conteúdo do arquivo
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                raise FileError(
                    message=f"Arquivo não encontrado: {file_path}",
                    file_path=file_path,
                    operation="read"
                )
            
            self._logger.info(f"Lendo arquivo: {file_path}")
            
            # Verificar extensão
            if path.suffix.lower() not in self._supported_extensions:
                self._logger.warning(f"Extensão {path.suffix} pode não ser suportada")
            
            content = path.read_text(encoding=encoding)
            
            self._logger.debug(f"Arquivo lido com sucesso: {len(content)} caracteres")
            return content
            
        except UnicodeDecodeError as e:
            raise FileError(
                message=f"Erro de codificação ao ler arquivo: {encoding}",
                file_path=file_path,
                operation="read",
                original_exception=e
            )
        
        except PermissionError as e:
            raise FileError(
                message="Sem permissão para ler o arquivo",
                file_path=file_path,
                operation="read",
                original_exception=e
            )
        
        except Exception as e:
            raise FileError(
                message=f"Erro inesperado ao ler arquivo: {str(e)}",
                file_path=file_path,
                operation="read",
                original_exception=e
            )
    
    async def write_file(
        self, 
        file_path: str, 
        content: str, 
        encoding: str = "utf-8"
    ) -> bool:
        """
        Escreve conteúdo em arquivo
        
        Args:
            file_path: Caminho do arquivo
            content: Conteúdo a ser escrito
            encoding: Codificação do arquivo
            
        Returns:
            True se escrito com sucesso
        """
        try:
            path = Path(file_path)
            
            # Criar diretórios se necessário
            path.parent.mkdir(parents=True, exist_ok=True)
            
            self._logger.info(f"Escrevendo arquivo: {file_path}")
            
            path.write_text(content, encoding=encoding)
            
            self._logger.debug(f"Arquivo escrito com sucesso: {len(content)} caracteres")
            return True
            
        except PermissionError as e:
            raise FileError(
                message="Sem permissão para escrever o arquivo",
                file_path=file_path,
                operation="write",
                original_exception=e
            )
        
        except Exception as e:
            raise FileError(
                message=f"Erro ao escrever arquivo: {str(e)}",
                file_path=file_path,
                operation="write",
                original_exception=e
            )
    
    async def file_exists(self, file_path: str) -> bool:
        """
        Verifica se arquivo existe
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            True se arquivo existe
        """
        return Path(file_path).exists()
    
    async def process_los_file(
        self, 
        file_path: str, 
        encoding: str = "utf-8"
    ) -> Tuple[List[str], List[str]]:
        """
        Processa arquivo .los específico
        
        Args:
            file_path: Caminho do arquivo .los
            encoding: Codificação do arquivo
            
        Returns:
            Tupla com (expressões_válidas, erros)
        """
        try:
            content = await self.read_file(file_path, encoding)
            
            expressions = []
            errors = []
            
            for line_num, line in enumerate(content.split('\n'), 1):
                line = line.strip()
                
                # Pular linhas de comentário e documentação
                if self._should_skip_line(line):
                    continue
                
                # Validar linha como expressão LOS
                if self._is_valid_los_expression(line):
                    expressions.append(line)
                else:
                    # Não é erro crítico, apenas não é expressão LOS
                    self._logger.debug(f"Linha {line_num} não é expressão LOS: {line[:50]}...")
            
            self._logger.info(f"Arquivo processado: {len(expressions)} expressões encontradas")
            
            return expressions, errors
            
        except Exception as e:
            error_msg = f"Erro processando arquivo LOS: {str(e)}"
            self._logger.error(error_msg)
            return [], [error_msg]
    
    async def export_results(
        self, 
        results: List[Dict[str, Any]], 
        output_path: str,
        format_type: str = "json"
    ) -> bool:
        """
        Exporta resultados em formato específico
        
        Args:
            results: Lista de resultados
            output_path: Caminho de saída
            format_type: Formato (json, csv, txt)
            
        Returns:
            True se exportado com sucesso
        """
        try:
            path = Path(output_path)
            
            if format_type.lower() == "json":
                content = json.dumps(results, indent=2, ensure_ascii=False)
                
            elif format_type.lower() == "csv":
                content = self._convert_to_csv(results)
                
            elif format_type.lower() == "txt":
                content = self._convert_to_text(results)
                
            else:
                raise FileError(
                    message=f"Formato não suportado: {format_type}",
                    file_path=output_path,
                    operation="export"
                )
            
            return await self.write_file(output_path, content)
            
        except Exception as e:
            raise FileError(
                message=f"Erro exportando resultados: {str(e)}",
                file_path=output_path,
                operation="export",
                original_exception=e
            )
    
    async def batch_process_directory(
        self, 
        directory_path: str,
        pattern: str = "*.los",
        recursive: bool = False
    ) -> Dict[str, Any]:
        """
        Processa todos os arquivos de um diretório
        
        Args:
            directory_path: Caminho do diretório
            pattern: Padrão de arquivos (*.los)
            recursive: Buscar recursivamente
            
        Returns:
            Resumo do processamento
        """
        try:
            directory = Path(directory_path)
            
            if not directory.exists() or not directory.is_dir():
                raise FileError(
                    message=f"Diretório não encontrado: {directory_path}",
                    file_path=directory_path,
                    operation="read"
                )
            
            # Buscar arquivos
            if recursive:
                files = list(directory.rglob(pattern))
            else:
                files = list(directory.glob(pattern))
            
            self._logger.info(f"Processando {len(files)} arquivos em {directory_path}")
            
            results = {
                "directory": directory_path,
                "files_found": len(files),
                "files_processed": 0,
                "total_expressions": 0,
                "total_errors": 0,
                "files": []
            }
            
            for file_path in files:
                try:
                    expressions, errors = await self.process_los_file(str(file_path))
                    
                    file_result = {
                        "file_path": str(file_path),
                        "expressions_count": len(expressions),
                        "errors_count": len(errors),
                        "expressions": expressions,
                        "errors": errors
                    }
                    
                    results["files"].append(file_result)
                    results["files_processed"] += 1
                    results["total_expressions"] += len(expressions)
                    results["total_errors"] += len(errors)
                    
                except Exception as e:
                    self._logger.error(f"Erro processando {file_path}: {e}")
                    
                    error_result = {
                        "file_path": str(file_path),
                        "expressions_count": 0,
                        "errors_count": 1,
                        "expressions": [],
                        "errors": [str(e)]
                    }
                    
                    results["files"].append(error_result)
                    results["total_errors"] += 1
            
            self._logger.info(
                f"Processamento em lote concluído: "
                f"{results['files_processed']}/{results['files_found']} arquivos"
            )
            
            return results
            
        except Exception as e:
            raise FileError(
                message=f"Erro no processamento em lote: {str(e)}",
                file_path=directory_path,
                operation="batch_process",
                original_exception=e
            )
    
    def _should_skip_line(self, line: str) -> bool:
        """Verifica se linha deve ser pulada"""
        if not line:
            return True
        
        # Comentários
        if line.startswith('#'):
            return True
        
        # Blocos de código
        if line.startswith('```'):
            return True
        
        # Markdown
        markdown_indicators = [
            '*', '**', '-', '|', '❌', '✅', '---', '===',
            '##', '###', '####'
        ]
        
        if any(line.startswith(indicator) for indicator in markdown_indicators):
            return True
        
        # Numeração de listas
        if any(line.startswith(f"{i}.") for i in range(1, 10)):
            return True
        
        return False
    
    def _is_valid_los_expression(self, line: str) -> bool:
        """Verifica se linha parece ser expressão LOS válida"""
        if not line:
            return False
        
        # Indicadores de expressões LOS
        los_keywords = [
            'MINIMIZAR:', 'MAXIMIZAR:', 'SOMA DE', 'PARA CADA',
            'SE ', ' ENTAO ', ' SENAO '
        ]
        
        # Operadores relacionais
        relational_ops = ['<=', '>=', '==', '!=', '<', '>', '=']
        
        line_upper = line.upper()
        
        # Verificar palavras-chave LOS
        if any(keyword in line_upper for keyword in los_keywords):
            return True
        
        # Verificar operadores relacionais (possível restrição)
        if any(op in line for op in relational_ops):
            return True
        
        # Expressões matemáticas simples (contém variáveis)
        if any(char.isalpha() for char in line) and any(op in line for op in ['+', '-', '*', '/']):
            return True
        
        return False
    
    def _convert_to_csv(self, results: List[Dict[str, Any]]) -> str:
        """Converte resultados para formato CSV"""
        if not results:
            return ""
        
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Cabeçalho
        if results:
            headers = results[0].keys()
            writer.writerow(headers)
            
            # Dados
            for result in results:
                row = []
                for key in headers:
                    value = result.get(key, "")
                    # Converter listas/dicts para string
                    if isinstance(value, (list, dict)):
                        value = json.dumps(value, ensure_ascii=False)
                    row.append(str(value))
                writer.writerow(row)
        
        return output.getvalue()
    
    def _convert_to_text(self, results: List[Dict[str, Any]]) -> str:
        """Converte resultados para formato texto"""
        lines = []
        lines.append("# Relatório de Processamento LOS")
        lines.append("=" * 50)
        lines.append("")
        
        for i, result in enumerate(results, 1):
            lines.append(f"## Resultado {i}")
            for key, value in result.items():
                lines.append(f"{key}: {value}")
            lines.append("")
        
        return "\n".join(lines)
