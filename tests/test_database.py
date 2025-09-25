import lmdb
import pytest
from phone_lookup import database

@pytest.fixture
def db(tmp_path):
    """Fixture to create a temporary LMDB database for testing."""
    db_path = tmp_path / "test.lmdb"
    db = database.get_db(db_path)
    yield db
    db.close()
    database._ENV = None  # Reset the global environment

def test_hset_hgetall(db):
    """Test setting and getting a hash map."""
    key = "test_key"
    data = {"field1": "value1", "field2": "value2"}

    with db.begin(write=True) as txn:
        database.hset(txn, key, data)

    with db.begin() as txn:
        retrieved_data = database.hgetall(txn, key)

    assert retrieved_data == data

def test_hgetall_nonexistent_key(db):
    """Test getting a nonexistent key."""
    with db.begin() as txn:
        retrieved_data = database.hgetall(txn, "nonexistent_key")

    assert retrieved_data is None