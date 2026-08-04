# Validation Record — Distressed / Restructuring (Recovery Waterfall, EV Sensitivity, Liquidation vs. Reorg)

## Verification hierarchy checklist

1. **Workbook opens** — yes.
2. **Formulas recalculate without errors** — yes; blank template recalcs
   clean, 89 formulas, 0 errors.
3. **Accounting or cash-flow identities tie** — yes, enforced on the
   Checks sheet: the base-case (0% EV scenario) fulcrum on the sensitivity
   table matches the standalone Recovery Waterfall tab's own answer; the
   count of fully-recovered tranches is non-decreasing as EV rises;
   recovery % never exceeds 100% for any tranche at any EV scenario; the
   liquidation-vs-reorg comparison correctly picks the higher NPV.
4. **Closed-form or independent-code benchmark agrees** —
   `check_restructuring_ev_sensitivity` in
   `tools/verify_reference_calcs.py`: independently re-derives the full
   6-tranche waterfall at all 7 EV scenarios in Python (a 6-tranche
   capital structure: $50mm DIP / $200mm 1st lien / $100mm 2nd lien /
   $150mm senior unsecured / $75mm subordinated / equity) and compares
   every tranche's recovery % AND the identified fulcrum at every
   scenario. All 42 recovery-percent values and all 7 fulcrum
   identifications matched exactly on last run.
5. **Sensitivities behave monotonically and economically** — tested
   directly: the fulcrum climbs from First Lien Secured (at -40% EV) to
   Senior Unsecured Notes (base case) to Subordinated Debt (at +40% EV) —
   confirming the central claim of the tab, that the fulcrum moves toward
   more senior claims as EV falls and toward more junior claims as EV
   rises, exactly as bankruptcy/distressed-investing theory predicts.
6. **Historical outcomes or external observations agree** — n/a; no
   populated instance yet, and no comparison against a real case's actual
   contested valuation range.
7. **Independent reviewer approves continued use** — not yet performed.

## Independent reference check(s)

`check_restructuring_ev_sensitivity` (`tools/verify_reference_calcs.py`).
Last run: fulcrum at EV -40% ($240mm) = First Lien Secured; -20% ($320mm)
= Second Lien Secured; -10%/base/+10%/+20% = Senior Unsecured Notes;
+40% ($560mm) = Subordinated Debt — all matched the independent
Python re-derivation exactly, along with every tranche's recovery
percentage at every scenario.

## Sensitivity / stress behavior tested

The full fulcrum-shift behavior across a -40% to +40% EV range, as
described in checklist item 5 — this IS the sensitivity test the tab
exists to run, not a separate add-on.

## Bug found and fixed during this validation pass

The first version of the fulcrum-identification formula (a nested `IF`
chain across the 6 tranches, one per EV-scenario column) had a string-
concatenation bug: the Python code building the formula omitted commas
between successive nested `IF` clauses, producing a malformed formula
string like `...B9IF(AND(...` instead of `...B9,IF(AND(...`. Caught before
shipping by tracing through the generated formula string for a small
example rather than only recalculating and hoping for the best; fixed by
adding the missing trailing comma to each condition fragment.

## Limitations surfaced during validation

- No test case yet with a negotiated deviation from strict absolute
  priority (see model_card.md) -- the model doesn't support this case at
  all currently, which is a scope limitation, not a bug.
- The EV scenario range is symmetric and illustrative, not calibrated to
  any real case's actual disputed valuation range.

## Conclusion

Pass, with limitations, and with one formula-construction bug found and
fixed before shipping (not found live in a recalculation, since I traced
the generated formula string directly). Independent-oracle check
registered and passing; Sources/Checks sheets, model card, and this
validation record now exist, satisfying the M3 evidence-pack gate. To
reach M4: add at least two populated instances and get independent
(non-developer) reviewer sign-off.

## Date and validator

2026-08-04. Authored by the same agent that built the feature — flagged,
not silently claimed as independent.
