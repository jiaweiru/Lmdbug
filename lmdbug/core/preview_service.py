from .lmdb_reader import LMDBReader
from .protobuf_handler import ProtobufHandler
from .exceptions import ProtobufError
from .logging import get_logger

logger = get_logger(__name__)


class PreviewService:
    """Service for previewing LMDB data with Protobuf support."""
    
    def __init__(self, db_path: str, map_size: int = 10 * 1024 * 1024 * 1024):
        """Initialize preview service.
        
        Args:
            db_path: Path to the LMDB database
            map_size: Maximum size of the database in bytes (default: 10GB)
        """
        self.db_path = db_path
        self.lmdb_reader = LMDBReader(db_path, map_size=map_size)
        self.protobuf_handler = ProtobufHandler()
        self.current_message_type: str | None = None
        
    def load_protobuf_modules(self, modules: list[dict[str, str]], default_message_type: str | None = None) -> bool:
        """Load protobuf modules."""
        for module_config in modules:
            if module_path := module_config.get('path'):
                if message_class := module_config.get('message_class'):
                    self.protobuf_handler.load_compiled_proto_module(module_path, message_class)
        
        if default_message_type:
            self.current_message_type = default_message_type
        return True
    
    def set_message_type(self, message_type: str):
        """Set the current message type for protobuf deserialization."""
        if message_type not in self.protobuf_handler.get_loaded_message_types():
            raise ValueError(f"Message type '{message_type}' not loaded")
        self.current_message_type = message_type
    
    def get_database_info(self) -> dict:
        """Get information about the LMDB database."""
        with self.lmdb_reader as reader:
            return {
                'database_path': str(self.db_path),
                'stats': reader.get_stats(),
                'env_info': reader.get_env_info(),
                'protobuf_types': self.protobuf_handler.get_loaded_message_types(),
                'current_message_type': self.current_message_type
            }
    
    def preview_first_entries(self, count: int = 10) -> list[dict]:
        """Preview the first N entries from the database."""
        with self.lmdb_reader as reader:
            entries = reader.get_first_n_entries(count)
            return [self._format_entry(key_bytes, value_bytes) for key_bytes, value_bytes in entries]
    
    def preview_by_index_range(self, start_index: int, count: int = 10) -> list[dict]:
        """Preview entries by index range."""
        with self.lmdb_reader as reader:
            entries = reader.search_keys_by_index(start_index, count)
            return [self._format_entry(key_bytes, value_bytes) for key_bytes, value_bytes in entries]
    
    def search_by_key(self, key: str) -> dict:
        """Search for a specific key."""
        key_bytes = key.encode('utf-8')
        with self.lmdb_reader as reader:
            value = reader.get_by_key(key_bytes)
            if value is None:
                return {'error': f'Key not found: {key}'}
            return self._format_entry(key_bytes, value)
    
    def search_by_key_prefix(self, prefix: str, limit: int = 100) -> list[dict]:
        """Search for keys with a specific prefix."""
        prefix_bytes = prefix.encode('utf-8')
        with self.lmdb_reader as reader:
            keys = reader.get_keys_with_prefix(prefix_bytes, limit)
            return self._get_entries_by_keys(reader, keys)
    
    def search_by_pattern(self, pattern: str, limit: int = 100) -> list[dict]:
        """Search for keys matching a pattern."""
        with self.lmdb_reader as reader:
            keys = reader.search_keys_by_pattern(pattern, limit)
            return self._get_entries_by_keys(reader, keys)
    
    def _get_entries_by_keys(self, reader, keys: list[bytes]) -> list[dict]:
        """Get and format entries by keys, filtering out None values."""
        entries = [(key, reader.get_by_key(key)) for key in keys]
        valid_entries = [(k, v) for k, v in entries if v is not None]
        return [self._format_entry(key_bytes, value_bytes) for key_bytes, value_bytes in valid_entries]
    
    def _format_entry(self, key_bytes: bytes, value_bytes: bytes) -> dict:
        """Format a single entry."""
        return {
            'key': self._format_key(key_bytes) or key_bytes.hex(),
            'key_raw': key_bytes.hex(),
            'value_size': len(value_bytes),
            'value_info': self._format_value(value_bytes)
        }
    
    def _format_key(self, key_bytes: bytes) -> str | None:
        """Format a key for display."""
        try:
            return key_bytes.decode('utf-8')
        except UnicodeDecodeError:
            return None
    
    def _format_value(self, value_bytes: bytes) -> dict:
        """Format a value for display."""
        result = {
            'raw_hex': value_bytes.hex(),
            'size': len(value_bytes)
        }
        
        if self._should_try_protobuf():
            self._add_protobuf_info(result, value_bytes, self.current_message_type)
        
        return result
    
    def _should_try_protobuf(self) -> bool:
        """Check if protobuf deserialization should be attempted."""
        return (self.current_message_type and 
                self.current_message_type in self.protobuf_handler.get_loaded_message_types())
    
    def _add_protobuf_info(self, result: dict, value_bytes: bytes, message_type: str | None) -> None:
        """Add protobuf information to result dict."""
        if not message_type or message_type not in self.protobuf_handler.get_loaded_message_types():
            if message_type:
                result['protobuf_error'] = f"Message type '{message_type}' not loaded"
            return
        
        try:
            message = self.protobuf_handler.deserialize(value_bytes, message_type)
            result['protobuf'] = {
                'success': True,
                'json': self.protobuf_handler.message_to_json(message),
                'dict': self.protobuf_handler.message_to_dict(message)
            }
            result['message_type_used'] = message_type
        except ProtobufError:
            logger.debug(f"Failed to deserialize with type: {message_type}")
            result['protobuf_error'] = f"Failed to deserialize with type: {message_type}"
    
    
    
    def get_available_message_types(self) -> list[str]:
        """Get list of available protobuf message types."""
        return self.protobuf_handler.get_loaded_message_types()