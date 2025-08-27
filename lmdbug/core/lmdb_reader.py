import lmdb
from pathlib import Path
from loguru import logger
from .exceptions import (
    DatabaseNotFoundError,
    DatabasePathError,
    DatabaseNotOpenError,
    DatabaseConnectionError,
)


class LMDBReader:
    """
    LMDB database reader with support for key-based queries and data preview.
    """

    def __init__(self, db_path: str):
        """Initialize LMDB reader."""
        self.db_path = Path(db_path)
        self.env = None
        self._validate_path()

    def _validate_path(self):
        """Validate that the LMDB database path exists."""
        if not self.db_path.exists():
            error_msg = f"LMDB database path not found: {self.db_path}"
            logger.error(error_msg)
            raise DatabaseNotFoundError(error_msg)
        if not self.db_path.is_dir():
            error_msg = f"LMDB path must be a directory, got: {self.db_path}"
            logger.error(error_msg)
            raise DatabasePathError(error_msg)

    def open(self):
        """Open the LMDB environment."""
        try:
            self.env = lmdb.open(str(self.db_path), readonly=True, lock=False)
            logger.info(f"Successfully opened LMDB database: {self.db_path}")
        except Exception as e:
            error_msg = f"Failed to open LMDB database at {self.db_path}: {e}"
            logger.error(error_msg)
            raise DatabaseConnectionError(error_msg) from e

    def close(self):
        """Close the LMDB environment."""
        if self.env:
            self.env.close()
            self.env = None
            logger.info("LMDB database closed")
    
    def _ensure_open(self):
        """Ensure database is open, raise error if not."""
        if not self.env:
            error_msg = "Database not opened. Call open() first."
            logger.error(error_msg)
            raise DatabaseNotOpenError(error_msg)

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

    def get_stats(self) -> dict[str, int]:
        """Get database statistics."""
        self._ensure_open()

        with self.env.begin() as txn:
            stats = txn.stat()
            return {
                "entries": stats["entries"],
                "page_size": stats["psize"],
                "depth": stats["depth"],
                "branch_pages": stats["branch_pages"],
                "leaf_pages": stats["leaf_pages"],
                "overflow_pages": stats["overflow_pages"],
            }

    def get_by_key(self, key: bytes) -> bytes | None:
        """Get value by exact key match."""
        self._ensure_open()

        with self.env.begin() as txn:
            return txn.get(key)

    def get_keys_with_prefix(self, prefix: bytes, limit: int = 100) -> list[bytes]:
        """Get keys that start with the given prefix."""
        self._ensure_open()

        keys = []
        with self.env.begin() as txn:
            cursor = txn.cursor()
            cursor.set_range(prefix)
            
            for key, _ in cursor:
                if not key.startswith(prefix):
                    break
                keys.append(key)
                if len(keys) >= limit:
                    break
        
        return keys

    def get_first_n_entries(self, n: int = 10) -> list[tuple[bytes, bytes]]:
        """Get the first N entries from the database."""
        self._ensure_open()

        with self.env.begin() as txn:
            cursor = txn.cursor()
            cursor.first()
            return [(key, value) for key, value in cursor][:n]

    def search_keys_by_index(self, start_index: int, count: int = 10) -> list[tuple[bytes, bytes]]:
        """Get entries by index range for pagination."""
        self._ensure_open()

        with self.env.begin() as txn:
            cursor = txn.cursor()
            cursor.first()
            
            # Skip to start_index
            for _ in range(start_index):
                if not cursor.next():
                    return []
            
            # Collect count entries
            return [(key, value) for key, value in cursor][:count]

    def iter_all_entries(self):
        """Iterator over all entries in the database."""
        self._ensure_open()

        with self.env.begin() as txn:
            cursor = txn.cursor()
            cursor.first()

            for key, value in cursor:
                yield key, value

    def search_keys_by_pattern(self, pattern: str, limit: int = 100) -> list[bytes]:
        """Search for keys containing a substring pattern."""
        self._ensure_open()

        pattern_bytes = pattern.encode("utf-8", errors="ignore")
        matching_keys = []
        
        with self.env.begin() as txn:
            cursor = txn.cursor()
            cursor.first()
            
            for key, _ in cursor:
                if len(matching_keys) >= limit:
                    break
                try:
                    if pattern_bytes in key:
                        matching_keys.append(key)
                except Exception as e:
                    logger.debug(f"Skipping key comparison due to error: {e}")
        
        return matching_keys
