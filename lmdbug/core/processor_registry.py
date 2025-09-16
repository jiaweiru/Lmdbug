"""
Processor registry for custom field processors.

This module provides a class-based system for registering and managing
custom field processors.
"""

import importlib.util
from abc import ABC, abstractmethod
from pathlib import Path

from .logging import get_logger
from .exceptions import DataProcessingError

logger = get_logger(__name__)


class BaseFieldProcessor(ABC):
    """Base class for all field processors.

    This abstract class defines the common interface for all field processors
    used to handle different data types in protobuf messages.
    """

    def __init__(self, config: dict | None = None):
        """Initialize the processor.

        Args:
            config: Configuration dictionary for the processor.
        """
        self.config = config or {}
        self.logger = get_logger(self.__class__.__name__)

    @abstractmethod
    def process(self, field_name: str, value) -> dict:
        """Process a protobuf field value.

        Args:
            field_name: Name of the protobuf field
            value: Field value (can be str, bytes, int, etc.)

        Returns:
            Dict with processing results. Must include:
            - "type": Preview type ("text", "audio", "image", "custom")
            - "field_name": Original field name
            - Other keys depend on the type
        """
        pass


class ProcessorRegistry:
    """Registry for managing field processor implementations."""

    def __init__(self):
        self._processors: dict[str, type[BaseFieldProcessor]] = {}

    def register(self, name: str, processor_class: type[BaseFieldProcessor]) -> None:
        """Register a processor implementation.

        Args:
            name: Unique name for the processor.
            processor_class: Processor class inheriting from BaseFieldProcessor.
        """
        self._processors[name] = processor_class
        logger.debug(f"Registered processor: {name}")

    def register_decorator(self, name: str | list[str]):
        """Decorator for registering processor classes.

        Args:
            name: Unique name or list of names for the processor.

        Usage:
            @processor_registry.register_decorator("pcm_audio")
            class PcmAudioProcessor(BaseFieldProcessor):
                def process(self, field_name, value, config):
                    return {"type": "audio", "temp_path": "..."}

            @processor_registry.register_decorator(["text", "bio", "content"])
            class TextProcessor(BaseFieldProcessor):
                def process(self, field_name, value, config):
                    return {"type": "text", "content": "..."}
        """

        def decorator(
            processor_class: type[BaseFieldProcessor],
        ) -> type[BaseFieldProcessor]:
            if isinstance(name, str):
                self.register(name, processor_class)
            elif isinstance(name, list):
                for field_name in name:
                    self.register(field_name, processor_class)
            else:
                raise ValueError("name must be a string or list of strings")
            return processor_class

        return decorator

    def create_processor(
        self, name: str, config: dict | None = None
    ) -> BaseFieldProcessor:
        """Create a processor instance.

        Args:
            name: Name of the processor.
            config: Configuration for the processor.

        Returns:
            Processor instance.

        Raises:
            DataProcessingError: If processor not found.
        """
        if name not in self._processors:
            available = list(self._processors.keys())
            raise DataProcessingError(
                f"Processor '{name}' not found. Available: {available}"
            )

        return self._processors[name](config)

    def get_processor_class(self, name: str) -> type[BaseFieldProcessor] | None:
        """Get processor class by name."""
        return self._processors.get(name)

    def list_processors(self) -> list[str]:
        """Get list of registered processors."""
        return list(self._processors.keys())

    def load_from_file(self, processor_file_path: str) -> int:
        """Load processors from a Python file.

        Args:
            processor_file_path: Path to processor file

        Returns:
            Number of processors loaded
        """
        processor_path = Path(processor_file_path)
        if not processor_path.exists():
            raise FileNotFoundError(f"Processor file not found: {processor_file_path}")

        initial_count = len(self._processors)

        # Load module
        spec = importlib.util.spec_from_file_location(
            f"processors_{processor_path.stem}_{hash(processor_file_path) & 0x7FFFFFFF}",
            processor_file_path,
        )
        if not spec or not spec.loader:
            raise DataProcessingError(
                f"Failed to create module spec for: {processor_file_path}"
            )

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        loaded_count = len(self._processors) - initial_count
        logger.info(f"Loaded {loaded_count} processors from {processor_file_path}")
        return loaded_count


# Global registry instance
processor_registry = ProcessorRegistry()

# Convenience decorator for easy processor registration
register_processor = processor_registry.register_decorator
