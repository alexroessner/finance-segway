# Model Card — Fintech / Payments (Unit Economics, Cohorts, Fraud Risk, Interchange)

## Decision this model is designed to support
Four linked questions: (1) is this fintech's customer unit economics
healthy (LTV/CAC, payback period), (2) what does actual cohort retention
look like vs. the steady-state churn assumption, (3) how exposed is the
business to fraud/chargeback/credit loss, and (4) — the new addition —
how much does the choice of issuing-bank partner (Durbin-regulated vs.
exempt) actually move interchange economics, which is the structural
reason many neobanks specifically choose a sub-$10B "sponsor bank."

## Owner
unassigned

## Risk tier
Tier 2 (material analysis / business-model decision support) for a
populated instance. Blank template is Tier 3.

## Methodology
- **Interchange economics**: implements the actual Reg II (Durbin
  Amendment) regulated-debit interchange cap (~$0.22 + 0.05% of
  transaction, folding in the optional $0.01 fraud-prevention adjustment)
  against the network-published unregulated rate available to issuers
  under the $10B-in-assets exemption threshold (~$0.04 + 1.65%). Computes
  the dollar and percentage advantage of exempt-bank interchange at a
  given average ticket size — directly, not just described.
- **Unit economics**: standard LTV (monthly revenue x gross margin x
  1/churn) and CAC payback.
- **Cohort retention**: an actual cohort-by-month retention grid,
  cross-referenced against the steady-state 1/churn LTV to flag when
  churn is front-loaded (the retention-curve LTV and the steady-state LTV
  diverge).
- **Fraud & risk**: fraud loss in bps of TPV (standard payments-industry
  convention), chargeback cost, and credit losses for a lending book.

## Conventions and units
USD. Interchange fees expressed per-transaction and as an effective % of
average ticket size. Fraud loss rate in bps (1bp = 0.01%).

## Material assumptions
- Interchange rates ($0.22+0.05% regulated, $0.04+1.65% exempt) are
  illustrative approximations of actual Reg II and network-published
  schedules — see the Sources sheet. A real card program's actual
  contracted rate can differ by network, card type, and merchant category.
- The interchange model assumes 100% debit-card volume; it does not model
  a mixed debit/credit TPV blend.

## Boundary conditions / when this breaks
- All interchange formulas guard division by average-transaction-size = 0
  with `IFERROR`.
- The exempt-vs-regulated advantage is ticket-size-dependent: it shrinks
  as average transaction size grows, since the fixed-fee component
  matters less relative to the ad-valorem component at high ticket sizes
  — noted directly on the sheet.

## Known limitations
- No populated instance yet.
- Does not model credit-card interchange (uncapped, network/issuer-set,
  materially different structure from debit).
- Does not model network fees (separate from interchange) or processor
  markup, which sit alongside interchange in a fintech's real cost stack.
- Fraud loss rate and chargeback cost are flat inputs, not a distribution.

## When this model should not be used
Not a substitute for the actual signed agreement with a card network and
issuing-bank partner — real interchange rates are negotiated and tiered by
merchant category code, card type, and program specifics that this
simplified two-scenario comparison does not capture.

## Stakeholder perspectives represented
- **Fintech operator**: unit economics, interchange strategy, fraud
  exposure.
Not represented: **issuing bank's own balance-sheet/capital view**,
**card network's view**, **regulator's view of exemption-threshold
structuring** (a real compliance/regulatory question this model
deliberately does not opine on beyond stating the rule).

## Version
Built by `tools/builders/build_fintech_template.py`. Interchange
Economics tab shipped alongside `check_fintech_interchange_durbin` in
`tools/verify_reference_calcs.py`.
