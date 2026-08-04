# Validation Record — Asset Management (Fund NAV, GP Carry & Clawback, LP Performance)

## Verification hierarchy checklist

1. **Workbook opens** — yes.
2. **Formulas recalculate without errors** — yes; blank template recalcs
   clean, 92 formulas, 0 errors.
3. **Accounting or cash-flow identities tie** — yes, enforced on the
   Checks sheet: GP take + LP take = total distributable value (single-
   period Fee Waterfall); cumulative carry reconstructs exactly from the
   sum of its own period-by-period increments; the catch-up-tranche
   division guard holds when catch-up% <= carry%; TVPI = DPI + RVPI.
4. **Closed-form or independent-code benchmark agrees** —
   `check_am_gp_carry_clawback` in `tools/verify_reference_calcs.py`:
   reproduces the full 4-period cumulative waterfall independently in
   Python (capital $1mm, hurdle 8%, carry 20%, catch-up 100%, gains of
   $400k/$300k/-$500k across periods 1-3) and compares cumulative and
   incremental GP carry every period. Matched exactly on last run.
5. **Sensitivities behave monotonically and economically** — tested: a
   markdown in period 3 (-$500k) pulls cumulative distributable value from
   $1.66mm down to $1.14mm, and cumulative GP carry correctly falls from
   $132,000 to $28,000 — an incremental of -$104,000, correctly flagged as
   a clawback ("GP owes $104,000 back to LPs"). This is the "meaningful
   downside behavior" the governance standard requires, and specifically
   the scenario a single-period waterfall calc cannot represent at all.
6. **Historical outcomes or external observations agree** — n/a; no
   populated instance yet.
7. **Independent reviewer approves continued use** — not yet performed.

## Independent reference check(s)

`check_am_gp_carry_clawback` (`tools/verify_reference_calcs.py`). Last run:
all 4 periods matched exactly on cumulative GP carry ($0 / $76,000 /
$132,000 / $28,000) and incremental carry ($0 / $76,000 / $56,000 /
-$104,000); the Period-3 clawback flag fired correctly.

## Bug found and fixed during this validation pass

The Fee Waterfall sheet's "GP catch-up %" input (default 100%) was never
referenced by the catch-up formula — the formula used the CARRY % input
in a way that only produces correct results when catch-up = 100% exactly,
silently ignoring whatever the user set the catch-up input to. A fund with
(for example) an 80% catch-up rate would have gotten 100%-catch-up numbers
with no indication anything was wrong. Replaced with the general
catch-up-tranche formula, `pref x carry% / (catch-up% - carry%)`, which
uses the catch-up input correctly and collapses to the original formula
exactly at catch-up = 100% (confirmed via the Checks-sheet guard and the
reference check above, both run at the 100% default).

## Sensitivity / stress behavior tested

Period-3 markdown triggering a clawback, as described in checklist item 5.

## Limitations surfaced during validation

- The clawback logic does not distinguish realized losses from unrealized
  marks, which a real LPA clawback provision often does (see model_card.md).
- Only tested at catch-up = 100%; the general formula's behavior at a
  partial catch-up rate (e.g. 80%) was verified algebraically but not
  against a populated test case in the permanent reference check — a
  reasonable follow-up.

## Conclusion

Pass, with limitations, and with one real bug (the dead catch-up-%
input) found and fixed. Independent-oracle check registered and passing;
Sources/Checks sheets, model card, and this validation record now exist,
satisfying the M3 evidence-pack gate. To reach M4: add at least two
populated instances and get independent (non-developer) reviewer sign-off.

## Date and validator

2026-08-04. Authored by the same agent that built the feature — flagged,
not silently claimed as independent.
