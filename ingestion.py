
import sqlite3
import json
import time
from datetime import datetime, timezone

from database import DB_PATH, create_database
from transaction_generator import generate_transaction
from validator import validate_transaction
from feature_engineering import calculate_features
from fraud_predictor import predict_fraud


# ----------------------------------------
# 1. QUARANTINE INVALID TRANSACTIONS
# ----------------------------------------

def quarantine(conn, transaction, reasons):

    conn.execute("""
        INSERT INTO quarantined_transactions
        (
            transaction_id,
            raw_data,
            rejection_reason,
            rejected_at
        )
        VALUES (?, ?, ?, ?)
    """, (
        str(transaction.get("transaction_id", "")),
        json.dumps(transaction, default=str),
        "; ".join(reasons),
        datetime.now(timezone.utc).isoformat()
    ))


# ----------------------------------------
# 2. PROCESS EACH TRANSACTION
# ----------------------------------------

def process_transaction(transaction):

    # STEP 1: Validate incoming transaction
    is_valid, errors = validate_transaction(transaction)

    with sqlite3.connect(DB_PATH, timeout=10) as conn:

        # STEP 2: Quarantine invalid data
        if not is_valid:
            quarantine(conn, transaction, errors)

            print(
                f"REJECTED | "
                f"Transaction: {transaction.get('transaction_id')} | "
                f"Reason: {errors}",
                flush=True
            )

            return "REJECTED"

        # STEP 3: Generate features, predict,
        # and store the results atomically.
        try:
            conn.execute("SAVEPOINT insert_transaction")

            # Calculate behavioural features
            # using previous customer transactions.
            features = calculate_features(conn, transaction)

            # Predict fraud risk using trained model.
            prediction = predict_fraud(features)

            # STEP 4: Save accepted transaction
            conn.execute("""
                INSERT INTO transactions
                (
                    transaction_id,
                    customer_id,
                    amount,
                    merchant,
                    city,
                    device,
                    timestamp
                )
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

            # STEP 5: Save engineered features
            conn.execute("""
                INSERT INTO transaction_features
                (
                    transaction_id,
                    customer_id,
                    amount,
                    txn_count_5m,
                    amount_sum_1h,
                    avg_prior_amount,
                    amount_ratio,
                    city_changed,
                    feature_timestamp
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                features["transaction_id"],
                features["customer_id"],
                features["amount"],
                features["txn_count_5m"],
                features["amount_sum_1h"],
                features["avg_prior_amount"],
                features["amount_ratio"],
                features["city_changed"],
                features["feature_timestamp"]
            ))

            # STEP 6: Save model prediction
            conn.execute("""
                INSERT INTO fraud_predictions
                (
                    transaction_id,
                    fraud_score,
                    is_suspicious,
                    model_version,
                    predicted_at
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                transaction["transaction_id"],
                prediction["fraud_score"],
                prediction["is_suspicious"],
                prediction["model_version"],
                datetime.now(timezone.utc).isoformat()
            ))

            conn.execute("RELEASE SAVEPOINT insert_transaction")

        except sqlite3.IntegrityError as error:

            conn.execute("ROLLBACK TO SAVEPOINT insert_transaction")
            conn.execute("RELEASE SAVEPOINT insert_transaction")

            # Only classify confirmed transaction ID
            # collisions as duplicates.
            existing = conn.execute("""
                SELECT 1 FROM transactions
                WHERE transaction_id = ?
            """, (
                transaction["transaction_id"],
            )).fetchone()

            if existing is None:
                raise

            quarantine(
                conn,
                transaction,
                ["Duplicate transaction ID"]
            )

            print(
                f"DUPLICATE | "
                f"Transaction: {transaction['transaction_id']}",
                flush=True
            )

            return "DUPLICATE"

    # STEP 7: Display successful prediction
    score = prediction["fraud_score"]

    status = (
        "SUSPICIOUS"
        if prediction["is_suspicious"] == 1
        else "NORMAL"
    )

    print(
        f"{status} | "
        f"Customer: {transaction['customer_id']} | "
        f"Amount: ₹{transaction['amount']:.2f} | "
        f"Fraud Score: {score:.3f} | "
        f"Model: {prediction['model_version']}",
        flush=True
    )

    return "ACCEPTED"


# ----------------------------------------
# 3. START LIVE INGESTION SERVICE
# ----------------------------------------

def main():

    # Ensure required SQLite tables exist.
    create_database()

    # Ensure model exists before accepting events.
    from fraud_predictor import load_model
    load_model()

    print("=" * 65)
    print("BANKING FRAUD DETECTION - LIVE MLOPS PIPELINE")
    print("=" * 65)

    print("Transaction Generator : ACTIVE")
    print("Data Validation       : ACTIVE")
    print("Feature Engineering   : ACTIVE")
    print("Fraud Prediction      : ACTIVE")
    print("SQLite Storage        : ACTIVE")
    print("Dashboard             : Run separately")
    print("-" * 65)

    try:
        while True:

            transaction = generate_transaction()

            process_transaction(transaction)

            time.sleep(2)

    except KeyboardInterrupt:
        print("\nIngestion service stopped by user.")


if __name__ == "__main__":
    main()
