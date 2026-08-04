# Model Card — Quant/Systematic (Returns, Statistical Significance, Position Sizing)

## Decision this model is designed to support
Three linked questions: (1) what are this strategy's risk-adjusted
returns (Sharpe, Sortino, max drawdown, CAPM alpha/beta), (2) — the new
addition — how CONFIDENT should you be in that headline Sharpe ratio
given the sample's length, skewness, and kurtosis (Statistical
Significance / PSR), and (3) how should a position actually be sized
given the strategy's estimated edge (Position Sizing / Kelly).

## Owner
unassigned

## Risk tier
Tier 2 (material analysis / manager-selection decision support) for a
populated instance. Blank template is Tier 3.

## Methodology
- **Probabilistic Sharpe Ratio (PSR)**: Bailey & Lopez de Prado (2012),
  "The Sharpe Ratio Efficient Frontier." Answers "what is the probability
  the TRUE Sharpe ratio exceeds a benchmark SR*," correcting the naive
  Sharpe estimate for sample length, skewness, and kurtosis — a short,
  skewed, fat-tailed track record needs a materially longer history to
  support the same confidence as a normally-distributed one.
- **Minimum Track Record Length (MinTRL)**: the companion diagnostic from
  the same paper — how many periods, AT THIS SAMPLE'S skew/kurtosis,
  would be needed to be confident (at a chosen confidence level) that the
  true Sharpe exceeds the benchmark.
- **Sharpe/Sortino/max drawdown/CAPM alpha-beta**: standard risk-adjusted
  performance measurement.
- **Kelly criterion**: standard edge-optimal position sizing,
  `W - (1-W)/R`; the sheet notes the practitioner convention of using
  1/4 to 1/2 Kelly rather than full Kelly.

## Conventions and units
Monthly return periodicity assumed throughout (annualization factors of
12 and sqrt(12)). PSR/MinTRL use the PERIODIC (monthly) Sharpe ratio, not
the annualized figure — mixing the two would give an incorrect z-statistic.

## Material assumptions
- PSR/MinTRL assume the return series is i.i.d. (independent, identically
  distributed) within the sample — a genuinely autocorrelated strategy
  (e.g. one holding illiquid positions with stale/smoothed marks) needs a
  further effective-sample-size correction this model does not apply.
- Excel's `SKEW`/`KURT` functions use a specific bias-corrected formula
  (matched exactly, not approximated, in the permanent reference check);
  other software's skewness/kurtosis functions can use slightly different
  bias corrections and won't tie exactly.

## Boundary conditions / when this breaks
- MinTRL is mathematically undefined when SR-hat does not exceed the
  benchmark SR* (the denominator term `(SR-hat - SR*)` would be zero or
  negative) — the sheet returns the literal string "undefined -- SR-hat
  must exceed SR*" rather than a nonsensical or misleadingly small number.
- `NORMSDIST`/`NORMSINV` (not `NORM.S.DIST`/`NORM.S.INV`) are used
  deliberately — the newer function names require XML namespace handling
  openpyxl doesn't add automatically, which produced `#NAME?` errors
  during this pass; the older names are functionally identical and
  universally supported.

## Known limitations
- No populated instance yet.
- Single-factor CAPM beta only — no multi-factor (Fama-French-style)
  regression.
- No autocorrelation adjustment for PSR/MinTRL (see Material Assumptions).

## When this model should not be used
Not a substitute for a full manager-due-diligence process — PSR/MinTRL
are diagnostics about STATISTICAL confidence in a Sharpe estimate, not a
judgment about strategy capacity, operational risk, or crowding.

## Stakeholder perspectives represented
- **Allocator / manager-selection view**: is this track record long
  enough to trust its headline Sharpe.
- **Trader / position-sizing view**: Kelly-based sizing.
Not represented: **operational due diligence view**, **liquidity/capacity
view**.

## Version
Built by `tools/builders/build_quant_template.py`. Statistical
Significance (PSR/MinTRL) tab shipped alongside `check_quant_psr_mintrl`
in `tools/verify_reference_calcs.py`.
