from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import lmdb

# Default LMDB configuration
DEFAULT_DB_PATH = Path("data/prod.lmdb")
DEFAULT_MAP_SIZE = 1024 * 1024 * 1024 * 10  # 10 GB

# Global variable to hold the LMDB environment
_ENV: Optional[lmdb.Environment] = None


def get_db(
    path: Path = DEFAULT_DB_PATH,
    map_size: int = DEFAULT_MAP_SIZE,
    readonly: bool = False,
) -> lmdb.Environment:
    """Get a connection to the LMDB database, creating it if it doesn't exist."""
    global _ENV
    if _ENV is None:
        # Ensure the parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        _ENV = lmdb.open(str(path), map_size=map_size, readonly=readonly, create=True)
    return _ENV


def hgetall(txn: lmdb.Transaction, key: str) -> Optional[dict[str, Any]]:
    """Get a hash map from the database."""
    value = txn.get(key.encode("utf-8"))
    if value is None:
        return None
    return json.loads(value.decode("utf-8"))


def hset(txn: lmdb.Transaction, key: str, mapping: dict[str, Any]) -> None:
    """Set a hash map in the database."""
    value = json.dumps(mapping).encode("utf-8")
    txn.put(key.encode("utf-8"), value)