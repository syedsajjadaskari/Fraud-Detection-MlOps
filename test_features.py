
import uuid
import sqlite3
from datetime import datetime, timedelta, timezone

from database import DB_PATH, create_database
from ingestion import process_transaction

create_database()

# A new customer for each test run
customer_id = "DEMO_" + uuid.uuid4().hex[:8]

base_time = datetime.now(timezone.utc)

test_data = [
    (-4, 500, "Bengaluru"),
    (-2, 1000, "Bengaluru"),
    (-1, 1500, "Bengaluru"),
    (0, 40000, "Mumbai")
]

for minutes, amount, city in test_data:

    transaction = {
        "transaction_id": str(uuid.uuid4()),
        "customer_id": customer_id,
        "amount": amount,
        "merchant": "Amazon",
        "city": city,
        "device": "Mobile",
        "timestamp": (
            base_time + timedelta(minutes=minutes)
        ).isoformat()
    }

    process_transaction(transaction)


# Show the engineered features
with sqlite3.connect(DB_PATH) as conn:

    rows = conn.execute("""
        SELECT
            amount,
            txn_count_5m,
            amount_sum_1h,
            ROUND(amount_ratio, 2),
            city_changed
        FROM transaction_features
        WHERE customer_id = ?
        ORDER BY feature_timestamp
    """, (customer_id,)).fetchall()

print("\nFEATURE RESULTS")

for row in rows:
    print(row)
