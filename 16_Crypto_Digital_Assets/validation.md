# Validation Record — Crypto / Digital Assets (Tokenomics, Valuation, Staking, Perp Funding)

## Verification hierarchy checklist

1. **Workbook opens** — yes.
2. **Formulas recalculate without errors** — yes; blank template recalcs
   clean, 82 formulas, 0 errors (required adding `IFERROR` guards to the
   annualized-funding-rate and funding-income formulas, and to the
   corresponding Checks-sheet identity, after the first build produced
   `#VALUE!` errors on the blank template where spot price = 0).
3. **Accounting or cash-flow identities tie** — yes, enforced on the
   Checks sheet: the basis trade's net P&L across all 5 sensitivity moves
   sums to 0; annualized funding income ties to notional x annualized
   rate; allocation percentages sum to 100% of max supply (once
   populated); circulating supply never exceeds max supply in the
   emission schedule.
4. **Closed-form or independent-code benchmark agrees** —
   `check_crypto_perp_funding_basis` in `tools/verify_reference_calcs.py`:
   reproduces the premium, periods/year, annualized funding rate, funding
   received per interval, and annualized funding income independently in
   Python for a test case (perp $100.50, spot $100.00, 8h interval, $1mm
   notional). All matched exactly on last run.
5. **Sensitivities behave monotonically and economically** — tested: net
   P&L across a -20%/-10%/0%/+10%/+20% spot move is exactly 0 at every
   point, confirming the basis trade is genuinely delta-neutral by
   construction (long spot P&L and short perp P&L cancel exactly at each
   move) — this is the core claim the "Perp Funding & Basis" tab makes,
   and it's checked directly rather than merely asserted.
6. **Historical outcomes or external observations agree** — n/a; no
   populated instance, and no comparison against a real venue's published
   historical funding-rate series yet.
7. **Independent reviewer approves continued use** — not yet performed.

## Independent reference check(s)

`check_crypto_perp_funding_basis` (`tools/verify_reference_calcs.py`).
Last run: premium=0.0050, periods/yr=1095, annualized funding rate=5.475
(547.5% — a deliberately large stress test rate to make the mechanic
obvious), funding received/interval=$5,000, annualized funding
income=$5,475,000 — all matched the independent Python calculation
exactly, and all 5 delta-neutrality checks confirmed net P&L = 0.

## Sensitivity / stress behavior tested

Delta-neutrality across a 5-point price-move sweep, as described in
checklist item 5.

## Limitations surfaced during validation

- The funding-rate simplification (pure premium, no interest-rate
  component) means the annualized rate at small premiums will be somewhat
  understated relative to a real venue's published rate — flagged in
  model_card.md, not fixed, since it's a deliberate simplification.
- No test case yet for a NEGATIVE funding environment (perp below spot,
  longs receive) — the formula is symmetric and should handle it
  correctly, but this hasn't been exercised in the permanent reference
  check.

## Conclusion

Pass, with limitations. Independent-oracle check registered and passing;
Sources/Checks sheets, model card, and this validation record now exist,
satisfying the M3 evidence-pack gate. To reach M4: add at least two
populated instances and get independent (non-developer) reviewer sign-off.

## Date and validator

2026-08-04. Authored by the same agent that built the feature — flagged,
not silently claimed as independent.
