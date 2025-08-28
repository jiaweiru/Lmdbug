import importlib.util
import json
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
        """Load a compiled protobuf Python module."""
        module_path_obj = Path(module_path)
        normalized_path = str(module_path_obj.resolve())
        
        # Check if this exact combination already exists
        if message_class_name in self.loaded_messages:
            existing_path = self.module_class_registry.get(message_class_name)
            if existing_path == normalized_path:
                logger.debug(f"Message class '{message_class_name}' from '{normalized_path}' already loaded, skipping")
                return
            else:
                logger.warning(f"Message class '{message_class_name}' already loaded from different path: "
                             f"existing='{existing_path}', new='{normalized_path}'. Overwriting.")
        
        if not module_path_obj.exists():
            error_msg = f"Proto module not found: {module_path}"
            logger.error(error_msg)
            raise ProtobufError(error_msg)
        
        # Load the module with unique name based on file path
        try:
            module_name = f"proto_module_{module_path_obj.stem}_{hash(normalized_path) & 0x7fffffff}"
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
        
        # Get the message class
        if not hasattr(proto_module, message_class_name):
            error_msg = f"Message class '{message_class_name}' not found in module {module_path}"
            logger.error(error_msg)
            raise ProtobufError(error_msg)
            
        self.loaded_messages[message_class_name] = getattr(proto_module, message_class_name)
        self.module_class_registry[message_class_name] = normalized_path
        logger.info(f"Successfully loaded message class '{message_class_name}' from '{normalized_path}'")
    
    
    def deserialize(self, data: bytes, message_type: str) -> Message:
        """Deserialize binary data to a protobuf message."""
        if message_type not in self.loaded_messages:
            available = list(self.loaded_messages.keys())
            error_msg = f"Message type '{message_type}' not loaded. Available: {available}"
            logger.error(error_msg)
            raise ProtobufError(error_msg)
        
        try:
            message = self.loaded_messages[message_type]()
            message.ParseFromString(data)
            return message
        except Exception as e:
            error_msg = f"Failed to deserialize {len(data)} bytes as {message_type}: {e}"
            logger.error(error_msg)
            raise ProtobufError(error_msg) from e
    
    def message_to_dict(self, message: Message) -> dict:
        """Convert a protobuf message to a dictionary."""
        try:
            return MessageToDict(message, preserving_proto_field_name=True)
        except Exception as e:
            error_msg = f"Failed to convert protobuf message to dict: {e}"
            logger.error(error_msg)
            raise ProtobufError(error_msg) from e
    
    def message_to_json(self, message: Message, indent: int = 2) -> str:
        """Convert a protobuf message to a JSON string."""
        try:
            message_dict = self.message_to_dict(message)
            return json.dumps(message_dict, indent=indent, ensure_ascii=False)
        except ProtobufError:
            raise  # Re-raise protobuf errors from message_to_dict
        except Exception as e:
            error_msg = f"Failed to convert protobuf message to JSON: {e}"
            logger.error(error_msg)
            raise ProtobufError(error_msg) from e
    
    
    
    
    def get_loaded_message_types(self) -> list[str]:
        """Get list of loaded message type names."""
        return list(self.loaded_messages.keys())
    
