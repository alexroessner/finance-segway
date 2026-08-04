# Model Card — Private Credit / Direct Lending (Facility, Covenants, ECF Sweep)

## Decision this model is designed to support
The lender's side of a direct-lending facility: is this credit within
covenant today, and how does the facility actually amortize given a
leverage-based Excess Cash Flow (ECF) sweep — the mechanism that
determines how fast a lender actually gets repaid, distinct from the
scheduled mandatory amortization alone.

## Owner
unassigned

## Risk tier
Tier 1 (credit approval decision) for a populated instance sizing or
monitoring a real facility. The blank template is Tier 3 until populated.

## Methodology
- **Covenant headroom**: standard maintenance-covenant definitions —
  leverage (Total Debt/EBITDA), interest coverage (EBITDA/Interest), and
  DSCR (CFADS/Debt Service) — each compared to a threshold with a
  PASS/BREACH flag.
- **ECF sweep**: standard leveraged-loan credit-agreement provision. Excess
  Cash Flow = CFADS less scheduled debt service (interest + mandatory
  amortization); a step-down grid (75% / 50% / 25% / 0% of ECF, by
  beginning-of-period leverage tier) determines how much of that excess
  sweeps the balance down. This is the actual mechanism credit agreements
  use to accelerate repayment as a borrower delevers, distinct from static
  mandatory amortization.
- **Non-circularity**: both interest expense and the sweep-tier leverage
  are computed off the BEGINNING-of-period balance only (never that
  period's own ending balance), so the sweep can depend on interest and
  interest can depend on the balance without a circular reference — the
  same convention used throughout this repository's other debt schedules
  (LBO, Securitization).
- **Approximate YTM**: standard bond-math approximation for yield including
  OID, `(coupon$+(100-price)/n)/((100+price)/2)`.

## Conventions and units
USD. Annual periods, Yr0-Yr5. Leverage/coverage/DSCR expressed as
multiples (x). CFADS and EBITDA are flat scalars across the projection
(not separately grown), consistent with this workbook's single-scenario
scope.

## Material assumptions
- ECF sweep tier thresholds (4.0x/3.0x/2.0x) and percentages
  (75%/50%/25%/0%) are illustrative defaults — see the Sources sheet; a
  real facility's actual credit-agreement grid must replace them.
- Covenant thresholds (5.0x leverage, 2.5x interest coverage, 1.2x DSCR)
  are placeholder defaults, not any specific facility's real covenants.

## Boundary conditions / when this breaks
- The sweep-tier lookup treats leverage exactly at a tier threshold as
  belonging to the tier BELOW it (strict `>` comparison) — e.g., leverage
  of exactly 4.0x gets the 50% tier, not 75%. This matches how most
  step-down grids are drafted ("greater than X.Xx") but should be checked
  against the actual indenture language for a real facility.
- If CFADS is less than scheduled debt service, the sweep floors at zero
  (`MAX(...,0)`) rather than going negative — the facility does not
  self-cure a shortfall through this mechanism.

## Known limitations
- Single tranche only — no multi-tranche (first lien / second lien /
  unitranche) cascade the way the LBO archetype's debt schedule has.
- No PIK-toggle option or covenant-cure/equity-cure mechanics, both common
  in real direct-lending documentation.
- CFADS and EBITDA are flat scalars, not driven by an underlying operating
  projection.
- No populated instance yet — all numbers in the shipped template are
  illustrative defaults.

## When this model should not be used
Not a substitute for reviewing the actual credit agreement's covenant
definitions and ECF sweep mechanics, which vary significantly by deal
(different EBITDA add-backs, different sweep-grid structures, basket
carve-outs this model does not represent).

## Stakeholder perspectives represented
- **Lender**: covenant compliance and repayment speed via the sweep.
Not represented: **borrower's view of available liquidity/covenant
flexibility**, **rating agency recovery view**.

## Version
Built by `tools/builders/build_credit_template.py`. ECF sweep step-down
grid and the mandatory-amortization formula fix (previously read the OID
cell instead of the amortization-% cell) shipped alongside
`check_credit_ecf_sweep_stepdown` in `tools/verify_reference_calcs.py`.
