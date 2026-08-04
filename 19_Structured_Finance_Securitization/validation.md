# Validation Record — Structured Finance / Securitization (PSA Prepayment Sensitivity)

## Verification hierarchy checklist

1. **Workbook opens** -- yes.
2. **Formulas recalculate without errors** -- yes; blank template recalcs
   clean, 750 formulas, 0 errors.
3. **Accounting or cash-flow identities tie** -- yes, enforced on the
   Checks sheet: pool ending balance (month 12) falls monotonically as
   PSA speed rises; the pool-vs-tranche reconciliation ties to the
   recovery-lag-explained difference (~0); per-tranche WAL is
   non-decreasing senior to junior; credit enhancement % is non-decreasing
   senior to junior.
4. **Closed-form or independent-code benchmark agrees** --
   `check_securitization_psa_sensitivity` in
   `tools/verify_reference_calcs.py`: independently re-derives the ENTIRE
   PSA cascade in Python (CPR ramp, SMM conversion, level-pay scheduled
   principal, prepayment, ending balance) for all 5 PSA speeds x 12
   months, plus the summary WAL-by-speed table, against a $100mm pool
   (6.5% WAC, 360 WAM). 0 cell mismatches on last run. The pre-existing
   `check_securitization_tranche_waterfall` (pool CF + 5-tranche cascade +
   reconciliation) also still passes.
5. **Sensitivities behave monotonically and economically** -- tested and
   corrected during this pass (see Bugs below): ending balance and total
   principal returned in the 12-month window are confirmed monotonic in
   PSA speed; WAL itself is confirmed NOT monotonic in this truncated
   window, and that non-monotonicity was verified to be a genuine
   property of the model, not noise.
6. **Historical outcomes or external observations agree** -- n/a; no
   populated instance yet.
7. **Independent reviewer approves continued use** -- not yet performed.

## Independent reference check(s)

`check_securitization_psa_sensitivity` (`tools/verify_reference_calcs.py`).
Last run: WAL by speed (50%->300% PSA) = [0.6021, 0.6274, 0.6419, 0.6512,
0.6626] years -- increasing, matching the independent Python
re-derivation to 4 decimal places at every speed. Ending balance by speed
= [98223703, 97563983, 96903092, 96241005, 94913145] -- decreasing, as
expected. The Checks-sheet monotonic-ending-balance check reads `True`.

`check_securitization_tranche_waterfall` (pre-existing): still passing,
0 cell mismatches across pool + 5 tranches x 12 months.

## Bugs found and fixed during this validation pass

1. **A real bug: the Checks-sheet monotonic-WAL formula referenced the
   wrong sheet.** The original formula compared cells like `C46<=C47`
   with no sheet-name prefix -- inside the Checks sheet itself, those
   cells are empty, so the comparison was silently vacuous (always
   evaluating against blanks, not the PSA sheet's actual WAL values).
   Caught by inspecting the formula before first build, not by a failing
   recalc (a formula referencing the wrong sheet doesn't throw an error --
   it just silently checks the wrong thing). Fixed by explicitly
   prefixing every cell reference with `'PSA Prepayment Sensitivity'!`.

2. **A real bug: the per-tranche WAL Checks-sheet formula hardcoded the
   wrong row range.** It referenced `C40:C44`, left over from an earlier
   layout draft; the actual computed `wal_row0` variable (derived from
   the tranche block layout: `block0 + 5 tranches x 5 rows each + 2`)
   evaluates to row 46, so the real per-tranche WAL values live at rows
   46-50, not 40-44. C40:C44 in the built workbook are unrelated cells
   (part of the reconciliation section), so the check was comparing the
   wrong numbers entirely. Caught by re-deriving `wal_row0` by hand before
   building and cross-checking against the hardcoded literal. Fixed by
   using the `wal_row0` variable directly instead of a hardcoded literal,
   which also makes the check immune to future row-layout changes.

3. **A conceptual bug in my own Sources/Checks design, caught only by
   independent re-derivation, not by a recalc error: WAL is NOT
   guaranteed to fall monotonically as PSA speed rises within a truncated
   12-month window.** The original check asserted this (worded "faster
   prepayment always returns principal sooner, never later") and it
   FAILED on first real test data: WAL actually *increased* with PSA
   speed (0.602 yrs at 50% PSA up to 0.663 yrs at 300% PSA). Independently
   re-derived the full cascade in Python and got the identical increasing
   pattern -- confirming this is a real property of the model, not an
   arithmetic error. Mechanism: the PSA ramp itself is still rising
   throughout months 1-12 (it doesn't flatten until month 30), so a higher
   speed multiplier makes prepayment DOLLARS grow faster across the window
   than at low speed; that back-loads the weighted-average payoff month
   even though the pool is unambiguously shrinking faster every single
   month at higher speed. Total principal returned and ending balance ARE
   both always monotonic in speed (verified independently: total principal
   $1.78mm -> $5.09mm, ending balance $98.2mm -> $94.9mm, both strictly
   monotonic across all 5 speeds). Fixed by replacing the WAL-monotonicity
   check with an ending-balance-monotonicity check (which IS always true),
   and rewrote the explanatory note under the WAL table to state the real
   property instead of the incorrect one.

4. **A test-data gap, not a formula bug: the Waterfall sheet's tranche
   face amounts were still at their blank-template default of $0** on
   first population, which zeroed out every tranche's beginning balance
   and made the reconciliation check report an $87.6mm "difference"
   (comparing a real pool balance against a sum of five zeroed-out tranche
   balances) instead of ~0. Caught by inspecting the Checks-sheet output
   for an implausibly large number. Fixed by also populating the Waterfall
   sheet's 5 tranche face amounts (summing to the $100mm pool balance, the
   real-deal invariant the reconciliation check assumes) in the test
   harness -- not a change to the model itself.

## Sensitivity / stress behavior tested

- WAL increasing with PSA speed within the 12-month window (finding #3
  above) -- confirmed via independent re-derivation, not just eyeballed.
- Ending balance and total principal returned confirmed strictly
  monotonic in PSA speed across all 5 speeds (50%/100%/150%/200%/300%).
- Diagnostic-only: re-ran with a deliberately small tranche structure (all
  5 tranches sized to be paid down within the 12-month window, not
  shipped as the final test data) and confirmed per-tranche WAL comes out
  genuinely, non-vacuously monotonic (0.141 -> 0.300 -> 0.440 -> 0.544 ->
  0.761 years, Class A shortest to Equity longest) when tranches actually
  receive principal -- ruling out the concern that the shipped check
  (where junior tranches show "-" and trivially satisfy the comparison
  via Excel's text-greater-than-number ordering) is silently masking a
  real ordering bug.

## Limitations surfaced during validation

- Reconciliation and per-tranche WAL checks both silently assume tranche
  face totals equal the pool balance; the model does not itself validate
  that a user's inputs satisfy this. Documented in model_card.md, not
  fixed (would need an explicit new Checks-sheet entry).
- Under the realistic (shipped) tranche sizing, only Class A receives any
  principal within the 12-month test window -- B/C/D/Equity show "-".
  This is realistic sequential-pay behavior, not a defect, but it means
  the shipped per-tranche WAL check only meaningfully exercises 1 of 5
  tranches; robustness of the comparison logic for the other 4 was
  confirmed separately (see Sensitivity testing above), not by the
  shipped check itself.

## Conclusion

Pass, with limitations, and with four real issues found and fixed during
this pass (two silent wrong-cell-reference bugs in my own Checks-sheet
formulas, one incorrect economic claim in my own check design that a
recalc alone would never have caught, and one test-data gap that produced
an alarming but non-model false signal). Independent-oracle check
registered and passing (now two checks for this domain); Sources/Checks
sheets, model card, and this validation record now exist, satisfying the
M3 evidence-pack gate. To reach M4: add at least two populated instances
and get independent (non-developer) reviewer sign-off.

## Date and validator

2026-08-04. Authored by the same agent that built the feature -- flagged,
not silently claimed as independent.
