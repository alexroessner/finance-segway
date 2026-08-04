import openpyxl
from template_helpers import *

wb = openpyxl.Workbook()
wb.remove(wb.active)

add_cover(wb, "[PROJECT] — Project Finance Model", [
    ("Sector:", "Infrastructure / Energy / PPP"),
    ("Financial close date:", "[date]"),
    ("Last refreshed:", "[date]"),
    ("Refresh cadence:", "Weekly during construction; monthly during ops"),
])

# ---------------- CONSTRUCTION BUDGET ----------------
ws = wb.create_sheet("Construction Budget")
set_col_widths(ws, [4, 30, 16, 16, 40])
ws["B2"] = "Construction Budget & Drawdown"; ws["B2"].font = TITLE
inputs = [
    ("Total project cost ($)", 0, CUR),
    ("Debt / equity ratio (e.g. 0.70 = 70% debt)", 0.70, PCT),
    ("Construction period (months)", 24, NUM),
    ("Interest during construction rate (%)", 0.06, PCT),
]
r = 5
for label, default, fmt in inputs:
    ws.cell(row=r, column=2, value=label).font = BLACK
    c = ws.cell(row=r, column=3, value=default); c.font = BLUE; c.fill = YELLOW_FILL
    c.number_format = fmt; c.border = BORDER
    r += 1
ws["B11"] = "Debt drawn"; ws["C11"] = "=C5*C6"; ws["C11"].number_format = CUR
ws["B12"] = "Equity drawn"; ws["C12"] = "=C5*(1-C6)"; ws["C12"].number_format = CUR
ws["B13"] = "Interest during construction (IDC, simple approx.)"
ws["C13"] = "=C11*C8*(C7/12)/2"; ws["C13"].number_format = CUR
ws["D13"] = "Approximation: avg drawn balance x rate x period, /2 for linear drawdown"
ws["D13"].font = ITALIC_GRAY
ws["B14"] = "Total debt at COD (incl. capitalized IDC)"
ws["C14"] = "=C11+C13"; ws["C14"].font = BOLD; ws["C14"].number_format = CUR
for r2 in (11, 12, 13, 14):
    ws.cell(row=r2, column=3).border = BORDER
ws.sheet_view.showGridLines = False

# ---------------- OPERATING CASH FLOW ----------------
ws = wb.create_sheet("Operating Cash Flow")
set_col_widths(ws, [4, 26, 13, 13, 13, 13, 13])
ws["B2"] = "Operating Period Cash Flow ($mm)"; ws["B2"].font = TITLE
for i, h in enumerate(["", "Line item", "Yr1", "Yr2", "Yr3", "Yr4", "Yr5"], start=1):
    ws.cell(row=4, column=i, value=h)
style_header_row(ws, 4, 5, start_col=3)
rows = ["Contracted/merchant revenue", "- Operating costs", "EBITDA",
        "- Maintenance capex reserve", "Cash flow available for debt service (CFADS)"]
r = 5
for label in rows:
    ws.cell(row=r, column=2, value=label).font = BOLD if label in ("EBITDA", "Cash flow available for debt service (CFADS)") else BLACK
    for c in range(3, 8):
        cell = ws.cell(row=r, column=c, value=0)
        cell.font = BLUE
        cell.number_format = CUR
        cell.border = BORDER
    r += 1
for c in range(3, 8):
    col = get_column_letter(c)
    ws.cell(row=7, column=c, value=f"={col}5+{col}6")  # EBITDA = rev - opcosts(neg)
    ws.cell(row=9, column=c, value=f"={col}7+{col}8")  # CFADS = EBITDA - capex(neg)
ws.sheet_view.showGridLines = False

# ---------------- DSCR & DEBT SIZING ----------------
ws = wb.create_sheet("DSCR & Debt Sizing")
set_col_widths(ws, [4, 26, 13, 13, 13, 13, 13])
ws["B2"] = "DSCR & Debt Sizing"; ws["B2"].font = TITLE
for i, h in enumerate(["", "", "Yr1", "Yr2", "Yr3", "Yr4", "Yr5"], start=1):
    ws.cell(row=4, column=i, value=h)
style_header_row(ws, 4, 5, start_col=3)
ws["B5"] = "CFADS"
ws["B6"] = "Debt service (P&I)"
ws["B7"] = "DSCR (CFADS / Debt service)"
for c in range(3, 8):
    col = get_column_letter(c)
    ws.cell(row=5, column=c, value=f"='Operating Cash Flow'!{col}9")
    ws.cell(row=5, column=c).font = GREEN
    ws.cell(row=6, column=c, value=0).font = BLUE
    ws.cell(row=7, column=c, value=f"=IFERROR({col}5/{col}6,\"-\")")
    for r2 in (5, 6):
        ws.cell(row=r2, column=c).number_format = CUR
        ws.cell(row=r2, column=c).border = BORDER
    ws.cell(row=7, column=c).number_format = '0.00x'
    ws.cell(row=7, column=c).fill = YELLOW_FILL
    ws.cell(row=7, column=c).border = BORDER

ws["B9"] = "Minimum DSCR covenant"; ws["C9"] = 1.20; ws["C9"].font = BLUE; ws["C9"].fill = YELLOW_FILL
ws["C9"].number_format = '0.00x'; ws["C9"].border = BORDER
ws["B10"] = "Debt interest rate (for sizing PV)"
ws["C10"] = 0.06; ws["C10"].font = BLUE; ws["C10"].fill = YELLOW_FILL
ws["C10"].number_format = PCT2; ws["C10"].border = BORDER

ws["B12"] = "Debt sizing (sculpted to the DSCR covenant)"; ws["B12"].font = BOLD; ws["B12"].fill = GRAY_FILL
ws["B13"] = "Max annual debt service (CFADS / target DSCR)"
ws["B14"] = "PV of max debt service (discounted at debt rate)"
for c in range(3, 8):
    col = get_column_letter(c)
    year = c - 2
    ws.cell(row=13, column=c, value=f"=IFERROR({col}5/$C$9,\"-\")")
    ws.cell(row=13, column=c).number_format = CUR
    ws.cell(row=13, column=c).border = BORDER
    ws.cell(row=14, column=c, value=f"=IFERROR({col}13/(1+$C$10)^{year},\"-\")")
    ws.cell(row=14, column=c).number_format = CUR
    ws.cell(row=14, column=c).border = BORDER
ws["B16"] = "Max sculpted debt (sum of PVs of annual capacity)"
ws["C16"] = "=SUM(C14:G14)"
ws["C16"].font = BOLD; ws["C16"].number_format = CUR; ws["C16"].border = BORDER
ws["D16"] = ("This is capacity, not a repayment schedule — a real deal still needs an amortization "
             "profile (sculpted or level) that fits within it and keeps DSCR above covenant every "
             "period, not just on average")
ws["D16"].font = ITALIC_GRAY
ws.sheet_view.showGridLines = False

# ---------------- SCULPTED DEBT SCHEDULE ----------------
ws = wb.create_sheet("Sculpted Debt Schedule")
set_col_widths(ws, [4, 30, 13, 13, 13, 13, 13, 40])
ws["B2"] = "Sculpted Debt Repayment Schedule"; ws["B2"].font = TITLE
ws["B3"] = ("\"Max sculpted debt\" on the DSCR & Debt Sizing tab is a capacity figure, not a schedule. This "
            "actually builds the amortization that hits the target DSCR every period by construction -- "
            "debt service each year is set to CFADS/target DSCR (sculpted), not level or mortgage-style -- "
            "and rolls the balance forward from interest on the BEGINNING balance only, so nothing here is circular.")
ws["B3"].font = ITALIC_GRAY
for i, h in enumerate(["", "", "Yr1", "Yr2", "Yr3", "Yr4", "Yr5"], start=1):
    ws.cell(row=5, column=i, value=h)
style_header_row(ws, 5, 5, start_col=3)

ws["B6"] = "Beginning balance"
ws["C6"] = "='Construction Budget'!C14"; ws["C6"].font = GREEN
for col in range(4, 8):
    letter = get_column_letter(col - 1)
    ws.cell(row=6, column=col, value=f"={letter}10")

ws["B7"] = "Interest (beginning balance x debt rate)"
for col in range(3, 8):
    letter = get_column_letter(col)
    ws.cell(row=7, column=col, value=f"={letter}6*'DSCR & Debt Sizing'!$C$10")

ws["B8"] = "Sculpted debt service (CFADS / target DSCR)"
for col in range(3, 8):
    letter = get_column_letter(col)
    ws.cell(row=8, column=col, value=f"='DSCR & Debt Sizing'!{letter}13")
    ws.cell(row=8, column=col).font = GREEN

ws["B9"] = "Principal repayment (debt service - interest)"
for col in range(3, 8):
    letter = get_column_letter(col)
    ws.cell(row=9, column=col, value=f'=IF({letter}8<{letter}7,"INFEASIBLE",{letter}8-{letter}7)')

ws["B10"] = "Ending balance"; ws["B10"].font = BOLD
for col in range(3, 8):
    letter = get_column_letter(col)
    ws.cell(row=10, column=col, value=f'=IF(ISNUMBER({letter}9),{letter}6-{letter}9,{letter}6)')
    ws.cell(row=10, column=col).font = BOLD

for row in (6, 7, 8, 9, 10):
    for col in range(3, 8):
        ws.cell(row=row, column=col).number_format = CUR
        ws.cell(row=row, column=col).border = BORDER

ws["B12"] = "Total debt at COD"
ws["C12"] = "='Construction Budget'!C14"; ws["C12"].font = GREEN; ws["C12"].number_format = CUR; ws["C12"].border = BORDER
ws["B13"] = "Cumulative principal repaid through Yr5"
ws["C13"] = "=SUM(C9:G9)"; ws["C13"].number_format = CUR; ws["C13"].border = BORDER
ws["B14"] = "Remaining balance at Yr5 (balloon / refinancing need)"
ws["C14"] = "=G10"; ws["C14"].font = BOLD; ws["C14"].number_format = CUR; ws["C14"].border = BORDER
ws["D14"] = "Positive = the visible 5-year CFADS window doesn't fully retire the debt at this DSCR target -- normal for a debt tenor longer than the modeled window, but flag it, don't ignore it."
ws["D14"].font = ITALIC_GRAY
ws.sheet_view.showGridLines = False

# ---------------- DEBT SERVICE RESERVE ACCOUNT (DSRA) ----------------
ws = wb.create_sheet("DSRA")
set_col_widths(ws, [4, 34, 13, 13, 13, 13, 13, 40])
ws["B2"] = "Debt Service Reserve Account (DSRA)"; ws["B2"].font = TITLE
ws["B3"] = ("A cash reserve sized at N months of FORWARD debt service, funded at financial close, that can be "
            "drawn to cover a temporary CFADS shortfall without breaching the DSCR covenant or triggering "
            "default -- the actual mechanism (not the sculpted schedule) that absorbs a bad year.")
ws["B3"].font = ITALIC_GRAY
ws["B5"] = "DSRA target (months of forward debt service)"
c = ws.cell(row=5, column=3, value=6); c.font = BLUE; c.fill = YELLOW_FILL; c.number_format = NUM; c.border = BORDER

for i, h in enumerate(["", "", "Yr1", "Yr2", "Yr3", "Yr4", "Yr5"], start=1):
    ws.cell(row=7, column=i, value=h)
style_header_row(ws, 7, 5, start_col=3)
ws["B8"] = "Required DSRA balance (target/12 x next yr's debt service)"
for col in range(3, 8):
    letter = get_column_letter(col)
    next_letter = get_column_letter(col + 1) if col < 7 else letter  # Yr5 has no "next" -- use own year
    ws.cell(row=8, column=col, value=f"=$C$5/12*'Sculpted Debt Schedule'!{next_letter}8")
    ws.cell(row=8, column=col).number_format = CUR
    ws.cell(row=8, column=col).border = BORDER

ws["B10"] = "Stress Test: a CFADS Shock"; ws["B10"].font = BOLD; ws["B10"].fill = GRAY_FILL
ws["B11"] = "Year shocked"
c = ws.cell(row=11, column=3, value=3); c.font = BLUE; c.fill = YELLOW_FILL; c.number_format = NUM; c.border = BORDER
ws["B12"] = "CFADS shock this year (%)"
c = ws.cell(row=12, column=3, value=-0.30); c.font = BLUE; c.fill = YELLOW_FILL; c.number_format = PCT; c.border = BORDER

for i, h in enumerate(["", "", "Yr1", "Yr2", "Yr3", "Yr4", "Yr5"], start=1):
    ws.cell(row=14, column=i, value=h)
style_header_row(ws, 14, 5, start_col=3)
ws["B15"] = "Sculpted debt service (fixed, contractual)"
ws["B16"] = "Stressed CFADS (shock applied only in the shocked year)"
ws["B17"] = "Shortfall vs. debt service ($, before DSRA)"
ws["B18"] = "DSRA draw (min of shortfall, available DSRA balance)"
ws["B19"] = "Effective DSCR with DSRA support"
ws["B20"] = "Payment made in full WITH DSRA? (avoids payment default)"
ws["B21"] = "Payment made in full WITHOUT DSRA? (for comparison)"
ws["B22"] = "Distribution lock-up test (DSCR >= target covenant)?"
for col in range(3, 8):
    letter = get_column_letter(col)
    year = col - 2
    ws.cell(row=15, column=col, value=f"='Sculpted Debt Schedule'!{letter}8").number_format = CUR
    ws.cell(row=16, column=col,
            value=f"=IF($C$11={year},'Operating Cash Flow'!{letter}9*(1+$C$12),'Operating Cash Flow'!{letter}9)")
    ws.cell(row=16, column=col).number_format = CUR
    ws.cell(row=17, column=col, value=f"=MAX({letter}15-{letter}16,0)").number_format = CUR
    ws.cell(row=18, column=col, value=f"=MIN({letter}17,{letter}8)").number_format = CUR
    ws.cell(row=19, column=col, value=f"=IFERROR(({letter}16+{letter}18)/{letter}15,\"-\")").number_format = '0.00x'
    ws.cell(row=20, column=col,
            value=f'=IF({letter}16+{letter}18>={letter}15,"PAID IN FULL","PAYMENT DEFAULT")')
    ws.cell(row=21, column=col,
            value=f'=IF({letter}16>={letter}15,"PAID IN FULL","PAYMENT DEFAULT")')
    ws.cell(row=22, column=col,
            value=f'=IF({letter}19="-","-",IF({letter}19>=\'DSCR & Debt Sizing\'!$C$9,"CLEAR","LOCKED UP"))')
    for row in range(15, 23):
        ws.cell(row=row, column=col).border = BORDER
    ws.cell(row=20, column=col).font = BOLD
    ws.cell(row=21, column=col).font = BOLD
ws["B24"] = ("DSRA's actual job is preventing a PAYMENT default (cash available < debt service itself, DSCR<1.0x), "
             "not clearing the softer distribution-lock-up test (DSCR<target). A DSRA draw large enough to fund "
             "the payment in full can still leave the deal below its target DSCR and locked up from paying "
             "dividends -- the two are genuinely different triggers, not the same event twice. A DSRA draw also "
             "must be replenished from future surplus cash before any dividend to sponsors.")
ws["B24"].font = ITALIC_GRAY
ws.sheet_view.showGridLines = False

add_sources_checks(
    wb,
    sources=[
        ("Sculpted debt service = CFADS / target DSCR", "Standard project-finance debt sizing convention -- sculpting hits the covenant exactly rather than over- or under-sizing debt service", "Standard practice", "Assumes CFADS forecast is reliable; sculpting to a forecast that proves optimistic under-reserves the actual repayment capacity"),
        ("DSRA sized at N months of forward debt service", "Standard project-finance security package feature (near-universal in infrastructure/PPP financings)", "Standard practice", "Forward-looking DSRA convention used here; some deals instead use a trailing/historic DSRA definition"),
        ("Interest on beginning-of-period balance only", "Modeling convention used throughout this repository to avoid circular references", "Standard practice", "Matches the LBO and Private Credit debt schedules' convention"),
        ("Interest during construction (IDC) as avg-drawn-balance x rate x period / 2", "Standard linear-drawdown IDC approximation", "Standard practice", "A real S-curve drawdown profile would give a different (usually slightly lower) IDC than linear"),
    ],
    checks=[
        ("Ending balance ties: beginning - principal repayment = ending (Yr5)", "=IFERROR('Sculpted Debt Schedule'!G10-('Sculpted Debt Schedule'!G6-'Sculpted Debt Schedule'!G9),\"-\")", "0 (exact) once the schedule is populated"),
        ("Roll-forward ties: Yr2 beginning balance = Yr1 ending balance", "='Sculpted Debt Schedule'!D6-'Sculpted Debt Schedule'!C10", "0 (exact)"),
        ("DSRA draw never exceeds the required DSRA balance", "=IF(MAX(DSRA!C18:G18-DSRA!C8:G8)<=0.0001,TRUE,FALSE)", "TRUE"),
        ("DSRA prevents payment default in the shocked year even though the softer lock-up test still fails", "=IF(AND(DSRA!E20=\"PAID IN FULL\",DSRA!E21=\"PAYMENT DEFAULT\",DSRA!E22=\"LOCKED UP\"),TRUE,FALSE)", "TRUE at the default 30% Yr3 shock -- confirms DSRA cures the default without curing the covenant, the actual real-world distinction between the two triggers"),
    ],
)

add_refresh_log(wb)
out_path = "PROJECT_FINANCE_template.xlsx"
wb.save(out_path)
print("saved", out_path)
