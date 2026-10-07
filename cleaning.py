"""MEMBER 2 owns this file.
Turns the messy CSVs into clean tables AND a log (notes) of everything that was fixed or flagged.
Rule: NEVER guess. If something cannot be resolved, flag it and leave it empty.
"""
import re
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


# ---------------------------------------------------------------- dates
def parse_date(value):
    """Return (Timestamp-or-NaT, is_ambiguous).
    2025-03-04  -> clear (ISO).
    15/03/2025  -> clear (15 can only be a day).
    03/04/2025  -> AMBIGUOUS (3 Apr or 4 Mar?) -> we refuse to guess.
    """
    if pd.isna(value):
        return pd.NaT, False
    s = str(value).strip()
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
            return pd.Timestamp(s), False
        m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", s)
        if m:
            a, b, year = int(m[1]), int(m[2]), int(m[3])
            if a <= 12 and b <= 12:
                if a == b:  # 05/05/2025 is the same either way
                    return pd.Timestamp(year=year, month=a, day=b), False
                return pd.NaT, True
            if a > 12 and b <= 12:  # day/month
                return pd.Timestamp(year=year, month=b, day=a), False
            if b > 12 and a <= 12:  # month/day
                return pd.Timestamp(year=year, month=a, day=b), False
    except ValueError:
        pass
    return pd.NaT, False


def parse_date_column(series):
    pairs = [parse_date(v) for v in series]
    dates = pd.to_datetime(pd.Series([p[0] for p in pairs], index=series.index))
    ambiguous = pd.Series([p[1] for p in pairs], index=series.index)
    return dates, ambiguous


# ---------------------------------------------------------------- orders
def clean_orders(df, rates, notes):
    df = df.copy()
    notes.append(f"orders: {len(df)} raw rows loaded")
    for c in ["order_id", "customer_id", "currency", "status"]:
        df[c] = df[c].astype(str).str.strip()
    df["currency"] = df["currency"].str.upper()
    df["status"] = df["status"].str.lower()

    # 1) exact duplicate rows
    n = int(df.duplicated().sum())
    if n:
        ids = ", ".join(df[df.duplicated()]["order_id"])
        notes.append(f"orders: removed {n} exact duplicate row(s) ({ids})")
        df = df.drop_duplicates()

    # 2) same order_id but different values
    dup = df[df.duplicated("order_id", keep="first")]
    if len(dup):
        notes.append(
            f"orders: order_id(s) {', '.join(dup['order_id'])} appear again with DIFFERENT values; "
            "kept the first occurrence (data conflict)"
        )
        df = df.drop_duplicates("order_id", keep="first")

    # 3) dates
    df["order_date"], df["date_ambiguous"] = parse_date_column(df["order_date"])
    amb = df[df["date_ambiguous"]]
    if len(amb):
        notes.append(
            f"orders: {len(amb)} order(s) have an AMBIGUOUS date ({', '.join(amb['order_id'])}): "
            "day and month cannot be told apart. Date left empty, so they are excluded from date-based totals"
        )

    # 4) missing amounts
    miss = df[df["amount"].isna()]
    if len(miss):
        notes.append(f"orders: missing amount for {', '.join(miss['order_id'])}; excluded from money totals")

    # 5) currency -> USD
    def to_usd(row):
        if pd.isna(row["amount"]):
            return float("nan")
        if row["currency"] == "USD":
            return row["amount"]
        if row["currency"] == "EUR" and pd.notna(row["order_date"]):
            rate = rates.get(row["order_date"].strftime("%Y-%m"))
            if rate is not None:
                return row["amount"] * rate
        return float("nan")

    df["amount_usd"] = df.apply(to_usd, axis=1)
    bad = df[df["amount"].notna() & df["amount_usd"].isna()]
    if len(bad):
        notes.append(
            f"orders: could not convert to USD (no exchange rate for that month, unknown date or currency): "
            f"{', '.join(bad['order_id'])}; excluded from USD totals"
        )
    n_eur = int(((df["currency"] == "EUR") & df["amount_usd"].notna()).sum())
    if n_eur:
        notes.append(f"orders: converted {n_eur} EUR order(s) to USD using the monthly rate in rates.csv")
    return df.reset_index(drop=True)


# ---------------------------------------------------------------- customers
def clean_customers(df, orders, notes):
    df = df.copy()
    for c in ["customer_id", "name", "country"]:
        df[c] = df[c].astype(str).str.strip()
    df["signup_date"] = pd.to_datetime(df["signup_date"], errors="coerce")
    d = int(df.duplicated("customer_id").sum())
    if d:
        notes.append(f"customers: removed {d} duplicate customer_id row(s)")
        df = df.drop_duplicates("customer_id")
    unknown = sorted(set(orders["customer_id"]) - set(df["customer_id"]))
    if unknown:
        notes.append(
            f"customers: customer_id(s) {', '.join(unknown)} appear in orders but NOT in customers table (country unknown)"
        )
    return df.reset_index(drop=True)


# ---------------------------------------------------------------- refunds
def clean_refunds(df, orders, notes):
    df = df.copy()
    df["order_id"] = df["order_id"].astype(str).str.strip()
    df["refund_date"] = pd.to_datetime(df["refund_date"], errors="coerce")
    ref = orders[["order_id", "amount", "amount_usd", "status"]].rename(
        columns={"amount": "order_amount", "status": "order_status"}
    )
    m = df.merge(ref, on="order_id", how="left")
    orphan = m["order_status"].isna()
    cancelled = m["order_status"].eq("cancelled")
    too_big = m["refund_amount"] > m["order_amount"]
    m["valid"] = ~orphan & ~cancelled & ~too_big
    # refund in USD = refund amount * (order's USD amount / order's own-currency amount)
    m["refund_usd"] = m["refund_amount"] * m["amount_usd"] / m["order_amount"]

    if orphan.any():
        notes.append(f"refunds: order(s) {', '.join(m[orphan]['order_id'])} do not exist in orders -> refund INVALID")
    if cancelled.any():
        notes.append(f"refunds: order(s) {', '.join(m[cancelled]['order_id'])} were cancelled -> refund INVALID")
    if too_big.any():
        notes.append(f"refunds: refund larger than the order for {', '.join(m[too_big]['order_id'])} -> refund INVALID")
    notes.append(f"refunds: {int(m['valid'].sum())} of {len(m)} refunds are valid")
    return m


# ---------------------------------------------------------------- public API
def load_policy():
    return (DATA_DIR / "policy.txt").read_text()


def load_clean_data():
    """Returns (tables, notes). tables = dict of cleaned DataFrames. notes = list of strings."""
    notes = []
    rates_df = pd.read_csv(DATA_DIR / "rates.csv")
    rates = dict(zip(rates_df["month"].astype(str), rates_df["eur_to_usd"]))
    orders = clean_orders(pd.read_csv(DATA_DIR / "orders.csv"), rates, notes)
    customers = clean_customers(pd.read_csv(DATA_DIR / "customers.csv"), orders, notes)
    refunds = clean_refunds(pd.read_csv(DATA_DIR / "refunds.csv"), orders, notes)
    return {"orders": orders, "customers": customers, "refunds": refunds, "rates": rates_df}, notes


def describe_tables(tables):
    """Short text description of the tables, given to the LLM so it knows the column names."""
    lines = []
    for name in ["orders", "customers", "refunds"]:
        df = tables[name]
        cols = ", ".join(f"{c} ({t})" for c, t in df.dtypes.astype(str).items())
        lines.append(f"TABLE {name}: {len(df)} rows. Columns: {cols}")
    o = tables["orders"]
    lines.append(f"orders.order_date range: {o['order_date'].min().date()} to {o['order_date'].max().date()}")
    lines.append(f"orders.status values: {sorted(o['status'].unique())}; currency values: {sorted(o['currency'].unique())}")
    lines.append(f"customers.customer_id values: {sorted(tables['customers']['customer_id'])}")
    lines.append(f"customers.country values: {sorted(tables['customers']['country'].unique())}")
    lines.append("orders.amount_usd = order amount converted to USD (empty if it could not be converted).")
    lines.append("orders.order_date is empty when the date was ambiguous.")
    lines.append("refunds.valid = True only for refunds allowed by the business rules; refunds.refund_usd = refund in USD.")
    lines.append("There is NO cost / profit / margin data anywhere.")
    return "\n".join(lines)
