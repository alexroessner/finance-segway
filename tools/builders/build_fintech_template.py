import openpyxl
from template_helpers import *

wb = openpyxl.Workbook()
wb.remove(wb.active)

# "Last refreshed" must land on row 6 (C6) -- weekly_refresh_check.py reads
# it unconditionally. This tab previously had only one field before it
# ("Business model"), landing Last refreshed on row 5 instead: the checker
# read "Refresh cadence" (text like "Weekly", unparseable as a date) at C6
# and silently flagged every Fintech instance "NO REFRESH DATE SET" even
# when properly filled in.
add_cover(wb, "[COMPANY] — Fintech / Payments Model", [
    ("Business model:", "Payments / lending / neobank / infra"),
    ("Regulatory status:", "[licensed / partner bank / sponsor bank]"),
    ("Last refreshed:", "[date]"),
    ("Next cohort/unit-economics review:", "[date]"),
    ("Refresh cadence:", "Weekly"),
])

# ---------------- UNIT ECONOMICS ----------------
ws = wb.create_sheet("Unit Economics")
set_col_widths(ws, [4, 30, 16, 40])
ws["B2"] = "Unit Economics"; ws["B2"].font = TITLE
inputs = [
    ("Total payment volume, TPV ($/mo)", 0, CUR),
    ("Take rate (%)", 0.025, PCT2),
    ("Interchange/processing cost (% of TPV)", 0.015, PCT2),
    ("CAC ($ per customer)", 0, CUR),
    ("Avg monthly revenue per customer ($)", 0, CUR),
    ("Monthly gross margin per customer (%)", 0.60, PCT),
    ("Monthly churn rate (%)", 0.03, PCT),
]
r = 5
for label, default, fmt in inputs:
    ws.cell(row=r, column=2, value=label).font = BLACK
    c = ws.cell(row=r, column=3, value=default); c.font = BLUE; c.fill = YELLOW_FILL
    c.number_format = fmt; c.border = BORDER
    r += 1

ws["B13"] = "Outputs"; ws["B13"].font = BOLD; ws["B13"].fill = GRAY_FILL
ws["B14"] = "Revenue (take rate x TPV)"
ws["C14"] = "=C5*C6"; ws["C14"].number_format = CUR
ws["B15"] = "Processing cost ($)"
ws["C15"] = "=C5*C7"; ws["C15"].number_format = CUR
ws["B16"] = "Net revenue after processing cost"
ws["C16"] = "=C14-C15"; ws["C16"].font = BOLD; ws["C16"].number_format = CUR
ws["B17"] = "Customer lifetime (months) = 1/churn"
ws["C17"] = "=IFERROR(1/C11,\"-\")"; ws["C17"].number_format = '0.0'
ws["B18"] = "LTV = monthly rev x gross margin x lifetime"
ws["C18"] = "=C9*C10*C17"; ws["C18"].font = BOLD; ws["C18"].number_format = CUR
ws["B19"] = "LTV / CAC ratio"
ws["C19"] = "=IFERROR(C18/C8,\"-\")"; ws["C19"].font = BOLD; ws["C19"].number_format = '0.00x'
ws["D19"] = "Rule of thumb: >3x is healthy, <1x means losing money per customer"
ws["D19"].font = ITALIC_GRAY
ws["B20"] = "CAC payback period (months)"
ws["C20"] = "=IFERROR(C8/(C9*C10),\"-\")"; ws["C20"].number_format = '0.0'
for r2 in range(14, 21):
    ws.cell(row=r2, column=3).border = BORDER
ws.sheet_view.showGridLines = False

# ---------------- INTERCHANGE ECONOMICS (DURBIN) ----------------
ws = wb.create_sheet("Interchange Economics")
set_col_widths(ws, [4, 40, 18, 18, 40])
ws["B2"] = "Interchange Economics — Durbin-Regulated vs. Exempt"; ws["B2"].font = TITLE
ws["B3"] = ("Reg II caps DEBIT interchange for issuers with >$10B in assets. Issuers below that threshold are "
            "EXEMPT and can charge network-published unregulated rates -- roughly 3x higher on typical "
            "transaction sizes. This is the actual structural reason many neobanks partner with a small "
            "\"sponsor bank\" rather than becoming a bank themselves: it isn't just charter overhead, it's "
            "interchange economics.")
ws["B3"].font = ITALIC_GRAY

ws["B5"] = "Inputs"; ws["B5"].font = BOLD; ws["B5"].fill = GRAY_FILL
ws["B6"] = "Average transaction size ($)"
c = ws.cell(row=6, column=3, value=40.00); c.font = BLUE; c.fill = YELLOW_FILL; c.number_format = CUR2; c.border = BORDER
ws["B7"] = "TPV this period ($/mo)"
ws["C7"] = "='Unit Economics'!C5"; ws["C7"].font = GREEN; ws["C7"].number_format = CUR; ws["C7"].border = BORDER
ws["B8"] = "Estimated transaction count"
ws["C8"] = "=IFERROR(C7/C6,\"-\")"; ws["C8"].number_format = NUM; ws["C8"].border = BORDER

ws["B10"] = "Regulated (Durbin-capped, issuing bank > $10B assets)"; ws["B10"].font = BOLD; ws["B10"].fill = GRAY_FILL
ws["B11"] = "Interchange per transaction (Reg II cap: $0.22 + 0.05% x txn size)"
ws["C11"] = "=0.22+0.0005*C6"; ws["C11"].number_format = CUR2; ws["C11"].border = BORDER
ws["B12"] = "Effective interchange rate (% of TPV)"
ws["C12"] = "=IFERROR(C11/C6,\"-\")"; ws["C12"].number_format = PCT2; ws["C12"].border = BORDER
ws["B13"] = "Interchange income/cost this period (rate x TPV)"
ws["C13"] = "=IFERROR(C12*C7,\"-\")"; ws["C13"].font = BOLD; ws["C13"].number_format = CUR; ws["C13"].border = BORDER

ws["B15"] = "Exempt (Durbin-exempt, issuing bank < $10B assets -- typical sponsor-bank structure)"
ws["B15"].font = BOLD; ws["B15"].fill = GRAY_FILL
ws["B16"] = "Interchange per transaction (network unregulated rate: $0.04 + 1.65% x txn size)"
ws["C16"] = "=0.04+0.0165*C6"; ws["C16"].number_format = CUR2; ws["C16"].border = BORDER
ws["B17"] = "Effective interchange rate (% of TPV)"
ws["C17"] = "=IFERROR(C16/C6,\"-\")"; ws["C17"].number_format = PCT2; ws["C17"].border = BORDER
ws["B18"] = "Interchange income/cost this period (rate x TPV)"
ws["C18"] = "=IFERROR(C17*C7,\"-\")"; ws["C18"].font = BOLD; ws["C18"].number_format = CUR; ws["C18"].border = BORDER

ws["B20"] = "Exempt vs. Regulated Advantage"; ws["B20"].font = BOLD; ws["B20"].fill = GRAY_FILL
ws["B21"] = "$ difference this period (exempt - regulated)"
ws["C21"] = "=C18-C13"; ws["C21"].font = BOLD; ws["C21"].number_format = CUR; ws["C21"].border = BORDER
ws["B22"] = "Annualized $ difference"
ws["C22"] = "=C21*12"; ws["C22"].number_format = CUR; ws["C22"].border = BORDER
ws["B23"] = "Exempt uplift (%)"
ws["C23"] = "=IFERROR(C18/C13-1,\"-\")"; ws["C23"].number_format = PCT; ws["C23"].border = BORDER
ws["D23"] = "This is a per-transaction-size-dependent advantage -- it shrinks toward zero as average ticket size grows, since the ad-valorem component matters more than the fixed component at high ticket sizes."
ws["D23"].font = ITALIC_GRAY
ws.sheet_view.showGridLines = False

# ---------------- COHORT RETENTION ----------------
ws = wb.create_sheet("Cohort Retention")
set_col_widths(ws, [4, 14] + [10]*8)
ws["B2"] = "Cohort Retention (% of cohort still active)"; ws["B2"].font = TITLE
ws["B4"] = "Cohort"; ws["B4"].font = BOLD; ws["B4"].fill = GRAY_FILL
months = [f"M{i}" for i in range(0, 8)]
for i, m in enumerate(months, start=3):
    c = ws.cell(row=4, column=i, value=m); c.font = BOLD; c.fill = GRAY_FILL
cohorts = ["Jan cohort", "Feb cohort", "Mar cohort", "Apr cohort"]
r = 5
for coh in cohorts:
    ws.cell(row=r, column=2, value=coh).font = BOLD
    for i, m in enumerate(months, start=3):
        val = 1.0 if i == 3 else 0
        c = ws.cell(row=r, column=i, value=val)
        c.font = BLUE; c.number_format = PCT; c.border = BORDER
    r += 1
ws["B9"] = "Average retention"; ws["B9"].font = BOLD
for i in range(3, 11):
    letter = get_column_letter(i)
    c = ws.cell(row=9, column=i, value=f"=AVERAGE({letter}5:{letter}8)")
    c.font = BOLD; c.number_format = PCT; c.border = BORDER
ws["B10"] = "Curve-implied LTV multiplier (sum of avg retention, M0-M7)"
ws["C10"] = "=SUM(C9:J9)"; ws["C10"].font = BOLD; ws["C10"].number_format = '0.00'
ws["C10"].border = BORDER
ws["B11"] = "M0 always = 100% by definition. Fill subsequent months as cohorts age."
ws["B11"].font = ITALIC_GRAY
ws["B12"] = ("Retention-curve LTV = monthly rev x gross margin x this multiplier — compare to the "
             "steady-state 1/churn LTV on Unit Economics; a big gap means churn isn't actually constant "
             "month to month (usually front-loaded), and the curve number is the more honest one.")
ws["B12"].font = ITALIC_GRAY
ws.sheet_view.showGridLines = False

# ---------------- FRAUD & RISK ----------------
ws = wb.create_sheet("Fraud & Risk")
set_col_widths(ws, [4, 34, 16, 44])
ws["B2"] = "Fraud, Chargeback & Credit Loss"; ws["B2"].font = TITLE
ws["B4"] = "Inputs"; ws["B4"].font = BOLD; ws["B4"].fill = GRAY_FILL
inputs2 = [
    ("Total payment volume, TPV ($/mo)", 0, CUR),
    ("Fraud loss rate (bps of TPV)", 8, NUM),
    ("Chargeback count (this period)", 0, NUM),
    ("Chargeback cost per incident ($, fee + lost goods)", 25, CUR),
    ("Credit losses — lending book only, if applicable ($)", 0, CUR),
]
r = 5
for label, default, fmt in inputs2:
    ws.cell(row=r, column=2, value=label).font = BLACK
    c = ws.cell(row=r, column=3, value=default); c.font = BLUE; c.fill = YELLOW_FILL
    c.number_format = fmt; c.border = BORDER
    r += 1

ws["B11"] = "Outputs"; ws["B11"].font = BOLD; ws["B11"].fill = GRAY_FILL
ws["B12"] = "Fraud loss ($)"
ws["C12"] = "=C5*C6/10000"; ws["C12"].number_format = CUR; ws["C12"].border = BORDER
ws["D12"] = "bps convention: 8 bps = 0.08%"
ws["D12"].font = ITALIC_GRAY
ws["B13"] = "Chargeback cost ($)"
ws["C13"] = "=C7*C8"; ws["C13"].number_format = CUR; ws["C13"].border = BORDER
ws["B14"] = "Total risk-related loss ($)"
ws["C14"] = "=C12+C13+C9"; ws["C14"].font = BOLD; ws["C14"].number_format = CUR; ws["C14"].border = BORDER
ws["B15"] = "Total loss as % of net revenue"
ws["C15"] = "=IFERROR(C14/'Unit Economics'!C16,\"-\")"; ws["C15"].font = BOLD; ws["C15"].number_format = PCT
ws["C15"].fill = YELLOW_FILL; ws["C15"].border = BORDER
ws["D15"] = "Card networks typically flag issuers/acquirers above ~90-100bps fraud-to-TPV as a monitoring risk"
ws["D15"].font = ITALIC_GRAY
ws.sheet_view.showGridLines = False

add_sources_checks(
    wb,
    sources=[
        ("Reg II regulated debit interchange cap ($0.22 + 0.05%)", "Federal Reserve Regulation II (Durbin Amendment implementing rule), covered issuers >$10B in assets", "Statutory/regulatory cap", "Includes the optional $0.01 fraud-prevention adjustment folded into the $0.22 base; actual issuer cap can vary slightly by fraud-prevention-standard compliance"),
        ("Durbin-exempt unregulated debit rate ($0.04 + 1.65%)", "Network-published unregulated debit interchange schedules (Visa/Mastercard), issuers <$10B in assets", "Standard practice / network schedules", "Illustrative approximation of published schedules -- actual rates vary by card program, merchant category, and network"),
        ("LTV = monthly revenue x gross margin x customer lifetime (1/churn)", "Standard SaaS/subscription LTV formula adapted for fintech unit economics", "Standard practice", "Assumes constant monthly churn -- the Cohort Retention tab's curve-implied multiplier is the more honest number when churn is front-loaded"),
        ("Fraud loss rate in bps of TPV", "Standard payments-industry convention", "Standard practice", "Card networks typically flag issuers/acquirers above ~90-100bps fraud-to-TPV as a monitoring risk, per the Fraud & Risk tab's note"),
    ],
    checks=[
        ("Exempt interchange income exceeds regulated at typical ticket sizes ($40 test)", "=IF('Interchange Economics'!C6=40,'Interchange Economics'!C18>'Interchange Economics'!C13,TRUE)", "TRUE at the $40 default -- confirms the Durbin-exempt advantage is actually wired, not just labeled"),
        ("Interchange income ties: rate x TPV = per-txn fee x transaction count (Regulated)", "=IFERROR('Interchange Economics'!C13-('Interchange Economics'!C11*'Interchange Economics'!C8),\"-\")", "0 (exact) once TPV is populated"),
        ("Interchange income ties: rate x TPV = per-txn fee x transaction count (Exempt)", "=IFERROR('Interchange Economics'!C18-('Interchange Economics'!C16*'Interchange Economics'!C8),\"-\")", "0 (exact) once TPV is populated"),
        ("Cohort M0 retention is always 100% by definition", "=IF(COUNTIF('Cohort Retention'!C5:C8,1)=4,TRUE,FALSE)", "TRUE"),
    ],
)

add_refresh_log(wb)
out_path = "FINTECH_template.xlsx"
wb.save(out_path)
print("saved", out_path)
