import sys

from loguru import logger


def configure_logging(level: str = "INFO") -> None:
    """Configure application logging."""
    logger.remove()
    logger.add(sys.stderr, level=level.upper())
