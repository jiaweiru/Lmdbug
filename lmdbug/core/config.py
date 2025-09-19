"""
Configuration management for Lmdbug.

This module provides centralized configuration handling for the application.
"""

from pathlib import Path
from dataclasses import dataclass, field

from .logging import get_logger

logger = get_logger()


@dataclass
class LmdbugConfig:
    """Central configuration for Lmdbug application."""

    # Database settings
    db_path: str | None = None
    map_size: int = 10 * 1024 * 1024 * 1024  # 10GB default

    # Protobuf settings
    protobuf_module_path: str | None = None
    protobuf_message_class: str | None = None

    # Processor settings
    processor_paths: list[str] = field(default_factory=list)

    auto_load_processors: bool = True

    # UI settings
    ui_host: str = "127.0.0.1"
    ui_port: int = 7860
    ui_theme: str = "soft"

    # Logging settings
    log_level: str = "INFO"
    log_file: str | None = None

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.db_path:
            self.validate_db_path()
        if self.protobuf_module_path:
            self.validate_protobuf_config()

    def validate_db_path(self) -> None:
        """Validate database path if provided."""
        if self.db_path and not Path(self.db_path).exists():
            logger.warning(f"Database path does not exist: {self.db_path}")

    def validate_protobuf_config(self) -> None:
        """Validate protobuf configuration."""
        if self.protobuf_module_path and not self.protobuf_message_class:
            raise ValueError(
                "protobuf_message_class is required when protobuf_module_path is provided"
            )

        if self.protobuf_module_path and not Path(self.protobuf_module_path).exists():
            logger.warning(
                f"Protobuf module does not exist: {self.protobuf_module_path}"
            )

    @property
    def has_protobuf_config(self) -> bool:
        """Check if protobuf configuration is complete."""
        return bool(self.protobuf_module_path and self.protobuf_message_class)

    @property
    def protobuf_config_dict(self) -> dict[str, str] | None:
        """Get protobuf configuration as dictionary."""
        if self.has_protobuf_config:
            return {
                "module_path": self.protobuf_module_path,
                "message_class": self.protobuf_message_class,
            }
        return None

    def update_from_cli_args(self, **kwargs) -> None:
        """Update configuration from command line arguments."""
        for key, value in kwargs.items():
            if hasattr(self, key) and value is not None:
                # Special handling for processor_paths to replace default
                if key == "processor_paths" and isinstance(value, list):
                    setattr(self, key, value)
                else:
                    setattr(self, key, value)
                logger.debug(f"Updated config: {key}={value}")


# Global configuration instance
config = LmdbugConfig()
