# Validation Record — Risk Management (VaR, Stress Scenarios, Portfolio VaR)

## Verification hierarchy checklist

1. **Workbook opens** — yes.
2. **Formulas recalculate without errors** — yes; blank template recalcs
   clean, 60 formulas, 0 errors.
3. **Accounting or cash-flow identities tie** — yes, enforced on the
   Checks sheet: component VaRs sum exactly to portfolio VaR (Euler's
   homogeneity theorem); diversification benefit is never negative;
   Expected Shortfall never falls below VaR at the same confidence;
   historical VaR is positive whenever the P&L sample has real losses.
4. **Closed-form or independent-code benchmark agrees** —
   `check_risk_historical_vs_parametric_var` in
   `tools/verify_reference_calcs.py`: independently replicates Excel's
   exact `PERCENTILE` linear-interpolation algorithm in Python (not
   scipy/numpy's percentile, whose interpolation can differ) and compares
   against the sheet's recalculated historical VaR/CVaR, plus an
   independent parametric-VaR calculation via `statistics.NormalDist`.
   All three matched exactly on a 100-observation fat-tailed synthetic
   P&L series (portfolio $10mm, 1.5% daily vol, 95% confidence).
5. **Sensitivities behave monotonically and economically** — tested
   directly: the fat-tailed P&L sample (5% of days include an extra
   -$400k tail event) produces historical VaR ($314,205) noticeably
   above parametric VaR ($246,728) — a 1.27x ratio, confirming the Method
   Comparison correctly surfaces when the normality assumption
   understates real tail risk. This is the core new claim, checked as an
   explicit assertion, not eyeballed.
6. **Historical outcomes or external observations agree** — n/a; no
   populated instance yet, and the P&L sample used for testing is
   synthetic, not a real trading book's history.
7. **Independent reviewer approves continued use** — not yet performed.

## Independent reference check(s)

`check_risk_historical_vs_parametric_var` (`tools/verify_reference_calcs.py`).
Last run: parametric VaR sheet=$246,728.04/ref=$246,728.04; historical
VaR sheet=$314,205.09/ref=$314,205.09; historical CVaR
sheet=$394,476.58/ref=$394,476.58 — all matched exactly; confirmed the
fat-tail sample makes historical VaR exceed parametric.

`check_portfolio_var` (pre-existing, from earlier in this session): still
passing — correlation-weighted portfolio VaR and Euler component VaR
match an independent Python re-implementation exactly.

## Sensitivity / stress behavior tested

Fat-tail P&L sample producing historical VaR > parametric VaR, as
described in checklist item 5.

## Limitations surfaced during validation

- Excel's `PERCENTILE` linear-interpolation algorithm needed to be
  replicated EXACTLY (not approximated via a different interpolation
  scheme) to get a clean match — a reminder that "independent
  re-implementation" sometimes means matching a specific software
  convention precisely, not just re-deriving the underlying statistic
  abstractly.
- No test yet for a THIN-tailed (historical VaR < parametric) sample —
  the reference check only exercises the fat-tail direction, which is
  the economically important one but not the only possible outcome.

## Conclusion

Pass, with limitations. Independent-oracle check registered and passing
(now two checks for this domain); Sources/Checks sheets, model card, and
this validation record now exist, satisfying the M3 evidence-pack gate.
To reach M4: add at least two populated instances and get independent
(non-developer) reviewer sign-off.

## Date and validator

2026-08-04. Authored by the same agent that built the feature — flagged,
not silently claimed as independent.
