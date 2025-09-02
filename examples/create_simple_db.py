#!/usr/bin/env python3
"""
Simple script to create a minimal LMDB database with protobuf data.
This demonstrates basic usage of LMDB with protobuf messages containing text and audio.
"""

import lmdb
import numpy as np
import sys
from pathlib import Path

# Import the generated protobuf class
try:
    from simple_message_pb2 import SimpleMessage
except ImportError:
    print("Error: simple_message_pb2.py not found. Please run:")
    print("protoc --python_out=. simple_message.proto")
    sys.exit(1)


def generate_sample_audio(duration_seconds: float = 1.0, frequency: int = 440) -> bytes:
    """Generate simple sine wave audio as 24kHz 16-bit PCM.

    Args:
        duration_seconds: Duration of audio in seconds
        frequency: Frequency of sine wave in Hz

    Returns:
        Raw PCM audio data as bytes
    """
    sample_rate = 24000
    num_samples = int(sample_rate * duration_seconds)

    # Generate time array
    t = np.linspace(0, duration_seconds, num_samples, False)

    # Generate sine wave
    audio_signal = np.sin(frequency * 2 * np.pi * t)

    # Convert to 16-bit integers
    audio_16bit = (audio_signal * 32767).astype(np.int16)

    return audio_16bit.tobytes()


def create_simple_database(db_path: str):
    """Create a simple LMDB database with sample protobuf data.

    Args:
        db_path: Path where to create the database
    """
    try:
        Path(db_path).mkdir(parents=True, exist_ok=True)

        with lmdb.open(db_path, map_size=10 * 1024 * 1024) as env:  # 10MB
            with env.begin(write=True) as txn:
                # Sample data: text and audio pairs
                samples = [
                    {
                        "text": "Hello, this is the first audio sample.",
                        "frequency": 440,  # A4 note
                        "duration": 1.0,
                    },
                    {
                        "text": "This is sample number two with a different tone.",
                        "frequency": 523,  # C5 note
                        "duration": 1.5,
                    },
                    {
                        "text": "Third example message with longer audio content.",
                        "frequency": 659,  # E5 note
                        "duration": 2.0,
                    },
                ]

                # Create and store protobuf messages
                for i, sample_data in enumerate(samples):
                    # Create SimpleMessage protobuf
                    message = SimpleMessage()
                    message.text = sample_data["text"]
                    message.wav = generate_sample_audio(
                        duration_seconds=sample_data["duration"],
                        frequency=sample_data["frequency"],
                    )

                    # Store in LMDB with simple key format
                    key = f"message:{i:03d}".encode()
                    txn.put(key, message.SerializeToString())

                print(f"✓ Created simple LMDB database at: {db_path}")
                print(f"✓ Added {len(samples)} SimpleMessage entries")
                print(f"✓ Total entries in database: {txn.stat()['entries']}")

    except Exception as e:
        print(f"✗ Failed to create database: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


def main():
    """Main function to create the simple database."""
    if len(sys.argv) != 2:
        print("Usage: python create_simple_db.py <database_path>")
        print("Example: python create_simple_db.py ./simple_lmdb")
        print(
            "\nThis creates a minimal LMDB database with SimpleMessage protobuf data."
        )
        sys.exit(1)

    db_path = sys.argv[1]
    print(f"Creating simple LMDB database at: {db_path}")

    create_simple_database(db_path)

    print(f"\n🎉 Simple database created successfully!")
    print(f"\nTo use this database with Lmdbug:")
    print(f"  lmdbug --db-path {db_path} \\")
    print(f"         --protobuf-module examples/simple_message_pb2.py \\")
    print(f"         --message-class SimpleMessage")
    print(f"\nExample keys to search for:")
    print("  - message: (all sample messages)")
    print("  - message:000, message:001, message:002 (specific messages)")
    print(f"\nEach message contains:")
    print("  - 'text' field: String content")
    print("  - 'wav' field: 24kHz 16-bit PCM audio data")


if __name__ == "__main__":
    main()
