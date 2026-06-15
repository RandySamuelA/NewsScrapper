"""
logger.py
Setup logger untuk NewsScrapper.
"""

import logging
import os
from configparser import ConfigParser


def setup_logger(config: ConfigParser) -> logging.Logger:
    """Setup logger dengan output ke file dan console. Idempotent."""
    logger = logging.getLogger("NewsScrapper")
    if logger.handlers:
        return logger  # Sudah disetup sebelumnya

    logger.setLevel(logging.DEBUG)

    # Formatter
    fmt = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # File handler
    log_file = config.get("settings", "log_file", fallback="logs/app.log")
    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    return logger
