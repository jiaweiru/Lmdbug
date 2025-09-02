"""
Simple processors for the minimal LMDB + protobuf example.
Handles text and audio fields from SimpleMessage protobuf.
"""

import tempfile
import numpy as np
import soundfile as sf

from lmdbug.core.processor_registry import BaseFieldProcessor, register_processor


@register_processor(["text"])
class SimpleTextProcessor(BaseFieldProcessor):
    """Processes text fields from SimpleMessage protobuf."""

    def process(self, field_name: str, value) -> dict:
        """Process text field and create text preview."""
        if not isinstance(value, str) or len(value) < 5:
            return {}

        # Create text preview
        preview_content = value[:200] + ("..." if len(value) > 200 else "")

        return {
            "type": "text",
            "field_name": field_name,
            "content": preview_content,
            "length": len(value),
            "info": f"Text ({len(value)} characters)",
        }


@register_processor(["wav"])
class SimpleAudioProcessor(BaseFieldProcessor):
    """Processes wav fields from SimpleMessage protobuf (24kHz 16-bit PCM)."""

    def process(self, field_name: str, value) -> dict:
        """Process audio field and save as WAV file."""
        try:
            # Handle bytes input (raw PCM data)
            if isinstance(value, bytes):
                audio_data = value
            else:
                return {}

            # Minimum size check
            if len(audio_data) < 100:
                return {}

            # Create temporary WAV file
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=f"_{field_name}.wav", prefix="simple_audio_"
            ) as temp_file:
                wav_path = temp_file.name

            # Convert bytes to numpy array for soundfile
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Write 24kHz 16-bit mono WAV file using soundfile
            sf.write(wav_path, audio_array, 24000, subtype='PCM_16')

            # Calculate duration
            num_samples = len(audio_data) // 2  # 16-bit = 2 bytes per sample
            duration_ms = int((num_samples / 24000) * 1000)

            return {
                "type": "audio",
                "field_name": field_name,
                "temp_path": wav_path,
                "info": f"24kHz 16-bit PCM ({len(audio_data)} bytes, {duration_ms}ms)",
            }

        except Exception as e:
            self.logger.warning(f"Failed to process audio {field_name}: {e}")
            return {}
