"""
Ultra-reliable logging utility with rotation and Windows path handling
"""
import logging
import logging.handlers
import os
from pathlib import Path
from datetime import datetime

BASE_PATH = Path("C:\\Users\\mpmmo\\FULL-LOCAL-PRODUCTION\\Telegram_Discord")
LOG_PATH = BASE_PATH / "logs"

# Ensure log directory exists
LOG_PATH.mkdir(parents=True, exist_ok=True)


def setup_logger(name: str, log_file: str = None, level=logging.INFO):
    """
    Create a logger with both file and console handlers

    Args:
        name: Logger name (usually module name)
        log_file: Optional specific log file name
        level: Logging level

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Clear existing handlers to prevent duplicates from process reloads
    # This is critical for PM2 restarts where Python logger state persists
    if logger.handlers:
        logger.handlers.clear()

    logger.setLevel(level)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)

    # File handler with rotation
    if log_file:
        file_path = LOG_PATH / log_file
    else:
        file_path = LOG_PATH / f"{name}.log"

    file_handler = logging.handlers.RotatingFileHandler(
        str(file_path),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(level)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


def get_logger(name: str, log_dir: str = None, filename: str = None):
    """Backwards compatible wrapper for setup_logger"""
    if filename:
        return setup_logger(name, filename)
    return setup_logger(name)


def log_exception(logger, exc, context=""):
    """Log exception with full traceback"""
    import traceback
    logger.error(f"Exception in {context}: {str(exc)}")
    logger.error(f"Traceback:\n{traceback.format_exc()}")


def log_rate_limit(logger, error_code, retry_after=None):
    """Log rate limit errors with remediation advice"""
    if error_code == 429:
        msg = f"Rate limit hit (429). Retry after: {retry_after}s"
        logger.warning(msg)
        logger.info("Remediation: Implementing exponential backoff")
    elif error_code == 1015:
        msg = "Discord rate limit (1015) - too many messages"
        logger.warning(msg)
        logger.info("Remediation: Reduce batch size or add delays")


def log_health_check(logger, service_name, status="healthy", details=None):
    """Log service health status"""
    timestamp = datetime.now().isoformat()
    msg = f"[HEALTH] {service_name} | {status} | {timestamp}"
    if details:
        msg += f" | {details}"

    if status == "healthy":
        logger.info(msg)
    else:
        logger.warning(msg)