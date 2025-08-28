"""
Lmdbug - LMDB Data Preview Tool

Provides preview functionality for LMDB format data, supporting parsing and visualization of Protobuf serialized data.
"""

from .core import logging

__version__ = "0.1.0"
__author__ = "Lmdbug Project"

# Backwards compatibility
configure_logger = logging.setup

from .core.lmdb_reader import LMDBReader
from .core.protobuf_handler import ProtobufHandler
from .core.preview_service import PreviewService
from .ui.gradio_interface import LmdbugInterface

__all__ = ["LMDBReader", "ProtobufHandler", "PreviewService", "LmdbugInterface", "configure_logger"]