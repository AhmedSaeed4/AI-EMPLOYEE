#!/usr/bin/env python3
"""
Error Handler for AI Employee - Error Classification System

Classifies errors into categories for appropriate recovery strategy:
- Transient: Network timeout, API rate limit → Retry with backoff
- Authentication: Expired token, revoked access → Alert human, pause
- Logic: Claude misinterprets message → Human review queue
- Data: Corrupted file, missing field → Quarantine + alert
- System: Orchestrator crash, disk full → Watchdog + auto-restart
"""

import asyncio
import logging
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger('ai_employee.error_handler')


class ErrorCategory(Enum):
    """Categories of errors with different recovery strategies."""
    TRANSIENT = "transient"       # Retry with exponential backoff
    AUTHENTICATION = "auth"       # Alert human, pause operations
    LOGIC = "logic"               # Human review queue
    DATA = "data"                 # Quarantine + alert
    SYSTEM = "system"             # Watchdog + auto-restart


@dataclass
class ErrorConfig:
    """Configuration for each error category."""
    retry: bool                   # Whether to retry
    max_attempts: int             # Maximum retry attempts
    alert_human: bool             # Whether to notify human
    pause_operations: bool        # Whether to pause operations
    quarantine: bool              # Whether to quarantine the data

    def __str__(self):
        return (
            f"ErrorConfig(retry={self.retry}, max_attempts={self.max_attempts}, "
            f"alert={self.alert_human}, pause={self.pause_operations}, "
            f"quarantine={self.quarantine})"
        )


# Error configurations for each category
ERROR_CONFIGS: Dict[ErrorCategory, ErrorConfig] = {
    ErrorCategory.TRANSIENT: ErrorConfig(
        retry=True,
        max_attempts=3,
        alert_human=False,
        pause_operations=False,
        quarantine=False
    ),
    ErrorCategory.AUTHENTICATION: ErrorConfig(
        retry=False,
        max_attempts=0,
        alert_human=True,
        pause_operations=True,
        quarantine=False
    ),
    ErrorCategory.LOGIC: ErrorConfig(
        retry=False,
        max_attempts=0,
        alert_human=True,
        pause_operations=False,
        quarantine=False
    ),
    ErrorCategory.DATA: ErrorConfig(
        retry=False,
        max_attempts=0,
        alert_human=True,
        pause_operations=False,
        quarantine=True
    ),
    ErrorCategory.SYSTEM: ErrorConfig(
        retry=False,
        max_attempts=0,
        alert_human=True,
        pause_operations=False,
        quarantine=False
    ),
}


class AIEmployeeException(Exception):
    """Base exception for AI Employee errors with automatic classification."""

    def __init__(
        self,
        message: str,
        error_type: ErrorCategory,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.error_type = error_type
        self.context = context or {}
        self.config = ERROR_CONFIGS.get(error_type, ERROR_CONFIGS[ErrorCategory.TRANSIENT])
        self.timestamp = datetime.now()

    def should_retry(self) -> bool:
        """Check if this error should be retried."""
        return self.config.retry

    def max_attempts(self) -> int:
        """Get maximum retry attempts for this error type."""
        return self.config.max_attempts

    def should_alert_human(self) -> bool:
        """Check if human should be alerted."""
        return self.config.alert_human

    def should_pause(self) -> bool:
        """Check if operations should be paused."""
        return self.config.pause_operations

    def should_quarantine(self) -> bool:
        """Check if data should be quarantined."""
        return self.config.quarantine


class TransientError(AIEmployeeException):
    """Transient errors: network timeouts, rate limits, temporary API issues."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCategory.TRANSIENT, context)


class AuthError(AIEmployeeException):
    """Authentication errors: expired tokens, revoked access."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCategory.AUTHENTICATION, context)


class LogicError(AIEmployeeException):
    """Logic errors: AI misinterpretation, incorrect processing."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCategory.LOGIC, context)


class DataError(AIEmployeeException):
    """Data errors: corrupted files, missing required fields."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCategory.DATA, context)


class SystemError(AIEmployeeException):
    """System errors: orchestrator crash, disk full, resource exhaustion."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCategory.SYSTEM, context)


def classify_error(exception: Exception) -> AIEmployeeException:
    """
    Classify a generic exception into an AI Employee error category.

    Args:
        exception: The exception to classify

    Returns:
        An AIEmployeeException subclass with appropriate category
    """
    error_message = str(exception).lower()
    exception_type = type(exception).__name__

    # Check for authentication errors
    auth_keywords = ['unauthorized', 'forbidden', 'authentication', 'token', '401', '403']
    if any(kw in error_message or kw in exception_type.lower() for kw in auth_keywords):
        return AuthError(
            f"Authentication failed: {str(exception)}",
            context={'original_exception': exception_type, 'original_message': str(exception)}
        )

    # Check for transient/network errors
    transient_keywords = [
        'timeout', 'connection', 'network', 'rate limit', '429',
        'temporary', 'unavailable', '503', '502', '504'
    ]
    if any(kw in error_message or kw in exception_type.lower() for kw in transient_keywords):
        return TransientError(
            f"Transient error: {str(exception)}",
            context={'original_exception': exception_type, 'original_message': str(exception)}
        )

    # Check for data errors
    data_keywords = ['corrupt', 'invalid', 'missing', 'parse', 'format', 'schema']
    if any(kw in error_message or kw in exception_type.lower() for kw in data_keywords):
        return DataError(
            f"Data error: {str(exception)}",
            context={'original_exception': exception_type, 'original_message': str(exception)}
        )

    # Check for system errors
    system_keywords = ['disk', 'memory', 'permission', 'system', 'oserror', 'ioerror']
    if any(kw in error_message or kw in exception_type.lower() for kw in system_keywords):
        return SystemError(
            f"System error: {str(exception)}",
            context={'original_exception': exception_type, 'original_message': str(exception)}
        )

    # Default: treat as transient for unknown errors (can retry)
    return TransientError(
        f"Unknown error (treating as transient): {str(exception)}",
        context={'original_exception': exception_type, 'original_message': str(exception)}
    )


def get_error_recovery_action(error: AIEmployeeException) -> str:
    """
    Get the recommended recovery action for an error.

    Args:
        error: The classified error

    Returns:
        String describing the recovery action
    """
    if error.error_type == ErrorCategory.TRANSIENT:
        return f"Retry with exponential backoff (max {error.max_attempts()} attempts)"
    elif error.error_type == ErrorCategory.AUTHENTICATION:
        return "Alert human - credentials may be expired. Pause operations requiring this service."
    elif error.error_type == ErrorCategory.LOGIC:
        return "Queue for human review - AI may have misinterpreted the request."
    elif error.error_type == ErrorCategory.DATA:
        return "Quarantine data and alert human - data is corrupted or invalid."
    elif error.error_type == ErrorCategory.SYSTEM:
        return "Restart process and alert human - system resource issue detected."
    else:
        return "Unknown error type - manual intervention required."


# Export list of exceptions that should trigger retry
RETRYABLE_ERRORS = (TransientError,)
