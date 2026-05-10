import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Union, Optional

def get_db_path() -> Path:
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir / "accent-trainer.db"

def init_db(db_path: Optional[Union[str, Path]] = None) -> None:
    if db_path is None:
        db_path = get_db_path()

    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            voice_preference TEXT DEFAULT 'female',
            onboarding_mode TEXT DEFAULT 'full',
            diagnostic_completed BOOLEAN DEFAULT FALSE
        );

        CREATE TABLE IF NOT EXISTS phoneme_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            phoneme TEXT NOT NULL,
            score REAL NOT NULL,
            sample_count INTEGER DEFAULT 1,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, phoneme)
        );

        CREATE TABLE IF NOT EXISTS practice_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            phrase_id INTEGER NOT NULL,
            level INTEGER NOT NULL,
            score REAL NOT NULL,
            word_scores TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS level_progress (
            user_id TEXT NOT NULL,
            level INTEGER NOT NULL,
            completed BOOLEAN DEFAULT FALSE,
            avg_score REAL DEFAULT 0,
            phrases_practiced INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, level),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)
    conn.commit()
    conn.close()

@contextmanager
def get_connection(db_path: Optional[Union[str, Path]] = None):
    if db_path is None:
        db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
