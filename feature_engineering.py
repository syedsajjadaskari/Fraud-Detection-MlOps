
from datetime import datetime, timedelta, timezone


def calculate_features(conn, transaction):

    customer_id = transaction["customer_id"]
    current_time = datetime.fromisoformat(
        transaction["timestamp"]
    ).astimezone(timezone.utc)

    five_minutes_ago = current_time - timedelta(minutes=5)
    one_hour_ago = current_time - timedelta(hours=1)

    # Fetch previous customer transactions
    # within the last hour.
    rows = conn.execute("""
        SELECT amount, city, timestamp
        FROM transactions
        WHERE customer_id = ?
          AND julianday(timestamp) >= julianday(?)
          AND julianday(timestamp) < julianday(?)
        ORDER BY julianday(timestamp), transaction_id
    """, (
        customer_id,
        one_hour_ago.isoformat(),
        current_time.isoformat()
    )).fetchall()

    # 1. Transaction count in previous 5 minutes
    txn_count_5m = sum(
        1 for amount, city, timestamp in rows
        if datetime.fromisoformat(timestamp).astimezone(
            timezone.utc
        ) >= five_minutes_ago
    )

    # 2. Total spending in previous hour
    amount_sum_1h = sum(
        amount for amount, city, timestamp in rows
    )

    # Fetch all earlier customer amounts
    # for historical average.
    history = conn.execute("""
        SELECT AVG(amount)
        FROM transactions
        WHERE customer_id = ?
          AND julianday(timestamp) < julianday(?)
    """, (
        customer_id,
        current_time.isoformat()
    )).fetchone()

    avg_prior_amount = history[0]

    # 3. Amount compared with historical average
    amount_ratio = (
        transaction["amount"] / avg_prior_amount
        if avg_prior_amount is not None
        and avg_prior_amount > 0
        else None
    )

    # 4. Find the customer's last known city
    last_record = conn.execute("""
        SELECT city
        FROM transactions
        WHERE customer_id = ?
          AND julianday(timestamp) < julianday(?)
        ORDER BY julianday(timestamp) DESC,
                 transaction_id DESC
        LIMIT 1
    """, (
        customer_id,
        current_time.isoformat()
    )).fetchone()

    city_changed = (
        int(last_record[0] != transaction["city"])
        if last_record is not None
        else 0
    )

    return {
        "transaction_id": transaction["transaction_id"],
        "customer_id": customer_id,
        "amount": transaction["amount"],
        "txn_count_5m": txn_count_5m,
        "amount_sum_1h": round(amount_sum_1h, 2),
        "avg_prior_amount": avg_prior_amount,
        "amount_ratio": amount_ratio,
        "city_changed": city_changed,
        "feature_timestamp": current_time.isoformat()
    }
