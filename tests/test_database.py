import pytest
import os
import tempfile
from database import init_db, get_db_path, get_connection

@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    os.unlink(path)

def test_init_db_creates_tables(temp_db):
    init_db(temp_db)
    import sqlite3
    conn = sqlite3.connect(temp_db)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    conn.close()
    assert "users" in tables
    assert "phoneme_scores" in tables
    assert "practice_history" in tables
    assert "level_progress" in tables

def test_get_db_path_returns_data_directory():
    path = get_db_path()
    assert "data" in str(path)
    assert path.name == "accent-trainer.db"
