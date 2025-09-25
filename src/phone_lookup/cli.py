"""Command-line interface for phone lookup utilities."""
from __future__ import annotations

import argparse
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator, Optional

from termcolor import colored

from .importer import ensure_paths_exist, import_all
from .store import DEFAULT_MAP_SIZE, PhoneLookupStore

DEFAULT_DB_PATH = Path(os.getenv("PHONE_LOOKUP_DB_PATH", "data/store"))

ENABLE_COLOR = os.getenv("NO_COLOR") is None and (bool(os.getenv("FORCE_COLOR")) or sys.stdout.isatty())

LINE_TYPE_LABELS = {
    "S": "LANDLINE",
    "C": "WIRELESS",
    "P": "PAGING",
    "M": "MIXED",
    "V": "VOIP",
}


def colorize(text: str, *args: Any, **kwargs: Any) -> str:
    if ENABLE_COLOR:
        return colored(text, *args, **kwargs)
    return text


def format_line_type(ltype: str) -> str:
    label = LINE_TYPE_LABELS.get(ltype.upper()) if ltype else None
    return label if label else ltype

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
        return f"{number}:{format_line_type(self.ltype)}:{self.common_name}"


def format_lookup_output(idx: int, total: int, result: LookupResult) -> str:
    number_display = result.normalized or result.original
    progress = colorize(f"{idx}/{total}", "cyan")
    if result.found:
        number = colorize(number_display, "green", attrs=["bold"])
        ltype = colorize(format_line_type(result.ltype), "green")
        common_name = colorize(result.common_name, "white")
    elif result.ltype == "INVALID":
        number = colorize(number_display, "red", attrs=["bold"])
        ltype = colorize(result.ltype, "red", attrs=["bold"])
        common_name = colorize(result.common_name, "red")
    else:
        number = colorize(number_display, "yellow", attrs=["bold"])
        ltype = colorize(format_line_type(result.ltype), "yellow")
        common_name = colorize(result.common_name, "yellow")
    return f"{progress} {number} {ltype} {common_name}"


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


def lookup_number(store: PhoneLookupStore, digits: str) -> tuple[bool, str, str]:
    npa = digits[:3]
    nxx = digits[3:6]
    block = digits[6]
    candidates = (block, "A") if block != "A" else ("A",)
    for candidate in candidates:
        key = f"npanxx:{npa}{nxx}:{candidate}"
        data = store.get_mapping(key)
        if not data:
            continue
        ltype = data.get("LTYPE") or "UNKNOWN"
        ocn = data.get("OCN") or ""
        common_name = ""
        if ocn:
            ocn_key = f"ocn:{ocn}"
            ocn_data = store.get_mapping(ocn_key)
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


def run_lookup(store: PhoneLookupStore, numbers: Iterable[str]) -> Iterator[LookupResult]:
    for number in numbers:
        normalized = normalize_number(number)
        if not normalized:
            yield LookupResult(number, None, "INVALID", "UNKNOWN", False)
            continue
        found, ltype, common_name = lookup_number(store, normalized)
        yield LookupResult(number, normalized, ltype, common_name, found)


def add_store_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--database-path",
        type=Path,
        default=DEFAULT_DB_PATH,
        help="Path to the LMDB environment directory (default: %(default)s)",
    )


def open_store(parser: argparse.ArgumentParser, *, path: Path) -> PhoneLookupStore:
    try:
        return PhoneLookupStore.open(path, map_size=DEFAULT_MAP_SIZE)
    except Exception as exc:  # pragma: no cover - defensive
        parser.error(f"Could not open LMDB database at {path}: {exc}")
        raise


def handle_lookup(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    numbers = load_numbers(args.file)
    if not numbers:
        parser.error("Input file did not contain any phone numbers")
    total = len(numbers)
    start = time.monotonic()
    with open_store(parser, path=args.database_path) as store:
        with args.output.open("w", encoding="utf-8") as handle:
            for idx, result in enumerate(run_lookup(store, numbers), start=1):
                print(format_lookup_output(idx, total, result), flush=True)
                handle.write(result.as_output_line() + "\n")
    elapsed = time.monotonic() - start
    completion_line = colorize(
        f"Completed {total} lookups in {elapsed:.2f} seconds.",
        "green",
        attrs=["bold"],
    )
    print(f"\n{completion_line}\n", flush=True)
    return 0


def handle_import(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    ensure_paths_exist((args.npanxx_path, args.ocn_path))
    with open_store(parser, path=args.database_path) as store:
        import_all(store, args.npanxx_path, args.ocn_path)
    print(colorize("Import complete.", "green", attrs=["bold"]))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Phone lookup tooling")
    subparsers = parser.add_subparsers(dest="command", required=True)

    lookup_parser = subparsers.add_parser("lookup", help="Perform bulk phone number lookups")
    add_store_arguments(lookup_parser)
    lookup_parser.add_argument("--file", required=True, type=Path, help="Path to input file containing phone numbers")
    lookup_parser.add_argument("--output", required=True, type=Path, help="File to write lookup results")

    import_parser = subparsers.add_parser("import", help="Import NPANXX/OCN data into the LMDB store")
    add_store_arguments(import_parser)
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
