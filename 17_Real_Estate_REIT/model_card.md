# Model Card — Real Estate / REIT (Pro Forma, Valuation, FFO/AFFO, Levered Hold, LP/GP Promote)

## Decision this model is designed to support
Four linked questions: (1) what does the property's stabilized pro forma
look like (NOI, cash flow before tax), (2) what is it worth on an income
basis (cap rate valuation), (3) for a REIT, what's the sustainable
dividend-paying capacity (FFO/AFFO), and (4) — the new addition — for a
syndicated deal with a sponsor (GP) co-investing alongside LPs, how does
the profit actually split once the GP's promote is applied, and does the
promote structure actually reward GP outperformance the way it's
supposed to.

## Owner
unassigned

## Risk tier
Tier 1 (acquisition/investment decision) for a populated instance. Blank
template is Tier 3.

## Methodology
- **LP/GP promote waterfall**: models the dominant real-estate
  syndication structure — sponsor (GP) co-invests alongside LPs, both get
  capital back plus a COMPOUNDED preferred return pro-rata to their
  ownership share, then the GP earns a promote (disproportionate share)
  on profit above the preferred. Unlike this repository's PE/VC/fund
  carry waterfalls (Asset Management, Venture Capital), this one has NO
  catch-up tranche — straight pref-then-split, which is genuinely how
  many real estate deals (as distinct from PE/VC funds) are structured.
- **Compounded preferred return**: `total_equity x ((1+pref)^hold - 1)`,
  a single lump-sum compounding over the full hold period, applied against
  the deal's ONE terminal distribution event (this model's Yr1-5 cash
  flows plus exit proceeds) — an approximation of a true cash-flow-weighted
  (XIRR-based) hurdle, appropriate for a model with one purchase and one
  sale, not a multi-close/multi-distribution fund.
- **Cap rate valuation, FFO/AFFO, levered IRR/MOIC**: standard
  income-approach valuation and REIT/private-deal return metrics,
  unchanged from the prior build.

## Conventions and units
USD. NOI growth compounds starting in Year 2 (Year 1 NOI is the current,
un-grown stabilized figure) — the exit cap rate is applied to Year 6's
FORWARD NOI, the standard convention (buyer prices off next year's income,
not the trailing year's).

## Material assumptions
- LP/GP ownership split (default 90/10), preferred return (default 8%),
  and promote (default 20% above pref) are illustrative defaults — see
  the Sources sheet.
- Debt is assumed interest-only with an unchanged balance through the
  hold (debt payoff at exit = original debt amount) — a real deal may
  amortize.

## Boundary conditions / when this breaks
- The compounded-pref lump-sum approach only works cleanly for a
  single-purchase, single-sale deal; a deal with additional capital calls
  or interim distributions would need a true XIRR-based hurdle instead.
- All ratio/division formulas guard against zero denominators with
  `IFERROR`.

## Known limitations
- No catch-up tranche — a deliberate modeling choice (see Methodology),
  not an oversight, but it means this specific tab cannot represent a
  deal that DOES include one without modification.
- No populated instance yet.
- Debt assumed interest-only for the levered-hold IRR calc; no amortizing-
  debt variant.

## When this model should not be used
Not a substitute for the actual operating/partnership agreement's
specific waterfall language — real deals vary in whether they include a
catch-up, multiple pref tiers, or a clawback provision, none of which
this simplified single-tier structure captures.

## Stakeholder perspectives represented
- **LP investor**: equity multiple, IRR.
- **GP/sponsor**: promote economics, co-invest multiple.
Not represented: **lender's perspective** (covered partially by the DSCR
row on the 5-Year Hold tab, but no full covenant/default modeling),
**property-level operator/asset-manager view**.

## Version
Built by `tools/builders/build_real_estate_template.py`. LP-GP Promote
tab shipped alongside `check_real_estate_lp_gp_promote` in
`tools/verify_reference_calcs.py`.
