"""
Custom exception classes for Lmdbug.

This module defines specific exception types for different error scenarios
in LMDB operations, Protobuf handling, and data processing.
"""


class LmdbugError(Exception):
    """Base exception class for all Lmdbug-related errors."""
    pass


class DatabaseError(LmdbugError):
    """Base class for database-related errors."""
    pass


class DatabaseNotFoundError(DatabaseError):
    """Raised when the LMDB database path does not exist."""
    pass


class DatabasePathError(DatabaseError):
    """Raised when the database path is invalid (not a directory)."""
    pass


class DatabaseNotOpenError(DatabaseError):
    """Raised when attempting operations on a closed database."""
    pass


class DatabaseConnectionError(DatabaseError):
    """Raised when failing to open/connect to the database."""
    pass


class ProtobufError(LmdbugError):
    """Base class for protobuf-related errors."""
    pass


class ProtobufModuleNotFoundError(ProtobufError):
    """Raised when a protobuf module file cannot be found."""
    pass


class ProtobufModuleLoadError(ProtobufError):
    """Raised when failing to load a protobuf module."""
    pass


class ProtobufMessageClassNotFoundError(ProtobufError):
    """Raised when a message class is not found in the protobuf module."""
    pass


class ProtobufMessageTypeNotLoadedError(ProtobufError):
    """Raised when attempting to use an unloaded message type."""
    pass


class ProtobufDeserializationError(ProtobufError):
    """Raised when protobuf deserialization fails."""
    pass


class ProtobufSerializationError(ProtobufError):
    """Raised when protobuf serialization (to dict/json) fails."""
    pass


class DataProcessingError(LmdbugError):
    """Base class for data processing errors."""
    pass


class KeyDecodingError(DataProcessingError):
    """Raised when failing to decode a database key."""
    pass


class ValueProcessingError(DataProcessingError):
    """Raised when failing to process a database value."""
    pass