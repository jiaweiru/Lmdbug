from .lmdb_reader import LMDBReader
from .protobuf_handler import ProtobufHandler
from loguru import logger

# Type aliases
DatabaseInfo = dict[str, str | dict[str, int] | list[str]]
EntryResult = dict[str, str | int | dict]


class PreviewService:
    """
    Service for previewing LMDB data with Protobuf support.
    Handles key searching, data formatting, and preview generation.
    """
    
    def __init__(self, db_path: str):
        """
        Initialize the preview service.
        
        Args:
            db_path: Path to the LMDB database
        """
        self.db_path = db_path
        self.lmdb_reader = LMDBReader(db_path)
        self.protobuf_handler = ProtobufHandler()
        self.current_message_type: str | None = None
        
    def load_protobuf_modules(self, modules: list[dict[str, str]], default_message_type: str | None = None) -> bool:
        """
        Load protobuf modules.
        
        Args:
            modules: List of module configurations with 'path' and 'message_class'
            default_message_type: Default message type to use
            
        Returns:
            True if loading successful
        """
        try:
            # Load compiled protobuf modules
            for module_config in modules:
                module_path = module_config.get('path')
                message_class = module_config.get('message_class')
                if module_path and message_class:
                    self.protobuf_handler.load_compiled_proto_module(module_path, message_class)
            
            # Set default message type
            if default_message_type:
                self.current_message_type = default_message_type
                
            return True
        except Exception as e:
            logger.error(f"Failed to load protobuf modules: {e}")
            return False
    
    def get_database_info(self) -> DatabaseInfo:
        """
        Get information about the LMDB database.
        
        Returns:
            Dictionary containing database information
        """
        try:
            with self.lmdb_reader as reader:
                stats = reader.get_stats()
                protobuf_types = self.protobuf_handler.get_loaded_message_types()
                
                return {
                    'database_path': str(self.db_path),
                    'stats': stats,
                    'protobuf_types': protobuf_types,
                    'current_message_type': self.current_message_type
                }
        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            return {'error': str(e)}
    
    def preview_first_entries(self, count: int = 10) -> list[EntryResult]:
        """
        Preview the first N entries from the database.
        
        Args:
            count: Number of entries to preview
            
        Returns:
            List of formatted entries
        """
        try:
            with self.lmdb_reader as reader:
                entries = reader.get_first_n_entries(count)
                return self._format_entries(entries)
        except Exception as e:
            logger.error(f"Failed to preview first entries: {e}")
            return [{'error': str(e)}]
    
    def preview_by_index_range(self, start_index: int, count: int = 10) -> list[EntryResult]:
        """
        Preview entries by index range.
        
        Args:
            start_index: Starting index (0-based)
            count: Number of entries to retrieve
            
        Returns:
            List of formatted entries
        """
        try:
            with self.lmdb_reader as reader:
                entries = reader.search_keys_by_index(start_index, count)
                return self._format_entries(entries)
        except Exception as e:
            logger.error(f"Failed to preview by index range: {e}")
            return [{'error': str(e)}]
    
    def search_by_key(self, key: str) -> EntryResult:
        """
        Search for a specific key.
        
        Args:
            key: The key to search for (will be encoded to bytes)
            
        Returns:
            Formatted entry data or error information
        """
        try:
            key_bytes = key.encode('utf-8')
            with self.lmdb_reader as reader:
                value = reader.get_by_key(key_bytes)
                if value is not None:
                    entry = (key_bytes, value)
                    formatted_entries = self._format_entries([entry])
                    return formatted_entries[0] if formatted_entries else {'error': 'Failed to format entry'}
                else:
                    return {'error': f'Key not found: {key}'}
        except Exception as e:
            logger.error(f"Failed to search by key '{key}': {e}")
            return {'error': str(e)}
    
    def search_by_key_prefix(self, prefix: str, limit: int = 100) -> list[EntryResult]:
        """
        Search for keys with a specific prefix.
        
        Args:
            prefix: The prefix to search for
            limit: Maximum number of results
            
        Returns:
            List of formatted entries
        """
        try:
            prefix_bytes = prefix.encode('utf-8')
            with self.lmdb_reader as reader:
                keys = reader.get_keys_with_prefix(prefix_bytes, limit)
                entries = []
                for key in keys:
                    value = reader.get_by_key(key)
                    if value is not None:
                        entries.append((key, value))
                return self._format_entries(entries)
        except Exception as e:
            logger.error(f"Failed to search by key prefix '{prefix}': {e}")
            return [{'error': str(e)}]
    
    def search_by_pattern(self, pattern: str, limit: int = 100) -> list[EntryResult]:
        """
        Search for keys matching a pattern.
        
        Args:
            pattern: The pattern to search for
            limit: Maximum number of results
            
        Returns:
            List of formatted entries
        """
        try:
            with self.lmdb_reader as reader:
                keys = reader.search_keys_by_pattern(pattern, limit)
                entries = []
                for key in keys:
                    value = reader.get_by_key(key)
                    if value is not None:
                        entries.append((key, value))
                return self._format_entries(entries)
        except Exception as e:
            logger.error(f"Failed to search by pattern '{pattern}': {e}")
            return [{'error': str(e)}]
    
    def _format_entries(self, entries: list[tuple[bytes, bytes]]) -> list[EntryResult]:
        """
        Format entries for display.
        
        Args:
            entries: List of (key, value) tuples
            
        Returns:
            List of formatted entry dictionaries
        """
        formatted = []
        
        for key_bytes, value_bytes in entries:
            try:
                # Format key
                key_str = self._format_key(key_bytes)
                
                # Format value
                value_info = self._format_value(value_bytes)
                
                formatted_entry = {
                    'key': key_str,
                    'key_raw': key_bytes.hex(),
                    'value_size': len(value_bytes),
                    'value_info': value_info
                }
                
                formatted.append(formatted_entry)
                
            except Exception as e:
                logger.error(f"Failed to format entry: {e}")
                formatted.append({
                    'key': f'<error: {e}>',
                    'key_raw': key_bytes.hex() if key_bytes else '',
                    'value_size': len(value_bytes) if value_bytes else 0,
                    'value_info': {'error': str(e)}
                })
        
        return formatted
    
    def _format_key(self, key_bytes: bytes) -> str:
        """
        Format a key for display.
        
        Args:
            key_bytes: The key as bytes
            
        Returns:
            Formatted key string
        """
        try:
            # Try to decode as UTF-8
            return key_bytes.decode('utf-8')
        except UnicodeDecodeError:
            # If decode fails, show as hex with ASCII representation
            hex_str = key_bytes.hex()
            ascii_repr = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in key_bytes)
            return f"hex:{hex_str} ascii:{ascii_repr}"
    
    def _format_value(self, value_bytes: bytes) -> dict[str, str | int | dict]:
        """
        Format a value for display, attempting Protobuf deserialization if configured.
        
        Args:
            value_bytes: The value as bytes
            
        Returns:
            Dictionary containing value information
        """
        result = {
            'raw_hex': value_bytes.hex(),
            'size': len(value_bytes),
            'protobuf_attempts': {},
            'text_preview': self._get_text_preview(value_bytes)
        }
        
        # Try protobuf deserialization if we have loaded message types
        protobuf_types = self.protobuf_handler.get_loaded_message_types()
        if protobuf_types:
            if self.current_message_type and self.current_message_type in protobuf_types:
                # Try with the current message type first
                pb_result = self._try_protobuf_deserialize(value_bytes, self.current_message_type)
                if pb_result:
                    result['protobuf_attempts'][self.current_message_type] = pb_result
                    result['primary_protobuf'] = pb_result
            
            # Try all other loaded types
            for msg_type in protobuf_types:
                if msg_type != self.current_message_type:
                    pb_result = self._try_protobuf_deserialize(value_bytes, msg_type)
                    if pb_result:
                        result['protobuf_attempts'][msg_type] = pb_result
                        if 'primary_protobuf' not in result:
                            result['primary_protobuf'] = pb_result
        
        return result
    
    def _try_protobuf_deserialize(self, data: bytes, message_type: str) -> dict[str, str | bool | dict] | None:
        """
        Try to deserialize data as a specific protobuf message type.
        
        Args:
            data: Binary data to deserialize
            message_type: Message type to try
            
        Returns:
            Dictionary with deserialized data or None if failed
        """
        try:
            message = self.protobuf_handler.deserialize(data, message_type)
            if message:
                return {
                    'success': True,
                    'json': self.protobuf_handler.message_to_json(message),
                    'dict': self.protobuf_handler.message_to_dict(message)
                }
        except Exception as e:
            logger.debug(f"Failed to deserialize as {message_type}: {e}")
        
        return None
    
    def _get_text_preview(self, data: bytes, max_length: int = 200) -> str:
        """
        Get a text preview of binary data.
        
        Args:
            data: Binary data
            max_length: Maximum length of preview
            
        Returns:
            Text preview string
        """
        try:
            # Try UTF-8 decode first
            text = data.decode('utf-8', errors='ignore')
            if len(text) > max_length:
                text = text[:max_length] + "..."
            return text
        except Exception:
            # Fallback to ASCII representation
            ascii_repr = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in data[:max_length])
            if len(data) > max_length:
                ascii_repr += "..."
            return ascii_repr
    
    def set_message_type(self, message_type: str) -> bool:
        """
        Set the current primary message type for protobuf deserialization.
        
        Args:
            message_type: The message type name
            
        Returns:
            True if the message type is valid and set
        """
        if message_type in self.protobuf_handler.get_loaded_message_types():
            self.current_message_type = message_type
            return True
        return False
    
    def get_available_message_types(self) -> list[str]:
        """
        Get list of available protobuf message types.
        
        Returns:
            List of message type names
        """
        return self.protobuf_handler.get_loaded_message_types()