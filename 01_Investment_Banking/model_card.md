# Model Card — Integrated 3-Statement / DCF (BASE archetype)

## Decision this model is designed to support
The flagship general-purpose valuation model: is this company's intrinsic
value (DCF) consistent with what the market currently pays for comparable
companies (Comps) — and if not, why. Feeds an integrated income
statement, balance sheet, and cash flow statement, then two independent
valuation methods triangulated against each other.

## Owner
unassigned

## Risk tier
Tier 2 (material analysis / investment recommendation) for a populated
instance. Blank template is Tier 3.

## Methodology
- **Integrated 3-statement model**: IS drives CF (net income, D&A flow
  through directly); BS is a manual-input-driven check (this template
  does not project a full balance-sheet roll-forward — every BS line item
  is a direct input, and the model verifies Assets = Liabilities + Equity
  rather than deriving the balance sheet from the other statements).
- **DCF**: standard unlevered FCF (`EBIT x (1-tax) + D&A - Capex`)
  discounted at WACC, with a Gordon Growth terminal value.
- **Valuation Cross-Check (the new tab)**: applies the Comps tab's own
  median EV/Revenue and EV/EBITDA multiples to the company's own FY1E
  financials to build a SECOND, independent valuation estimate, then
  compares it against the DCF's implied value/share. This is standard
  sell-side/buy-side practice — no single valuation method is trusted in
  isolation, and a large DCF-vs-comps gap is a prompt to investigate the
  DCF's growth/WACC/terminal-growth assumptions, not something to
  average away.

## Conventions and units
$mm throughout. FY-2A/FY-1A/FY0A are historical actuals (manual input);
FY1E onward are projected, driven entirely by the Assumptions tab once
the FY0A actuals are entered.

## Material assumptions
- Interest expense is held FLAT at the last actual (documented directly
  on the IS tab) — this simplified template does not build a debt
  schedule, to avoid a circular reference to a Balance Sheet this
  template doesn't project. A real leveraged deal model needs an actual
  debt schedule (see the LBO archetype for that mechanic).
- Comps-implied EV is a simple average of the EV/Revenue-method and
  EV/EBITDA-method estimates — a real analyst might weight these
  differently depending on the company (e.g., favoring EV/EBITDA for a
  mature, profitable business).

## Boundary conditions / when this breaks
- The DCF's Gordon Growth terminal value formula, `FCF x (1+g)/(WACC-g)`,
  requires WACC > terminal growth — checked explicitly on the Checks
  sheet, since the formula produces a nonsensical (or negative) result
  otherwise.
- The Comps-implied value/share guards against a blank/zero comps table
  producing a misleading result via `IFERROR`.

## Known limitations
- Single populated instance (ACME.xlsx), not two (M4 gate).
- No debt schedule — see Material Assumptions.
- Comps-implied EV blend is a simple average, not weighted or
  regression-based.

## When this model should not be used
Not a substitute for a full leveraged/credit model when debt structure
and interest expense sensitivity actually matter to the decision — this
template's flat-interest simplification is appropriate for a general
equity-research-style valuation, not a financing decision.

## Stakeholder perspectives represented
- **Equity analyst / investor**: intrinsic value (DCF) triangulated
  against market-implied value (comps).
Not represented: **credit/lender's view** (no debt schedule), **M&A
acquirer's view** (no precedent-transactions or synergy analysis).

## Version
Built by `tools/builders/build_template.py`. Valuation Cross-Check tab
shipped alongside `check_base_dcf_comps_triangulation` in
`tools/verify_reference_calcs.py` (joining the pre-existing
`check_base_archetype_integration`).
