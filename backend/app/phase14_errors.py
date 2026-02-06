"""
Phase 14: Error Handling & Fail-Safes

Standardized error handling across all API endpoints and internal functions.
Ensures graceful degradation, human-readable errors, and full logging context.

Core Principles:
- Never crash silently
- Always return safe fallback responses
- Log full context for debugging
- Distinguish user errors from system errors
- User-facing errors are readable
- Internal errors are logged completely
"""

from functools import wraps
from typing import Optional, Callable, Any, Dict, Tuple
from datetime import datetime
import traceback
import logging

logger = logging.getLogger(__name__)


class ConstructionAIException(Exception):
    """Base exception for Construction AI Suite"""
    def __init__(self, message: str, error_code: str, user_message: Optional[str] = None, details: Optional[Dict] = None):
        self.message = message
        self.error_code = error_code
        self.user_message = user_message or "An error occurred. Please try again."
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(ConstructionAIException):
    """Data validation error (user responsibility)"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            user_message="Invalid input data. Please check your request.",
            details=details
        )


class ModelError(ConstructionAIException):
    """Model inference error (system issue, not user fault)"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code="MODEL_ERROR",
            user_message="Model processing failed. Please try again or contact support.",
            details=details
        )


class DataProcessingError(ConstructionAIException):
    """Data preprocessing error (usually system issue)"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code="DATA_PROCESSING_ERROR",
            user_message="Data processing failed. Please check your input.",
            details=details
        )


class StorageError(ConstructionAIException):
    """Storage/IO error (system issue)"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code="STORAGE_ERROR",
            user_message="System storage error. Please try again.",
            details=details
        )


class ResourceExhaustedError(ConstructionAIException):
    """Resource exhaustion (system under stress)"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code="RESOURCE_EXHAUSTED",
            user_message="System is under heavy load. Please try again.",
            details=details
        )


def error_response(
    exception: Exception,
    status_code: int = 500,
    request_id: Optional[str] = None
) -> Tuple[Dict, int]:
    """
    Convert exception to standardized API error response.
    
    Returns:
        (response_dict, http_status_code)
    """
    
    if isinstance(exception, ConstructionAIException):
        return {
            'status': 'error',
            'error_code': exception.error_code,
            'message': exception.user_message,
            'request_id': request_id,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
        }, status_code
    
    # Generic exception (shouldn't normally reach here)
    return {
        'status': 'error',
        'error_code': 'INTERNAL_ERROR',
        'message': 'An unexpected error occurred. Please contact support.',
        'request_id': request_id,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
    }, 500


def safe_api_call(func: Callable) -> Callable:
    """
    Decorator for API endpoints to ensure safe error handling.
    
    Catches exceptions, logs with full context, returns safe responses.
    
    Usage:
        @safe_api_call
        def my_endpoint():
            return {"data": "value"}
    """
    
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        import uuid
        from flask import jsonify
        
        request_id = str(uuid.uuid4())[:8]
        
        try:
            # Execute the endpoint
            result = func(*args, **kwargs)
            return result
        
        except ValidationError as e:
            logger.warning(
                f"Validation error in {func.__name__}",
                extra={
                    'request_id': request_id,
                    'error_code': e.error_code,
                    'error': e.message,
                    'details': e.details
                }
            )
            response, status = error_response(e, status_code=400, request_id=request_id)
            return jsonify(response), status
        
        except ModelError as e:
            logger.error(
                f"Model error in {func.__name__}",
                extra={
                    'request_id': request_id,
                    'error_code': e.error_code,
                    'error': e.message,
                    'details': e.details,
                    'traceback': traceback.format_exc()
                }
            )
            response, status = error_response(e, status_code=500, request_id=request_id)
            return jsonify(response), status
        
        except DataProcessingError as e:
            logger.error(
                f"Data processing error in {func.__name__}",
                extra={
                    'request_id': request_id,
                    'error_code': e.error_code,
                    'error': e.message,
                    'details': e.details
                }
            )
            response, status = error_response(e, status_code=400, request_id=request_id)
            return jsonify(response), status
        
        except ResourceExhaustedError as e:
            logger.warning(
                f"Resource exhausted in {func.__name__}",
                extra={
                    'request_id': request_id,
                    'error_code': e.error_code,
                    'error': e.message
                }
            )
            response, status = error_response(e, status_code=429, request_id=request_id)
            return jsonify(response), status
        
        except ConstructionAIException as e:
            logger.error(
                f"Construction AI error in {func.__name__}",
                extra={
                    'request_id': request_id,
                    'error_code': e.error_code,
                    'error': e.message,
                    'details': e.details
                }
            )
            response, status = error_response(e, status_code=500, request_id=request_id)
            return jsonify(response), status
        
        except Exception as e:
            # Unhandled exception - log fully, return safe response
            logger.error(
                f"Unhandled exception in {func.__name__}",
                extra={
                    'request_id': request_id,
                    'error': str(e),
                    'error_type': type(e).__name__,
                    'traceback': traceback.format_exc()
                }
            )
            response, status = error_response(e, status_code=500, request_id=request_id)
            return jsonify(response), status
    
    return wrapper


def safe_sync_operation(func: Callable) -> Callable:
    """
    Decorator for internal synchronous operations (non-API).
    
    Ensures exceptions are logged with context but not swallowed.
    Allows calling code to handle exceptions.
    
    Usage:
        @safe_sync_operation
        def process_data(data):
            return transformed_data
    """
    
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(
                f"Error in {func.__name__}",
                extra={
                    'error': str(e),
                    'error_type': type(e).__name__,
                    'traceback': traceback.format_exc()
                }
            )
            raise  # Re-raise for calling code to handle
    
    return wrapper


class ErrorContext:
    """Context manager for detailed error logging"""
    
    def __init__(self, operation: str, details: Optional[Dict] = None):
        self.operation = operation
        self.details = details or {}
        self.start_time = datetime.utcnow()
    
    def __enter__(self):
        logger.debug(
            f"Starting: {self.operation}",
            extra={'details': self.details}
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.utcnow() - self.start_time).total_seconds()
        
        if exc_type is not None:
            logger.error(
                f"Failed: {self.operation}",
                extra={
                    'error_type': exc_type.__name__,
                    'error': str(exc_val),
                    'duration_seconds': duration,
                    'details': self.details,
                    'traceback': traceback.format_exc()
                }
            )
        else:
            logger.info(
                f"Completed: {self.operation}",
                extra={
                    'duration_seconds': duration,
                    'details': self.details
                }
            )
        
        return False  # Don't suppress exceptions


# Fallback responses for common failure scenarios

FALLBACK_PHASE9_OUTPUT = {
    "status": "error",
    "message": "Intelligence generation failed. Using fallback response.",
    "risk_score": None,
    "delay_probability": None,
    "risk_factors": [],
    "fallback": True,
    "error_code": "MODEL_INFERENCE_FAILED"
}

FALLBACK_PHASE12_OUTPUT = {
    "status": "error",
    "message": "Recommendation generation failed.",
    "recommendations": [],
    "fallback": True,
    "error_code": "RECOMMENDATION_GENERATION_FAILED"
}

FALLBACK_PHASE13_OUTPUT = {
    "status": "error",
    "message": "Feedback processing failed.",
    "feedback_stored": False,
    "fallback": True,
    "error_code": "FEEDBACK_PROCESSING_FAILED"
}
