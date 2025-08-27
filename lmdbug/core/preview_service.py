from .lmdb_reader import LMDBReader
from .protobuf_handler import ProtobufHandler
from .exceptions import ProtobufError
from loguru import logger


class PreviewService:
    """Service for previewing LMDB data with Protobuf support."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.lmdb_reader = LMDBReader(db_path)
        self.protobuf_handler = ProtobufHandler()
        self.current_message_type: str | None = None
        
    def load_protobuf_modules(self, modules: list[dict[str, str]], default_message_type: str | None = None) -> bool:
        """Load protobuf modules."""
        for module_config in modules:
            module_path = module_config.get('path')
            message_class = module_config.get('message_class')
            if module_path and message_class:
                self.protobuf_handler.load_compiled_proto_module(module_path, message_class)
        
        if default_message_type:
            self.current_message_type = default_message_type
        return True
    
    def get_database_info(self) -> dict:
        """Get information about the LMDB database."""
        with self.lmdb_reader as reader:
            return {
                'database_path': str(self.db_path),
                'stats': reader.get_stats(),
                'protobuf_types': self.protobuf_handler.get_loaded_message_types(),
                'current_message_type': self.current_message_type
            }
    
    def preview_first_entries(self, count: int = 10) -> list[dict]:
        """Preview the first N entries from the database."""
        with self.lmdb_reader as reader:
            entries = reader.get_first_n_entries(count)
            return self._format_entries(entries)
    
    def preview_by_index_range(self, start_index: int, count: int = 10) -> list[dict]:
        """Preview entries by index range."""
        with self.lmdb_reader as reader:
            entries = reader.search_keys_by_index(start_index, count)
            return self._format_entries(entries)
    
    def search_by_key(self, key: str) -> dict:
        """Search for a specific key."""
        key_bytes = key.encode('utf-8')
        with self.lmdb_reader as reader:
            value = reader.get_by_key(key_bytes)
            if value is None:
                return {'error': f'Key not found: {key}'}
            
            formatted_entries = self._format_entries([(key_bytes, value)])
            return formatted_entries[0] if formatted_entries else {'error': 'Failed to format entry'}
    
    def search_by_key_prefix(self, prefix: str, limit: int = 100) -> list[dict]:
        """Search for keys with a specific prefix."""
        prefix_bytes = prefix.encode('utf-8')
        with self.lmdb_reader as reader:
            keys = reader.get_keys_with_prefix(prefix_bytes, limit)
            entries = [(key, reader.get_by_key(key)) for key in keys]
            # Filter out None values
            entries = [(k, v) for k, v in entries if v is not None]
            return self._format_entries(entries)
    
    def search_by_pattern(self, pattern: str, limit: int = 100) -> list[dict]:
        """Search for keys matching a pattern."""
        with self.lmdb_reader as reader:
            keys = reader.search_keys_by_pattern(pattern, limit)
            entries = [(key, reader.get_by_key(key)) for key in keys]
            # Filter out None values
            entries = [(k, v) for k, v in entries if v is not None]
            return self._format_entries(entries)
    
    def _format_entries(self, entries: list[tuple[bytes, bytes]]) -> list[dict]:
        """Format entries for display."""
        return [self._format_entry(key_bytes, value_bytes) for key_bytes, value_bytes in entries]
    
    def _format_entry(self, key_bytes: bytes, value_bytes: bytes) -> dict:
        """Format a single entry."""
        return {
            'key': self._format_key(key_bytes),
            'key_raw': key_bytes.hex(),
            'value_size': len(value_bytes),
            'value_info': self._format_value(value_bytes)
        }
    
    def _format_key(self, key_bytes: bytes) -> str:
        """Format a key for display."""
        try:
            return key_bytes.decode('utf-8')
        except UnicodeDecodeError:
            hex_str = key_bytes.hex()
            ascii_repr = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in key_bytes)
            return f"hex:{hex_str} ascii:{ascii_repr}"
    
    def _format_value(self, value_bytes: bytes) -> dict:
        """Format a value for display."""
        result = {
            'raw_hex': value_bytes.hex(),
            'size': len(value_bytes),
            'text_preview': self._get_text_preview(value_bytes)
        }
        
        # Try protobuf deserialization
        protobuf_types = self.protobuf_handler.get_loaded_message_types()
        if protobuf_types:
            protobuf_attempts = {}
            primary_protobuf = None
            
            # Try current message type first
            if self.current_message_type and self.current_message_type in protobuf_types:
                pb_result = self._try_protobuf_deserialize(value_bytes, self.current_message_type)
                if pb_result:
                    protobuf_attempts[self.current_message_type] = pb_result
                    primary_protobuf = pb_result
            
            # Try other types
            for msg_type in protobuf_types:
                if msg_type != self.current_message_type:
                    pb_result = self._try_protobuf_deserialize(value_bytes, msg_type)
                    if pb_result:
                        protobuf_attempts[msg_type] = pb_result
                        if not primary_protobuf:
                            primary_protobuf = pb_result
            
            result['protobuf_attempts'] = protobuf_attempts
            if primary_protobuf:
                result['primary_protobuf'] = primary_protobuf
        
        return result
    
    def _try_protobuf_deserialize(self, data: bytes, message_type: str) -> dict | None:
        """Try to deserialize data as a protobuf message type."""
        message = self.protobuf_handler.try_deserialize(data, message_type)
        if not message:
            return None
        
        try:
            return {
                'success': True,
                'json': self.protobuf_handler.message_to_json(message),
                'dict': self.protobuf_handler.message_to_dict(message)
            }
        except ProtobufError:
            logger.debug(f"Serialization failed for message type {message_type}")
            return None
    
    def _get_text_preview(self, data: bytes, max_length: int = 200) -> str:
        """Get a text preview of binary data."""
        text = data.decode('utf-8', errors='ignore')
        return text[:max_length] + "..." if len(text) > max_length else text
    
    def set_message_type(self, message_type: str) -> bool:
        """Set the current primary message type."""
        if message_type in self.protobuf_handler.get_loaded_message_types():
            self.current_message_type = message_type
            return True
        return False
    
    def get_available_message_types(self) -> list[str]:
        """Get list of available protobuf message types."""
        return self.protobuf_handler.get_loaded_message_types()