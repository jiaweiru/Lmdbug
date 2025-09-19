"""
Simplified data service that combines LMDB reading and protobuf handling.
"""

import importlib.util
from pathlib import Path
from google.protobuf.json_format import MessageToDict

from .lmdb_reader import LMDBReader
from .logging import get_logger
from .exceptions import ProtobufError, DataProcessingError

logger = get_logger()


class DataService:
    """Simplified service for LMDB data preview with optional protobuf support."""

    def __init__(
        self,
        db_path: str,
        map_size: int = 10 * 1024 * 1024 * 1024,
        processor_paths: list[str] | None = None,
    ):
        self.lmdb_reader = LMDBReader(db_path, map_size)
        self.protobuf_message_class = None
        self.temp_files = []
        self.processor_paths = processor_paths

    def open(self):
        """Open the LMDB environment."""
        self.lmdb_reader.open()

    def close(self):
        """Close the LMDB environment and cleanup temp files."""
        self.lmdb_reader.close()
        self.cleanup_temp_files()

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, _exc_tb):
        self.close()
        if exc_type:
            logger.error(
                f"Exception in DataService context: {exc_type.__name__}: {exc_val}"
            )
        return False

    def load_protobuf_module(self, module_path: str, message_class_name: str):
        """Load a protobuf module for data deserialization."""
        module_path_obj = Path(module_path)
        if not module_path_obj.exists():
            raise ProtobufError(f"Proto module not found: {module_path}")

        try:
            module_name = f"proto_module_{module_path_obj.stem}"
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if not spec or not spec.loader:
                raise ProtobufError(f"Failed to create module spec for: {module_path}")

            proto_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(proto_module)

            if not hasattr(proto_module, message_class_name):
                raise ProtobufError(
                    f"Message class '{message_class_name}' not found in module"
                )

            self.protobuf_message_class = getattr(proto_module, message_class_name)
            logger.info(
                f"Loaded protobuf class '{message_class_name}' from {module_path}"
            )

        except Exception as e:
            raise ProtobufError(f"Failed to load proto module: {e}") from e

    def get_database_info(self) -> dict:
        """Get database information."""
        info = self.lmdb_reader.get_basic_info()
        info["database_path"] = str(self.lmdb_reader.db_path)
        info["has_protobuf"] = self.protobuf_message_class is not None
        return info

    def get_first_entries(self, count: int = 10) -> list[dict]:
        """Get the first N entries from the database."""
        logger.debug(f"Retrieving first {count} entries from database")
        entries = self.lmdb_reader.get_first_entries(count)
        logger.debug(f"Retrieved {len(entries)} entries")
        return [self._format_entry(k, v) for k, v in entries]

    def search_keys(self, pattern: str, count: int = 10) -> list[dict]:
        """Search keys matching regex pattern and return first count matches."""
        logger.debug(f"Searching for pattern '{pattern}', limit {count}")
        matches = self.lmdb_reader.search_keys(pattern, count)
        if not matches:
            logger.debug(f"No matches found for pattern: {pattern}")
            return []
        logger.debug(f"Found {len(matches)} matches for pattern: {pattern}")
        return [self._format_entry(k, v) for k, v in matches]

    def _format_entry(self, key_bytes: bytes, value_bytes: bytes) -> dict:
        """Format an entry for display, focusing on key and protobuf content."""
        try:
            key_str = key_bytes.decode("utf-8")
        except UnicodeDecodeError:
            key_str = key_bytes.hex()

        result = {"key": key_str}

        # Try protobuf deserialization if available
        if self.protobuf_message_class:
            try:
                message = self.protobuf_message_class()
                message.ParseFromString(value_bytes)
                protobuf_data = MessageToDict(message, preserving_proto_field_name=True)
                result["protobuf"] = protobuf_data

                # Add media previews using registered processors
                self._add_media_preview(result, protobuf_data)

            except Exception as e:
                result["protobuf_error"] = f"Failed to deserialize: {str(e)}"

        return result

    def _add_media_preview(self, result: dict, protobuf_dict: dict):
        """Add media previews using registered processors."""
        from .processor_registry import processor_registry

        # Auto-load processors if none registered
        if not processor_registry.list_processors():
            self._auto_load_processors()

        media_previews = {"text": [], "audio": [], "image": []}
        valid_types = set(media_previews.keys())

        for field_name, value in protobuf_dict.items():
            # Process field using registered processors
            preview = self._process_field(field_name, value, processor_registry)
            if preview:
                # Validate preview has required type field
                if "type" not in preview:
                    raise DataProcessingError(
                        f"Preview for field '{field_name}' missing required 'type' field"
                    )

                preview_type = preview["type"]
                # Validate preview type
                if preview_type not in valid_types:
                    raise DataProcessingError(
                        f"Invalid preview type '{preview_type}' for field '{field_name}'. Valid types: {valid_types}"
                    )

                # Register temp file for cleanup if present
                if "temp_path" in preview:
                    self.temp_files.append(preview["temp_path"])

                if preview_type in media_previews:
                    media_previews[preview_type].append(preview)

        # Only add non-empty previews
        filtered_previews = {k: v for k, v in media_previews.items() if v}
        if filtered_previews:
            result["media_preview"] = filtered_previews

    def _process_field(self, field_name: str, value, processor_registry) -> dict | None:
        """Process a field using registered processors."""

        # Try to find a processor registered with the exact field name
        if field_name in processor_registry.list_processors():
            try:
                processor_instance = processor_registry.create_processor(field_name)
                result = processor_instance.process(field_name, value)
                if result:
                    return result
            except Exception as e:
                logger.debug(f"Processor {field_name} failed for {field_name}: {e}")

        return None

    def _auto_load_processors(self):
        """Auto-load processors from configured paths."""
        from .processor_registry import processor_registry

        loaded_count = 0
        for processor_path in self.processor_paths:
            try:
                processor_file = Path(processor_path)
                if processor_file.exists():
                    # Use processor_registry's load_from_file method
                    count = processor_registry.load_from_file(str(processor_file))
                    loaded_count += count

                    logger.debug(f"Loaded {count} processors from {processor_path}")
                else:
                    logger.debug(f"Processor file not found: {processor_path}")
            except Exception as e:
                logger.warning(f"Failed to load processors from {processor_path}: {e}")

        if loaded_count > 0:
            logger.info(f"Auto-loaded {loaded_count} processors")
        else:
            logger.debug("No processors auto-loaded")

    def cleanup_temp_files(self):
        """Clean up temporary files."""
        for path in self.temp_files:
            try:
                Path(path).unlink(missing_ok=True)
            except Exception as e:
                logger.debug(f"Failed to cleanup {path}: {e}")
        self.temp_files.clear()
