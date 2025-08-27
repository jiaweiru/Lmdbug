import importlib.util
import json
from pathlib import Path

from google.protobuf.message import Message
from google.protobuf.json_format import MessageToDict
from loguru import logger

# Type aliases for cleaner code
JsonValue = str | int | float | bool | dict | list
ProtobufResult = dict[str, str | Message | dict | list]


class ProtobufHandler:
    """
    Handler for Protobuf serialization/deserialization operations.
    Supports loading proto files and deserializing binary data.
    """
    
    def __init__(self):
        """Initialize the Protobuf handler."""
        self.loaded_messages: dict[str, type[Message]] = {}
    
    
    def load_compiled_proto_module(self, module_path: str, message_class_name: str) -> bool:
        """Load a compiled protobuf Python module."""
        try:
            if not Path(module_path).exists():
                logger.error(f"Proto module not found: {module_path}")
                return False
            
            spec = importlib.util.spec_from_file_location("proto_module", module_path)
            if not spec or not spec.loader:
                logger.error(f"Failed to load module spec: {module_path}")
                return False
                
            proto_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(proto_module)
            
            if not hasattr(proto_module, message_class_name):
                logger.error(f"Message class {message_class_name} not found")
                return False
                
            message_class = getattr(proto_module, message_class_name)
            self.loaded_messages[message_class_name] = message_class
            logger.info(f"Loaded message class: {message_class_name}")
            return True
                
        except Exception as e:
            logger.error(f"Failed to load proto module: {e}")
            return False
    
    def register_message_class(self, message_class: type[Message], name: str | None = None) -> str:
        """Register a protobuf message class directly."""
        class_name = name or message_class.__name__
        self.loaded_messages[class_name] = message_class
        logger.info(f"Registered message class: {class_name}")
        return class_name
    
    def deserialize(self, data: bytes, message_type: str) -> Message | None:
        """Deserialize binary data to a protobuf message."""
        if message_type not in self.loaded_messages:
            logger.error(f"Message type {message_type} not loaded")
            return None
        
        try:
            message_class = self.loaded_messages[message_type]
            message = message_class()
            message.ParseFromString(data)
            return message
        except Exception as e:
            logger.error(f"Failed to deserialize as {message_type}: {e}")
            return None
    
    def message_to_dict(self, message: Message) -> dict[str, JsonValue]:
        """Convert a protobuf message to a dictionary."""
        try:
            return MessageToDict(message, preserving_proto_field_name=True)
        except Exception as e:
            logger.error(f"Failed to convert message to dict: {e}")
            return {}
    
    def message_to_json(self, message: Message, indent: int = 2) -> str:
        """Convert a protobuf message to a JSON string."""
        try:
            message_dict = self.message_to_dict(message)
            return json.dumps(message_dict, indent=indent, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to convert message to JSON: {e}")
            return "{}"
    
    def try_deserialize_all_types(self, data: bytes) -> dict[str, ProtobufResult]:
        """Try to deserialize data with all loaded message types."""
        results = {}
        
        for message_type in self.loaded_messages:
            try:
                message = self.deserialize(data, message_type)
                if message:
                    results[message_type] = {
                        'message': message,
                        'dict': self.message_to_dict(message),
                        'json': self.message_to_json(message)
                    }
            except Exception:
                continue
        
        return results
    
    def get_loaded_message_types(self) -> list[str]:
        """Get list of loaded message type names."""
        return list(self.loaded_messages.keys())
    
