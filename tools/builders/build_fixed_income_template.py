import openpyxl
from datetime import date
from template_helpers import *

wb = openpyxl.Workbook()
wb.remove(wb.active)

add_cover(wb, "[BOND/CURVE] — Fixed Income Model", [
    ("Instrument:", "[fill in]"),
    ("Issuer / sector:", "[fill in]"),
    ("Last refreshed:", "[date]"),
    ("Refresh cadence:", "Weekly"),
])

# ---------------- BOND PRICING ----------------
ws = wb.create_sheet("Bond Pricing")
set_col_widths(ws, [4, 30, 16, 40])
ws["B2"] = "Bond Pricing"; ws["B2"].font = TITLE
inputs = [
    ("Face value ($)", 1000, CUR),
    ("Coupon rate (annual, %)", 0.05, PCT),
    ("Coupon frequency (payments/yr)", 2, NUM),
    ("Years to maturity", 10, NUM),
    ("Yield to maturity (annual, %)", 0.055, PCT),
]
r = 5
for label, default, fmt in inputs:
    ws.cell(row=r, column=2, value=label).font = BLACK
    c = ws.cell(row=r, column=3, value=default); c.font = BLUE; c.fill = YELLOW_FILL
    c.number_format = fmt; c.border = BORDER
    r += 1
ws["B11"] = "Price (using PV formula)"
ws["C11"] = "=-PV(C9/C7,C7*C8,C5*C6/C7,C5)"
ws["C11"].font = BOLD; ws["C11"].number_format = CUR2; ws["C11"].border = BORDER
ws["D11"] = "PV(YTM per period, n periods, coupon per period, face value)"
ws["D11"].font = ITALIC_GRAY
ws["B12"] = "Price as % of par"
ws["C12"] = "=IFERROR(C11/C5,\"-\")"; ws["C12"].number_format = PCT2; ws["C12"].border = BORDER
ws["B13"] = "Current yield (annual coupon / price)"
ws["C13"] = "=IFERROR(C5*C6/C11,\"-\")"; ws["C13"].number_format = PCT2; ws["C13"].border = BORDER
ws.sheet_view.showGridLines = False

# ---------------- DURATION & CONVEXITY ----------------
ws = wb.create_sheet("Duration & Convexity")
set_col_widths(ws, [4, 34, 16, 40])
ws["B2"] = "Duration & Convexity"; ws["B2"].font = TITLE
ws["B4"] = "Modified duration (approx., via price shock)"; ws["B4"].font = BOLD; ws["B4"].fill = GRAY_FILL
ws["B5"] = "Yield shock (bp) for numerical estimate"; ws["C5"] = 50; ws["C5"].font = BLUE; ws["C5"].number_format = '0'
ws["B6"] = "Price at YTM - shock"
ws["C6"] = "=-PV(('Bond Pricing'!C9-C5/10000)/'Bond Pricing'!C7,'Bond Pricing'!C7*'Bond Pricing'!C8,'Bond Pricing'!C5*'Bond Pricing'!C6/'Bond Pricing'!C7,'Bond Pricing'!C5)"
ws["C6"].number_format = CUR2
ws["B7"] = "Price at YTM + shock"
ws["C7"] = "=-PV(('Bond Pricing'!C9+C5/10000)/'Bond Pricing'!C7,'Bond Pricing'!C7*'Bond Pricing'!C8,'Bond Pricing'!C5*'Bond Pricing'!C6/'Bond Pricing'!C7,'Bond Pricing'!C5)"
ws["C7"].number_format = CUR2
ws["B8"] = "Modified duration = (P- - P+) / (2 x P0 x shock in decimal)"
ws["C8"] = "=IFERROR((C6-C7)/(2*'Bond Pricing'!C11*(C5/10000)),\"-\")"
ws["C8"].font = BOLD; ws["C8"].number_format = '0.00'
ws["B9"] = "Convexity = (P- + P+ - 2xP0) / (P0 x shock^2)"
ws["C9"] = "=IFERROR((C6+C7-2*'Bond Pricing'!C11)/('Bond Pricing'!C11*(C5/10000)^2),\"-\")"
ws["C9"].number_format = '0.00'
ws["B10"] = "Est. price change for 100bp move (duration + convexity)"
ws["C10"] = "=IFERROR(-C8*0.01+0.5*C9*0.01^2,\"-\")"
ws["C10"].number_format = PCT2
for r2 in range(6, 11):
    ws.cell(row=r2, column=3).border = BORDER
ws.sheet_view.showGridLines = False

# ---------------- YIELD CURVE ----------------
ws = wb.create_sheet("Yield Curve")
set_col_widths(ws, [4, 14, 14, 14, 40])
ws["B2"] = "Yield Curve & Spread Analysis"; ws["B2"].font = TITLE
headers = ["", "Tenor", "Benchmark yield", "Instrument spread (bp)", "All-in yield"]
for i, h in enumerate(headers, start=1):
    ws.cell(row=4, column=i, value=h)
style_header_row(ws, 4, len(headers)-1)
tenors = ["3M", "2Y", "5Y", "10Y", "30Y"]
r = 5
for t in tenors:
    ws.cell(row=r, column=2, value=t).font = BLACK
    c_y = ws.cell(row=r, column=3, value=0); c_y.font = BLUE; c_y.number_format = PCT2; c_y.border = BORDER
    c_s = ws.cell(row=r, column=4, value=0); c_s.font = BLUE; c_s.number_format = '0'; c_s.border = BORDER
    c_all = ws.cell(row=r, column=5, value=f"=C{r}+D{r}/10000")
    c_all.number_format = PCT2; c_all.border = BORDER
    r += 1
ws["B11"] = "2s10s spread (bp)"
ws["C11"] = "=(C7-C6)*10000"; ws["C11"].number_format = '0'
ws["D11"] = "Negative = inverted curve"
ws["D11"].font = ITALIC_GRAY
ws.sheet_view.showGridLines = False

# ---------------- TOTAL RETURN SCENARIOS ----------------
ws = wb.create_sheet("Total Return Scenarios")
set_col_widths(ws, [4, 26] + [12]*7 + [40])
ws["B2"] = "1-Year Total Return Under Rate Shocks"; ws["B2"].font = TITLE
ws["B4"] = "Uses duration/convexity from the Duration & Convexity tab plus current yield as the income component — same approximation as that tab's single 100bp estimate, extended across a scenario grid."
ws["B4"].font = ITALIC_GRAY

shocks = [-100, -50, -25, 0, 25, 50, 100]
ws["B6"] = "Parallel shift (bp)"
for i, s in enumerate(shocks, start=3):
    c = ws.cell(row=6, column=i, value=s); c.font = BOLD; c.fill = HEADER_FILL
    c.font = BOLD_WHITE; c.alignment = Alignment(horizontal="center")
    c.number_format = '+0;-0'

ws["B7"] = "Price return (duration + convexity)"
for i, s in enumerate(shocks, start=3):
    letter = get_column_letter(i)
    ws.cell(row=7, column=i,
            value=f"=IFERROR(-'Duration & Convexity'!$C$8*({letter}6/10000)"
                  f"+0.5*'Duration & Convexity'!$C$9*({letter}6/10000)^2,\"-\")")
    ws.cell(row=7, column=i).number_format = PCT2
    ws.cell(row=7, column=i).border = BORDER

ws["B8"] = "Income return (current yield)"
for i, s in enumerate(shocks, start=3):
    letter = get_column_letter(i)
    ws.cell(row=8, column=i, value="='Bond Pricing'!$C$13")
    ws.cell(row=8, column=i).font = GREEN
    ws.cell(row=8, column=i).number_format = PCT2
    ws.cell(row=8, column=i).border = BORDER

ws["B9"] = "Total return"; ws["B9"].font = BOLD
for i, s in enumerate(shocks, start=3):
    letter = get_column_letter(i)
    ws.cell(row=9, column=i, value=f"={letter}7+{letter}8")
    ws.cell(row=9, column=i).font = BOLD
    ws.cell(row=9, column=i).number_format = PCT2
    ws.cell(row=9, column=i).border = BORDER
    ws.cell(row=9, column=i).fill = YELLOW_FILL
ws.sheet_view.showGridLines = False

# ---------------- ACCRUED INTEREST & CLEAN/DIRTY PRICE ----------------
# Bond Pricing above computes a "clean" price valued exactly on a coupon
# date — the theoretical PV. In practice a bond trades and settles between
# coupon dates, and the buyer owes the seller the coupon that's accrued
# since the last payment: the price you SEE quoted (clean) is not the cash
# that actually changes hands at settlement (dirty/invoice price = clean +
# accrued). Day-count convention changes the accrued-interest number even
# for the identical settlement date — 30/360 (standard for most corporate
# bonds) and Actual/Actual (standard for Treasuries) do not agree.
ws = wb.create_sheet("Accrued Interest & Settlement")
set_col_widths(ws, [4, 34, 16, 40])
ws["B2"] = "Accrued Interest & Clean/Dirty Price"; ws["B2"].font = TITLE
ws["B4"] = "Inputs"; ws["B4"].font = BOLD; ws["B4"].fill = GRAY_FILL
ws["B5"] = "Day-count convention (30/360 or Actual/Actual)"
ws["C5"] = "30/360"; ws["C5"].font = BLUE; ws["C5"].fill = YELLOW_FILL; ws["C5"].border = BORDER
ws["B6"] = "Last coupon date"
ws["C6"] = date(2026, 1, 1); ws["C6"].font = BLUE; ws["C6"].fill = YELLOW_FILL
ws["C6"].number_format = "yyyy-mm-dd"; ws["C6"].border = BORDER
ws["B7"] = "Next coupon date"
ws["C7"] = date(2026, 7, 1); ws["C7"].font = BLUE; ws["C7"].fill = YELLOW_FILL
ws["C7"].number_format = "yyyy-mm-dd"; ws["C7"].border = BORDER
ws["B8"] = "Settlement date"
ws["C8"] = date(2026, 4, 1); ws["C8"].font = BLUE; ws["C8"].fill = YELLOW_FILL
ws["C8"].number_format = "yyyy-mm-dd"; ws["C8"].border = BORDER

ws["B10"] = "Day Count"; ws["B10"].font = BOLD; ws["B10"].fill = GRAY_FILL
ws["B11"] = "Days accrued (last coupon -> settlement)"
ws["C11"] = '=IF($C$5="30/360",DAYS360(C6,C8),C8-C6)'
ws["C11"].number_format = "0"; ws["C11"].border = BORDER
ws["B12"] = "Days in full coupon period (last coupon -> next coupon)"
ws["C12"] = '=IF($C$5="30/360",DAYS360(C6,C7),C7-C6)'
ws["C12"].number_format = "0"; ws["C12"].border = BORDER
ws["B13"] = "Accrual fraction of the period"
ws["C13"] = "=IFERROR(C11/C12,\"-\")"; ws["C13"].number_format = "0.0000"; ws["C13"].border = BORDER

ws["B15"] = "Accrued Interest & Invoice Price"; ws["B15"].font = BOLD; ws["B15"].fill = GRAY_FILL
ws["B16"] = "Periodic coupon (from Bond Pricing)"
ws["C16"] = "='Bond Pricing'!C5*'Bond Pricing'!C6/'Bond Pricing'!C7"
ws["C16"].font = GREEN; ws["C16"].number_format = CUR2; ws["C16"].border = BORDER
ws["B17"] = "Accrued interest"
ws["C17"] = "=IFERROR(C16*C13,\"-\")"; ws["C17"].font = BOLD; ws["C17"].number_format = CUR2
ws["C17"].border = BORDER
ws["B18"] = "Clean price (from Bond Pricing — quoted market price)"
ws["C18"] = "='Bond Pricing'!C11"; ws["C18"].font = GREEN; ws["C18"].number_format = CUR2
ws["C18"].border = BORDER
ws["B19"] = "Dirty / invoice price (clean + accrued — what the buyer actually pays)"
ws["C19"] = "=IFERROR(C18+C17,\"-\")"; ws["C19"].font = BOLD; ws["C19"].number_format = CUR2
ws["C19"].fill = YELLOW_FILL; ws["C19"].border = BORDER
ws["D19"] = "This is the number that actually settles — quoting only the clean price is a market convention, not the real cash flow"
ws["D19"].font = ITALIC_GRAY
ws.sheet_view.showGridLines = False

add_refresh_log(wb)
out_path = "FIXED_INCOME_template.xlsx"
wb.save(out_path)
print("saved", out_path)
