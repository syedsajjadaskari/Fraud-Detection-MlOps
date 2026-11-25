import sqlite3
import pandas as pd

from pathlib import Path
from datetime import datetime, timezone

from database import DB_PATH

output_dir = Path("data/snapshots")
output_dir.mkdir(parents=True, exist_ok=True)

query = """
SELECT
    t.transaction_id,
    t.customer_id,
    t.timestamp,
    t.city,
    t.merchant,
    t.device,
    f.amount,
    f.txn_count_5m,
    f.amount_sum_1h,
    f.avg_prior_amount,
    f.amount_ratio,
    f.city_changed
FROM transactions t
JOIN transaction_features f
    ON t.transaction_id = f.transaction_id
ORDER BY t.timestamp, t.transaction_id
"""

with sqlite3.connect(DB_PATH) as conn:
    df = pd.read_sql_query(query, conn)

output_path = output_dir / "fraud_features.parquet"

df.to_parquet(
    output_path,
    engine="pyarrow",
    compression="snappy",
    index=False
)

print("snapshot exported sucefullly")
print("rows ",len(df))
print(df.head)