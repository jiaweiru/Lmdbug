"""
Simple example of a custom field processor.
This processes 24kHz 16-bit PCM audio data and saves it as a WAV file.
"""
import tempfile
import wave
import base64

from lmdbug.core.processor_registry import BaseFieldProcessor, register_processor


@register_processor(["bio", "content", "text", "message", "description"])
class TextFieldProcessor(BaseFieldProcessor):
    """Processes various text fields for text preview."""
    
    def process(self, field_name: str, value) -> dict:
        """Process text fields and create text preview."""
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


@register_processor(["pcm", "audio_data", "audio", "voice_audio"])
class AudioDataProcessor(BaseFieldProcessor):
    """Processes various audio fields as PCM data."""
    
    def process(self, field_name: str, value) -> dict:
        """Process audio field and save as WAV file."""
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
                delete=False, suffix=f"_{field_name}.wav", prefix="lmdbug_audio_"
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
            self.logger.warning(f"Failed to process audio {field_name}: {e}")
            return {}


