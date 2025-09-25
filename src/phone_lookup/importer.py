"""Utilities for importing phone metadata into LMDB."""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

import lmdb

from . import database


def load_npanxx(db: lmdb.Environment, path: Path) -> None:
    """Load NPANXX data into LMDB."""
    with db.begin(write=True) as txn, path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
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
            database.hset(txn, key, mapping)


def load_ocn(db: lmdb.Environment, path: Path) -> None:
    """Load OCN data into LMDB."""
    with db.begin(write=True) as txn, path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            key = f"ocn:{row['OCN']}"
            mapping = {
                "COMPANY": row.get("COMPANY", ""),
                "DBA": row.get("DBA", ""),
                "CommonName": row.get("CommonName", ""),
                "TYPE": row.get("TYPE", ""),
                "SMS": row.get("SMS", ""),
                "Rural": row.get("Rural", ""),
            }
            database.hset(txn, key, mapping)


def import_all(db: lmdb.Environment, npanxx_path: Path, ocn_path: Path) -> None:
    load_npanxx(db, npanxx_path)
    load_ocn(db, ocn_path)


def ensure_paths_exist(paths: Iterable[Path]) -> None:
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required data files: {', '.join(missing)}")
