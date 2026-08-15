"""Helper functions for database operations with retry logic."""

import sqlite3
import time
import logging
from functools import wraps
from typing import Callable, Any

logger = logging.getLogger('process')


class DatabaseLockError(Exception):
    """Custom exception for database lock errors."""
    pass


def retry_on_locked(max_retries: int = 10, delay: float = 0.5):
    """
    Decorator para retry de operações de banco de dados quando está locked.

    Args:
        max_retries: Número máximo de tentativas
        delay: Tempo de espera inicial entre tentativas em segundos
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_error = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except sqlite3.OperationalError as e:
                    last_error = e
                    if 'locked' in str(e).lower() or 'database is locked' in str(e).lower():
                        logger.warning(f"Database locked, tentando novamente ({attempt + 1}/{max_retries})...")
                        # Exponential backoff com jitter para evitar thundering herd
                        backoff_time = delay * (2 ** min(attempt, 5))  # Cap at 2^5 = 32x delay
                        time.sleep(backoff_time)
                        continue
                    else:
                        # Outros erros, não retry
                        raise
                except Exception as e:
                    # Outros tipos de erro, não retry
                    raise

            # Se chegou aqui, todas as tentativas falharam
            logger.error(f"Database ainda locked após {max_retries} tentativas")
            raise DatabaseLockError(f"Database locked após {max_retries} tentativas") from last_error

        return wrapper
    return decorator


def safe_execute(db: sqlite3.Connection, query: str, params: tuple = None, max_retries: int = 10):
    """
    Executa query com retry automático em caso de database locked.

    Args:
        db: Conexão do banco de dados
        query: Query SQL a ser executada
        params: Parâmetros da query (opcional)
        max_retries: Número máximo de tentativas

    Returns:
        Cursor com resultado da query
    """
    last_error = None

    for attempt in range(max_retries):
        try:
            if params:
                return db.execute(query, params)
            else:
                return db.execute(query)
        except sqlite3.OperationalError as e:
            last_error = e
            if 'locked' in str(e).lower() or 'database is locked' in str(e).lower():
                logger.warning(f"Database locked ao executar query, tentando novamente ({attempt + 1}/{max_retries})...")
                # Exponential backoff com cap para evitar esperas muito longas
                backoff_time = 0.5 * (2 ** min(attempt, 5))  # Cap at 2^5 = 32x 0.5 = 16s
                time.sleep(backoff_time)
                continue
            else:
                raise
        except Exception as e:
            raise

    # Se chegou aqui, todas as tentativas falharam
    logger.error(f"Database ainda locked após {max_retries} tentativas ao executar query")
    raise DatabaseLockError(f"Database locked após {max_retries} tentativas") from last_error


def safe_commit(db: sqlite3.Connection, max_retries: int = 10) -> bool:
    """
    Faz commit com retry automático em caso de database locked.

    Args:
        db: Conexão do banco de dados
        max_retries: Número máximo de tentativas

    Returns:
        True se commit foi bem-sucedido
    """
    last_error = None

    for attempt in range(max_retries):
        try:
            db.commit()
            return True
        except sqlite3.OperationalError as e:
            last_error = e
            if 'locked' in str(e).lower() or 'database is locked' in str(e).lower():
                logger.warning(f"Database locked ao fazer commit, tentando novamente ({attempt + 1}/{max_retries})...")
                # Exponential backoff com cap para evitar esperas muito longas
                backoff_time = 0.5 * (2 ** min(attempt, 5))  # Cap at 2^5 = 32x 0.5 = 16s
                time.sleep(backoff_time)
                continue
            else:
                raise
        except Exception as e:
            raise

    # Se chegou aqui, todas as tentativas falharam
    logger.error(f"Database ainda locked após {max_retries} tentativas ao fazer commit")
    raise DatabaseLockError(f"Database locked após {max_retries} tentativas") from last_error
