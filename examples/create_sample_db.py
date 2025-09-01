#!/usr/bin/env python3
"""
Sample script to create a test LMDB database with sample data.
This script demonstrates how to create an LMDB database and store Protobuf data
that works with Lmdbug's custom processors (text and audio).
"""

import lmdb
import json
import sys
import base64
import time
from pathlib import Path

# Import the generated protobuf classes
try:
    from sample_proto_pb2 import User, Profile, Location, ProfileSettings
except ImportError:
    print("Error: sample_proto_pb2.py not found. Please run:")
    print("protoc --python_out=. sample_proto.proto")
    sys.exit(1)


def generate_fake_pcm_audio(duration_ms: int = 1000) -> str:
    """Generate fake PCM audio data for demonstration.

    Args:
        duration_ms: Duration in milliseconds

    Returns:
        Base64 encoded PCM audio data
    """
    # Generate fake 24kHz 16-bit PCM data
    sample_rate = 24000
    samples = int(sample_rate * duration_ms / 1000)

    # Simple sine wave pattern for demonstration
    fake_pcm_data = bytearray()
    for i in range(samples):
        # Simple pattern to simulate PCM data
        value = int(32767 * 0.5 * (i % 100) / 100)  # 16-bit signed
        fake_pcm_data.extend(value.to_bytes(2, byteorder="little", signed=True))

    return base64.b64encode(fake_pcm_data).decode("utf-8")


def create_sample_database(db_path: str):
    """
    Create a sample LMDB database with test data.

    Args:
        db_path: Path where to create the database
    """
    try:
        Path(db_path).mkdir(parents=True, exist_ok=True)

        with lmdb.open(
            db_path, map_size=50 * 1024 * 1024
        ) as env:  # 50MB for audio data
            with env.begin(write=True) as txn:
                # Create sample User protobuf messages with audio and text data
                users_data = [
                    {
                        "id": 1,
                        "username": "alice_dev",
                        "email": "alice@example.com",
                        "description": "Software developer from San Francisco. Loves building web applications and contributing to open source projects. Currently working on machine learning models for natural language processing.",
                        "voice_audio": generate_fake_pcm_audio(
                            1500
                        ),  # 1.5 second audio
                    },
                    {
                        "id": 2,
                        "username": "bob_designer",
                        "email": "bob@example.com",
                        "description": "UX/UI designer with 5 years of experience. Passionate about creating user-friendly interfaces and improving digital experiences. Based in New York City.",
                        "voice_audio": generate_fake_pcm_audio(2000),  # 2 second audio
                    },
                    {
                        "id": 3,
                        "username": "charlie_pm",
                        "email": "charlie@example.com",
                        "description": "Product manager focused on B2B SaaS solutions. Expert in agile methodologies and cross-functional team leadership. Enjoys hiking and photography in spare time.",
                        "voice_audio": generate_fake_pcm_audio(
                            1200
                        ),  # 1.2 second audio
                    },
                ]

                for user_data in users_data:
                    # Create User protobuf message
                    user = User()
                    user.id = user_data["id"]
                    user.username = user_data["username"]
                    user.email = user_data["email"]
                    user.description = user_data[
                        "description"
                    ]  # Text for text processor
                    user.voice_audio = user_data[
                        "voice_audio"
                    ]  # Audio for audio processor
                    user.created_at = int(time.time())
                    user.is_active = True
                    user.tags.extend(["demo", "sample", "lmdbug"])
                    user.metadata["source"] = "sample_generator"
                    user.metadata["version"] = "1.0"

                    # Create profile
                    user.profile.display_name = f"User {user_data['username']}"
                    user.profile.bio = (
                        user_data["description"][:100] + "..."
                    )  # Short bio
                    user.profile.settings.is_public = True
                    user.profile.settings.theme = ProfileSettings.Theme.AUTO
                    user.profile.settings.language = "en"

                    # Serialize and store
                    key = f"proto:user:{user.id}".encode()
                    txn.put(key, user.SerializeToString())

                # Add some raw JSON data for comparison
                json_users = [
                    {"id": 101, "name": "JSON Alice", "type": "json_sample"},
                    {"id": 102, "name": "JSON Bob", "type": "json_sample"},
                ]
                for json_user in json_users:
                    key = f"json:user:{json_user['id']}".encode()
                    txn.put(key, json.dumps(json_user).encode("utf-8"))

                # Add configuration and statistics
                config_data = {
                    "app:version": "2.1.0",
                    "app:environment": "development",
                    "app:debug_mode": "true",
                    "db:max_connections": "100",
                }
                for config_key, config_value in config_data.items():
                    txn.put(f"config:{config_key}".encode(), config_value.encode())

                stats_data = {
                    "users:total": "250",
                    "users:active": "180",
                    "sessions:current": "45",
                    "audio:processed": "1024",
                }
                for stat_key, stat_value in stats_data.items():
                    txn.put(f"stats:{stat_key}".encode(), stat_value.encode())

                # Add some test items
                for i in range(15):
                    key = f"test:item:{i:04d}".encode()
                    value = (
                        f"Test item #{i} - created for Lmdbug demonstration".encode()
                    )
                    txn.put(key, value)

                print(f"✓ Created sample LMDB database at: {db_path}")
                print(f"✓ Added {txn.stat()['entries']} entries")
                print(
                    f"✓ Generated {len(users_data)} User protobuf messages with audio and text data"
                )

    except Exception as e:
        print(f"✗ Failed to create sample database: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


def main():
    """Main function to create sample database."""
    if len(sys.argv) != 2:
        print("Usage: python create_sample_db.py <database_path>")
        print("Example: python create_sample_db.py ./sample_lmdb")
        print("\nThis script creates a sample LMDB database with:")
        print("  - User protobuf messages containing audio and text data")
        print("  - Compatible with config_examples/custom_processors.py")
        print("  - Demonstrates text and audio preview functionality")
        sys.exit(1)

    db_path = sys.argv[1]
    print(f"Creating sample LMDB database at: {db_path}")
    print("Generating protobuf data with audio and text content...")

    create_sample_database(db_path)

    print(f"\n🎉 Sample database created successfully!")
    print(f"\nTo use this database with Lmdbug:")
    print(f"  lmdbug --db-path {db_path} \\")
    print(f"         --protobuf-module examples/sample_proto_pb2.py \\")
    print(f"         --message-class User")
    print(f"\nExample keys to search for:")
    print("  - proto:user: (protobuf users with audio/text)")
    print("  - json:user: (JSON users for comparison)")
    print("  - config: (configuration entries)")
    print("  - stats: (statistics entries)")
    print("  - test:item: (test items)")
    print(f"\nThe protobuf messages contain:")
    print("  - 'description' field: Long text for text preview")
    print("  - 'voice_audio' field: Base64 PCM audio for audio preview")
    print("  - Other fields: username, email, tags, etc.")


if __name__ == "__main__":
    main()
