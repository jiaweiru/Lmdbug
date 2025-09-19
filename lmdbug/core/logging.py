import sys
from pathlib import Path
from loguru import logger

logger.remove()

logger.add(
    sys.stderr,
    level="INFO",
    format=(
        "<green>{time:HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    ),
    colorize=True,
    backtrace=True,
    diagnose=True,
)


def setup(
    level: str = "INFO", file: str | Path | None = None, colorize: bool | None = None
):
    """Setup logging configuration.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        file: Optional log file path
        colorize: Enable colors (auto-detects if None)
    """
    logger.remove()

    if colorize is None:
        colorize = sys.stderr.isatty()

    format_str = (
        (
            "<green>{time:HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        )
        if colorize
        else ("{time:HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}")
    )

    logger.add(
        sys.stderr,
        level=level,
        format=format_str,
        colorize=colorize,
        backtrace=True,
        diagnose=True,
    )

    if file:
        file_path = Path(file)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        logger.add(
            str(file_path),
            level=level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="10 MB",
            retention="7 days",
            compression="zip",
            backtrace=True,
            diagnose=True,
            enqueue=True,
        )


def get_logger():
    """Return the shared application logger."""
    return logger
