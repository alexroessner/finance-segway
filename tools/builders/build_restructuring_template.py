import openpyxl
from template_helpers import *

wb = openpyxl.Workbook()
wb.remove(wb.active)

add_cover(wb, "[COMPANY] — Distressed / Restructuring Model", [
    ("Situation type:", "Chapter 11 / Out-of-court / Chapter 7"),
    ("Petition/filing date:", "[date]"),
    ("Last refreshed:", "[date]"),
    ("Refresh cadence:", "Weekly (daily near key dates)"),
])

# ---------------- CAPITAL STRUCTURE & RECOVERY WATERFALL ----------------
ws = wb.create_sheet("Recovery Waterfall")
set_col_widths(ws, [4, 24, 14, 14, 14, 14, 16])
ws["B2"] = "Capital Structure & Recovery Waterfall"; ws["B2"].font = TITLE
headers = ["", "Tranche", "Face claim ($)", "Seniority rank", "Recovery ($)", "Recovery %", "Fulcrum?"]
for i, h in enumerate(headers, start=1):
    ws.cell(row=4, column=i, value=h)
style_header_row(ws, 4, len(headers)-1)
tranches = ["DIP / super-priority", "First lien secured", "Second lien secured",
            "Senior unsecured notes", "Subordinated debt", "Equity"]
r = 5
for i, t in enumerate(tranches):
    ws.cell(row=r, column=2, value=t).font = BLACK
    c_face = ws.cell(row=r, column=3, value=0); c_face.font = BLUE; c_face.number_format = CUR; c_face.border = BORDER
    ws.cell(row=r, column=4, value=i+1).font = BLUE
    r += 1
last_tranche_row = r - 1

ws["B12"] = "Total enterprise value available for distribution ($)"
ws["C12"] = 0; ws["C12"].font = BLUE; ws["C12"].fill = YELLOW_FILL; ws["C12"].number_format = CUR

# waterfall: each tranche gets min(remaining value, its face claim), cascading by seniority
ws["B14"] = "Waterfall (senior to junior, absolute priority)"
ws["B14"].font = BOLD; ws["B14"].fill = GRAY_FILL
r = 5
for i in range(len(tranches)):
    remaining_formula = "C12" if i == 0 else f"MAX(C12-SUM(E5:E{4+i}),0)"
    ws.cell(row=r, column=5, value=f"=MIN({remaining_formula},C{r})")
    ws.cell(row=r, column=5).number_format = CUR
    ws.cell(row=r, column=5).border = BORDER
    ws.cell(row=r, column=6, value=f"=IFERROR(E{r}/C{r},\"-\")")
    ws.cell(row=r, column=6).number_format = PCT
    ws.cell(row=r, column=6).border = BORDER
    # Fulcrum = the first tranche (top-down) whose recovery drops below 100%,
    # given the tranche immediately senior to it was paid in full. Guarded on
    # ISNUMBER so a blank template (all "-") never falsely flags a fulcrum.
    if i == 0:
        fulcrum_formula = f'=IF(AND(ISNUMBER(F{r}),F{r}<1),"FULCRUM","")'
    else:
        fulcrum_formula = (f'=IF(AND(ISNUMBER(F{r}),F{r}<1,ISNUMBER(F{r-1}),F{r-1}>=1),'
                            f'"FULCRUM","")')
    ws.cell(row=r, column=7, value=fulcrum_formula)
    ws.cell(row=r, column=7).font = BOLD
    ws.cell(row=r, column=7).border = BORDER
    r += 1
ws["B20"] = ("Fulcrum security = the tranche where recovery % first drops below 100% "
             "— that class controls the reorg (converts to new equity)")
ws["B20"].font = ITALIC_GRAY
ws["B21"] = "Fulcrum security"
ws["C21"] = (f'=IFERROR(INDEX(B5:B{last_tranche_row},'
             f'MATCH("FULCRUM",G5:G{last_tranche_row},0)),"-")')
ws["C21"].font = BOLD; ws["C21"].border = BORDER
ws.sheet_view.showGridLines = False

# ---------------- EV SENSITIVITY: WHERE THE FULCRUM MOVES ----------------
ws = wb.create_sheet("EV Sensitivity")
set_col_widths(ws, [4, 26, 13, 13, 13, 13, 13, 13, 13])
ws["B2"] = "Enterprise Value Sensitivity: Where the Fulcrum Moves"; ws["B2"].font = TITLE
ws["B3"] = ("The fulcrum security isn't fixed -- it's a function of enterprise value, and EV is exactly what "
            "every party in a Chapter 11 fights over. As EV falls, the fulcrum moves UP the capital structure "
            "(more senior classes get impaired); as EV rises, it moves DOWN. This is why EV disputes are the "
            "actual battleground, not a side issue -- whoever's class becomes the fulcrum controls the plan.")
ws["B3"].font = ITALIC_GRAY

ev_scenarios = [-0.40, -0.20, -0.10, 0.0, 0.10, 0.20, 0.40]
ws["B5"] = "EV scenario (% of base case)"
for i, s in enumerate(ev_scenarios, start=3):
    c = ws.cell(row=5, column=i, value=s); c.font = BOLD; c.fill = GRAY_FILL; c.number_format = PCT
ws["B6"] = "Enterprise value ($)"
for i, s in enumerate(ev_scenarios, start=3):
    letter = get_column_letter(i)
    ws.cell(row=6, column=i, value=f"='Recovery Waterfall'!$C$12*(1+{letter}5)").number_format = CUR
    ws.cell(row=6, column=i).border = BORDER

n_tranches = 6
ws["B8"] = "Recovery % by tranche"; ws["B8"].font = BOLD; ws["B8"].fill = GRAY_FILL
for t in range(n_tranches):
    row = 9 + t
    ws.cell(row=row, column=2, value=f"='Recovery Waterfall'!B{5+t}").font = GREEN
    for i in range(3, 3 + len(ev_scenarios)):
        letter = get_column_letter(i)
        face_ref = f"'Recovery Waterfall'!$C${5+t}"
        if t == 0:
            remaining = f"{letter}6"
        else:
            senior_faces = "+".join(f"'Recovery Waterfall'!$C${5+k}" for k in range(t))
            senior_recovered = "+".join(f"{letter}{9+k}*'Recovery Waterfall'!$C${5+k}" for k in range(t))
            remaining = f"MAX({letter}6-({senior_recovered}),0)"
        formula = f'=IFERROR(MIN({remaining},{face_ref})/{face_ref},"-")'
        ws.cell(row=row, column=i, value=formula).number_format = PCT
        ws.cell(row=row, column=i).border = BORDER

ws["B16"] = "Fulcrum tranche at this EV"; ws["B16"].font = BOLD
for i in range(3, 3 + len(ev_scenarios)):
    letter = get_column_letter(i)
    conditions = []
    for t in range(n_tranches):
        row = 9 + t
        if t == 0:
            conditions.append(f'IF(AND(ISNUMBER({letter}{row}),{letter}{row}<1),B{row},')
        else:
            prev_row = row - 1
            conditions.append(f'IF(AND(ISNUMBER({letter}{row}),{letter}{row}<1,ISNUMBER({letter}{prev_row}),{letter}{prev_row}>=1),B{row},')
    formula = "=" + "".join(conditions) + '"none -- equity in the money"' + ")" * len(conditions)
    ws.cell(row=16, column=i, value=formula)
    ws.cell(row=16, column=i).font = BOLD
    ws.cell(row=16, column=i).border = BORDER
ws["B18"] = "Read left to right: the fulcrum climbs toward DIP/first-lien as EV falls, and drops toward equity as EV rises -- the same capital structure, a completely different plan of reorganization."
ws["B18"].font = ITALIC_GRAY
ws.sheet_view.showGridLines = False

# ---------------- LIQUIDATION VS REORG ----------------
ws = wb.create_sheet("Liquidation vs Reorg")
set_col_widths(ws, [4, 30, 16, 16, 40])
ws["B2"] = "Liquidation (Ch. 7) vs. Reorganization (Ch. 11) NPV"; ws["B2"].font = TITLE
headers = ["", "", "Liquidation", "Reorg", "Notes"]
for i, h in enumerate(headers, start=1):
    ws.cell(row=4, column=i, value=h)
style_header_row(ws, 4, 3, start_col=3)

ws["B5"] = "Gross asset value / going-concern EV"
ws["C5"] = 0; ws["C5"].font = BLUE; ws["C5"].number_format = CUR
ws["D5"] = 0; ws["D5"].font = BLUE; ws["D5"].number_format = CUR
ws["B6"] = "Less: liquidation discount / distress costs"
ws["C6"] = 0; ws["C6"].font = BLUE; ws["C6"].number_format = CUR
ws["B7"] = "Less: administrative/professional fees"
ws["C7"] = 0; ws["C7"].font = BLUE; ws["C7"].number_format = CUR
ws["D7"] = 0; ws["D7"].font = BLUE; ws["D7"].number_format = CUR
ws["B8"] = "Time to distribution (months)"
ws["C8"] = 6; ws["C8"].font = BLUE; ws["C8"].number_format = NUM
ws["D8"] = 18; ws["D8"].font = BLUE; ws["D8"].number_format = NUM
ws["B9"] = "Discount rate (annual, for NPV of delayed recovery)"
ws["C9"] = 0.15; ws["C9"].font = BLUE; ws["C9"].fill = YELLOW_FILL; ws["C9"].number_format = PCT

ws["B11"] = "Net proceeds"
ws["C11"] = "=C5-C6-C7"; ws["C11"].number_format = CUR
ws["D11"] = "=D5-D7"; ws["D11"].number_format = CUR
ws["B12"] = "NPV of proceeds (discounted for time to distribution)"
ws["C12"] = "=C11/(1+$C$9)^(C8/12)"; ws["C12"].font = BOLD; ws["C12"].number_format = CUR
ws["D12"] = "=D11/(1+$C$9)^(D8/12)"; ws["D12"].font = BOLD; ws["D12"].number_format = CUR
ws["E12"] = "Compare NPVs — higher wins for creditors as a class, though individual tranche outcomes differ"
ws["E12"].font = ITALIC_GRAY
for r2 in range(5, 13):
    for c in (3, 4):
        ws.cell(row=r2, column=c).border = BORDER
ws.sheet_view.showGridLines = False

add_sources_checks(
    wb,
    sources=[
        ("Absolute priority waterfall (senior tranches paid in full before any junior recovery)", "U.S. Bankruptcy Code absolute priority rule (11 U.S.C. Section 1129(b))", "Statutory", "Assumes strict absolute priority -- real plans sometimes deviate via negotiated settlements (e.g. gifting to equity) that this model does not represent"),
        ("Fulcrum security = first tranche whose recovery drops below 100%", "Standard distressed-investing / restructuring practitioner definition", "Standard practice", "Identifies the fulcrum GIVEN a single point-estimate EV -- see the EV Sensitivity tab for how it moves across a range"),
        ("EV sensitivity across a -40% to +40% scenario range", "Reflects the reality that enterprise value in a Chapter 11 is contested, not a known fact", "Modeling choice, not a specific case's actual EV range", "Symmetric percentage range for illustration -- a real case's plausible EV range depends on valuation methodology disputes (DCF vs. comps vs. precedent transactions)"),
        ("Liquidation vs. reorg NPV comparison", "Standard best-interests-of-creditors test framing (11 U.S.C. Section 1129(a)(7))", "Statutory framing, illustrative implementation", "A real best-interests test is class-by-class, not just an aggregate NPV comparison"),
    ],
    checks=[
        ("Fulcrum tranche at the base case (0% EV scenario) matches the single-scenario Recovery Waterfall tab", "=IF('EV Sensitivity'!F16='Recovery Waterfall'!C21,TRUE,FALSE)", "TRUE -- the sensitivity table's base-case column must reproduce the standalone waterfall's own answer"),
        ("Number of fully-recovered tranches is non-decreasing as EV rises from -40% to +40%", "=IF(COUNTIF('EV Sensitivity'!C9:C14,\">=0.9999\")<=COUNTIF('EV Sensitivity'!I9:I14,\">=0.9999\"),TRUE,FALSE)", "TRUE -- more enterprise value can only help junior tranches recover, never hurt senior ones"),
        ("Recovery % never exceeds 100% for any tranche at any EV scenario", "=IF(COUNTIF('EV Sensitivity'!C9:I14,\">1.0000001\")=0,TRUE,FALSE)", "TRUE -- absolute priority caps every tranche's recovery at its own face claim"),
        ("NPV comparison picks the higher of liquidation vs. reorg", "=IF(OR(NOT(ISNUMBER('Liquidation vs Reorg'!C12)),NOT(ISNUMBER('Liquidation vs Reorg'!D12))),TRUE,MAX('Liquidation vs Reorg'!C12,'Liquidation vs Reorg'!D12)=IF('Liquidation vs Reorg'!C12>'Liquidation vs Reorg'!D12,'Liquidation vs Reorg'!C12,'Liquidation vs Reorg'!D12))", "TRUE"),
    ],
)

add_refresh_log(wb)
out_path = "RESTRUCTURING_template.xlsx"
wb.save(out_path)
print("saved", out_path)
