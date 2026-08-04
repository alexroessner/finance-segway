<!--
Template for <domain>/validation.md, per docs/MODEL_GOVERNANCE_STANDARD.md's
M3 evidence pack and its verification hierarchy (workbook opens -> formulas
recalc clean -> identities tie -> independent benchmark agrees -> sensitivities
behave monotonically -> historical outcomes agree -> independent reviewer
approves). Fill in every level actually performed; do not mark a level done
without retained evidence (a command, a check name, a number).
-->

# Validation Record — [Archetype Name]

## Verification hierarchy checklist

1. **Workbook opens** — [yes/no; how checked]
2. **Formulas recalculate without errors** — [tools/recalc.py output / date last run]
3. **Accounting or cash-flow identities tie** — [which identities; where enforced --
   e.g. a Checks-sheet formula, or a verify_reference_calcs.py assertion]
4. **Closed-form or independent-code benchmark agrees** — [name of the
   registered check in tools/verify_reference_calcs.py, and what it compares]
5. **Sensitivities behave monotonically and economically** — [what was
   perturbed, what direction the output moved, and why that's the expected
   direction]
6. **Historical outcomes or external observations agree** — [n/a until a
   populated instance exists with real outcomes to compare against; state
   that explicitly rather than omitting the line]
7. **Independent reviewer approves continued use** — [reviewer identity,
   date, and what they reviewed -- review comments without a clear
   conclusion do not count per the governance standard]

## Independent reference check(s)

[List the check_* function name(s) in tools/verify_reference_calcs.py,
what independent Python re-implementation each compares against, and the
specific numeric result from the last run.]

## Sensitivity / stress behavior tested

[Concrete scenarios run and the direction/magnitude of the output response.]

## Limitations surfaced during validation

[Anything the validator found that the model card doesn't already disclose.]

## Conclusion

[Pass / pass-with-limitations / fail, and what would need to change to
raise this to the next maturity level.]

## Date and validator

[Date this record was last updated, and who performed the validation --
must be someone other than the primary developer per the governance
standard's independent-validation requirement.]
