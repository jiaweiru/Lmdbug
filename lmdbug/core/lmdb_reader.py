import lmdb
from pathlib import Path
from itertools import islice
from .logging import get_logger
from .exceptions import DatabaseError

logger = get_logger(__name__)


class LMDBReader:
    """
    LMDB database reader with support for key-based queries and data preview.
    """

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
            logger.error(error_msg)
            raise DatabaseError(error_msg)
        if not self.db_path.is_dir():
            error_msg = f"LMDB path must be a directory, got: {self.db_path}"
            logger.error(error_msg)
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

    def get_env_info(self) -> dict[str, int]:
        """Get LMDB environment information including mapsize."""
        self._ensure_open()

        info = self.env.info()
        return {
            "map_size": info["map_size"],
            "last_pgno": info["last_pgno"],
            "last_txnid": info["last_txnid"],
            "max_readers": info["max_readers"],
            "num_readers": info["num_readers"],
        }

    def get_by_key(self, key: bytes) -> bytes | None:
        """Get value by exact key match."""
        self._ensure_open()

        with self.env.begin() as txn:
            return txn.get(key)

    def get_keys_with_prefix(self, prefix: bytes, limit: int = 100) -> list[bytes]:
        """Get keys that start with the given prefix."""
        self._ensure_open()

        with self.env.begin() as txn:
            cursor = txn.cursor()
            cursor.set_range(prefix)

            return list(
                islice((key for key, _ in cursor if key.startswith(prefix)), limit)
            )

    def get_first_n_entries(self, n: int = 10) -> list[tuple[bytes, bytes]]:
        """Get the first N entries from the database."""
        self._ensure_open()

        with self.env.begin() as txn:
            cursor = txn.cursor()
            cursor.first()
            return list(islice(cursor, n))

    def search_keys_by_index(
        self, start_index: int, count: int = 10
    ) -> list[tuple[bytes, bytes]]:
        """Get entries by index range for pagination."""
        self._ensure_open()

        with self.env.begin() as txn:
            cursor = txn.cursor()
            cursor.first()

            all_entries = islice(cursor, start_index + count)
            return list(islice(all_entries, start_index, None))

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

        def key_generator():
            with self.env.begin() as txn:
                cursor = txn.cursor()
                cursor.first()

                for key, _ in cursor:
                    if pattern_bytes in key:
                        yield key

        return list(islice(key_generator(), limit))
