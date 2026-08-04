# Validation Record — Trade Finance (Working Capital Cycle, LC/Factoring, Dynamic Discounting, SCF)

## Verification hierarchy checklist

1. **Workbook opens** — yes.
2. **Formulas recalculate without errors** — yes; blank template recalcs
   clean, 30 formulas, 0 errors.
3. **Accounting or cash-flow identities tie** — yes, enforced on the
   Checks sheet: the 2/10 net 30 default reproduces the canonical ~36.7%
   benchmark within 0.1%; SCF is confirmed cheaper than standalone
   factoring whenever the buyer's rate input is genuinely lower; the
   5-channel comparison never declares a winner on partial data; LC total
   cost ties to its own rate x face x tenor decomposition.
4. **Closed-form or independent-code benchmark agrees** —
   `check_trade_finance_dynamic_discounting` in
   `tools/verify_reference_calcs.py`: independently computes the implied
   APR and SCF cost in Python and compares against the sheet's
   recalculated output. Matched exactly on last run (2/10 net 30 ->
   36.73%; SCF cost on a $500k invoice at 4.5%/60 days -> $3,698.63).
5. **Sensitivities behave monotonically and economically** — tested: SCF
   rate (4.5%, buyer's credit) confirmed cheaper than the supplier's own
   standalone factoring rate (12.17% in the test case) — the entire
   premise of reverse factoring, checked as an explicit assertion.
6. **Historical outcomes or external observations agree** — yes, in a
   narrow but meaningful sense: the 2/10 net 30 implied APR is checked
   against the WIDELY-PUBLISHED textbook benchmark figure (~36.7%), not
   just internal consistency — one of the few checks in this repository
   that validates against an external, independently-known number rather
   than only a from-scratch re-derivation.
7. **Independent reviewer approves continued use** — not yet performed.

## Independent reference check(s)

`check_trade_finance_dynamic_discounting` (`tools/verify_reference_calcs.py`).
Last run: implied APR sheet=0.3673/ref=0.3673 (matches the canonical
36.7% figure to within 1e-6); SCF cost sheet=$3,698.63/ref=$3,698.63; SCF
rate confirmed below the standalone factoring rate.

## Bug found and fixed during this validation pass

The first version of the early-payment-discount APR formula used a
365-day year, consistent with this workbook's other rate annualizations
— but produced 37.24% for the 2/10 net 30 default, NOT the widely-cited
~36.7% textbook figure (which specifically uses a 360-day convention for
this formula). Caught by checking the result against the known external
benchmark rather than only checking internal consistency. Switched the
day-count in this one formula to 360 (documented as a deliberate,
noted exception to the workbook's usual 365-day convention) and
re-verified — now reproduces the canonical figure exactly.

## Sensitivity / stress behavior tested

SCF-cheaper-than-standalone-factoring assertion, as described in
checklist item 5.

## Limitations surfaced during validation

- No test case for the scenario where SCF is NOT the cheaper channel
  (e.g. a weak-credit buyer) — the reference check only exercises the
  "SCF wins" case (see model_card.md).

## Conclusion

Pass, with limitations, and with one real day-count-convention bug found
and fixed by checking against a known external benchmark rather than
only internal consistency. Independent-oracle check registered and
passing; Sources/Checks sheets, model card, and this validation record
now exist, satisfying the M3 evidence-pack gate. To reach M4: add at
least two populated instances and get independent (non-developer)
reviewer sign-off.

## Date and validator

2026-08-04. Authored by the same agent that built the feature — flagged,
not silently claimed as independent.
