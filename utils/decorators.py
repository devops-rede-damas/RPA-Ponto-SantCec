"""
Decorador @retry com backoff exponencial.

Uso:
    @retry(max_attempts=3, delay=2.0, backoff=2.0)
    def minha_funcao():
        ...
"""

import functools
import logging
import time

logger = logging.getLogger(__name__)


def retry(max_attempts: int = 3, delay: float = 2.0, backoff: float = 2.0, exceptions: tuple = (Exception,)):
    """
    Retenta a função decorada até max_attempts vezes.

    Args:
        max_attempts: Número máximo de tentativas (incluindo a primeira).
        delay: Segundos antes da primeira retentativa.
        backoff: Multiplicador exponencial do delay a cada tentativa.
        exceptions: Tupla de exceções que disparam retry.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exception = exc
                    if attempt == max_attempts:
                        logger.error(
                            "%s — tentativa %d/%d falhou (sem mais retentativas): %s",
                            func.__name__, attempt, max_attempts, exc,
                        )
                        raise
                    logger.warning(
                        "%s — tentativa %d/%d falhou: %s | Próxima em %.1fs",
                        func.__name__, attempt, max_attempts, exc, current_delay,
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff

            raise last_exception  # safety net (nunca deve chegar aqui)

        return wrapper
    return decorator
