# Model Card — Trade Finance (Working Capital Cycle, LC/Factoring, Dynamic Discounting, SCF)

## Decision this model is designed to support
Which financing channel is cheapest for a given working-capital need,
now across FIVE channels: letter of credit, factoring/invoice
discounting, a revolving credit line, the opportunity cost of forgoing
an early-payment trade discount, and supply chain finance (reverse
factoring).

## Owner
unassigned

## Risk tier
Tier 2 (material analysis / financing-channel decision support) for a
populated instance. Blank template is Tier 3.

## Methodology
- **Early-payment discount implied APR**: the classic corporate-finance
  formula, `(d/(1-d)) x (360/(net days - discount days))`, using the
  360-day-year convention that is the textbook standard for this specific
  calculation (not this repository's usual 365-day convention elsewhere)
  — chosen deliberately so the model reproduces the commonly-cited
  "2/10 net 30 ≈ 36.7% APR" benchmark exactly, not a slightly-different
  365-day variant that wouldn't match what anyone familiar with the
  textbook figure would expect.
- **Supply chain finance (reverse factoring)**: prices off the BUYER's
  (stronger, often investment-grade) credit rating rather than the
  supplier's own — the entire mechanical reason SCF/reverse-factoring
  programs exist and are cheaper than a supplier's standalone factoring
  arrangement.
- **LC, factoring, revolver, cash conversion cycle**: unchanged standard
  methodology from the prior build.

## Conventions and units
USD. The early-payment-discount formula uses a 360-day year (textbook
convention for THIS specific formula); all other rate annualizations in
this workbook use 365 days — noted explicitly so a reader doesn't assume
inconsistency is an error.

## Material assumptions
- SCF's discount rate is assumed to genuinely reflect the buyer's
  stronger credit — the model does not independently verify the buyer's
  credit rating or confirm the assumed rate is achievable.
- The 5-channel cost comparison is financing-cost-only; it explicitly
  does NOT weigh speed, collateral/covenant burden, or credit-risk
  transfer differences (LC shifts payment risk to the issuing bank;
  factoring can be structured non-recourse; SCF depends on the buyer
  maintaining its credit quality for the life of the program) — stated
  directly on the Financing Cost Comparison sheet.

## Boundary conditions / when this breaks
- The cheapest-channel comparison only declares a winner once all 5
  channels have real (non-blank) inputs — guarded so one populated
  channel doesn't beat four blanks by default.
- All ratio formulas guard division by zero with `IFERROR`.

## Known limitations
- No populated instance yet.
- SCF modeled as a single flat annualized rate; a real program may have
  a rate that varies by days-early-paid tier.
- No test case yet for the scenario where SCF is NOT cheaper than
  standalone factoring (e.g., a buyer with weak credit) — the reference
  check only exercises the "SCF wins" case.

## When this model should not be used
Not a substitute for the actual signed program terms with a bank or SCF
platform — real LC, factoring, and SCF agreements have fee structures,
minimum volumes, and tiered pricing this simplified flat-rate comparison
does not capture.

## Stakeholder perspectives represented
- **Treasury / working-capital manager**: which channel is cheapest.
Not represented: **buyer's balance-sheet view** of sponsoring an SCF
program, **bank/factor's own credit-risk pricing view**.

## Version
Built by `tools/builders/build_trade_finance_template.py`. Dynamic
Discounting & SCF tab shipped alongside
`check_trade_finance_dynamic_discounting` in
`tools/verify_reference_calcs.py`.
