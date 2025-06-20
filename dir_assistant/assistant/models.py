import sqlite3

def create_prompt_history_table(conn: sqlite3.Connection):
    """Creates the prompt_history table if it doesn't exist."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prompt_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt TEXT NOT NULL,
            artifacts_json TEXT NOT NULL,
            timestamp REAL NOT NULL
        )
    """)

