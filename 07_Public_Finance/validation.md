# Validation Record — Public Finance (DSA + Revenue Bond Coverage + Additional Bonds Test)

## Verification hierarchy checklist

1. **Workbook opens** — yes; builder produces a valid .xlsx, confirmed via
   `openpyxl.load_workbook`.
2. **Formulas recalculate without errors** — yes;
   `tools/recalc.py 07_Public_Finance/_template_PUBLIC_FINANCE.xlsx` reports
   `status: success, total_errors: 0` on the blank template (55 formulas).
3. **Accounting or cash-flow identities tie** — yes, enforced live on the
   Checks sheet: net revenue = gross revenue − O&M ties to 0; pro-forma
   Year-1 debt service = existing + new ties to 0; the DSA trajectory label
   matches the sign of the primary-balance gap (TRUE).
4. **Closed-form or independent-code benchmark agrees** —
   `check_public_finance_additional_bonds_test` in
   `tools/verify_reference_calcs.py`: the new bond's level annual debt
   service (sheet's `PMT` formula) is compared against a closed-form
   annuity-payment formula computed independently in Python
   (`par * r / (1 - (1+r)^-n)`); the 5-year projected DSCR path is
   reproduced independently from the same growth-rate inputs. All matched
   to within 1e-4 relative tolerance on last run.
5. **Sensitivities behave monotonically and economically** — tested: under
   the Base scenario (revenue +3%/yr, O&M +2.5%/yr) the projected test
   passes all 5 years (min DSCR 1.434x in Year 1, rising to 1.627x by
   Year 5). Under Stress (revenue −2%/yr, O&M +5%/yr) DSCR falls
   monotonically each year and breaches the 1.25x covenant by Year 5
   (1.034x) — the correct direction and the "meaningful downside behavior"
   the governance standard requires.
6. **Historical outcomes or external observations agree** — n/a; no
   populated instance with real outcomes exists yet.
7. **Independent reviewer approves continued use** — not yet performed;
   this record was authored by the same session that built the feature.
   Flagged as an open item below.

## Independent reference check(s)

`check_public_finance_additional_bonds_test` (`tools/verify_reference_calcs.py`):
- New-bond level debt service: sheet `PMT` formula vs. closed-form annuity
  payment. Last run: sheet=1,537,522.89, closed-form=1,537,522.89.
- Pro-forma DSCR: sheet=1.3896, ref=1.3896.
- Base-scenario 5-yr min DSCR: sheet=1.4342, ref=1.4342, both PASS.
- Stress-scenario 5-yr min DSCR: sheet=1.0343, ref=1.0343, both FAIL
  (breach in Year 5) — confirms the scenario switch actually changes the
  pass/fail outcome, not just the displayed number.

## Sensitivity / stress behavior tested

Base vs. Stress revenue/O&M growth scenario (Cover!C9 selector), as
described in checklist item 5 above.

## Limitations surfaced during validation

- The projected test assumes existing debt service stays flat across the
  5-year window; a portfolio with a laddered maturity schedule would need
  each series modeled separately (noted in model_card.md).
- No test yet for a proposed issuance that itself fails the historical test
  but passes the projected test (or vice versa) — both paths are computed
  but a combined "either test passes" summary line is a candidate follow-up.

## Conclusion

Pass, with limitations. Independent-oracle check registered and passing;
Sources/Checks sheets, model card, and this validation record now exist,
satisfying the M3 evidence-pack gate. To reach M4: add at least two
populated instances (real issuer financials + a real proposed issuance),
and get independent reviewer sign-off distinct from the developer.

## Date and validator

2026-08-04. Authored by the same agent that built the feature — this
record itself does not yet satisfy the "someone other than the primary
developer" requirement in docs/MODEL_GOVERNANCE_STANDARD.md's validation
lifecycle step; flagged here rather than silently claimed.
