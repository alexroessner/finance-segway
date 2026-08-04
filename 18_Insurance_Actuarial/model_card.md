# Model Card — Insurance / Actuarial (Chain-Ladder, BF, Mack Method)

## Decision this model is designed to support
Three linked questions about loss reserving: (1) what is the point-
estimate ultimate loss and IBNR by accident year (chain-ladder), (2) does
blending in an independent a priori expected loss ratio change that
estimate for immature years (Bornhuetter-Ferguson), and (3) — the new
addition — how CONFIDENT should you be in the chain-ladder point
estimate, expressed as a standard error and a reserve range, not just a
single number (Mack method).

## Owner
unassigned

## Risk tier
Tier 1 (reserve adequacy decision) for a populated instance. Blank
template is Tier 3.

## Methodology
- **Chain-ladder**: standard volume-weighted age-to-age link factors and
  cumulative development factors (CDF) to ultimate.
- **Bornhuetter-Ferguson**: Bornhuetter & Ferguson (1972) — blends
  actual-reported-to-date with an independent a priori expected-loss-
  ratio-based IBNR estimate, converging exactly to chain-ladder at full
  maturity (CDF=1).
- **Mack method (the new addition)**: Mack (1993) — a distribution-free
  standard error for the chain-ladder reserve, derived purely from how
  much each accident year's own development factor scattered around the
  volume-weighted average link factor. No assumption about the
  underlying loss distribution (unlike a parametric bootstrap). Includes:
  - A **Completed Triangle** that projects the lower-right (unobserved)
    corner using the chain-ladder link factors — both a useful
    visualization and the direct source of the `C_{i,k}` terms Mack's
    formula needs for future development periods.
  - **Mack's own recommended extrapolation** for the thinnest development
    factor (only 1 accident year contributes, giving zero degrees of
    freedom): `sigma_{n-1}^2 = MIN(sigma_{n-2}^2, sigma_{n-3}^2,
    sigma_{n-2}^4/sigma_{n-3}^2)`.
  - A per-accident-year reserve range (`reserve +/- 1.96 x SE`, a normal
    approximation) and a total-reserve SE that is EXPLICITLY the simple
    sum-of-squares across accident years, not Mack's full total-reserve
    formula (see Known Limitations).

## Conventions and units
USD. 6 accident years x 6 development periods (a fixed triangle size);
scaling to a different triangle size would need the sheet's row/column
ranges regenerated, not just extended.

## Material assumptions
- The reserve range uses a normal (`+/-1.96 SE`) approximation for a
  ~95% interval — Mack's method gives the mean and standard error
  distribution-free, but the TRUE distribution of reserve outcomes is
  typically right-skewed (large adverse developments are more likely
  than the normal approximation implies), so the upper bound is probably
  understated relative to the true tail risk.
- Mack's last-link-factor extrapolation is a necessary approximation
  when only one accident year contributes to the thinnest development
  factor — not a full independent estimate.

## Boundary conditions / when this breaks
- All Mack Method formulas guard non-numeric intermediate values
  (blank-template "-" placeholders propagating from the underlying
  triangle) via `IFERROR`/`ISNUMBER` checks throughout.
- The fully-developed accident year (AY2020 in this 6x6 triangle) always
  has exactly zero reserve and zero Mack SE by construction — verified
  directly on the Checks sheet.

## Known limitations
- **Total reserve SE excludes the cross-accident-year covariance term.**
  Mack's full total-reserve formula includes a correlation term because
  different accident years' reserve errors share the same underlying
  `sigma_k^2` estimates (they're not independent) — this workbook reports
  only `sqrt(sum of individual accident-year MSEs)`, which UNDERSTATES
  the true total reserve volatility. Documented directly on the sheet,
  not silently omitted.
- No populated instance yet.
- Fixed 6x6 triangle size.

## When this model should not be used
Not a substitute for a full actuarial reserve opinion, which would use
multiple methods (chain-ladder, BF, Mack, bootstrap, GLM-based reserving)
triangulated together, account for the cross-accident-year covariance
this model explicitly omits, and reflect claims-specific knowledge
(large-loss development, reinsurance recoveries, claim-handling changes)
this purely mechanical triangle-based approach cannot see.

## Stakeholder perspectives represented
- **Reserving actuary / CFO**: point estimate + confidence in that
  estimate.
Not represented: **regulator's statutory reserve adequacy view**,
**reinsurer's ceded-reserve view**.

## Version
Built by `tools/builders/build_insurance_template.py`. Mack Method tab
shipped alongside `check_insurance_mack_method` in
`tools/verify_reference_calcs.py` (joining the pre-existing
`check_bornhuetter_ferguson`).
