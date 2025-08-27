import lmdb
from pathlib import Path
from loguru import logger


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
            raise FileNotFoundError(f"LMDB path not found: {self.db_path}")
        if not self.db_path.is_dir():
            raise ValueError(f"LMDB path must be a directory: {self.db_path}")
    
    def open(self):
        """Open the LMDB environment."""
        try:
            self.env = lmdb.open(str(self.db_path), readonly=True, lock=False)
            logger.info(f"Successfully opened LMDB database: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to open LMDB database: {e}")
            raise
    
    def close(self):
        """Close the LMDB environment."""
        if self.env:
            self.env.close()
            self.env = None
            logger.info("LMDB database closed")
    
    def __enter__(self):
        """Context manager entry."""
        self.open()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def get_stats(self) -> dict[str, int]:
        """Get database statistics."""
        if not self.env:
            raise RuntimeError("Database not opened")
            
        with self.env.begin() as txn:
            stats = txn.stat()
            return {
                "entries": stats["entries"],
                "page_size": stats["psize"],
                "depth": stats["depth"],
                "branch_pages": stats["branch_pages"],
                "leaf_pages": stats["leaf_pages"],
                "overflow_pages": stats["overflow_pages"]
            }
    
    def get_by_key(self, key: bytes) -> bytes | None:
        """Get value by exact key match."""
        if not self.env:
            raise RuntimeError("Database not opened")
            
        with self.env.begin() as txn:
            return txn.get(key)
    
    def get_keys_with_prefix(self, prefix: bytes, limit: int = 100) -> list[bytes]:
        """Get keys that start with the given prefix."""
        if not self.env:
            raise RuntimeError("Database not opened")
            
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
        if not self.env:
            raise RuntimeError("Database not opened")
            
        entries = []
        with self.env.begin() as txn:
            cursor = txn.cursor()
            cursor.first()
            
            for key, value in cursor:
                entries.append((key, value))
                if len(entries) >= n:
                    break
                    
        return entries
    
    def search_keys_by_index(self, start_index: int, count: int = 10) -> list[tuple[bytes, bytes]]:
        """Get entries by index range for pagination."""
        if not self.env:
            raise RuntimeError("Database not opened")
            
        entries = []
        current_index = 0
        
        with self.env.begin() as txn:
            cursor = txn.cursor()
            cursor.first()
            
            # Skip to start_index
            for _ in range(start_index):
                if not cursor.next():
                    return entries
            
            # Collect count entries
            for key, value in cursor:
                entries.append((key, value))
                if len(entries) >= count:
                    break
                    
        return entries
    
    def iter_all_entries(self):
        """
        Iterator over all entries in the database.
        
        Yields:
            (key, value) tuples
        """
        if not self.env:
            raise RuntimeError("Database not opened. Call open() first.")
            
        with self.env.begin() as txn:
            cursor = txn.cursor()
            cursor.first()
            
            for key, value in cursor:
                yield key, value
                
    def search_keys_by_pattern(self, pattern: str, limit: int = 100) -> list[bytes]:
        """Search for keys containing a substring pattern."""
        if not self.env:
            raise RuntimeError("Database not opened")
            
        pattern_bytes = pattern.encode('utf-8', errors='ignore')
        matching_keys = []
        
        with self.env.begin() as txn:
            cursor = txn.cursor()
            cursor.first()
            
            for key, _ in cursor:
                try:
                    if pattern_bytes in key:
                        matching_keys.append(key)
                        if len(matching_keys) >= limit:
                            break
                except:
                    # Skip keys that can't be compared
                    continue
                    
        return matching_keys