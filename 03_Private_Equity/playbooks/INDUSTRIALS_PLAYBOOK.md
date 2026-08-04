# Industrials / Manufacturing Playbook — LBO (03_Private_Equity)

## What makes this sector's economics genuinely different
Cash flow is cyclical and operating-leverage-heavy: revenue moves with
end-market demand (often tied to broader industrial production or a
specific end-market like autos, construction, or energy), and because a
meaningful share of costs are fixed, EBITDA margin compresses sharply
when volume falls — a demand shock hits harder than the revenue decline
alone would suggest. Capex is also largely maintenance-driven and
doesn't flex down much in a downturn, so free cash flow conversion falls
even further than EBITDA does. This is the sector where the downside
case needs to punish BOTH EBITDA and FCF conversion simultaneously, not
just one.

## Typical valuation range
6-9x EBITDA is typical for industrial/manufacturing buyouts — the lowest
of the three sectors in this playbook set, reflecting cyclicality risk
and the absence of a growth or defensiveness premium. This playbook's
example uses 7.5x entry.

## Typical capital structure
4.0-5.0x Debt/EBITDA at close — moderate, reflecting real but
manageable cyclicality risk (lower than healthcare's stability-driven
tolerance, but not as conservative as an extremely volatile commodity
business might require). This playbook's example: $100mm Term Loan A +
$80mm Term Loan B on $40mm entry EBITDA = 4.5x at close.

## Key operating assumptions
- EBITDA growth: low and CYCLICAL (4%/yr Base in this example) — modest
  organic growth in a normal year, not a growth story.
- FCF conversion: the LOWEST of the three sectors (35% Base) — capex
  intensity (maintenance capex, equipment replacement) is structurally
  higher than either SaaS or healthcare services.
- The downside case needs both EBITDA decline AND FCF conversion
  collapse modeled together — see below.

## Sector-specific KPIs (beyond what the generic template tracks)
Capacity utilization, order backlog and book-to-bill ratio, input-cost
pass-through ability (can the company raise prices as fast as raw
material/commodity costs rise, or does it eat margin compression during
the lag), customer concentration by end-market (a supplier concentrated
in one cyclical end-market carries more risk than one diversified
across several), and working-capital swings tied to commodity input
costs (inventory and payables balloon when input costs spike). None of
these are in the generic LBO template.

## Downside scenario: what actually breaks
An industrials downside is a DEMAND shock that hits twice, mechanically:
EBITDA growth flips sharply negative (this example: -12%/yr, the
steepest downside of the three sectors, reflecting operating leverage —
a modest revenue decline in a fixed-cost-heavy business produces an
outsized EBITDA decline) AND FCF conversion collapses further (35% Base
down to 15% Downside) because maintenance capex is largely fixed and
doesn't flex down with volume the way variable costs do — so the SAME
dollar of EBITDA converts to much less free cash flow in a downturn,
compounding the debt-service strain exactly when the company can least
afford it.

## Diligence items specific to this sector
End-market concentration and cyclicality correlation, customer contract
structure (long-term agreements with price-escalation clauses vs. spot
pricing), input-cost hedging program (if any) and historical pass-through
track record, equipment age/condition and deferred-maintenance risk,
and environmental/regulatory liabilities (a genuine and sector-specific
diligence item for manufacturing facilities).

## How to parameterize the builder
On `Debt Schedule`: set EBITDA growth (row 5) with the WIDEST Base/
Downside spread of the three playbooks (this example: 4% / -12%) to
reflect operating leverage; FCF conversion (row 6) LOW in both cases and
falling further in Downside (35% / 15%) to reflect fixed maintenance
capex; leverage moderate (4.0-5.0x). On `Returns`: entry multiple in the
6-9x range (the lowest of the three sectors); exit-multiple compression
(8.0x Base to 6.0x Downside in this example) reflecting cyclical-trough
pricing on exit if the downside materializes near the hold period's end.

## Populated example instance
`03_Private_Equity/deals/INDUSTRIALS_EXAMPLE.xlsx` — $40mm entry EBITDA,
7.5x entry multiple ($300mm EV), $180mm debt at close (4.5x). Base case:
4% EBITDA growth, 35% FCF conversion, 8.0x exit multiple. Result:
leverage delevers the SLOWEST of the three examples (Yr0 4.54x to Yr5
3.48x — low growth combined with low FCF conversion means mandatory
amortization does most of the work, with little cash sweep), blended
MOIC 1.69x / IRR 11.1% — well below the 20% promote hurdle, so
management earns zero promote. This is the weakest of the three example
outcomes, honestly reflecting that a 7.5x-entry, low-growth, low-FCF-
conversion industrial deal needs EITHER a lower entry multiple, more
aggressive deleveraging assumptions, or real operational upside
(margin improvement, bolt-on M&A) that this baseline example doesn't
include, to underwrite to a target return.

## Sources
Multiple/leverage ranges are illustrative, informed by general public
commentary on industrials LBO market convention (not any specific deal)
— mark every number here as a modeling assumption, not a sourced fact,
before using this playbook for a real investment decision.
