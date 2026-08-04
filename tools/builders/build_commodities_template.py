import openpyxl
from template_helpers import *

wb = openpyxl.Workbook()
wb.remove(wb.active)

add_cover(wb, "[COMMODITY] — Commodities Model", [
    ("Commodity:", "[e.g. WTI Crude, Corn, Copper]"),
    ("Exchange:", "[NYMEX / CME / ICE]"),
    ("Last refreshed:", "[date]"),
    ("Next roll date:", "[date]"),
    ("Refresh cadence:", "Weekly (daily near roll/expiry)"),
])

# ---------------- FUTURES CURVE ----------------
ws = wb.create_sheet("Futures Curve")
set_col_widths(ws, [4, 16, 14, 14, 14, 14, 20])
ws["B2"] = "Futures Curve — Contango / Backwardation"; ws["B2"].font = TITLE
headers = ["", "Contract month", "Price", "Days to expiry", "Annualized basis %", "vs. front month", "Curve shape"]
for i, h in enumerate(headers, start=1):
    ws.cell(row=4, column=i, value=h)
style_header_row(ws, 4, len(headers)-1)

months = ["M1 (front)", "M2", "M3", "M6", "M12"]
r = 5
first_row = r
for m in months:
    ws.cell(row=r, column=2, value=m).font = BLACK
    c_price = ws.cell(row=r, column=3, value=0); c_price.font = BLUE; c_price.number_format = CUR2; c_price.border = BORDER
    c_days = ws.cell(row=r, column=4, value=0); c_days.font = BLUE; c_days.number_format = NUM; c_days.border = BORDER
    r += 1
last_row = r - 1
for rr in range(first_row, last_row + 1):
    # Standard cost-of-carry annualization uses the GAP between the two
    # contracts' expiries (D{rr} - D{front}), not this contract's own
    # days-to-expiry from today — those are different periods. Using the
    # latter understates the annualized rate for every month past the
    # front (e.g. $70 front/10d vs $71/40d: correct annualization is
    # 17.4%, using the contract's own day count alone gives only 13.0%).
    ws.cell(row=rr, column=5,
            value=f"=IFERROR((C{rr}/$C${first_row}-1)*(365/(D{rr}-$D${first_row})),\"-\")")
    ws.cell(row=rr, column=5).number_format = PCT
    ws.cell(row=rr, column=5).border = BORDER
    ws.cell(row=rr, column=6,
            value=f"=IFERROR(C{rr}/$C${first_row}-1,\"-\")").number_format = PCT
    ws.cell(row=rr, column=6).border = BORDER
    ws.cell(row=rr, column=7,
            value=f'=IF(C{rr}>$C${first_row},"Contango",IF(C{rr}<$C${first_row},"Backwardation","Flat"))')
    ws.cell(row=rr, column=7).border = BORDER
ws.sheet_view.showGridLines = False

# ---------------- COST OF CARRY & CONVENIENCE YIELD ----------------
ws = wb.create_sheet("Cost of Carry")
set_col_widths(ws, [4, 16, 14, 12, 16, 18, 18, 18])
ws["B2"] = "Cost of Carry & Implied Convenience Yield"; ws["B2"].font = TITLE
ws["B3"] = ("The Futures Curve tab shows THAT a curve is in contango or backwardation. This explains WHY: the "
            "cost-of-carry model says F = S x e^((r+u-y)T) -- given the market's own observed futures prices, "
            "solve for y, the convenience yield, which is the market's revealed value of holding physical "
            "inventory right now (stockout risk, production flexibility) rather than buying the future.")
ws["B3"].font = ITALIC_GRAY

ws["B5"] = "Inputs"; ws["B5"].font = BOLD; ws["B5"].fill = GRAY_FILL
carry_inputs = [
    ("Spot price", 0, CUR2),
    ("Risk-free rate, r (%)", 0.05, PCT2),
    ("Storage cost, u (% of spot, annualized)", 0.02, PCT2),
]
r = 6
for label, default, fmt in carry_inputs:
    ws.cell(row=r, column=2, value=label).font = BLACK
    c = ws.cell(row=r, column=3, value=default); c.font = BLUE; c.fill = YELLOW_FILL
    c.number_format = fmt; c.border = BORDER
    r += 1

headers = ["", "Contract month", "Days to expiry", "T (yrs)", "Observed futures price",
           "Theoretical price (no convenience yield)", "Implied convenience yield, y (%)", "Reprice check (F(y) - observed)"]
for i, h in enumerate(headers, start=1):
    ws.cell(row=10, column=i, value=h)
style_header_row(ws, 10, 7, start_col=2)

carry_rows = [(11, 5), (12, 6), (13, 7), (14, 8), (15, 9)]  # (this sheet's row, Futures Curve's row)
for this_row, fc_row in carry_rows:
    ws.cell(row=this_row, column=2, value=f"='Futures Curve'!B{fc_row}").font = GREEN
    ws.cell(row=this_row, column=3, value=f"='Futures Curve'!D{fc_row}").font = GREEN
    ws.cell(row=this_row, column=3).number_format = NUM
    ws.cell(row=this_row, column=4, value=f"=C{this_row}/365").number_format = '0.000'
    ws.cell(row=this_row, column=5, value=f"='Futures Curve'!C{fc_row}").font = GREEN
    ws.cell(row=this_row, column=5).number_format = CUR2
    ws.cell(row=this_row, column=6,
            value=f"=IFERROR($C$6*EXP(($C$7+$C$8)*D{this_row}),\"-\")").number_format = CUR2
    ws.cell(row=this_row, column=7,
            value=f'=IFERROR(IF(OR(D{this_row}=0,$C$6<=0,E{this_row}<=0),"-",$C$7+$C$8-LN(E{this_row}/$C$6)/D{this_row}),"-")')
    ws.cell(row=this_row, column=7).number_format = PCT2
    ws.cell(row=this_row, column=7).font = BOLD
    ws.cell(row=this_row, column=8,
            value=f'=IFERROR(IF(ISNUMBER(G{this_row}),$C$6*EXP(($C$7+$C$8-G{this_row})*D{this_row})-E{this_row},"-"),"-")')
    ws.cell(row=this_row, column=8).number_format = '0.0000'
    for col in range(2, 9):
        ws.cell(row=this_row, column=col).border = BORDER

ws["B17"] = "Reading it: y > r+u means the curve is in backwardation (physical premium exceeds financing+storage cost)."
ws["B17"].font = ITALIC_GRAY
ws["B18"] = "y < r+u means contango (holding physical isn't worth the storage+financing drag) -- consistent with the Futures Curve tab's curve-shape column."
ws["B18"].font = ITALIC_GRAY
ws.sheet_view.showGridLines = False

# ---------------- ROLL YIELD ----------------
ws = wb.create_sheet("Roll Yield")
set_col_widths(ws, [4, 26, 16, 16, 40])
ws["B2"] = "Roll Yield"; ws["B2"].font = TITLE
ws["B4"] = "Expiring contract price"; ws["C4"] = "='Futures Curve'!C5"; ws["C4"].font = GREEN; ws["C4"].number_format = CUR2
ws["B5"] = "Next contract price"; ws["C5"] = "='Futures Curve'!C6"; ws["C5"].font = GREEN; ws["C5"].number_format = CUR2
ws["B6"] = "Roll yield (%)"
ws["C6"] = "=IFERROR(C4/C5-1,\"-\")"; ws["C6"].font = BOLD; ws["C6"].number_format = PCT
ws["D6"] = "Positive = backwardation roll gain (long-only benefits). Negative = contango roll cost."
ws["D6"].font = ITALIC_GRAY
ws["B8"] = "Annual roll cost/gain estimate (12 rolls, illustrative)"
ws["C8"] = "=IFERROR(C6*12,\"-\")"; ws["C8"].number_format = PCT
ws.sheet_view.showGridLines = False

# ---------------- HEDGING ----------------
ws = wb.create_sheet("Hedging")
set_col_widths(ws, [4, 28, 16, 16, 40])
ws["B2"] = "Producer / Consumer Hedge Model"; ws["B2"].font = TITLE
ws["B4"] = "Inputs"; ws["B4"].font = BOLD; ws["B4"].fill = GRAY_FILL
inputs = [
    ("Physical exposure (units)", 0, NUM),
    ("Futures contract size (units)", 1000, NUM),
    ("Spot price", 0, CUR2),
    ("Futures price (hedge contract)", 0, CUR2),
    ("Hedge ratio (beta-adjusted)", 1.0, '0.00'),
]
r = 5
for label, default, fmt in inputs:
    ws.cell(row=r, column=2, value=label).font = BLACK
    c = ws.cell(row=r, column=3, value=default); c.font = BLUE; c.fill = YELLOW_FILL
    c.number_format = fmt; c.border = BORDER
    r += 1

ws["B11"] = "Outputs"; ws["B11"].font = BOLD; ws["B11"].fill = GRAY_FILL
ws["B12"] = "Contracts needed"
ws["C12"] = "=IFERROR(ROUND(C5*C9/C6,0),\"-\")"; ws["C12"].font = BOLD; ws["C12"].number_format = NUM
ws["B13"] = "Notional hedged"
ws["C13"] = "=C12*C6*C8"; ws["C13"].number_format = CUR
ws["B14"] = "Unhedged basis exposure"
ws["C14"] = "=C5*C7-C13"; ws["C14"].number_format = CUR
for r2 in (12, 13, 14):
    ws.cell(row=r2, column=3).border = BORDER
ws.sheet_view.showGridLines = False

# ---------------- SENSITIVITY ----------------
ws = wb.create_sheet("Sensitivity")
set_col_widths(ws, [4, 20] + [12]*5)
ws["B2"] = "Sensitivity — P&L by Spot Move"; ws["B2"].font = TITLE
ws["B4"] = "Spot move %"; ws["B4"].font = BOLD; ws["B4"].fill = GRAY_FILL
moves = [-0.20, -0.10, 0.0, 0.10, 0.20]
for i, m in enumerate(moves, start=3):
    c = ws.cell(row=4, column=i, value=m); c.font = BOLD; c.fill = GRAY_FILL; c.number_format = PCT
ws["B5"] = "Unhedged P&L"; ws["B6"] = "Hedged P&L"
for i, m in enumerate(moves, start=3):
    col = get_column_letter(i)
    ws.cell(row=5, column=i, value=f"='Hedging'!$C$5*'Hedging'!$C$7*{col}4").number_format = CUR
    ws.cell(row=6, column=i, value=f"=({col}4*'Hedging'!$C$5*'Hedging'!$C$7)-({col}4*'Hedging'!$C$13)").number_format = CUR
    ws.cell(row=5, column=i).border = BORDER
    ws.cell(row=6, column=i).border = BORDER
ws.sheet_view.showGridLines = False

add_sources_checks(
    wb,
    sources=[
        ("Cost-of-carry model, F = S x e^((r+u-y)T)", "Standard commodity futures pricing theory (theory of storage)", "Standard practice", "Assumes continuous compounding and a constant storage cost -- real curves can have seasonal storage-cost variation this doesn't capture"),
        ("Implied convenience yield solved directly from the observed futures price", "Derived from the cost-of-carry identity, not statistically fitted", "Derived", "A point estimate per contract month, not a fitted term-structure model"),
        ("Roll yield ~ (expiring price / next price) - 1", "Standard commodities practitioner approximation", "Standard practice", "Assumes a constant-maturity roll; a real fund's roll depends on its specific contract weighting schedule"),
        ("Hedge contracts needed = physical exposure x hedge ratio / contract size", "Standard futures hedging formula", "Standard practice", "Hedge ratio should reflect basis-risk-adjusted beta, not an assumed 1:1 unless justified"),
    ],
    checks=[
        ("Sum of |reprice check| across all 5 contract months (Cost of Carry)", "=IFERROR(SUMPRODUCT(ABS(IF(ISNUMBER('Cost of Carry'!H11:H15),'Cost of Carry'!H11:H15,0))),\"-\")", "~0 -- each month's implied convenience yield exactly reprices the observed futures price by construction"),
        ("Unhedged P&L is zero at a 0% spot move", "='Sensitivity'!E5", "0 (exact)"),
        ("Hedged P&L is zero at a 0% spot move", "='Sensitivity'!E6", "0 (exact)"),
        ("Curve-shape label matches the sign of the annualized basis (M12 vs. M1)", '=IF(\'Futures Curve\'!E9>0,\'Futures Curve\'!G9="Contango",IF(\'Futures Curve\'!E9<0,\'Futures Curve\'!G9="Backwardation",TRUE))', "TRUE"),
    ],
)

add_refresh_log(wb)

out_path = "COMMODITIES_template.xlsx"
wb.save(out_path)
print("saved", out_path)
