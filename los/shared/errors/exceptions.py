"""Tratamento de Erros Customizado."""

from typing import Any, Dict, Optional, List


class LOSError(Exception):
    """Base para exceções do sistema LOS."""
    
    def __init__(
        self, 
        message: str, 
        error_code: str,
        context: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        self.original_exception = original_exception
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa erro para dicionário."""
        return {
            'error_type': self.__class__.__name__,
            'error_code': self.error_code,
            'message': self.message,
            'context': self.context,
            'original_exception': str(self.original_exception) if self.original_exception else None
        }


class ParseError(LOSError):
    """Erro de parsing."""
    
    def __init__(
        self, 
        message: str, 
        expression: str,
        line_number: Optional[int] = None,
        column: Optional[int] = None,
        original_exception: Optional[Exception] = None
    ):
        context = {
            'expression': expression,
            'line_number': line_number,
            'column': column
        }
        super().__init__(
            message=message,
            error_code='PARSE_ERROR',
            context=context,
            original_exception=original_exception
        )


class ValidationError(LOSError):
    """Erro de validação."""
    
    def __init__(
        self, 
        message: str, 
        field: Optional[str] = None,
        validation_rules: Optional[List[str]] = None,
        original_exception: Optional[Exception] = None
    ):
        context = {
            'field': field,
            'validation_rules': validation_rules or []
        }
        super().__init__(
            message=message,
            error_code='VALIDATION_ERROR',
            context=context,
            original_exception=original_exception
        )


class TranslationError(LOSError):
    """Erro de tradução."""
    
    def __init__(
        self, 
        message: str, 
        source_expression: str,
        target_language: str = "python",
        original_exception: Optional[Exception] = None
    ):
        context = {
            'source_expression': source_expression,
            'target_language': target_language
        }
        super().__init__(
            message=message,
            error_code='TRANSLATION_ERROR',
            context=context,
            original_exception=original_exception
        )


class ConfigurationError(LOSError):
    """Erro de configuração."""
    
    def __init__(
        self, 
        message: str, 
        config_key: Optional[str] = None,
        expected_type: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        context = {
            'config_key': config_key,
            'expected_type': expected_type
        }
        super().__init__(
            message=message,
            error_code='CONFIGURATION_ERROR',
            context=context,
            original_exception=original_exception
        )


class BusinessRuleError(LOSError):
    """Erro de regra de negócio."""
    
    def __init__(
        self, 
        message: str, 
        rule_name: str,
        violated_constraints: Optional[List[str]] = None,
        original_exception: Optional[Exception] = None
    ):
        context = {
            'rule_name': rule_name,
            'violated_constraints': violated_constraints or []
        }
        super().__init__(
            message=message,
            error_code='BUSINESS_RULE_ERROR',
            context=context,
            original_exception=original_exception
        )


class FileError(LOSError):
    """Erro de arquivo."""
    
    def __init__(
        self, 
        message: str, 
        file_path: str,
        operation: str = "read",
        original_exception: Optional[Exception] = None
    ):
        context = {
            'file_path': file_path,
            'operation': operation
        }
        super().__init__(
            message=message,
            error_code='FILE_ERROR',
            context=context,
            original_exception=original_exception
        )


class InternalError(LOSError):
    """Erro interno."""
    
    def __init__(
        self, 
        message: str, 
        original_exception: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            error_code='INTERNAL_ERROR',
            context={},
            original_exception=original_exception
        )


def wrap_exception(
    exception: Exception, 
    message: Optional[str] = None,
    error_code: str = "UNKNOWN_ERROR",
    context: Optional[Dict[str, Any]] = None
) -> LOSError:
    """Converte exceção padrão em LOSError."""
    final_message = message or str(exception)
    
    # Se já for LOSError, retorna ela mesma
    if isinstance(exception, LOSError):
        return exception
        
    return InternalError(
        message=final_message,
        original_exception=exception
    )
