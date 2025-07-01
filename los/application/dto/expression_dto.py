"""
📤 Data Transfer Objects (DTOs)
Objetos para transferência de dados entre camadas
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import UUID


@dataclass
class ExpressionRequestDTO:
    """DTO para requisições de análise de expressão"""
    text: str
    validate: bool = True
    save_result: bool = False
    context: Optional[Dict[str, Any]] = None


@dataclass
class ExpressionResponseDTO:
    """DTO para resposta de análise de expressão"""
    id: str
    original_text: str
    python_code: str
    expression_type: str
    operation_type: str
    variables: List[str]
    dataset_references: List[str]
    complexity: Dict[str, Any]
    is_valid: bool
    validation_errors: List[str]
    created_at: str
    success: bool
    errors: List[str]
    warnings: List[str]


@dataclass
class BatchProcessRequestDTO:
    """DTO para processamento em lote de expressões"""
    expressions: List[str]
    validate_all: bool = True
    save_results: bool = False
    stop_on_error: bool = False


@dataclass  
class BatchProcessResponseDTO:
    """DTO para resposta de processamento em lote"""
    total_processed: int
    successful: int
    failed: int
    expressions: List[ExpressionResponseDTO]
    global_errors: List[str]
    processing_time: float


@dataclass
class FileProcessRequestDTO:
    """DTO para processamento de arquivo .los"""
    file_path: str
    encoding: str = "utf-8"
    validate_syntax: bool = True
    save_expressions: bool = False


@dataclass
class FileProcessResponseDTO:
    """DTO para resposta de processamento de arquivo"""
    file_path: str
    expressions_found: int
    expressions_processed: int
    expressions_valid: int
    expressions: List[ExpressionResponseDTO]
    file_errors: List[str]


@dataclass
class ValidationRequestDTO:
    """DTO para requisições de validação"""
    expression_id: Optional[str] = None
    expression_text: Optional[str] = None
    validation_rules: List[str] = None


@dataclass
class ValidationResponseDTO:
    """DTO para resposta de validação"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    applied_rules: List[str]


@dataclass
class TranslationRequestDTO:
    """DTO para requisições de tradução"""
    expression_id: Optional[str] = None
    expression_text: Optional[str] = None
    target_language: str = "python"
    target_framework: str = "pulp"


@dataclass
class TranslationResponseDTO:
    """DTO para resposta de tradução"""
    source_text: str
    translated_code: str
    target_language: str
    target_framework: str
    translation_success: bool
    translation_errors: List[str]


@dataclass
class StatisticsResponseDTO:
    """DTO para estatísticas do sistema"""
    total_expressions: int
    expressions_by_type: Dict[str, int]
    expressions_by_complexity: Dict[str, int]
    most_used_variables: List[Dict[str, Any]]
    most_used_datasets: List[Dict[str, Any]]
    average_complexity: float
    parsing_success_rate: float
