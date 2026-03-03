"""
Shared utilities for AI Employee scripts.

Includes error handling, retry logic, and common utilities.
"""

from .error_handler import (
    ErrorCategory,
    AIEmployeeException,
    TransientError,
    AuthError,
    LogicError,
    DataError,
    SystemError,
    classify_error,
    get_error_recovery_action,
    RETRYABLE_ERRORS,
)

from .retry_handler import (
    with_retry,
    with_async_retry,
    RetryContext,
    calculate_backoff,
)

__all__ = [
    # Error Handler exports
    'ErrorCategory',
    'AIEmployeeException',
    'TransientError',
    'AuthError',
    'LogicError',
    'DataError',
    'SystemError',
    'classify_error',
    'get_error_recovery_action',
    'RETRYABLE_ERRORS',
    # Retry Handler exports
    'with_retry',
    'with_async_retry',
    'RetryContext',
    'calculate_backoff',
]
