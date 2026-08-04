# Validation Record — Insurance / Actuarial (Chain-Ladder, BF, Mack Method)

## Verification hierarchy checklist

1. **Workbook opens** — yes.
2. **Formulas recalculate without errors** — yes; blank template recalcs
   clean, 187 formulas, 0 errors (required multiple rounds of `IFERROR`/
   `ISNUMBER` guards across the new Mack Method sheet — see Bugs below).
3. **Accounting or cash-flow identities tie** — yes, enforced on the
   Checks sheet: BF converges to chain-ladder exactly at full maturity
   (AY2020); the fully-developed accident year's Mack reserve is exactly
   zero; the Completed Triangle's actual (non-projected) cells tie
   exactly to the source triangle; Mack SE is non-negative for every
   accident year.
4. **Closed-form or independent-code benchmark agrees** —
   `check_insurance_mack_method` in `tools/verify_reference_calcs.py`:
   independently re-derives the ENTIRE Mack cascade in Python (link
   factors, sigma_k^2 including the last-factor extrapolation, column
   sums S_k, the completed/projected triangle, and per-accident-year MSE)
   for a realistic 6x6 test triangle with genuine cross-accident-year
   variance. All 6 accident years' standard errors matched the sheet
   exactly on last run.
5. **Sensitivities behave monotonically and economically** — tested:
   Mack SE grows monotonically with immaturity (AY2020=0 -> AY2025=6.66,
   the least mature year), consistent with the intuition that less data
   means more uncertainty in the projection.
6. **Historical outcomes or external observations agree** — n/a; no
   populated instance yet.
7. **Independent reviewer approves continued use** — not yet performed.

## Independent reference check(s)

`check_insurance_mack_method` (`tools/verify_reference_calcs.py`). Last
run (realistic triangle with genuine variance: AY2020 100/150/175/190/
197/200, AY2021 110/170/200/215/222, etc.): every accident year's Mack
SE matched the independent Python re-derivation to within 1e-3 (e.g.
AY2025: sheet=6.6612, ref=6.6612).

`check_bornhuetter_ferguson` (pre-existing, from earlier in this
session): still passing.

## Bugs found and fixed during this validation pass

1. **My first test triangle was too clean to validate the new
   mechanic.** The synthetic triangle originally used elsewhere in this
   session (from the earlier Bornhuetter-Ferguson work) has every
   accident year developing by IDENTICAL proportional ratios — a
   deliberate simplification for that earlier check, but it makes every
   `sigma_k^2` exactly zero (no scatter around the mean link factor to
   measure), which trivially "passed" without exercising the actual
   variance-computation formulas. Caught by inspecting the sigma_k^2
   output and recognizing zero variance was suspicious, not a real
   validation result. Rebuilt with a triangle carrying genuine
   accident-year-to-accident-year variation and re-verified.

2. **Multiple `#VALUE!` errors on the blank template**, all from the
   same root cause: link factors and other intermediate values resolve
   to the text placeholder `"-"` (via `IFERROR`) when the underlying
   triangle is unpopulated, and several new Mack Method formulas
   (the last-factor sigma extrapolation, the projected/completed
   triangle cells, the per-accident-year MSE/lower/upper bounds, and one
   Checks-sheet formula) performed arithmetic directly on those cells
   without guarding for non-numeric input. Added `IFERROR`/`ISNUMBER`
   guards throughout; re-verified clean on both the blank template and
   the populated test case.

3. **A conceptual error in my own Sources/Checks design**, caught only
   once realistic (non-degenerate) test data was used: the original
   convergence check assumed BOTH AY2020 and AY2021 have CDF=1 (fully
   mature) — true only by coincidence in the old degenerate test
   triangle, where AY2020's specific Dev5->Dev6 ratio happened to equal
   exactly 1.0. In a 6-period triangle, only the accident year with ALL
   6 periods of data (AY2020) is guaranteed fully mature; AY2021 (5
   periods) is not, in general. Corrected the check to test only AY2020.

## Sensitivity / stress behavior tested

Mack SE growing monotonically with accident-year immaturity, as described
in checklist item 5.

## Limitations surfaced during validation

- Total reserve SE (sum-of-squares across accident years) is confirmed
  to understate the true total volatility, since it excludes the
  cross-accident-year covariance term — documented in model_card.md, not
  fixed (a full implementation would need substantially more formula
  complexity for a proportionally smaller accuracy gain at this stage).

## Conclusion

Pass, with limitations, and with three real issues found and fixed
during this pass (a too-clean test triangle that would have shipped an
unexercised mechanic, multiple blank-template formula errors, and a
conceptual bug in my own verification check). Independent-oracle check
registered and passing (now two checks for this domain); Sources/Checks
sheets, model card, and this validation record now exist, satisfying the
M3 evidence-pack gate. To reach M4: add at least two populated instances
and get independent (non-developer) reviewer sign-off.

## Date and validator

2026-08-04. Authored by the same agent that built the feature — flagged,
not silently claimed as independent.
