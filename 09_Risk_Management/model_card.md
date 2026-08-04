# Model Card — Risk Management (VaR, Stress Scenarios, Portfolio VaR)

## Decision this model is designed to support
How much could this portfolio lose, measured three complementary ways:
(1) parametric VaR/Expected Shortfall (fast, assumes normal returns),
(2) historical VaR/CVaR from actual trailing P&L (no distributional
assumption, but only as good as the sample), and (3) multi-asset
correlation-weighted portfolio VaR with Euler component VaR (risk
budgeting/limit-setting across positions). The new addition — a direct
Parametric-vs-Historical comparison — answers a fourth question: is the
normality assumption underlying methods (1) and the correlation-based
method (3) actually understating this portfolio's real tail risk.

## Owner
unassigned

## Risk tier
Tier 1 (trading-risk-limit decision) for a populated instance. Blank
template is Tier 3.

## Methodology
- **Parametric VaR**: standard RiskMetrics-style Z x sigma x portfolio
  value, with an analytic Expected Shortfall formula under normality.
- **Historical VaR/CVaR**: standard non-parametric methodology using
  Excel's `PERCENTILE` (linear interpolation between closest ranks) and
  `AVERAGEIF` over trailing daily P&L — makes no distributional
  assumption, but is exactly as reliable as the underlying P&L sample.
- **Method Comparison (the new addition)**: a direct ratio of historical
  to parametric VaR. When the ratio exceeds 1x, it's a real, checkable
  signal — not a rounding difference — that the actual P&L history has
  fatter tails or more negative skew than a normal distribution predicts,
  and the parametric method (and by extension the correlation-based
  Portfolio VaR tab, which shares the same normality assumption) is
  understating tail risk.
- **Portfolio VaR (multi-asset)**: correlation-weighted variance
  aggregation with Euler-theorem component VaR — marginal contributions
  sum exactly to the total by mathematical identity, not approximation.

## Conventions and units
USD. 1-day VaR by default, scaled by sqrt(holding period) for N-day
(a simplification noted directly on the sheet — exact only under i.i.d.
returns).

## Material assumptions
- The historical P&L sample needs to be genuinely representative
  (100+ observations recommended) — a short or unrepresentative sample
  will produce a historical VaR that looks precise but isn't reliable.
- Stress scenario shocks (2008-style crash, rate shock, etc.) are
  illustrative placeholders, explicitly flagged on the sheet as needing
  calibration to the actual portfolio's beta/sensitivity before use.

## Boundary conditions / when this breaks
- `PERCENTILE`/`AVERAGEIF` formulas guard against an empty P&L sample
  via `IFERROR`.
- The Method Comparison ratio is only meaningful once BOTH methods have
  real inputs — on a blank or partially-populated template it resolves
  to "-" rather than a misleading number.

## Known limitations
- No Monte Carlo VaR — only parametric and historical methods.
- No populated instance yet.
- Portfolio VaR's explicit-sum variance formula is written for exactly
  3 positions; scaling to N positions would need the formula regenerated,
  not just more rows added.

## When this model should not be used
Not a substitute for a full risk system with real-time position feeds
and a validated historical database — this template is for periodic
(weekly/daily-in-stress) risk review with manually-entered snapshots,
not continuous intraday risk monitoring.

## Stakeholder perspectives represented
- **Risk manager / trading desk**: VaR, ES, stress scenarios, limit
  utilization via component VaR.
Not represented: **regulatory capital view** (this isn't a Basel-style
regulatory VaR/ES calculation), **counterparty credit risk view**.

## Version
Built by `tools/builders/build_risk_template.py`. Method Comparison rows
shipped alongside `check_risk_historical_vs_parametric_var` in
`tools/verify_reference_calcs.py` (joining the pre-existing
`check_portfolio_var`).
