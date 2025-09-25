import pytest
from pathlib import Path
from unittest.mock import MagicMock
from phone_lookup import cli

@pytest.fixture
def mock_db(mocker):
    """Fixture to mock the database."""
    return mocker.patch("phone_lookup.database.get_db")

def test_handle_lookup(mocker, tmp_path):
    """Test the lookup command."""
    mock_db_env = MagicMock()
    mock_txn = MagicMock()
    mock_db_env.begin.return_value.__enter__.return_value = mock_txn

    mocker.patch("phone_lookup.database.get_db", return_value=mock_db_env)
    mocker.patch("phone_lookup.cli.lookup_number", side_effect=[
        (True, "LANDLINE", "Test Carrier"),
        (False, "UNKNOWN", "UNKNOWN"),
    ])

    input_file = tmp_path / "numbers.txt"
    output_file = tmp_path / "results.txt"
    input_file.write_text("1234567890\n0987654321")

    parser = cli.build_parser()
    args = parser.parse_args(["lookup", "--file", str(input_file), "--output", str(output_file)])

    cli.handle_lookup(parser, args)

    output_content = output_file.read_text()
    assert "1234567890:LANDLINE:Test Carrier" in output_content
    assert "0987654321:UNKNOWN:UNKNOWN" in output_content

def test_normalize_number():
    """Test phone number normalization."""
    assert cli.normalize_number("1234567890") == "1234567890"
    assert cli.normalize_number("11234567890") == "1234567890"
    assert cli.normalize_number("123-456-7890") == "1234567890"
    assert cli.normalize_number("12345") is None