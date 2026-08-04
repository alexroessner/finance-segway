# Validation Record — Quant/Systematic (Returns, Statistical Significance, Position Sizing)

## Verification hierarchy checklist

1. **Workbook opens** — yes.
2. **Formulas recalculate without errors** — yes; blank template recalcs
   clean, 102 formulas, 0 errors (after fixing a `#NAME?` error found
   during this pass -- see Bug below).
3. **Accounting or cash-flow identities tie** — yes, enforced on the
   Checks sheet: the PSR z-statistic's sign always matches whether SR-hat
   beats the benchmark; MinTRL correctly returns "undefined" (not a
   misleadingly small number) when SR-hat doesn't exceed the benchmark;
   max drawdown is always <= 0; half-Kelly is exactly half of full Kelly.
4. **Closed-form or independent-code benchmark agrees** —
   `check_quant_psr_mintrl` in `tools/verify_reference_calcs.py`:
   independently replicates Excel's EXACT bias-corrected `SKEW`/`KURT`
   formulas (not scipy's, which uses a different bias correction) in pure
   Python, then computes skewness, excess kurtosis, periodic Sharpe, PSR
   z-statistic, PSR, and MinTRL for a 24-period synthetic return series.
   All six values matched the sheet's recalculated output within 1e-4 on
   last run.
5. **Sensitivities behave monotonically and economically** — tested: a
   sample with SR-hat well above the benchmark (0.38 vs. 0) still shows
   MinTRL (25.7 periods) exceeding the actual sample length (24 periods),
   correctly flagging the track record as "TOO SHORT -- treat SR-hat with
   caution" despite a superficially strong headline Sharpe — exactly the
   overconfidence PSR/MinTRL exist to catch.
6. **Historical outcomes or external observations agree** — n/a; no
   populated instance yet, and no comparison against a real manager's
   published track record.
7. **Independent reviewer approves continued use** — not yet performed.

## Independent reference check(s)

`check_quant_psr_mintrl` (`tools/verify_reference_calcs.py`). Last run
(24-period synthetic series, mean 1.5%/mo, std 3%/mo, rf 3%/yr): skew
sheet=-0.6815/ref=-0.6815, kurt sheet=-0.2370/ref=-0.2370, SR-hat
sheet=0.3804/ref=0.3804, PSR z sheet=1.5859/ref=1.5859, PSR
sheet=0.9436/ref=0.9436, MinTRL sheet=25.74/ref=25.74 — all matched.

## Bug found and fixed during this validation pass

The sheet initially used `NORM.S.DIST` and `NORM.S.INV` (the modern Excel
2010+ function names). Both produced `#NAME?` errors when recalculated by
LibreOffice via openpyxl-written files: these "future functions" require
an `_xlfn.` namespace prefix in the underlying XML that openpyxl does not
add automatically when writing a plain formula string. Diagnosed with a
minimal isolated test (a 4-cell workbook comparing all four function name
variants) before touching the real template, confirming `NORMSDIST`/
`NORMSINV` (the pre-2010 names) compute identical results without the
namespace issue. Switched both formulas; re-verified clean.

## Sensitivity / stress behavior tested

MinTRL-exceeds-sample-length flagging on a superficially strong Sharpe
ratio, as described in checklist item 5.

## Limitations surfaced during validation

- No test case yet for the autocorrelated-returns scenario where PSR/MinTRL
  are known to be overconfident (see model_card.md) -- flagged as a
  documented limitation rather than silently assumed away.

## Conclusion

Pass, with limitations, and with one real formula-compatibility bug found
and fixed (`#NAME?` from unsupported modern function names). Independent-
oracle check registered and passing; Sources/Checks sheets, model card,
and this validation record now exist, satisfying the M3 evidence-pack
gate. To reach M4: add at least two populated instances and get
independent (non-developer) reviewer sign-off.

## Date and validator

2026-08-04. Authored by the same agent that built the feature — flagged,
not silently claimed as independent.
