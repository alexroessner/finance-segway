# Model Card — Options & Derivatives (BS Pricer, Greeks, IV Solver, American Binomial)

## Decision this model is designed to support
Four linked questions: (1) what is an option worth under Black-Scholes,
(2) how sensitive is that value to spot/vol/time/rate (Greeks), (3) given
an observed market price, what volatility does it imply, and (4) for an
American-style option (early exercise allowed), what is the correct
price and how much of it is the early-exercise premium Black-Scholes
structurally cannot capture.

## Owner
unassigned

## Risk tier
Tier 1 (trading/hedging decision) for a populated instance. Blank
template is Tier 3.

## Methodology
- **Black-Scholes pricer**: standard closed-form call/put pricing via
  `NORMSDIST` (Excel's built-in cumulative normal), which is why the
  pricer itself was never affected by the bug described below.
- **Greeks**: closed-form partial derivatives (Delta, Gamma, Vega, Theta,
  Rho), now computed via Excel's built-in `NORMDIST(x,0,1,FALSE)` density
  function rather than a hand-rolled `EXP(-x^2/2)/SQRT(2*PI())` — see
  Known Limitations / bug history below.
- **Greeks FD Check (the new tab)**: independently reproduces each Greek
  via finite-difference bump-and-reprice (perturb the input, reprice the
  FULL Black-Scholes formula from scratch, take the numerical
  derivative) — a genuinely different calculation method from calculus,
  the same way an options desk sanity-checks analytical Greeks in
  practice.
- **Implied volatility solver**: Newton-Raphson unrolled across 9 fixed
  columns (deterministic, no Excel iterative-calculation setting needed),
  seeded with the Brenner-Subrahmanyam closed-form approximation.
- **American option binomial tree**: 10-step Cox-Ross-Rubinstein lattice,
  with a European binomial value computed alongside as both a comparison
  and a cross-check against the closed-form Black-Scholes price.

## Conventions and units
Standard Black-Scholes notation (S, K, T, r, q, sigma). Vega expressed
per 1 percentage point of volatility; Rho per 1 percentage point of rate;
Theta per calendar day.

## Material assumptions
- Finite-difference bump sizes (default $0.01 for spot, 0.01pt for vol/
  rate, 0.0001yr for time) are fixed defaults tuned for typical
  at-the-money equity option inputs — they are not adaptively scaled to
  the magnitude of a populated instance's actual inputs.

## Boundary conditions / when this breaks
- **Bug found and fixed this pass**: Excel evaluates unary minus BEFORE
  exponentiation (`=-2^2` returns `4`, not `-4`) — a hand-rolled normal-
  density formula `EXP(-(d1)^2/2)` therefore silently computed
  `EXP(+d1^2/2)` instead of `EXP(-d1^2/2)`, because the negation bound to
  `d1` before squaring, and squaring erased the sign. This corrupted
  Gamma, Vega, and Theta (all three use the normal density) on both the
  Greeks tab and the Implied Volatility solver's internal Newton-Raphson
  vega term, for as long as those formulas existed in this repository —
  never caught because no independent check had ever verified the Greeks
  sheet. Fixed by switching to Excel's built-in `NORMDIST(x,0,1,FALSE)`
  density function, which has no such precedence ambiguity. Delta and Rho
  were never affected (they use `NORMSDIST`, the cumulative function, not
  a hand-rolled density).
- Finite-difference Gamma has the loosest tolerance of the five Greeks
  (second-derivative formulas are more sensitive to bump size) — noted
  directly on the sheet.

## Known limitations
- No populated instance yet.
- IV solver's final answer was likely unaffected by the precedence bug
  above (Newton-Raphson is self-correcting on the price residual even
  with an imperfect derivative term, and the convergence check compares
  final PRICE, not vega) — but the internal iteration dynamics were
  running on a wrong intermediate value regardless, now fixed.

## When this model should not be used
Not a substitute for a real options pricing/risk system with live market
data feeds — this is a single-scenario, manually-updated snapshot tool.

## Stakeholder perspectives represented
- **Options trader / hedger**: pricing, Greeks, implied vol.
Not represented: **market-maker's inventory/skew view** (single flat vol
input, no smile/skew surface), **margin/collateral view**.

## Version
Built by `tools/builders/build_options_template.py`. Greeks FD Check tab
and the NORMDIST precedence-bug fix shipped alongside
`check_options_greeks_finite_difference` in
`tools/verify_reference_calcs.py` (joining the pre-existing
`check_black_scholes` and `check_american_option_binomial`).
