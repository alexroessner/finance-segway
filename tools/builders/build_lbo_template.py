"""
Builds LBO_template.xlsx — private equity / merchant banking archetype.
Distinct mechanics from the IB base template: Sources & Uses, multi-tranche
debt schedule with cash sweep, and an IRR/MOIC returns waterfall.
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
PCT2 = '0.00%;(0.00%);"-"'
MULT = '0.0x'
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
ws["B2"] = "[TARGET] — LBO Model"; ws["B2"].font = TITLE
# "Last refreshed" MUST land on row 6 (C6) and the next material date on row
# 7 (C7) -- weekly_refresh_check.py reads those two cells unconditionally,
# regardless of archetype. An earlier version of this Cover tab put Entry
# date before Last refreshed, which shifted both by one row: the checker
# silently read Entry date as the refresh date and the real refresh date as
# the next-material-date, on every Private Equity / Merchant Banking
# instance (both domains share this template).
fields = [("Sponsor:", ""), ("Deal type:", "LBO / take-private / add-on"),
          ("Last refreshed:", "[date]"), ("Next covenant/refinancing date:", "[date]"),
          ("Entry date:", "[date]"),
          ("Hold period (yrs):", 5), ("Refresh cadence:", "Weekly"),
          ("Active scenario (Base or Downside):", "Base")]
r = 4
for label, default in fields:
    ws.cell(row=r, column=2, value=label).font = BOLD
    c = ws.cell(row=r, column=3, value=default); c.font = BLUE
    r += 1
ws.sheet_view.showGridLines = False

# ---------------- SOURCES & USES ----------------
ws = wb.create_sheet("Sources & Uses")
set_col_widths(ws, [4, 26, 14, 6, 26, 14])
ws["B2"] = "Sources & Uses"; ws["B2"].font = TITLE
ws["B4"] = "Sources"; ws["B4"].font = BOLD; ws["B4"].fill = GRAY_FILL
ws["E4"] = "Uses"; ws["E4"].font = BOLD; ws["E4"].fill = GRAY_FILL

sources = ["Revolver (undrawn at close)", "Term Loan A", "Term Loan B", "Senior Notes",
           "Sponsor equity", "Management rollover"]
uses = ["Purchase of equity (at entry mult.)", "Refinance existing debt",
        "Transaction fees", "Financing fees", "Cash to balance sheet"]

r = 5
for s in sources:
    ws.cell(row=r, column=2, value=s).font = BLACK
    c = ws.cell(row=r, column=3, value=0); c.font = BLUE; c.number_format = CUR; c.border = BORDER
    r += 1
ws.cell(row=r, column=2, value="Total sources").font = BOLD
ws.cell(row=r, column=3, value=f"=SUM(C5:C{r-1})").font = BOLD
ws.cell(row=r, column=3).number_format = CUR
src_total_row = r

r = 5
for u in uses:
    ws.cell(row=r, column=5, value=u).font = BLACK
    c = ws.cell(row=r, column=6, value=0); c.font = BLUE; c.number_format = CUR; c.border = BORDER
    r += 1
ws.cell(row=r, column=5, value="Total uses").font = BOLD
ws.cell(row=r, column=6, value=f"=SUM(F5:F{r-1})").font = BOLD
ws.cell(row=r, column=6).number_format = CUR
uses_total_row = r

ws.cell(row=max(src_total_row, uses_total_row)+2, column=2, value="Check (sources = uses):").font = BOLD
ws.cell(row=max(src_total_row, uses_total_row)+2, column=3,
        value=f"=C{src_total_row}-F{uses_total_row}").number_format = CUR
ws.sheet_view.showGridLines = False

# ---------------- DEBT SCHEDULE ----------------
# Multi-tranche: revolver (liquidity backstop, draws on shortfall / repaid
# first from any surplus) + Term Loan A (senior, faster-amortizing, cheaper)
# + Term Loan B (junior, slower-amortizing, more expensive) — the standard
# real-world stack, not a single toy tranche. Cash sweep priority: revolver
# repaid in full before anything else, then TLA swept to zero before TLB
# sees a dollar (absolute priority by seniority, same logic as the
# Restructuring archetype's recovery waterfall).
ws = wb.create_sheet("Debt Schedule")
set_col_widths(ws, [4, 30, 12, 12, 12, 12, 12, 12, 4, 40, 12, 12, 14])
ws["B2"] = "Debt Schedule — Revolver / TLA / TLB (with cash sweep)"; ws["B2"].font = TITLE
for i, h in enumerate(["", "", "Yr0", "Yr1", "Yr2", "Yr3", "Yr4", "Yr5"], start=1):
    ws.cell(row=4, column=i, value=h)
style_header_row(ws, 4, 6, start_col=3)

# ---- assumptions block (drives every formula below; columns J:M) ----
# Base/Downside scenario switching, not a single point estimate — real deal
# models always run at least two cases, and the protocol's own workbook
# acceptance gates call out "explicit actual/forecast and Base/Downside
# boundaries" specifically. Column M ("Active") is what every formula in
# this sheet actually reads; it's a live switch off Cover!C11, not a copy.
ws["J4"] = "Assumptions"; ws["J4"].font = BOLD; ws["J4"].fill = GRAY_FILL
for col, label in ((11, "Base"), (12, "Downside"), (13, "Active")):
    c = ws.cell(row=4, column=col, value=label)
    c.font = BOLD_WHITE; c.fill = HEADER_FILL; c.alignment = Alignment(horizontal="center")
assumptions = [
    ("Entry EBITDA growth (%/yr)", 0.05, -0.03, PCT),
    ("FCF conversion (FCF / EBITDA, %)", 0.50, 0.35, PCT),
    ("TLA mandatory amort (% of original/yr)", 0.05, 0.05, PCT),
    ("TLA interest rate (%)", 0.070, 0.085, PCT2),
    ("TLB mandatory amort (% of original/yr)", 0.01, 0.01, PCT),
    ("TLB interest rate (%)", 0.095, 0.115, PCT2),
    ("Cash sweep (% of excess cash, after revolver)", 0.75, 0.75, PCT),
    ("Revolver commitment / capacity ($)", 50, 50, CUR),
    ("Revolver interest rate (%, on drawn balance)", 0.080, 0.095, PCT2),
]
r = 5
for label, base, downside, fmt in assumptions:
    ws.cell(row=r, column=10, value=label).font = BLACK
    cb = ws.cell(row=r, column=11, value=base); cb.font = BLUE; cb.fill = YELLOW_FILL
    cb.number_format = fmt; cb.border = BORDER
    cd = ws.cell(row=r, column=12, value=downside); cd.font = BLUE; cd.fill = YELLOW_FILL
    cd.number_format = fmt; cd.border = BORDER
    ca = ws.cell(row=r, column=13, value=f'=IF(Cover!$C$11="Downside",L{r},K{r})')
    ca.font = GREEN; ca.number_format = fmt; ca.border = BORDER
    r += 1
ws["J14"] = "Original TLA balance (Yr0, $)"
ws["M14"] = "='Sources & Uses'!C6"; ws["M14"].font = GREEN; ws["M14"].number_format = CUR
ws["M14"].border = BORDER
ws["J15"] = "Original TLB balance (Yr0, $)"
ws["M15"] = "='Sources & Uses'!C7"; ws["M15"].font = GREEN; ws["M15"].number_format = CUR
ws["M15"].border = BORDER
ws["J16"] = "Revolver drawn at close ($)"
ws["M16"] = "='Sources & Uses'!C5"; ws["M16"].font = GREEN; ws["M16"].number_format = CUR
ws["M16"].border = BORDER
ws["J18"] = "Deal terms (rows 14-16) don't vary by scenario, so they skip the"
ws["J19"] = "Base/Downside split and go straight in the Active column. Revolver"
ws["J20"] = "commitment (M12) is total facility SIZE available to draw against,"
ws["J21"] = "separate from the 'drawn at close' amount (M16, typically 0)."
for rr in (18, 19, 20, 21):
    ws.cell(row=rr, column=10).font = ITALIC_GRAY

# ---- EBITDA and FCF, grown off the entry EBITDA on the Returns tab ----
ws["B5"] = "EBITDA"; ws["B5"].font = GREEN
ws["C5"] = "=Returns!C5"; ws["C5"].font = GREEN
for col in range(4, 9):
    prev = get_column_letter(col - 1)
    ws.cell(row=5, column=col, value=f"={prev}5*(1+$M$5)")
ws["B6"] = "Cash flow available for debt service (FCF)"; ws["B6"].font = BLACK
for col in range(3, 9):
    letter = get_column_letter(col)
    ws.cell(row=6, column=col, value=f"={letter}5*$M$6")
for row in (5, 6):
    for c in range(3, 9):
        ws.cell(row=row, column=c).number_format = CUR
        ws.cell(row=row, column=c).border = BORDER

# ---- Revolver ----
ws["B8"] = "Revolving Credit Facility"; ws["B8"].font = BOLD
ws["B9"] = "  Beginning balance"
ws["B10"] = "  Interest expense (rate x beginning balance)"
ws["B11"] = "  Cash available for revolver / sweep decisions"
ws["B12"] = "  Draw / (repayment)"
ws["B13"] = "  Ending balance"
ws["B14"] = "  Excess cash remaining for term loan sweep"

ws["C9"] = "=$M$16"
for col in range(4, 9):
    prev = get_column_letter(col - 1)
    ws.cell(row=9, column=col, value=f"={prev}13")
for col in range(3, 9):
    letter = get_column_letter(col)
    ws.cell(row=10, column=col, value=f"={letter}9*$M$13")
    # Cash available = FCF less mandatory amort on BOTH term loans and ALL
    # interest (revolver + TLA + TLB) — everything here depends only on
    # beginning-of-period balances, so this stays acyclic even though the
    # term loan rows are defined further down the sheet.
    ws.cell(row=11, column=col,
            value=f"={letter}6-{letter}18-{letter}25-{letter}10-{letter}21-{letter}28")
    ws.cell(row=12, column=col,
            value=(f"=IF({letter}11<0,MIN(-{letter}11,$M$12-{letter}9),"
                   f"-MIN({letter}9,MAX(0,{letter}11)))"))
    ws.cell(row=13, column=col, value=f"={letter}9+{letter}12")
    ws.cell(row=14, column=col, value=f"=MAX(0,MAX(0,{letter}11)-{letter}9)")
for row in (9, 10, 11, 12, 13, 14):
    for c in range(3, 9):
        ws.cell(row=row, column=c).number_format = CUR
        ws.cell(row=row, column=c).border = BORDER
        ws.cell(row=row, column=c).font = BLACK

# ---- Term Loan A (senior, amortizing) ----
ws["B16"] = "Term Loan A (senior, amortizing)"; ws["B16"].font = BOLD
ws["B17"] = "  Beginning balance"
ws["B18"] = "  Mandatory amortization"
ws["B19"] = "  Cash sweep (after revolver fully repaid)"
ws["B20"] = "  Ending balance"
ws["B21"] = "  Interest expense (rate x beginning balance)"

ws["C17"] = "=$M$14"
for col in range(4, 9):
    prev = get_column_letter(col - 1)
    ws.cell(row=17, column=col, value=f"={prev}20")
for col in range(3, 9):
    letter = get_column_letter(col)
    ws.cell(row=18, column=col, value=f"=MIN($M$14*$M$7,{letter}17)")
    ws.cell(row=19, column=col, value=f"=MIN($M$11*{letter}14,{letter}17-{letter}18)")
    ws.cell(row=20, column=col, value=f"={letter}17-{letter}18-{letter}19")
    ws.cell(row=21, column=col, value=f"={letter}17*$M$8")
for row in (17, 18, 19, 20, 21):
    for c in range(3, 9):
        ws.cell(row=row, column=c).number_format = CUR
        ws.cell(row=row, column=c).border = BORDER
        ws.cell(row=row, column=c).font = BLACK

# ---- Term Loan B (junior — only sees a dollar once TLA is fully swept) ----
ws["B23"] = "Term Loan B (junior)"; ws["B23"].font = BOLD
ws["B24"] = "  Beginning balance"
ws["B25"] = "  Mandatory amortization"
ws["B26"] = "  Cash sweep (only after TLA fully repaid)"
ws["B27"] = "  Ending balance"
ws["B28"] = "  Interest expense (rate x beginning balance)"

ws["C24"] = "=$M$15"
for col in range(4, 9):
    prev = get_column_letter(col - 1)
    ws.cell(row=24, column=col, value=f"={prev}27")
for col in range(3, 9):
    letter = get_column_letter(col)
    ws.cell(row=25, column=col, value=f"=MIN($M$15*$M$9,{letter}24)")
    ws.cell(row=26, column=col, value=f"=MIN($M$11*{letter}14-{letter}19,{letter}24-{letter}25)")
    ws.cell(row=27, column=col, value=f"={letter}24-{letter}25-{letter}26")
    ws.cell(row=28, column=col, value=f"={letter}24*$M$10")
for row in (24, 25, 26, 27, 28):
    for c in range(3, 9):
        ws.cell(row=row, column=c).number_format = CUR
        ws.cell(row=row, column=c).border = BORDER
        ws.cell(row=row, column=c).font = BLACK

ws["B30"] = "Total debt (end of period)"; ws["B30"].font = BOLD
ws["B31"] = "Total interest expense"; ws["B31"].font = BOLD
ws["B32"] = "Total debt / EBITDA (leverage)"; ws["B32"].font = BOLD
for col in range(3, 9):
    letter = get_column_letter(col)
    ws.cell(row=30, column=col, value=f"={letter}13+{letter}20+{letter}27")
    ws.cell(row=30, column=col).number_format = CUR
    ws.cell(row=31, column=col, value=f"={letter}10+{letter}21+{letter}28")
    ws.cell(row=31, column=col).number_format = CUR
    ws.cell(row=32, column=col, value=f"=IFERROR({letter}30/{letter}5,\"-\")")
    ws.cell(row=32, column=col).number_format = MULT
    ws.cell(row=32, column=col).fill = YELLOW_FILL
ws.sheet_view.showGridLines = False

# ---------------- RETURNS WATERFALL ----------------
ws = wb.create_sheet("Returns")
set_col_widths(ws, [4, 28, 14, 14, 14, 14])
ws["B2"] = "Returns — IRR / MOIC"; ws["B2"].font = TITLE

ws["B4"] = "Entry"; ws["B4"].font = BOLD; ws["B4"].fill = GRAY_FILL
ws["B5"] = "Entry EBITDA"; ws["C5"] = 0; ws["C5"].font = BLUE; ws["C5"].number_format = CUR
ws["B6"] = "Entry multiple"; ws["C6"] = 0; ws["C6"].font = BLUE; ws["C6"].fill = YELLOW_FILL; ws["C6"].number_format = MULT
ws["B7"] = "Entry EV"; ws["C7"] = "=C5*C6"; ws["C7"].number_format = CUR
ws["B8"] = "Sponsor equity check"; ws["C8"] = "='Sources & Uses'!C9"; ws["C8"].font = GREEN; ws["C8"].number_format = CUR

ws["B10"] = "Exit"; ws["B10"].font = BOLD; ws["B10"].fill = GRAY_FILL
ws["B11"] = "Exit EBITDA (Yr5)"; ws["C11"] = "='Debt Schedule'!H5"; ws["C11"].font = GREEN; ws["C11"].number_format = CUR
# Exit multiple is scenario-aware (entry multiple isn't — it's a contractual
# fact of the deal that already happened; the exit multiple is the genuinely
# uncertain forward assumption). Downside cases pair worse operating
# performance with multiple compression — a distressed exit gets punished
# twice, not just once on EBITDA.
ws["D11"] = "Base"; ws["D11"].font = BOLD
ws["E11"] = "Downside"; ws["E11"].font = BOLD
ws["B12"] = "Exit multiple (Active)"
ws["C12"] = '=IFERROR(IF(Cover!$C$11="Downside",E12,D12),"-")'
ws["C12"].font = BOLD; ws["C12"].fill = YELLOW_FILL; ws["C12"].number_format = MULT
ws["D12"] = 0; ws["D12"].font = BLUE; ws["D12"].fill = YELLOW_FILL; ws["D12"].number_format = MULT
ws["E12"] = 0; ws["E12"].font = BLUE; ws["E12"].fill = YELLOW_FILL; ws["E12"].number_format = MULT
ws["B13"] = "Exit EV"; ws["C13"] = "=C11*C12"; ws["C13"].number_format = CUR
ws["B14"] = "Less: net debt at exit"; ws["C14"] = "='Debt Schedule'!H30"; ws["C14"].font = GREEN; ws["C14"].number_format = CUR
ws["B15"] = "Exit equity value"; ws["C15"] = "=C13-C14"; ws["C15"].font = BOLD; ws["C15"].number_format = CUR

ws["B17"] = "Deal-Level Returns (blended, before management promote)"; ws["B17"].font = BOLD; ws["B17"].fill = GRAY_FILL
ws["B18"] = "MOIC (exit equity value / ALL invested equity, sponsor + mgmt)"
ws["C18"] = "=IFERROR(C15/(C8+'Sources & Uses'!C10),\"-\")"; ws["C18"].font = BOLD; ws["C18"].number_format = MULT
ws["D18"] = "Everyone's return before the promote reallocates value from sponsor to management below — not the sponsor's actual net return"
ws["D18"].font = ITALIC_GRAY
ws["B19"] = "Hold period (yrs)"; ws["C19"] = "=Cover!C9"; ws["C19"].font = GREEN
ws["B20"] = "IRR"; ws["C20"] = "=IFERROR(C18^(1/C19)-1,\"-\")"; ws["C20"].font = BOLD; ws["C20"].number_format = PCT

# ---------------- MANAGEMENT PROMOTE / RATCHET ----------------
# Standard real-world structure absent from most teaching LBO models:
# management's rollover equity isn't just a pro-rata slice of proceeds —
# it typically carries a promote that kicks in once the sponsor clears an
# IRR hurdle, mechanically identical to a GP catch-up (see the Asset
# Management archetype's fee waterfall for the same idea from the fund
# side rather than the deal side).
ws["B22"] = "Management Promote / Ratchet"; ws["B22"].font = BOLD; ws["B22"].fill = GRAY_FILL
ws["B23"] = "Total sponsor + management invested equity"
ws["C23"] = "='Sources & Uses'!C9+'Sources & Uses'!C10"; ws["C23"].font = GREEN; ws["C23"].number_format = CUR
ws["B24"] = "Management rollover % of total equity"
ws["C24"] = "=IFERROR('Sources & Uses'!C10/C23,\"-\")"; ws["C24"].font = GREEN; ws["C24"].number_format = PCT
ws["B25"] = "IRR hurdle for promote to kick in"
ws["C25"] = 0.20; ws["C25"].font = BLUE; ws["C25"].fill = YELLOW_FILL; ws["C25"].number_format = PCT
ws["B26"] = "Management promote % of value created above hurdle"
ws["C26"] = 0.20; ws["C26"].font = BLUE; ws["C26"].fill = YELLOW_FILL; ws["C26"].number_format = PCT
ws["B27"] = "Hurdle equity value (invested equity grown at hurdle IRR)"
ws["C27"] = "=IFERROR(C23*(1+C25)^C19,\"-\")"; ws["C27"].number_format = CUR
ws["B28"] = "Value created above hurdle"
ws["C28"] = "=MAX(0,C15-C27)"; ws["C28"].number_format = CUR
ws["B29"] = "Management promote ($)"
ws["C29"] = "=C28*C26"; ws["C29"].font = BOLD; ws["C29"].number_format = CUR
ws["B30"] = "Management total proceeds (pro-rata rollover + promote)"
ws["C30"] = "=IFERROR(C24*C15+C29,\"-\")"; ws["C30"].font = BOLD; ws["C30"].number_format = CUR
ws["B31"] = "Sponsor net proceeds (exit equity value less management take)"
ws["C31"] = "=IFERROR(C15-C30,\"-\")"; ws["C31"].font = BOLD; ws["C31"].number_format = CUR
ws["B32"] = "Sponsor-only MOIC (on sponsor equity, net of promote paid away)"
ws["C32"] = "=IFERROR(C31/'Sources & Uses'!C9,\"-\")"; ws["C32"].font = BOLD; ws["C32"].number_format = MULT
ws["B33"] = "Sponsor-only IRR (net of promote paid away)"
ws["C33"] = "=IFERROR(C32^(1/C19)-1,\"-\")"; ws["C33"].font = BOLD; ws["C33"].number_format = PCT
ws["D33"] = "This is the number that actually matters to the sponsor's LPs — the blended IRR above overstates what the fund itself earns once management's promote is paid away"
ws["D33"].font = ITALIC_GRAY
for r2 in range(23, 34):
    ws.cell(row=r2, column=3).border = BORDER
ws.sheet_view.showGridLines = False

# ---------------- SENSITIVITY ----------------
ws = wb.create_sheet("Sensitivity")
set_col_widths(ws, [4, 20] + [12]*5)
ws["B2"] = "Sensitivity — IRR by Entry/Exit Multiple"; ws["B2"].font = TITLE
ws["B4"] = "Entry \\ Exit mult."; ws["B4"].font = BOLD; ws["B4"].fill = GRAY_FILL
exits = [7, 8, 9, 10, 11]
entries = [6, 7, 8, 9, 10]
for i, e in enumerate(exits, start=3):
    c = ws.cell(row=4, column=i, value=e); c.font = BOLD; c.fill = GRAY_FILL; c.number_format = MULT
for j, en in enumerate(entries, start=5):
    c = ws.cell(row=j, column=2, value=en); c.font = BOLD; c.fill = GRAY_FILL; c.number_format = MULT
    for i in range(3, 8):
        ws.cell(row=j, column=i, value="[data table — Excel What-If Analysis]").font = Font(
            name="Arial", size=8, italic=True, color="808080")
ws.sheet_view.showGridLines = False

add_sources_checks(
    wb,
    sources=[
        ("Multi-tranche cash sweep priority (revolver, then TLA, then TLB)", "Standard leveraged-loan credit-agreement absolute-priority cash sweep", "Standard practice", "Real credit agreements can have more nuanced sweep mechanics (e.g. leverage-based step-downs, as modeled in the Private Credit archetype) -- this uses strict seniority order only"),
        ("Interest computed off beginning-of-period balances only", "Modeling convention used throughout this repository to avoid circular references", "Standard practice", "Matches the Private Credit and Project Finance debt schedules' convention"),
        ("Management promote / ratchet above an IRR hurdle", "Standard PE deal-level management incentive structure, mechanically identical to a GP catch-up (see the Asset Management archetype's fee waterfall for the fund-side analogue)", "Standard practice", "Single hurdle/promote tier -- no multi-tier ratchet (increasing promote % at higher IRR bands), which some deals use"),
        ("Exit multiple is scenario-aware (Base/Downside); entry multiple is not", "Modeling choice: entry multiple is a contractual fact of the deal that already happened, exit multiple is the genuine forward uncertainty", "Modeling choice, documented on the Returns tab", "A downside case pairs worse operating performance with multiple compression -- a distressed exit is punished twice, not once on EBITDA alone"),
    ],
    checks=[
        ("Sources = Uses at close", "='Sources & Uses'!C13", "0 (exact)"),
        ("Total debt ties: revolver+TLA+TLB ending balances = Total debt row (Yr5)", "='Debt Schedule'!H30-('Debt Schedule'!H13+'Debt Schedule'!H20+'Debt Schedule'!H27)", "0 (exact)"),
        ("Sponsor-only IRR never exceeds blended IRR (promote only transfers value away from the sponsor, never adds to it)", "=IF(OR(NOT(ISNUMBER(Returns!C33)),NOT(ISNUMBER(Returns!C20))),TRUE,Returns!C33<=Returns!C20+0.0000001)", "TRUE"),
        ("Active debt-schedule assumptions match the Cover scenario selector", '=IF(Cover!$C$11="Downside",\'Debt Schedule\'!M5=\'Debt Schedule\'!L5,\'Debt Schedule\'!M5=\'Debt Schedule\'!K5)', "TRUE"),
    ],
)

# ---------------- REFRESH LOG ----------------
ws = wb.create_sheet("RefreshLog")
set_col_widths(ws, [4, 14, 16, 30, 30, 16])
ws["B2"] = "Refresh Log"; ws["B2"].font = TITLE
for i, h in enumerate(["", "Date", "Trigger", "What changed", "Reviewer notes", "Next check"], start=1):
    ws.cell(row=4, column=i, value=h)
style_header_row(ws, 4, 5, start_col=2)
ws.sheet_view.showGridLines = False

out_path = "LBO_template.xlsx"
wb.save(out_path)
print("saved", out_path)
