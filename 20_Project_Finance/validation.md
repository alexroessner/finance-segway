# Validation Record — Project Finance (Construction, Sculpted Debt, DSRA)

## Verification hierarchy checklist

1. **Workbook opens** — yes.
2. **Formulas recalculate without errors** — yes; blank template recalcs
   clean, 112 formulas, 0 errors (required an `IFERROR` guard on one
   Checks-sheet formula after the first build produced a `#VALUE!` on the
   blank template).
3. **Accounting or cash-flow identities tie** — yes, enforced on the
   Checks sheet: ending balance ties to beginning minus principal
   repayment (Yr5); the roll-forward chains correctly (Yr2 beginning =
   Yr1 ending); DSRA draw never exceeds the required DSRA balance; the
   DSRA stress test confirms payment-default is avoided while the
   distribution-lock-up test still correctly fails in the shocked year.
4. **Closed-form or independent-code benchmark agrees** —
   `check_project_finance_dsra` in `tools/verify_reference_calcs.py`:
   independently re-derives the full 5-year sculpted debt schedule
   (beginning balance, interest, principal, ending balance) in Python and
   compares every year's ending balance to the sheet. Also independently
   re-derives the DSRA stress test's three outcomes (WITH-DSRA payability,
   WITHOUT-DSRA payability, and the lock-up test) and confirms they match.
   All matched exactly on last run.
5. **Sensitivities behave monotonically and economically** — tested: a
   30% CFADS shock in Year 3 without a DSRA produces a payment default
   (cash available < debt service); the SAME shock WITH a 6-month DSRA is
   fully paid (cash + draw >= debt service) but STILL fails the softer
   distribution-lock-up test (effective DSCR remains below the 1.30x
   target even with the reserve draw) — confirming the model captures the
   real, meaningfully different behavior of these two covenant triggers
   rather than collapsing them into one.
6. **Historical outcomes or external observations agree** — n/a; no
   populated instance yet.
7. **Independent reviewer approves continued use** — not yet performed.

## Independent reference check(s)

`check_project_finance_dsra` (`tools/verify_reference_calcs.py`). Last
run ($500mm project, 70% debt, 24-month construction, $80mm/yr revenue,
target DSCR 1.30x): all 5 years' ending balances matched exactly (e.g.
Yr1: sheet=$350,952,308 / ref=$350,952,308); the Yr3 stress test
confirmed WITH-DSRA="PAID IN FULL", WITHOUT-DSRA="PAYMENT DEFAULT",
lock-up="LOCKED UP" — all three matching the independent Python
derivation.

## Bug found and fixed during this validation pass

The first version of the "Sculpted DSCR ties exactly to target" Checks-
sheet formula compared the WRONG cells: `DSCR & Debt Sizing`'s row 7
(DSCR computed off a manually-entered debt-service input, independent of
the new sculpted schedule) against the target — a tautological
comparison of the wrong pair of numbers, and one that also produced
`#VALUE!` on the blank template. Replaced with a genuine roll-forward
identity (ending balance ties to beginning minus principal repayment) on
the actual Sculpted Debt Schedule sheet.

Separately, the DSRA stress test's first design compared the WITH-DSRA
and WITHOUT-DSRA outcomes both against the TARGET DSCR covenant, which
produced identical "BREACH" results in both cases for realistic test
inputs — DSRA restores cash up to the debt-service amount (DSCR=1.0x),
not up to the target covenant (1.30x), so it can never single-handedly
clear a target-DSCR test. Redesigned around the real distinction: payment
default (cash < debt service) vs. distribution lock-up (DSCR < target,
a materially different and lower-severity trigger) — this is both more
accurate and the more informative comparison.

## Sensitivity / stress behavior tested

Yr3 CFADS shock (-30%), WITH-DSRA vs. WITHOUT-DSRA vs. distribution-lock-up,
as described in checklist item 5.

## Limitations surfaced during validation

- DSRA replenishment after a draw is not modeled as a multi-year
  schedule (see model_card.md).
- The sculpting logic's "INFEASIBLE" guard (when sculpted debt service
  is less than the period's interest) has not been exercised in the
  permanent reference check with inputs that actually trigger it.

## Conclusion

Pass, with limitations, and with two real modeling bugs found and fixed
during this pass (a tautological/wrong-cell check, and a DSRA stress-test
design that couldn't have differentiated WITH from WITHOUT for any
realistic covenant level). Independent-oracle check registered and
passing; Sources/Checks sheets, model card, and this validation record
now exist, satisfying the M3 evidence-pack gate. To reach M4: add at
least two populated instances and get independent (non-developer)
reviewer sign-off.

## Date and validator

2026-08-04. Authored by the same agent that built the feature — flagged,
not silently claimed as independent.
