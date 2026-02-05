"""
Phase 14: Performance & Resource Stability

Monitors memory usage, execution time, and resource constraints.
Prevents system degradation under load.
Adds timeouts for long-running operations.
"""

import logging
import psutil
import time
from functools import wraps
from typing import Callable, Optional, Dict, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class ResourceMonitor:
    """Monitors system resources"""
    
    # Warning thresholds
    MEMORY_WARNING_PERCENT = 80  # Warn if >80% memory used
    CPU_WARNING_PERCENT = 90     # Warn if >90% CPU used
    TIMEOUT_SECONDS = 300        # 5 minute default timeout
    
    @staticmethod
    def get_memory_usage() -> Dict[str, float]:
        """Get current memory usage"""
        try:
            memory = psutil.virtual_memory()
            return {
                'total_mb': memory.total / (1024 * 1024),
                'used_mb': memory.used / (1024 * 1024),
                'available_mb': memory.available / (1024 * 1024),
                'percent': memory.percent,
            }
        except Exception as e:
            logger.error(f"Failed to get memory usage: {e}")
            return {}
    
    @staticmethod
    def get_cpu_usage() -> Dict[str, float]:
        """Get current CPU usage"""
        try:
            return {
                'percent': psutil.cpu_percent(interval=1),
                'core_count': psutil.cpu_count(),
            }
        except Exception as e:
            logger.error(f"Failed to get CPU usage: {e}")
            return {}
    
    @staticmethod
    def check_memory_available(required_mb: float) -> tuple[bool, Optional[str]]:
        """Check if sufficient memory is available"""
        try:
            memory = psutil.virtual_memory()
            available_mb = memory.available / (1024 * 1024)
            
            if available_mb < required_mb:
                return False, (
                    f"Insufficient memory: {available_mb:.0f} MB available, "
                    f"{required_mb:.0f} MB required"
                )
            
            return True, None
        except Exception as e:
            logger.error(f"Failed to check memory: {e}")
            return False, f"Memory check failed: {e}"
    
    @staticmethod
    def log_resource_stats():
        """Log current resource usage"""
        memory = ResourceMonitor.get_memory_usage()
        cpu = ResourceMonitor.get_cpu_usage()
        
        logger.info(
            "Resource stats",
            extra={
                'event_type': 'RESOURCE_STATS',
                'memory': memory,
                'cpu': cpu,
            }
        )


class PerformanceTracker:
    """Tracks performance metrics"""
    
    def __init__(self, name: str):
        self.name = name
        self.start_time = None
        self.start_memory = None
    
    def __enter__(self):
        self.start_time = time.time()
        try:
            process = psutil.Process()
            self.start_memory = process.memory_info().rss / (1024 * 1024)  # MB
        except Exception:
            self.start_memory = None
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000
        
        memory_delta_mb = None
        try:
            process = psutil.Process()
            end_memory = process.memory_info().rss / (1024 * 1024)  # MB
            memory_delta_mb = end_memory - self.start_memory
        except Exception:
            pass
        
        if exc_type is None:
            logger.info(
                f"Operation completed: {self.name}",
                extra={
                    'event_type': 'OPERATION_COMPLETE',
                    'operation': self.name,
                    'duration_ms': duration_ms,
                    'memory_delta_mb': memory_delta_mb,
                }
            )
        else:
            logger.error(
                f"Operation failed: {self.name}",
                extra={
                    'event_type': 'OPERATION_FAILED',
                    'operation': self.name,
                    'duration_ms': duration_ms,
                    'error': str(exc_val),
                }
            )
        
        return False  # Don't suppress exceptions


def timeout(seconds: float = ResourceMonitor.TIMEOUT_SECONDS):
    """
    Decorator to add timeout to function.
    
    Usage:
        @timeout(30)
        def slow_operation():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError(f"{func.__name__} exceeded {seconds} seconds")
            
            # Set timeout
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(seconds))
            
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)  # Cancel alarm
            
            return result
        
        return wrapper
    
    return decorator


def track_performance(func: Callable) -> Callable:
    """
    Decorator to track performance of a function.
    
    Logs duration and memory usage.
    
    Usage:
        @track_performance
        def my_function():
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        with PerformanceTracker(func.__name__):
            return func(*args, **kwargs)
    
    return wrapper


@contextmanager
def operation_timer(operation_name: str):
    """
    Context manager for timing operations.
    
    Usage:
        with operation_timer("data_loading"):
            data = load_data()
    """
    start_time = time.time()
    start_memory = None
    
    try:
        process = psutil.Process()
        start_memory = process.memory_info().rss / (1024 * 1024)
    except Exception:
        pass
    
    try:
        yield
    finally:
        duration_ms = (time.time() - start_time) * 1000
        
        memory_delta_mb = None
        try:
            process = psutil.Process()
            end_memory = process.memory_info().rss / (1024 * 1024)
            memory_delta_mb = end_memory - start_memory
        except Exception:
            pass
        
        logger.info(
            f"Operation timed: {operation_name}",
            extra={
                'event_type': 'OPERATION_TIMING',
                'operation': operation_name,
                'duration_ms': duration_ms,
                'memory_delta_mb': memory_delta_mb,
            }
        )


class SlowOperationDetector:
    """Detects and logs slow operations"""
    
    # Thresholds for warning (milliseconds)
    THRESHOLDS = {
        'data_load': 5000,         # 5 seconds
        'model_inference': 10000,  # 10 seconds
        'data_validation': 3000,   # 3 seconds
    }
    
    @staticmethod
    def check_duration(
        operation_type: str,
        duration_ms: float
    ) -> Optional[str]:
        """
        Check if operation took too long.
        
        Returns warning message if slow, None otherwise.
        """
        threshold = SlowOperationDetector.THRESHOLDS.get(operation_type)
        
        if threshold is None or duration_ms <= threshold:
            return None
        
        warning = (
            f"Slow operation detected: {operation_type} "
            f"took {duration_ms:.0f}ms (threshold: {threshold}ms)"
        )
        
        logger.warning(
            warning,
            extra={
                'event_type': 'SLOW_OPERATION',
                'operation_type': operation_type,
                'duration_ms': duration_ms,
                'threshold_ms': threshold,
            }
        )
        
        return warning


def require_memory(required_mb: float):
    """
    Decorator to ensure sufficient memory before function execution.
    
    Usage:
        @require_memory(500)  # Require 500 MB
        def memory_intensive_operation():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            from phase14_errors import ResourceExhaustedError
            
            has_memory, error = ResourceMonitor.check_memory_available(required_mb)
            if not has_memory:
                raise ResourceExhaustedError(error or "Insufficient memory")
            
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


# Performance budget for critical operations
class PerformanceBudget:
    """Tracks if operations are within performance budget"""
    
    def __init__(self, operation: str, budget_ms: float):
        self.operation = operation
        self.budget_ms = budget_ms
        self.start_time = time.time()
    
    def remaining_ms(self) -> float:
        """Time remaining in budget"""
        elapsed = (time.time() - self.start_time) * 1000
        return max(0, self.budget_ms - elapsed)
    
    def exceeded(self) -> bool:
        """Check if budget exceeded"""
        return self.remaining_ms() <= 0
    
    def assert_not_exceeded(self, message: Optional[str] = None):
        """Raise error if budget exceeded"""
        if self.exceeded():
            msg = message or f"{self.operation} exceeded {self.budget_ms}ms budget"
            logger.error(msg)
            raise TimeoutError(msg)
