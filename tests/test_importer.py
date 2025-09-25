from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from phone_lookup.importer import ensure_paths_exist, import_all, load_npanxx, load_ocn
from phone_lookup.store import PhoneLookupStore


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


class ImporterTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self._tmp_dir.name) / "db"
        self.store = PhoneLookupStore.open(self.db_path)

    def tearDown(self) -> None:
        self.store.close()
        self._tmp_dir.cleanup()

    def test_load_npanxx_imports_rows(self) -> None:
        csv_path = Path(self._tmp_dir.name) / "npanxx.csv"
        write_csv(
            csv_path,
            [
                "NPA",
                "NXX",
                "BLOCK_ID",
                "OCN",
                "LTYPE",
                "NXXTYPE",
                "RC",
                "RCLONG",
                "STATE",
                "COUNTRY",
                "LATA",
                "SWITCH",
                "TBP_IND",
                "ADATE",
                "EFFDATE",
            ],
            [
                {
                    "NPA": "415",
                    "NXX": "555",
                    "BLOCK_ID": "1",
                    "OCN": "9999",
                    "LTYPE": "C",
                    "NXXTYPE": "",  # optional field
                    "RC": "SF",
                    "RCLONG": "San Francisco",
                    "STATE": "CA",
                    "COUNTRY": "USA",
                    "LATA": "722",
                    "SWITCH": "SFTCCA",
                    "TBP_IND": "N",
                    "ADATE": "2023-01-01",
                    "EFFDATE": "2023-02-01",
                }
            ],
        )

        load_npanxx(self.store, csv_path, batch=2)

        key = "npanxx:415555:1"
        stored = self.store.get_mapping(key)
        self.assertEqual(stored.get("OCN"), "9999")
        self.assertEqual(stored.get("LTYPE"), "C")
        self.assertEqual(stored.get("RCLONG"), "San Francisco")

    def test_load_ocn_imports_rows(self) -> None:
        csv_path = Path(self._tmp_dir.name) / "ocn.csv"
        write_csv(
            csv_path,
            ["OCN", "COMPANY", "DBA", "CommonName", "TYPE", "SMS", "Rural"],
            [
                {
                    "OCN": "1234",
                    "COMPANY": "Carrier Inc.",
                    "DBA": "Carrier",
                    "CommonName": "Carrier",
                    "TYPE": "CLEC",
                    "SMS": "Y",
                    "Rural": "N",
                }
            ],
        )

        load_ocn(self.store, csv_path, batch=1)

        stored = self.store.get_mapping("ocn:1234")
        self.assertEqual(stored.get("COMPANY"), "Carrier Inc.")
        self.assertEqual(stored.get("CommonName"), "Carrier")

    def test_import_all_invokes_both_loaders(self) -> None:
        npanxx_path = Path(self._tmp_dir.name) / "npanxx_all.csv"
        ocn_path = Path(self._tmp_dir.name) / "ocn_all.csv"
        write_csv(
            npanxx_path,
            ["NPA", "NXX", "BLOCK_ID", "OCN", "LTYPE", "NXXTYPE", "RC", "RCLONG", "STATE", "COUNTRY", "LATA", "SWITCH", "TBP_IND", "ADATE", "EFFDATE"],
            [
                {
                    "NPA": "212",
                    "NXX": "555",
                    "BLOCK_ID": "A",
                    "OCN": "5678",
                    "LTYPE": "S",
                    "NXXTYPE": "",
                    "RC": "NYC",
                    "RCLONG": "New York",
                    "STATE": "NY",
                    "COUNTRY": "USA",
                    "LATA": "132",
                    "SWITCH": "NYNYNY",
                    "TBP_IND": "Y",
                    "ADATE": "2022-03-01",
                    "EFFDATE": "2022-04-01",
                }
            ],
        )
        write_csv(
            ocn_path,
            ["OCN", "COMPANY", "DBA", "CommonName", "TYPE", "SMS", "Rural"],
            [
                {
                    "OCN": "5678",
                    "COMPANY": "City Tel",
                    "DBA": "City Tel",
                    "CommonName": "City Tel",
                    "TYPE": "ILEC",
                    "SMS": "N",
                    "Rural": "N",
                }
            ],
        )

        import_all(self.store, npanxx_path, ocn_path)

        self.assertTrue(self.store.get_mapping("npanxx:212555:A"))
        self.assertTrue(self.store.get_mapping("ocn:5678"))

    def test_ensure_paths_exist_raises_for_missing_files(self) -> None:
        missing_path = Path(self._tmp_dir.name) / "missing.csv"
        with self.assertRaises(FileNotFoundError):
            ensure_paths_exist([missing_path])


if __name__ == "__main__":  # pragma: no cover - convenience
    unittest.main()
