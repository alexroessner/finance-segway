# Postgres portfolio layer

A cross-portfolio SQL query layer on top of the Excel LBO/PE deal models in
`03_Private_Equity/deals/`. This is a pilot on one domain (LBO/PE — the
only domain with multiple real populated instances so far: `PROJECT_ATLAS`,
`HEALTHCARE_SERVICES_EXAMPLE`, `INDUSTRIALS_EXAMPLE`, `SAAS_EXAMPLE`) rather
than a rewrite of every domain into SQL. Extend `DEALS` in
`tools/postgres_etl.py` if/when more domains reach the same populated-
instance bar this one already has.

## Design principle: Excel is the calculation engine, Postgres is the query layer

Every number in this database is extracted from a workbook **after** it has
been recalculated for real by `tools/recalc.py` (headless LibreOffice) —
nothing here is a SQL or Python re-implementation of an IRR solve, a cash
sweep cascade, or a returns waterfall. The Base/Downside split is read by
toggling the workbook's own `Cover!C11` scenario switch and recalculating
twice, the exact same mechanism `check_lbo_scenario_switch` in
`tools/verify_reference_calcs.py` already verifies against an independent
Python re-implementation of the debt schedule. This keeps a single source
of truth (the spreadsheet) and avoids a second calculation engine that
could silently drift from it — the risk with hand-translating Excel
formulas into SQL directly.

Practically: **an analyst who trusts the Excel model can trust this
database**, because they're the same numbers, not a parallel computation.
Re-run the ETL any time the underlying deal workbooks change; there's
nothing to keep in sync by hand.

## Setup

```bash
createdb finance_segway                          # or: psql -c "CREATE DATABASE finance_segway;"
psql -d finance_segway -f db/schema.sql
pip install psycopg2-binary
python3 tools/postgres_etl.py                     # loads all 4 registered deals, both scenarios
```

`tools/postgres_etl.py --dry-run` extracts and prints without touching the
database — useful for checking a workbook change before loading it.

Connection defaults to `dbname=finance_segway` (peer/local auth). Override
with `--dsn` or the `FINANCE_SEGWAY_PG_DSN` environment variable, e.g.
`--dsn "host=... dbname=finance_segway user=... password=..."`.

## Schema

- `deals` — one row per deal (sponsor, sector, entry date, hold period, source workbook path).
- `deal_sources_uses` — Sources & Uses line items at entry (not scenario-dependent).
- `deal_returns` — one row per deal x scenario (Base/Downside): entry/exit multiples and EV, blended and sponsor-only MOIC/IRR, Yr5 leverage.
- `deal_debt_schedule` — one row per deal x scenario x year (Yr0-Yr5): EBITDA, FCF, per-tranche ending balances (revolver/TLA/TLB), total debt, interest expense, leverage.
- `v_deal_summary` — analyst-friendly join of `deals` + `deal_returns`, no manual join needed.
- `v_deal_downside_sensitivity` — pre-built Base-vs-Downside delta per deal (IRR drop, leverage increase) via a self-join on `v_deal_summary`.

## Example queries

Cross-portfolio view, one row per deal x scenario (the query most analysts start with):

```sql
SELECT deal_id, sector, scenario, sponsor_irr, sponsor_moic, yr5_leverage
FROM v_deal_summary
ORDER BY sector, scenario;
```

Average Base-case sponsor IRR by sector — the kind of cross-deal rollup
that's slow in Excel (open N files, copy one cell from each) and one line
here:

```sql
SELECT sector, ROUND(AVG(sponsor_irr), 4) AS avg_base_sponsor_irr
FROM v_deal_summary
WHERE scenario = 'Base'
GROUP BY sector
ORDER BY avg_base_sponsor_irr DESC;
```

Which deals are most exposed to a downside scenario (biggest IRR drop and
leverage build), ranked — the pre-built self-join view:

```sql
SELECT deal_id, sector, base_sponsor_irr, downside_sponsor_irr,
       sponsor_irr_drop, yr5_leverage_increase
FROM v_deal_downside_sensitivity
ORDER BY sponsor_irr_drop DESC;
```

Leverage trajectory (deleveraging path) for one deal, Base case:

```sql
SELECT year, ebitda, total_debt_ending, leverage_multiple
FROM deal_debt_schedule
WHERE deal_id = 'PROJECT_ATLAS' AND scenario = 'Base'
ORDER BY year;
```

Sources & Uses for one deal:

```sql
SELECT side, line_item, amount
FROM deal_sources_uses
WHERE deal_id = 'PROJECT_ATLAS'
ORDER BY side, line_item;
```

## Known limitations

- Pilot scope: LBO/PE only, 4 deals. Other domains don't have multiple
  populated instances yet (see `standards/model_inventory.json` — M4
  requires >=2 populated instances, and LBO/PE is currently the only
  domain at M4).
- `deal_name` currently reads the workbook's own Cover tab, which for
  these illustrative/fictional deals still carries the `[TARGET]`
  placeholder bracket -- expected, since these are example instances, not
  real portfolio companies (see each deal's own model_card.md).
- Sector is tracked in `tools/postgres_etl.py`'s `DEALS` registry, not in
  the workbook itself (the Cover tab has sponsor/deal-type/dates but no
  sector field) -- add new deals there.
- No incremental sync / change detection: re-running the ETL fully
  re-extracts and upserts every registered deal each time. Fine at this
  scale (4 deals); would want a smarter diff at real portfolio scale.
- This loads pre-computed OUTPUTS (returns, debt schedule), not the full
  formula graph -- it's a reporting/query layer, not a substitute for
  opening the workbook to change an assumption.
