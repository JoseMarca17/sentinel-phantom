"""
SENTINEL PHANTOM - Logger Central
Logging estructurado con salida a consola y archivo rotativo.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional


def _ensure_dir(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Devuelve un logger con el nombre dado, configurado con:
    - StreamHandler (consola con color ANSI)
    - RotatingFileHandler (archivo, máx 5 MB × 3 backups)
    Si el logger ya existe, lo retorna directamente.
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger  # ya configurado

    # Nivel
    from config import LOG_LEVEL, LOG_FILE
    effective_level = getattr(logging, (level or LOG_LEVEL).upper(), logging.INFO)
    logger.setLevel(effective_level)

    fmt = logging.Formatter(
        fmt="%(asctime)s  [%(levelname)-8s]  %(name)-28s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ── Consola ───────────────────────────────────────────────────────────────
    ch = logging.StreamHandler()
    ch.setLevel(effective_level)
    ch.setFormatter(_ColorFormatter(fmt))
    logger.addHandler(ch)

    # ── Archivo ───────────────────────────────────────────────────────────────
    try:
        _ensure_dir(LOG_FILE)
        fh = RotatingFileHandler(LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
        fh.setLevel(effective_level)
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    except Exception as exc:
        logger.warning(f"No se pudo crear el archivo de log ({LOG_FILE}): {exc}")

    logger.propagate = False
    return logger


# ── ANSI color formatter ──────────────────────────────────────────────────────
_COLORS = {
    "DEBUG":    "\033[36m",   # cyan
    "INFO":     "\033[32m",   # green
    "WARNING":  "\033[33m",   # yellow
    "ERROR":    "\033[31m",   # red
    "CRITICAL": "\033[35m",   # magenta
}
_RESET = "\033[0m"


class _ColorFormatter(logging.Formatter):
    def __init__(self, base_fmt: logging.Formatter):
        super().__init__()
        self._base = base_fmt

    def format(self, record: logging.LogRecord) -> str:
        color = _COLORS.get(record.levelname, "")
        msg = self._base.format(record)
        return f"{color}{msg}{_RESET}" if color else msg