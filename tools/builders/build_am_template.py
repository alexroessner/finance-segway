import openpyxl
from template_helpers import *

wb = openpyxl.Workbook()
wb.remove(wb.active)

add_cover(wb, "[FUND] — Asset Management Model", [
    ("Fund structure:", "Hedge fund / PE fund / mutual fund"),
    ("Vintage / inception:", "[date]"),
    ("Last refreshed:", "[date]"),
    ("Next capital call/distribution:", "[date]"),
    ("Refresh cadence:", "Weekly (monthly NAV strike)"),
])

# ---------------- FUND NAV ----------------
ws = wb.create_sheet("Fund NAV")
set_col_widths(ws, [4, 26, 14, 14, 14, 14])
ws["B2"] = "Fund NAV Build"; ws["B2"].font = TITLE
headers = ["", "", "Period 0", "Period 1", "Period 2", "Period 3"]
for i, h in enumerate(headers, start=1):
    ws.cell(row=4, column=i, value=h)
style_header_row(ws, 4, 4, start_col=3)
rows = ["Beginning NAV", "+ Capital contributions", "+ Realized/unrealized gains",
        "- Fees & expenses", "- Distributions", "Ending NAV"]
r = 5
for label in rows:
    ws.cell(row=r, column=2, value=label).font = BOLD if label in ("Beginning NAV", "Ending NAV") else BLACK
    for c in range(3, 7):
        cell = ws.cell(row=r, column=c, value=0 if label != "Ending NAV" else None)
        cell.number_format = CUR
        cell.border = BORDER
        cell.font = BLUE if label != "Ending NAV" else BLACK
    r += 1
end_row = r - 1
begin_row = 5
for c in range(3, 7):
    col = get_column_letter(c)
    ws.cell(row=end_row, column=c,
            value=f"={col}{begin_row}+{col}{begin_row+1}+{col}{begin_row+2}-{col}{begin_row+3}-{col}{begin_row+4}")
    ws.cell(row=end_row, column=c).font = BOLD
    ws.cell(row=end_row, column=c).number_format = CUR
# chain beginning NAV of period n+1 = ending NAV of period n
for c in range(4, 7):
    col = get_column_letter(c)
    prev = get_column_letter(c-1)
    ws.cell(row=begin_row, column=c, value=f"={prev}{end_row}")
ws.sheet_view.showGridLines = False

# ---------------- FEE WATERFALL ----------------
ws = wb.create_sheet("Fee Waterfall")
set_col_widths(ws, [4, 30, 16, 40])
ws["B2"] = "Fee Waterfall — Mgmt Fee + Carry w/ Hurdle"; ws["B2"].font = TITLE
ws["B4"] = "Inputs"; ws["B4"].font = BOLD; ws["B4"].fill = GRAY_FILL
inputs = [
    ("Committed capital", 0, CUR),
    ("Management fee %", 0.02, PCT),
    ("Preferred return / hurdle %", 0.08, PCT),
    ("Carry / promote %", 0.20, PCT),
    ("GP catch-up %", 1.00, PCT),
    ("Gross fund profit (this period)", 0, CUR),
    ("Capital invested (basis for hurdle)", 0, CUR),
]
r = 5
for label, default, fmt in inputs:
    ws.cell(row=r, column=2, value=label).font = BLACK
    c = ws.cell(row=r, column=3, value=default); c.font = BLUE; c.fill = YELLOW_FILL
    c.number_format = fmt; c.border = BORDER
    r += 1

ws["B13"] = "Waterfall"; ws["B13"].font = BOLD; ws["B13"].fill = GRAY_FILL
ws["B14"] = "1. Return of capital"
ws["C14"] = "=MIN(C10,C11)"; ws["C14"].number_format = CUR
ws["B15"] = "2. Preferred return (hurdle) to LPs"
ws["C15"] = "=MIN(MAX(C10-C14,0),C11*C7)"; ws["C15"].number_format = CUR
ws["B16"] = "3. GP catch-up tranche (total, before GP/LP split)"
ws["C16"] = '=IF(C9<=C8,0,MIN(MAX(C10-C14-C15,0),C15*C8/(C9-C8)))'
ws["C16"].number_format = CUR
ws["D16"] = "General catch-up formula for an arbitrary catch-up rate C9 (not hardcoded to 100%): tranche size = pref x carry% / (catch-up% - carry%). At C9=100% this collapses to the standard pref x carry%/(1-carry%) formula."
ws["D16"].font = ITALIC_GRAY
ws["B17"] = "   GP share of catch-up tranche (x catch-up %)"
ws["C17"] = "=C16*C9"; ws["C17"].number_format = CUR
ws["B18"] = "   LP share of catch-up tranche (x (1 - catch-up %))"
ws["C18"] = "=C16*(1-C9)"; ws["C18"].number_format = CUR
ws["B19"] = "4. Remaining profit split (LP/GP per carry%)"
ws["C19"] = "=MAX(C10-C14-C15-C16,0)"; ws["C19"].number_format = CUR
ws["B20"] = "   GP share of remainder"
ws["C20"] = "=C19*C8"; ws["C20"].number_format = CUR
ws["B21"] = "   LP share of remainder"
ws["C21"] = "=C19*(1-C8)"; ws["C21"].number_format = CUR
ws["B23"] = "Total GP take (catch-up + carry)"
ws["C23"] = "=C17+C20"; ws["C23"].font = BOLD; ws["C23"].number_format = CUR
ws["B24"] = "Total LP take"
ws["C24"] = "=C14+C15+C18+C21"; ws["C24"].font = BOLD; ws["C24"].number_format = CUR
ws["B25"] = "Annual management fee (separate from carry)"
ws["C25"] = "=C5*C6"; ws["C25"].number_format = CUR
ws["B26"] = "GP effective carry % of total profit (sanity check — should trend to C8 as profit grows)"
ws["C26"] = "=IFERROR(C23/(C10-C14),\"-\")"; ws["C26"].number_format = PCT2
for r2 in list(range(14, 22)) + [23, 24, 25, 26]:
    ws.cell(row=r2, column=3).border = BORDER
ws.sheet_view.showGridLines = False

# ---------------- GP CARRY & CLAWBACK ----------------
ws = wb.create_sheet("GP Carry & Clawback")
set_col_widths(ws, [4, 44, 16, 16, 16, 16])
ws["B2"] = "GP Carry & Clawback — Whole-Fund (European) Waterfall"; ws["B2"].font = TITLE
ws["B3"] = ("Re-runs the SAME waterfall as the Fee Waterfall tab, but cumulatively through each period rather than "
            "once. That's what a whole-fund/European waterfall actually is: carry earned to date is always a "
            "function of CUMULATIVE fund performance, so a later markdown can make previously-paid carry excessive "
            "-- a clawback obligation -- which a single-period calc can never show.")
ws["B3"].font = ITALIC_GRAY

for i, h in enumerate(["", "", "Period 0", "Period 1", "Period 2", "Period 3"], start=1):
    ws.cell(row=5, column=i, value=h)
style_header_row(ws, 5, 4, start_col=3)

periods = ["C", "D", "E", "F"]
ws["B6"] = "Cumulative capital contributed"
ws["B7"] = "Cumulative net gains (gains less fees)"
ws["B8"] = "Cumulative distributable value (capital + net gains)"
for L in periods:
    ws[f"{L}6"] = f"=SUM('Fund NAV'!$C$6:{L}6)"
    ws[f"{L}7"] = f"=SUM('Fund NAV'!$C$7:{L}7)-SUM('Fund NAV'!$C$8:{L}8)"
    ws[f"{L}8"] = f"={L}6+{L}7"
    for row in (6, 7, 8):
        ws[f"{L}{row}"].number_format = CUR
        ws[f"{L}{row}"].border = BORDER

ws["B10"] = "Cumulative waterfall (hurdle/carry/catch-up % from Fee Waterfall tab)"
ws["B10"].font = BOLD; ws["B10"].fill = GRAY_FILL
ws["B11"] = "Return of capital (cumulative)"
ws["B12"] = "Preferred return (cumulative)"
ws["B13"] = "GP catch-up tranche (cumulative)"
ws["B14"] = "  GP share of catch-up"
ws["B15"] = "Remainder above catch-up (cumulative)"
ws["B16"] = "  GP share of remainder"
ws["B17"] = "Cumulative GP carry earned through this period"
ws["B17"].font = BOLD
for L in periods:
    ws[f"{L}11"] = f"=MIN({L}8,{L}6)"
    ws[f"{L}12"] = f"=MIN(MAX({L}8-{L}11,0),{L}6*'Fee Waterfall'!$C$7)"
    ws[f"{L}13"] = (f"=IF('Fee Waterfall'!$C$9<='Fee Waterfall'!$C$8,0,"
                     f"MIN(MAX({L}8-{L}11-{L}12,0),{L}12*'Fee Waterfall'!$C$8/('Fee Waterfall'!$C$9-'Fee Waterfall'!$C$8)))")
    ws[f"{L}14"] = f"={L}13*'Fee Waterfall'!$C$9"
    ws[f"{L}15"] = f"=MAX({L}8-{L}11-{L}12-{L}13,0)"
    ws[f"{L}16"] = f"={L}15*'Fee Waterfall'!$C$8"
    ws[f"{L}17"] = f"={L}14+{L}16"
    for row in (11, 12, 13, 14, 15, 16, 17):
        ws[f"{L}{row}"].number_format = CUR
        ws[f"{L}{row}"].border = BORDER
    ws[f"{L}17"].font = BOLD

ws["B19"] = "Incremental GP carry this period"; ws["B19"].font = BOLD
ws["B20"] = "Running total carry paid to GP"
ws["B21"] = "Clawback status"
for i, L in enumerate(periods):
    if i == 0:
        ws[f"{L}19"] = f"={L}17"
    else:
        prior = periods[i - 1]
        ws[f"{L}19"] = f"={L}17-{prior}17"
    ws[f"{L}20"] = f"=SUM($C$19:{L}19)"
    ws[f"{L}21"] = f'=IF({L}19<0,"CLAWBACK — GP owes $"&TEXT(-{L}19,"#,##0")&" back to LPs","-")'
    ws[f"{L}19"].number_format = CUR; ws[f"{L}19"].font = BOLD; ws[f"{L}19"].border = BORDER
    ws[f"{L}20"].number_format = CUR; ws[f"{L}20"].border = BORDER
    ws[f"{L}21"].border = BORDER
ws.sheet_view.showGridLines = False

# ---------------- PERFORMANCE ATTRIBUTION ----------------
ws = wb.create_sheet("Performance Attribution")
set_col_widths(ws, [4, 24, 14, 14, 14, 40])
ws["B2"] = "Performance Attribution"; ws["B2"].font = TITLE
headers = ["", "Position/Strategy", "Contribution ($)", "Contribution (%)", "Weight (%)", "Notes"]
for i, h in enumerate(headers, start=1):
    ws.cell(row=4, column=i, value=h)
style_header_row(ws, 4, len(headers)-1)
for r in range(5, 12):
    ws.cell(row=r, column=2, value="[fill in]").font = BLUE
    c1 = ws.cell(row=r, column=3, value=0); c1.font = BLUE; c1.number_format = CUR; c1.border = BORDER
    c2 = ws.cell(row=r, column=4, value=0); c2.font = BLUE; c2.number_format = PCT; c2.border = BORDER
    c3 = ws.cell(row=r, column=5, value=0); c3.font = BLUE; c3.number_format = PCT; c3.border = BORDER
total_r = 12
ws.cell(row=total_r, column=2, value="Total fund return").font = BOLD
ws.cell(row=total_r, column=3, value="=SUM(C5:C11)").font = BOLD
ws.cell(row=total_r, column=3).number_format = CUR
ws.sheet_view.showGridLines = False

# ---------------- FUND PERFORMANCE (TVPI / DPI / NET IRR) ----------------
ws = wb.create_sheet("Fund Performance")
set_col_widths(ws, [4, 30, 14, 14, 14, 14, 40])
ws["B2"] = "Fund Performance — LP Reporting Metrics"; ws["B2"].font = TITLE
ws["B4"] = "Uses the period cash flows and ending NAV from the Fund NAV tab."
ws["B4"].font = ITALIC_GRAY

for i, h in enumerate(["", "", "Period 0", "Period 1", "Period 2", "Period 3"], start=1):
    ws.cell(row=6, column=i, value=h)
style_header_row(ws, 6, 4, start_col=3)
ws["B7"] = "LP net cash flow (distributions - contributions)"
for col in range(3, 7):
    letter = get_column_letter(col)
    ws.cell(row=7, column=col, value=f"='Fund NAV'!{letter}9-'Fund NAV'!{letter}6")
    ws.cell(row=7, column=col).number_format = CUR
    ws.cell(row=7, column=col).border = BORDER
ws["B8"] = "  + terminal NAV added to final period"
ws["C8"] = "='Fund NAV'!F10"; ws["C8"].font = GREEN; ws["C8"].number_format = CUR
ws["C8"].border = BORDER
ws["B9"] = "LP cash flow incl. terminal value (for IRR)"
for col in range(3, 6):
    letter = get_column_letter(col)
    ws.cell(row=9, column=col, value=f"={letter}7")
    ws.cell(row=9, column=col).number_format = CUR
    ws.cell(row=9, column=col).border = BORDER
ws.cell(row=9, column=6, value="=F7+C8")
ws.cell(row=9, column=6).number_format = CUR
ws.cell(row=9, column=6).border = BORDER

ws["B12"] = "Outputs"; ws["B12"].font = BOLD; ws["B12"].fill = GRAY_FILL
ws["B13"] = "Cumulative capital called"
ws["C13"] = "=SUM('Fund NAV'!C6:F6)"; ws["C13"].font = GREEN; ws["C13"].number_format = CUR
ws["B14"] = "Cumulative distributions"
ws["C14"] = "=SUM('Fund NAV'!C9:F9)"; ws["C14"].font = GREEN; ws["C14"].number_format = CUR
ws["B15"] = "Current NAV (residual value)"
ws["C15"] = "='Fund NAV'!F10"; ws["C15"].font = GREEN; ws["C15"].number_format = CUR
ws["B16"] = "DPI (Distributions to Paid-In)"
ws["C16"] = "=IFERROR(C14/C13,\"-\")"; ws["C16"].font = BOLD; ws["C16"].number_format = MULT
ws["B17"] = "RVPI (Residual Value to Paid-In)"
ws["C17"] = "=IFERROR(C15/C13,\"-\")"; ws["C17"].font = BOLD; ws["C17"].number_format = MULT
ws["B18"] = "TVPI (Total Value to Paid-In = DPI + RVPI)"
ws["C18"] = "=IFERROR(C16+C17,\"-\")"; ws["C18"].font = BOLD; ws["C18"].number_format = MULT
ws["D18"] = "Headline LP metric — total value (realized + unrealized) per dollar called"
ws["D18"].font = ITALIC_GRAY
ws["B19"] = "Net IRR to LPs (periodic, undated)"
ws["C19"] = "=IFERROR(IRR(C9:F9),\"-\")"; ws["C19"].font = BOLD; ws["C19"].number_format = PCT
ws["C19"].fill = YELLOW_FILL
ws["D19"] = "Treats each period as evenly spaced — use XIRR with real dates for called capital at irregular intervals"
ws["D19"].font = ITALIC_GRAY
for r2 in (13, 14, 15, 16, 17, 18, 19):
    ws.cell(row=r2, column=3).border = BORDER
ws.sheet_view.showGridLines = False

add_sources_checks(
    wb,
    sources=[
        ("Waterfall structure (ROC -> pref -> GP catch-up -> carry split)", "Standard private-fund LPA waterfall mechanics", "Standard practice", "Whole-fund/European structure (cumulative), not deal-by-deal/American"),
        ("General catch-up formula for an arbitrary catch-up rate", "Derived from the target-carry identity GP_catchup/(pref+catchup)=carry%, solved for a catch-up tranche paid at rate g", "Derived, not copied from a single source", "Collapses to the standard 100%-catch-up formula when the catch-up rate = 100%"),
        ("Default fee terms (2% mgmt, 8% hurdle, 20% carry, 100% catch-up)", "Common industry-standard private-fund terms", "Standard practice", "Illustrative defaults; replace with the actual LPA's terms"),
        ("TVPI/DPI/RVPI and periodic IRR", "Standard LP-reporting metric definitions (ILPA-style)", "Standard practice", "Periodic IRR treats periods as evenly spaced -- use XIRR with real dates for irregular capital calls"),
    ],
    checks=[
        ("Waterfall conserves: GP take + LP take = total distributable value (Fee Waterfall)", "='Fee Waterfall'!C23+'Fee Waterfall'!C24-'Fee Waterfall'!C10", "0 (exact) -- every dollar of distributable value lands with either the GP or the LPs"),
        ("Cumulative carry reconstructs from its own increments (Period 3)", "='GP Carry & Clawback'!F20-'GP Carry & Clawback'!F17", "0 (exact) -- the running total of incremental carry must equal the cumulative figure it was built from"),
        ("GP catch-up tranche is zero whenever catch-up % <= carry % (guards the division)", "=IF('Fee Waterfall'!C9<='Fee Waterfall'!C8,'Fee Waterfall'!C16=0,TRUE)", "TRUE"),
        ("TVPI = DPI + RVPI identity", "=IFERROR('Fund Performance'!C18-('Fund Performance'!C16+'Fund Performance'!C17),\"-\")", "0 (exact) once capital has been called; \"-\" on a blank template"),
    ],
)

add_refresh_log(wb)
out_path = "AM_template.xlsx"
wb.save(out_path)
print("saved", out_path)
