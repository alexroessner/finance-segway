# Model Card — Project Finance (Construction, Sculpted Debt, DSRA)

## Decision this model is designed to support
Three linked questions: (1) what does the project cost and how is it
financed through construction (Construction Budget), (2) what debt can
the operating cash flow actually support at a target DSCR, sculpted year
by year rather than as an aggregate capacity number (Sculpted Debt
Schedule), and (3) — the new addition — does a Debt Service Reserve
Account actually change the outcome of a bad year, and specifically:
does it prevent PAYMENT DEFAULT (the real bright-line event) even when it
can't cure the softer DSCR distribution-lock-up test (DSRA tab).

## Owner
unassigned

## Risk tier
Tier 1 (project financing decision) for a populated instance. Blank
template is Tier 3.

## Methodology
- **Sculpted debt schedule**: debt service each year is DEFINED as
  CFADS / target DSCR (not level or mortgage-style amortization) — this
  is what "sculpting" means in project finance. Interest is computed on
  the BEGINNING-of-period balance only (same convention as this
  repository's LBO and Private Credit debt schedules), so nothing here
  is circular.
- **DSRA (Debt Service Reserve Account)**: sized at N months of FORWARD
  debt service (default 6 months), funded to be drawn against a temporary
  CFADS shortfall. The model draws a critical, often-blurred distinction:
  - **Payment default** (the real bright-line credit event): cash
    available (stressed CFADS + DSRA draw) < debt service itself
    (effective DSCR < 1.0x).
  - **Distribution lock-up** (a softer, non-default trigger): effective
    DSCR is positive and above 1.0x but still below the TARGET covenant
    (e.g. 1.30x) — this restricts dividends to sponsors but does not, by
    itself, put the loan in default.
  A DSRA draw large enough to fund the payment in full can still leave
  the deal below its target DSCR and locked up from paying dividends —
  these are genuinely different triggers, modeled and tested separately,
  not the same event shown twice.

## Conventions and units
USD ($mm-scale inputs, formatted as full dollars). 5-year operating
window; construction period in months. IDC (interest during construction)
uses a linear-drawdown approximation.

## Material assumptions
- Sculpting assumes the CFADS forecast is reliable; an optimistic
  forecast under-reserves the real repayment capacity, since debt service
  is sized directly off it.
- DSRA required balance is FORWARD-looking (based on the NEXT period's
  debt service); some deals instead define DSRA against trailing/historic
  debt service — noted on the Sources sheet.
- The 5-year operating window is a modeling convenience, not necessarily
  the real debt tenor — a real infrastructure financing often has a
  15-30 year tenor, so a remaining balance at the end of this window is
  expected and shown explicitly ("balloon / refinancing need"), not
  treated as an error.

## Boundary conditions / when this breaks
- If sculpted debt service is less than the period's interest accrual
  (an infeasible sculpting scenario — the target DSCR is too low relative
  to CFADS and the debt rate), the Principal Repayment row returns the
  literal string "INFEASIBLE" rather than silently producing a growing
  balance.
- All ratio and division formulas guard against zero denominators with
  `IFERROR`.

## Known limitations
- No populated instance yet.
- DSRA replenishment (paying the reserve back down after a draw, before
  resuming dividends) is described but not modeled as a multi-year
  schedule — only the single-year draw mechanics are computed.
- No construction-phase risk modeling (cost overrun, delay) — the
  Construction Budget tab is a static single-scenario budget.

## When this model should not be used
Not a substitute for the actual project's credit agreement / common terms
agreement, which will define DSRA sizing, the specific distribution-
lock-up and default trigger levels, and cure-period mechanics in ways
that can differ meaningfully from the illustrative defaults here.

## Stakeholder perspectives represented
- **Lender**: DSCR covenant, DSRA adequacy, payment-default risk.
- **Sponsor**: distribution lock-up risk (money trapped in the project
  even absent default).
Not represented: **rating agency view** (typically layers additional
stress scenarios and P50/P90 sensitivity cases this single-scenario model
doesn't run), **offtaker/counterparty credit view**.

## Version
Built by `tools/builders/build_project_finance_template.py`. Sculpted
Debt Schedule and DSRA tabs shipped alongside `check_project_finance_dsra`
in `tools/verify_reference_calcs.py`.
