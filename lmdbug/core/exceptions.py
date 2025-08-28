"""
Custom exception classes for Lmdbug.

This module defines specific exception types for different error scenarios
in LMDB operations, Protobuf handling, and data processing.
"""


class LmdbugError(Exception):
    """Base exception class for all Lmdbug-related errors."""
    pass


class DatabaseError(LmdbugError):
    """Raised for all database-related errors including connection, path, and operation issues."""
    pass


class ProtobufError(LmdbugError):
    """Raised for all protobuf-related errors including loading, parsing, and serialization issues."""
    pass


class DataProcessingError(LmdbugError):
    """Raised for data processing errors including key/value decoding issues."""
    pass