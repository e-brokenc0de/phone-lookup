"""Utilities for importing phone metadata into the LMDB store."""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

from .store import PhoneLookupStore


def load_npanxx(store: PhoneLookupStore, path: Path, batch: int = 10_000) -> None:
    """Load NPANXX data into LMDB records."""

    def rows() -> Iterable[tuple[str, dict[str, str]]]:
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                key = f"npanxx:{row['NPA']}{row['NXX']}:{row['BLOCK_ID']}"
                yield key, {
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

    store.bulk_put(rows(), batch_size=batch)


def load_ocn(store: PhoneLookupStore, path: Path, batch: int = 5_000) -> None:
    """Load OCN data into LMDB records."""

    def rows() -> Iterable[tuple[str, dict[str, str]]]:
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                key = f"ocn:{row['OCN']}"
                yield key, {
                    "COMPANY": row.get("COMPANY", ""),
                    "DBA": row.get("DBA", ""),
                    "CommonName": row.get("CommonName", ""),
                    "TYPE": row.get("TYPE", ""),
                    "SMS": row.get("SMS", ""),
                    "Rural": row.get("Rural", ""),
                }

    store.bulk_put(rows(), batch_size=batch)


def import_all(store: PhoneLookupStore, npanxx_path: Path, ocn_path: Path) -> None:
    load_npanxx(store, npanxx_path)
    load_ocn(store, ocn_path)


def ensure_paths_exist(paths: Iterable[Path]) -> None:
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required data files: {', '.join(missing)}")
