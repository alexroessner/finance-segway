# Model Card — Structured Finance / Securitization

## Decision this model is designed to support
Two linked questions about an asset-backed pool and its tranche structure:
(1) how does the collateral pool's cash flow cascade through a sequential-
pay tranche structure -- principal senior-to-junior, losses junior-to-
senior -- and what weighted-average life (WAL) and credit-enhancement
does each class actually get, and (2) -- the new addition -- how sensitive
is the pool's own WAL to the prepayment-SPEED assumption, expressed on the
industry-standard PSA (Public Securities Association / SIFMA) benchmark
ladder (50% through 300% PSA), not just a single flat CPR.

## Owner
unassigned

## Risk tier
Tier 1 (pricing / structuring decision) for a populated instance. Blank
template is Tier 3.

## Methodology
- **Collateral pool**: level-pay mortgage-style amortization (`Balance x
  (WAC/12) / (1-(1+WAC/12)^-WAM)`), with CPR-driven prepayment and CDR-
  driven default converted to monthly rates via the standard `1-(1-annual)
  ^(1/12)` conditional-to-monthly formula, and a fixed 3-month recovery lag
  on defaulted balances.
- **Tranche Cash Flow Waterfall**: sequential-pay cascade -- principal
  flows senior to junior (Class A first, then B, C, D, Equity), losses are
  allocated junior to senior (Equity absorbs first). Includes per-tranche
  WAL and a reconciliation section tying pool-level and tranche-level cash
  flow.
- **PSA Prepayment Sensitivity (the new addition)**: the standard SIFMA/
  PSA benchmark curve -- 100% PSA ramps CPR 0.2%/month from month 1,
  capping at 6% CPR at month 30 and holding flat thereafter; other speeds
  (50%, 150%, 200%, 300%) scale that same ramp proportionally at every
  month. Isolates the prepayment-speed effect on the pool's own WAL,
  independent of the default/loss mechanics on the waterfall tab, over a
  12-month test window.

## Conventions and units
USD. 12-month cash flow window on both the Tranche Cash Flow Waterfall and
PSA Prepayment Sensitivity tabs (a real deal's full WAM is far longer;
see Known Limitations). 5-tranche capital structure (Class A/B/C/D/Equity),
fixed at build time -- adding or removing tranches requires the builder's
row ranges to be regenerated, not just extended.

## Material assumptions
- All 12 test-window months sit on the RISING part of the PSA ramp (it
  doesn't flatten until month 30), so this workbook never exercises the
  flat-6%-CPR regime.
- Tranche face amounts are assumed (not enforced) to sum to the pool's
  initial balance -- the Reconciliation check and the per-tranche WAL
  check both depend on this being true; the model does not itself flag a
  capital structure that under- or over-tranches the pool.
- Sequential pay only. No pro-rata, shifting-interest, or PAC/companion
  structures.
- A single WAC/WAM applies to the whole pool -- no loan-level dispersion.

## Boundary conditions / when this breaks
- **Pool WAL is NOT guaranteed to fall monotonically as PSA speed rises**
  within this truncated 12-month window -- verified as a genuine
  mathematical property (not an arithmetic bug) during this validation
  pass; see validation.md. A higher speed multiplier amplifies how much
  prepayment DOLLARS grow across the ramp within the window, which can
  pull the weighted-average payoff month LATER even though the pool
  unambiguously shrinks faster in every month. Ending balance and total
  principal returned in the window ARE always monotonic in speed -- the
  Checks sheet tests the property that's actually guaranteed, not WAL
  directly.
- Under a realistic capital structure (senior tranche large relative to
  12 months of pool paydown), junior tranches will show "-" (undefined
  WAL) because they receive zero principal within the test window -- this
  is realistic sequential-pay behavior, not a formula error.
- All new-mechanic formulas guard non-numeric intermediate values via
  `IFERROR`.

## Known limitations
- **12-month window, not full deal life.** A real ABS/RMBS deal's WAM can
  run 25-30+ years; this workbook's per-tranche and PSA-sensitivity WAL
  figures are truncated to a 12-month illustrative window and will
  understate the true disclosure WAL for any tranche (especially
  subordinate ones) that keeps receiving principal past month 12.
  Documented directly on both sheets, not silently omitted.
- **Tranche total vs. pool balance is not enforced.** If a user sizes
  tranches to something other than the pool's initial balance, the
  Reconciliation and per-tranche-WAL Checks-sheet entries will no longer
  behave as designed (documented, not auto-corrected).
- No populated instance yet.
- Sequential pay only.

## When this model should not be used
Not a substitute for a full cash flow engine used in actual ABS/RMBS
structuring or pricing, which would model the full deal life (not a
12-month window), loan-level (not pool-level weighted-average)
prepayment/default behavior, and structures beyond sequential pay
(pro-rata, shifting interest, PAC/companion tranching) this workbook does
not attempt to represent.

## Stakeholder perspectives represented
- **Structurer / trading desk**: tranche WAL and credit enhancement,
  prepayment-speed sensitivity on pricing-relevant WAL.
Not represented: **rating agency cash flow stress view**, **servicer's
loan-level view**, **investor's OAS/prepayment-model view**.

## Version
Built by `tools/builders/build_securitization_template.py`. PSA
Prepayment Sensitivity tab shipped alongside
`check_securitization_psa_sensitivity` in
`tools/verify_reference_calcs.py` (joining the pre-existing
`check_securitization_tranche_waterfall`).
