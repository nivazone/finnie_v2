import logging
from logging.handlers import RotatingFileHandler
import sys
from pathlib import Path

def setup_logger(
    name: str = "Finnie",
    level: int = logging.INFO,
    *,
    to_console: bool = False,
    log_path: str | Path = "finnie.log",
    max_bytes: int = 5_000_000,        # 5 MB before rotating
    backup_count: int = 0,
) -> logging.Logger:
    """
    Create (or return) the named logger.
    By default everything goes to finnie.log, not to stdout.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )

    fmt = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt, datefmt=datefmt)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    if to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    logger.propagate = False
    return logger

log = setup_logger()

