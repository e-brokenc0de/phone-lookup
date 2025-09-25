"""LMDB-backed storage utilities for phone lookup data."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Iterable, Iterator, Tuple

import lmdb

DEFAULT_MAP_SIZE = int(os.getenv("PHONE_LOOKUP_LMDB_MAP_SIZE", str(1 << 33)))

MappingItem = Tuple[str, Dict[str, str]]


def _encode_mapping(mapping: Dict[str, str]) -> bytes:
    return json.dumps(mapping, ensure_ascii=False).encode("utf-8")


def _decode_mapping(raw: bytes | None) -> Dict[str, str]:
    if raw is None:
        return {}
    try:
        return json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
        return {}


class PhoneLookupStore:
    """Convenience wrapper around an LMDB environment."""

    def __init__(self, env: lmdb.Environment):
        self._env = env

    @classmethod
    def open(cls, path: Path, *, map_size: int = DEFAULT_MAP_SIZE) -> "PhoneLookupStore":
        path = Path(path)
        if path.exists() and not path.is_dir():
            raise ValueError(f"Database path must be a directory: {path}")
        path.mkdir(parents=True, exist_ok=True)
        env = lmdb.open(
            str(path),
            map_size=map_size,
            subdir=True,
            max_dbs=1,
            lock=True,
            readahead=True,
            writemap=False,
        )
        return cls(env)

    def close(self) -> None:
        self._env.close()

    def __enter__(self) -> "PhoneLookupStore":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        self.close()

    def get_mapping(self, key: str) -> Dict[str, str]:
        encoded_key = key.encode("utf-8")
        with self._env.begin(buffers=False) as txn:
            raw = txn.get(encoded_key)
        return _decode_mapping(raw)

    def put_mapping(self, key: str, mapping: Dict[str, str]) -> None:
        encoded_key = key.encode("utf-8")
        encoded_value = _encode_mapping(mapping)
        with self._env.begin(write=True) as txn:
            txn.put(encoded_key, encoded_value, overwrite=True)

    def bulk_put(self, items: Iterable[MappingItem], *, batch_size: int = 10_000) -> None:
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")

        txn = self._env.begin(write=True)
        count = 0
        try:
            for key, mapping in items:
                txn.put(key.encode("utf-8"), _encode_mapping(mapping), overwrite=True)
                count += 1
                if count % batch_size == 0:
                    txn.commit()
                    txn = self._env.begin(write=True)
            if count == 0:
                txn.abort()
            elif count % batch_size != 0:
                txn.commit()
            else:
                txn.abort()
        except Exception:
            txn.abort()
            raise

    def iterate_keys(self) -> Iterator[str]:
        with self._env.begin() as txn:
            with txn.cursor() as cursor:
                for key, _ in cursor:
                    yield key.decode("utf-8")

