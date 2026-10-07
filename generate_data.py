"""MEMBER 1 owns this file.
Creates the messy dataset on purpose. Run:  python data/generate_data.py
Every trap is listed in data/TRAPS.md so judges (and teammates) can see what is planted.
"""
import csv
from pathlib import Path

D = Path(__file__).resolve().parent

orders = [
    # order_id, customer_id, order_date, amount, currency, status
    ("O001", "C01", "2025-01-05", "100.00", "USD", "completed"),
    ("O002", "C02", "2025-01-12", "200.00", "USD", "completed"),
    ("O003", "C03", "2025-01-20", "50.00", "EUR", "completed"),
    ("O004", "C01", "2025-02-02", "150.00", "USD", "completed"),
    ("O005", "C04", "2025-02-10", "80.00", "EUR", "completed"),
    ("O006", "C02", "2025-02-15", "120.00", "USD", "cancelled"),
    ("O007", "C05", "2025-02-25", "300.00", "USD", "completed"),
    ("O008", "C03", "2025-03-03", "75.00", "EUR", "completed"),
    ("O009", "C04", "2025-03-14", "220.00", "USD", "completed"),
    ("O010", "C06", "2025-03-21", "", "USD", "completed"),            # TRAP: missing amount
    ("O011", "C05", "2025-03-28", "90.00", "USD", "completed"),
    ("O012", "C01", "15/03/2025", "60.00", "USD", "completed"),        # day/month, unambiguous (15 > 12)
    ("O013", "C02", "03/04/2025", "130.00", "USD", "completed"),       # TRAP: 3 Apr or 4 Mar?
    ("O014", "C06", "2025-04-08", "110.00", "EUR", "completed"),       # TRAP: no EUR rate for April
    ("O015", "C03", "2025-04-15", "95.00", "USD", "completed"),
    ("O016", "C07", "2025-04-22", "180.00", "USD", "completed"),       # TRAP: C07 not in customers.csv
    ("O003", "C03", "2025-01-20", "50.00", "EUR", "completed"),        # TRAP: exact duplicate
    ("O009", "C04", "2025-03-14", "220.00", "USD", "completed"),       # TRAP: exact duplicate
    ("O015", "C03", "2025-04-15", "105.00", "USD", "completed"),       # TRAP: same id, different amount
]
customers = [
    ("C01", "Asha", "India", "2024-11-02"),
    ("C02", "Ben", "UK", "2024-12-15"),
    ("C03", "Carlos", "Spain", "2025-01-03"),
    ("C04", "Dina", "Germany", "2025-01-30"),
    ("C05", "Eli", "USA", "2025-02-11"),
    ("C06", "Farah", "India", "2025-03-01"),
]
refunds = [
    # order_id, refund_amount (same currency as the order), refund_date
    ("O001", "20.00", "2025-01-25"),
    ("O004", "200.00", "2025-02-20"),   # TRAP: refund bigger than the order (150)
    ("O006", "120.00", "2025-02-20"),   # TRAP: refund for a CANCELLED order
    ("O009", "40.00", "2025-03-20"),
    ("O999", "25.00", "2025-03-25"),    # TRAP: order does not exist
]
rates = [("2025-01", "1.10"), ("2025-02", "1.05"), ("2025-03", "1.08")]  # TRAP: no April rate


def write(name, header, rows):
    with open(D / name, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


write("orders.csv", ["order_id", "customer_id", "order_date", "amount", "currency", "status"], orders)
write("customers.csv", ["customer_id", "name", "country", "signup_date"], customers)
write("refunds.csv", ["order_id", "refund_amount", "refund_date"], refunds)
write("rates.csv", ["month", "eur_to_usd"], rates)

(D / "policy.txt").write_text(
    "BUSINESS RULES\n"
    "1. Revenue means orders with status 'completed' only. Cancelled orders are not revenue.\n"
    "2. Gross revenue = sum of completed orders in USD. Net revenue = gross revenue minus VALID refunds.\n"
    "3. A refund is valid only if its order exists, the order is completed, and the refund is not larger than the order.\n"
    "4. All money is reported in USD. EUR orders are converted with the monthly rate in rates.csv.\n"
    "5. Quarter 1 means January, February and March 2025.\n"
)
print("Data written to", D)
