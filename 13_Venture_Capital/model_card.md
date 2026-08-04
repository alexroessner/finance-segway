# Model Card — Venture Capital (Cap Table, Rounds, SAFE, Exit Waterfall, Participating Preferred)

## Decision this model is designed to support
Five linked questions: (1) what does the cap table look like today, (2)
what happens to it in a new priced round (dilution, post-money), (3) how
does an outstanding SAFE convert at that round, (4) at exit, who gets
what under a standard 1x non-participating pref stack vs. as-converted,
and (5) — the new addition — for a class with CAPPED PARTICIPATING
preferred specifically (a structurally different term from what's on the
Exit Waterfall tab), at what exit value does the cap flip a rational
holder from taking pref+participation to converting to common instead.

## Owner
unassigned

## Risk tier
Tier 2 (material analysis / negotiation decision support) for a
populated instance. Blank template is Tier 3.

## Methodology
- **Capped participating preferred**: pref taken off the top, then
  pro-rata participation in the remainder alongside common (the
  "double-dip"), capped at a multiple of invested capital. Models the
  RATIONAL HOLDER'S CHOICE directly: `actual = MAX(capped participating
  payout, as-converted payout)` — a holder converts to common exactly
  when the cap has made participating preferred worse than just
  converting, which is precisely what a cap is FOR (bounding the
  preferred holder's upside, not helping them).
- **Exit waterfall (1x non-participating)**, **SAFE conversion**, **round
  modeling**: unchanged standard methodology from the prior build,
  including the documented whole-cap-table regime-switch simplification
  on the Exit Waterfall tab.

## Conventions and units
USD. The participating-preferred tab models ONE class against "everyone
else" as a residual pool (via its as-converted ownership %), not a full
multi-class cascade — appropriate for evaluating a single term sheet's
structure, not for modeling an exit with multiple different preference
classes simultaneously (the Exit Waterfall tab is the right tool for
that, with its own documented 1x-non-participating-only scope).

## Material assumptions
- Participation is uncapped on the way up until the cap multiple binds;
  the model does not represent a "cap that ratchets" or other exotic
  variants.
- The 7-point exit-value sweep (`$20mm` to `$500mm`) is illustrative —
  size it to the actual company's plausible exit range for real use.

## Boundary conditions / when this breaks
- At the exact exit value where capped participation equals as-converted
  (the crossover), the model favors "CONVERT TO COMMON" on a tie — an
  arbitrary but immaterial choice at the single knife-edge point.
- All formulas guard division/comparison edge cases; the participating-
  preferred sheet has no explicit `IFERROR` need since its inputs default
  to sensible non-zero values, unlike ratio-heavy sheets elsewhere.

## Known limitations
- No populated instance yet.
- Single-class participating-preferred model, not integrated into the
  main Exit Waterfall tab's multi-class cascade — a real cap table with
  BOTH a non-participating senior class and a participating junior class
  would need both tabs read together, not a single unified calculation.
- No multi-round dilution walk (SAFE -> Seed -> A -> B chained together
  in one model) — each round/conversion tool works independently per
  snapshot.

## When this model should not be used
Not a substitute for the actual signed term sheet and cap table
software (Carta, Pulley, etc.) for a real financing — this is a
structural-understanding and negotiation-prep tool, not a system of
record.

## Stakeholder perspectives represented
- **Preferred investor**: pref, participation, and cap economics.
- **Founder/common holder**: dilution and what's left after preferred
  claims.
Not represented: **option-holder tax/exercise-timing view**, **new
investor's view of the SAME round from the other side of the table**.

## Version
Built by `tools/builders/build_vc_template.py`. Participating Preferred
tab shipped alongside `check_vc_participating_preferred_cap` in
`tools/verify_reference_calcs.py` (joining the pre-existing
`check_vc_waterfall_conservation`).
