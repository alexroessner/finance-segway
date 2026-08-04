# SaaS / Software Playbook — LBO (03_Private_Equity)

## What makes this sector's economics genuinely different
Revenue is contractual and recurring, so growth compounds directly into
EBITDA growth at a rate no industrial or services business can match —
but EBITDA margins are typically lower than the multiple would suggest
(growth investment suppresses near-term profitability), and the entire
valuation is a bet on the growth rate PERSISTING. Lenders therefore
underwrite LOWER leverage relative to EBITDA than a stable-cash-flow
sector would get, despite SaaS often being lower-risk on a pure
revenue-durability basis — the multiple itself is the risk lenders are
pricing, not the near-term cash flow.

## Typical valuation range
Entry multiples of 10-18x EBITDA are common for growth-stage software
buyouts (vs. 6-10x for mature industrials) — the premium reflects the
growth rate capitalized into EBITDA, not current profitability. This
playbook's example uses 15.0x entry.

## Typical capital structure
3.5-4.5x Debt/EBITDA at close, well below what a stable-cash-flow sector
like healthcare services supports at the same nominal EBITDA — lenders
are wary of underwriting hard debt service against a cash flow stream
that could deteriorate quickly if growth stalls or churn rises. This
playbook's example: $50mm Term Loan A + $30mm Term Loan B on $20mm entry
EBITDA = 4.0x at close.

## Key operating assumptions
- EBITDA growth: high and directly tied to revenue growth (this
  playbook's example: 20%/yr Base case).
- FCF conversion: moderate-to-high (55% in the example) since SaaS is
  typically capital-light (low capex intensity) once past the initial
  build-out phase.
- Multiple compression risk is the dominant downside driver, more than
  EBITDA decline itself.

## Sector-specific KPIs (beyond what the generic template tracks)
Net Revenue Retention (NRR), Rule of 40 (growth % + margin % >= 40),
CAC payback period, gross revenue churn vs. net revenue churn, ARR
growth vs. GAAP revenue growth (timing lag from ratable recognition).
None of these are in the generic LBO template — a real SaaS diligence
process tracks them explicitly; this playbook's model uses EBITDA growth
as a proxy for what NRR and Rule of 40 would otherwise decompose.

## Downside scenario: what actually breaks
A SaaS downside is a GROWTH/CHURN shock, not a demand collapse — and it
hits twice: EBITDA growth flips negative (this example: -5%/yr, a steep
deceleration reflecting elevated churn plus a slower net-new bookings
environment), AND the exit multiple compresses hard (14.0x Base down to
9.0x Downside in this example) because the market re-rates decelerating
growth companies punitively — a SaaS company trading on a growth
multiple that stops growing loses the growth premium entirely, not just
proportionally.

## Diligence items specific to this sector
Cohort-level retention curves (not just blended NRR), customer
concentration, platform/technical debt that could slow future feature
velocity, pricing power evidence (has the company actually raised
prices without losing customers), and sales-efficiency metrics (magic
number, CAC payback) as a leading indicator of whether growth is
becoming more or less capital-efficient.

## How to parameterize the builder
On `Debt Schedule` (columns K=Base, L=Downside): set EBITDA growth (row
5) high and volatile between scenarios (this example: 20% / -5%); FCF
conversion (row 6) moderate-high (55% / 35%); keep leverage LOW at
Sources & Uses (TLA+TLB well under 4.5x entry EBITDA). On `Returns`: set
a HIGH entry multiple (row 6, 10-18x) and an even wider Base/Downside
exit-multiple spread (row 12, D/E columns) than other sectors, since
multiple compression is the primary downside transmission mechanism.

## Populated example instance
`03_Private_Equity/deals/SAAS_EXAMPLE.xlsx` — $20mm entry EBITDA, 15.0x
entry multiple ($300mm EV), $80mm debt at close (4.0x). Base case: 20%
EBITDA growth, 55% FCF conversion, 14.0x exit multiple. Result: Yr0
(post-Year-1) leverage delevers fast to 3.79x and reaches 0.34x by Yr5
(high growth + high FCF conversion pays down debt quickly), blended MOIC
2.96x / IRR 24.2% — comfortably clears the 20% promote hurdle, so
management earns a real promote ($21.5mm) and the sponsor's net IRR
(23.4%) sits just below the blended figure. This is the one of the three
pilot instances that clears its hurdle, consistent with SaaS's higher
target-return profile at underwriting.

## Sources
Multiple ranges and leverage tolerance are illustrative, informed by
general public commentary on software LBO market convention (not any
specific deal) — mark every number here as a modeling assumption, not a
sourced fact, before using this playbook for a real investment decision.
