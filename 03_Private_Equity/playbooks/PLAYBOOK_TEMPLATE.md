<!--
Template for a sector playbook: a document that tells you HOW TO PARAMETERIZE
the domain's builder (here, tools/builders/build_lbo_template.py) for a given
sector or archetype, and WHY those parameters differ from another sector's.

A playbook is not a new builder and not a new set of formulas -- it's the
missing layer between "here is a generic template" and "here is what a real
deal in this sector actually looks like." Copy this file, fill in every
section, then build a populated instance (see the bottom section) and link it
here.
-->

# [Sector Name] Playbook — [Domain / Archetype]

## What makes this sector's economics genuinely different
[Not "this sector is different" — the SPECIFIC mechanical reason the model's
outputs should look different here than in a generic instance. E.g., "cash
generation is stable and non-cyclical, so lenders underwrite materially higher
leverage than they would for a cyclical industrial business at the same EBITDA."]

## Typical valuation range
[Entry/exit multiple ranges seen in real transactions in this sector, and
what drives the range — growth, margin structure, scarcity of assets,
regulatory risk, etc. Cite the mechanism, not just a number.]

## Typical capital structure
[Leverage tolerance (Debt/EBITDA), typical tranche mix, typical pricing —
and WHY lenders underwrite this sector the way they do.]

## Key operating assumptions
[Growth rate ranges, margin structure, FCF conversion, capex intensity —
whatever drives the model's projection engine for this sector specifically.]

## Sector-specific KPIs (beyond what the generic template tracks)
[What would a specialist in this sector actually look at that a generic
LBO/DCF/credit model doesn't surface? E.g., Net Revenue Retention and Rule of
40 for SaaS; payor mix and reimbursement risk for healthcare services;
capacity utilization and input-cost pass-through for industrials.]

## Downside scenario: what actually breaks
[Not a generic "-20% haircut" — the SPECIFIC mechanism by which this sector's
downside actually happens, and why it looks different from another sector's
downside. E.g., SaaS downside is a growth/churn shock that also compresses
the exit multiple; industrials downside is a demand shock that hits EBITDA
AND FCF conversion simultaneously because capex doesn't flex down.]

## Diligence items specific to this sector
[What would an experienced sector investor specifically dig into before
signing, beyond standard financial/legal/tax diligence?]

## How to parameterize the builder
[Concrete guidance: which cells/assumptions in the builder's output to set,
and to what kind of range, for a deal in this sector. Point to the actual
sheet/cell layout, not just prose.]

## Populated example instance
[Path to a live populated .xlsx built with this playbook's assumptions, and
a one-paragraph summary of what it shows — including the outcome, honestly,
even if the deal as parameterized doesn't clear a return hurdle. A playbook
that only ever shows winning deals isn't credible.]

## Sources
[Where these ranges/conventions come from — industry reports, practitioner
convention, specific deals (if public/citable). Mark anything that's an
illustrative assumption rather than a sourced figure.]
