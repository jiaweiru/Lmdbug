import importlib.util
from pathlib import Path

from google.protobuf.message import Message
from google.protobuf.json_format import MessageToDict

from .logging import get_logger
from .exceptions import ProtobufError

logger = get_logger(__name__)


class ProtobufHandler:
    """
    Handler for Protobuf serialization/deserialization operations.
    Supports loading proto files and deserializing binary data.
    """

    def __init__(self):
        """Initialize the Protobuf handler."""
        self.loaded_messages: dict[str, type[Message]] = {}
        self.module_class_registry: dict[str, str] = {}  # message_class -> module_path

    def load_compiled_proto_module(self, module_path: str, message_class_name: str):
        """Loads a compiled protobuf Python module.

        Args:
            module_path: Path to the compiled .py module.
            message_class_name: Name of the protobuf message class.

        Raises:
            ProtobufError: If module loading fails.
        """
        module_path_obj = Path(module_path)
        normalized_path = str(module_path_obj.resolve())

        if message_class_name in self.loaded_messages:
            existing_path = self.module_class_registry.get(message_class_name)
            if existing_path == normalized_path:
                logger.debug(
                    f"Message class '{message_class_name}' from '{normalized_path}' already loaded, skipping"
                )
                return
            else:
                logger.warning(
                    f"Message class '{message_class_name}' already loaded from different path: "
                    f"existing='{existing_path}', new='{normalized_path}'. Overwriting."
                )

        if not module_path_obj.exists():
            error_msg = f"Proto module not found: {module_path}"
            logger.error(error_msg)
            raise ProtobufError(error_msg)

        try:
            module_name = f"proto_module_{module_path_obj.stem}_{hash(normalized_path) & 0x7FFFFFFF}"
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if not spec or not spec.loader:
                error_msg = f"Failed to create module spec for: {module_path}"
                logger.error(error_msg)
                raise ProtobufError(error_msg)

            proto_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(proto_module)

        except Exception as e:
            error_msg = f"Failed to load proto module '{module_path}': {e}"
            logger.error(error_msg)
            raise ProtobufError(error_msg) from e

        if not hasattr(proto_module, message_class_name):
            error_msg = f"Message class '{message_class_name}' not found in module {module_path}"
            logger.error(error_msg)
            raise ProtobufError(error_msg)

        self.loaded_messages[message_class_name] = getattr(
            proto_module, message_class_name
        )
        self.module_class_registry[message_class_name] = normalized_path
        logger.debug(f"Loaded message class '{message_class_name}' from '{normalized_path}'")

    def deserialize(self, data: bytes, message_type: str) -> Message:
        """Deserializes binary data to a protobuf message.

        Args:
            data: Binary protobuf data.
            message_type: Name of the message type to deserialize as.

        Returns:
            Deserialized protobuf message.

        Raises:
            ProtobufError: If deserialization fails.
        """
        if message_type not in self.loaded_messages:
            available = list(self.loaded_messages.keys())
            error_msg = (
                f"Message type '{message_type}' not loaded. Available: {available}"
            )
            logger.error(error_msg)
            raise ProtobufError(error_msg)

        try:
            message = self.loaded_messages[message_type]()
            message.ParseFromString(data)
            return message
        except Exception as e:
            error_msg = (
                f"Failed to deserialize {len(data)} bytes as {message_type}: {e}"
            )
            logger.error(error_msg)
            raise ProtobufError(error_msg) from e

    def message_to_dict(self, message: Message) -> dict:
        """Converts a protobuf message to a dictionary.

        Args:
            message: Protobuf message to convert.

        Returns:
            Dictionary representation of the message.

        Raises:
            ProtobufError: If conversion fails.
        """
        try:
            return MessageToDict(message, preserving_proto_field_name=True)
        except Exception as e:
            error_msg = f"Failed to convert protobuf message to dict: {e}"
            logger.error(error_msg)
            raise ProtobufError(error_msg) from e

    def get_loaded_message_types(self) -> list[str]:
        """Gets list of loaded message type names.

        Returns:
            List of loaded message type names.
        """
        return list(self.loaded_messages.keys())


    def process_media_fields(
        self, data_dict: dict, field_config: dict[str, dict]
    ) -> dict:
        """Processes media fields using global processor registry.

        Args:
            data_dict: Protobuf message converted to dict.
            field_config: Mapping of field names to processor configs.
                         e.g. {"audio_data": {"processor": "pcm_audio", "config": {...}}}

        Returns:
            Dictionary with media previews for configured fields.
        """
        from .processor_registry import processor_registry
        
        media_previews = {"text": [], "audio": [], "image": [], "custom": []}

        for field_name, field_config in field_config.items():
            if field_name not in data_dict:
                continue

            field_value = data_dict[field_name]
            processor_name = field_config.get("processor")
            processor_config = field_config.get("config", {})

            try:
                processor_instance = processor_registry.create_processor(processor_name, processor_config)
                result = processor_instance.process(field_name, field_value, processor_config)
                if result:
                    result_type = result.get("type", "custom")
                    if result_type in media_previews:
                        media_previews[result_type].append(result)
                    else:
                        media_previews["custom"].append(result)
            except ValueError:
                logger.warning(f"Unknown processor: {processor_name} for field {field_name}")
            except Exception as e:
                logger.error(f"Error processing field {field_name} with processor {processor_name}: {e}")

        return media_previews

    def cleanup_temp_files(self, temp_paths: list[str]):
        """Cleans up temporary preview files.

        Args:
            temp_paths: List of file paths to remove.
        """
        for path in temp_paths:
            try:
                if path:
                    path_obj = Path(path)
                    if path_obj.exists():
                        path_obj.unlink()
                        logger.debug(f"Cleaned up temp file: {path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file {path}: {e}")
