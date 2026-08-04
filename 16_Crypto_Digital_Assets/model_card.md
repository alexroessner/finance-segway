# Model Card — Crypto / Digital Assets (Tokenomics, Valuation, Staking, Perp Funding)

## Decision this model is designed to support
Four linked questions: (1) what is the token's supply schedule and current
dilution trajectory (Tokenomics, Supply Emission Schedule), (2) how is it
valued relative to on-chain activity (Valuation, Comparable Protocols),
(3) what's the real (non-inflationary) yield from staking (Staking Yield),
and (4) is there a delta-neutral carry opportunity in the perpetual
futures funding rate right now (Perp Funding & Basis) — a genuinely
crypto-native trade with no direct TradFi analogue in this repository.

## Owner
unassigned

## Risk tier
Tier 2 (material analysis / trading decision support) for a populated
instance. Blank template is Tier 3.

## Methodology
- **Perp funding rate**: simplified to the pure premium,
  `(Perp - Spot) / Spot`, the dominant component of the funding formulas
  most major venues actually use (which also add a small clamped
  interest-rate term this omits).
- **Cash-and-carry basis trade**: long spot + short an equal notional of
  perp is delta-neutral to the underlying's price by construction — the
  model demonstrates this directly with a 5-point price-move sensitivity
  table showing net P&L is exactly zero at every move, isolating funding
  income as the trade's actual return driver.
- **On-chain valuation multiples**: standard NVT, Mkt cap/TVL, FDV/TVL —
  crypto-native analogues to P/E and P/B, used relatively (vs. history or
  comps), not as an absolute valuation anchor.
- **Staking yield decomposition**: inflationary yield (new emissions
  diluting existing holders) vs. real yield (protocol fee revenue), net
  staking yield = real minus inflationary.

## Conventions and units
Token counts as raw units (not USD) in Tokenomics; USD for prices and
notional elsewhere. Funding periods annualized via `365 x 24 / interval_hours`.

## Material assumptions
- The basis trade assumes the perp tracks spot 1:1 in the sensitivity
  table (no basis change during the price move) — this isolates funding
  income cleanly for the demonstration, but a real position's basis can
  itself widen or narrow, which is the trade's actual risk (noted
  directly on the sheet).
- Emission schedule (Supply Emission Schedule tab) is a flat annual %,
  explicitly labeled a planning approximation — real unlocks are cliff +
  linear per allocation bucket.

## Boundary conditions / when this breaks
- All ratio/rate formulas guard division by zero (spot price = 0, e.g.)
  with `IFERROR`, returning "-" on a blank template rather than a formula
  error.
- The delta-neutral P&L identity assumes EQUAL notional on both legs; a
  mismatched hedge ratio would leave residual price exposure this sheet
  does not model.

## Known limitations
- No populated instance yet.
- Funding rate formula omits the interest-rate component real exchanges
  add (usually small relative to the premium, but not zero).
- No slashing-risk modeling for proof-of-stake staking (validator
  downtime/misbehavior penalties).
- No liquidation-risk modeling for the perp leg of the basis trade
  (margin calls if the exchange requires posting collateral against
  mark-to-market losses before the position is closed).

## When this model should not be used
Not a substitute for a real venue's actual funding-rate formula and
historical funding-rate volatility when sizing a live basis trade — the
simplified premium-only formula here is directional, not a production
pricing model, and says nothing about liquidation risk on the short-perp
leg.

## Stakeholder perspectives represented
- **Token holder**: dilution, staking yield.
- **Basis trader**: funding carry, delta-neutral P&L.
Not represented: **exchange/counterparty risk view**, **on-chain
governance/protocol-treasury view**.

## Version
Built by `tools/builders/build_crypto_template.py`. Perp Funding & Basis
tab shipped alongside `check_crypto_perp_funding_basis` in
`tools/verify_reference_calcs.py`.
