-- Postgres portfolio layer -- schema for cross-portfolio SQL analytics on
-- top of the Excel LBO/PE deal models in 03_Private_Equity/deals/.
--
-- Design principle: Excel remains the calculation engine. Every number in
-- these tables is extracted from a workbook AFTER it has been recalculated
-- for real by tools/recalc.py (headless LibreOffice) -- nothing here is a
-- SQL re-implementation of a duration formula, an IRR solve, or a cash
-- sweep cascade. This is a query/reporting layer fed by verified output,
-- not a second, parallel calculation engine that could silently drift from
-- the spreadsheets. See tools/postgres_etl.py for the extraction logic and
-- db/README.md for setup + example analyst queries.
--
-- Run: psql -d finance_segway -f db/schema.sql

BEGIN;

CREATE TABLE IF NOT EXISTS deals (
    deal_id            TEXT PRIMARY KEY,        -- e.g. 'PROJECT_ATLAS' (matches the workbook filename stem)
    deal_name          TEXT NOT NULL,
    sponsor            TEXT,
    deal_type          TEXT,                    -- Cover!C5, e.g. 'LBO / carve-out'
    sector             TEXT,                    -- Healthcare Services / Industrials / SaaS / Diversified
    entry_date         DATE,
    hold_period_years  INTEGER,
    workbook_path      TEXT NOT NULL,            -- repo-relative path to the source .xlsx
    source_domain      TEXT NOT NULL DEFAULT 'lbo-pe-mb',  -- standards/model_inventory.json id
    last_synced_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS deal_sources_uses (
    deal_id     TEXT NOT NULL REFERENCES deals(deal_id) ON DELETE CASCADE,
    side        TEXT NOT NULL CHECK (side IN ('Sources', 'Uses')),
    line_item   TEXT NOT NULL,
    amount      NUMERIC NOT NULL,
    PRIMARY KEY (deal_id, side, line_item)
);

-- One row per deal per scenario (Base / Downside), matching the workbook's
-- own Cover!C11 scenario toggle -- NOT re-derived, just extracted twice
-- (once per toggle position) after a real recalc each time. See
-- check_lbo_scenario_switch in tools/verify_reference_calcs.py for the
-- same toggle mechanism already verified against an independent Python
-- re-implementation of the debt cascade.
CREATE TABLE IF NOT EXISTS deal_returns (
    deal_id                 TEXT NOT NULL REFERENCES deals(deal_id) ON DELETE CASCADE,
    scenario                TEXT NOT NULL CHECK (scenario IN ('Base', 'Downside')),
    entry_ebitda            NUMERIC,
    entry_multiple          NUMERIC,
    entry_ev                NUMERIC,
    sponsor_equity_entry    NUMERIC,
    exit_ebitda             NUMERIC,
    exit_multiple           NUMERIC,
    exit_ev                 NUMERIC,
    net_debt_at_exit        NUMERIC,
    exit_equity_value       NUMERIC,
    moic_blended            NUMERIC,             -- before management promote
    irr_blended             NUMERIC,
    hold_period_years       NUMERIC,
    management_promote      NUMERIC,
    sponsor_net_proceeds    NUMERIC,
    sponsor_moic            NUMERIC,             -- net of promote paid away -- the number that matters to LPs
    sponsor_irr             NUMERIC,
    yr5_leverage            NUMERIC,             -- total debt / EBITDA at hold-period end
    PRIMARY KEY (deal_id, scenario)
);

-- Year-by-year debt schedule detail (Yr0..Yr5), one row per deal x
-- scenario x year, extracted from the Debt Schedule tab's Active column
-- after toggling Cover!C11 and recalculating.
CREATE TABLE IF NOT EXISTS deal_debt_schedule (
    deal_id                  TEXT NOT NULL REFERENCES deals(deal_id) ON DELETE CASCADE,
    scenario                 TEXT NOT NULL CHECK (scenario IN ('Base', 'Downside')),
    year                     INTEGER NOT NULL CHECK (year BETWEEN 0 AND 5),
    ebitda                   NUMERIC,
    fcf                      NUMERIC,
    revolver_ending_balance  NUMERIC,
    tla_ending_balance       NUMERIC,
    tlb_ending_balance       NUMERIC,
    total_debt_ending        NUMERIC,
    total_interest_expense   NUMERIC,
    leverage_multiple        NUMERIC,             -- total debt / EBITDA
    PRIMARY KEY (deal_id, scenario, year)
);

CREATE INDEX IF NOT EXISTS idx_deal_returns_scenario ON deal_returns(scenario);
CREATE INDEX IF NOT EXISTS idx_deal_debt_schedule_scenario_year ON deal_debt_schedule(scenario, year);
CREATE INDEX IF NOT EXISTS idx_deals_sector ON deals(sector);

-- Analyst-friendly view: one row per deal x scenario with the headline
-- decision metrics, sector/sponsor context included so cross-portfolio
-- filtering and grouping doesn't require a manual join.
CREATE OR REPLACE VIEW v_deal_summary AS
SELECT
    d.deal_id,
    d.deal_name,
    d.sector,
    d.sponsor,
    d.deal_type,
    d.entry_date,
    r.scenario,
    r.entry_multiple,
    r.exit_multiple,
    r.moic_blended,
    r.irr_blended,
    r.sponsor_moic,
    r.sponsor_irr,
    r.yr5_leverage
FROM deals d
JOIN deal_returns r USING (deal_id);

-- Downside-vs-Base delta per deal -- the single most useful "how exposed
-- is this deal to a growth slowdown" query, pre-built as a view since it
-- needs a self-join most analysts wouldn't want to hand-write each time.
CREATE OR REPLACE VIEW v_deal_downside_sensitivity AS
SELECT
    b.deal_id,
    b.deal_name,
    b.sector,
    b.sponsor_irr AS base_sponsor_irr,
    dn.sponsor_irr AS downside_sponsor_irr,
    b.sponsor_irr - dn.sponsor_irr AS sponsor_irr_drop,
    b.yr5_leverage AS base_yr5_leverage,
    dn.yr5_leverage AS downside_yr5_leverage,
    dn.yr5_leverage - b.yr5_leverage AS yr5_leverage_increase
FROM v_deal_summary b
JOIN v_deal_summary dn ON dn.deal_id = b.deal_id AND dn.scenario = 'Downside'
WHERE b.scenario = 'Base';

COMMIT;
