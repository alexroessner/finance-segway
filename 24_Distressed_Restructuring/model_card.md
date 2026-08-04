# Model Card — Distressed / Restructuring (Recovery Waterfall, EV Sensitivity, Liquidation vs. Reorg)

## Decision this model is designed to support
Three linked questions: (1) at a given enterprise value, what does each
tranche recover and which class is the fulcrum security (controls the
reorganization, converts to new equity), (2) — the new addition — HOW
DOES THAT ANSWER CHANGE across a range of enterprise values, since EV is
precisely what every party in a Chapter 11 disputes, and (3) is
liquidation or reorganization NPV-superior for creditors as a class.

## Owner
unassigned

## Risk tier
Tier 1 (recovery/plan-of-reorganization decision) for a populated
instance. Blank template is Tier 3.

## Methodology
- **Absolute priority waterfall**: senior tranches paid in full (up to
  face claim) before any junior tranche recovers anything — the U.S.
  Bankruptcy Code's absolute priority rule (11 U.S.C. Section 1129(b)).
- **Fulcrum security**: the first tranche (top-down) whose recovery drops
  below 100%, given the tranche immediately senior to it was paid in
  full — standard distressed-investing definition.
- **EV Sensitivity (the new tab)**: reruns the identical waterfall logic
  across a 7-point range of enterprise values (-40% to +40% of the base
  case) and identifies the fulcrum at EACH point — making visible that
  the fulcrum is a FUNCTION of EV, not a fixed fact about the capital
  structure. As EV falls, the fulcrum climbs toward the most senior
  claims; as EV rises, it drops toward equity.
- **Liquidation vs. reorg NPV**: compares net proceeds under each path,
  discounted for time to distribution — a simplified version of the
  Bankruptcy Code's best-interests-of-creditors test (11 U.S.C. Section
  1129(a)(7)), which in reality is applied class-by-class, not just in
  aggregate.

## Conventions and units
USD. Tranches ordered by seniority rank (DIP/super-priority most senior,
equity most junior) — this repository's illustrative default capital
structure; a real case's actual tranche list and ranking must replace it.

## Material assumptions
- Strict absolute priority — no negotiated deviations. Real Chapter 11
  plans sometimes include negotiated settlements (e.g., senior classes
  "gifting" recovery to equity or a junior class to secure a consensual
  plan) that this model does not represent.
- The EV sensitivity range (-40% to +40%, symmetric) is illustrative, not
  calibrated to any specific case's actual disputed valuation range,
  which depends on the specific DCF/comps/precedent-transaction
  methodology dispute at hand.

## Boundary conditions / when this breaks
- The fulcrum-identification formula is guarded with `ISNUMBER` checks so
  a blank template (all "-") never falsely flags a fulcrum.
- Recovery % is capped at the tranche's own face claim by construction
  (the `MIN(remaining, face)` waterfall structure) — verified directly in
  the Checks sheet.

## Known limitations
- No populated instance yet.
- Single-point EV per scenario column, not a continuous or Monte Carlo
  distribution over EV — the 7 columns are illustrative points, not a
  full probability-weighted analysis.
- No secured-vs-unsecured collateral-coverage nuance within a tranche
  (treats each tranche as a single uniform claim).

## When this model should not be used
Not a substitute for the actual plan of reorganization's specific
distribution mechanics, which can include convenience classes, equity
kickers, warrants, or other structures beyond a pure cash/new-equity
absolute-priority waterfall.

## Stakeholder perspectives represented
- **Senior secured creditor**: recovery certainty across the EV range.
- **Junior/fulcrum creditor**: the class whose recovery is genuinely
  contested and who has the most incentive to litigate the EV question.
Not represented: **debtor/management's view**, **equity holders'
out-of-the-money incentive to delay**.

## Version
Built by `tools/builders/build_restructuring_template.py`. EV
Sensitivity tab shipped alongside `check_restructuring_ev_sensitivity`
in `tools/verify_reference_calcs.py`.
