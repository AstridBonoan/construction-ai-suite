"""
Phase 14: Standardized Logging & Observability

Unified logging across all phases:
- Consistent format (timestamp, level, module, message)
- Structured logging (context, details)
- Error categorization (user/system/AI)
- Persistent storage (file-based)
- Easy diagnosis without guessing
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import json


class StructuredFormatter(logging.Formatter):
    """
    Structured logging formatter that outputs consistent JSON format.
    
    Format:
    {
        "timestamp": "2024-02-04T10:30:45.123Z",
        "level": "ERROR",
        "module": "phase9_model",
        "function": "infer",
        "message": "Model inference failed",
        "details": {...},
        "error": "ValueError: ...",
        "traceback": "..."
    }
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage(),
        }
        
        # Add extra context if provided
        if hasattr(record, 'details'):
            log_entry['details'] = record.details
        
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        
        if hasattr(record, 'error_code'):
            log_entry['error_code'] = record.error_code
        
        if hasattr(record, 'error'):
            log_entry['error'] = record.error
        
        if hasattr(record, 'traceback'):
            log_entry['traceback'] = record.traceback
        
        # Add exception info if available
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
            }
        
        return json.dumps(log_entry, separators=(',', ':'), default=str)


def setup_logging(
    app_name: str = 'construction-ai-suite',
    log_dir: Optional[Path] = None,
    level: int = logging.INFO
) -> None:
    """
    Set up standardized logging for the application.
    
    Args:
        app_name: Application name
        log_dir: Directory for log files (defaults to ./logs)
        level: Logging level (INFO, DEBUG, ERROR, etc.)
    """
    
    if log_dir is None:
        log_dir = Path(__file__).parent.parent.parent / 'logs'
    
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers to avoid duplication
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Formatter
    formatter = StructuredFormatter()
    
    # File handler (rotating)
    file_path = log_dir / f'{app_name}.log'
    file_handler = logging.handlers.RotatingFileHandler(
        file_path,
        maxBytes=100_000_000,  # 100 MB
        backupCount=10,        # Keep 10 rotated files
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)
    root_logger.addHandler(file_handler)
    
    # Console handler (simplified, human-readable)
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        '[%(levelname)s] %(name)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(level)
    root_logger.addHandler(console_handler)
    
    # Log startup
    logger = logging.getLogger(__name__)
    logger.info(
        f"Logging initialized",
        extra={
            'details': {
                'app_name': app_name,
                'log_dir': str(log_dir),
                'log_level': logging.getLevelName(level)
            }
        }
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a specific module"""
    return logging.getLogger(name)


# Category-specific loggers for easy filtering

def log_user_error(logger: logging.Logger, message: str, details: Optional[Dict] = None):
    """Log user-caused error (bad input, validation failure)"""
    logger.warning(
        f"User error: {message}",
        extra={
            'error_type': 'USER_ERROR',
            'details': details or {}
        }
    )


def log_system_error(logger: logging.Logger, message: str, details: Optional[Dict] = None):
    """Log system-caused error (I/O, storage, resource)"""
    logger.error(
        f"System error: {message}",
        extra={
            'error_type': 'SYSTEM_ERROR',
            'details': details or {}
        }
    )


def log_ai_error(logger: logging.Logger, message: str, details: Optional[Dict] = None):
    """Log AI/model-caused error (inference failure, numerical issue)"""
    logger.error(
        f"AI error: {message}",
        extra={
            'error_type': 'AI_ERROR',
            'details': details or {}
        }
    )


def log_inference(
    logger: logging.Logger,
    phase: str,
    model_name: str,
    input_size: int,
    duration_ms: float,
    success: bool,
    details: Optional[Dict] = None
):
    """Log model inference event"""
    logger.info(
        f"{phase} inference",
        extra={
            'event_type': 'INFERENCE',
            'phase': phase,
            'model_name': model_name,
            'input_size': input_size,
            'duration_ms': duration_ms,
            'success': success,
            'details': details or {}
        }
    )


def log_data_validation(
    logger: logging.Logger,
    source: str,
    row_count: int,
    invalid_count: int,
    details: Optional[Dict] = None
):
    """Log data validation event"""
    logger.info(
        f"Data validation: {source}",
        extra={
            'event_type': 'VALIDATION',
            'source': source,
            'row_count': row_count,
            'invalid_count': invalid_count,
            'valid_count': row_count - invalid_count,
            'details': details or {}
        }
    )


def log_storage_operation(
    logger: logging.Logger,
    operation: str,
    path: str,
    success: bool,
    duration_ms: float,
    details: Optional[Dict] = None
):
    """Log storage/I/O operation"""
    logger.info(
        f"Storage operation: {operation}",
        extra={
            'event_type': 'STORAGE',
            'operation': operation,
            'path': path,
            'success': success,
            'duration_ms': duration_ms,
            'details': details or {}
        }
    )


def log_performance_warning(
    logger: logging.Logger,
    metric: str,
    value: float,
    threshold: float,
    details: Optional[Dict] = None
):
    """Log performance warning (slow operation, high memory, etc.)"""
    logger.warning(
        f"Performance warning: {metric}",
        extra={
            'event_type': 'PERFORMANCE',
            'metric': metric,
            'value': value,
            'threshold': threshold,
            'details': details or {}
        }
    )
