# Lmdbug - LMDB Data Preview Tool

Lmdbug is a web-based tool for previewing and exploring LMDB (Lightning Memory-Mapped Database) data with support for Protocol Buffers (Protobuf) deserialization.

## Features

- **Web-based Interface**: Clean and intuitive Gradio-based web interface
- **LMDB Support**: Read and browse LMDB databases efficiently  
- **Protobuf Integration**: Automatic deserialization of Protobuf-encoded values
- **Multiple Search Methods**: 
  - Browse by index range
  - Search by exact key
  - Search by key prefix
  - Search by key pattern (substring matching)
- **Flexible Configuration**: YAML/JSON configuration files
- **Data Format Support**: 
  - Raw binary data preview
  - Text preview with encoding detection
  - JSON formatted Protobuf data
- **Safe Read-Only Access**: Database opened in read-only mode by default

## Installation

### Prerequisites

- Python 3.7 or higher
- pip package manager

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Install from Source

```bash
pip install -e .
```

## Quick Start

### 1. Basic Usage

Launch Lmdbug with a database path:

```bash
lmdbug /path/to/your/lmdb/database
```

### 2. With Protobuf Support

Specify protobuf module and message class:

```bash
lmdbug /path/to/your/lmdb/database --protobuf-module user_pb2.py --message-class User
```

### 3. Custom Host and Port

```bash
lmdbug /path/to/db --host 0.0.0.0 --port 8080
```

## Configuration

### Simple Command-Line Configuration

Lmdbug uses a simple command-line interface without complex configuration files. All settings can be specified directly as parameters:

```bash
# Database path (required)
lmdbug /path/to/database

# With protobuf support
lmdbug /path/to/database --protobuf-module your_pb2.py --message-class YourMessage

# Custom host and port
lmdbug /path/to/database --host 0.0.0.0 --port 8080

# Debug logging
lmdbug /path/to/database --log-level DEBUG
```

### Protobuf Setup

To use Protobuf deserialization, you need compiled Python protobuf files:

1. **Compile your .proto files**:
   ```bash
   protoc --python_out=. your_proto_file.proto
   ```

2. **Use the compiled module directly**:
   ```bash
   lmdbug /path/to/database --protobuf-module your_proto_file_pb2.py --message-class YourMessageClass
   ```

## Usage Guide

### Web Interface

1. **Load Database**: Enter your LMDB database path and optional protobuf settings
2. **Browse Data**: Use the "Browse" tab to view entries by index range
3. **Search**: Use various search methods to find specific keys
4. **View Results**: Results show both raw data and Protobuf deserialized content

### Search Methods

- **Browse by Index**: View entries 0-9, 10-19, etc.
- **Exact Key Search**: Find a specific key
- **Prefix Search**: Find all keys starting with a prefix  
- **Pattern Search**: Find keys containing a substring

### Data Display

For each entry, Lmdbug shows:
- **Key**: Human-readable key (UTF-8 decoded when possible)
- **Value Size**: Size of the stored value in bytes
- **Protobuf Data**: JSON representation if deserialization succeeds
- **Text Preview**: Raw text preview of the value
- **Raw Hex**: Hexadecimal representation of raw data

## Examples

### Example 1: Basic Setup

```bash
# Create sample database
python examples/create_sample_db.py ./sample_lmdb

# Launch with basic settings
lmdbug ./sample_lmdb
```

### Example 2: E-commerce Product Database

If you have an LMDB database storing e-commerce products as Protobuf:

1. **Create protobuf definition** (`product.proto`):
   ```protobuf
   syntax = "proto3";
   
   message Product {
     string id = 1;
     string name = 2;
     string description = 3;
     int64 price_cents = 4;
     string currency = 5;
   }
   ```

2. **Compile protobuf**:
   ```bash
   protoc --python_out=. product.proto
   ```

3. **Launch with protobuf support**:
   ```bash
   lmdbug /data/products.lmdb --protobuf-module product_pb2.py --message-class Product
   ```

4. **Explore your product data through the web interface**

## Command Line Options

```
Usage: lmdbug [OPTIONS] [DB_PATH]

Arguments:
  [DB_PATH]                       Path to LMDB database directory

Options:
  -p, --protobuf-module TEXT      Path to compiled protobuf module (.py file)
  -m, --message-class TEXT        Protobuf message class name
  --port INTEGER                  Port to run the web interface on (default: 7860)
  --host TEXT                     Host to bind the web interface to (default: 127.0.0.1)
  --log-level [DEBUG|INFO|WARNING|ERROR]  Logging level (default: INFO)
  --version                       Show the version and exit
  --help                          Show this message and exit
```

## Architecture

```
src/lmdbug/
├── core/
│   ├── lmdb_reader.py      # LMDB database reading logic
│   ├── protobuf_handler.py # Protobuf deserialization
│   └── preview_service.py  # Data preview and search service
├── ui/
│   └── gradio_interface.py # Web interface using Gradio
└── main.py                 # Main entry point with Typer CLI
```

## Development

### Setting up Development Environment

```bash
# Clone the repository
git clone <repository-url>
cd Lmdbug

# Install in development mode
pip install -e .

# Install development dependencies
pip install pytest black flake8
```

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black src/
```

## Troubleshooting

### Common Issues

1. **"Database path does not exist"**
   - Verify the LMDB database path is correct
   - Ensure the path points to a directory, not a file

2. **"Failed to load protobuf module"** 
   - Check that protobuf .py files are compiled correctly
   - Verify file paths are absolute or relative to working directory
   - Ensure protobuf Python package is installed
   - Make sure both `--protobuf-module` and `--message-class` are provided together

3. **"Protobuf deserialization failed"**
   - Check that the data is actually Protobuf-encoded
   - Verify you're using the correct message type
   - Some LMDB values might not be Protobuf data

4. **Web interface not accessible**
   - Check firewall settings if using `--host 0.0.0.0`
   - Try different port numbers if 7860 is occupied
   - Check console output for binding errors

### Debug Mode

Enable debug logging for more detailed error information:

```bash
lmdbug /your/db/path --log-level DEBUG
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Changelog

### Version 0.1.0
- Initial release
- Basic LMDB reading capabilities  
- Protobuf deserialization support
- Web-based Gradio interface
- Configuration file support
- Multiple search methods