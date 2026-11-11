import sqlite3
import time

from database import DB_PATH, create_database
from transaction_generator import generate_transaction

create_database()
while True:
    transaction = generate_transaction()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO transactions
            (transaction_id, customer_id, amount, merchant,
            city, device, timestamp) VALUES (?,?,?,?,?,?,?)""", 
            (transaction["transaction_id"],transaction["customer_id"],
            transaction["amount"],transaction["merchant"],
            transaction["city"],transaction["device"],
            transaction["timestamp"]
            ))
    print(f"saved {transaction['customer_id']}",
          f"| amount {transaction['amount']}.2f",
          f"| Merchant{transaction['merchant']}", flush=True)

    time.sleep(2)