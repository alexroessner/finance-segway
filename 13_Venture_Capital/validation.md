# Validation Record — Venture Capital (Cap Table, Rounds, SAFE, Exit Waterfall, Participating Preferred)

## Verification hierarchy checklist

1. **Workbook opens** — yes.
2. **Formulas recalculate without errors** — yes; blank template recalcs
   clean, 99 formulas, 0 errors.
3. **Accounting or cash-flow identities tie** — yes, enforced on the
   Checks sheet: capped payout never exceeds the cap; both regimes
   (take-pref-and-participate, convert-to-common) are actually exercised
   across the exit-value sweep, not just theoretically possible; the
   pre-existing Exit Waterfall total-distributed check still ties to
   total proceeds.
4. **Closed-form or independent-code benchmark agrees** —
   `check_vc_participating_preferred_cap` in
   `tools/verify_reference_calcs.py`: independently re-derives the
   capped-participating-preferred payout at all 7 exit-value points in
   Python ($10mm invested, 1x pref, 3x cap, 20% ownership) and compares
   both the payout AND the election (take pref vs. convert) against the
   sheet. All 7 points matched exactly on last run, alongside the
   pre-existing `check_vc_waterfall_conservation` for the main Exit
   Waterfall tab.
5. **Sensitivities behave monotonically and economically** — tested
   directly: at low exit values ($20mm-$100mm) the holder rationally
   takes pref+participation; at the crossover ($150mm, where capped
   payout exactly equals as-converted) and above, the holder converts to
   common — confirming the cap's actual economic function (bounding
   preferred's upside) is mechanically represented, not just labeled.
6. **Historical outcomes or external observations agree** — n/a; no
   populated instance yet.
7. **Independent reviewer approves continued use** — not yet performed.

## Independent reference check(s)

`check_vc_participating_preferred_cap` (`tools/verify_reference_calcs.py`).
Last run: all 7 exit-value points ($20mm through $500mm) matched exactly
on payout and election; confirmed both regimes are hit within the sweep
(not just one, which would mean the cap was never actually tested).

`check_vc_waterfall_conservation` (pre-existing, from an earlier session
pass): still passing — small-exit (pref-stack regime) and large-exit
(as-converted regime) both conserve to total proceeds exactly.

## Sensitivity / stress behavior tested

Full payout-kink sweep across 7 exit values, as described in checklist
item 5.

## Limitations surfaced during validation

- The single-class participating-preferred model isn't integrated with
  the multi-class Exit Waterfall tab — a cap table with both preference
  types simultaneously needs both tabs reasoned about together, not one
  combined calculation (see model_card.md).
- No test case for a participating-preferred class with NO cap
  (uncapped participation) — the model supports arbitrarily large cap
  inputs as a workaround, but this hasn't been exercised in the
  permanent reference check.

## Conclusion

Pass, with limitations. Independent-oracle check registered and passing
(now two checks for this domain); Sources/Checks sheets, model card, and
this validation record now exist, satisfying the M3 evidence-pack gate.
To reach M4: add at least two populated instances and get independent
(non-developer) reviewer sign-off.

## Date and validator

2026-08-04. Authored by the same agent that built the feature — flagged,
not silently claimed as independent.
