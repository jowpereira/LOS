"""
Application interfaces
"""

from .adapters import (
    IParserAdapter,
    ITranslatorAdapter,
    IValidatorAdapter,
    ICacheAdapter,
    IFileAdapter,
    INotificationAdapter
)

__all__ = [
    'IParserAdapter',
    'ITranslatorAdapter',
    'IValidatorAdapter',
    'ICacheAdapter',
    'IFileAdapter',
    'INotificationAdapter'
]
