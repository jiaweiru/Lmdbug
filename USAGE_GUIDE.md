# Lmdbug Usage Guide

Lmdbug is a modern LMDB database preview tool with Protobuf deserialization support and an intuitive web interface.

## Quick Start

### Basic Usage
```bash
# Preview an LMDB database
lmdbug /path/to/your/database

# With custom port
lmdbug /path/to/your/database --port 8080
```

### With Protobuf Support
```bash
# Load a compiled protobuf module
lmdbug /path/to/your/database \
  --protobuf-module /path/to/user_pb2.py \
  --message-class User
```

## Installation

### Prerequisites
- Python 3.9+
- LMDB database files
- (Optional) Compiled protobuf Python modules

### Install Dependencies
```bash
pip install lmdb protobuf gradio typer loguru
```

### Install from Source
```bash
git clone <repository-url>
cd Lmdbug
pip install -e .
```

## Command Line Interface

### Synopsis
```
lmdbug [OPTIONS] [DB_PATH]
```

### Arguments
- `DB_PATH`: Path to LMDB database directory (optional, can be set in web interface)

### Options
- `-p, --protobuf-module TEXT`: Path to compiled protobuf module (.py file)
- `-m, --message-class TEXT`: Protobuf message class name
- `--port INTEGER`: Server port (default: 7860)
- `--host TEXT`: Server host (default: 127.0.0.1)
- `--log-level [DEBUG|INFO|WARNING|ERROR]`: Logging level (default: INFO)
- `--version`: Show version and exit
- `--help`: Show help message

### Usage Examples

#### Example 1: Basic Database Preview
```bash
lmdbug ./my_database
```
Opens the web interface at http://127.0.0.1:7860 for basic LMDB data browsing.

#### Example 2: Production Server with Protobuf
```bash
lmdbug /prod/user_data.lmdb \
  --protobuf-module user_pb2.py \
  --message-class User \
  --host 0.0.0.0 \
  --port 8080
```
Starts a production server accessible from any IP address.

#### Example 3: Development with Debug Logging
```bash
lmdbug ./dev_database --log-level DEBUG
```
Enables detailed logging for development and debugging.

## Web Interface Features

### Database Configuration
- **Database Path**: Set or change the LMDB database location
- **Protobuf Module**: Load compiled protobuf modules for data deserialization
- **Message Class**: Select the primary protobuf message type

### Data Browsing
- **First N Entries**: Preview the first entries in the database
- **Index Range**: Browse data by index with pagination
- **Key Search**: Find specific entries by exact key match
- **Prefix Search**: Find entries with keys starting with a prefix
- **Pattern Search**: Find entries with keys containing a pattern

### Data Display
- **Key Information**: Shows both UTF-8 decoded and hex representations
- **Value Preview**: Displays text preview and hex dump
- **Protobuf Deserialization**: Automatically attempts to deserialize binary data as protobuf messages
- **JSON View**: Pretty-printed JSON representation of protobuf data

## Protobuf Integration

### Preparing Protobuf Modules

1. **Compile your .proto files**:
```bash
protoc --python_out=. your_schema.proto
```

2. **Ensure the generated Python file is accessible**:
```bash
ls your_schema_pb2.py
```

3. **Use with Lmdbug**:
```bash
lmdbug /path/to/database \
  --protobuf-module your_schema_pb2.py \
  --message-class YourMessage
```

### Example: Using the Sample Schema

The project includes a sample protobuf schema in `examples/sample_proto.proto`:

```bash
# Compile the sample proto
protoc --python_out=examples examples/sample_proto.proto

# Use with Lmdbug
lmdbug ./sample_database \
  --protobuf-module examples/sample_proto_pb2.py \
  --message-class User
```

## Database Operations

### Supported Search Types
1. **Exact Key Match**: Find a specific entry by its exact key
2. **Prefix Search**: Find all keys starting with a given prefix
3. **Pattern Search**: Find keys containing a substring
4. **Index Range**: Browse entries by their position in the database

### Data Format Support
- **Text Keys**: UTF-8 encoded strings
- **Binary Keys**: Hex representation with ASCII preview
- **Binary Values**: Automatic format detection
- **Protobuf Values**: Deserialization with multiple message type attempts

## Configuration

### Environment Variables
No environment variables are required. All configuration is done via command line arguments or the web interface.

### Runtime Configuration
- Database path can be changed in the web interface
- Protobuf modules can be loaded dynamically
- Message types can be switched on-the-fly

## Troubleshooting

### Common Issues

#### Database Not Found
```
Error: Database path does not exist: /path/to/database
```
**Solution**: Verify the database path exists and is a directory containing LMDB files.

#### Protobuf Module Loading Failed
```
Error: Failed to load protobuf modules: No module named 'user_pb2'
```
**Solutions**:
- Ensure the .py file path is correct
- Check that the protobuf module was compiled successfully
- Verify the message class name matches the proto definition

#### Port Already in Use
```
Error: Address already in use
```
**Solution**: Use a different port with `--port` option or stop the service using the port.

### Debug Mode
Enable debug logging for detailed information:
```bash
lmdbug /path/to/database --log-level DEBUG
```

### Performance Considerations
- Large databases: Use index range browsing instead of loading all entries
- Memory usage: Protobuf deserialization consumes memory proportional to data size
- Network access: Use `--host 0.0.0.0` only in trusted environments

## Integration Examples

### CI/CD Pipeline Usage
```bash
#!/bin/bash
# Automated database validation script
lmdbug /build/output/database \
  --protobuf-module build_pb2.py \
  --message-class BuildResult \
  --port 9999 &

# Run your tests against the preview server
curl http://localhost:9999/api/health
# ... additional validation logic
```

### Development Workflow
```bash
# Terminal 1: Start development server
lmdbug ./dev_database --log-level DEBUG

# Terminal 2: Make changes to your data
python populate_database.py

# Browse to http://localhost:7860 to see changes
```

## API Reference

The web interface exposes the following core functionality programmatically:

### Database Information
- Get database statistics (entry count, page size, etc.)
- List available protobuf message types

### Data Access
- Retrieve entries by index range
- Search by key patterns
- Get formatted entry data with protobuf deserialization

### Configuration
- Set database path
- Load protobuf modules
- Switch message types

## Architecture Overview

Lmdbug follows a clean architecture with separate concerns:

- **Core Layer**: LMDB reading, protobuf handling, data formatting
- **Service Layer**: Preview service orchestrating core components  
- **UI Layer**: Gradio web interface
- **CLI Layer**: Typer-based command line interface

This separation ensures the tool can be extended or integrated into other systems easily.

## Version History

### Current Version Features
- Direct CLI parameter configuration (no config files needed)
- Modern Python 3.9+ type system
- Simplified dependencies (5 packages)
- Ruff-compliant code formatting
- Loguru-based logging
- Typer-based CLI

### Breaking Changes from Previous Versions
- YAML configuration files no longer supported
- Click CLI replaced with Typer
- `--create-config` option removed
- Simplified parameter structure

## Contributing

When contributing to Lmdbug:

1. Follow ruff formatting standards
2. Use modern Python type hints (union types with `|`)
3. Write clear, concise documentation
4. Test with multiple LMDB databases and protobuf schemas
5. Ensure compatibility with Python 3.9+

## License

[Include license information here]