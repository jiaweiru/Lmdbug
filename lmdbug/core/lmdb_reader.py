import re
import lmdb
from pathlib import Path
from itertools import islice

from .logging import get_logger
from .exceptions import DatabaseError

logger = get_logger(__name__)


class LMDBReader:
    """Simple LMDB database reader for data preview and key search."""

    def __init__(self, db_path: str, map_size: int = 10 * 1024 * 1024 * 1024):
        """Initialize LMDB reader.

        Args:
            db_path: Path to the LMDB database
            map_size: Maximum size of the database in bytes (default: 10GB)
        """
        self.db_path = Path(db_path)
        self.map_size = map_size
        self.env = None
        self._validate_path()

    def _validate_path(self):
        """Validate that the LMDB database path exists."""
        if not self.db_path.exists():
            error_msg = f"LMDB database path not found: {self.db_path}"
            logger.warning(error_msg)  # Changed from error to warning - validation issue
            raise DatabaseError(error_msg)
        if not self.db_path.is_dir():
            error_msg = f"LMDB path must be a directory, got: {self.db_path}"
            logger.warning(error_msg)  # Changed from error to warning - validation issue
            raise DatabaseError(error_msg)

    def open(self):
        """Open the LMDB environment."""
        try:
            self.env = lmdb.open(
                str(self.db_path), readonly=True, lock=False, map_size=self.map_size
            )
            logger.info(f"Successfully opened LMDB database: {self.db_path}")
            logger.debug(f"LMDB database map_size: {self.map_size}")
        except Exception as e:
            error_msg = f"Failed to open LMDB database at {self.db_path}: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def close(self):
        """Close the LMDB environment."""
        if self.env:
            self.env.close()
            self.env = None
            logger.debug("LMDB database closed")

    def _ensure_open(self):
        """Ensure database is open, raise error if not."""
        if not self.env:
            error_msg = "Database not opened. Call open() first."
            logger.error(error_msg)
            raise DatabaseError(error_msg)

    def __enter__(self):
        """Context manager entry."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, _exc_tb):
        """Context manager exit."""
        self.close()
        if exc_type:
            logger.error(f"Exception in LMDB context: {exc_type.__name__}: {exc_val}")
        return False

    def get_basic_info(self) -> dict:
        """Get basic database information."""
        self._ensure_open()
        with self.env.begin() as txn:
            stats = txn.stat()
            info = self.env.info()
            return {
                "entries": stats["entries"],
                "map_size": info["map_size"],
            }

    def search_keys(self, pattern: str, count: int = 10) -> list[tuple[bytes, bytes]]:
        """Search keys matching regex pattern and return first count matches."""
        self._ensure_open()

        # Try to compile as regex pattern
        try:
            regex = re.compile(pattern, re.IGNORECASE)
            use_regex = True
        except re.error as e:
            logger.warning(f"Invalid regex pattern '{pattern}': {e}")
            pattern_bytes = pattern.encode("utf-8")
            use_regex = False

        def matches_pattern(key: bytes) -> bool:
            if use_regex:
                return bool(regex.search(key.decode("utf-8", errors="ignore")))
            else:
                return pattern_bytes in key

        with self.env.begin() as txn:
            cursor = txn.cursor()
            cursor.first()

            # Use generator + islice for efficient matching
            matching_entries = (
                (key, value) for key, value in cursor if matches_pattern(key)
            )
            return list(islice(matching_entries, count))

    def get_first_entries(self, count: int = 10) -> list[tuple[bytes, bytes]]:
        """Get the first N entries from the database."""
        self._ensure_open()
        with self.env.begin() as txn:
            cursor = txn.cursor()
            cursor.first()
            return list(islice(cursor, count))
