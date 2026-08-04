# Model Card — Microfinance (Portfolio Quality, Sustainability, Provisioning, True Cost of Credit)

## Decision this model is designed to support
Four linked questions: (1) how healthy is the loan portfolio (PAR30/PAR90,
write-off ratio), (2) is the MFI operationally and financially
self-sufficient (OSS/FSS), (3) is it adequately reserved against its own
aging-bucket risk profile, and (4) — the new addition — what is the TRUE
cost of credit to a borrower when the MFI quotes a "flat" rate, versus
the declining-balance rate that actually produces the same repayment
schedule. That last question is a genuine truth-in-lending/disclosure
issue in real microfinance markets, not just an academic curiosity.

## Owner
unassigned

## Risk tier
Tier 2 (material analysis / pricing-transparency decision support) for a
populated instance. Blank template is Tier 3.

## Methodology
- **Flat vs. declining-balance rate**: a flat-rate loan charges interest
  on the ORIGINAL principal every period, even as the borrower's actual
  balance amortizes down — this means the STATED rate materially
  understates the TRUE cost of credit. The model computes the flat-rate
  loan's equal installment, then finds the declining-balance periodic rate
  that would produce the SAME installment two ways: (a) the standard
  closed-form approximation cited in CGAP/MFTransparency pricing-
  transparency training materials (`2 x n x flat / (n+1)`), and (b) an
  exact 16-step bisection solve on the amortizing-loan installment
  identity, `P x r / (1 - (1+r)^-n) = installment`.
- **OSS/FSS**: standard SEEP Network/CGAP operational and financial
  self-sufficiency ratios; FSS is strictly the more conservative of the
  two (adds a positive imputed cost-of-capital term to the denominator).
- **PAR aging-bucket provisioning**: standard days-past-due tiering with
  increasing required reserve rates.

## Conventions and units
USD (or local-currency equivalent, currency-agnostic). Rates per period
(commonly monthly in microfinance); the effective-annual-rate conversion
on the Flat vs Declining Rate tab assumes monthly periods specifically —
adjust the compounding power if the loan's actual period isn't monthly.

## Material assumptions
- The bisection solve's search bracket is `[flat_rate, 4 x flat_rate]` —
  wide enough for typical microfinance term lengths (monthly, 6-36
  months) but not validated for extreme edge cases (very short terms,
  very high flat rates).
- 16 bisection steps give roughly 6 significant figures of precision on
  a bracket this size — more than sufficient for any practical use, and
  confirmed against an independently-coded fixed-point solve (a
  genuinely different numerical method) in the permanent reference check.

## Boundary conditions / when this breaks
- Requires flat_rate > 0 and n >= 1; the bisection bracket assumes the
  true declining-balance rate is between 1x and 4x the flat rate, which
  holds for realistic microfinance parameters but is not proven for all
  possible inputs.
- All ratio formulas guard division by zero with `IFERROR`.

## Known limitations
- No group-lending / joint-liability mechanics — the core risk-sharing
  innovation of classic (Grameen-style) microfinance, where a borrower
  group is collectively responsible for a defaulting member's obligation,
  is not modeled anywhere in this workbook.
- No populated instance yet.
- The effective-annual-rate conversion assumes monthly compounding
  specifically; a model card reviewer should confirm this matches the
  actual loan's period before quoting the annualized figure externally.

## When this model should not be used
Not a substitute for the specific jurisdiction's actual truth-in-lending
disclosure calculation methodology (APR calculation rules vary by
country) — this model computes a standard, defensible approximation and
an exact numerical solve of the SAME simplified model, not a
jurisdiction-specific regulatory APR.

## Stakeholder perspectives represented
- **MFI management**: portfolio quality, sustainability, reserve
  adequacy.
- **Borrower / consumer-protection view**: true cost of credit,
  surfaced directly rather than left implicit in a flat-rate quote.
Not represented: **funder/investor covenant view**, **regulator's
specific APR-calculation methodology**.

## Version
Built by `tools/builders/build_microfinance_template.py`. Flat vs
Declining Rate tab shipped alongside
`check_microfinance_flat_vs_declining` in
`tools/verify_reference_calcs.py`.
