import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "database.db"

def create_database():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id TEXT PRIMARY KEY,
                customer_id TEXT,
                amount REAL,
                merchant TEXT,
                city TEXT,
                device TEXT,
                timestamp TEXT
            )
        """)
    print("Database is ready at:", DB_PATH)
if __name__ == "__main__":
    create_database()