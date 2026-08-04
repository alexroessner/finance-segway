# Model Card — LBO (Sources & Uses, Multi-Tranche Debt, Management Promote)

## Decision this model is designed to support
Sponsor-side underwriting of a leveraged buyout: does the proposed
capital structure (revolver + Term Loan A + Term Loan B + sponsor/
management equity) work, what does the debt schedule look like under a
cash sweep, and what returns does the deal generate for the sponsor and
for management (net of the promote) under Base and Downside operating
scenarios.

## Owner
unassigned

## Risk tier
Tier 1 (acquisition underwriting decision) for a populated instance.
Blank template is Tier 3.

## Methodology
- **Sources & Uses**: standard LBO capital structure, checked to balance
  exactly.
- **Multi-tranche debt schedule**: revolver (liquidity backstop, drawn
  on shortfall, repaid first from surplus), Term Loan A (senior,
  amortizing), Term Loan B (junior, minimal amortization, only swept
  after TLA is fully repaid) — absolute priority by seniority, the same
  logic as this repository's Restructuring recovery waterfall. Interest
  computed off BEGINNING-of-period balances only, avoiding a circular
  reference to the same period's cash-sweep-dependent ending balance.
- **Base/Downside scenario switching**: every assumption on the Debt
  Schedule tab has a Base and Downside column; a single Cover-tab
  selector (`Cover!C11`) drives which one every formula in the sheet
  actually reads (the "Active" column), not a copy — verified by
  `check_lbo_scenario_switch`.
- **Management promote / ratchet**: mechanically identical to a GP
  catch-up (see the Asset Management archetype's fee waterfall for the
  fund-side analogue) — management's rollover equity earns a
  disproportionate share of value created above an IRR hurdle, paid away
  from the sponsor's gross return to produce the sponsor's NET return
  (the number that actually matters to the sponsor's own LPs).

## Conventions and units
$mm. Entry multiple is a fixed contractual fact of the deal (not
scenario-aware); exit multiple IS scenario-aware, since it's the genuine
forward uncertainty — a Downside case pairs worse operating performance
with multiple compression, punishing a distressed exit twice rather than
once on EBITDA alone.

## Material assumptions
- Single-tier promote (one hurdle, one promote %) — no multi-tier
  ratchet (increasing promote at higher IRR bands), which some real deals
  use.
- Cash sweep is strict seniority order (revolver, then TLA, then TLB) —
  no leverage-based step-down grid the way the Private Credit archetype
  models (a genuinely different, also-real credit-agreement structure).

## Boundary conditions / when this breaks
- All ratio/IRR formulas guard division-by-zero and non-numeric
  intermediate results with `IFERROR`.
- The management-promote calculation floors "value created above hurdle"
  at zero (`MAX(0, exit_equity - hurdle_equity)`), so a deal that doesn't
  clear its hurdle correctly pays zero promote rather than a negative
  number.

## Known limitations
- No independent (non-developer) effective-challenge record on file yet
  — M4's "outcome monitoring and backtesting" and "versioned releases and
  migration notes" requirements are only partially satisfied by the
  version history in this repository's git log, not a formal separate
  record.
- Sector playbooks (`03_Private_Equity/playbooks/`) cover 3 sectors
  (SaaS, Healthcare Services, Industrials) as a pilot — not comprehensive
  coverage of plausible LBO sectors.

## When this model should not be used
Not a substitute for a full credit-committee underwriting package — this
template covers the core mechanics (sources & uses, debt schedule,
returns) but not covenant compliance certificates, security/collateral
documentation, or lender-side credit analysis (see the Private Credit
archetype for the lender's-side equivalent).

## Stakeholder perspectives represented
- **Sponsor**: net returns after the management promote.
- **Management (rollover equity)**: promote economics.
Not represented: **lender's own credit view** (see Private Credit for
that), **LP/fund-level view** of this single deal in a broader portfolio
context.

## Version
Built by `tools/builders/build_lbo_template.py`. Sources/Checks sheets
shipped in this pass, joining the pre-existing
`check_lbo_sources_uses_and_debt_schedule` and `check_lbo_scenario_switch`
in `tools/verify_reference_calcs.py`. Sector playbook pilot
(`03_Private_Equity/playbooks/`) and 3 new populated instances
(SAAS_EXAMPLE.xlsx, HEALTHCARE_SERVICES_EXAMPLE.xlsx,
INDUSTRIALS_EXAMPLE.xlsx) added alongside the pre-existing
PROJECT_ATLAS.xlsx, bringing this domain to 4 populated instances.
