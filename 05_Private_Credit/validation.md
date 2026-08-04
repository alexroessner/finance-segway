# Validation Record — Private Credit / Direct Lending

## Verification hierarchy checklist

1. **Workbook opens** — yes.
2. **Formulas recalculate without errors** — yes; blank template recalcs
   clean, 68 formulas, 0 errors.
3. **Accounting or cash-flow identities tie** — yes, enforced on the Checks
   sheet: ending balance = beginning − amort − sweep (ties to 0 on Yr5);
   the Yr1 beginning balance ties to Yr0's ending balance (roll-forward);
   Assumptions' total-debt figure ties to the Debt Schedule's Yr0 beginning
   balance; the ECF sweep never goes negative across the full 6-period
   schedule.
4. **Closed-form or independent-code benchmark agrees** —
   `check_credit_ecf_sweep_stepdown` in `tools/verify_reference_calcs.py`:
   reproduces the entire 6-period beginning balance / amortization /
   sweep-tier / interest / sweep / ending balance roll-forward
   independently in Python and compares every cell to the sheet's
   recalculated value. Matched exactly on last run (test inputs: $100mm
   drawn, 9.5% all-in rate, 1% mandatory amort, $25mm EBITDA, $20mm CFADS).
5. **Sensitivities behave monotonically and economically** — tested: as
   the balance amortizes and sweeps down across Yr0-Yr5, beginning-period
   leverage falls from 4.00x to 2.74x and the sweep tier correctly steps
   down from 50% to 25% partway through the schedule (crossing the 3.0x
   boundary) — confirmed the grid is mechanically wired, not decorative,
   by checking more than one tier is actually visited across the schedule.
   Also confirmed the full tier range (75%/50%/25%/0%) responds correctly
   to leverage inputs spanning above and below every threshold.
6. **Historical outcomes or external observations agree** — n/a; no
   populated instance yet.
7. **Independent reviewer approves continued use** — not yet performed;
   open item, same as every other model in this repository at this stage.

## Independent reference check(s)

`check_credit_ecf_sweep_stepdown` (`tools/verify_reference_calcs.py`).
Last run: all 6 periods (Yr0-Yr5) matched exactly on beginning balance,
sweep %, interest, cash sweep amount, and ending balance; confirmed the
tier set visited across the schedule is `{0.5, 0.25}` (not flat), i.e. the
step-down is mechanically real.

## Bug found and fixed during this validation pass

The mandatory-amortization formula (`Debt Schedule` row 7, and the DSCR
covenant formula on the `Covenants` sheet) referenced `Assumptions!C9` —
the OID/issue-price cell (~99) — instead of `Assumptions!C11`, the
mandatory-amortization-percent cell (~0.01). This inflated modeled
mandatory amortization by roughly 9,900x (e.g., $100mm drawn x 99 instead
of x 0.01), which on the old hardcoded-zero cash sweep silently produced a
wildly negative debt balance within one period — caught only once the ECF
sweep was wired and the schedule was actually exercised end-to-end with
real test inputs. Fixed in both locations; the reference check above now
pins the correct behavior as a permanent regression test.

## Sensitivity / stress behavior tested

Leverage-tier boundary behavior (75%/50%/25%/0% grid, tested at leverage
levels above, within, and below each threshold) and the multi-period
step-down as the facility naturally delevers, as described above.

## Limitations surfaced during validation

- The grid's strict `>` boundary convention (leverage exactly at a
  threshold gets the lower tier) should be confirmed against real
  indenture drafting conventions before use on an actual facility.
- CFADS and EBITDA being flat scalars means this cannot yet model a
  borrower whose cash generation is itself improving or deteriorating
  over the projection window.

## Conclusion

Pass, with limitations, and with one real bug found and fixed in this
pass (see above). Independent-oracle check registered and passing;
Sources/Checks sheets, model card, and this validation record now exist,
satisfying the M3 evidence-pack gate. To reach M4: add at least two
populated instances and get independent (non-developer) reviewer sign-off.

## Date and validator

2026-08-04. Authored by the same agent that built the feature — flagged,
not silently claimed as independent, consistent with every other
validation record in this repository at this stage.
