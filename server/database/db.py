"""
SENTINEL PHANTOM — Servidor Central: Base de datos SQL Server
Capa de acceso con pyodbc. Pool de conexiones simple + context manager.
"""

import os
import threading
from contextlib import contextmanager
from typing import Any, Generator, Optional

import pyodbc
from dotenv import load_dotenv

load_dotenv()

# ── Config desde .env ─────────────────────────────────────────────────────────
_SERVER   = os.getenv("DB_SERVER",   "localhost")
_DATABASE = os.getenv("DB_NAME",     "SentinelPhantom")
_UID      = os.getenv("DB_USER",     "sa")
_PWD      = os.getenv("DB_PASSWORD", "")
_DRIVER   = os.getenv("DB_DRIVER",   "ODBC Driver 17 for SQL Server")

_CONNECTION_STRING = (
    f"DRIVER={{{_DRIVER}}};"
    f"SERVER={_SERVER};"
    f"DATABASE={_DATABASE};"
    f"UID={_UID};"
    f"PWD={_PWD};"
    f"TrustServerCertificate=yes;"
)

# ── Pool simple (una conexión por thread) ─────────────────────────────────────
_local = threading.local()


def _get_conn() -> pyodbc.Connection:
    if not getattr(_local, "conn", None):
        _local.conn = pyodbc.connect(_CONNECTION_STRING, autocommit=False)
    return _local.conn


@contextmanager
def get_cursor() -> Generator[pyodbc.Cursor, None, None]:
    """
    Context manager que abre un cursor, hace commit al salir
    o rollback si hay excepción.
    """
    conn = _get_conn()
    cur  = conn.cursor()
    try:
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


def close_thread_connection() -> None:
    """Llama al final de cada request Flask para cerrar la conexión del thread."""
    conn = getattr(_local, "conn", None)
    if conn:
        conn.close()
        _local.conn = None


# ── Helpers de escritura ──────────────────────────────────────────────────────

def execute(sql: str, params: tuple = ()) -> None:
    with get_cursor() as cur:
        cur.execute(sql, params)


def executemany(sql: str, data: list[tuple]) -> None:
    with get_cursor() as cur:
        cur.executemany(sql, data)


def fetchall(sql: str, params: tuple = ()) -> list[dict]:
    with get_cursor() as cur:
        cur.execute(sql, params)
        cols = [col[0] for col in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def fetchone(sql: str, params: tuple = ()) -> Optional[dict]:
    with get_cursor() as cur:
        cur.execute(sql, params)
        cols = [col[0] for col in cur.description]
        row  = cur.fetchone()
        return dict(zip(cols, row)) if row else None


def test_connection() -> bool:
    try:
        result = fetchone("SELECT 1 AS ok")
        return result is not None
    except Exception as exc:
        print(f"[DB] Error de conexión: {exc}")
        return False