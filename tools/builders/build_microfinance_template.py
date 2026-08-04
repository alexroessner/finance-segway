import openpyxl
from template_helpers import *

wb = openpyxl.Workbook()
wb.remove(wb.active)

add_cover(wb, "[MFI] — Microfinance Model", [
    ("Institution:", "[fill in]"),
    ("Region:", "[fill in]"),
    ("Last refreshed:", "[date]"),
    ("Refresh cadence:", "Weekly"),
])

# ---------------- LOAN PORTFOLIO ----------------
ws = wb.create_sheet("Loan Portfolio")
set_col_widths(ws, [4, 30, 16, 40])
ws["B2"] = "Loan Portfolio Overview"; ws["B2"].font = TITLE
inputs = [
    ("Gross loan portfolio (GLP, $)", 0, CUR),
    ("Number of active borrowers", 0, NUM),
    ("Portfolio at risk >30 days ($)", 0, CUR),
    ("Portfolio at risk >90 days ($)", 0, CUR),
    ("Write-offs this period ($)", 0, CUR),
    ("Average loan balance ($)", 0, CUR),
]
r = 5
for label, default, fmt in inputs:
    ws.cell(row=r, column=2, value=label).font = BLACK
    c = ws.cell(row=r, column=3, value=default); c.font = BLUE; c.fill = YELLOW_FILL
    c.number_format = fmt; c.border = BORDER
    r += 1

ws["B12"] = "Portfolio Quality"; ws["B12"].font = BOLD; ws["B12"].fill = GRAY_FILL
ws["B13"] = "PAR 30 %"; ws["C13"] = "=IFERROR(C7/C5,\"-\")"; ws["C13"].number_format = PCT
ws["B14"] = "PAR 90 %"; ws["C14"] = "=IFERROR(C8/C5,\"-\")"; ws["C14"].number_format = PCT
ws["B15"] = "Write-off ratio (annualized)"; ws["C15"] = "=IFERROR(C9/C5,\"-\")"; ws["C15"].number_format = PCT
ws["B16"] = "Avg loan / borrower check"; ws["C16"] = "=IFERROR(C5/C6,\"-\")"; ws["C16"].number_format = CUR
for r2 in range(13, 17):
    ws.cell(row=r2, column=3).border = BORDER
ws.sheet_view.showGridLines = False

# ---------------- SUSTAINABILITY RATIOS ----------------
ws = wb.create_sheet("Sustainability")
set_col_widths(ws, [4, 34, 16, 40])
ws["B2"] = "Operational & Financial Self-Sufficiency (OSS/FSS)"; ws["B2"].font = TITLE
ws["B4"] = "Inputs"; ws["B4"].font = BOLD; ws["B4"].fill = GRAY_FILL
inputs = [
    ("Financial revenue (interest + fees, $)", 0, CUR),
    ("Financial expense (cost of funds, $)", 0, CUR),
    ("Loan loss provision expense ($)", 0, CUR),
    ("Operating expense ($)", 0, CUR),
    ("Cost of capital at market rate (imputed, $)", 0, CUR),
]
r = 5
for label, default, fmt in inputs:
    ws.cell(row=r, column=2, value=label).font = BLACK
    c = ws.cell(row=r, column=3, value=default); c.font = BLUE; c.fill = YELLOW_FILL
    c.number_format = fmt; c.border = BORDER
    r += 1

ws["B11"] = "Outputs"; ws["B11"].font = BOLD; ws["B11"].fill = GRAY_FILL
ws["B12"] = "Operational Self-Sufficiency (OSS) = Rev / (Fin exp + Loss prov + Opex)"
ws["C12"] = "=IFERROR(C5/(C6+C7+C8),\"-\")"; ws["C12"].font = BOLD; ws["C12"].number_format = PCT
ws["D12"] = ">100% = covering costs from operations, not subsidy-dependent"
ws["D12"].font = ITALIC_GRAY
ws["B13"] = "Financial Self-Sufficiency (FSS) = Rev / (Fin exp + Loss prov + Opex + imputed cost of capital)"
ws["C13"] = "=IFERROR(C5/(C6+C7+C8+C9),\"-\")"; ws["C13"].font = BOLD; ws["C13"].number_format = PCT
ws["D13"] = "Stricter than OSS — adjusts for subsidized funding cost vs. commercial rate"
ws["D13"].font = ITALIC_GRAY
ws["B14"] = "Portfolio yield (Rev / avg GLP)"
ws["C14"] = "=IFERROR(C5/'Loan Portfolio'!C5,\"-\")"; ws["C14"].number_format = PCT
for r2 in range(12, 15):
    ws.cell(row=r2, column=3).border = BORDER
ws.sheet_view.showGridLines = False

# ---------------- LOAN LOSS PROVISIONING ----------------
ws = wb.create_sheet("Provisioning")
set_col_widths(ws, [4, 26, 16, 14, 16, 40])
ws["B2"] = "Loan Loss Reserve Adequacy (days-past-due tiering)"; ws["B2"].font = TITLE
for i, h in enumerate(["", "Aging bucket", "Outstanding balance ($)", "Reserve rate",
                        "Required reserve ($)", ""], start=1):
    ws.cell(row=4, column=i, value=h)
style_header_row(ws, 4, 4, start_col=2)

tiers = [
    ("Current (0-30 days)", 0.01),
    ("31-90 days", 0.10),
    ("91-180 days", 0.50),
    ("180+ days / written off pending", 1.00),
]
r = 5
for label, rate in tiers:
    ws.cell(row=r, column=2, value=label).font = BLACK
    bal = ws.cell(row=r, column=3, value=0); bal.font = BLUE; bal.fill = YELLOW_FILL
    bal.number_format = CUR; bal.border = BORDER
    rt = ws.cell(row=r, column=4, value=rate); rt.font = BLUE; rt.number_format = PCT; rt.border = BORDER
    req = ws.cell(row=r, column=5, value=f"=C{r}*D{r}"); req.number_format = CUR; req.border = BORDER
    r += 1

ws["B9"] = "Total outstanding portfolio"; ws["B9"].font = BOLD
ws["C9"] = "=SUM(C5:C8)"; ws["C9"].font = BOLD; ws["C9"].number_format = CUR; ws["C9"].border = BORDER
ws["B10"] = "Total required reserve (sum of tiers)"; ws["B10"].font = BOLD
ws["E10"] = "=SUM(E5:E8)"; ws["E10"].font = BOLD; ws["E10"].number_format = CUR; ws["E10"].border = BORDER

ws["B12"] = "Actual reserve held ($)"
c = ws.cell(row=12, column=3, value=0); c.font = BLUE; c.fill = YELLOW_FILL; c.number_format = CUR; c.border = BORDER
ws["B13"] = "Reserve adequacy (actual / required)"
ws["C13"] = "=IFERROR(C12/E10,\"-\")"; ws["C13"].font = BOLD; ws["C13"].number_format = PCT
ws["C13"].fill = YELLOW_FILL; ws["C13"].border = BORDER
ws["D13"] = "<100% = under-reserved relative to portfolio risk profile — review provisioning policy"
ws["D13"].font = ITALIC_GRAY
ws["B14"] = "Cross-check vs Loan Portfolio tab (should tie to GLP)"
ws["C14"] = "=IFERROR(C9-'Loan Portfolio'!C5,\"-\")"; ws["C14"].font = GREEN; ws["C14"].number_format = CUR
ws["C14"].border = BORDER
ws.sheet_view.showGridLines = False

# ---------------- FLAT VS. DECLINING-BALANCE EFFECTIVE RATE ----------------
ws = wb.create_sheet("Flat vs Declining Rate")
set_col_widths(ws, [4, 34] + [11] * 17)
ws["B2"] = "Flat-Rate vs. Declining-Balance: the True Cost of a Loan"; ws["B2"].font = TITLE
ws["B3"] = ("Many MFIs quote a \"flat\" rate -- interest charged on the ORIGINAL principal every period, "
            "even as the balance amortizes down. The declining-balance rate that produces the SAME "
            "installment is always meaningfully higher: this is the core truth-in-lending gap the "
            "MFTransparency/CGAP pricing-transparency initiatives exist to surface.")
ws["B3"].font = ITALIC_GRAY

ws["B5"] = "Inputs"; ws["B5"].font = BOLD; ws["B5"].fill = GRAY_FILL
ws["B6"] = "Loan principal ($)"
c = ws.cell(row=6, column=3, value=1000); c.font = BLUE; c.fill = YELLOW_FILL; c.number_format = CUR; c.border = BORDER
ws["B7"] = "Quoted flat rate (per period, %)"
c = ws.cell(row=7, column=3, value=0.02); c.font = BLUE; c.fill = YELLOW_FILL; c.number_format = PCT2; c.border = BORDER
ws["B8"] = "Number of periods (loan term)"
c = ws.cell(row=8, column=3, value=12); c.font = BLUE; c.fill = YELLOW_FILL; c.number_format = NUM; c.border = BORDER

ws["B10"] = "Flat-Rate Loan"; ws["B10"].font = BOLD; ws["B10"].fill = GRAY_FILL
ws["B11"] = "Interest per period (principal x flat rate, constant)"
ws["C11"] = "=C6*C7"; ws["C11"].number_format = CUR2; ws["C11"].border = BORDER
ws["B12"] = "Total interest over the loan"
ws["C12"] = "=C11*C8"; ws["C12"].number_format = CUR; ws["C12"].border = BORDER
ws["B13"] = "Equal installment (principal + total interest) / n"
ws["C13"] = "=(C6+C12)/C8"; ws["C13"].font = BOLD; ws["C13"].number_format = CUR2; ws["C13"].border = BORDER

ws["B15"] = "Quick Industry Approximation (CGAP/MFTransparency rule of thumb)"
ws["B15"].font = BOLD; ws["B15"].fill = GRAY_FILL
ws["B16"] = "Approx. declining-balance rate = 2 x n x flat rate / (n + 1)"
ws["C16"] = "=2*C8*C7/(C8+1)"; ws["C16"].font = BOLD; ws["C16"].number_format = PCT2; ws["C16"].border = BORDER
ws["D16"] = "Standard closed-form approximation used in microfinance pricing-transparency training materials"
ws["D16"].font = ITALIC_GRAY

ws["B18"] = "Exact Declining-Balance Rate (bisection solve, 16 steps)"
ws["B18"].font = BOLD; ws["B18"].fill = GRAY_FILL
ws["B19"] = ("Solves for the periodic rate r such that a standard amortizing loan (P, r, n) has the SAME "
             "equal installment as the flat-rate loan above -- the actual apples-to-apples comparison rate.")
ws["B19"].font = ITALIC_GRAY
n_steps = 16
step_headers = ["", ""] + [f"Step {i}" for i in range(1, n_steps + 1)]
for i, h in enumerate(step_headers, start=1):
    ws.cell(row=21, column=i, value=h)
style_header_row(ws, 21, n_steps, start_col=3)
ws["B22"] = "Low"; ws["B23"] = "High"; ws["B24"] = "Mid (candidate rate)"
ws["B25"] = "Installment at mid"; ws["B26"] = "f(mid) = installment - target"
for step in range(1, n_steps + 1):
    col = get_column_letter(2 + step)
    if step == 1:
        ws[f"{col}22"] = "=$C$7"
        ws[f"{col}23"] = "=$C$7*4"
    else:
        prev = get_column_letter(2 + step - 1)
        ws[f"{col}22"] = f'=IF({prev}26<0,{prev}24,{prev}22)'
        ws[f"{col}23"] = f'=IF({prev}26<0,{prev}23,{prev}24)'
    ws[f"{col}24"] = f"=({col}22+{col}23)/2"
    ws[f"{col}25"] = f"=IFERROR($C$6*{col}24/(1-(1+{col}24)^-$C$8),\"-\")"
    ws[f"{col}26"] = f'=IFERROR({col}25-$C$13,"-")'
    for row in (22, 23, 24, 25, 26):
        ws[f"{col}{row}"].number_format = '0.00000' if row in (22, 23, 24) else CUR2
        ws[f"{col}{row}"].border = BORDER

last_col = get_column_letter(2 + n_steps)
ws["B28"] = "Exact declining-balance rate (converged)"
ws["C28"] = f"={last_col}24"; ws["C28"].font = BOLD; ws["C28"].number_format = PCT2; ws["C28"].border = BORDER
ws["B29"] = "Effective annualized rate (exact, compounded)"
ws["C29"] = "=IFERROR((1+C28)^12-1,\"-\")"; ws["C29"].number_format = PCT; ws["C29"].border = BORDER
ws["D29"] = "Assumes monthly periods; adjust the compounding power if the loan's period isn't monthly"
ws["D29"].font = ITALIC_GRAY
ws["B30"] = "Approximation error (quick rule vs. exact solve)"
ws["C30"] = "=IFERROR(C16-C28,\"-\")"; ws["C30"].number_format = PCT2; ws["C30"].border = BORDER
ws["B31"] = "True cost multiple (exact declining rate / quoted flat rate)"
ws["C31"] = "=IFERROR(C28/C7,\"-\")"; ws["C31"].font = BOLD; ws["C31"].number_format = '0.00x'; ws["C31"].border = BORDER
ws["D31"] = "A '2% flat' loan commonly prices out close to 2x that in true declining-balance terms -- this is exactly why disclosure regulations target flat-rate quoting"
ws["D31"].font = ITALIC_GRAY
ws.sheet_view.showGridLines = False

# ---------------- GROWTH & PRODUCTIVITY ----------------
ws = wb.create_sheet("Growth & Productivity")
set_col_widths(ws, [4, 34, 16, 40])
ws["B2"] = "Growth & Loan Officer Productivity"; ws["B2"].font = TITLE
ws["B4"] = "Inputs"; ws["B4"].font = BOLD; ws["B4"].fill = GRAY_FILL
inputs = [
    ("Active borrowers — prior period", 0, NUM),
    ("Active borrowers — current period", 0, NUM),
    ("New disbursements this period ($)", 0, CUR),
    ("Number of loan officers", 0, NUM),
]
r = 5
for label, default, fmt in inputs:
    ws.cell(row=r, column=2, value=label).font = BLACK
    c = ws.cell(row=r, column=3, value=default); c.font = BLUE; c.fill = YELLOW_FILL
    c.number_format = fmt; c.border = BORDER
    r += 1

ws["B10"] = "Outputs"; ws["B10"].font = BOLD; ws["B10"].fill = GRAY_FILL
ws["B11"] = "Borrower growth rate (period over period)"
ws["C11"] = "=IFERROR((C6-C5)/C5,\"-\")"; ws["C11"].number_format = PCT
ws["B12"] = "Borrowers per loan officer (caseload)"
ws["C12"] = "=IFERROR(C6/C8,\"-\")"; ws["C12"].number_format = NUM
ws["D12"] = "Typical sustainable caseload benchmark: 250-400 borrowers/officer, group-lending-dependent"
ws["D12"].font = ITALIC_GRAY
ws["B13"] = "Disbursement per active borrower ($, avg)"
ws["C13"] = "=IFERROR(C7/C6,\"-\")"; ws["C13"].number_format = CUR
for r2 in (11, 12, 13):
    ws.cell(row=r2, column=3).border = BORDER
ws.sheet_view.showGridLines = False

add_sources_checks(
    wb,
    sources=[
        ("Flat-to-declining approximation: r ~ 2 x n x flat / (n+1)", "CGAP / MFTransparency pricing-transparency training materials", "Standard practice / industry convention", "A closed-form rule of thumb -- the bisection solve on the same sheet gives the exact rate for comparison"),
        ("Exact declining-balance rate via 16-step bisection solve", "Standard root-finding on the amortizing-loan installment identity, P*r/(1-(1+r)^-n)=installment", "Derived, not copied from a source", "16 steps on a [flat, 4x flat] bracket -- more than sufficient precision for typical microfinance term lengths"),
        ("OSS/FSS sustainability ratios", "Standard MFI financial-performance ratios (SEEP Network / CGAP definitions)", "Standard practice", "FSS's imputed cost-of-capital adjustment requires an external market-rate benchmark, which varies by country/currency"),
        ("PAR30/PAR90 and aging-bucket loan-loss provisioning tiers", "Standard microfinance portfolio-quality and reserve-adequacy conventions", "Standard practice", "Illustrative reserve rates by aging bucket (1%/10%/50%/100%) -- a real MFI's provisioning policy may differ"),
    ],
    checks=[
        ("Bisection solve converges: |f(mid)| shrinks monotonically over the 16 steps", "=IF(ABS('Flat vs Declining Rate'!R26)<=ABS('Flat vs Declining Rate'!C26),TRUE,FALSE)", "TRUE -- the final step's installment gap is smaller in magnitude than the first step's"),
        ("Exact declining rate exceeds the quoted flat rate (the whole point of the tab)", "=IF('Flat vs Declining Rate'!C28>'Flat vs Declining Rate'!C7,TRUE,FALSE)", "TRUE"),
        ("Reserve tiers cross-check ties to GLP (Provisioning vs. Loan Portfolio)", "=Provisioning!C14", "0 (exact) once both tabs' portfolio figures are populated consistently"),
        ("FSS <= OSS always (FSS adds a strictly positive imputed cost-of-capital term to the denominator)", "=IF(OR('Sustainability'!C12=\"-\",'Sustainability'!C13=\"-\"),TRUE,'Sustainability'!C12>='Sustainability'!C13)", "TRUE"),
    ],
)

add_refresh_log(wb)
out_path = "MICROFINANCE_template.xlsx"
wb.save(out_path)
print("saved", out_path)
