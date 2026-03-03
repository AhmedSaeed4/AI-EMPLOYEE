#!/usr/bin/env python3
"""
Retry Handler for AI Employee - Exponential Backoff Retry Decorator

Provides both sync and async retry decorators with exponential backoff
for handling transient errors in MCP servers and watchers.
"""

import asyncio
import time
import functools
import logging
from typing import Callable, Type, Tuple, Any, Optional
from datetime import datetime

from .error_handler import AIEmployeeException, TransientError, classify_error

logger = logging.getLogger('ai_employee.retry_handler')


def calculate_backoff(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
    """
    Calculate exponential backoff delay with jitter.

    Args:
        attempt: Current attempt number (0-indexed)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds

    Returns:
        Delay in seconds with jitter
    """
    exponential_delay = base_delay * (2 ** attempt)
    capped_delay = min(exponential_delay, max_delay)
    # Add jitter (±25% randomness to avoid thundering herd)
    jitter = capped_delay * 0.25 * (2 * (hash(attempt) % 2) - 1)  # Simple jitter
    return max(0, capped_delay + jitter)


def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retry_on: Optional[Tuple[Type[Exception], ...]] = None
):
    """
    Decorator for sync functions with retry logic and exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        retry_on: Tuple of exception types to retry on (defaults to TransientError)

    Example:
        @with_retry(max_attempts=3, base_delay=1.0)
        def send_email(to, subject, body):
            # ... send email logic
    """
    if retry_on is None:
        retry_on = (TransientError,)

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)

                except retry_on as e:
                    last_exception = e

                    # If this is the last attempt, raise
                    if attempt == max_attempts - 1:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise

                    # Calculate delay
                    delay = calculate_backoff(attempt, base_delay, max_delay)

                    logger.warning(
                        f"{func.__name__} attempt {attempt + 1}/{max_attempts} "
                        f"failed: {e}. Retrying in {delay:.1f}s..."
                    )

                    time.sleep(delay)

                except Exception as e:
                    # For non-retryable errors, classify and handle
                    classified_error = classify_error(e)

                    if classified_error.should_retry():
                        # Treat as retryable
                        last_exception = classified_error

                        if attempt == max_attempts - 1:
                            logger.error(
                                f"{func.__name__} failed after {max_attempts} attempts: {e}"
                            )
                            raise

                        delay = calculate_backoff(attempt, base_delay, max_delay)
                        logger.warning(
                            f"{func.__name__} attempt {attempt + 1}/{max_attempts} "
                            f"failed with {type(e).__name__}: {e}. Retrying in {delay:.1f}s..."
                        )
                        time.sleep(delay)
                    else:
                        # Non-retryable, raise immediately
                        logger.error(
                            f"{func.__name__} encountered non-retryable error "
                            f"({type(e).__name__}): {e}"
                        )
                        raise

            # Should never reach here, but just in case
            if last_exception:
                raise last_exception

        return wrapper
    return decorator


def with_async_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retry_on: Optional[Tuple[Type[Exception], ...]] = None
):
    """
    Decorator for async functions with retry logic and exponential backoff.

    This is the async version for MCP servers which use async tool functions.

    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        retry_on: Tuple of exception types to retry on (defaults to TransientError)

    Example:
        @mcp.tool()
        @with_async_retry(max_attempts=3)
        async def send_email(to: str, subject: str, body: str) -> str:
            # ... send email logic
    """
    if retry_on is None:
        retry_on = (TransientError,)

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)

                except retry_on as e:
                    last_exception = e

                    if attempt == max_attempts - 1:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise

                    delay = calculate_backoff(attempt, base_delay, max_delay)

                    logger.warning(
                        f"{func.__name__} attempt {attempt + 1}/{max_attempts} "
                        f"failed: {e}. Retrying in {delay:.1f}s..."
                    )

                    await asyncio.sleep(delay)

                except Exception as e:
                    # For non-retryable errors, classify and handle
                    classified_error = classify_error(e)

                    if classified_error.should_retry():
                        last_exception = classified_error

                        if attempt == max_attempts - 1:
                            logger.error(
                                f"{func.__name__} failed after {max_attempts} attempts: {e}"
                            )
                            raise

                        delay = calculate_backoff(attempt, base_delay, max_delay)
                        logger.warning(
                            f"{func.__name__} attempt {attempt + 1}/{max_attempts} "
                            f"failed with {type(e).__name__}: {e}. Retrying in {delay:.1f}s..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"{func.__name__} encountered non-retryable error "
                            f"({type(e).__name__}): {e}"
                        )
                        raise

            if last_exception:
                raise last_exception

        return wrapper
    return decorator


class RetryContext:
    """Context manager for retrying code blocks."""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        operation_name: str = "operation"
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.operation_name = operation_name
        self.attempts = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False  # Don't suppress exceptions

    async def retry(self, coro):
        """Execute a coroutine with retry logic."""
        while self.attempts < self.max_attempts:
            try:
                self.attempts += 1
                return await coro
            except Exception as e:
                classified_error = classify_error(e)

                if not classified_error.should_retry():
                    raise

                if self.attempts >= self.max_attempts:
                    logger.error(
                        f"{self.operation_name} failed after {self.max_attempts} attempts"
                    )
                    raise

                delay = calculate_backoff(self.attempts - 1, self.base_delay, self.max_delay)
                logger.warning(
                    f"{self.operation_name} attempt {self.attempts}/{self.max_attempts} "
                    f"failed: {e}. Retrying in {delay:.1f}s..."
                )
                await asyncio.sleep(delay)
