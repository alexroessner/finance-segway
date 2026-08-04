# Model Card — Commodities (Futures Curve, Cost of Carry, Roll Yield, Hedging)

## Decision this model is designed to support
Two linked questions: (1) what does the observed futures curve imply about
the market's convenience yield for holding physical inventory right now
(the Cost of Carry tab — explains WHY the curve is shaped as it is, not
just whether it's contango or backwardation), and (2) for a producer or
consumer with physical exposure, how many futures contracts hedge it and
what's the resulting unhedged basis risk (the Hedging tab).

## Owner
unassigned

## Risk tier
Tier 2 (material analysis / hedging decision support) for a populated
instance. Blank template is Tier 3.

## Methodology
- **Futures curve shape**: contango/backwardation classified by comparing
  each contract's price to the front month; annualized basis uses the
  GAP between each contract's own expiry and the front month's expiry
  (not each contract's own days-to-expiry from today), a bug fixed
  earlier in this repository's history.
- **Cost of carry / convenience yield**: standard theory-of-storage model,
  F = S x e^((r+u-y)T). Given the market's own OBSERVED futures price at
  each maturity, solves for y directly (`y = r+u - ln(F/S)/T`) rather than
  assuming a value — the convenience yield is backed out from market
  prices, not asserted.
- **Roll yield**: standard practitioner approximation, expiring-contract
  price over next-contract price minus 1.
- **Hedging**: standard futures hedge-ratio sizing, contracts needed =
  physical exposure x hedge ratio / contract size.

## Conventions and units
Prices per unit (currency-agnostic). Days to expiry in calendar days;
T = days/365. Rates and yields annualized, continuously compounded for
the cost-of-carry model specifically (to keep the closed-form solve for y
exact).

## Material assumptions
- The Cost of Carry tab's "Spot price" input is a distinct field, but it's
  commonly set equal to the front-month futures price as a practical
  proxy — true spot (physical, immediate delivery) can differ from M1
  futures, especially for commodities with high storage costs or delivery
  logistics frictions.
- Storage cost is a single annualized % of spot, not a curve — real
  storage costs are often seasonal (e.g. natural gas, grains).

## Boundary conditions / when this breaks
- The convenience-yield solve requires T > 0, spot > 0, and observed
  price > 0; guarded to return "-" otherwise rather than a division error
  or `LN` of a non-positive number.
- The reprice identity (`S x e^((r+u-y)T)` reproducing the observed price
  exactly) holds BY CONSTRUCTION for every contract — it is a solved
  identity, not an independent forecast; it validates the arithmetic, not
  whether r, u, or the resulting y are economically reasonable.

## Known limitations
- No populated instance yet.
- Convenience yield is a point estimate per contract month, not a fitted
  term-structure model (e.g. no smoothing or interpolation between
  observed maturities).
- Roll yield uses only the front two contracts, not a full weighted-roll
  schedule (e.g. Goldman-roll-style multi-day rolls).

## When this model should not be used
Not a substitute for a proper term-structure / seasonality model for
commodities with pronounced seasonal storage economics (natural gas,
agricultural products around harvest) — the single annualized storage-cost
input here is a simplification that can materially misstate convenience
yield for those commodities.

## Stakeholder perspectives represented
- **Trader / curve analyst**: convenience yield and curve shape.
- **Producer/consumer hedger**: contracts needed, unhedged basis exposure.
Not represented: **exchange/clearinghouse margin/liquidity view**.

## Version
Built by `tools/builders/build_commodities_template.py`. Cost of Carry
tab shipped alongside `check_commodities_convenience_yield` in
`tools/verify_reference_calcs.py`.
