"""
Custom Field Processors for LMDB Protobuf Data

This module provides a framework for defining custom field processors
that can handle various data formats (audio, image, text, etc.) stored
in protobuf messages within LMDB databases.

Usage:
1. Define processor functions with signature: (field_name: str, value: any, config: dict) -> dict
2. Register processors using the @processor decorator
3. Load this module in your application

Example:
    @processor("pcm_audio")
    def process_pcm_audio(field_name: str, value: bytes, config: dict) -> dict:
        sample_rate = config.get("sample_rate", 16000)
        channels = config.get("channels", 1)
        
        # Convert PCM to WAV file
        wav_path = convert_pcm_to_wav(value, sample_rate, channels)
        
        return {
            "type": "audio",
            "field_name": field_name,
            "temp_path": wav_path,
            "size": len(value),
            "sample_rate": sample_rate
        }
"""

import tempfile
import wave
import base64
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

_PROCESSORS: dict[str, callable] = {}


def processor(name: str):
    """Decorator to register a custom field processor.
    
    Args:
        name: Name of the processor.
        
    Usage:
        @processor("pcm_audio")
        def process_pcm_audio(field_name: str, value: bytes, config: dict) -> dict:
            # Processing logic here
            return {"type": "audio", "temp_path": wav_file}
    """
    def decorator(func):
        _PROCESSORS[name] = func
        logger.info(f"Registered custom processor: {name}")
        return func
    return decorator


def get_registered_processors() -> dict[str, callable]:
    """Gets all registered processors.
    
    Returns:
        Dictionary mapping processor names to functions.
    """
    return _PROCESSORS.copy()


def clear_processors():
    """Clears all registered processors."""
    global _PROCESSORS
    _PROCESSORS.clear()


@processor("simple_text")
def process_simple_text(field_name: str, value: str, config: dict) -> dict:
    """Processes simple text fields.
    
    Args:
        field_name: Name of the field.
        value: Text content.
        config: Processing configuration.
        
    Returns:
        Dictionary with text processing results.
    """
    if not isinstance(value, str):
        return {}
    
    return {
        "type": "text",
        "field_name": field_name,
        "content": value,
        "length": len(value),
        "preview": value[:200] + "..." if len(value) > 200 else value,
        "is_multiline": "\n" in value,
        "line_count": value.count("\n") + 1
    }


@processor("base64_text")
def process_base64_text(field_name: str, value: str, config: dict) -> dict:
    """Processes base64 encoded text fields.
    
    Args:
        field_name: Name of the field.
        value: Base64 encoded text.
        config: Processing configuration.
        
    Returns:
        Dictionary with decoded text results.
    """
    try:
        if isinstance(value, str):
            decoded_text = base64.b64decode(value).decode('utf-8')
        else:
            decoded_text = value.decode('utf-8') if isinstance(value, bytes) else str(value)
        
        return {
            "type": "text",
            "field_name": field_name,
            "content": decoded_text,
            "length": len(decoded_text),
            "preview": decoded_text[:200] + "..." if len(decoded_text) > 200 else decoded_text,
            "is_multiline": "\n" in decoded_text,
            "line_count": decoded_text.count("\n") + 1
        }
    except Exception as e:
        logger.error(f"Failed to process base64 text field {field_name}: {e}")
        return {}


@processor("pcm_audio_16khz")
def process_pcm_audio_16khz(field_name: str, value: bytes, config: dict) -> dict:
    """Processes PCM audio data at 16kHz sample rate.
    
    Args:
        field_name: Name of the field.
        value: PCM audio data.
        config: Processing configuration with sample rate, channels, etc.
        
    Returns:
        Dictionary with audio file path and metadata.
    """
    try:
        sample_rate = config.get("sample_rate", 16000)
        channels = config.get("channels", 1)
        sample_width = config.get("sample_width", 2)  # 2 bytes for int16
        
        if isinstance(value, str):
            audio_data = base64.b64decode(value)
        elif isinstance(value, bytes):
            audio_data = value
        else:
            return {}
        
        # Create WAV file
        with tempfile.NamedTemporaryFile(
            delete=False, 
            suffix=f"_{field_name}.wav",
            prefix="lmdbug_pcm_"
        ) as temp_file:
            wav_path = temp_file.name
        
        # Write WAV file
        with wave.open(wav_path, 'wb') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data)
        
        return {
            "type": "audio",
            "field_name": field_name,
            "temp_path": wav_path,
            "size": len(audio_data),
            "sample_rate": sample_rate,
            "channels": channels,
            "duration": len(audio_data) / (sample_rate * channels * sample_width)
        }
    
    except Exception as e:
        logger.error(f"Failed to process PCM audio field {field_name}: {e}")
        return {}


@processor("raw_image_rgb")
def process_raw_image_rgb(field_name: str, value: bytes, config: dict) -> dict:
    """Processes raw RGB image data.
    
    Args:
        field_name: Name of the field.
        value: Raw RGB image bytes.
        config: Processing configuration with width, height, channels.
        
    Returns:
        Dictionary with image file path and metadata.
    """
    try:
        width = config.get("width", 224)
        height = config.get("height", 224)
        channels = config.get("channels", 3)
        
        if isinstance(value, str):
            image_data = base64.b64decode(value)
        elif isinstance(value, bytes):
            image_data = value
        else:
            return {}
        
        expected_size = width * height * channels
        if len(image_data) != expected_size:
            logger.warning(f"Image data size mismatch: expected {expected_size}, got {len(image_data)}")
        
        try:
            from PIL import Image
            import numpy as np
            
            img_array = np.frombuffer(image_data, dtype=np.uint8)
            img_array = img_array.reshape((height, width, channels))
            
            if channels == 3:
                img = Image.fromarray(img_array, 'RGB')
            elif channels == 1:
                img = Image.fromarray(img_array.squeeze(), 'L')
            else:
                logger.error(f"Unsupported channel count: {channels}")
                return {}
            
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=f"_{field_name}.png",
                prefix="lmdbug_img_"
            ) as temp_file:
                png_path = temp_file.name
            
            img.save(png_path, 'PNG')
            
            return {
                "type": "image",
                "field_name": field_name,
                "temp_path": png_path,
                "size": len(image_data),
                "width": width,
                "height": height,
                "channels": channels
            }
        
        except ImportError:
            logger.error("PIL not available for image processing")
            return {}
    
    except Exception as e:
        logger.error(f"Failed to process raw image field {field_name}: {e}")
        return {}


@processor("hex_display")
def process_hex_display(field_name: str, value: bytes, config: dict) -> dict:
    """Displays raw data as hex string.
    
    Args:
        field_name: Name of the field.
        value: Raw bytes to display.
        config: Processing configuration.
        
    Returns:
        Dictionary with hex representation.
    """
    try:
        if isinstance(value, str):
            hex_data = value
        elif isinstance(value, bytes):
            hex_data = value.hex()
        else:
            hex_data = str(value)
        
        max_length = config.get("max_length", 200)
        preview = hex_data[:max_length] + "..." if len(hex_data) > max_length else hex_data
        
        return {
            "type": "text",
            "field_name": field_name,
            "content": hex_data,
            "preview": f"Hex: {preview}",
            "length": len(hex_data)
        }
    
    except Exception as e:
        logger.error(f"Failed to process hex display field {field_name}: {e}")
        return {}


def cleanup_temp_files(temp_paths: list[str]):
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