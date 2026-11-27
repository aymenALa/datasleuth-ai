"""Reproducible generator for data/samples/enterprise_invoice_ledger.csv (seed=42)."""

from __future__ import annotations

import csv
from datetime import date, timedelta
from pathlib import Path
import random


def generate_enterprise_invoice_ledger(output_path: Path, seed: int = 42) -> tuple[int, int]:
    """Generate a deterministic 2,000-row synthetic invoice ledger with known quality scenarios."""

    rng = random.Random(seed)
    headers = [
        "invoice_id",
        "account_id",
        "issue_date",
        "payment_date",
        "region",
        "customer_segment",
        "quantity",
        "unit_price",
        "discount_rate",
        "invoice_amount",
    ]
    regions = ["North America", "Europe", "Asia Pacific", "Latin America"]
    segments = ["Enterprise", "Mid-Market", "SMB", "Public Sector"]
    base_date = date(2025, 1, 1)

    rows: list[list[object]] = []
    for i in range(1, 1971):
        inv_id = f"INV-{10000 + i}"
        acct_id = f"ACCT-{rng.randint(100, 499)}"
        issue = base_date + timedelta(days=rng.randint(0, 360))
        pay = "" if rng.random() < 0.045 else (issue + timedelta(days=rng.randint(1, 45))).isoformat()
        reg = "" if rng.random() < 0.03 else rng.choice(regions)
        seg = "" if rng.random() < 0.035 else rng.choice(segments)
        qty = rng.randint(1, 20)
        price = round(rng.uniform(25.0, 450.0), 2)
        if rng.random() < 0.025:
            disc: object = rng.choice(["N/A", "exempt", "pending"])
            disc_val = 0.0
        else:
            disc_pct = rng.choice([0, 5, 10, 15, 20])
            disc = str(disc_pct)
            disc_val = disc_pct / 100.0
        amt = round(qty * price * (1.0 - disc_val), 2)
        if i in (42, 189, 512, 877, 1204, 1533, 1890):
            amt = round(rng.uniform(28000.0, 65000.0), 2)
        rows.append([inv_id, acct_id, issue.isoformat(), pay, reg, seg, qty, price, disc, amt])

    # Inject 30 deterministic duplicate rows to reach 2,000 rows
    for idx in range(0, 30):
        rows.append(list(rows[idx * 50]))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)

    return len(rows), len(headers)


if __name__ == "__main__":
    target = Path(__file__).resolve().parents[1] / "data" / "samples" / "enterprise_invoice_ledger.csv"
    row_count, col_count = generate_enterprise_invoice_ledger(target)
    print(f"Generated {target}: {row_count} rows, {col_count} columns")
