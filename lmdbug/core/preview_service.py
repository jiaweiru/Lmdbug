from .lmdb_reader import LMDBReader
from .protobuf_handler import ProtobufHandler
from .exceptions import ProtobufError
from .logging import get_logger
import importlib.util
import json
from pathlib import Path

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
        self.field_config: dict[str, dict] = {}

    def load_protobuf_modules(
        self, modules: list[dict[str, str]], default_message_type: str | None = None
    ) -> None:
        """Loads protobuf modules.
        
        Args:
            modules: List of module configurations with 'path' and 'message_class'.
            default_message_type: Default message type to set.
        
        Raises:
            ProtobufError: If any protobuf module fails to load.
            ValueError: If module configuration is invalid.
        """
        if not modules:
            raise ValueError("No protobuf modules provided")
            
        loaded_count = 0
        errors = []
        
        for module_config in modules:
            module_path = module_config.get("path")
            message_class = module_config.get("message_class")
            
            if not module_path:
                errors.append("Missing module path in configuration")
                continue
            if not message_class:
                errors.append(f"Missing message class for module {module_path}")
                continue
                
            try:
                self.protobuf_handler.load_compiled_proto_module(
                    module_path, message_class
                )
                loaded_count += 1
                logger.info(f"Successfully loaded {message_class} from {module_path}")
            except Exception as e:
                error_msg = f"Failed to load {message_class} from {module_path}: {e}"
                errors.append(error_msg)
                logger.error(error_msg)

        if errors:
            raise ProtobufError(f"Failed to load {len(errors)} modules: {'; '.join(errors)}")
        
        if loaded_count == 0:
            raise ProtobufError("No protobuf modules were loaded successfully")

        if default_message_type:
            self.current_message_type = default_message_type
            
        logger.info(f"Successfully loaded {loaded_count} protobuf modules")

    def set_message_type(self, message_type: str):
        """Sets the current message type for protobuf deserialization.
        
        Args:
            message_type: Name of the protobuf message type.
            
        Raises:
            ValueError: If message type is not loaded.
        """
        if message_type not in self.protobuf_handler.get_loaded_message_types():
            raise ValueError(f"Message type '{message_type}' not loaded")
        self.current_message_type = message_type

    def get_database_info(self) -> dict:
        """Gets information about the LMDB database.
        
        Returns:
            Dictionary with database information.
        """
        with self.lmdb_reader as reader:
            return {
                "database_path": str(self.db_path),
                "stats": reader.get_stats(),
                "env_info": reader.get_env_info(),
                "protobuf_types": self.protobuf_handler.get_loaded_message_types(),
                "current_message_type": self.current_message_type,
            }

    def preview_first_entries(self, count: int = 10) -> list[dict]:
        """Previews the first N entries from the database.
        
        Args:
            count: Number of entries to preview.
            
        Returns:
            List of formatted entries.
        """
        with self.lmdb_reader as reader:
            entries = reader.get_first_n_entries(count)
            return [
                self._format_entry(key_bytes, value_bytes)
                for key_bytes, value_bytes in entries
            ]

    def preview_by_index_range(self, start_index: int, count: int = 10) -> list[dict]:
        """Previews entries by index range.
        
        Args:
            start_index: Starting index.
            count: Number of entries to preview.
            
        Returns:
            List of formatted entries.
        """
        with self.lmdb_reader as reader:
            entries = reader.search_keys_by_index(start_index, count)
            return [
                self._format_entry(key_bytes, value_bytes)
                for key_bytes, value_bytes in entries
            ]

    def search_by_key(self, key: str) -> dict:
        """Searches for a specific key.
        
        Args:
            key: Key to search for.
            
        Returns:
            Formatted entry or error information.
        """
        key_bytes = key.encode("utf-8")
        with self.lmdb_reader as reader:
            value = reader.get_by_key(key_bytes)
            if value is None:
                return {"error": f"Key not found: {key}"}
            return self._format_entry(key_bytes, value)

    def search_by_key_prefix(self, prefix: str, limit: int = 100) -> list[dict]:
        """Searches for keys with a specific prefix.
        
        Args:
            prefix: Key prefix to search for.
            limit: Maximum number of results.
            
        Returns:
            List of formatted entries.
        """
        prefix_bytes = prefix.encode("utf-8")
        with self.lmdb_reader as reader:
            keys = reader.get_keys_with_prefix(prefix_bytes, limit)
            return self._get_entries_by_keys(reader, keys)

    def search_by_pattern(self, pattern: str, limit: int = 100) -> list[dict]:
        """Searches for keys matching a pattern.
        
        Args:
            pattern: Pattern to search for in keys.
            limit: Maximum number of results.
            
        Returns:
            List of formatted entries.
        """
        with self.lmdb_reader as reader:
            keys = reader.search_keys_by_pattern(pattern, limit)
            return self._get_entries_by_keys(reader, keys)

    def _get_entries_by_keys(self, reader, keys: list[bytes]) -> list[dict]:
        """Gets and formats entries by keys, filtering out None values.
        
        Args:
            reader: LMDB reader instance.
            keys: List of keys to fetch.
            
        Returns:
            List of formatted entries.
        """
        entries = [(key, reader.get_by_key(key)) for key in keys]
        valid_entries = [(k, v) for k, v in entries if v is not None]
        return [
            self._format_entry(key_bytes, value_bytes)
            for key_bytes, value_bytes in valid_entries
        ]

    def _format_entry(self, key_bytes: bytes, value_bytes: bytes) -> dict:
        """Formats a single entry.
        
        Args:
            key_bytes: Raw key bytes.
            value_bytes: Raw value bytes.
            
        Returns:
            Dictionary with formatted entry information.
        """
        return {
            "key": self._format_key(key_bytes) or key_bytes.hex(),
            "key_raw": key_bytes.hex(),
            "value_size": len(value_bytes),
            "value_info": self._format_value(value_bytes),
        }

    def _format_key(self, key_bytes: bytes) -> str | None:
        """Formats a key for display.
        
        Args:
            key_bytes: Raw key bytes.
            
        Returns:
            UTF-8 decoded key string or None if decoding fails.
        """
        try:
            return key_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return None

    def _format_value(self, value_bytes: bytes) -> dict:
        """Formats a value for display.
        
        Args:
            value_bytes: Raw value bytes.
            
        Returns:
            Dictionary with formatted value information.
        """
        result = {"raw_hex": value_bytes.hex(), "size": len(value_bytes)}

        if self._should_try_protobuf():
            self._add_protobuf_info(result, value_bytes, self.current_message_type)

        return result

    def _should_try_protobuf(self) -> bool:
        """Checks if protobuf deserialization should be attempted.
        
        Returns:
            True if protobuf deserialization should be tried.
        """
        return (
            self.current_message_type
            and self.current_message_type
            in self.protobuf_handler.get_loaded_message_types()
        )

    def _add_protobuf_info(
        self, result: dict, value_bytes: bytes, message_type: str | None
    ) -> None:
        """Adds protobuf information to result dict.
        
        Args:
            result: Result dictionary to update.
            value_bytes: Raw value bytes to deserialize.
            message_type: Protobuf message type name.
        """
        if (
            not message_type
            or message_type not in self.protobuf_handler.get_loaded_message_types()
        ):
            if message_type:
                result["protobuf_error"] = f"Message type '{message_type}' not loaded"
            return

        try:
            message = self.protobuf_handler.deserialize(value_bytes, message_type)
            message_dict = self.protobuf_handler.message_to_dict(message)
            
            result["protobuf"] = {
                "dict": message_dict,
            }
            result["message_type_used"] = message_type
            
            field_config = self.get_field_config(message_type)
            if field_config:
                media_previews = self.protobuf_handler.process_media_fields(
                    message_dict, field_config
                )
                if any(media_previews.values()):
                    result["media_previews"] = media_previews
        except ProtobufError as e:
            logger.warning(
                f"Failed to deserialize {len(value_bytes)} bytes with message type '{message_type}': {e}"
            )
            result["protobuf_error"] = f"Failed to deserialize with type '{message_type}': {str(e)}"
        except Exception as e:
            logger.error(
                f"Unexpected error during protobuf deserialization for type '{message_type}' "
                f"with {len(value_bytes)} bytes: {e}",
                exc_info=True
            )
            result["protobuf_error"] = f"Unexpected error with type '{message_type}': {str(e)}"

    def get_available_message_types(self) -> list[str]:
        """Gets list of available protobuf message types.
        
        Returns:
            List of message type names.
        """
        return self.protobuf_handler.get_loaded_message_types()

    def set_field_config(self, message_type: str, config: dict[str, dict]):
        """Sets field configuration for a message type.
        
        Args:
            message_type: The protobuf message type name.
            config: Field configuration mapping field names to processor configs.
                    e.g. {"audio_data": {"processor": "pcm_audio", "config": {"sample_rate": 16000}}}
        """
        self.field_config[message_type] = config
        logger.info(f"Updated field config for {message_type}: {config}")

    def get_field_config(self, message_type: str | None = None) -> dict[str, dict]:
        """Gets field configuration for a message type.
        
        Args:
            message_type: Message type name, uses current type if None.
            
        Returns:
            Field configuration dictionary.
        """
        if message_type is None:
            message_type = self.current_message_type
        return self.field_config.get(message_type, {})

    def register_custom_processor(self, processor_name: str, processor_func: callable):
        """Registers a custom field processor function.
        
        Args:
            processor_name: Name of the processor.
            processor_func: Function with signature (field_name: str, value: any, config: dict) -> dict.
                          Should return dict with keys: type, field_name, and other preview data.
        """
        self.protobuf_handler.register_custom_processor(processor_name, processor_func)

    def custom_processor(self, processor_name: str):
        """Decorator to register a custom field processor.
        
        Args:
            processor_name: Name of the processor.
            
        Usage:
            @preview_service.custom_processor("pcm_audio")
            def process_pcm_audio(field_name: str, value: bytes, config: dict) -> dict:
                # Custom processing logic
                return {"type": "audio", "temp_path": wav_file}
        """
        return self.protobuf_handler.custom_processor(processor_name)

    def load_custom_processors(self, processor_file_path: str) -> None:
        """Loads custom processors from a Python file.
        
        Args:
            processor_file_path: Path to the Python file containing custom processors.
            
        Raises:
            FileNotFoundError: If processor file doesn't exist.
            ImportError: If file cannot be imported.
            SyntaxError: If file has syntax errors.
            ValueError: If file doesn't contain required functions.
        """
        processor_path = Path(processor_file_path)
        if not processor_path.exists():
            raise FileNotFoundError(f"Processor file not found: {processor_file_path}")

        spec = importlib.util.spec_from_file_location(
            f"custom_processors_{processor_path.stem}", 
            processor_file_path
        )
        if not spec or not spec.loader:
            raise ImportError(f"Failed to create module spec for: {processor_file_path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if not hasattr(module, 'get_registered_processors'):
            raise ValueError(f"Module {processor_file_path} must have a 'get_registered_processors' function")
        
        processors = module.get_registered_processors()
        if not processors:
            raise ValueError(f"No processors found in {processor_file_path}")
        
        loaded_count = 0
        errors = []
        
        for name, func in processors.items():
            try:
                self.register_custom_processor(name, func)
                loaded_count += 1
                logger.debug(f"Registered processor: {name}")
            except Exception as e:
                error_msg = f"Failed to register processor '{name}': {e}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        if errors:
            raise RuntimeError(f"Failed to register {len(errors)} processors: {'; '.join(errors)}")
        
        logger.info(f"Successfully loaded {loaded_count} custom processors from {processor_file_path}")

    def load_field_config_from_file(self, config_file_path: str) -> dict:
        """Loads field configuration from JSON file.
        
        Args:
            config_file_path: Path to the JSON configuration file.
            
        Returns:
            Configuration dictionary.
            
        Raises:
            FileNotFoundError: If config file doesn't exist.
            json.JSONDecodeError: If file contains invalid JSON.
            PermissionError: If file cannot be read.
            ValueError: If config structure is invalid.
        """
        config_path = Path(config_file_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_file_path}")

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON syntax in {config_file_path} at line {e.lineno}: {e.msg}",
                e.doc, e.pos
            )
        
        if not isinstance(config, dict):
            raise ValueError(f"Config file {config_file_path} must contain a JSON object at root level")
        
        if not config:
            raise ValueError(f"Config file {config_file_path} is empty")
            
        message_types = len(config)
        logger.info(f"Loaded field configuration with {message_types} message types from {config_file_path}")
        return config

    def cleanup_temp_files(self, temp_paths: list[str]):
        """Cleans up temporary files using the protobuf handler.
        
        Args:
            temp_paths: List of temporary file paths to clean up.
        """
        self.protobuf_handler.cleanup_temp_files(temp_paths)
