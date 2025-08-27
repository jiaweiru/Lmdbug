"""
Lmdbug - LMDB Data Preview Tool

Provides preview functionality for LMDB format data, supporting parsing and visualization of Protobuf serialized data.
"""

import sys
from loguru import logger

__version__ = "0.1.0"
__author__ = "Lmdbug Project"

# Configure default logger
def configure_logger(level: str = "INFO", format_string: str = None):
    """
    Configure the default logger for the application.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        format_string: Custom format string for log messages
    """
    if format_string is None:
        format_string = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    
    logger.remove()  # Remove default handler
    logger.add(sys.stdout, level=level, format=format_string, colorize=True)
    logger.add("logs/lmdbug.log", level=level, format=format_string, rotation="10 MB", retention="7 days")

# Initialize with default configuration
configure_logger()

from .core.lmdb_reader import LMDBReader
from .core.protobuf_handler import ProtobufHandler
from .core.preview_service import PreviewService
from .ui.gradio_interface import LmdbugInterface

__all__ = ["LMDBReader", "ProtobufHandler", "PreviewService", "LmdbugInterface", "configure_logger"]