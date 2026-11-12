
import sqlite3
import json
import time
from datetime import datetime, timezone

from database import DB_PATH, create_database
from transaction_generator import generate_transaction
from validator import validate_transaction


def quarantine(conn, transaction, reasons):

    conn.execute("""
        INSERT INTO quarantine_transactions
        (transaction_id, raw_data, rejection_reason, rejected_at)
        VALUES (?, ?, ?, ?)
    """, (
        str(transaction.get("transaction_id", "")),
        json.dumps(transaction, default=str),
        "; ".join(reasons),
        datetime.now(timezone.utc).isoformat()
    ))


def process_transaction(transaction):

    is_valid, errors = validate_transaction(transaction)

    with sqlite3.connect(DB_PATH) as conn:

        if not is_valid:
            quarantine(conn, transaction, errors)
            print("REJECTED:", errors)
            return "REJECTED"

        try:
            # SAVEPOINT allows us to recover from a
            # duplicate without losing the quarantine insert.
            conn.execute("SAVEPOINT insert_transaction")

            conn.execute("""
                INSERT INTO transactions
                (transaction_id, customer_id, amount,
                 merchant, city, device, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                transaction["transaction_id"],
                transaction["customer_id"],
                transaction["amount"],
                transaction["merchant"],
                transaction["city"],
                transaction["device"],
                transaction["timestamp"]
            ))

            conn.execute("RELEASE SAVEPOINT insert_transaction")

        except sqlite3.IntegrityError:
            conn.execute("ROLLBACK TO SAVEPOINT insert_transaction")
            conn.execute("RELEASE SAVEPOINT insert_transaction")

            quarantine(
                conn,
                transaction,
                ["Duplicate transaction ID"]
            )

            print("DUPLICATE:", transaction["transaction_id"])
            return "DUPLICATE"

    print(
        f"ACCEPTED: {transaction['customer_id']} "
        f"| ₹{transaction['amount']:.2f}"
    )

    return "ACCEPTED"


if __name__ == "__main__":

    create_database()

    print("Data quality ingestion service started")

    try:
        while True:
            transaction = generate_transaction()
            process_transaction(transaction)
            time.sleep(2)

    except KeyboardInterrupt:
        print("\nIngestion service stopped")
