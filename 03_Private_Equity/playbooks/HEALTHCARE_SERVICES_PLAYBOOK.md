# Healthcare Services Playbook — LBO (03_Private_Equity)

## What makes this sector's economics genuinely different
Demand is largely inelastic (people need care regardless of the economic
cycle) and revenue is often payor-diversified across commercial
insurance, Medicare, and Medicaid — which makes cash flow unusually
stable and recession-resistant relative to almost any other sector in
this repository. Lenders reward that stability with materially HIGHER
leverage tolerance than a cyclical or growth-uncertain business gets at
the same EBITDA, even though the entry multiple itself is also elevated
(scarcity of scaled, professionally-run platforms plus active
consolidation/roll-up demand from strategics and other sponsors).

## Typical valuation range
8-12x EBITDA is common for platform healthcare services buyouts, with
premium paid for scale, multi-state footprint, and payor diversification
— lower than SaaS (no growth-rate premium) but higher than industrials
(no cyclicality discount). This playbook's example uses 10.0x entry.

## Typical capital structure
5.0-6.5x Debt/EBITDA at close is common and underwritable specifically
BECAUSE of cash-flow stability — a healthcare services platform can
carry leverage an industrial business at the same EBITDA could not
safely service through a downturn. This playbook's example: $90mm Term
Loan A + $75mm Term Loan B on $30mm entry EBITDA = 5.5x at close.

## Key operating assumptions
- EBITDA growth: moderate and STABLE (8%/yr Base in this example) —
  driven by a mix of organic growth (volume, modest price increases) and
  inorganic growth (add-on acquisitions in a roll-up strategy), not
  pure organic expansion.
- FCF conversion: moderate (45%), lower than SaaS because healthcare
  services genuinely requires real capex (facilities, equipment,
  de novo site build-out) that doesn't disappear the way software capex
  does.
- Downside is comparatively MILD relative to SaaS or industrials — this
  is the sector's defining characteristic.

## Sector-specific KPIs (beyond what the generic template tracks)
Payor mix (commercial vs. Medicare/Medicaid reimbursement rates and
timing), same-store volume growth vs. de novo/acquired growth,
provider/clinician retention and recruiting pipeline, regulatory/
licensure risk by state, and EBITDA add-backs specific to the sector
(one-time litigation reserves, de novo site losses before ramp,
management-company fee normalization). None of these are in the generic
LBO template — a real healthcare diligence process scrutinizes add-backs
especially hard, since reported EBITDA in this sector is more
adjustment-heavy than most.

## Downside scenario: what actually breaks
A healthcare downside is usually a REIMBURSEMENT or REGULATORY shock —
a rate cut from a major payor, a change in CMS reimbursement policy, or
a licensure/compliance issue at a subset of sites — not a demand
collapse. This example models a comparatively mild -2%/yr EBITDA
Downside (vs. SaaS's -5% and industrials' -12%), reflecting genuine
demand inelasticity, alongside a MODEST exit-multiple compression
(10.5x Base to 8.5x Downside) — smaller than either other sector's
compression, because buyers of healthcare platforms pay for stability
precisely because it doesn't evaporate in a downturn.

## Diligence items specific to this sector
Payor contract terms and renewal timing, regulatory/compliance history
(state licensure, CMS survey results), clinician employment/retention
structure (W-2 vs. contracted, non-compete enforceability), integration
track record if this is a roll-up platform (has the company actually
realized synergies on prior add-ons, or just accumulated EBITDA
add-backs), and malpractice/liability insurance adequacy.

## How to parameterize the builder
On `Debt Schedule`: set EBITDA growth (row 5) moderate and with a MILD
downside spread relative to other sectors (this example: 8% / -2%); FCF
conversion (row 6) moderate (45% / 30%, reflecting real capex need); size
leverage HIGH relative to the generic template default (TLA+TLB toward
5.5-6.0x entry EBITDA — this is the sector where higher leverage is
actually the correct call, not aggressive). On `Returns`: entry multiple
in the 8-12x range; keep the Base/Downside exit-multiple spread
NARROWER than SaaS's, reflecting genuine defensiveness.

## Populated example instance
`03_Private_Equity/deals/HEALTHCARE_SERVICES_EXAMPLE.xlsx` — $30mm entry
EBITDA, 10.0x entry multiple ($300mm EV), $165mm debt at close (5.5x).
Base case: 8% EBITDA growth, 45% FCF conversion, 10.5x exit multiple.
Result: leverage delevers more slowly than the SaaS example (Yr0 5.47x
to Yr5 3.16x, reflecting lower FCF conversion despite comparable
mandatory amortization), blended MOIC 2.23x / IRR 17.4% — this deal, AS
PARAMETERIZED, does NOT clear the 20% promote hurdle, so management
earns zero promote and the sponsor's net IRR equals the blended IRR
exactly (no value transferred away). This is an intentionally honest
result, not a tuned "success story": at a 10.0x entry multiple with only
8% growth and modest multiple expansion, the deal underwrites to a solid
but sub-hurdle outcome — illustrating that healthcare services' safety
comes with a real return trade-off unless entry discipline or leverage
is pushed harder than this example does.

## Sources
Multiple/leverage ranges are illustrative, informed by general public
commentary on healthcare services LBO market convention (not any
specific deal) — mark every number here as a modeling assumption, not a
sourced fact, before using this playbook for a real investment decision.
