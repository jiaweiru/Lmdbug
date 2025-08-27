"""
User interface components for LMDB data preview.

This module provides the Gradio-based web interface for interacting
with LMDB databases and viewing protobuf data.
"""

from .gradio_interface import LmdbugInterface

__all__ = ["LmdbugInterface"]