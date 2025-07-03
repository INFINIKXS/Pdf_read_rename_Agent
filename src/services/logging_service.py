
"""
Centralized Logging Service for the Document Intelligence Agent
- Logs to both console and rotating file handler
- Follows best practices for auditable, consistent logging
"""
import logging
from logging.handlers import RotatingFileHandler
import os

LOG_DIR = os.getenv("LOG_DIR", "logs")
LOG_FILE = os.path.join(LOG_DIR, "agent.log")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
MAX_BYTES = 2 * 1024 * 1024  # 2MB per log file
BACKUP_COUNT = 5

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def get_logger(name: str = "agent") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.hasHandlers():
        return logger
    logger.setLevel(LOG_LEVEL)
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(LOG_LEVEL)
    ch_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    ch.setFormatter(ch_formatter)
    # Rotating file handler
    fh = RotatingFileHandler(LOG_FILE, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT)
    fh.setLevel(LOG_LEVEL)
    fh_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    fh.setFormatter(fh_formatter)
    # Add handlers
    logger.addHandler(ch)
    logger.addHandler(fh)
    logger.propagate = False
    return logger
