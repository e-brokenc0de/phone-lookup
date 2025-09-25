"""Simple benchmarking helpers for the LMDB-backed store."""
from __future__ import annotations

import argparse
import random
import string
import tempfile
import time
from pathlib import Path

from phone_lookup.store import PhoneLookupStore


def random_mapping(index: int) -> dict[str, str]:
    ocn = f"{index % 10000:04d}"
    return {
        "OCN": ocn,
        "LTYPE": random.choice(["C", "S", "V", "P"]),
        "RCLONG": "".join(random.choices(string.ascii_uppercase, k=12)),
    }


def generate_items(count: int) -> list[tuple[str, dict[str, str]]]:
    return [
        (f"npanxx:{i:03d}{(i + 1) % 1000:03d}:{i % 10}", random_mapping(i))
        for i in range(count)
    ]


def bulk_insert(store: PhoneLookupStore, items: list[tuple[str, dict[str, str]]], batch_size: int) -> float:
    start = time.perf_counter()
    store.bulk_put(items, batch_size=batch_size)
    return time.perf_counter() - start


def random_reads(store: PhoneLookupStore, keys: list[str], samples: int) -> float:
    start = time.perf_counter()
    for _ in range(samples):
        key = random.choice(keys)
        store.get_mapping(key)
    return time.perf_counter() - start


def run_benchmark(count: int, batch_size: int, samples: int, db_path: Path | None) -> None:
    temp_dir: tempfile.TemporaryDirectory[str] | None = None
    if db_path is None:
        temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(temp_dir.name) / "bench-db"

    store = PhoneLookupStore.open(db_path)
    try:
        items = generate_items(count)
        insert_time = bulk_insert(store, items, batch_size)
        read_time = random_reads(store, [key for key, _ in items], samples)

        print("Benchmark results")
        print("-----------------")
        print(f"Bulk insert of {count} records (batch_size={batch_size}): {insert_time:.3f}s")
        print(f"Random reads ({samples} samples): {read_time:.3f}s")
    finally:
        store.close()
        if temp_dir is not None:
            temp_dir.cleanup()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark the LMDB-backed phone lookup store")
    parser.add_argument("--count", type=int, default=10000, help="Number of records to insert")
    parser.add_argument("--batch-size", type=int, default=1000, help="Batch size for bulk inserts")
    parser.add_argument("--samples", type=int, default=5000, help="Number of random reads to perform")
    parser.add_argument("--db-path", type=Path, default=None, help="Optional path to reuse an existing LMDB directory")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_benchmark(args.count, args.batch_size, args.samples, args.db_path)


if __name__ == "__main__":
    main()
