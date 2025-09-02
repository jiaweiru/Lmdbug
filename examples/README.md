# LMDB + Protobuf Examples

This directory contains a minimal example demonstrating how to use LMDB with Protocol Buffers and the Lmdbug tool.

## Files

- `simple_message.proto` - Simple Protocol Buffer definition with text and audio fields
- `create_simple_db.py` - Script to generate sample LMDB database
- `simple_message_pb2.py` - Generated Python protobuf classes (created by protoc)

## Quick Start

### 1. Generate Protobuf Classes

First, generate the Python protobuf classes from the .proto file:

```bash
cd examples/
protoc --python_out=. simple_message.proto
```

This creates `simple_message_pb2.py`.

### 2. Create Sample Database

Generate a sample LMDB database with protobuf data:

```bash
python create_simple_db.py ./simple_lmdb
```

This creates a database containing 3 sample messages, each with:
- **text field**: String content  
- **wav field**: 24kHz 16-bit PCM audio data (sine waves)

### 3. View with Lmdbug

Launch Lmdbug to browse the database:

```bash
lmdbug --db-path ./simple_lmdb \
       --protobuf-module examples/simple_message_pb2.py \
       --message-class SimpleMessage
```

## Database Contents

The sample database contains entries with keys like:
- `message:000` - First sample message
- `message:001` - Second sample message  
- `message:002` - Third sample message

Each entry is a `SimpleMessage` protobuf with:
- `text`: Sample text content
- `wav`: Raw 24kHz 16-bit PCM audio bytes (sine wave tones)

## Requirements

- Python 3.10+
- `lmdb` package
- `numpy` package  
- `protobuf` package
- Protocol Buffers compiler (`protoc`)

Install dependencies:
```bash
pip install lmdb numpy protobuf
```

## Custom Processors

For enhanced viewing experience with text and audio preview, use the corresponding processors in `../config_examples/simple_processors.py`.

## Message Format

The `SimpleMessage` protobuf schema:

```protobuf
message SimpleMessage {
  string text = 1;  // Text content
  bytes wav = 2;    // 24kHz 16-bit PCM audio
}
```

This minimal schema demonstrates basic LMDB + protobuf integration with both text and binary audio data.