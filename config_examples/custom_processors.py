"""
Simple example of a custom field processor.
This processes 24kHz 16-bit PCM audio data and saves it as a WAV file.
"""
import tempfile
import wave
import base64

from lmdbug.core.processor_registry import BaseFieldProcessor, register_processor


@register_processor("text_description")
class TextDescriptionProcessor(BaseFieldProcessor):
    """Processes text description fields for text preview."""
    
    def process(self, field_name: str, value) -> dict:
        """Process text description fields and create text preview."""
        # Only process fields that contain text descriptions
        if field_name.lower() not in ('description', 'bio', 'content', 'text', 'message'):
            return {}
        
        if not isinstance(value, str) or len(value) < 20:
            return {}
        
        # Create text preview with truncation
        preview_content = value[:300] + ("..." if len(value) > 300 else "")
        
        return {
            "type": "text",
            "field_name": field_name,
            "content": preview_content,
            "length": len(value),
            "info": f"Text content ({len(value)} chars)"
        }


@register_processor("pcm_24khz_16bit")
class Pcm24khzProcessor(BaseFieldProcessor):
    """Processes 24kHz 16-bit PCM audio data."""
    
    def process(self, field_name: str, value) -> dict:
        """Process PCM audio field and save as WAV file."""
        # Only process fields that look like audio
        if not field_name.lower().endswith(('audio', 'pcm')):
            return {}
            
        try:
            # Handle different input formats
            if isinstance(value, str):
                audio_data = base64.b64decode(value)
            elif isinstance(value, bytes):
                audio_data = value
            else:
                return {}
            
            # Minimum size check
            if len(audio_data) < 1000:
                return {}
            
            # Create temporary WAV file
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=f"_{field_name}.wav", prefix="lmdbug_pcm24_"
            ) as temp_file:
                wav_path = temp_file.name
            
            # Write 24kHz 16-bit mono WAV file
            with wave.open(wav_path, 'wb') as wav_file:
                wav_file.setnchannels(1)        # mono
                wav_file.setsampwidth(2)        # 16-bit = 2 bytes
                wav_file.setframerate(24000)    # 24kHz
                wav_file.writeframes(audio_data)
            
            return {
                "type": "audio",
                "field_name": field_name,
                "temp_path": wav_path,
                "info": f"24kHz 16-bit PCM ({len(audio_data)} bytes)"
            }
            
        except Exception as e:
            self.logger.warning(f"Failed to process PCM audio {field_name}: {e}")  # Processing failure, not system error
            return {}