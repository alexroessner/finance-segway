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

# ---- Closed-form (analytic) cross-check: build the actual period-by-
# period cash flow schedule and derive Macaulay/modified duration and
# convexity from their textbook definitions (sum of t x PV(CF_t), sum of
# t(t+1) x PV(CF_t)), rather than the finite-difference price-shock
# approximation above. The two methods are conceptually independent
# (one differentiates the price formula numerically, the other sums a
# closed-form series) and should agree closely for a well-behaved bond. ----
MAXP = 120  # supports up to 120 periods (e.g. 60y semi-annual, 30y quarterly, 10y monthly)
n_ref = "'Bond Pricing'!$C$7*'Bond Pricing'!$C$8"
y_ref = "'Bond Pricing'!$C$9/'Bond Pricing'!$C$7"
coupon_ref = "'Bond Pricing'!$C$5*'Bond Pricing'!$C$6/'Bond Pricing'!$C$7"
face_ref = "'Bond Pricing'!$C$5"

ws["B12"] = "Closed-Form Cross-Check (exact cash flow schedule)"
ws["B12"].font = BOLD; ws["B12"].fill = GRAY_FILL
ws["B13"] = ("Sums t x PV(CF) and t(t+1) x PV(CF) across every period from the bond's actual cash flows -- "
             "the textbook closed-form definition, independent of the finite-difference shock above.")
ws["B13"].font = ITALIC_GRAY

table_headers = ["Period", "Cash flow ($)", "PV factor", "PV(CF)", "t x PV(CF)", "t(t+1) x PV(CF)"]
header_row = 15
for i, h in enumerate(table_headers, start=2):
    ws.cell(row=header_row, column=i, value=h)
style_header_row(ws, header_row, len(table_headers) - 1, start_col=2)

first_data_row = header_row + 1
for i in range(MAXP):
    r2 = first_data_row + i
    t = i + 1
    ws.cell(row=r2, column=2, value=t).font = BLACK
    ws.cell(row=r2, column=3,
            value=f"=IF({t}>{n_ref},0,IF({t}={n_ref},{coupon_ref}+{face_ref},{coupon_ref}))")
    ws.cell(row=r2, column=3).number_format = CUR2
    ws.cell(row=r2, column=4, value=f"=1/(1+{y_ref})^{t}")
    ws.cell(row=r2, column=4).number_format = "0.000000"
    ws.cell(row=r2, column=5, value=f"=C{r2}*D{r2}")
    ws.cell(row=r2, column=5).number_format = CUR2
    ws.cell(row=r2, column=6, value=f"={t}*E{r2}")
    ws.cell(row=r2, column=6).number_format = CUR2
    ws.cell(row=r2, column=7, value=f"={t}*({t}+1)*E{r2}")
    ws.cell(row=r2, column=7).number_format = CUR2
last_data_row = first_data_row + MAXP - 1

sum_row = last_data_row + 1
ws.cell(row=sum_row, column=2, value="Total").font = BOLD
for col in (5, 6, 7):
    letter = get_column_letter(col)
    ws.cell(row=sum_row, column=col, value=f"=SUM({letter}{first_data_row}:{letter}{last_data_row})")
    ws.cell(row=sum_row, column=col).number_format = CUR2
    ws.cell(row=sum_row, column=col).font = BOLD

r = sum_row + 2
ws.cell(row=r, column=2, value="Closed-form price (should equal Bond Pricing price)")
ws.cell(row=r, column=3, value=f"=E{sum_row}")
ws.cell(row=r, column=3).number_format = CUR2; ws.cell(row=r, column=3).border = BORDER
price_check_row = r; r += 1
ws.cell(row=r, column=2, value="Macaulay duration (years)")
ws.cell(row=r, column=3, value=f"=IFERROR((F{sum_row}/E{sum_row})/'Bond Pricing'!$C$7,\"-\")")
ws.cell(row=r, column=3).number_format = "0.0000"; ws.cell(row=r, column=3).border = BORDER
mac_dur_row = r; r += 1
ws.cell(row=r, column=2, value="Modified duration (closed-form)")
ws.cell(row=r, column=3, value=f"=IFERROR(C{mac_dur_row}/(1+{y_ref}),\"-\")")
ws.cell(row=r, column=3).font = BOLD; ws.cell(row=r, column=3).number_format = "0.00"
ws.cell(row=r, column=3).border = BORDER
mod_dur_cf_row = r; r += 1
ws.cell(row=r, column=2, value="Convexity (closed-form, annualized)")
ws.cell(row=r, column=3,
        value=f"=IFERROR((G{sum_row}/E{sum_row})/(1+{y_ref})^2/'Bond Pricing'!$C$7^2,\"-\")")
ws.cell(row=r, column=3).font = BOLD; ws.cell(row=r, column=3).number_format = "0.00"
ws.cell(row=r, column=3).border = BORDER
convexity_cf_row = r; r += 1
ws.cell(row=r, column=2, value="Diff vs. numerical (FD) modified duration above")
ws.cell(row=r, column=3, value=f"=IFERROR(C{mod_dur_cf_row}-C8,\"-\")")
ws.cell(row=r, column=3).number_format = "0.0000"; ws.cell(row=r, column=3).border = BORDER
r += 1
ws.cell(row=r, column=2, value="Diff vs. numerical (FD) convexity above")
ws.cell(row=r, column=3, value=f"=IFERROR(C{convexity_cf_row}-C9,\"-\")")
ws.cell(row=r, column=3).number_format = "0.0000"; ws.cell(row=r, column=3).border = BORDER
r += 1
ws.cell(row=r, column=2,
        value=(f"Cash flow schedule supports up to {MAXP} periods (coupon frequency x years to maturity). "
               f"Inputs implying more periods than that will silently truncate the closed-form sums -- the "
               f"price-check row above should always be verified to still match Bond Pricing's price."))
ws.cell(row=r, column=2).font = ITALIC_GRAY

set_col_widths(ws, [4, 34, 16, 16, 16, 16, 16])
ws.sheet_view.showGridLines = False

add_sources_checks(
    wb,
    sources=[
        ("Modified duration and convexity via finite-difference price shock (+/- 50bp)", "Standard numerical price-sensitivity estimation", "Standard practice", "A numerical approximation -- accuracy depends on shock size; too large a shock understates convexity's own curvature"),
        ("Modified duration and convexity via closed-form cash flow schedule (sum of t x PV(CF) / sum of t(t+1) x PV(CF))", "Standard fixed-income textbook definition (e.g. Fabozzi, Bond Markets, Analysis, and Strategies)", "Textbook standard", "Exact given the bond's stated cash flows -- the reference the numerical method above is approximating"),
        ("30/360 and Actual/Actual day-count conventions for accrued interest", "Standard bond market day-count conventions", "Standard practice", "30/360 is standard for most corporate/municipal bonds; Actual/Actual is standard for U.S. Treasuries -- using the wrong one for the instrument type misstates accrued interest"),
        ("Level annuity + bullet PV bond pricing (Excel PV function)", "Standard fixed-coupon bond pricing", "Standard practice", "Assumes no embedded optionality (call/put/convert) -- an option-adjusted spread (OAS) model would be needed for callable/putable bonds"),
    ],
    checks=[
        ("Closed-form price (from the cash flow schedule) matches Bond Pricing's PV-formula price", f"='Duration & Convexity'!C{price_check_row}-'Bond Pricing'!C11", "0 (exact) -- both are the same bond priced two different ways"),
        ("Closed-form modified duration matches numerical (finite-difference) modified duration", f"='Duration & Convexity'!C{mod_dur_cf_row}-'Duration & Convexity'!C8", "~0 (small) -- the FD estimate is an approximation of the closed-form value, not identical to the decimal"),
        ("Closed-form convexity matches numerical (finite-difference) convexity", f"='Duration & Convexity'!C{convexity_cf_row}-'Duration & Convexity'!C9", "~0 (small) -- same relationship as duration, one differentiation order higher"),
        ("Convexity is non-negative for this option-free bond", "=IF('Duration & Convexity'!C9>=0,TRUE,FALSE)", "TRUE -- a plain-vanilla (option-free) bond's price-yield curve is always convex from below"),
    ],
)

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
