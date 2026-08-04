<!--
Template for <domain>/model_card.md, per docs/MODEL_GOVERNANCE_STANDARD.md's
M3 evidence pack. Copy into the domain folder and fill in every section --
an unfilled section is worse than an absent card, because it looks complete.
-->

# Model Card — [Archetype Name]

## Decision this model is designed to support
[What real decision does a populated instance of this model inform? Be specific
about the decision, not the topic -- "supports go/no-go on a proposed bond
issuance's additional-bonds-test covenant," not "public finance analysis."]

## Owner
[Named owner. "unassigned" is honest but should not be permanent.]

## Risk tier
[Tier 1 / 2 / 3, per docs/MODEL_GOVERNANCE_STANDARD.md, for a populated
instance used for its intended decision.]

## Methodology
[The economic/financial theory being implemented, and why this methodology
was chosen over alternatives. Cite the standard practitioner reference where
one exists (e.g. "IMF DSA framework," "level-debt-service PMT amortization,"
"Bornhuetter-Ferguson, standard actuarial reserving practice").]

## Conventions and units
[Day-count convention, currency, sign conventions, period length, whatever a
new reader needs to not misread an output.]

## Material assumptions
[The inputs the output is most sensitive to. Cross-reference the Sources
sheet inside the workbook.]

## Boundary conditions / when this breaks
[Inputs or regimes where the model's formulas stop being meaningful --
divide-by-zero guards, negative-rate edge cases, non-monotonic ranges, etc.]

## Known limitations
[What this model does NOT do. Be as specific and unflattering as the
Insurance/Securitization/LBO commits in this repo's git history -- a
limitations section that reads like marketing copy is not a limitations
section.]

## When this model should not be used
[The decision(s) this archetype is the wrong tool for, even though it looks
applicable.]

## Stakeholder perspectives represented
[Which lenses from docs/MODEL_GOVERNANCE_STANDARD.md's list this model shows
(owner/sponsor, lender, rating agency, LP/IC, regulator, counterparty,
taxpayer/public authority, servicer/operator, restructuring/recovery) and
which are deliberately out of scope.]

## Version
[Version identifier / commit reference this card describes.]
