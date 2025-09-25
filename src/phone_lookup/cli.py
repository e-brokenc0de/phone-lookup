"""Command-line interface for phone lookup utilities."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Optional

from redis import ConnectionError, Redis

from .importer import ensure_paths_exist, import_all

DEFAULT_REDIS_HOST = "127.0.0.1"
DEFAULT_REDIS_PORT = 6379
DEFAULT_REDIS_DB = 0


@dataclass(frozen=True)
class LookupResult:
    """Container for lookup responses."""

    original: str
    normalized: Optional[str]
    ltype: str
    common_name: str
    found: bool

    def as_output_line(self) -> str:
        number = self.normalized or self.original
        return f"{number}:{self.ltype}:{self.common_name}"


def normalize_number(raw: str) -> Optional[str]:
    digits = "".join(ch for ch in raw if ch.isdigit())
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10:
        return None
    return digits


def load_numbers(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8") as handle:
        numbers = [line.strip() for line in handle if line.strip()]
    return numbers


def lookup_number(redis: Redis, digits: str) -> tuple[bool, str, str]:
    npa = digits[:3]
    nxx = digits[3:6]
    block = digits[6]
    candidates = (block, "A") if block != "A" else ("A",)
    for candidate in candidates:
        key = f"npanxx:{npa}{nxx}:{candidate}"
        data = redis.hgetall(key)
        if not data:
            continue
        ltype = data.get("LTYPE") or "UNKNOWN"
        ocn = data.get("OCN") or ""
        common_name = ""
        if ocn:
            ocn_key = f"ocn:{ocn}"
            ocn_data = redis.hgetall(ocn_key)
            if ocn_data:
                common_name = (
                    ocn_data.get("CommonName")
                    or ocn_data.get("DBA")
                    or ocn_data.get("COMPANY")
                    or ""
                )
        if not common_name:
            common_name = "UNKNOWN"
        return True, ltype or "UNKNOWN", common_name
    return False, "UNKNOWN", "UNKNOWN"


def run_lookup(redis: Redis, numbers: Iterable[str]) -> Iterator[LookupResult]:
    for number in numbers:
        normalized = normalize_number(number)
        if not normalized:
            yield LookupResult(number, None, "INVALID", "UNKNOWN", False)
            continue
        found, ltype, common_name = lookup_number(redis, normalized)
        yield LookupResult(number, normalized, ltype, common_name, found)


def add_redis_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--redis-host", default=DEFAULT_REDIS_HOST, help=argparse.SUPPRESS)
    parser.add_argument("--redis-port", type=int, default=DEFAULT_REDIS_PORT, help=argparse.SUPPRESS)
    parser.add_argument("--redis-db", type=int, default=DEFAULT_REDIS_DB, help=argparse.SUPPRESS)


def connect_redis(parser: argparse.ArgumentParser, *, host: str, port: int, db: int) -> Redis:
    try:
        redis_client = Redis(host=host, port=port, db=db, decode_responses=True)
        if not redis_client.ping():
            raise ConnectionError("Unable to ping Redis")
        return redis_client
    except ConnectionError as exc:
        parser.error(f"Could not connect to Redis: {exc}")
        raise  # unreachable but keeps type checkers happy


def handle_lookup(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    numbers = load_numbers(args.file)
    if not numbers:
        parser.error("Input file did not contain any phone numbers")
    redis_client = connect_redis(parser, host=args.redis_host, port=args.redis_port, db=args.redis_db)
    results = list(run_lookup(redis_client, numbers))
    total = len(results)
    with args.output.open("w", encoding="utf-8") as handle:
        for idx, result in enumerate(results, start=1):
            number_display = result.normalized or result.original
            print(f"{idx}/{total} {number_display} {result.ltype} {result.common_name}")
            handle.write(result.as_output_line() + "\n")
    return 0


def handle_import(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    ensure_paths_exist((args.npanxx_path, args.ocn_path))
    redis_client = connect_redis(parser, host=args.redis_host, port=args.redis_port, db=args.redis_db)
    import_all(redis_client, args.npanxx_path, args.ocn_path)
    print("Import complete.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Phone lookup tooling")
    subparsers = parser.add_subparsers(dest="command", required=True)

    lookup_parser = subparsers.add_parser("lookup", help="Perform bulk phone number lookups")
    add_redis_arguments(lookup_parser)
    lookup_parser.add_argument("--file", required=True, type=Path, help="Path to input file containing phone numbers")
    lookup_parser.add_argument("--output", required=True, type=Path, help="File to write lookup results")

    import_parser = subparsers.add_parser("import", help="Import NPANXX/OCN data into Redis")
    add_redis_arguments(import_parser)
    import_parser.add_argument(
        "--npanxx-path",
        type=Path,
        default=Path("data/raw/phoneplatinumwire.csv"),
        help="Path to NPANXX CSV file",
    )
    import_parser.add_argument(
        "--ocn-path",
        type=Path,
        default=Path("data/raw/ocn.csv"),
        help="Path to OCN CSV file",
    )

    return parser


def run(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "lookup":
        return handle_lookup(parser, args)
    if args.command == "import":
        return handle_import(parser, args)
    parser.error("A command is required")
    return 2


if __name__ == "__main__":
    raise SystemExit(run())
