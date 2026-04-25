# flake8: noqa
import logging
import time
from typing import Any, Callable

__all__ = ["retry_on_transaction_error"]


def retry_on_transaction_error(
    max_attempts: int = 15,
    initial_delay: float = 1,
    backoff_factor: float = 2,
    cutoff: float = 10,
) -> Callable:
    _logger = logging.getLogger("RetryTransaction")

    def decorator(func: Callable) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempts: int = 0
            delay: float = initial_delay

            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if e.__class__.__name__ != "OperationalError":
                        raise

                    attempts += 1
                    if attempts >= max_attempts:
                        raise e

                    time.sleep(min(delay, cutoff))
                    delay *= backoff_factor

                    _logger.error(f"Transaction failed. Retrying... Attempt {attempts}/{max_attempts}")

        return wrapper

    return decorator
