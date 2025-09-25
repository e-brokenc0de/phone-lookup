from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from phone_lookup.store import PhoneLookupStore


class PhoneLookupStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.store = PhoneLookupStore.open(Path(self._tmp.name))

    def tearDown(self) -> None:
        self.store.close()
        self._tmp.cleanup()

    def test_put_and_get_mapping_roundtrip(self) -> None:
        key = "ocn:4321"
        mapping = {"OCN": "4321", "CommonName": "Test Carrier"}
        self.store.put_mapping(key, mapping)

        retrieved = self.store.get_mapping(key)
        self.assertEqual(retrieved, mapping)
        self.assertEqual(self.store.get_mapping("missing:key"), {})

    def test_bulk_put_with_batches(self) -> None:
        items = [(f"npanxx:55500{i}:{i}", {"OCN": f"{i:04d}"}) for i in range(15)]

        self.store.bulk_put(items, batch_size=4)

        for key, mapping in items:
            self.assertEqual(self.store.get_mapping(key), mapping)

    def test_bulk_put_requires_positive_batch_size(self) -> None:
        with self.assertRaises(ValueError):
            self.store.bulk_put([], batch_size=0)

    def test_iterate_keys_returns_all_inserted_entries(self) -> None:
        items = {f"npanxx:0000{i}:A": {"OCN": str(i)} for i in range(5)}
        for key, mapping in items.items():
            self.store.put_mapping(key, mapping)

        returned_keys = set(self.store.iterate_keys())
        self.assertEqual(returned_keys, set(items))


if __name__ == "__main__":  # pragma: no cover - convenience
    unittest.main()
