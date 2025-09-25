"""Utilities for importing phone metadata into Redis."""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

from redis import Redis


def load_npanxx(redis: Redis, path: Path, batch: int = 10_000) -> None:
    """Load NPANXX data into Redis hashes."""
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        pipe = redis.pipeline(transaction=False)
        for idx, row in enumerate(reader, start=1):
            key = f"npanxx:{row['NPA']}{row['NXX']}:{row['BLOCK_ID']}"
            mapping = {
                "OCN": row.get("OCN", ""),
                "LTYPE": row.get("LTYPE", ""),
                "NXXTYPE": row.get("NXXTYPE", ""),
                "RC": row.get("RC", ""),
                "RCLONG": row.get("RCLONG", ""),
                "STATE": row.get("STATE", ""),
                "COUNTRY": row.get("COUNTRY", ""),
                "LATA": row.get("LATA", ""),
                "SWITCH": row.get("SWITCH", ""),
                "TBP_IND": row.get("TBP_IND", ""),
                "ADATE": row.get("ADATE", ""),
                "EFFDATE": row.get("EFFDATE", ""),
            }
            pipe.hset(key, mapping=mapping)
            if idx % batch == 0:
                pipe.execute()
        pipe.execute()


def load_ocn(redis: Redis, path: Path, batch: int = 5_000) -> None:
    """Load OCN data into Redis hashes."""
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        pipe = redis.pipeline(transaction=False)
        for idx, row in enumerate(reader, start=1):
            key = f"ocn:{row['OCN']}"
            mapping = {
                "COMPANY": row.get("COMPANY", ""),
                "DBA": row.get("DBA", ""),
                "CommonName": row.get("CommonName", ""),
                "TYPE": row.get("TYPE", ""),
                "SMS": row.get("SMS", ""),
                "Rural": row.get("Rural", ""),
            }
            pipe.hset(key, mapping=mapping)
            if idx % batch == 0:
                pipe.execute()
        pipe.execute()


def import_all(redis: Redis, npanxx_path: Path, ocn_path: Path) -> None:
    load_npanxx(redis, npanxx_path)
    load_ocn(redis, ocn_path)


def ensure_paths_exist(paths: Iterable[Path]) -> None:
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required data files: {', '.join(missing)}")
