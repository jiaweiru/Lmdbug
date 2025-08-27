#!/usr/bin/env python3
"""
Sample script to create a test LMDB database with sample data.
This script demonstrates how to create an LMDB database and store Protobuf data.
"""

import lmdb
import json
import sys
from pathlib import Path

# Note: This is a simple example. In practice, you would:
# 1. Compile your .proto files using protoc
# 2. Import the generated Python modules
# 3. Create message instances and serialize them

def create_sample_database(db_path: str):
    """
    Create a sample LMDB database with test data.
    
    Args:
        db_path: Path where to create the database
    """
    try:
        # Create database directory
        Path(db_path).mkdir(parents=True, exist_ok=True)
        
        # Open LMDB environment
        with lmdb.open(db_path, map_size=10 * 1024 * 1024) as env:  # 10MB
            with env.begin(write=True) as txn:
                
                # Sample 1: Simple string data
                txn.put(b'user:1', b'{"id": 1, "name": "Alice", "email": "alice@example.com"}')
                txn.put(b'user:2', b'{"id": 2, "name": "Bob", "email": "bob@example.com"}')
                txn.put(b'user:3', b'{"id": 3, "name": "Charlie", "email": "charlie@example.com"}')
                
                # Sample 2: Binary data (simulating protobuf)
                # In real usage, this would be protobuf.SerializeToString()
                sample_binary = bytes([
                    0x08, 0x96, 0x01, 0x12, 0x05, 0x41, 0x6c, 0x69, 0x63, 0x65,
                    0x1a, 0x11, 0x61, 0x6c, 0x69, 0x63, 0x65, 0x40, 0x65, 0x78,
                    0x61, 0x6d, 0x70, 0x6c, 0x65, 0x2e, 0x63, 0x6f, 0x6d
                ])
                txn.put(b'proto:user:1', sample_binary)
                
                # Sample 3: Product data
                product_data = {
                    "id": "PROD001",
                    "name": "Sample Product",
                    "price": 2999,
                    "category": "Electronics"
                }
                txn.put(b'product:PROD001', json.dumps(product_data).encode('utf-8'))
                
                # Sample 4: Various key formats
                txn.put(b'config:app_version', b'1.0.0')
                txn.put(b'config:debug_mode', b'false')
                txn.put(b'stats:total_users', b'150')
                txn.put(b'stats:active_sessions', b'23')
                
                # Sample 5: Numeric keys
                for i in range(10):
                    key = f"item:{i:04d}".encode()
                    value = f"Sample item number {i}".encode()
                    txn.put(key, value)
                
                print(f"✓ Created sample LMDB database at: {db_path}")
                print(f"✓ Added {txn.stat()['entries']} entries")
                
    except Exception as e:
        print(f"✗ Failed to create sample database: {e}")
        sys.exit(1)


def main():
    """Main function to create sample database."""
    if len(sys.argv) != 2:
        print("Usage: python create_sample_db.py <database_path>")
        print("Example: python create_sample_db.py ./sample_lmdb")
        sys.exit(1)
    
    db_path = sys.argv[1]
    print(f"Creating sample LMDB database at: {db_path}")
    
    create_sample_database(db_path)
    
    print("\nTo use this database with Lmdbug:")
    print(f"  lmdbug --db-path {db_path}")
    print("\nExample keys to search for:")
    print("  - user:1")
    print("  - user: (prefix search)")
    print("  - config: (prefix search)")
    print("  - item: (prefix search)")


if __name__ == "__main__":
    main()