"""
Custom Field Processors for LMDB Protobuf Data

This module defines custom field processors using the class-based design.
Processors are automatically registered when the module is loaded.

Usage:
1. Inherit from BaseFieldProcessor
2. Use @register_processor("name") decorator
3. Load this module via preview_service.load_custom_processors()

Example:
    @register_processor("pcm_audio")
    class PcmAudioProcessor(BaseFieldProcessor):
        def process(self, field_name: str, value: bytes, config: dict) -> dict:
            sample_rate = config.get("sample_rate", 16000)
            channels = config.get("channels", 1)
            
            # Convert PCM to WAV file
            wav_path = self.convert_pcm_to_wav(value, sample_rate, channels)
            
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
import logging

from lmdbug.core.processor_registry import BaseFieldProcessor, register_processor

logger = logging.getLogger(__name__)


@register_processor("simple_text")
class SimpleTextProcessor(BaseFieldProcessor):
    """Processes simple text fields."""
    
    def process(self, field_name: str, value: str, config: dict) -> dict:
        """Processes simple text fields."""
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


@register_processor("base64_text")
class Base64TextProcessor(BaseFieldProcessor):
    """Processes base64 encoded text fields."""
    
    def process(self, field_name: str, value: str, config: dict) -> dict:
        """Processes base64 encoded text fields."""
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
            self.logger.error(f"Failed to process base64 text field {field_name}: {e}")
            return {}


@register_processor("pcm_audio_16khz")
class PcmAudio16khzProcessor(BaseFieldProcessor):
    """Processes PCM audio data at 16kHz sample rate."""
    
    def process(self, field_name: str, value: bytes, config: dict) -> dict:
        """Processes PCM audio data at 16kHz sample rate."""
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
            self.logger.error(f"Failed to process PCM audio field {field_name}: {e}")
            return {}


@register_processor("raw_image_rgb")
class RawImageRgbProcessor(BaseFieldProcessor):
    """Processes raw RGB image data."""
    
    def process(self, field_name: str, value: bytes, config: dict) -> dict:
        """Processes raw RGB image data."""
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
                self.logger.warning(f"Image data size mismatch: expected {expected_size}, got {len(image_data)}")
            
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
                    self.logger.error(f"Unsupported channel count: {channels}")
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
                self.logger.error("PIL not available for image processing")
                return {}
        
        except Exception as e:
            self.logger.error(f"Failed to process raw image field {field_name}: {e}")
            return {}


@register_processor("hex_display")
class HexDisplayProcessor(BaseFieldProcessor):
    """Displays raw data as hex string."""
    
    def process(self, field_name: str, value: bytes, config: dict) -> dict:
        """Displays raw data as hex string."""
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
            self.logger.error(f"Failed to process hex display field {field_name}: {e}")
            return {}