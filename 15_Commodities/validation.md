# Validation Record — Commodities (Futures Curve, Cost of Carry, Roll Yield, Hedging)

## Verification hierarchy checklist

1. **Workbook opens** — yes.
2. **Formulas recalculate without errors** — yes; blank template recalcs
   clean, 71 formulas, 0 errors.
3. **Accounting or cash-flow identities tie** — yes, enforced on the
   Checks sheet: the sum of absolute reprice-check residuals across all 5
   contract months is 0; unhedged and hedged P&L are both exactly 0 at a
   0% spot move; the curve-shape label matches the sign of the annualized
   basis.
4. **Closed-form or independent-code benchmark agrees** —
   `check_commodities_convenience_yield` in
   `tools/verify_reference_calcs.py`: reproduces the convenience-yield
   solve independently in Python (`y = r+u - ln(F/S)/T`) for a 5-point
   contango curve ($70/$71/$72/$74.50/$77 at 10/40/70/160/340 days) and
   confirms the reprice identity holds to within 1e-6 for every contract.
   Matched exactly on last run.
5. **Sensitivities behave monotonically and economically** — tested: for
   a strictly-rising (contango) curve, implied convenience yield is below
   r+u (5%+2%=7%) for every contract past the front month — economically
   correct, since contango means the market is NOT paying a premium for
   physical inventory. Confirmed as an explicit assertion in the reference
   check, not just eyeballed.
6. **Historical outcomes or external observations agree** — n/a; no
   populated instance yet, and this model doesn't (yet) compare implied
   convenience yield against any independently-published series.
7. **Independent reviewer approves continued use** — not yet performed.

## Independent reference check(s)

`check_commodities_convenience_yield` (`tools/verify_reference_calcs.py`).
Last run: all 5 contract months' implied convenience yield matched the
independent closed-form calculation exactly (e.g. M2: sheet=-0.0594,
ref=-0.0594), and the reprice identity reproduced each observed futures
price to within 1e-6.

## Sensitivity / stress behavior tested

Contango-curve convenience-yield sign check, as described in checklist
item 5.

## Limitations surfaced during validation

- The reprice-identity check validates internal arithmetic consistency,
  not economic reasonableness of the solved convenience yield — a
  deliberately mislabeled r or u input would still reprice exactly (see
  model_card.md's note on this).
- Only tested on a contango curve; a backwardation test case (where
  implied y should exceed r+u) is a reasonable follow-up for the
  permanent reference check.

## Conclusion

Pass, with limitations. Independent-oracle check registered and passing;
Sources/Checks sheets, model card, and this validation record now exist,
satisfying the M3 evidence-pack gate. To reach M4: add at least two
populated instances and get independent (non-developer) reviewer sign-off.

## Date and validator

2026-08-04. Authored by the same agent that built the feature — flagged,
not silently claimed as independent.
