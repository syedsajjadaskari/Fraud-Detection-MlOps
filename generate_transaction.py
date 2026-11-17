import numpy as np
import pandas as pd
from pathlib import Path

rng = np.random.default_rng(42)

n = 10000

#generate synthetic data for transactions
amount = rng.uniform(100, 50000, n)

txn_count_5m = rng.poisson(5,n)
amount_sum_1h = rng.uniform(0, 120000, n)

amount_ratio = rng.lognormal(mean = 0.5, sigma = 1, size = n)

city_changed = rng.binomial(1, 0.2, n)

#simulate hidden realionship between features and target variable
risk = (
    -4.0 
    + 0.75 * (txn_count_5m >= 3)
    +1.3 * (amount_ratio > 5)
    +1.1 * (amount_ratio > 15)
     + 0.5 * city_changed
     + 0.5 * (amount > 25000)
     + 0.5 * (amount_sum_1h > 40000)
)

fraud_probability = 1 / (1+ np.exp(-risk))

fraud_label = rng.binomial(1, fraud_probability)

df = pd.DataFrame(
    {
        "amount": amount,
        "txn_count_5m": txn_count_5m,
        "amount_sum_1h": amount_sum_1h,
        "amount_ratio": amount_ratio,
        "city_changed": city_changed,
        "is_fraud": fraud_label
    }
)

Path("data").mkdir(exist_ok=True)
df.to_csv("data/transaction.csv", index=False)

print("data created successfully")
print("Total records:", len(df))
print("Fraud records distribution")
print(df["is_fraud"].value_counts(normalize=True))
print("Sample of the data created")
print(df.head())