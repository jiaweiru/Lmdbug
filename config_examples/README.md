# Configuration Examples

This folder contains example configuration files and custom processors for Lmdbug.

## Files

### custom_processors.py
Example custom field processors that demonstrate how to handle various data types:
- **simple_text**: Basic text field processing
- **base64_text**: Base64-encoded text decoding
- **pcm_audio_16khz**: PCM audio data to WAV conversion
- **raw_image_rgb**: Raw RGB image data to PNG conversion
- **hex_display**: Raw data hex display

### example_field_config.json
Example field configuration file showing how to configure different message types and their field processors.

## Usage

1. **Copy and modify the example files**:
   ```bash
   cp config_examples/custom_processors.py my_processors.py
   cp config_examples/example_field_config.json my_config.json
   ```

2. **Customize your processors** in `my_processors.py`:
   ```python
   from config_examples.custom_processors import processor
   
   @processor("my_custom_processor")
   def my_processor(field_name: str, value: any, config: dict) -> dict:
       # Your custom processing logic here
       return {"type": "audio", "temp_path": "/path/to/temp/file"}
   ```

3. **Update your configuration** in `my_config.json`:
   ```json
   {
     "MyMessageType": {
       "my_field": {
         "processor": "my_custom_processor",
         "config": {
           "param1": "value1",
           "param2": 42
         }
       }
     }
   }
   ```

4. **Load in Lmdbug**:
   - Load your custom processors file in the "Custom Processors" section
   - Load your configuration file in the "Field Configuration" section

## Creating Custom Processors

Custom processors should follow this signature:
```python
def processor_function(field_name: str, value: any, config: dict) -> dict:
    """
    Process a protobuf field value.
    
    Args:
        field_name: Name of the protobuf field
        value: Field value (can be str, bytes, int, etc.)
        config: Configuration parameters from JSON config
        
    Returns:
        Dict with processing results. Must include:
        - "type": Preview type ("text", "audio", "image", "custom")
        - "field_name": Original field name
        - Other keys depend on the type (e.g., "temp_path" for audio/image)
    """
    return {
        "type": "text",  # or "audio", "image", "custom"
        "field_name": field_name,
        # ... other result data
    }
```

## Return Types

- **text**: Display in text preview area
  - Required: `content` or `preview`
  - Optional: `length`, `is_multiline`, `line_count`

- **audio**: Display in audio player
  - Required: `temp_path` (path to audio file)
  - Optional: `size`, `sample_rate`, `channels`, `duration`

- **image**: Display in image viewer
  - Required: `temp_path` (path to image file)
  - Optional: `size`, `width`, `height`, `channels`

- **custom**: Display in JSON results
  - Any custom fields for debugging/inspection