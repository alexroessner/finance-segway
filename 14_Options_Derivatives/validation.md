# Validation Record — Options & Derivatives (BS Pricer, Greeks, IV Solver, American Binomial)

## Verification hierarchy checklist

1. **Workbook opens** — yes.
2. **Formulas recalculate without errors** — yes; blank template recalcs
   clean, 326 formulas, 0 errors.
3. **Accounting or cash-flow identities tie** — yes, enforced on the
   Checks sheet: finite-difference Delta/Vega match closed-form; the IV
   solver's convergence (round-trip) check holds; put-call parity holds
   on the BS Pricer's own outputs.
4. **Closed-form or independent-code benchmark agrees** —
   `check_options_greeks_finite_difference` in
   `tools/verify_reference_calcs.py`: independently computes Delta,
   Gamma, Vega, and Theta in Python using the correct normal-density
   formula, and separately computes what the KNOWN-BUGGY (wrong exponent
   sign) version would have produced, asserting the sheet's Vega does
   NOT match the buggy value — a regression test specifically shaped to
   catch this exact bug class if it ever reappears, not just a generic
   "does it match" check.
5. **Sensitivities behave monotonically and economically** — n/a beyond
   the Greeks' own signs (Delta positive for calls/negative for puts,
   Gamma/Vega positive for both, Rho positive for calls/negative for
   puts) — all confirmed correct post-fix.
6. **Historical outcomes or external observations agree** — n/a; no
   populated instance, no comparison against real observed option
   Greeks from a market data provider.
7. **Independent reviewer approves continued use** — not yet performed.

## Bug found and fixed during this validation pass

**This is the most significant bug found in this repository this
session.** The Greeks tab's Gamma, Vega, and Theta formulas hand-rolled
the standard normal density as `EXP(-(d1)^2/2)/SQRT(2*PI())`. Excel
evaluates unary minus BEFORE exponentiation — `=-2^2` returns `4` in
Excel, not `-4` — so this formula actually computed `EXP(+d1^2/2)`
instead of `EXP(-d1^2/2)`: the leading minus bound to `d1` before the
squaring operation, and squaring a negative number erases its sign. The
same bug existed independently in the Implied Volatility solver's
internal Newton-Raphson vega term.

**Impact**: for the test case (S=K=$100, T=0.25yr, r=4.5%, vol=30%),
Vega was reported as 0.2017 instead of the correct 0.1972 — a ~2.3%
overstatement at this specific input combination, though the error
scales with `d1^2` and can be far larger away from at-the-money. Gamma
and Theta were similarly wrong. Delta and Rho were NOT affected — they
use `NORMSDIST` (the cumulative distribution function), which has no
such precedence ambiguity.

**How it was caught**: building the finite-difference cross-check
(bump-and-reprice using the FULL Black-Scholes formula via `NORMSDIST`,
not the buggy density shortcut) produced Vega values that didn't match
the closed-form Greeks tab. Tracing the discrepancy by hand (computing
d1, phi(d1), and the expected Vega independently) revealed the
closed-form sheet was reproducing `exp(+d1^2/2)` rather than
`exp(-d1^2/2)` — at which point the Excel operator-precedence rule
became the obvious explanation.

**Fix**: replaced every hand-rolled `EXP(-(x)^2/2)/SQRT(2*PI())` with
Excel's built-in `NORMDIST(x,0,1,FALSE)` density function, which has no
precedence trap. Re-verified: all Greeks now match finite-difference to
5-6 decimal places.

**Why this had gone undetected**: this workbook and its Greeks sheet
predate this session's independent-verification discipline — no check
had ever been registered for the Greeks or IV-solver tabs specifically
(only `check_black_scholes`, which only exercises the BS Pricer's
`NORMSDIST`-based call/put prices, and `check_american_option_binomial`,
which exercises the binomial tree — neither touches the Greeks tab's
formulas at all).

## Independent reference check(s)

`check_options_greeks_finite_difference` (`tools/verify_reference_calcs.py`).
Last run: Delta/Gamma/Vega/Theta (call) all matched an independent Python
re-derivation to within 1e-4, and the sheet's Vega was confirmed to NOT
match the pre-fix buggy computation.

## Limitations surfaced during validation

- The IV solver's FINAL converged output was likely correct even before
  the fix (Newton-Raphson is self-correcting on the price residual, and
  the sheet's own convergence check compares final price, not vega) —
  but this was not verified retroactively for the pre-fix version; only
  the post-fix version has been confirmed correct.

## Conclusion

Pass, with a significant real bug found and fixed (see above), fully
documented rather than silently patched. Independent-oracle check
registered and passing (now three checks for this domain); Sources/
Checks sheets, model card, and this validation record now exist,
satisfying the M3 evidence-pack gate. To reach M4: add at least two
populated instances and get independent (non-developer) reviewer
sign-off.

## Date and validator

2026-08-04. Authored by the same agent that built the feature — flagged,
not silently claimed as independent.
