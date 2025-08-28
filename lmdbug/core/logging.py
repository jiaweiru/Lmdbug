import sys
from pathlib import Path
from loguru import logger

# Remove default handler to have full control
logger.remove()

# Add default console handler
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
    # Remove all existing handlers
    logger.remove()

    # Auto-detect colorize setting
    if colorize is None:
        colorize = sys.stderr.isatty()

    # Console format
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

    # Console handler
    logger.add(
        sys.stderr,
        level=level,
        format=format_str,
        colorize=colorize,
        backtrace=True,
        diagnose=True,
    )

    # File handler if requested
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


def get_logger(name: str | None = None):
    """Get logger bound to a specific name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance bound to the name
    """
    return logger.bind(name=name) if name else logger
