import sqlite3

def apply_sqlite_production_pragmas(conn: sqlite3.Connection) -> None:
    """Apply the official high-performance pragma preset. Optimizes read and write throughput with zero external dependencies."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode = WAL;")           # Enable concurrent non-blocking reads and writes.
    cursor.execute("PRAGMA synchronous = NORMAL;")         # Maximize WAL performance without risking database corruption.
    cursor.execute("PRAGMA mmap_size = 268435456;")         # Configure 256 MB of memory-mapped I/O for in-memory reads.
    cursor.execute("PRAGMA cache_size = -64000;")           # Allocate a 64 MB in-memory page cache.
    cursor.execute("PRAGMA temp_store = MEMORY;")          # Store temporary tables in memory.
    cursor.execute("PRAGMA busy_timeout = 5000;")           # 5 segundos de espera anti-bloqueo
