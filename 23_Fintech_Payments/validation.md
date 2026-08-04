# Validation Record — Fintech / Payments (Unit Economics, Cohorts, Fraud Risk, Interchange)

## Verification hierarchy checklist

1. **Workbook opens** — yes.
2. **Formulas recalculate without errors** — yes; blank template recalcs
   clean, 35 formulas, 0 errors.
3. **Accounting or cash-flow identities tie** — yes, enforced on the
   Checks sheet: interchange income computed as rate x TPV ties exactly
   to per-transaction-fee x transaction count for both the regulated and
   exempt scenarios; cohort M0 retention is always exactly 100%.
4. **Closed-form or independent-code benchmark agrees** —
   `check_fintech_interchange_durbin` in `tools/verify_reference_calcs.py`:
   reproduces transaction count, both scenarios' per-transaction fees, and
   both scenarios' interchange income independently in Python for a test
   case ($50mm TPV, $40 average ticket). All matched exactly on last run.
5. **Sensitivities behave monotonically and economically** — tested: at
   the $40 default ticket size, exempt interchange income ($875,000/mo)
   is confirmed to exceed regulated income ($300,000/mo) by more than 1.5x
   — the core economic claim of the tab, checked directly rather than
   merely described. The model card notes (and a future test could
   confirm) that this advantage should shrink as ticket size grows, since
   Reg II's fixed-fee component matters less at high ticket sizes.
6. **Historical outcomes or external observations agree** — n/a; no
   populated instance, and no comparison against a real issuer's actual
   contracted interchange rates yet.
7. **Independent reviewer approves continued use** — not yet performed.

## Independent reference check(s)

`check_fintech_interchange_durbin` (`tools/verify_reference_calcs.py`).
Last run: transaction count=1,250,000, regulated fee=$0.24 (income
$300,000/mo), exempt fee=$0.70 (income $875,000/mo) — all matched the
independent Python calculation exactly; exempt income confirmed >1.5x
regulated.

## Sensitivity / stress behavior tested

Exempt-vs-regulated interchange advantage at a $40 average ticket size,
as described in checklist item 5.

## Limitations surfaced during validation

- Only tested at one ticket size ($40); a test confirming the advantage
  shrinks (and eventually could reverse in relative terms) as ticket size
  grows toward the ad-valorem-dominated regime is a reasonable follow-up.
- Interchange rates are illustrative, not any specific card program's
  actual contracted schedule (see model_card.md).

## Conclusion

Pass, with limitations. Independent-oracle check registered and passing;
Sources/Checks sheets, model card, and this validation record now exist,
satisfying the M3 evidence-pack gate. To reach M4: add at least two
populated instances and get independent (non-developer) reviewer sign-off.

## Date and validator

2026-08-04. Authored by the same agent that built the feature — flagged,
not silently claimed as independent.
