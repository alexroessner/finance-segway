# Model Card — Asset Management (Fund NAV, GP Carry & Clawback, LP Performance)

## Decision this model is designed to support
Three linked questions for a fund's LP reporting and GP economics:
1. **Fund NAV** — what is the fund's NAV roll-forward this period.
2. **GP Carry & Clawback** — how much carried interest has the GP actually
   earned on a cumulative, whole-fund basis, and does a later markdown
   create a clawback obligation the GP must return to LPs.
3. **Fund Performance** — the headline LP-reporting metrics (TVPI, DPI,
   RVPI, net IRR).

## Owner
unassigned

## Risk tier
Tier 2 (material analysis / LP reporting) for a populated instance.
The blank template is Tier 3 until populated with a real fund's cash flows.

## Methodology
- **Waterfall structure**: standard private-fund LPA mechanics — return of
  capital, preferred return (hurdle), GP catch-up, then a carry split on
  the remainder.
- **General catch-up formula**: the pre-existing single-period Fee
  Waterfall sheet had a "GP catch-up %" input that was never actually used
  in the formula — the catch-up tranche was hardcoded to the standard
  100%-catch-up shape (`pref x carry% / (1 - carry%)`) regardless of what
  the user set that input to. Replaced with the general form,
  `pref x carry% / (catch-up% - carry%)`, which reduces to the same
  formula at catch-up% = 100% and actually splits the catch-up tranche
  between GP and LP when the catch-up rate is below 100% (common in some
  fund structures).
- **Whole-fund (European) waterfall with clawback**: the new GP Carry &
  Clawback sheet re-runs the identical waterfall formula CUMULATIVELY
  through each period (using cumulative capital contributed and cumulative
  net gains-to-date as the basis, not each period's isolated figures).
  Incremental GP carry each period = this period's cumulative carry minus
  last period's. When cumulative profit falls (a markdown), the
  cumulative carry recomputation can fall too, making the incremental
  figure negative — a clawback, flagged explicitly. This is what a
  whole-fund/European waterfall structurally IS; a single-period
  (American/deal-by-deal-style) calc can never show a clawback because it
  never looks at cumulative performance.

## Conventions and units
USD. Periods are unlabeled/undated (Period 0-3) — periodic IRR treats them
as evenly spaced.

## Material assumptions
- Fee terms (2% management fee, 8% hurdle, 20% carry, 100% catch-up) are
  illustrative industry-standard defaults, not any specific LPA's actual
  terms — see the Sources sheet.
- "Cumulative net gains" for the whole-fund waterfall = cumulative
  (realized/unrealized gains − fees), not distinguishing realized from
  unrealized (a real clawback provision often only claws back based on
  REALIZED losses, not marks — see Known Limitations).

## Boundary conditions / when this breaks
- If catch-up % <= carry %, the catch-up tranche formula is undefined
  (division by a non-positive number) — guarded explicitly to return 0 in
  that case (see the Checks sheet).
- The clawback flag only fires when incremental carry actually goes
  negative; a merely SLOWER rate of carry accrual (still positive
  incremental) is not a clawback.

## Known limitations
- Whole-fund/European structure only — does not model a deal-by-deal
  (American) structure, which many US buyout funds actually use and which
  has different (generally more GP-favorable, no cross-fund clawback)
  economics.
- Clawback is computed on cumulative gains including UNREALIZED marks; a
  real fund's LPA clawback provision often triggers only on realized
  losses at the end of the fund's life (with an interim true-up), which
  this model does not distinguish.
- No populated instance yet.
- No fund-level expenses (organizational costs, fund-level debt) modeled.

## When this model should not be used
Not a substitute for the specific LPA's actual waterfall mechanics, which
vary meaningfully by fund (deal-by-deal vs. whole-fund, clawback true-up
timing and interest, GP tax distributions netted against clawback).

## Stakeholder perspectives represented
- **GP**: carry earned and at-risk-of-clawback.
- **LP / investment committee**: TVPI/DPI/RVPI, net IRR, and the clawback
  protection this structure provides.
Not represented: **fund administrator's tax-basis view** of carry (often
differs from the economic view modeled here).

## Version
Built by `tools/builders/build_am_template.py`. GP Carry & Clawback sheet
and the catch-up-formula fix shipped alongside `check_am_gp_carry_clawback`
in `tools/verify_reference_calcs.py`.
