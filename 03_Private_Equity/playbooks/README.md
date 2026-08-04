# Sector Playbooks — Private Equity / LBO

A playbook is the missing layer between "here is a generic LBO template"
and "here is what a real deal in this specific sector actually looks
like." Same builder (`tools/builders/build_lbo_template.py`), same
verified formulas (`check_lbo_sources_uses_and_debt_schedule` and
`check_lbo_scenario_switch` in `tools/verify_reference_calcs.py` cover
the underlying mechanics) — genuinely different capital structure,
growth/margin assumptions, and downside mechanics per sector, with the
reasoning made explicit rather than left implicit in a spreadsheet cell.

This is a pilot covering three sectors chosen specifically because their
LBO economics diverge in ways that are mechanically interesting, not
just cosmetically different:

| Sector | Playbook | Instance | Entry mult. | Leverage | Base IRR | Clears 20% hurdle? |
|---|---|---|---|---|---|---|
| SaaS / Software | [SAAS_PLAYBOOK.md](SAAS_PLAYBOOK.md) | `../deals/SAAS_EXAMPLE.xlsx` | 15.0x | 4.0x | 24.2% | Yes |
| Healthcare Services | [HEALTHCARE_SERVICES_PLAYBOOK.md](HEALTHCARE_SERVICES_PLAYBOOK.md) | `../deals/HEALTHCARE_SERVICES_EXAMPLE.xlsx` | 10.0x | 5.5x | 17.4% | No |
| Industrials / Manufacturing | [INDUSTRIALS_PLAYBOOK.md](INDUSTRIALS_PLAYBOOK.md) | `../deals/INDUSTRIALS_EXAMPLE.xlsx` | 7.5x | 4.5x | 11.1% | No |

Two of the three example instances do NOT clear the 20% management-
promote hurdle as parameterized. That's deliberate: a playbook set that
only ever shows winning deals isn't credible, and the point of these
examples is to show how each sector's mechanics actually behave — high
growth deleveraging fast, defensiveness trading off against absolute
return, cyclicality compounding downside through both EBITDA and FCF
conversion — not to manufacture a good-looking outcome for every sector.

## Using a playbook

1. Read the playbook for your sector — it explains WHY the numbers
   differ from a generic instance, not just WHAT they are.
2. Open the corresponding populated instance to see the assumptions in
   context, on a live, recalculated workbook.
3. Copy `PLAYBOOK_TEMPLATE.md` to add a new sector; build a matching
   instance via the same pattern used in this pilot (populate
   `tools/builders/build_lbo_template.py`'s output, save under
   `03_Private_Equity/deals/`, recalculate for real with
   `tools/recalc.py`, and sanity-check the headline outputs against an
   independent hand or Python calculation before treating it as
   reliable).

## Extending beyond LBO

This pattern — playbook doc + populated instance, same verified builder
— generalizes to any domain in this repository where sector or use-case
differences are mechanically meaningful (e.g., property-type differences
in Real Estate, industry-specific covenant packages in Private Credit).
Nothing about the pattern is LBO-specific; this pilot exists to prove the
shape out before replicating it elsewhere.
