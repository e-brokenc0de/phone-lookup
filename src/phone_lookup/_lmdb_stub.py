"""Fallback in-memory LMDB-compatible shim used for testing."""
from __future__ import annotations

import pickle
import threading
from pathlib import Path
from typing import Dict, Iterator, Tuple


class Cursor:
    def __init__(self, view: Dict[bytes, bytes]):
        self._items = sorted(view.items())
        self._index = 0

    def __enter__(self) -> "Cursor":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        return None

    def __iter__(self) -> Iterator[Tuple[bytes, bytes]]:
        return iter(self._items)


class Transaction:
    def __init__(self, env: "Environment", write: bool):
        self._env = env
        self._write = write
        self._completed = False
        if write:
            self._view = dict(env._data)
        else:
            self._view = env._data

    def __enter__(self) -> "Transaction":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        if exc_type is not None:
            self.abort()
            return None
        if self._write and not self._completed:
            self.commit()
        return None

    def get(self, key: bytes) -> bytes | None:
        return self._view.get(key)

    def put(self, key: bytes, value: bytes, overwrite: bool = True) -> bool:
        if not self._write:
            raise RuntimeError("Cannot write in a read-only transaction")
        if not overwrite and key in self._view:
            return False
        self._view[key] = value
        return True

    def commit(self) -> None:
        if self._completed:
            return
        if self._write:
            with self._env._lock:
                self._env._data = dict(self._view)
                self._env._persist()
        self._completed = True

    def abort(self) -> None:
        self._completed = True

    def cursor(self) -> Cursor:
        return Cursor(dict(self._view))


class Environment:
    def __init__(
        self,
        path: str,
        map_size: int = 0,
        subdir: bool = True,
        max_dbs: int = 1,
        lock: bool = True,
        readahead: bool = True,
        writemap: bool = False,
    ) -> None:
        self._base_path = Path(path)
        if subdir:
            self._base_path.mkdir(parents=True, exist_ok=True)
            self._data_path = self._base_path / "stub-lmdb.pickle"
        else:
            self._base_path.parent.mkdir(parents=True, exist_ok=True)
            self._data_path = self._base_path
        self._lock = threading.RLock() if lock else threading.Lock()
        self._data: Dict[bytes, bytes] = {}
        self._load()

    def _load(self) -> None:
        if self._data_path.exists():
            with self._data_path.open("rb") as handle:
                try:
                    data = pickle.load(handle)
                except Exception:
                    data = {}
            if isinstance(data, dict):
                self._data = {bytes(k): bytes(v) for k, v in data.items()}

    def _persist(self) -> None:
        with self._data_path.open("wb") as handle:
            pickle.dump(self._data, handle)

    def begin(self, write: bool = False, buffers: bool | None = None) -> Transaction:
        return Transaction(self, write)

    def close(self) -> None:
        return None


def open(
    path: str,
    map_size: int = 0,
    subdir: bool = True,
    max_dbs: int = 1,
    lock: bool = True,
    readahead: bool = True,
    writemap: bool = False,
) -> Environment:
    return Environment(path, map_size=map_size, subdir=subdir, max_dbs=max_dbs, lock=lock, readahead=readahead, writemap=writemap)
