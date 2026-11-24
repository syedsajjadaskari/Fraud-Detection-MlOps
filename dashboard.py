"""BankShield classroom MLOps operations dashboard (read-only)."""
from datetime import datetime, timezone
import sqlite3

import pandas as pd
import streamlit as st

from database import DB_PATH

st.set_page_config(page_title="BankShield | Fraud Operations", page_icon="🏦", layout="wide")
st.title("🏦 BankShield | Fraud Operations")
st.caption("Synthetic transactions • Classroom fraud model • SQLite-backed monitoring")

REQUIRED = {
    "transactions", "quarantined_transactions",
    "transaction_features", "fraud_predictions"
}


def read_sql(query, params=()):
    with sqlite3.connect(DB_PATH, timeout=5) as conn:
        return pd.read_sql_query(query, conn, params=params)


def check_tables():
    if not DB_PATH.exists():
        st.error(f"Database not found: {DB_PATH}. Run python3 database.py first.")
        st.stop()
    names = set(read_sql("SELECT name FROM sqlite_master WHERE type='table'")["name"])
    missing = REQUIRED - names
    if missing:
        st.error(f"Missing tables: {', '.join(sorted(missing))}. Complete Stages 3–5 and run database.py.")
        st.stop()


check_tables()

with st.sidebar:
    st.header("Dashboard controls")
    auto_refresh = st.toggle("Auto-refresh", value=True)
    st.caption("Updates every 5 seconds while this page is open")
    min_score = st.slider("Minimum score in alerts", 0.0, 1.0, 0.65, 0.05)
    max_rows = st.selectbox("Rows to display", [10, 25, 50, 100], index=1)
    if st.button("Refresh now"):
        st.rerun()
    st.divider()
    st.caption(f"Database: {DB_PATH}")


@st.fragment(run_every="5s" if auto_refresh else None)
def live_dashboard():
    overview = read_sql("""
        SELECT
          (SELECT COUNT(*) FROM transactions) AS accepted,
          (SELECT COUNT(*) FROM quarantined_transactions) AS rejected,
          (SELECT COUNT(*) FROM fraud_predictions) AS scored,
          (SELECT COUNT(*) FROM fraud_predictions WHERE is_suspicious = 1) AS alerts,
          (SELECT MAX(timestamp) FROM transactions) AS latest_event
    """).iloc[0]

    accepted, rejected = int(overview["accepted"]), int(overview["rejected"])
    scored, alerts = int(overview["scored"]), int(overview["alerts"])
    alert_rate = alerts / scored * 100 if scored else 0
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Accepted", f"{accepted:,}")
    c2.metric("Quarantined", f"{rejected:,}")
    c3.metric("Scored", f"{scored:,}")
    c4.metric("Flagged", f"{alerts:,}")
    c5.metric("Flag rate", f"{alert_rate:.1f}%")

    st.caption("Counts are lifetime totals. Flag rate = flagged / scored, not verified fraud rate.")
    latest = overview["latest_event"]
    if pd.isna(latest):
        st.info("No accepted transactions yet. Start ingestion.py in another terminal.")
    else:
        try:
            age = (datetime.now(timezone.utc) - datetime.fromisoformat(str(latest)).astimezone(timezone.utc)).total_seconds()
            if age > 30:
                st.warning(f"Latest transaction timestamp is {age:.0f} seconds old; ingestion may be idle.")
            elif age >= 0:
                st.success(f"Recent transaction timestamp: {str(latest)}")
            else:
                st.info("Most recent event timestamp is in the future; check simulated event times.")
        except ValueError:
            st.warning("Latest transaction timestamp could not be parsed.")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Activity", "🚨 Fraud alerts", "🧹 Data quality", "🤖 Models & features"
    ])

    with tab1:
        hourly = read_sql("""
            SELECT strftime('%Y-%m-%d %H:00', timestamp) AS hour,
                   COUNT(*) AS transactions
            FROM transactions
            GROUP BY strftime('%Y-%m-%d %H:00', timestamp)
            ORDER BY hour DESC LIMIT 24
        """)
        st.subheader("Transactions by UTC hour")
        if not hourly.empty:
            st.bar_chart(hourly.sort_values("hour").set_index("hour"))
        else:
            st.info("No transactions to chart yet.")
        recent = read_sql("""
            SELECT t.timestamp, t.customer_id, t.amount, t.merchant, t.city,
                   ROUND(p.fraud_score, 3) AS fraud_score,
                   p.is_suspicious
            FROM transactions t
            LEFT JOIN fraud_predictions p ON t.transaction_id = p.transaction_id
            ORDER BY t.timestamp DESC LIMIT ?
        """, (max_rows,))
        st.subheader("Latest accepted transactions")
        st.dataframe(recent, hide_index=True, width="stretch")

    with tab2:
        alerts_df = read_sql("""
            SELECT t.timestamp, t.customer_id, t.amount, t.city,
                   ROUND(p.fraud_score, 3) AS fraud_score,
                   p.model_version,
                   f.txn_count_5m, ROUND(f.amount_ratio, 2) AS amount_ratio,
                   f.city_changed
            FROM fraud_predictions p
            JOIN transactions t ON t.transaction_id = p.transaction_id
            LEFT JOIN transaction_features f ON f.transaction_id = t.transaction_id
            WHERE p.is_suspicious = 1 AND p.fraud_score >= ?
            ORDER BY p.predicted_at DESC LIMIT ?
        """, (min_score, max_rows))
        if alerts_df.empty:
            st.info("No alerts meet the selected score filter.")
        else:
            st.dataframe(alerts_df, hide_index=True, width="stretch")
        st.caption("An alert is a model-generated flag, not confirmed fraud.")

    with tab3:
        reasons = read_sql("""
            SELECT rejection_reason, COUNT(*) AS count
            FROM quarantined_transactions
            GROUP BY rejection_reason ORDER BY count DESC
        """)
        if not reasons.empty:
            st.subheader("Quarantine reasons")
            st.bar_chart(reasons.set_index("rejection_reason"))
        rejected_df = read_sql("""
            SELECT transaction_id, rejection_reason, rejected_at
            FROM quarantined_transactions ORDER BY id DESC LIMIT ?
        """, (max_rows,))
        st.subheader("Latest rejected attempts")
        st.dataframe(rejected_df, hide_index=True, width="stretch")
        if accepted + rejected:
            st.caption(f"Stored-row quarantine share: {rejected / (accepted + rejected) * 100:.1f}% (not a complete ingestion-attempt failure rate)")

    with tab4:
        models = read_sql("""
            SELECT model_version, COUNT(*) AS predictions,
                   ROUND(AVG(fraud_score), 3) AS avg_score,
                   SUM(is_suspicious) AS flagged
            FROM fraud_predictions GROUP BY model_version
            ORDER BY model_version
        """)
        st.subheader("Predictions by model version")
        st.dataframe(models, hide_index=True, width="stretch")
        st.metric("Accepted records without a prediction", max(0, accepted - scored))
        features = read_sql("""
            SELECT customer_id, amount, txn_count_5m,
                   amount_sum_1h, ROUND(amount_ratio, 2) AS amount_ratio,
                   city_changed, feature_timestamp
            FROM transaction_features
            ORDER BY feature_timestamp DESC LIMIT ?
        """, (max_rows,))
        st.subheader("Latest engineered features")
        st.dataframe(features, hide_index=True, width="stretch")

    st.caption(f"Dashboard refreshed (UTC): {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}")


live_dashboard()