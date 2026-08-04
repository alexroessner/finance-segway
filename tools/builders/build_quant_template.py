import openpyxl
from template_helpers import *

wb = openpyxl.Workbook()
wb.remove(wb.active)

add_cover(wb, "[STRATEGY] — Quantitative / Systematic Model", [
    ("Strategy:", "[fill in]"),
    ("Asset class / universe:", "[fill in]"),
    ("Last refreshed:", "[date]"),
    ("Refresh cadence:", "Weekly (daily if live-traded)"),
])

# ---------------- RETURNS & SHARPE ----------------
ws = wb.create_sheet("Returns & Sharpe")
set_col_widths(ws, [4, 30, 16, 40, 14, 14, 14, 14])
ws["B2"] = "Risk-Adjusted Return Statistics"; ws["B2"].font = TITLE
ws["B4"] = "Monthly return series (enter below, extend as needed)"
ws["B4"].font = ITALIC_GRAY
ws["B5"] = "Month"; ws["C5"] = "Return %"
ws["E5"] = "Benchmark %"; ws["F5"] = "Wealth idx"; ws["G5"] = "Peak"; ws["H5"] = "Drawdown"
style_header_row(ws, 5, 2, start_col=2)
style_header_row(ws, 5, 4, start_col=5)
r = 6
for m in range(1, 25):
    ws.cell(row=r, column=2, value=f"M{m}")
    c = ws.cell(row=r, column=3, value=0.0)
    c.font = BLUE; c.number_format = PCT2; c.border = BORDER
    e = ws.cell(row=r, column=5, value=0.0)
    e.font = BLUE; e.number_format = PCT2; e.border = BORDER

    f = ws.cell(row=r, column=6,
                value=f"=1*(1+C{r})" if r == 6 else f"=F{r-1}*(1+C{r})")
    f.number_format = '0.0000'; f.border = BORDER
    g = ws.cell(row=r, column=7, value=f"=MAX($F$6:F{r})")
    g.number_format = '0.0000'; g.border = BORDER
    h = ws.cell(row=r, column=8, value=f"=IFERROR(F{r}/G{r}-1,\"-\")")
    h.number_format = PCT; h.border = BORDER
    r += 1
last_data_row = r - 1

ws["B32"] = "Risk-free rate (annual, %)"; ws["C32"] = 0.045; ws["C32"].font = BLUE
ws["C32"].fill = YELLOW_FILL; ws["C32"].number_format = PCT

ws["B34"] = "Outputs"; ws["B34"].font = BOLD; ws["B34"].fill = GRAY_FILL
ws["B35"] = "Avg monthly return"
ws["C35"] = f"=AVERAGE(C6:C{last_data_row})"; ws["C35"].number_format = PCT2
ws["B36"] = "Monthly std dev"
ws["C36"] = f"=STDEV(C6:C{last_data_row})"; ws["C36"].number_format = PCT2
ws["B37"] = "Annualized return"
ws["C37"] = "=(1+C35)^12-1"; ws["C37"].number_format = PCT
ws["B38"] = "Annualized volatility"
ws["C38"] = "=C36*SQRT(12)"; ws["C38"].number_format = PCT
ws["B39"] = "Sharpe ratio"
ws["C39"] = "=IFERROR((C37-C32)/C38,\"-\")"; ws["C39"].font = BOLD; ws["C39"].number_format = '0.00'
ws["B40"] = "Downside deviation (returns < 0 only)"
ws["C40"] = f'=IFERROR(SQRT(SUMPRODUCT((C6:C{last_data_row}<0)*(C6:C{last_data_row})^2)/COUNTIF(C6:C{last_data_row},"<0"))*SQRT(12),"-")'
ws["C40"].number_format = PCT
ws["B41"] = "Sortino ratio"
ws["C41"] = "=IFERROR((C37-C32)/C40,\"-\")"; ws["C41"].font = BOLD; ws["C41"].number_format = '0.00'
ws["B42"] = "Max drawdown"
ws["C42"] = f"=MIN(H6:H{last_data_row})"
ws["C42"].font = BOLD; ws["C42"].number_format = PCT
ws["D42"] = "Trough of the wealth-index drawdown series (columns F-H) — worst peak-to-trough decline in the sample"
ws["D42"].font = ITALIC_GRAY
for r2 in range(35, 43):
    ws.cell(row=r2, column=3).border = BORDER
ws.sheet_view.showGridLines = False

# ---------------- BENCHMARK & FACTOR EXPOSURE ----------------
ws2 = wb["Returns & Sharpe"]
ws2["B44"] = "Benchmark & Factor Exposure (single-factor / CAPM)"; ws2["B44"].font = BOLD; ws2["B44"].fill = GRAY_FILL
ws2["B45"] = "Avg monthly benchmark return"
ws2["C45"] = f"=AVERAGE(E6:E{last_data_row})"; ws2["C45"].number_format = PCT2
ws2["B46"] = "Annualized benchmark return"
ws2["C46"] = "=(1+C45)^12-1"; ws2["C46"].number_format = PCT
ws2["B47"] = "Beta (vs benchmark)"
ws2["C47"] = f"=IFERROR(SLOPE(C6:C{last_data_row},E6:E{last_data_row}),\"-\")"
ws2["C47"].font = BOLD; ws2["C47"].number_format = '0.00'
ws2["B48"] = "R-squared"
ws2["C48"] = f"=IFERROR(RSQ(C6:C{last_data_row},E6:E{last_data_row}),\"-\")"; ws2["C48"].number_format = PCT
ws2["B49"] = "Jensen's alpha (annualized) = Rp - [Rf + Beta x (Rm - Rf)]"
ws2["C49"] = "=IFERROR(C37-(C32+C47*(C46-C32)),\"-\")"; ws2["C49"].font = BOLD; ws2["C49"].number_format = PCT
ws2["D49"] = "Positive = generating return beyond what beta exposure to the benchmark would explain"
ws2["D49"].font = ITALIC_GRAY
for r2 in range(45, 50):
    ws2.cell(row=r2, column=3).border = BORDER

# ---------------- STATISTICAL SIGNIFICANCE (PSR) ----------------
ws = wb.create_sheet("Statistical Significance")
set_col_widths(ws, [4, 40, 16, 46])
ws["B2"] = "Probabilistic Sharpe Ratio & Minimum Track Record Length"; ws["B2"].font = TITLE
ws["B3"] = ("A Sharpe ratio from a short, noisy, skewed return sample is an ESTIMATE, not a fact -- the naive "
            "headline number overstates confidence. Bailey & Lopez de Prado's Probabilistic Sharpe Ratio answers "
            "'how confident are we the TRUE Sharpe exceeds some benchmark,' correcting for sample length, "
            "skewness, and kurtosis -- exactly the corrections a track record with only 24 months and fat tails "
            "actually needs.")
ws["B3"].font = ITALIC_GRAY

ws["B5"] = "Inputs"; ws["B5"].font = BOLD; ws["B5"].fill = GRAY_FILL
ws["B6"] = "Benchmark Sharpe to test against, SR* (periodic/monthly)"
c = ws.cell(row=6, column=3, value=0.0); c.font = BLUE; c.fill = YELLOW_FILL; c.number_format = '0.00'; c.border = BORDER
ws["B7"] = "Confidence level (for Minimum Track Record Length)"
c = ws.cell(row=7, column=3, value=0.95); c.font = BLUE; c.fill = YELLOW_FILL; c.number_format = PCT; c.border = BORDER

ws["B9"] = "From the Return Sample"; ws["B9"].font = BOLD; ws["B9"].fill = GRAY_FILL
ws["B10"] = "Number of periods, n"
ws["C10"] = f"=COUNT('Returns & Sharpe'!C6:C{last_data_row})"; ws["C10"].font = GREEN; ws["C10"].number_format = NUM
ws["C10"].border = BORDER
ws["B11"] = "Skewness"
ws["C11"] = f"=IFERROR(SKEW('Returns & Sharpe'!C6:C{last_data_row}),\"-\")"; ws["C11"].number_format = '0.000'
ws["C11"].border = BORDER
ws["B12"] = "Excess kurtosis (0 = normal)"
ws["C12"] = f"=IFERROR(KURT('Returns & Sharpe'!C6:C{last_data_row}),\"-\")"; ws["C12"].number_format = '0.000'
ws["C12"].border = BORDER
ws["B13"] = "Periodic (monthly) Sharpe ratio, SR-hat"
ws["C13"] = "=IFERROR(('Returns & Sharpe'!C35-'Returns & Sharpe'!C32/12)/'Returns & Sharpe'!C36,\"-\")"
ws["C13"].font = BOLD; ws["C13"].number_format = '0.0000'; ws["C13"].border = BORDER

ws["B15"] = "Probabilistic Sharpe Ratio"; ws["B15"].font = BOLD; ws["B15"].fill = GRAY_FILL
ws["B16"] = "PSR denominator: sqrt(1 - skew x SR + (kurt+2)/4 x SR^2)"
ws["C16"] = '=IFERROR(SQRT(1-C11*C13+(C12+2)/4*C13^2),"-")'; ws["C16"].number_format = '0.0000'
ws["C16"].border = BORDER
ws["D16"] = "Bailey & Lopez de Prado (2012). Reduces to sqrt(1/(n-1)) under normality (skew=0, excess kurt=0)."
ws["D16"].font = ITALIC_GRAY
ws["B17"] = "PSR z-statistic: (SR-hat - SR*) x sqrt(n-1) / denominator"
ws["C17"] = '=IFERROR((C13-C6)*SQRT(C10-1)/C16,"-")'; ws["C17"].number_format = '0.0000'; ws["C17"].border = BORDER
ws["B18"] = "PSR = P(true Sharpe > SR*)"
ws["C18"] = '=IFERROR(NORMSDIST(C17),"-")'; ws["C18"].font = BOLD; ws["C18"].number_format = PCT
ws["C18"].fill = YELLOW_FILL; ws["C18"].border = BORDER
ws["D18"] = "Below ~95% is a real reason to doubt the headline Sharpe, no matter how good it looks"
ws["D18"].font = ITALIC_GRAY

ws["B20"] = "Minimum Track Record Length"; ws["B20"].font = BOLD; ws["B20"].fill = GRAY_FILL
ws["B21"] = "z-score at chosen confidence (NORMSINV)"
ws["C21"] = "=IFERROR(NORMSINV(C7),\"-\")"; ws["C21"].number_format = '0.0000'; ws["C21"].border = BORDER
ws["B22"] = "MinTRL (periods needed at this confidence)"
ws["C22"] = '=IFERROR(IF(C13<=C6,"undefined -- SR-hat must exceed SR*",1+(1-C11*C13+(C12+2)/4*C13^2)*(C21/(C13-C6))^2),"-")'
ws["C22"].font = BOLD; ws["C22"].number_format = '0.0'; ws["C22"].border = BORDER
ws["D22"] = "How many periods of track record, at this sample's skew/kurtosis, would be needed to be this confident SR-hat truly exceeds SR*"
ws["D22"].font = ITALIC_GRAY
ws["B23"] = "Track record adequate? (n vs. MinTRL)"
ws["C23"] = '=IF(OR(NOT(ISNUMBER(C22)),NOT(ISNUMBER(C10))),"-",IF(C10>=C22,"ADEQUATE","TOO SHORT -- treat SR-hat with caution"))'
ws["C23"].font = BOLD
ws.sheet_view.showGridLines = False

# ---------------- POSITION SIZING ----------------
ws = wb.create_sheet("Position Sizing")
set_col_widths(ws, [4, 30, 16, 40])
ws["B2"] = "Position Sizing (Kelly & Fixed Fractional)"; ws["B2"].font = TITLE
inputs = [
    ("Win rate (%)", 0.55, PCT),
    ("Avg win / avg loss ratio (payoff ratio)", 1.5, '0.00'),
    ("Account equity ($)", 0, CUR),
    ("Max risk per trade (fixed-fractional, %)", 0.01, PCT),
]
r = 5
for label, default, fmt in inputs:
    ws.cell(row=r, column=2, value=label).font = BLACK
    c = ws.cell(row=r, column=3, value=default); c.font = BLUE; c.fill = YELLOW_FILL
    c.number_format = fmt; c.border = BORDER
    r += 1
ws["B10"] = "Kelly fraction = W - (1-W)/R"
ws["C10"] = "=C5-(1-C5)/C6"; ws["C10"].font = BOLD; ws["C10"].number_format = PCT
ws["D10"] = "Full Kelly is aggressive — most practitioners use 1/4 to 1/2 Kelly"
ws["D10"].font = ITALIC_GRAY
ws["B11"] = "Half-Kelly position size ($)"
ws["C11"] = "=IFERROR(C7*C10/2,\"-\")"; ws["C11"].number_format = CUR
ws["B12"] = "Fixed-fractional position size ($)"
ws["C12"] = "=C7*C8"; ws["C12"].number_format = CUR
for r2 in (10, 11, 12):
    ws.cell(row=r2, column=3).border = BORDER
ws.sheet_view.showGridLines = False

add_sources_checks(
    wb,
    sources=[
        ("Probabilistic Sharpe Ratio (PSR)", "Bailey, D. and Lopez de Prado, M. (2012), \"The Sharpe Ratio Efficient Frontier\"", "Peer-reviewed methodology", "Assumes returns are i.i.d. within the sample (no autocorrelation adjustment) -- a genuinely autocorrelated strategy needs a further effective-sample-size correction this doesn't apply"),
        ("Minimum Track Record Length (MinTRL)", "Bailey, D. and Lopez de Prado, M. (2012), same PSR paper", "Peer-reviewed methodology", "A diagnostic for how much history is needed at the CURRENT sample's skew/kurtosis, not a guarantee those higher moments are stable out of sample"),
        ("Kelly criterion, W - (1-W)/R", "Kelly (1956) criterion for edge-optimal position sizing", "Standard practice", "Assumes win rate and payoff ratio are known and stationary -- in practice both are estimated with error, hence the 1/4-1/2 Kelly practitioner convention"),
        ("Sharpe/Sortino/max drawdown/CAPM beta-alpha", "Standard risk-adjusted performance measurement conventions", "Standard practice", "Monthly-periodicity annualization (x12, xsqrt(12)) throughout -- would need adjustment for a different return frequency"),
    ],
    checks=[
        ("PSR z-statistic sign matches whether SR-hat beats the benchmark (denominator is always positive)", "=IF(NOT(ISNUMBER('Statistical Significance'!C17)),TRUE,IF('Statistical Significance'!C13>='Statistical Significance'!C6,'Statistical Significance'!C17>=0,'Statistical Significance'!C17<=0))", "TRUE"),
        ("MinTRL is undefined (not a false low number) when SR-hat doesn't exceed SR*", "=IF('Statistical Significance'!C13<='Statistical Significance'!C6,'Statistical Significance'!C22=\"undefined -- SR-hat must exceed SR*\",TRUE)", "TRUE"),
        ("Max drawdown is always <= 0 (a decline, never a gain, by definition)", "=IF(ISNUMBER('Returns & Sharpe'!C42),'Returns & Sharpe'!C42<=0,TRUE)", "TRUE"),
        ("Half-Kelly is exactly half of full Kelly", "=IFERROR('Position Sizing'!C11-('Position Sizing'!C7*'Position Sizing'!C10/2),\"-\")", "0 (exact) once account equity is populated"),
    ],
)

add_refresh_log(wb)
out_path = "QUANT_template.xlsx"
wb.save(out_path)
print("saved", out_path)
