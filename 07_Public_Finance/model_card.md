# Model Card — Public Finance (DSA + Revenue Bond Coverage + Additional Bonds Test)

## Decision this model is designed to support
Two distinct decisions on one workbook, each with its own tab:

1. **Debt Sustainability sheet** — is an issuer's overall debt load on a
   stabilizing or explosive trajectory, given its current primary balance
   (IMF/DSA-style question, relevant to a sovereign or general-obligation
   credit view).
2. **Revenue Bond Coverage + Additional Bonds Test sheets** — can a specific
   revenue-backed bond issuer take on a proposed new tranche of parity debt
   without breaching its coverage covenant. This is the concrete go/no-go
   gate a municipal bond underwriter, trustee, or issuer's financial advisor
   actually has to clear before a new issuance can be priced.

## Owner
unassigned

## Risk tier
Tier 1 (credit approval / regulatory-adjacent decision) for a populated
instance used to size an actual proposed issuance. The blank template
itself is Tier 3 (demonstration) until populated with a real issuer's
audited financials and a real proposed issuance.

## Methodology
- **Debt sustainability**: standard IMF DSA debt-stabilizing primary balance
  identity, pb* = (r − g)/(1 + g) × debt ratio. Public-domain formula, not
  issuer-specific.
- **Revenue bond coverage**: net revenue (gross pledged revenue less
  operating & maintenance expense) divided by senior, then all-in, debt
  service — the standard muni-market DSCR definitions.
- **Additional Bonds Test (ABT)**: models a proposed new issuance's level
  debt service via Excel's native `PMT` function (current-interest, level
  P&I — the standard muni structuring convention), then runs two tests
  against the pro-forma total debt service (existing + new):
  - *Historical (look-back) test*: current-period net revenue against
    pro-forma debt service.
  - *Projected (look-forward) test*: a 5-year revenue/O&M projection under
    a Base/Stress growth-rate scenario switch (Cover!C9), checking that the
    minimum DSCR across all 5 years still clears covenant.
  Real bond indentures vary in whether they require passing one or both of
  these; this model computes both and lets the reviewer apply the specific
  indenture's rule.

## Conventions and units
USD. Annual periods. DSCR expressed as a multiple (x). Growth rates as
annual percentages. The projected test assumes existing debt service and
the new bond's debt service are both flat/level across the 5-year window
(true for level-debt-service structures, which is the default assumed
here).

## Material assumptions
- The ABT covenant level (default 1.25x) is a placeholder — see the Sources
  sheet; it must be replaced with the specific bond indenture's actual
  covenant before this is used for a real issuance decision.
- Existing debt service is assumed flat across the projection horizon.
- Revenue and O&M growth rates are single scalars per scenario (Base/Stress),
  not driven by an underlying operating model.

## Boundary conditions / when this breaks
- `PMT` requires coupon > 0 and term > 0; a zero-coupon or zero-term input
  produces a division-by-zero-guarded `"-"` rather than a formula error.
- The Debt Sustainability trajectory rule (`r >= g` implies explosive
  dynamics absent an adequate primary balance) is a first-order
  approximation — it ignores stock-flow adjustments, FX-denominated debt,
  and contingent liabilities, as noted directly on that sheet.

## Known limitations
- Single instrument only — does not aggregate a full debt portfolio with
  staggered maturities and multiple outstanding series.
- Level debt service (PMT) only — does not model capital-appreciation
  bonds, deferred-interest structures, or non-level amortization.
- No populated instance yet; all numbers in the shipped template are
  illustrative defaults, not a real issuer's financials.
- Does not model debt service reserve funds (DSRF) or reserve-fund
  surety mechanics common in revenue bond indentures.

## When this model should not be used
Not a substitute for the issuer's actual bond counsel review of the
indenture's specific ABT covenant language — this model computes the
standard historical/projected test pattern, but real indentures sometimes
add issuer-specific carve-outs (e.g., rate covenants, additional coverage
tests tied to specific revenue sub-categories) this model does not capture.

## Stakeholder perspectives represented
- **Issuer / financial advisor**: can we issue this bond (ABT pass/fail).
- **Rating agency / trustee**: coverage trajectory under stress.
Not represented: **bondholder secondary-market pricing view**, **taxpayer
burden view** on the DSA side beyond the raw debt-to-GDP trajectory.

## Version
Built by `tools/builders/build_public_finance_template.py`, ABT added
alongside `check_public_finance_additional_bonds_test` in
`tools/verify_reference_calcs.py`.
