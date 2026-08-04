# Validation Record — Real Estate / REIT (Pro Forma, Valuation, FFO/AFFO, Levered Hold, LP/GP Promote)

## Verification hierarchy checklist

1. **Workbook opens** — yes.
2. **Formulas recalculate without errors** — yes; blank template recalcs
   clean, 65 formulas, 0 errors.
3. **Accounting or cash-flow identities tie** — yes, enforced on the
   Checks sheet: LP + GP distribution conserves to total distributions;
   GP multiple exceeds LP's whenever there's a promote to earn; FFO=AFFO
   when both adjustment lines are zero; exit equity proceeds feed the
   levered-IRR terminal cash flow exactly.
4. **Closed-form or independent-code benchmark agrees** —
   `check_real_estate_lp_gp_promote` in `tools/verify_reference_calcs.py`:
   independently re-derives the full deal (NOI growth path, exit value,
   net exit equity, and the LP/GP waterfall) in Python and compares
   against the sheet's recalculated output for a test case ($45mm
   purchase, $27mm debt, 90/10 LP/GP, 8% pref, 20% promote). All matched
   exactly on last run.
5. **Sensitivities behave monotonically and economically** — tested: GP's
   equity multiple (2.27x) exceeds LP's (1.82x) on a profitable deal,
   confirming the promote is actually doing its job (disproportionate GP
   upside), checked as an explicit assertion rather than eyeballed.
6. **Historical outcomes or external observations agree** — n/a; no
   populated instance yet.
7. **Independent reviewer approves continued use** — not yet performed.

## Independent reference check(s)

`check_real_estate_lp_gp_promote` (`tools/verify_reference_calcs.py`).
Last run: total distributions, preferred-return target, residual profit,
LP total, and GP total all matched the independent Python re-derivation
exactly (e.g. LP total: sheet=$29,559,233 / ref=$29,559,233).

## Bug found and fixed during this validation pass

The FIRST version of the independent reference check had an off-by-one
error in its own NOI growth path: it applied growth starting in Year 1
(`noi0 * (1+g)^1` for Yr1), but the sheet's actual convention is that
Year 1 NOI is the CURRENT, un-grown stabilized figure, with growth
compounding starting in Year 2. This produced a mismatch on "total
distributions" (ref $34,975,915 vs. sheet $33,643,054) that traced
directly to the growth-path exponent, not a sheet formula problem.
Corrected the Python reference to use exponents 0-4 for Years 1-5
(matching the sheet's `C13, D13=C13*(1+g), E13=D13*(1+g), ...` chain)
and re-verified — exact match.

## Sensitivity / stress behavior tested

GP-multiple-exceeds-LP-multiple assertion on a profitable test deal, as
described in checklist item 5.

## Limitations surfaced during validation

- The compounded-pref, single-terminal-distribution approach is only
  valid for a single-purchase/single-sale deal structure (see
  model_card.md) — not tested against a multi-capital-call scenario.
- No catch-up tranche, by design — flagged as a structural limitation,
  not silently assumed universal.

## Conclusion

Pass, with limitations, and with one reference-check bug (an off-by-one
in the independent Python re-derivation, not the sheet itself) found and
fixed during validation. Independent-oracle check registered and passing;
Sources/Checks sheets, model card, and this validation record now exist,
satisfying the M3 evidence-pack gate. To reach M4: add at least two
populated instances and get independent (non-developer) reviewer sign-off.

## Date and validator

2026-08-04. Authored by the same agent that built the feature — flagged,
not silently claimed as independent.
