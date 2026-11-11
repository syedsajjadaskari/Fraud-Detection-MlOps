import sqlite3
import pandas as pd
from database import DB_PATH

with sqlite3.connect(DB_PATH) as conn:
    df = pd.read_sql_query("" \
    "SELECT * FROM transactions ORDER BY timestamp DESC", conn)

print(df.head(10))