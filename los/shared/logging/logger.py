"""Configuração de Logging."""

import logging
import logging.config
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


class LOSLogger:
    """Logger centralizado (Singleton)."""
    _instance: Optional['LOSLogger'] = None
    _initialized = False
    
    def __new__(cls) -> 'LOSLogger':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._setup_logging()
            LOSLogger._initialized = True
    
    def _setup_logging(self):
        """Configura sistema de logging."""
        
        # Criar diretório de logs se não existir
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Nome do arquivo de log com timestamp
        log_file = log_dir / f"los_{datetime.now().strftime('%Y%m%d')}.log"
        
        # Configuração de logging
        logging_config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'detailed': {
                    'format': '%(asctime)s [%(levelname)8s] %(name)s:%(lineno)d - %(message)s',
                    'datefmt': '%Y-%m-%d %H:%M:%S'
                },
                'simple': {
                    'format': '%(levelname)s - %(message)s'
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': 'INFO',
                    'formatter': 'simple',
                    'stream': sys.stdout
                },
                'file': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'level': 'DEBUG',
                    'formatter': 'detailed',
                    'filename': str(log_file),
                    'maxBytes': 10485760,  # 10MB
                    'backupCount': 5,
                    'encoding': 'utf-8'
                }
            },
            'loggers': {
                'los': {
                    'level': 'DEBUG',
                    'handlers': ['console', 'file'],
                    'propagate': False
                }
            },
            'root': {
                'level': 'WARNING',
                'handlers': ['console']
            }
        }
        
        logging.config.dictConfig(logging_config)
        self.logger = logging.getLogger('los')
        self.logger.info("Sistema de logging LOS inicializado com sucesso")
    
    def get_logger(self, name: str = 'los') -> logging.Logger:
        """Retorna logger para módulo."""
        return logging.getLogger(f"los.{name}")


# Função factory para obter logger facilmente
def get_logger(name: str = 'main') -> logging.Logger:
    """Factory function para obter logger."""
    los_logger = LOSLogger()
    return los_logger.get_logger(name)


# Logger principal para uso direto
logger = get_logger('core')
