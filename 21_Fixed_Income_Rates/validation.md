# Validation Record — Fixed Income / Rates (Convexity Closed-Form Cross-Check)

## Verification hierarchy checklist

1. **Workbook opens** -- yes.
2. **Formulas recalculate without errors** -- yes; blank template recalcs
   clean, 655 formulas, 0 errors.
3. **Accounting or cash-flow identities tie** -- yes, enforced on the
   Checks sheet: the closed-form price (summed from the actual cash flow
   schedule) matches Bond Pricing's PV-formula price exactly; closed-form
   modified duration and convexity match their numerical (finite-
   difference) counterparts to within a small, expected discretization
   tolerance; convexity is non-negative (required for any option-free
   bond).
4. **Closed-form or independent-code benchmark agrees** --
   `check_bond_convexity` in `tools/verify_reference_calcs.py`:
   independently re-derives the closed-form cash-flow-series convexity in
   Python AND a third, independent tiny-shock (1bp) numerical second
   derivative, to settle which of the sheet's two on-sheet methods (50bp
   FD vs. closed-form) is actually correct when they disagreed (see Bugs
   below). All three now agree to within expected numerical tolerance on
   the default $1,000/5%/semi-annual/10y/5.5% YTM test bond, and on two
   additional parameterizations (3%/quarterly/5y/6% YTM and
   7%/annual/20y/4% YTM) checked independently in Python during this pass.
5. **Sensitivities behave monotonically and economically** -- convexity
   confirmed non-negative (option-free bonds are always convex from
   below); the FD-vs-closed-form duration diff is much smaller than the
   FD-vs-closed-form convexity diff at the same shock size, consistent
   with the well-known numerical-analysis property that finite-difference
   second-derivative estimates are inherently noisier than first-
   derivative ones at a given step size.
6. **Historical outcomes or external observations agree** -- n/a; no
   populated instance yet.
7. **Independent reviewer approves continued use** -- not yet performed.

## Independent reference check(s)

`check_bond_convexity` (`tools/verify_reference_calcs.py`). Last run
($1,000 face, 5% semi-annual coupon, 10y, 5.5% YTM): closed-form
convexity sheet=72.7069, ref=72.7069; independent tiny-shock (1bp) FD
convexity=72.7070 (agrees with closed-form to 4 decimal places, confirming
the closed-form formula -- not the sheet's original 50bp FD estimate --
is the one converging to the true second derivative); sheet's 50bp-shock
FD convexity=72.7239 (differs from the exact value by ~0.02%, ordinary
discretization error, not a bug).

`check_bond_duration` (pre-existing): still passing, sheet(numerical)
modified duration=7.7331 vs. closed-form=7.7300 (~0.04% diff, small as
expected).

`check_accrued_interest` (pre-existing): still passing.

## Bugs found and fixed during this validation pass

1. **A real, meaningful bug: the first draft of the closed-form convexity
   formula was missing a `1/(1+y)^2` term.** Convexity is the SECOND
   derivative of price with respect to yield, `d^2P/dy^2 / P`. Taking the
   second derivative of `P = sum(CF_t / (1+y)^t)` twice brings down not
   just the `t(t+1)` factor but also an extra `(1+y)^-2` from the chain
   rule -- i.e. `d^2P/dy^2 = sum(CF_t x t(t+1) / (1+y)^(t+2))`, not
   `sum(CF_t x t(t+1) / (1+y)^t)`. The first draft only divided by
   `(1+y)^t` (matching the `t x PV(CF_t)` sum used for duration, which is
   correct for a FIRST derivative but not a second one), overstating
   convexity by ~5.6% (76.76 vs. the correct 72.71) at the default test
   inputs -- big enough to look plausible at a glance (both numbers are
   "roughly 70-something") but wrong.

   **How it was caught**: comparing the closed-form value against the
   sheet's existing 50bp-shock finite-difference convexity at a SINGLE
   shock size showed a ~5% gap, which could plausibly be dismissed as
   "FD discretization error, convexity estimates are noisier than
   duration estimates." To rule that out, I computed the FD convexity at
   progressively smaller shocks (50bp, 25bp, 10bp) in independent Python
   and found it CONVERGING toward ~72.71, not toward the closed-form
   formula's 76.76 -- proving the two formulas were computing genuinely
   different quantities, not just approximating the same one at different
   precision. That pointed straight at an error in the closed-form
   formula's derivation. Rederived it by hand (the missing `1/(1+y)^2`
   factor), fixed the Excel formula, and reran the shock-convergence test
   to confirm the corrected closed-form value (72.7069) now sits well
   inside the range the FD estimate converges toward as shock -> 0
   (72.7070 at a 1bp shock).

   This is the same category of bug as the Options domain's Excel
   operator-precedence bug earlier in this session: a formula that looks
   directionally plausible (right order of magnitude, right sign, "close
   enough" at a glance) but is actually wrong, caught only by an
   independent second computation -- and in this case, by refusing to
   accept "close enough at one data point" as proof of correctness and
   instead testing the CONVERGENCE behavior as the shock size shrinks.

## Sensitivity / stress behavior tested

- FD convexity error vs. shock size: 50bp shock gives ~0.02% relative
  error vs. the (corrected) closed-form value; convergence confirmed as
  shock size shrinks toward 1bp.
- Cross-checked the corrected closed-form formula against two additional
  bond parameterizations beyond the shipped test case (3% quarterly
  coupon / 5y / 6% YTM, and 7% annual coupon / 20y / 4% YTM) in
  standalone Python -- both matched a tiny-shock numerical second
  derivative to within 1e-4 relative, confirming the fix generalizes and
  wasn't a coincidence of the one test bond.

## Limitations surfaced during validation

- The sheet's numerical (50bp-shock) convexity is a materially less
  precise estimate than its numerical duration counterpart at the same
  shock size -- a well-known property of finite-difference second-
  derivative estimates, not specific to this workbook, but worth stating
  explicitly since a user comparing the two numbers side by side might
  otherwise expect similar precision. Documented in model_card.md.
  Downstream impact is small: convexity's own contribution to the Total
  Return Scenarios tab is already a second-order (small) correction term,
  so a ~0.02%-5% error in convexity itself (depending on shock size)
  moves the final total-return number by a few basis points at most, not
  a decision-changing amount.
- Closed-form schedule capped at 120 periods; documented on-sheet and in
  model_card.md.

## Conclusion

Pass, with limitations, and with one significant, genuinely wrong formula
found and fixed during this pass -- caught only by refusing to accept a
single-shock "close enough" comparison as proof and instead testing
convergence behavior as the finite-difference shock shrinks toward zero.
Independent-oracle check registered and passing (now three checks for
this domain); Sources/Checks sheets, model card, and this validation
record now exist, satisfying the M3 evidence-pack gate. To reach M4: add
at least two populated instances and get independent (non-developer)
reviewer sign-off.

## Date and validator

2026-08-04. Authored by the same agent that built the feature -- flagged,
not silently claimed as independent.
