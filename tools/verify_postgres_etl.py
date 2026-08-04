"""
verify_postgres_etl.py — confirm Postgres holds exactly what's in the
source workbooks right now, not stale or ETL-mangled data.

This isn't an independent-oracle check in the sense the rest of
tools/verify_reference_calcs.py is (there's no second, independently
derived truth to compare against — the workbook's recalculated cells ARE
the truth, by design; see db/README.md). What this catches is ETL bugs:
wrong row/column references, a silently-skipped scenario, a load that
didn't run after a workbook changed. Re-extracts every registered deal
fresh and diffs against what's actually stored in Postgres.

Usage:
    python3 tools/verify_postgres_etl.py [--dsn "dbname=finance_segway"]
Exit code is 0 iff Postgres matches a fresh extraction for every deal.
"""
import argparse
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))

from postgres_etl import DEALS, SCENARIOS, extract_deal  # noqa: E402

TOL = 1e-6


def close(a, b):
    if a is None or b is None:
        return a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) < TOL
    return a == b


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dsn", default=os.environ.get("FINANCE_SEGWAY_PG_DSN", "dbname=finance_segway"))
    args = ap.parse_args()

    import psycopg2
    conn = psycopg2.connect(args.dsn)
    mismatches = []
    deals_checked = 0

    try:
        for deal_id, meta in DEALS.items():
            payload = extract_deal(deal_id, meta["path"])
            deals_checked += 1
            with conn.cursor() as cur:
                for scenario in SCENARIOS:
                    ref = payload["returns"][scenario]
                    cur.execute(
                        """SELECT sponsor_irr, sponsor_moic, moic_blended, irr_blended, yr5_leverage
                           FROM deal_returns WHERE deal_id = %s AND scenario = %s""",
                        (deal_id, scenario),
                    )
                    row = cur.fetchone()
                    if row is None:
                        mismatches.append(f"{deal_id}/{scenario}: no deal_returns row in Postgres")
                        continue
                    db_sponsor_irr, db_sponsor_moic, db_moic, db_irr, db_lev = row
                    checks = [
                        ("sponsor_irr", db_sponsor_irr, ref["sponsor_irr"]),
                        ("sponsor_moic", db_sponsor_moic, ref["sponsor_moic"]),
                        ("moic_blended", db_moic, ref["moic_blended"]),
                        ("irr_blended", db_irr, ref["irr_blended"]),
                        ("yr5_leverage", db_lev, ref["yr5_leverage"]),
                    ]
                    for field, db_val, ref_val in checks:
                        if not close(float(db_val), float(ref_val)):
                            mismatches.append(
                                f"{deal_id}/{scenario}/{field}: db={db_val} fresh_extract={ref_val}")

                    cur.execute(
                        """SELECT year, ebitda, total_debt_ending, leverage_multiple
                           FROM deal_debt_schedule WHERE deal_id = %s AND scenario = %s ORDER BY year""",
                        (deal_id, scenario),
                    )
                    db_rows = {r[0]: r[1:] for r in cur.fetchall()}
                    for row_ref in payload["debt_schedule"][scenario]:
                        y = row_ref["year"]
                        if y not in db_rows:
                            mismatches.append(f"{deal_id}/{scenario}/year{y}: missing from deal_debt_schedule")
                            continue
                        db_ebitda, db_debt, db_lev2 = db_rows[y]
                        if not close(float(db_ebitda), float(row_ref["ebitda"])):
                            mismatches.append(f"{deal_id}/{scenario}/year{y}/ebitda: db={db_ebitda} fresh={row_ref['ebitda']}")
                        if not close(float(db_debt), float(row_ref["total_debt_ending"])):
                            mismatches.append(f"{deal_id}/{scenario}/year{y}/total_debt_ending: db={db_debt} fresh={row_ref['total_debt_ending']}")
    finally:
        conn.close()

    print(f"Checked {deals_checked} deals x {len(SCENARIOS)} scenarios against Postgres.")
    if mismatches:
        print(f"\n{len(mismatches)} MISMATCH(ES):")
        for m in mismatches:
            print(f"  - {m}")
        sys.exit(1)
    print("Postgres matches a fresh extraction from every source workbook. PASS")


if __name__ == "__main__":
    main()
