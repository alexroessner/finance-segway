import openpyxl
from template_helpers import *

wb = openpyxl.Workbook()
wb.remove(wb.active)

add_cover(wb, "[DEAL] — Structured Finance / Securitization Model", [
    ("Asset class:", "RMBS / ABS / CLO"),
    ("Closing date:", "[date]"),
    ("Last refreshed:", "[date]"),
    ("Refresh cadence:", "Weekly (monthly at distribution date)"),
])

# ---------------- COLLATERAL POOL ----------------
ws = wb.create_sheet("Collateral Pool")
set_col_widths(ws, [4, 30, 16, 40])
ws["B2"] = "Collateral Pool Summary"; ws["B2"].font = TITLE
inputs = [
    ("Aggregate pool balance ($)", 0, CUR),
    ("Weighted avg coupon (WAC, %)", 0.06, PCT),
    ("Weighted avg maturity (WAM, months)", 360, NUM),
    ("Conditional prepayment rate assumption (CPR, %)", 0.08, PCT),
    ("Conditional default rate assumption (CDR, annual %)", 0.03, PCT),
    ("Recovery rate on defaults (%)", 0.50, PCT),
    ("Recovery lag (months from default to cash)", 3, NUM),
]
r = 5
for label, default, fmt in inputs:
    ws.cell(row=r, column=2, value=label).font = BLACK
    c = ws.cell(row=r, column=3, value=default); c.font = BLUE; c.fill = YELLOW_FILL
    c.number_format = fmt; c.border = BORDER
    r += 1

ws["B13"] = "Single Monthly Mortality (SMM) from CPR"
ws["C13"] = "=1-(1-C8)^(1/12)"; ws["C13"].number_format = PCT2
ws["D13"] = "SMM = 1-(1-CPR)^(1/12) — standard CPR-to-SMM conversion"
ws["D13"].font = ITALIC_GRAY
ws["C13"].border = BORDER
ws["B14"] = "Monthly Default Rate (MDR) from CDR"
ws["C14"] = "=1-(1-C9)^(1/12)"; ws["C14"].number_format = PCT2
ws["D14"] = "MDR = 1-(1-CDR)^(1/12) — same conditional-rate-to-monthly conversion as SMM, applied to defaults instead of prepayments"
ws["D14"].font = ITALIC_GRAY
ws["C14"].border = BORDER
ws["B15"] = "Scheduled monthly P&I payment (level-pay amortization)"
ws["C15"] = "=IFERROR(C5*(C6/12)/(1-(1+C6/12)^(-C7)),\"-\")"
ws["C15"].font = BOLD; ws["C15"].number_format = CUR2; ws["C15"].border = BORDER
ws["D15"] = "Standard mortgage-style level payment: Balance x (WAC/12) / (1-(1+WAC/12)^-WAM). Constant $ payment; the interest/principal split shifts over time as the balance amortizes."
ws["D15"].font = ITALIC_GRAY
ws.sheet_view.showGridLines = False

# ---------------- TRANCHE WATERFALL ----------------
ws = wb.create_sheet("Waterfall")
set_col_widths(ws, [4, 18, 14, 14, 14, 16, 40])
ws["B2"] = "Tranche Structure & Credit Enhancement"; ws["B2"].font = TITLE
headers = ["", "Tranche", "Face ($)", "% of pool", "Coupon", "Credit enhancement %", "Notes"]
for i, h in enumerate(headers, start=1):
    ws.cell(row=4, column=i, value=h)
style_header_row(ws, 4, len(headers)-1)
tranches = ["Class A (senior)", "Class B (mezz)", "Class C (mezz)", "Class D (subordinate)", "Equity / residual"]
r = 5
for t in tranches:
    ws.cell(row=r, column=2, value=t).font = BLACK
    c_face = ws.cell(row=r, column=3, value=0); c_face.font = BLUE; c_face.number_format = CUR; c_face.border = BORDER
    c_cpn = ws.cell(row=r, column=5, value=0); c_cpn.font = BLUE; c_cpn.number_format = PCT; c_cpn.border = BORDER
    r += 1
total_row = r
ws.cell(row=total_row, column=2, value="Total").font = BOLD
ws.cell(row=total_row, column=3, value=f"=SUM(C5:C{total_row-1})").font = BOLD
ws.cell(row=total_row, column=3).number_format = CUR
for rr in range(5, total_row):
    ws.cell(row=rr, column=4, value=f"=IFERROR(C{rr}/$C${total_row},\"-\")").number_format = PCT
    # CE = sum of face value of all tranches junior to this one, as % of pool
    ws.cell(row=rr, column=6, value=f"=IFERROR(SUM(C{rr+1}:C{total_row-1})/$C${total_row},\"-\")").number_format = PCT
ws["B" + str(total_row+2)] = "CE% for a tranche = subordinate tranche cushion that absorbs losses before it does"
ws["B" + str(total_row+2)].font = ITALIC_GRAY
ws.sheet_view.showGridLines = False

# ---------------- TRANCHE CASH FLOW WATERFALL ----------------
# The Waterfall tab above is a static, point-in-time structure (face
# values, credit enhancement %). A real securitization is a DYNAMIC
# monthly cash flow allocation: pool collections (scheduled P&I,
# prepayments, recoveries net of a servicing/liquidation lag) cascade
# principal senior-to-junior (Class A paid down first), while losses
# cascade the OPPOSITE direction, junior-to-senior (Equity absorbs first,
# protecting Class A last) — that two-directional cascade IS what credit
# enhancement / subordination actually means, not just the static % on
# the Waterfall tab. 12 months here (not the full WAM) — enough to show
# every mechanic (sequential pay, loss allocation, recovery lag) working
# without an unreadable 360-column schedule.
ws = wb.create_sheet("Tranche Cash Flow Waterfall")
N_MONTHS = 12
set_col_widths(ws, [4, 34] + [11] * N_MONTHS + [4])
ws["B2"] = f"{N_MONTHS}-Month Tranche Cash Flow Waterfall"; ws["B2"].font = TITLE

ws.cell(row=4, column=2, value="Pool Cash Flow")
ws.cell(row=4, column=2).font = BOLD
ws.cell(row=4, column=2).fill = GRAY_FILL
for m in range(1, N_MONTHS + 1):
    c = ws.cell(row=4, column=2 + m, value=f"M{m}")
    c.font = BOLD_WHITE; c.fill = HEADER_FILL; c.alignment = Alignment(horizontal="center")

pool_rows = {
    "beg": 5, "sched_int": 6, "sched_prin": 7, "defaults": 8,
    "prepay": 9, "recovery": 10, "loss": 11, "end": 12,
    "prin_avail": 14, "loss_avail": 15,
}
labels = {
    "beg": "Beginning balance", "sched_int": "Scheduled interest (WAC/12 x beg.)",
    "sched_prin": "Scheduled principal (level-pay P&I - interest)",
    "defaults": "Defaults (MDR x beg.)", "prepay": "Prepayments (SMM x remaining)",
    "recovery": "Recovery proceeds (lagged, net of severity)",
    "loss": "Realized loss (defaults x (1 - recovery rate))",
    "end": "Ending balance",
    "prin_avail": "Principal available for tranches",
    "loss_avail": "Loss to allocate to tranches",
}
for key, row in pool_rows.items():
    ws.cell(row=row, column=2, value=labels[key]).font = BOLD if key in ("prin_avail", "loss_avail") else BLACK

for m in range(1, N_MONTHS + 1):
    col = get_column_letter(2 + m)
    prev = get_column_letter(1 + m)
    r = pool_rows
    if m == 1:
        ws[f"{col}{r['beg']}"] = "='Collateral Pool'!$C$5"
    else:
        ws[f"{col}{r['beg']}"] = f"={prev}{r['end']}"
    ws[f"{col}{r['sched_int']}"] = f"={col}{r['beg']}*'Collateral Pool'!$C$6/12"
    ws[f"{col}{r['sched_prin']}"] = f"=MAX(0,'Collateral Pool'!$C$15-{col}{r['sched_int']})"
    ws[f"{col}{r['defaults']}"] = f"={col}{r['beg']}*'Collateral Pool'!$C$14"
    ws[f"{col}{r['prepay']}"] = (f"=MAX(0,{col}{r['beg']}-{col}{r['sched_prin']}"
                                  f"-{col}{r['defaults']})*'Collateral Pool'!$C$13")
    ws[f"{col}{r['loss']}"] = f"={col}{r['defaults']}*(1-'Collateral Pool'!$C$10)"
    ws[f"{col}{r['end']}"] = (f"={col}{r['beg']}-{col}{r['sched_prin']}"
                               f"-{col}{r['defaults']}-{col}{r['prepay']}")
    ws[f"{col}{r['prin_avail']}"] = f"={col}{r['sched_prin']}+{col}{r['prepay']}+{col}{r['recovery']}"
    ws[f"{col}{r['loss_avail']}"] = f"={col}{r['loss']}"
    for key in pool_rows:
        cell = ws[f"{col}{pool_rows[key]}"]
        cell.number_format = CUR
        cell.border = BORDER

# Recovery proceeds need a fixed month offset (the recovery lag), computed
# in Python since Excel's OFFSET with a cell-referenced distance is harder
# to audit than a direct cell reference — the lag is a fixed assumption, so
# bake the target column in directly rather than looking it up at runtime.
RECOVERY_LAG_MONTHS = 3  # must match Collateral Pool!C11's default
for m in range(1, N_MONTHS + 1):
    col = get_column_letter(2 + m)
    target_month = m - RECOVERY_LAG_MONTHS
    if target_month >= 1:
        target_col = get_column_letter(2 + target_month)
        ws[f"{col}{pool_rows['recovery']}"] = (
            f"={target_col}{pool_rows['defaults']}*'Collateral Pool'!$C$10")
    else:
        ws[f"{col}{pool_rows['recovery']}"] = 0
    ws[f"{col}{pool_rows['recovery']}"].number_format = CUR
    ws[f"{col}{pool_rows['recovery']}"].border = BORDER
ws.cell(row=16, column=2,
        value=(f"Recovery lag fixed at {RECOVERY_LAG_MONTHS} months to match Collateral Pool's "
               "default assumption — if you change that input, update RECOVERY_LAG_MONTHS in the "
               "builder and regenerate, since the lag is baked into which column each recovery "
               "formula references, not read dynamically."))
ws.cell(row=16, column=2).font = ITALIC_GRAY

# ---- Tranche waterfall: 5 tranches, principal cascades senior->junior,
# losses cascade junior->senior. Each tranche gets a 4-row block. ----
tranche_names = ["Class A (senior)", "Class B (mezz)", "Class C (mezz)",
                  "Class D (subordinate)", "Equity / residual"]
block0 = 19
blocks = {i: block0 + i * 5 for i in range(5)}  # header row of each tranche's block

for i, name in enumerate(tranche_names):
    base = blocks[i]
    ws.cell(row=base, column=2, value=name).font = BOLD
    ws.cell(row=base, column=2).fill = GRAY_FILL
    ws.cell(row=base + 1, column=2, value="  Beginning balance").font = BLACK
    ws.cell(row=base + 2, column=2, value="  Principal received").font = BLACK
    ws.cell(row=base + 3, column=2, value="  Loss allocated").font = BLACK
    ws.cell(row=base + 4, column=2, value="  Ending balance").font = BLACK

for m in range(1, N_MONTHS + 1):
    col = get_column_letter(2 + m)
    prev = get_column_letter(1 + m)

    # Principal cascades senior (A) to junior (Equity): each tranche gets
    # MIN(what's left after more senior tranches took theirs, its own
    # beginning balance) — can never receive more than it's owed.
    prin_cells_so_far = []
    for i in range(5):
        base = blocks[i]
        beg_cell = f"{col}{base + 1}"
        if m == 1:
            ws[beg_cell] = f"='Waterfall'!C{5 + i}"
        else:
            ws[beg_cell] = f"={prev}{base + 4}"
        ws[beg_cell].number_format = CUR
        ws[beg_cell].border = BORDER

        remaining_expr = f"{col}{pool_rows['prin_avail']}"
        if prin_cells_so_far:
            remaining_expr += "-" + "-".join(prin_cells_so_far)
        prin_cell = f"{col}{base + 2}"
        ws[prin_cell] = f"=MAX(0,MIN({remaining_expr},{beg_cell}))"
        ws[prin_cell].number_format = CUR
        ws[prin_cell].border = BORDER
        prin_cells_so_far.append(prin_cell)

    # Losses cascade junior (Equity) to senior (A): reverse order.
    loss_cells_so_far = []
    for i in reversed(range(5)):
        base = blocks[i]
        beg_cell = f"{col}{base + 1}"
        prin_cell = f"{col}{base + 2}"
        remaining_after_principal = f"({beg_cell}-{prin_cell})"
        remaining_loss_expr = f"{col}{pool_rows['loss_avail']}"
        if loss_cells_so_far:
            remaining_loss_expr += "-" + "-".join(loss_cells_so_far)
        loss_cell = f"{col}{base + 3}"
        ws[loss_cell] = f"=MAX(0,MIN({remaining_loss_expr},{remaining_after_principal}))"
        ws[loss_cell].number_format = CUR
        ws[loss_cell].border = BORDER
        loss_cells_so_far.append(loss_cell)

        end_cell = f"{col}{base + 4}"
        ws[end_cell] = f"={beg_cell}-{prin_cell}-{loss_cell}"
        ws[end_cell].number_format = CUR
        ws[end_cell].border = BORDER

# ---- Per-tranche WAL, same definition as the pool-level WAL but applied
# to each tranche's own principal-received row -- senior tranches should
# show a materially shorter WAL than subordinate ones, since they're paid
# down first. ----
wal_row0 = block0 + 5 * 5 + 2
ws.cell(row=wal_row0 - 1, column=2, value="Per-Tranche WAL (this 12-month window only)").font = BOLD
ws.cell(row=wal_row0 - 1, column=2).fill = GRAY_FILL
first_col, last_col = get_column_letter(3), get_column_letter(2 + N_MONTHS)
for i, name in enumerate(tranche_names):
    base = blocks[i]
    prin_range = f"{first_col}{base + 2}:{last_col}{base + 2}"
    row = wal_row0 + i
    ws.cell(row=row, column=2, value=name).font = BLACK
    ws.cell(row=row, column=3,
            value=(f"=IFERROR(SUMPRODUCT(COLUMN({prin_range})-COLUMN({first_col}{base + 2})+1,{prin_range})"
                   f"/SUM({prin_range})/12,\"-\")"))
    ws.cell(row=row, column=3).number_format = "0.00"
    ws.cell(row=row, column=3).border = BORDER
ws.cell(row=wal_row0 + 5, column=2,
        value=("Truncated to this 12-month window, not the full deal life — senior tranches whose "
               "principal keeps flowing past month 12 will show an understated WAL here. Extend the "
               "schedule to the deal's actual WAM for a real disclosure number."))
ws.cell(row=wal_row0 + 5, column=2).font = ITALIC_GRAY

# ---- Reconciliation: pool ending balance vs. sum of tranche ending
# balances. These will NOT tie exactly within a truncated window, and
# that's a real, quantifiable modeling effect worth surfacing rather than
# leaving as an unexplained gap: loss is recognized immediately at default
# (severity x default amount), but the offsetting recovery CASH arrives
# `Collateral Pool!C11` months later. Defaults from the last few months of
# the window haven't had their recovery land yet, so the tranches (whose
# balance only falls from principal PAID + loss ALLOCATED) haven't
# absorbed as much reduction as the pool (whose balance falls the moment a
# loan defaults, independent of when recovery cash shows up) — the two
# converge once the window runs past the recovery lag.
recon_row = wal_row0 + 7
ws.cell(row=recon_row, column=2, value="Reconciliation: Pool vs. Tranches").font = BOLD
ws.cell(row=recon_row, column=2).fill = GRAY_FILL
ws.cell(row=recon_row + 1, column=2, value="Pool ending balance (month 12)")
pool_end_cell = f"{last_col}{pool_rows['end']}"
ws.cell(row=recon_row + 1, column=3, value=f"={pool_end_cell}")
ws.cell(row=recon_row + 1, column=3).number_format = CUR
ws.cell(row=recon_row + 1, column=3).border = BORDER
tranche_end_cells = [f"{last_col}{blocks[i] + 4}" for i in range(5)]
ws.cell(row=recon_row + 2, column=2, value="Sum of tranche ending balances (month 12)")
ws.cell(row=recon_row + 2, column=3, value="=" + "+".join(tranche_end_cells))
ws.cell(row=recon_row + 2, column=3).number_format = CUR
ws.cell(row=recon_row + 2, column=3).border = BORDER
ws.cell(row=recon_row + 3, column=2, value="Difference (pool - tranches)")
ws.cell(row=recon_row + 3, column=3, value=f"=C{recon_row + 1}-C{recon_row + 2}")
ws.cell(row=recon_row + 3, column=3).number_format = CUR
ws.cell(row=recon_row + 3, column=3).border = BORDER
recovered_defaults_terms = "+".join(
    f"{get_column_letter(2 + m)}{pool_rows['defaults']}"
    for m in range(N_MONTHS - RECOVERY_LAG_MONTHS + 1, N_MONTHS + 1)
)
ws.cell(row=recon_row + 4, column=2,
        value=f"Expected difference: -(recovery rate x defaults from the last {RECOVERY_LAG_MONTHS} months, not yet recovered in-window)")
ws.cell(row=recon_row + 4, column=3,
        value=f"=-'Collateral Pool'!$C$10*({recovered_defaults_terms})")
ws.cell(row=recon_row + 4, column=3).number_format = CUR
ws.cell(row=recon_row + 4, column=3).border = BORDER
ws.cell(row=recon_row + 5, column=2,
        value="Check (actual difference - expected difference, should be ~0)")
ws.cell(row=recon_row + 5, column=3, value=f"=C{recon_row + 3}-C{recon_row + 4}")
ws.cell(row=recon_row + 5, column=3).number_format = CUR
ws.cell(row=recon_row + 5, column=3).font = BOLD
ws.cell(row=recon_row + 5, column=3).fill = YELLOW_FILL
ws.cell(row=recon_row + 5, column=3).border = BORDER
ws.sheet_view.showGridLines = False

add_refresh_log(wb)
out_path = "SECURITIZATION_template.xlsx"
wb.save(out_path)
print("saved", out_path)
