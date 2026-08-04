"""
Builds _template.xlsx — the master model template.
Tabs: Cover, Assumptions, IS, BS, CF, DCF, Comps, Sensitivity, RefreshLog
Convention: blue=hardcode input, black=formula, green=cross-sheet link, yellow fill=key assumption
"""
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from template_helpers import add_sources_checks

BLUE = Font(name="Arial", size=10, color="0000FF")
BLACK = Font(name="Arial", size=10, color="000000")
GREEN = Font(name="Arial", size=10, color="008000")
BOLD = Font(name="Arial", size=10, bold=True)
BOLD_WHITE = Font(name="Arial", size=11, bold=True, color="FFFFFF")
TITLE = Font(name="Arial", size=16, bold=True)
YELLOW_FILL = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
HEADER_FILL = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
GRAY_FILL = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

CUR = '$#,##0;($#,##0);"-"'
PCT = '0.0%;(0.0%);"-"'
MULT = '0.0x'
YR = '@'
ITALIC_GRAY = Font(name="Arial", size=8, italic=True, color="808080")

wb = openpyxl.Workbook()
wb.remove(wb.active)

def style_header_row(ws, row, ncols, start_col=1):
    for c in range(start_col, start_col + ncols):
        cell = ws.cell(row=row, column=c)
        cell.font = BOLD_WHITE
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal="center")

def set_col_widths(ws, widths):
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w

# ---------------- COVER ----------------
ws = wb.create_sheet("Cover")
set_col_widths(ws, [4, 30, 40, 4])
ws["B2"] = "[TICKER] — Company Name"
ws["B2"].font = TITLE
ws["B4"] = "Sector:"; ws["B4"].font = BOLD; ws["C4"] = "[fill in]"; ws["C4"].font = BLUE
ws["B5"] = "Coverage started:"; ws["B5"].font = BOLD; ws["C5"] = "[date]"; ws["C5"].font = BLUE
ws["B6"] = "Last refreshed:"; ws["B6"].font = BOLD; ws["C6"] = "[date]"; ws["C6"].font = BLUE
ws["B7"] = "Next earnings date:"; ws["B7"].font = BOLD; ws["C7"] = "[date]"; ws["C7"].font = BLUE
ws["B8"] = "Refresh cadence:"; ws["B8"].font = BOLD; ws["C8"] = "Weekly"; ws["C8"].font = BLACK
ws["B10"] = "Thesis (2-3 sentences):"; ws["B10"].font = BOLD
ws["B11"] = "[fill in]"; ws["B11"].font = BLUE
ws.merge_cells("B11:D14")
ws["B16"] = "COLOR LEGEND"; ws["B16"].font = BOLD
legend = [
    ("Blue text", "Hardcoded input / scenario lever — edit freely", BLUE),
    ("Black text", "Formula — do not overwrite", BLACK),
    ("Green text", "Link to another sheet in this workbook", GREEN),
    ("Yellow fill", "Key assumption — review every refresh", None),
]
r = 17
for label, desc, font in legend:
    ws.cell(row=r, column=2, value=label).font = font if font else BOLD
    if label == "Yellow fill":
        ws.cell(row=r, column=2).fill = YELLOW_FILL
    ws.cell(row=r, column=3, value=desc).font = BLACK
    r += 1
ws.sheet_view.showGridLines = False

# ---------------- ASSUMPTIONS ----------------
ws = wb.create_sheet("Assumptions")
set_col_widths(ws, [4, 30, 14, 14, 14, 14, 14, 40])
ws["B2"] = "Assumptions"; ws["B2"].font = TITLE
headers = ["", "Driver", "FY1", "FY2", "FY3", "FY4", "FY5", "Source / notes"]
for i, h in enumerate(headers, start=1):
    ws.cell(row=4, column=i, value=h)
style_header_row(ws, 4, len(headers))

rows = [
    ("Revenue growth %", PCT, "yellow"),
    ("Gross margin %", PCT, "yellow"),
    ("Opex % of revenue", PCT, "yellow"),
    ("Tax rate %", PCT, "yellow"),
    ("D&A % of capex", PCT, None),
    ("Capex % of revenue", PCT, None),
    ("NWC % of revenue chg", PCT, None),
    ("Shares outstanding (mm)", CUR, None),
    ("WACC %", PCT, "yellow"),
    ("Terminal growth %", PCT, "yellow"),
]
r = 5
for label, fmt, flag in rows:
    ws.cell(row=r, column=2, value=label).font = BLACK
    for c in range(3, 8):
        cell = ws.cell(row=r, column=c, value=0.0)
        cell.font = BLUE
        cell.number_format = fmt
        if flag == "yellow":
            cell.fill = YELLOW_FILL
        cell.border = BORDER
    ws.cell(row=r, column=8, value="Source: [10-K/10-Q cite or user estimate]").font = Font(name="Arial", size=9, italic=True, color="808080")
    r += 1
ws.sheet_view.showGridLines = False

# ---------------- INCOME STATEMENT ----------------
ws = wb.create_sheet("IS")
set_col_widths(ws, [4, 26, 13, 13, 13, 13, 13, 13, 13])
ws["B2"] = "Income Statement ($mm)"; ws["B2"].font = TITLE
per_headers = ["", "Line item", "FY-2A", "FY-1A", "FY0A", "FY1E", "FY2E", "FY3E", "FY4E"]
for i, h in enumerate(per_headers, start=1):
    ws.cell(row=4, column=i, value=h)
style_header_row(ws, 4, len(per_headers))

is_rows = ["Revenue", "  Revenue growth %", "COGS", "Gross profit", "  Gross margin %",
           "Opex", "EBITDA", "  EBITDA margin %", "D&A", "EBIT", "Interest expense",
           "Pre-tax income", "Tax", "Net income", "Diluted shares", "Diluted EPS"]
r = 5
first_data_row = r
for label in is_rows:
    is_pct = "%" in label
    ws.cell(row=r, column=2, value=label.strip()).font = BOLD if label in ("Revenue", "Gross profit", "EBITDA", "EBIT", "Net income") else BLACK
    for c in range(3, 10):
        cell = ws.cell(row=r, column=c)
        cell.border = BORDER
        cell.number_format = PCT if is_pct else CUR
        cell.font = BLACK
    r += 1
last_data_row = r - 1

# IS rows (from is_rows, r starting at 5): 5 Revenue, 6 Revenue growth %, 7 COGS,
# 8 Gross profit, 9 Gross margin %, 10 Opex, 11 EBITDA, 12 EBITDA margin %,
# 13 D&A, 14 EBIT, 15 Interest expense, 16 Pre-tax income, 17 Tax,
# 18 Net income, 19 Diluted shares, 20 Diluted EPS.
(rev_row, growth_row, cogs_row, gp_row, gm_row, opex_row, ebitda_row, ebitdam_row,
 da_row, ebit_row, int_row, pretax_row, tax_row, ni_row, shares_row, eps_row) = range(5, 21)

# Historical columns (C,D,E = FY-2A/FY-1A/FY0A) are hardcoded actuals the user
# enters — growth%/gross profit/gross margin% are still derived from them.
for c in range(4, 10):
    col_letter = get_column_letter(c)
    prev_letter = get_column_letter(c-1)
    ws.cell(row=growth_row, column=c, value=f"=IFERROR({col_letter}{rev_row}/{prev_letter}{rev_row}-1,\"-\")")
    ws.cell(row=gp_row, column=c, value=f"={col_letter}{rev_row}-{col_letter}{cogs_row}")
    ws.cell(row=gm_row, column=c, value=f"=IFERROR({col_letter}{gp_row}/{col_letter}{rev_row},\"-\")")

# Projection columns (F,G,H,I = FY1E-FY4E) map to Assumptions columns C,D,E,F
# (FY1-FY4) — a fixed 3-column offset (IS column minus 3). Fully driven by
# Assumptions from here down; nothing here should need manual input once the
# FY0A actuals and Assumptions are filled in.
for c in range(6, 10):
    col = get_column_letter(c)
    prev = get_column_letter(c-1)
    a = get_column_letter(c-3)  # matching Assumptions column
    ws.cell(row=rev_row, column=c, value=f"={prev}{rev_row}*(1+Assumptions!{a}5)")
    ws.cell(row=cogs_row, column=c, value=f"={col}{rev_row}*(1-Assumptions!{a}6)")
    ws.cell(row=opex_row, column=c, value=f"={col}{rev_row}*Assumptions!{a}7")
    ws.cell(row=ebitda_row, column=c, value=f"={col}{gp_row}-{col}{opex_row}")
    ws.cell(row=ebitdam_row, column=c, value=f"=IFERROR({col}{ebitda_row}/{col}{rev_row},\"-\")")
    # D&A driven off capex (capex itself isn't its own IS row — computed inline
    # as revenue x capex%, then x D&A-as-%-of-capex, per the Assumptions design).
    ws.cell(row=da_row, column=c,
            value=f"={col}{rev_row}*Assumptions!{a}10*Assumptions!{a}9")
    ws.cell(row=ebit_row, column=c, value=f"={col}{ebitda_row}-{col}{da_row}")
    # Interest held flat at the last actual (FY0A, column E) — avoids a
    # circular reference to the Balance Sheet's debt balance, which this
    # simplified template doesn't otherwise schedule. Deals with real debt
    # schedules should override this with a proper link.
    ws.cell(row=int_row, column=c, value=f"=$E${int_row}")
    ws.cell(row=pretax_row, column=c, value=f"={col}{ebit_row}-{col}{int_row}")
    ws.cell(row=tax_row, column=c, value=f"={col}{pretax_row}*Assumptions!{a}8")
    ws.cell(row=ni_row, column=c, value=f"={col}{pretax_row}-{col}{tax_row}")
    ws.cell(row=shares_row, column=c, value=f"=Assumptions!{a}12")
    ws.cell(row=eps_row, column=c, value=f"=IFERROR({col}{ni_row}/{col}{shares_row},\"-\")")
ws.sheet_view.showGridLines = False
ws.freeze_panes = "C5"

# ---------------- BALANCE SHEET ----------------
ws = wb.create_sheet("BS")
set_col_widths(ws, [4, 26, 13, 13, 13, 13, 13])
ws["B2"] = "Balance Sheet ($mm)"; ws["B2"].font = TITLE
for i, h in enumerate(["", "Line item", "FY-1A", "FY0A", "FY1E", "FY2E", "FY3E"], start=1):
    ws.cell(row=4, column=i, value=h)
style_header_row(ws, 4, 6)
bs_rows = ["Cash & equivalents", "Accounts receivable", "Inventory", "Total current assets",
           "PP&E net", "Goodwill & intangibles", "Total assets",
           "Accounts payable", "Debt (current)", "Total current liabilities",
           "Long-term debt", "Total liabilities", "Total equity"]
r = 5
for label in bs_rows:
    ws.cell(row=r, column=2, value=label).font = BOLD if "Total" in label else BLACK
    for c in range(3, 8):
        cell = ws.cell(row=r, column=c); cell.number_format = CUR; cell.border = BORDER; cell.font = BLACK
    r += 1

# Rows: 5 Cash, 6 AR, 7 Inventory, 8 Total current assets, 9 PP&E, 10 Goodwill,
# 11 Total assets, 12 AP, 13 Debt (current), 14 Total current liab,
# 15 LT debt, 16 Total liabilities, 17 Total equity. Every line item (5-7,
# 9-10, 12-13, 15, 17) stays a manual input — this template doesn't project
# a full balance sheet roll-forward, only the arithmetic totals, so those
# always tie to whatever the user enters above them.
for c in range(3, 8):
    col = get_column_letter(c)
    ws.cell(row=8, column=c, value=f"={col}5+{col}6+{col}7")
    ws.cell(row=11, column=c, value=f"={col}8+{col}9+{col}10")
    ws.cell(row=14, column=c, value=f"={col}12+{col}13")
    ws.cell(row=16, column=c, value=f"={col}14+{col}15")

ws["B19"] = "Balance check (Total assets - Total liabilities - Total equity, should = 0)"
ws["B19"].font = ITALIC_GRAY
for c in range(3, 8):
    col = get_column_letter(c)
    cell = ws.cell(row=19, column=c, value=f"={col}11-{col}16-{col}17")
    cell.number_format = CUR
    cell.border = BORDER
ws.sheet_view.showGridLines = False

# ---------------- CASH FLOW ----------------
ws = wb.create_sheet("CF")
set_col_widths(ws, [4, 26, 13, 13, 13, 13, 13])
ws["B2"] = "Cash Flow ($mm)"; ws["B2"].font = TITLE
for i, h in enumerate(["", "Line item", "FY-1A", "FY0A", "FY1E", "FY2E", "FY3E"], start=1):
    ws.cell(row=4, column=i, value=h)
style_header_row(ws, 4, 6)
cf_rows = ["Net income", "+ D&A", "+/- Change in NWC", "Cash flow from operations",
           "Capex", "Free cash flow", "Debt issuance/(repayment)", "Dividends/buybacks",
           "Net change in cash"]
r = 5
for label in cf_rows:
    ws.cell(row=r, column=2, value=label).font = BOLD if label in ("Cash flow from operations", "Free cash flow") else BLACK
    for c in range(3, 8):
        cell = ws.cell(row=r, column=c); cell.number_format = CUR; cell.border = BORDER; cell.font = BLACK
    r += 1

# Rows: 5 NI, 6 D&A, 7 +/- NWC chg, 8 CFO, 9 Capex, 10 FCF, 11 Debt iss/(repay),
# 12 Dividends, 13 Net change in cash. Capex/dividends entered as negative
# numbers (outflows), consistent with the "-" convention used elsewhere in
# this repo (e.g. the LBO and Real Estate archetypes).
for c in range(3, 8):
    col = get_column_letter(c)
    ws.cell(row=8, column=c, value=f"={col}5+{col}6+{col}7")
    ws.cell(row=10, column=c, value=f"={col}8+{col}9")
    ws.cell(row=13, column=c, value=f"={col}10+{col}11+{col}12")

# Projection columns only (E,F,G = FY1E-FY3E) pull NI and D&A straight from
# the Income Statement — a fixed +1 column offset (CF's FY1E is column E,
# IS's FY1E is column F, because IS carries one more historical year than
# CF/BS do). Historicals (C,D) stay manual inputs, same as IS's own
# historical columns.
for c in range(5, 8):
    col = get_column_letter(c)
    is_col = get_column_letter(c + 1)
    ws.cell(row=5, column=c, value=f"=IS!{is_col}18")
    ws.cell(row=5, column=c).font = GREEN
    ws.cell(row=6, column=c, value=f"=IS!{is_col}13")
    ws.cell(row=6, column=c).font = GREEN
ws.sheet_view.showGridLines = False

# ---------------- DCF ----------------
ws = wb.create_sheet("DCF")
set_col_widths(ws, [4, 26, 13, 13, 13, 13, 13, 4, 22, 14])
ws["B2"] = "DCF Valuation"; ws["B2"].font = TITLE
for i, h in enumerate(["", "", "FY1E", "FY2E", "FY3E", "FY4E", "FY5E"], start=1):
    ws.cell(row=4, column=i, value=h)
style_header_row(ws, 4, 5, start_col=3)
ws["B5"] = "Unlevered FCF"
# DCF's FY1E-FY4E (columns C-F) map to IS's FY1E-FY4E (columns F-I, offset +3)
# and, conveniently, DCF's own columns already line up 1:1 with Assumptions'
# FY1-FY5 columns (both start FY1 at column C) — no offset needed there.
# Unlevered FCF = EBIT x (1-tax) + D&A - Capex, computed straight off the IS
# (not CF's levered FCF, which nets out interest — a DCF wants the unlevered
# figure). Capex isn't its own IS line, so it's rebuilt inline exactly like
# the IS's own D&A formula does: revenue x capex%.
for c in range(3, 7):
    col = get_column_letter(c)
    is_col = get_column_letter(c + 3)
    ws.cell(row=5, column=c,
            value=(f"=IS!{is_col}14*(1-Assumptions!{col}8)+IS!{is_col}13"
                   f"-IS!{is_col}5*Assumptions!{col}10"))
    ws.cell(row=5, column=c).font = GREEN
    ws.cell(row=5, column=c).number_format = CUR
# FY5E (column G) has no matching IS column (IS only projects 4 years) —
# extend it by growing FY4E's unlevered FCF at the Assumptions FY5 revenue
# growth rate, a standard one-year bridge to a 5-year DCF window.
ws["G5"] = "=F5*(1+Assumptions!G5)"
ws["G5"].font = GREEN
ws["G5"].number_format = CUR
ws["B6"] = "Discount factor"
ws["B7"] = "PV of FCF"
for c in range(3, 8):
    col = get_column_letter(c)
    ws.cell(row=6, column=c, value=f"=1/(1+$I$5)^({c-2})").number_format = '0.000'
    ws.cell(row=7, column=c, value=f"={col}5*{col}6").number_format = CUR

ws["H4"] = "Key outputs"; ws["H4"].font = BOLD
ws["H5"] = "WACC"; ws["I5"] = 0.10; ws["I5"].font = BLUE; ws["I5"].fill = YELLOW_FILL; ws["I5"].number_format = PCT
ws["H6"] = "Terminal growth"; ws["I6"] = 0.025; ws["I6"].font = BLUE; ws["I6"].fill = YELLOW_FILL; ws["I6"].number_format = PCT
ws["H7"] = "Terminal value"; ws["I7"] = "=G5*(1+I6)/(I5-I6)"; ws["I7"].number_format = CUR
ws["H8"] = "PV of terminal value"; ws["I8"] = "=I7*G6"; ws["I8"].number_format = CUR
ws["H9"] = "Sum PV of FCF"; ws["I9"] = "=SUM(C7:G7)"; ws["I9"].number_format = CUR
ws["H10"] = "Enterprise value"; ws["I10"] = "=I8+I9"; ws["I10"].font = BOLD; ws["I10"].number_format = CUR
ws["H11"] = "Less: net debt"; ws["I11"] = 0; ws["I11"].font = BLUE; ws["I11"].number_format = CUR
ws["H12"] = "Equity value"; ws["I12"] = "=I10-I11"; ws["I12"].font = BOLD; ws["I12"].number_format = CUR
ws["H13"] = "Diluted shares (mm)"; ws["I13"] = 1; ws["I13"].font = BLUE; ws["I13"].number_format = CUR
ws["H14"] = "Implied value/share"; ws["I14"] = "=I12/I13"; ws["I14"].font = BOLD; ws["I14"].number_format = CUR
ws.sheet_view.showGridLines = False

# ---------------- COMPS ----------------
ws = wb.create_sheet("Comps")
set_col_widths(ws, [4, 22, 12, 12, 12, 12, 12, 12])
ws["B2"] = "Comparable Companies"; ws["B2"].font = TITLE
comp_headers = ["", "Ticker", "Price", "Mkt Cap", "EV", "EV/Rev", "EV/EBITDA", "P/E"]
for i, h in enumerate(comp_headers, start=1):
    ws.cell(row=4, column=i, value=h)
style_header_row(ws, 4, len(comp_headers))
for r in range(5, 12):
    ws.cell(row=r, column=2, value="[TICKER]").font = BLUE
    for c in range(3, 9):
        cell = ws.cell(row=r, column=c, value=0)
        cell.font = BLUE
        cell.number_format = MULT if c >= 6 else CUR
        cell.border = BORDER
ws.cell(row=13, column=2, value="Median").font = BOLD
for c in range(3, 9):
    col = get_column_letter(c)
    ws.cell(row=13, column=c, value=f"=MEDIAN({col}5:{col}12)").font = BOLD
    ws.cell(row=13, column=c).number_format = MULT if c >= 6 else CUR
ws.sheet_view.showGridLines = False

# ---------------- VALUATION CROSS-CHECK ----------------
ws = wb.create_sheet("Valuation Cross-Check")
set_col_widths(ws, [4, 40, 16, 46])
ws["B2"] = "DCF vs. Comps: Valuation Triangulation"; ws["B2"].font = TITLE
ws["B3"] = ("No banker trusts a DCF in isolation -- the terminal value assumption alone can swing it wildly. "
            "This applies the Comps tab's own median multiples to the company's own financials to get a SECOND, "
            "independent valuation estimate, then compares it to the DCF. A large gap isn't necessarily wrong, "
            "but it means the DCF's growth/WACC/terminal-growth assumptions are pricing in something the "
            "market's current multiples for comparable companies are not -- and that's worth a second look, not "
            "an automatic override of either number.")
ws["B3"].font = ITALIC_GRAY

ws["B5"] = "From the DCF"; ws["B5"].font = BOLD; ws["B5"].fill = GRAY_FILL
ws["B6"] = "DCF-implied value/share"
ws["C6"] = "=DCF!I14"; ws["C6"].font = GREEN; ws["C6"].number_format = CUR; ws["C6"].border = BORDER
ws["B7"] = "Net debt (same figure as the DCF)"
ws["C7"] = "=DCF!I11"; ws["C7"].font = GREEN; ws["C7"].number_format = CUR; ws["C7"].border = BORDER
ws["B8"] = "Diluted shares (mm)"
ws["C8"] = "=DCF!I13"; ws["C8"].font = GREEN; ws["C8"].number_format = CUR; ws["C8"].border = BORDER

ws["B10"] = "From Comps (median multiples x this company's own financials)"
ws["B10"].font = BOLD; ws["B10"].fill = GRAY_FILL
ws["B11"] = "Company FY1E revenue"
ws["C11"] = "=IS!F5"; ws["C11"].font = GREEN; ws["C11"].number_format = CUR; ws["C11"].border = BORDER
ws["B12"] = "Company FY1E EBITDA"
ws["C12"] = "=IS!F11"; ws["C12"].font = GREEN; ws["C12"].number_format = CUR; ws["C12"].border = BORDER
ws["B13"] = "Comps median EV/Revenue"
ws["C13"] = "=Comps!F13"; ws["C13"].font = GREEN; ws["C13"].number_format = MULT; ws["C13"].border = BORDER
ws["B14"] = "Comps median EV/EBITDA"
ws["C14"] = "=Comps!G13"; ws["C14"].font = GREEN; ws["C14"].number_format = MULT; ws["C14"].border = BORDER
ws["B15"] = "Comps-implied EV (EV/Revenue method)"
ws["C15"] = "=C11*C13"; ws["C15"].number_format = CUR; ws["C15"].border = BORDER
ws["B16"] = "Comps-implied EV (EV/EBITDA method)"
ws["C16"] = "=C12*C14"; ws["C16"].number_format = CUR; ws["C16"].border = BORDER
ws["B17"] = "Comps-implied EV (average of both methods)"
ws["C17"] = "=AVERAGE(C15,C16)"; ws["C17"].font = BOLD; ws["C17"].number_format = CUR; ws["C17"].border = BORDER
ws["B18"] = "Comps-implied equity value"
ws["C18"] = "=C17-C7"; ws["C18"].number_format = CUR; ws["C18"].border = BORDER
ws["B19"] = "Comps-implied value/share"
ws["C19"] = "=IFERROR(C18/C8,\"-\")"; ws["C19"].font = BOLD; ws["C19"].number_format = CUR; ws["C19"].border = BORDER

ws["B21"] = "Triangulation"; ws["B21"].font = BOLD; ws["B21"].fill = GRAY_FILL
ws["B22"] = "DCF vs. Comps: premium/(discount)"
ws["C22"] = "=IFERROR(C6/C19-1,\"-\")"; ws["C22"].font = BOLD; ws["C22"].number_format = PCT
ws["C22"].fill = YELLOW_FILL; ws["C22"].border = BORDER
ws["D22"] = "Large positive = DCF is pricing in more than the market currently pays for comparable companies; large negative = the opposite. Investigate the gap, don't just average it away."
ws["D22"].font = ITALIC_GRAY
ws.sheet_view.showGridLines = False

# ---------------- SENSITIVITY ----------------
ws = wb.create_sheet("Sensitivity")
set_col_widths(ws, [4, 20] + [12]*6)
ws["B2"] = "Sensitivity — Implied Value/Share"; ws["B2"].font = TITLE
ws["B4"] = "WACC \\ Term. growth"; ws["B4"].font = BOLD
ws["B4"].fill = GRAY_FILL
term_g = [0.015, 0.02, 0.025, 0.03, 0.035]
waccs = [0.08, 0.09, 0.10, 0.11, 0.12]
for i, g in enumerate(term_g, start=3):
    c = ws.cell(row=4, column=i, value=g); c.number_format = PCT; c.font = BOLD; c.fill = GRAY_FILL
for j, w in enumerate(waccs, start=5):
    c = ws.cell(row=j, column=2, value=w); c.number_format = PCT; c.font = BOLD; c.fill = GRAY_FILL
    for i in range(3, 8):
        cell = ws.cell(row=j, column=i, value="[data table — Excel What-If Analysis]")
        cell.font = Font(name="Arial", size=8, italic=True, color="808080")
ws.sheet_view.showGridLines = False

# ---------------- REFRESH LOG ----------------
ws = wb.create_sheet("RefreshLog")
set_col_widths(ws, [4, 14, 16, 30, 30, 16])
ws["B2"] = "Refresh Log"; ws["B2"].font = TITLE
log_headers = ["", "Date", "Trigger", "What changed", "Reviewer notes", "Next check"]
for i, h in enumerate(log_headers, start=1):
    ws.cell(row=4, column=i, value=h)
style_header_row(ws, 4, len(log_headers))
for r in range(5, 15):
    for c in range(2, 7):
        ws.cell(row=r, column=c).border = BORDER
ws.sheet_view.showGridLines = False

add_sources_checks(
    wb,
    sources=[
        ("DCF vs. Comps valuation triangulation", "Standard sell-side/buy-side practice: no single valuation method is trusted in isolation", "Standard practice", "A gap between methods is a prompt to investigate, not a signal either number is wrong -- comps and DCF answer related but distinct questions"),
        ("Unlevered FCF = EBIT x (1-tax) + D&A - Capex", "Standard DCF unlevered free cash flow build", "Standard practice", "Uses the IS's EBIT/D&A rather than CF's levered FCF, which nets out interest -- a DCF wants the unlevered figure"),
        ("Comps-implied EV blended as a simple average of the EV/Revenue and EV/EBITDA methods", "Modeling choice for this template", "Modeling choice, not a universal convention", "A weighted blend (e.g. favoring EV/EBITDA for a mature business) may be more appropriate depending on the company -- simple average is the template default"),
        ("Interest expense held flat at the last actual (no debt schedule)", "Simplification documented directly on the IS tab", "Modeling choice, stated on the sheet", "Avoids a circular reference to a Balance Sheet debt schedule this simplified template doesn't build -- a real deal model needs an actual debt schedule"),
    ],
    checks=[
        ("Balance sheet balances (Assets = Liabilities + Equity) across every projected year", "=SUMPRODUCT(ABS(BS!C19:G19))", "0 (exact) once the Balance Sheet is populated -- BS!row19 is this template's own balance-check row"),
        ("Comps-implied value/share is positive whenever both multiples and financials are populated", "=IF(AND(ISNUMBER('Valuation Cross-Check'!C19),'Valuation Cross-Check'!C11>0,'Valuation Cross-Check'!C13>0),'Valuation Cross-Check'!C19>0,TRUE)", "TRUE"),
        ("DCF terminal value uses the SAME terminal growth rate as its own discount-rate spread (WACC > terminal growth, not a divide-by-negative)", "=IF(DCF!I5>DCF!I6,TRUE,FALSE)", "TRUE -- the Gordon Growth terminal-value formula is undefined/nonsensical when WACC <= terminal growth"),
        ("CF's Net income and D&A tie exactly to the IS (cross-sheet link, not a re-entered duplicate)", "=SUMPRODUCT(ABS(CF!E5:G5-IS!F18:H18))+SUMPRODUCT(ABS(CF!E6:G6-IS!F13:H13))", "0 (exact) -- confirms the green cross-sheet links actually pull the IS figures, not stale hardcodes"),
    ],
)

wb.move_sheet("Cover", offset=-len(wb.sheetnames))
out_path = "_template_BASE.xlsx"
wb.save(out_path)
print("saved", out_path)
