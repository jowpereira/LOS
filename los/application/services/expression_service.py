"""
🎯 Expression Application Service
Serviço de aplicação principal para operações com expressões LOS
"""

import time
import re
from typing import List, Optional, Dict, Any
from uuid import UUID

from ..dto.expression_dto import (
    ExpressionRequestDTO,
    ExpressionResponseDTO,
    BatchProcessRequestDTO,
    BatchProcessResponseDTO,
    FileProcessRequestDTO,
    FileProcessResponseDTO,
    StatisticsResponseDTO
)
from ..interfaces.adapters import (
    IParserAdapter,
    ITranslatorAdapter,
    IValidatorAdapter,
    ICacheAdapter,
    IFileAdapter
)
from ...domain.use_cases.parse_expression import (
    ParseExpressionUseCase,
    ParseExpressionRequest,
    ParseExpressionResponse
)
from ...domain.repositories.interfaces import (
    IExpressionRepository,
    IGrammarRepository
)
from ...domain.entities.expression import Expression
from ...shared.errors.exceptions import (
    ValidationError,
    FileError,
    BusinessRuleError
)
from ...shared.logging.logger import get_logger


class ExpressionService:
    """
    Serviço de aplicação para operações com expressões LOS
    
    Coordena use cases, adaptadores e repositórios para fornecer
    API unificada para as camadas superiores.
    
    Nota: Implementação síncrona (v3)
    """
    
    def __init__(
        self,
        expression_repository: IExpressionRepository,
        grammar_repository: IGrammarRepository,
        parser_adapter: IParserAdapter,
        translator_adapter: ITranslatorAdapter,
        validator_adapter: IValidatorAdapter,
        cache_adapter: Optional[ICacheAdapter] = None,
        file_adapter: Optional[IFileAdapter] = None
    ):
        self._expression_repo = expression_repository
        self._grammar_repo = grammar_repository
        self._parser_adapter = parser_adapter
        self._translator_adapter = translator_adapter
        self._validator_adapter = validator_adapter
        self._cache_adapter = cache_adapter
        self._file_adapter = file_adapter
        
        # Use cases
        self._parse_expression_uc = ParseExpressionUseCase(
            expression_repository, 
            grammar_repository,
            parser_adapter # Injetando parser
        )
        
        self._logger = get_logger('services.expression')
    
    def parse_expression(self, request: ExpressionRequestDTO) -> ExpressionResponseDTO:
        """
        Analisa uma expressão LOS
        """
        try:
            self._logger.info(f"Iniciando análise de expressão: {request.text[:50]}...")
            
            # Verificar cache se disponível
            cache_key = f"expression:{hash(request.text)}"
            if self._cache_adapter:
                cached_result = self._cache_adapter.get(cache_key)
                if cached_result:
                    self._logger.info("Resultado encontrado no cache")
                    return cached_result
            
            # Executar use case (Síncrono)
            uc_request = ParseExpressionRequest(
                text=request.text,
                validate=request.validate,
                save_result=request.save_result
            )
            
            uc_response = self._parse_expression_uc.execute(uc_request)
            
            # Fix R12/A08: Integrate Translator into Service
            # Ensure python_code is generated if parsing was successful
            if uc_response.success and uc_response.expression.is_valid:
                 try:
                     self._translator_adapter.translate_expression(uc_response.expression)
                 except Exception as e:
                     self._logger.error(f"Translation failed: {e}")
                     # We append warning/error but don't fail the parse if structure is valid?
                     # Ideally we want complete success.
                     uc_response.success = False
                     uc_response.errors.append(f"Translation Error: {str(e)}")
                     uc_response.expression.validation_errors.append(f"Translation Error: {str(e)}")
            
            
            # Converter para DTO
            response = self._convert_to_expression_dto(uc_response)
            
            # Armazenar no cache se disponível e bem-sucedido
            if self._cache_adapter and response.success:
                self._cache_adapter.set(cache_key, response, ttl=3600)
            
            self._logger.info(f"Análise concluída - Sucesso: {response.success}")
            return response
            
        except Exception as e:
            self._logger.error(f"Erro durante análise: {e}")
            return ExpressionResponseDTO(
                id="",
                original_text=request.text,
                python_code="",
                expression_type="",
                operation_type="",
                variables=[],
                dataset_references=[],
                complexity={},
                is_valid=False,
                validation_errors=[str(e)],
                created_at="",
                success=False,
                errors=[str(e)],
                warnings=[]
            )
    
    def process_batch(self, request: BatchProcessRequestDTO) -> BatchProcessResponseDTO:
        """
        Processa múltiplas expressões em lote
        """
        start_time = time.time()
        results = []
        global_errors = []
        successful = 0
        failed = 0
        
        try:
            self._logger.info(f"Iniciando processamento em lote de {len(request.expressions)} expressões")
            
            for i, expression_text in enumerate(request.expressions):
                try:
                    # Criar requisição individual
                    expr_request = ExpressionRequestDTO(
                        text=expression_text,
                        validate=request.validate_all,
                        save_result=request.save_results
                    )
                    
                    # Processar expressão
                    result = self.parse_expression(expr_request)
                    results.append(result)
                    
                    if result.success:
                        successful += 1
                    else:
                        failed += 1
                        if request.stop_on_error:
                            global_errors.append(f"Parada solicitada na expressão {i+1} devido a erro")
                            break
                    
                except Exception as e:
                    failed += 1
                    error_msg = f"Erro na expressão {i+1}: {str(e)}"
                    global_errors.append(error_msg)
                    self._logger.error(error_msg)
                    
                    if request.stop_on_error:
                        break
            
            processing_time = time.time() - start_time
            
            self._logger.info(
                f"Lote processado - Total: {len(results)}, "
                f"Sucesso: {successful}, Falhas: {failed}, "
                f"Tempo: {processing_time:.2f}s"
            )
            
            return BatchProcessResponseDTO(
                total_processed=len(results),
                successful=successful,
                failed=failed,
                expressions=results,
                global_errors=global_errors,
                processing_time=processing_time
            )
            
        except Exception as e:
            self._logger.error(f"Erro durante processamento em lote: {e}")
            return BatchProcessResponseDTO(
                total_processed=0,
                successful=0,
                failed=len(request.expressions),
                expressions=[],
                global_errors=[str(e)],
                processing_time=time.time() - start_time
            )
    
    def process_file(self, request: FileProcessRequestDTO) -> FileProcessResponseDTO:
        """
        Processa arquivo .los/.txt/.csv
        """
        if not self._file_adapter:
            raise BusinessRuleError(
                message="Adaptador de arquivo não configurado",
                rule_name="file_processing"
            )
        
        try:
            self._logger.info(f"Processando arquivo: {request.file_path}")
            
            # Verificar se arquivo existe (Sync)
            if not self._file_adapter.file_exists(request.file_path):
                raise FileError(
                    message=f"Arquivo não encontrado: {request.file_path}",
                    file_path=request.file_path,
                    operation="read"
                )
            
            # Ler conteúdo do arquivo (Sync)
            content = self._file_adapter.read_file(request.file_path, request.encoding)
            
            # TODO: Se for CSV, processar diferente. Por enquanto assume texto/los
            
            # Extrair expressões (remover comentários e linhas vazias)
            expressions = self._extract_expressions_from_content(content)
            
            # Processar expressões em lote
            batch_request = BatchProcessRequestDTO(
                expressions=expressions,
                validate_all=request.validate_syntax,
                save_results=request.save_expressions,
                stop_on_error=False
            )
            
            batch_result = self.process_batch(batch_request)
            
            return FileProcessResponseDTO(
                file_path=request.file_path,
                expressions_found=len(expressions),
                expressions_processed=batch_result.total_processed,
                expressions_valid=batch_result.successful,
                expressions=batch_result.expressions,
                file_errors=batch_result.global_errors
            )
            
        except Exception as e:
            self._logger.error(f"Erro processando arquivo {request.file_path}: {e}")
            return FileProcessResponseDTO(
                file_path=request.file_path,
                expressions_found=0,
                expressions_processed=0,
                expressions_valid=0,
                expressions=[],
                file_errors=[str(e)]
            )
    
    def get_statistics(self) -> StatisticsResponseDTO:
        """
        Retorna estatísticas do sistema
        """
        try:
            self._logger.info("Compilando estatísticas do sistema")
            
            # Buscar todas as expressões (Sync)
            all_expressions = self._expression_repo.find_all()
            
            # Calcular estatísticas
            total = len(all_expressions)
            
            # Por tipo
            by_type = {}
            for expr in all_expressions:
                expr_type = expr.expression_type.value
                by_type[expr_type] = by_type.get(expr_type, 0) + 1
            
            # Por complexidade
            by_complexity = {}
            total_complexity = 0
            for expr in all_expressions:
                complexity_level = expr.complexity.complexity_level
                by_complexity[complexity_level] = by_complexity.get(complexity_level, 0) + 1
                total_complexity += expr.complexity.total_complexity
            
            avg_complexity = total_complexity / total if total > 0 else 0
            
            # Variáveis mais usadas
            variable_count = {}
            for expr in all_expressions:
                for var in expr.variables:
                    variable_count[var.name] = variable_count.get(var.name, 0) + 1
            
            most_used_vars = sorted(
                [{"name": name, "count": count} for name, count in variable_count.items()],
                key=lambda x: x["count"],
                reverse=True
            )[:10]
            
            # Datasets mais usados
            dataset_count = {}
            for expr in all_expressions:
                for ref in expr.dataset_references:
                    dataset_count[ref.dataset_name] = dataset_count.get(ref.dataset_name, 0) + 1
            
            most_used_datasets = sorted(
                [{"name": name, "count": count} for name, count in dataset_count.items()],
                key=lambda x: x["count"],
                reverse=True
            )[:10]
            
            # Taxa de sucesso (baseado em expressões válidas)
            valid_expressions = sum(1 for expr in all_expressions if expr.is_valid)
            success_rate = (valid_expressions / total * 100) if total > 0 else 0
            
            return StatisticsResponseDTO(
                total_expressions=total,
                expressions_by_type=by_type,
                expressions_by_complexity=by_complexity,
                most_used_variables=most_used_vars,
                most_used_datasets=most_used_datasets,
                average_complexity=avg_complexity,
                parsing_success_rate=success_rate
            )
            
        except Exception as e:
            self._logger.error(f"Erro compilando estatísticas: {e}")
            return StatisticsResponseDTO(
                total_expressions=0,
                expressions_by_type={},
                expressions_by_complexity={},
                most_used_variables=[],
                most_used_datasets=[],
                average_complexity=0.0,
                parsing_success_rate=0.0
            )
    
    def _convert_to_expression_dto(self, uc_response: ParseExpressionResponse) -> ExpressionResponseDTO:
        """Converte resposta do use case para DTO"""
        expr = uc_response.expression
        
        return ExpressionResponseDTO(
            id=str(expr.id),
            original_text=expr.original_text,
            python_code=expr.python_code,
            expression_type=expr.expression_type.value,
            operation_type=expr.operation_type.value,
            variables=[var.name for var in expr.variables],
            dataset_references=[
                f"{ref.dataset_name}.{ref.column_name}" 
                for ref in expr.dataset_references
            ],
            complexity={
                "total": expr.complexity.total_complexity,
                "level": expr.complexity.complexity_level,
                "variables": expr.complexity.variable_count,
                "operations": expr.complexity.operation_count
            },
            is_valid=expr.is_valid,
            validation_errors=expr.validation_errors,
            created_at=expr.created_at.isoformat(),
            success=uc_response.success,
            errors=uc_response.errors,
            warnings=uc_response.warnings
        )
    
    def _extract_expressions_from_content(self, content: str) -> List[str]:
        """Extrai expressões válidas de conteúdo de arquivo"""
        # F04: Proper keyword detection — strip comments first, then check for
        # LOS v3 model keywords using word boundaries to avoid substring matches.
        
        # Strip comment lines before checking keywords
        code_lines = []
        for line in content.split('\n'):
            stripped = line.strip()
            if stripped.startswith('#') or stripped.startswith('//'):
                continue
            # Remove inline comments
            if '#' in stripped:
                stripped = stripped[:stripped.index('#')].strip()
            if stripped:
                code_lines.append(stripped)
        
        code_content = '\n'.join(code_lines)
        
        # If content contains LOS v3 model keywords, treat entire file as one model
        model_keywords = r'\b(st:|var\s|set\s|param\s|min:|max:|import\s)'
        if re.search(model_keywords, code_content):
            return [content]
        
        # Otherwise, split into individual expression lines
        expressions = []
        for line in code_lines:
            if line and not line.startswith('```') and not line.startswith('---'):
                expressions.append(line)
        return expressions
