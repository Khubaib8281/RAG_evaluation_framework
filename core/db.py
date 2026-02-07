import sqlite3
from pathlib import Path

DB_PATH = Path("data/logs.db")

def get_connection():
    DB_PATH.parent.mkdir(exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        query TEXT,
        answer TEXT,
        latency_ms REAL,
        tokens_used INTGER,
        provider TEXT,
        confidence REAL,
        hallucination INTEGER
    )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS errors(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            error_message TEXT
            )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cache(
            query_hash TEXT PRIMARY KEY,
            answer TEXT NOT NULL,
            top_chunks TEXT,
            timestamp TEXT NOT NULL
    )
    """)
    
    conn.commit()
    conn.close()