import pytest
from pathlib import Path
from unittest.mock import MagicMock, call
from phone_lookup import importer, database

@pytest.fixture
def mock_db_env(mocker):
    """Fixture to mock the LMDB environment."""
    db_env = MagicMock()
    txn = MagicMock()
    db_env.begin.return_value.__enter__.return_value = txn
    mocker.patch("phone_lookup.database.get_db", return_value=db_env)
    mocker.patch("phone_lookup.database.hset")
    return db_env

def test_load_npanxx(mock_db_env, tmp_path):
    """Test loading NPANXX data."""
    npanxx_file = tmp_path / "npanxx.csv"
    npanxx_file.write_text("NPA,NXX,BLOCK_ID,OCN,LTYPE\n212,456,A,1234,LANDLINE")

    importer.load_npanxx(mock_db_env, npanxx_file)

    expected_key = "npanxx:212456:A"
    expected_mapping = {
        "OCN": "1234",
        "LTYPE": "LANDLINE",
        "NXXTYPE": "",
        "RC": "",
        "RCLONG": "",
        "STATE": "",
        "COUNTRY": "",
        "LATA": "",
        "SWITCH": "",
        "TBP_IND": "",
        "ADATE": "",
        "EFFDATE": "",
    }

    database.hset.assert_called_once_with(mock_db_env.begin().__enter__(), expected_key, expected_mapping)

def test_load_ocn(mock_db_env, tmp_path):
    """Test loading OCN data."""
    ocn_file = tmp_path / "ocn.csv"
    ocn_file.write_text("OCN,COMPANY,CommonName\n1234,Test Company,Test Carrier")

    importer.load_ocn(mock_db_env, ocn_file)

    expected_key = "ocn:1234"
    expected_mapping = {
        "COMPANY": "Test Company",
        "DBA": "",
        "CommonName": "Test Carrier",
        "TYPE": "",
        "SMS": "",
        "Rural": "",
    }

    database.hset.assert_called_once_with(mock_db_env.begin().__enter__(), expected_key, expected_mapping)