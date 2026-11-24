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
        #create quarantine table to store rejected transactions
        conn.execute("""
            CREATE TABLE IF NOT EXISTS quarantine_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT,
                raw_data TEXT,
                rejection_reason TEXT NOT NULL,
                rejected_at TEXT NOT NULL)""")

        feature_columns = conn.execute(
            "PRAGMA table_info(transaction_features)"
        ).fetchall()
        expected_columns = {
            "transaction_id",
            "customer_id",
            "amount",
            "txn_count_5m",
            "amount_sum_1h",
            "avg_prior_amount",
            "amount_ratio",
            "city_changed",
            "feature_timestamp",
        }
        existing_columns = {row[1] for row in feature_columns}

        if feature_columns and existing_columns != expected_columns:
            conn.execute("DROP TABLE transaction_features")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS transaction_features (
                transaction_id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL,
                amount REAL NOT NULL,
                txn_count_5m INTEGER NOT NULL,
                amount_sum_1h REAL NOT NULL,
                avg_prior_amount REAL,
                amount_ratio REAL,
                city_changed INTEGER NOT NULL,
                feature_timestamp TEXT NOT NULL,
                FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS fraud_predictions (
                transaction_id TEXT PRIMARY KEY,
                fraud_score REAL NOT NULL,
                is_suspicious INTEGER NOT NULL,
                model_version TEXT NOT NULL,
                predicted_at TEXT NOT NULL,
                FOREIGN KEY (transaction_id)
                    REFERENCES transactions(transaction_id)
            )
        """)


    print("Database and quarantine tables are ready at:", DB_PATH)


if __name__ == "__main__":
    create_database()