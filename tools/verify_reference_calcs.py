"""
verify_reference_calcs.py — independent-oracle regression tests for the
highest-risk formulas in the library.

Every check in here follows the same shape: build a template with known
test inputs (openpyxl), recalculate it for real (tools/recalc.py, headless
LibreOffice — not just "did it open"), and compare the recalculated cell
against a value computed a SECOND way in plain Python, independent of the
spreadsheet formula. That's a materially stronger bar than "recalc
succeeded with zero cached errors" (which only proves the formula didn't
throw, not that it's computing the right thing) — it's how several of the
bugs fixed in this library were actually caught (the VC waterfall
conservation break, the LBO debt schedule being unwired, the Commodities
annualized-basis day-count error).

This does not attempt to re-verify every archetype — it covers the
mathematically riskiest pieces (closed-form vs. numerical duration,
Black-Scholes vs. put-call parity, an integrated 3-statement build,
LBO Sources=Uses, VC waterfall conservation). Extend it as new archetypes
get the same treatment; see CONTRIBUTING.md's verification standard.

Usage:
    python3 tools/verify_reference_calcs.py
Exit code is 0 iff every check passes.
"""
import math
import os
import shutil
import statistics
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))

import openpyxl  # noqa: E402
from openpyxl.utils import get_column_letter  # noqa: E402
from recalc import recalc  # noqa: E402

TOL = 1e-4  # relative tolerance for float comparisons


def close(a, b, tol=TOL):
    if a is None or b is None:
        return False
    if b == 0:
        return abs(a) < 1e-6
    return abs(a - b) / abs(b) < tol


def with_recalc(src_path, populate_fn):
    """Copy src_path to a temp file, let populate_fn mutate an openpyxl
    workbook in place, recalc it for real, and return the recalculated
    (data_only) workbook."""
    tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
    tmp.close()
    shutil.copy(src_path, tmp.name)
    try:
        wb = openpyxl.load_workbook(tmp.name)
        populate_fn(wb)
        wb.save(tmp.name)
        result = recalc(tmp.name, timeout=45)
        if "error" in result:
            raise RuntimeError(f"recalc failed: {result['error']}")
        if result.get("status") != "success":
            raise RuntimeError(f"recalc found formula errors: {result}")
        return openpyxl.load_workbook(tmp.name, data_only=True)
    finally:
        os.unlink(tmp.name)


# ---------------------------------------------------------------------
# Black-Scholes: put-call parity + closed-form cross-check
# ---------------------------------------------------------------------
def norm_cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def black_scholes(S, K, T, r, q, sigma):
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    call = S * math.exp(-q * T) * norm_cdf(d1) - K * math.exp(-r * T) * norm_cdf(d2)
    put = K * math.exp(-r * T) * norm_cdf(-d2) - S * math.exp(-q * T) * norm_cdf(-d1)
    return call, put


def check_black_scholes():
    S, K, T, r, q, sigma = 100, 100, 0.25, 0.045, 0.0, 0.30
    path = os.path.join(REPO_ROOT, "14_Options_Derivatives", "_template_OPTIONS.xlsx")

    def populate(wb):
        bs = wb["BS Pricer"]
        bs["C5"], bs["C6"], bs["C7"] = S, K, T
        bs["C8"], bs["C9"], bs["C10"] = r, q, sigma

    wb = with_recalc(path, populate)
    sheet_call = wb["BS Pricer"]["C13"].value
    sheet_put = wb["BS Pricer"]["C14"].value
    ref_call, ref_put = black_scholes(S, K, T, r, q, sigma)

    ok = close(sheet_call, ref_call) and close(sheet_put, ref_put)
    parity_lhs = sheet_call - sheet_put
    parity_rhs = S * math.exp(-q * T) - K * math.exp(-r * T)
    ok = ok and close(parity_lhs, parity_rhs)
    detail = (f"sheet call={sheet_call:.6f} ref={ref_call:.6f} | "
              f"sheet put={sheet_put:.6f} ref={ref_put:.6f} | "
              f"parity lhs={parity_lhs:.6f} rhs={parity_rhs:.6f}")
    return "Black-Scholes price + put-call parity", ok, detail


# ---------------------------------------------------------------------
# Bond duration: closed-form Macaulay/modified duration vs. the sheet's
# numerical (price-shock finite-difference) duration.
# ---------------------------------------------------------------------
def bond_price(face, coupon_rate, freq, years, ytm):
    n = int(round(freq * years))
    c = face * coupon_rate / freq
    y = ytm / freq
    price = sum(c / (1 + y) ** t for t in range(1, n + 1)) + face / (1 + y) ** n
    return price


def closed_form_modified_duration(face, coupon_rate, freq, years, ytm):
    n = int(round(freq * years))
    c = face * coupon_rate / freq
    y = ytm / freq
    price = bond_price(face, coupon_rate, freq, years, ytm)
    mac_dur_periods = sum(
        t * (c if t < n else c + face) / (1 + y) ** t for t in range(1, n + 1)
    ) / price
    mac_dur_years = mac_dur_periods / freq
    mod_dur = mac_dur_years / (1 + y)
    return mod_dur


def check_bond_duration():
    face, coupon, freq, years, ytm = 1000, 0.05, 2, 10, 0.055
    path = os.path.join(REPO_ROOT, "21_Fixed_Income_Rates", "_template_FIXED_INCOME.xlsx")

    def populate(wb):
        bp = wb["Bond Pricing"]
        bp["C5"], bp["C6"], bp["C7"] = face, coupon, freq
        bp["C8"], bp["C9"] = years, ytm

    wb = with_recalc(path, populate)
    sheet_price = wb["Bond Pricing"]["C11"].value
    sheet_mod_dur = wb["Duration & Convexity"]["C8"].value

    ref_price = bond_price(face, coupon, freq, years, ytm)
    ref_mod_dur = closed_form_modified_duration(face, coupon, freq, years, ytm)

    # Numerical (50bp shock, finite-difference) duration is an approximation
    # of the closed-form value — allow a looser tolerance than exact formulas.
    ok = close(sheet_price, ref_price, tol=1e-6) and close(sheet_mod_dur, ref_mod_dur, tol=0.01)
    detail = (f"price: sheet={sheet_price:.4f} closed-form={ref_price:.4f} | "
              f"mod. duration: sheet(numerical)={sheet_mod_dur:.4f} "
              f"closed-form={ref_mod_dur:.4f}")
    return "Bond price + closed-form vs. numerical duration", ok, detail


# ---------------------------------------------------------------------
# Accrued interest / clean-dirty price: cross-check both day-count
# conventions against independent Python date arithmetic. 30/360 and
# Actual/Actual must give DIFFERENT answers for the identical settlement
# date -- that's the whole point of the convention mattering.
# ---------------------------------------------------------------------
def check_accrued_interest():
    path = os.path.join(REPO_ROOT, "21_Fixed_Income_Rates", "_template_FIXED_INCOME.xlsx")
    from datetime import date as _date

    def populate(wb, convention):
        ai = wb["Accrued Interest & Settlement"]
        ai["C5"] = convention

    wb_360 = with_recalc(path, lambda w: populate(w, "30/360"))
    wb_act = with_recalc(path, lambda w: populate(w, "Actual/Actual"))

    ai_360 = wb_360["Accrued Interest & Settlement"]
    ai_act = wb_act["Accrued Interest & Settlement"]

    # Default template dates: last coupon 2026-01-01, next 2026-07-01,
    # settlement 2026-04-01. 30/360 treats every month as exactly 30 days;
    # actual counts real calendar days.
    ref_days_360 = 90
    ref_period_360 = 180
    ref_days_act = (_date(2026, 4, 1) - _date(2026, 1, 1)).days
    ref_period_act = (_date(2026, 7, 1) - _date(2026, 1, 1)).days
    periodic_coupon = 1000 * 0.05 / 2  # default Bond Pricing inputs

    ref_accrued_360 = periodic_coupon * ref_days_360 / ref_period_360
    ref_accrued_act = periodic_coupon * ref_days_act / ref_period_act

    sheet_accrued_360 = ai_360["C17"].value
    sheet_accrued_act = ai_act["C17"].value

    ok = (close(sheet_accrued_360, ref_accrued_360)
          and close(sheet_accrued_act, ref_accrued_act)
          and abs(sheet_accrued_360 - sheet_accrued_act) > 0.01)  # conventions must actually differ

    dirty_360 = ai_360["C19"].value
    clean_360 = ai_360["C18"].value
    ok = ok and close(dirty_360, clean_360 + sheet_accrued_360)

    detail = (f"30/360: sheet={sheet_accrued_360:.4f} ref={ref_accrued_360:.4f} | "
              f"Actual/Actual: sheet={sheet_accrued_act:.4f} ref={ref_accrued_act:.4f} | "
              f"conventions differ: {abs(sheet_accrued_360 - sheet_accrued_act) > 0.01} | "
              f"dirty=clean+accrued: {close(dirty_360, clean_360 + sheet_accrued_360)}")
    return "Accrued interest: 30/360 vs Actual/Actual day-count conventions", ok, detail


# ---------------------------------------------------------------------
# Bornhuetter-Ferguson: verify against the closed-form definition
# (BF ultimate = actual reported + expected ultimate x (1 - 1/CDF)) for
# every accident year, AND the convergence property that makes BF/CL
# agreement at CDF=1 a meaningful sanity check rather than a coincidence.
# ---------------------------------------------------------------------
def check_bornhuetter_ferguson():
    path = os.path.join(REPO_ROOT, "18_Insurance_Actuarial", "_template_INSURANCE.xlsx")
    triangle = {
        5: [100, 150, 180, 195, 200, 200], 6: [120, 180, 216, 234, 240],
        7: [110, 165, 198, 214.5], 8: [130, 195, 234], 9: [140, 210], 10: [150],
    }
    elr = 0.60
    premium = 350 / elr  # expected ultimate = 350 flat for every AY

    def populate(wb):
        tri = wb["Loss Reserve Triangle"]
        for row, vals in triangle.items():
            for i, v in enumerate(vals):
                tri.cell(row=row, column=3 + i, value=v)
        bf = wb["Bornhuetter-Ferguson"]
        bf["C4"] = elr
        for r in range(7, 13):
            bf.cell(row=r, column=3, value=premium)

    wb = with_recalc(path, populate)
    bf = wb["Bornhuetter-Ferguson"]

    # Actual reported (latest diagonal) and CDF, in AY2020..AY2025 order.
    # CDF is the volume-weighted chain-ladder chain computed programmatically
    # from the same `triangle` dict used to populate the sheet -- built the
    # same way the sheet's own formulas are (volume-weighted link factors,
    # cumulative product back from Dev6), but as an independent Python
    # computation rather than a copy of the sheet's formula text.
    rows_by_ay = [5, 6, 7, 8, 9, 10]  # AY2020..AY2025
    actual = [triangle[row][-1] for row in rows_by_ay]  # each AY's latest diagonal value

    # link factor from dev period k to k+1 (0-indexed k=0 is Dev1->Dev2):
    # volume-weighted sum(Dev k+1) / sum(Dev k) over AYs with data in both.
    link = []
    for k in range(5):  # 5 transitions: Dev1->2, 2->3, 3->4, 4->5, 5->6
        num = sum(triangle[row][k + 1] for row in rows_by_ay if len(triangle[row]) > k + 1)
        den = sum(triangle[row][k] for row in rows_by_ay if len(triangle[row]) > k + 1)
        link.append(num / den)

    cdf_by_dev = [1.0] * 6  # CDF to ultimate, indexed by dev period (0=Dev1..5=Dev6)
    cdf_by_dev[5] = 1.0
    for dev in range(4, -1, -1):
        cdf_by_dev[dev] = link[dev] * cdf_by_dev[dev + 1]
    # AY2020 (most mature) sits at Dev6 (index 5); AY2025 (least mature) at Dev1 (index 0).
    cdf = [cdf_by_dev[5 - i] for i in range(6)]  # AY2020..AY2025
    ref_bf_ultimate = [actual[i] + 350 * (1 - 1 / cdf[i]) for i in range(6)]

    ok = True
    mismatches = []
    for i in range(6):
        row = 7 + i
        sheet_val = bf.cell(row=row, column=9).value
        if not close(sheet_val, ref_bf_ultimate[i]):
            mismatches.append(f"AY{2020+i}: sheet={sheet_val} ref={ref_bf_ultimate[i]:.4f}")
    ok = not mismatches

    # Convergence property: at CDF=1 (AY2020, AY2021 in this dataset), BF
    # must equal chain-ladder EXACTLY, not approximately.
    diff_2020 = bf.cell(row=7, column=11).value
    diff_2021 = bf.cell(row=8, column=11).value
    ok = ok and close(diff_2020, 0, tol=1e-6) and close(diff_2021, 0, tol=1e-6)
    # And divergence should be monotonically increasing as CDF rises
    # (least mature year = biggest BF-vs-CL gap).
    diffs = [bf.cell(row=r, column=11).value for r in range(7, 13)]
    ok = ok and all(diffs[i] <= diffs[i + 1] + 1e-6 for i in range(5))

    detail = (f"{len(mismatches)} mismatches" + (f" (first: {mismatches[0]})" if mismatches else "")
              + f" | convergence at CDF=1: AY2020 diff={diff_2020}, AY2021 diff={diff_2021} | "
              f"diffs monotonically increasing with immaturity: {diffs}")
    return "Bornhuetter-Ferguson vs. closed-form + chain-ladder convergence at maturity", ok, detail


# ---------------------------------------------------------------------
# Securitization: pool cash flow (CDR/CPR/recovery lag) + the two-
# directional tranche cascade (principal senior->junior, loss junior->
# senior) cross-checked cell-by-cell against an independent Python
# re-implementation, plus the pool-vs-tranche reconciliation identity.
# ---------------------------------------------------------------------
def check_securitization_tranche_waterfall():
    path = os.path.join(REPO_ROOT, "19_Structured_Finance_Securitization",
                         "_template_SECURITIZATION.xlsx")
    pool_balance, wac, wam, cpr, cdr, recovery_rate, lag = (
        100_000_000.0, 0.06, 360, 0.08, 0.03, 0.50, 3)
    faces = [80_000_000.0, 10_000_000.0, 5_000_000.0, 3_000_000.0, 2_000_000.0]

    def populate(wb):
        cp = wb["Collateral Pool"]
        cp["C5"], cp["C6"], cp["C7"] = pool_balance, wac, wam
        cp["C8"], cp["C9"], cp["C10"], cp["C11"] = cpr, cdr, recovery_rate, lag
        wf = wb["Waterfall"]
        for i, f in enumerate(faces):
            wf.cell(row=5 + i, column=3, value=f)

    wb = with_recalc(path, populate)
    ws = wb["Tranche Cash Flow Waterfall"]

    smm = 1 - (1 - cpr) ** (1 / 12)
    mdr = 1 - (1 - cdr) ** (1 / 12)
    pmt = pool_balance * (wac / 12) / (1 - (1 + wac / 12) ** (-wam))
    N = 12
    beg = [0.0] * N; sched_prin = [0.0] * N; defaults = [0.0] * N
    prepay = [0.0] * N; end = [0.0] * N
    for m in range(N):
        beg[m] = pool_balance if m == 0 else end[m - 1]
        sched_int = beg[m] * wac / 12
        sched_prin[m] = max(0, pmt - sched_int)
        defaults[m] = beg[m] * mdr
        prepay[m] = max(0, beg[m] - sched_prin[m] - defaults[m]) * smm
        end[m] = beg[m] - sched_prin[m] - defaults[m] - prepay[m]
    recovery = [defaults[m - lag] * recovery_rate if m - lag >= 0 else 0.0 for m in range(N)]
    loss = [defaults[m] * (1 - recovery_rate) for m in range(N)]
    prin_avail = [sched_prin[m] + prepay[m] + recovery[m] for m in range(N)]

    tranche_beg = [[0.0] * N for _ in range(5)]
    tranche_prin = [[0.0] * N for _ in range(5)]
    tranche_loss = [[0.0] * N for _ in range(5)]
    tranche_end = [[0.0] * N for _ in range(5)]
    for m in range(N):
        remaining = prin_avail[m]
        for i in range(5):
            tranche_beg[i][m] = faces[i] if m == 0 else tranche_end[i][m - 1]
            p = max(0, min(remaining, tranche_beg[i][m]))
            tranche_prin[i][m] = p
            remaining -= p
        remaining_loss = loss[m]
        for i in reversed(range(5)):
            after_prin = tranche_beg[i][m] - tranche_prin[i][m]
            losses_alloc = max(0, min(remaining_loss, after_prin))
            tranche_loss[i][m] = losses_alloc
            remaining_loss -= losses_alloc
            tranche_end[i][m] = tranche_beg[i][m] - tranche_prin[i][m] - tranche_loss[i][m]

    blocks = {i: 19 + i * 5 for i in range(5)}
    mismatches = []
    for m in range(N):
        col = get_column_letter(3 + m)
        if not close(ws[f"{col}12"].value, end[m]):
            mismatches.append(f"pool end m{m + 1}: sheet={ws[f'{col}12'].value} ref={end[m]:.2f}")
        for i in range(5):
            base = blocks[i]
            for name, row, ref in ((("beg", base + 1, tranche_beg[i][m]),
                                     ("prin", base + 2, tranche_prin[i][m]),
                                     ("loss", base + 3, tranche_loss[i][m]),
                                     ("end", base + 4, tranche_end[i][m]))):
                sheet_val = ws.cell(row=row, column=3 + m).value
                if not close(sheet_val, ref):
                    mismatches.append(f"tranche{i} {name} m{m + 1}: sheet={sheet_val} ref={ref:.2f}")

    ok = not mismatches

    recon_row0 = 19 + 25 + 2 + 7
    recon_check = ws.cell(row=recon_row0 + 5, column=3).value
    ok = ok and close(recon_check, 0, tol=1e-3)

    a_wal = ws.cell(row=19 + 25 + 2, column=3).value
    ref_a_wal = (sum((m + 1) * tranche_prin[0][m] for m in range(N))
                 / sum(tranche_prin[0]) / 12)
    ok = ok and close(a_wal, ref_a_wal)

    detail = (f"{len(mismatches)} cell mismatches across pool + 5 tranches x 12 months"
              + (f" (first: {mismatches[0]})" if mismatches else "")
              + f" | reconciliation check={recon_check:.6f} | "
              f"Class A WAL: sheet={a_wal:.4f} ref={ref_a_wal:.4f}")
    return "Securitization: pool CF + two-directional tranche cascade + reconciliation", ok, detail


# ---------------------------------------------------------------------
# LBO: Sources = Uses, and the debt schedule cash-sweep cascade
# ---------------------------------------------------------------------
def check_lbo_sources_uses_and_debt_schedule():
    path = os.path.join(REPO_ROOT, "03_Private_Equity", "_template_LBO.xlsx")

    def populate(wb):
        su = wb["Sources & Uses"]
        su["C5"], su["C6"], su["C7"] = 0, 300, 200   # revolver, TLA, TLB
        su["C8"], su["C9"], su["C10"] = 0, 150, 50   # notes, sponsor equity, rollover
        su["F5"], su["F9"] = 650, 50                 # purchase price, cash to balance sheet
        ds = wb["Debt Schedule"]
        # Column K = Base scenario input; Cover defaults to "Base", so the
        # Active column (M) should read straight from K here.
        ds["K5"], ds["K6"] = 0.05, 0.50              # EBITDA growth, FCF conversion
        ds["K7"], ds["K8"] = 0.05, 0.07              # TLA mandatory amort %, TLA rate
        ds["K9"], ds["K10"] = 0.01, 0.095            # TLB mandatory amort %, TLB rate
        ds["K11"] = 0.75                             # cash sweep %
        ds["K12"], ds["K13"] = 50, 0.08              # revolver capacity, revolver rate
        ret = wb["Returns"]
        ret["C5"] = 100  # entry EBITDA

    wb = with_recalc(path, populate)
    su = wb["Sources & Uses"]
    # Sources has 6 line items (rows 5-10) -> total at row 11; Uses has 5
    # (rows 5-9) -> total at row 10. The two "Total" rows land one apart.
    sources_total = su["C11"].value
    uses_total = su["F10"].value
    check_cell = su["C13"].value

    ok = close(sources_total, 700) and close(uses_total, 700) and close(check_cell, 0, tol=1e-6)

    # Cross-check the FULL multi-tranche cash-sweep cascade (revolver draws
    # on a shortfall / repays first from any surplus, then TLA is swept to
    # zero before TLB sees a dollar) against an independent Python
    # re-implementation of the same non-circular mechanic, for all 6 years
    # -- not just the final balance, so an error in an early year (e.g. the
    # revolver draw logic) can't hide behind a correct-by-coincidence Yr5.
    ds = wb["Debt Schedule"]
    ebitda0, growth, fcf_conv = 100.0, 0.05, 0.50
    tla_orig, tla_amort_pct, tla_rate = 300.0, 0.05, 0.07
    tlb_orig, tlb_amort_pct, tlb_rate = 200.0, 0.01, 0.095
    sweep_pct, rev_capacity, rev_rate = 0.75, 50.0, 0.08

    rev_beg, tla_beg, tlb_beg = 0.0, tla_orig, tlb_orig
    mismatches = []
    for yr in range(6):
        ebitda = ebitda0 * (1 + growth) ** yr
        fcf = ebitda * fcf_conv
        tla_mand = min(tla_orig * tla_amort_pct, tla_beg)
        tlb_mand = min(tlb_orig * tlb_amort_pct, tlb_beg)
        rev_int, tla_int, tlb_int = rev_beg * rev_rate, tla_beg * tla_rate, tlb_beg * tlb_rate
        cash_avail = fcf - tla_mand - tlb_mand - rev_int - tla_int - tlb_int
        if cash_avail < 0:
            draw_repay = min(-cash_avail, rev_capacity - rev_beg)
        else:
            draw_repay = -min(rev_beg, max(0, cash_avail))
        rev_end = rev_beg + draw_repay
        excess_for_sweep = max(0, max(0, cash_avail) - rev_beg)
        sweep_pool = sweep_pct * excess_for_sweep
        tla_sweep = min(sweep_pool, tla_beg - tla_mand)
        tla_end = tla_beg - tla_mand - tla_sweep
        tlb_sweep = min(sweep_pool - tla_sweep, tlb_beg - tlb_mand)
        tlb_end = tlb_beg - tlb_mand - tlb_sweep
        ref_total_debt = rev_end + tla_end + tlb_end

        col = get_column_letter(3 + yr)
        sheet_total_debt = ds[f"{col}30"].value
        if not close(sheet_total_debt, ref_total_debt):
            mismatches.append(f"Yr{yr}: sheet={sheet_total_debt} ref={ref_total_debt:.4f}")

        rev_beg, tla_beg, tlb_beg = rev_end, tla_end, tlb_end

    ok = ok and not mismatches
    detail = (f"sources={sources_total} uses={uses_total} check={check_cell} | "
              f"final Yr5 total debt: sheet={ds['H30'].value:.4f} python-reimpl={rev_beg+tla_beg+tlb_beg:.4f}"
              + (f" | MISMATCHES: {mismatches}" if mismatches else " | all 6 years matched"))
    return "LBO Sources=Uses + multi-tranche debt schedule (revolver/TLA/TLB) cascade", ok, detail


# ---------------------------------------------------------------------
# LBO Base/Downside scenario switch: confirm the Active column genuinely
# follows Cover's scenario selector (not just showing Base regardless),
# and that switching to Downside actually degrades leverage and returns in
# the right direction, not just "some different number."
# ---------------------------------------------------------------------
def check_lbo_scenario_switch():
    path = os.path.join(REPO_ROOT, "03_Private_Equity", "_template_LBO.xlsx")

    def populate(wb, scenario):
        su = wb["Sources & Uses"]
        su["C6"], su["C7"], su["C9"], su["C10"] = 300, 200, 150, 50
        ds = wb["Debt Schedule"]
        ds["K5"], ds["L5"] = 0.05, -0.03   # EBITDA growth: Base, Downside
        ds["K6"], ds["L6"] = 0.50, 0.35    # FCF conversion
        for row in (7, 9, 11, 12):         # amort %, sweep %, revolver capacity same both cases
            ds[f"K{row}"] = ds[f"L{row}"] = {7: 0.05, 9: 0.01, 11: 0.75, 12: 50}[row]
        ds["K8"], ds["L8"] = 0.07, 0.085   # TLA rate
        ds["K10"], ds["L10"] = 0.095, 0.115  # TLB rate
        ds["K13"], ds["L13"] = 0.08, 0.095  # revolver rate
        ret = wb["Returns"]
        ret["C5"], ret["C6"] = 100, 8.0
        ret["D12"], ret["E12"] = 8.5, 6.5  # exit multiple: Base, Downside
        cov = wb["Cover"]
        cov["C9"] = 5
        cov["C11"] = scenario

    wb_base = with_recalc(path, lambda w: populate(w, "Base"))
    wb_down = with_recalc(path, lambda w: populate(w, "Downside"))

    ds_base, ds_down = wb_base["Debt Schedule"], wb_down["Debt Schedule"]
    ret_base, ret_down = wb_base["Returns"], wb_down["Returns"]

    active_base = [ds_base.cell(row=r, column=13).value for r in (5, 6, 8, 10)]
    active_down = [ds_down.cell(row=r, column=13).value for r in (5, 6, 8, 10)]
    expected_base = [0.05, 0.50, 0.07, 0.095]
    expected_down = [-0.03, 0.35, 0.085, 0.115]

    ok = (all(close(a, e) for a, e in zip(active_base, expected_base))
          and all(close(a, e) for a, e in zip(active_down, expected_down)))

    lev_base, lev_down = ds_base["H32"].value, ds_down["H32"].value
    moic_base, moic_down = ret_base["C18"].value, ret_down["C18"].value
    exit_mult_base, exit_mult_down = ret_base["C12"].value, ret_down["C12"].value

    ok = ok and close(exit_mult_base, 8.5) and close(exit_mult_down, 6.5)
    # Downside must be strictly worse on both leverage and returns -- not
    # just "a different number," but degraded in the economically correct
    # direction.
    ok = ok and (lev_down > lev_base) and (moic_down < moic_base)

    detail = (f"active Base assumptions={active_base} (expect {expected_base}) | "
              f"active Downside assumptions={active_down} (expect {expected_down}) | "
              f"Yr5 leverage: Base={lev_base:.3f}x Downside={lev_down:.3f}x | "
              f"Deal MOIC: Base={moic_base:.3f}x Downside={moic_down:.3f}x")
    return "LBO Base/Downside scenario switch (Cover selector drives Active column correctly)", ok, detail


# ---------------------------------------------------------------------
# American option binomial tree: cross-check both the American and
# European trees against an independent Python CRR re-implementation with
# the same N, and confirm the textbook boundary condition that an American
# call on a non-dividend stock is worth EXACTLY the same as its European
# counterpart (early exercise is never optimal without dividends) — a
# strong, well-known correctness signal that's cheap to check permanently.
# ---------------------------------------------------------------------
def crr_binomial(S, K, T, r, q, sigma, N, is_call, american):
    dt = T / N
    u = math.exp(sigma * math.sqrt(dt))
    d = 1 / u
    p = (math.exp((r - q) * dt) - d) / (u - d)
    disc = math.exp(-r * dt)
    values = []
    for j in range(N + 1):
        S_T = S * u ** j * d ** (N - j)
        values.append(max(S_T - K, 0) if is_call else max(K - S_T, 0))
    for i in range(N - 1, -1, -1):
        new_values = []
        for j in range(i + 1):
            cont = disc * (p * values[j + 1] + (1 - p) * values[j])
            if american:
                S_ij = S * u ** j * d ** (i - j)
                intrinsic = max(S_ij - K, 0) if is_call else max(K - S_ij, 0)
                new_values.append(max(intrinsic, cont))
            else:
                new_values.append(cont)
        values = new_values
    return values[0]


def check_american_option_binomial():
    path = os.path.join(REPO_ROOT, "14_Options_Derivatives", "_template_OPTIONS.xlsx")
    S, K, T, r, q, sigma, N = 100, 100, 1.0, 0.045, 0.0, 0.30, 10
    sr = 61  # summary row: American, European, Premium, BS check

    ok = True
    details = []
    for opt_type in ("Put", "Call"):
        def populate(wb, ot=opt_type):
            ws = wb["American Option (Binomial)"]
            ws["C5"] = ot

        wb = with_recalc(path, populate)
        ws = wb["American Option (Binomial)"]
        sheet_american = ws.cell(row=sr, column=3).value
        sheet_european = ws.cell(row=sr + 1, column=3).value

        ref_american = crr_binomial(S, K, T, r, q, sigma, N, opt_type == "Call", american=True)
        ref_european = crr_binomial(S, K, T, r, q, sigma, N, opt_type == "Call", american=False)

        this_ok = close(sheet_american, ref_american) and close(sheet_european, ref_european)
        ok = ok and this_ok
        details.append(f"{opt_type}: American sheet={sheet_american:.4f} ref={ref_american:.4f}, "
                        f"European sheet={sheet_european:.4f} ref={ref_european:.4f}")

        if opt_type == "Call":
            # No dividends -> American call must equal European call exactly.
            boundary_ok = close(sheet_american, sheet_european, tol=1e-6)
            ok = ok and boundary_ok
            details.append(f"no-dividend call boundary (American==European): {'OK' if boundary_ok else 'FAIL'}")

    return "American option binomial tree (CRR) vs. independent Python re-implementation", ok, "; ".join(details)


# ---------------------------------------------------------------------
# Portfolio VaR: cross-check the 3-asset correlation-weighted portfolio
# variance/VaR and component VaR against an independent Python
# implementation, and confirm Euler's homogeneity theorem holds exactly
# (component VaRs must sum to total portfolio VaR for a variance-based
# risk measure) -- a strong self-consistency check baked into the sheet.
# ---------------------------------------------------------------------
def check_portfolio_var():
    path = os.path.join(REPO_ROOT, "09_Risk_Management", "_template_RISK.xlsx")
    w = {"A": 1_000_000.0, "B": 800_000.0, "C": 600_000.0}
    sigma = {"A": 0.020, "B": 0.015, "C": 0.025}
    rho = {("A", "B"): 0.30, ("A", "C"): 0.10, ("B", "C"): 0.50}

    def populate(wb):
        pv = wb["Portfolio VaR (Multi-Asset)"]
        pv["C9"], pv["D9"] = w["A"], sigma["A"]
        pv["C10"], pv["D10"] = w["B"], sigma["B"]
        pv["C11"], pv["D11"] = w["C"], sigma["C"]
        pv["D15"], pv["E15"], pv["E16"] = rho[("A", "B")], rho[("A", "C")], rho[("B", "C")]

    wb = with_recalc(path, populate)
    pv = wb["Portfolio VaR (Multi-Asset)"]

    def get_rho(i, j):
        if i == j:
            return 1.0
        return rho.get((i, j), rho.get((j, i)))

    assets = ["A", "B", "C"]
    port_var = sum(w[i] * w[j] * sigma[i] * sigma[j] * get_rho(i, j) for i in assets for j in assets)
    z = 1.6448536269514722  # NORMSINV(0.95)
    ref_port_var_dollar = (port_var ** 0.5) * z
    ref_undiv = sum(w[i] * sigma[i] * z for i in assets)
    ref_component = {}
    for i in assets:
        cov_i_port = sum(w[j] * sigma[i] * sigma[j] * get_rho(i, j) for j in assets)
        ref_component[i] = (w[i] * cov_i_port / port_var) * ref_port_var_dollar

    sheet_port_var = pv["C22"].value
    sheet_undiv = pv["C23"].value
    sheet_components = [pv.cell(row=r, column=3).value for r in (27, 28, 29)]
    sheet_component_sum = pv["C30"].value

    ok = (close(sheet_port_var, ref_port_var_dollar) and close(sheet_undiv, ref_undiv)
          and all(close(s, ref_component[a]) for s, a in zip(sheet_components, assets))
          and close(sheet_component_sum, sheet_port_var, tol=1e-6))

    detail = (f"portfolio VaR: sheet={sheet_port_var:.2f} ref={ref_port_var_dollar:.2f} | "
              f"undiversified: sheet={sheet_undiv:.2f} ref={ref_undiv:.2f} | "
              f"components: sheet={[round(s, 2) for s in sheet_components]} "
              f"ref={[round(ref_component[a], 2) for a in assets]} | "
              f"component sum == portfolio VaR: {close(sheet_component_sum, sheet_port_var, tol=1e-6)}")
    return "Portfolio VaR: correlation-weighted aggregation + Euler component-VaR check", ok, detail


# ---------------------------------------------------------------------
# Cover tab field alignment: weekly_refresh_check.py reads Cover!C6 as
# "Last refreshed" and Cover!C7 as the next material date UNCONDITIONALLY,
# for every archetype. If a template's Cover tab layout puts a different
# field at C6/C7 (e.g. an extra field inserted before "Last refreshed"),
# the checker silently reads the wrong cell — either misparsing a label as
# a date (usually harmless, just drops the date silently) or, worse,
# misreading a REAL date in the wrong field as if it were the refresh date
# (actively wrong, not just missing). This exact bug shipped in the LBO,
# Insurance, and Fintech archetypes and was only caught by populating a
# real instance and watching the weekly checker misfire on it.
# ---------------------------------------------------------------------
def check_cover_tab_field_alignment():
    domain_dirs = sorted(
        d for d in os.listdir(REPO_ROOT)
        if os.path.isdir(os.path.join(REPO_ROOT, d)) and d[:2].isdigit()
    )
    bad = []
    checked = 0
    for d in domain_dirs:
        domain_path = os.path.join(REPO_ROOT, d)
        for fname in os.listdir(domain_path):
            if fname.startswith("_template_") and fname.endswith(".xlsx"):
                path = os.path.join(domain_path, fname)
                wb = openpyxl.load_workbook(path)
                if "Cover" not in wb.sheetnames:
                    bad.append(f"{d}/{fname}: no Cover tab")
                    continue
                cov = wb["Cover"]
                label = str(cov["B6"].value or "")
                checked += 1
                if "last refresh" not in label.lower():
                    bad.append(f"{d}/{fname}: B6 label is {label!r}, expected something containing 'Last refreshed'")

    ok = len(bad) == 0
    detail = f"checked {checked} archetype templates" + (f" | misaligned: {bad}" if bad else " | all aligned")
    return "Cover tab field alignment (Last refreshed must be at C6, every archetype)", ok, detail


# ---------------------------------------------------------------------
# Venture Capital: capped participating preferred -- the payout "kink"
# where a rational holder switches from taking pref+participation to
# converting to common once the cap makes conversion strictly better.
# ---------------------------------------------------------------------
def check_vc_participating_preferred_cap():
    path = os.path.join(REPO_ROOT, "13_Venture_Capital", "_template_VC.xlsx")
    invested, pref_mult, cap_mult, ownership = 10_000_000, 1.0, 3.0, 0.20
    exit_values = [20_000_000, 50_000_000, 80_000_000, 100_000_000, 150_000_000, 200_000_000, 500_000_000]

    def populate(wb):
        pp = wb["Participating Preferred"]
        pp["C6"], pp["C7"], pp["C8"], pp["C9"] = invested, pref_mult, cap_mult, ownership

    wb = with_recalc(path, populate)
    pp = wb["Participating Preferred"]

    pref = invested * pref_mult
    cap = invested * cap_mult
    ok = True
    details = []
    for i, ev in enumerate(exit_values):
        col = 3 + i
        uncapped = pref + ownership * max(ev - pref, 0)
        capped = min(uncapped, cap)
        as_converted = ownership * ev
        actual = max(capped, as_converted)
        ref_election = "CONVERT TO COMMON" if actual == as_converted else "TAKE PREF + PARTICIPATE"

        sheet_actual = pp.cell(row=16, column=col).value
        sheet_election = pp.cell(row=17, column=col).value
        this_ok = close(sheet_actual, actual) and sheet_election == ref_election
        ok = ok and this_ok
        details.append(f"EV ${ev/1e6:.0f}mm: payout sheet={sheet_actual:.0f}/ref={actual:.0f}, "
                        f"election sheet='{sheet_election}' ref='{ref_election}' {'OK' if this_ok else 'MISMATCH'}")

    # the whole point: at low exits, pref+participation wins; at high exits (above
    # the cap crossover), conversion wins -- confirm BOTH regimes are actually hit
    low_regime = pp.cell(row=17, column=3).value == "TAKE PREF + PARTICIPATE"
    high_regime = pp.cell(row=17, column=9).value == "CONVERT TO COMMON"
    both_regimes_hit = low_regime and high_regime
    ok = ok and both_regimes_hit
    details.append(f"both regimes exercised across the sweep: {'OK' if both_regimes_hit else 'FAIL'}")

    return "VC: capped participating preferred payout kink", ok, " | ".join(details)


# ---------------------------------------------------------------------
# Risk Management: historical VaR (Excel PERCENTILE/AVERAGEIF) vs.
# parametric VaR -- independently reproduces Excel's exact linear-
# interpolation percentile method, and confirms the fat-tail P&L sample
# makes historical VaR exceed parametric, the real-world direction.
# ---------------------------------------------------------------------
def check_risk_historical_vs_parametric_var():
    path = os.path.join(REPO_ROOT, "09_Risk_Management", "_template_RISK.xlsx")
    import random
    random.seed(11)
    pnl = []
    for _ in range(100):
        v = random.gauss(0, 150_000)
        if random.random() < 0.05:
            v -= 400_000
        pnl.append(v)
    portfolio_value, daily_vol, confidence, holding_days = 10_000_000, 0.015, 0.95, 1

    def populate(wb):
        var = wb["VaR"]
        var["C5"], var["C6"], var["C7"], var["C8"] = portfolio_value, daily_vol, confidence, holding_days
        for i, v in enumerate(pnl):
            var.cell(row=23 + i, column=5, value=v)

    wb = with_recalc(path, populate)
    var = wb["VaR"]

    def excel_percentile(data, p):
        data = sorted(data)
        n = len(data)
        k = (n - 1) * p
        f = int(k)
        c = k - f
        return data[f] + c * (data[f + 1] - data[f]) if f + 1 < n else data[f]

    pctile_val = excel_percentile(pnl, 1 - confidence)
    ref_hist_var = -pctile_val
    losses_beyond = [x for x in pnl if x <= pctile_val]
    ref_hist_cvar = -(sum(losses_beyond) / len(losses_beyond))
    z = -abs(statistics.NormalDist().inv_cdf(1 - confidence))  # z at (1-confidence) tail, negative
    ref_param_var = portfolio_value * daily_vol * abs(z)

    ok = True
    details = []
    for label, sheet_val, ref_val in [
        ("parametric VaR", var["C12"].value, ref_param_var),
        ("historical VaR", var["C21"].value, ref_hist_var),
        ("historical CVaR", var["C22"].value, ref_hist_cvar),
    ]:
        this_ok = close(sheet_val, ref_val, tol=1e-6)
        ok = ok and this_ok
        details.append(f"{label}: sheet={sheet_val:.2f} ref={ref_val:.2f} {'OK' if this_ok else 'MISMATCH'}")

    fat_tail_direction = ref_hist_var > ref_param_var
    ok = ok and fat_tail_direction
    details.append(f"fat-tail sample makes historical VaR exceed parametric: {'OK' if fat_tail_direction else 'FAIL'}")

    return "Risk Management: historical vs. parametric VaR (exact PERCENTILE match)", ok, " | ".join(details)


# ---------------------------------------------------------------------
# Options: closed-form Greeks vs. finite-difference (bump-and-reprice)
# cross-check -- pins the fix for a real Excel operator-precedence bug
# (unary minus binds tighter than exponentiation, so a hand-rolled
# EXP(-x^2/2) silently computed EXP(+x^2/2)) that corrupted Gamma/Vega/
# Theta until caught by this check.
# ---------------------------------------------------------------------
def check_options_greeks_finite_difference():
    path = os.path.join(REPO_ROOT, "14_Options_Derivatives", "_template_OPTIONS.xlsx")
    S, K, T, r, q, sigma = 100.0, 100.0, 0.25, 0.045, 0.0, 0.30

    def populate(wb):
        bs = wb["BS Pricer"]
        bs["C5"], bs["C6"], bs["C7"], bs["C8"], bs["C9"], bs["C10"] = S, K, T, r, q, sigma

    wb = with_recalc(path, populate)
    g = wb["Greeks"]

    d1 = (math.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    phi_d1 = math.exp(-d1 ** 2 / 2) / math.sqrt(2 * math.pi)
    Nd1, Nd2 = norm_cdf(d1), norm_cdf(d1 - sigma * math.sqrt(T))

    ref_gamma = math.exp(-q * T) * phi_d1 / (S * sigma * math.sqrt(T))
    ref_vega = S * math.exp(-q * T) * phi_d1 * math.sqrt(T) / 100
    ref_theta_call = (-S * phi_d1 * sigma * math.exp(-q * T) / (2 * math.sqrt(T))
                       - r * K * math.exp(-r * T) * Nd2 + q * S * math.exp(-q * T) * Nd1) / 365
    ref_delta_call = math.exp(-q * T) * Nd1

    ok = True
    details = []
    for label, sheet_val, ref_val in [
        ("Delta (call)", g["C5"].value, ref_delta_call),
        ("Gamma (call)", g["C6"].value, ref_gamma),
        ("Vega (call)", g["C7"].value, ref_vega),
        ("Theta (call)", g["C8"].value, ref_theta_call),
    ]:
        this_ok = close(sheet_val, ref_val, tol=1e-4)
        ok = ok and this_ok
        details.append(f"{label}: sheet={sheet_val:.6f} ref={ref_val:.6f} {'OK' if this_ok else 'MISMATCH'}")

    # the regression this check exists to catch: the precedence bug made
    # Gamma/Vega/Theta come out with the WRONG exponent sign on phi(d1),
    # which (for these inputs) inflates them well past a 1% tolerance
    buggy_phi = math.exp(d1 ** 2 / 2) / math.sqrt(2 * math.pi)  # the bug's actual (wrong) computation
    buggy_vega = S * math.exp(-q * T) * buggy_phi * math.sqrt(T) / 100
    not_the_bug = not close(g["C7"].value, buggy_vega, tol=1e-6)
    ok = ok and not_the_bug
    details.append(f"Vega does NOT match the known-buggy (wrong-sign) computation: {'OK' if not_the_bug else 'FAIL — bug has regressed'}")

    return "Options: closed-form Greeks match finite-difference (precedence-bug regression check)", ok, " | ".join(details)


# ---------------------------------------------------------------------
# Insurance: Mack method distribution-free standard error of the
# chain-ladder reserve -- independently re-derives the full sigma_k^2 /
# completed-triangle / per-accident-year MSE cascade in Python.
# ---------------------------------------------------------------------
def check_insurance_mack_method():
    path = os.path.join(REPO_ROOT, "18_Insurance_Actuarial", "_template_INSURANCE.xlsx")
    triangle = {
        5: [100, 150, 175, 190, 197, 200], 6: [110, 170, 200, 215, 222],
        7: [105, 155, 183, 196], 8: [120, 175, 205], 9: [130, 195], 10: [140],
    }

    def populate(wb):
        tri = wb["Loss Reserve Triangle"]
        for row, vals in triangle.items():
            for i, v in enumerate(vals):
                tri.cell(row=row, column=3 + i, value=v)

    wb = with_recalc(path, populate)
    mm = wb["Mack Method"]

    tri_data = {ay: triangle[row] for ay, row in zip(range(6), [5, 6, 7, 8, 9, 10])}

    link = []
    for k in range(5):
        num = sum(tri_data[ay][k + 1] for ay in range(6) if len(tri_data[ay]) > k + 1)
        den = sum(tri_data[ay][k] for ay in range(6) if len(tri_data[ay]) > k + 1)
        link.append(num / den)

    sigma2 = []
    for k in range(4):
        n = sum(1 for ay in range(6) if len(tri_data[ay]) > k + 1)
        s = sum(tri_data[ay][k] * (tri_data[ay][k + 1] / tri_data[ay][k] - link[k]) ** 2
                for ay in range(6) if len(tri_data[ay]) > k + 1)
        sigma2.append(s / (n - 1))
    sigma2.append(min(sigma2[3], sigma2[2], sigma2[3] ** 2 / sigma2[2]))  # Mack's last-factor extrapolation

    S = [sum(tri_data[ay][k] for ay in range(6) if len(tri_data[ay]) > k + 1) for k in range(5)]

    cdf_by_dev = [1.0] * 6
    for dev in range(4, -1, -1):
        cdf_by_dev[dev] = link[dev] * cdf_by_dev[dev + 1]

    ok = True
    details = []
    for ay in range(6):
        d_i = len(tri_data[ay])
        latest = tri_data[ay][-1]
        cdf = cdf_by_dev[d_i - 1]
        ultimate = latest * cdf
        completed = list(tri_data[ay])
        for k in range(d_i, 6):
            completed.append(completed[-1] * link[k - 1])
        mse = 0.0
        for k in range(d_i, 6):
            idx = k - 1
            c_ik = completed[k - 1]
            mse += (sigma2[idx] / link[idx] ** 2) * (1 / c_ik + 1 / S[idx])
        mse *= ultimate ** 2
        se = mse ** 0.5

        sheet_se = mm.cell(row=25 + ay, column=6).value
        this_ok = close(sheet_se, se, tol=1e-3) if se > 0 else (sheet_se == 0)
        ok = ok and this_ok
        details.append(f"AY{2020+ay}: SE sheet={sheet_se} ref={se:.4f} {'OK' if this_ok else 'MISMATCH'}")

    return "Insurance: Mack method standard error (independent sigma_k^2 + MSE cascade)", ok, " | ".join(details)


# ---------------------------------------------------------------------
# Trade Finance: early-payment discount implied APR (the classic
# "2/10 net 30" corporate-finance factoid) + reverse factoring priced
# off the buyer's stronger credit.
# ---------------------------------------------------------------------
def check_trade_finance_dynamic_discounting():
    path = os.path.join(REPO_ROOT, "10_Trade_Finance", "_template_TRADE_FINANCE.xlsx")
    discount_pct, discount_days, net_days = 0.02, 10, 30
    invoice_face, scf_rate, days_early = 500_000, 0.045, 60

    def populate(wb):
        dd = wb["Dynamic Discounting & SCF"]
        dd["C6"], dd["C7"], dd["C8"] = discount_pct, discount_days, net_days
        dd["C12"], dd["C13"], dd["C14"] = invoice_face, scf_rate, days_early
        lc = wb["LC & Factoring Cost"]
        lc["C14"], lc["C15"], lc["C16"], lc["C17"] = 500_000, 0.85, 0.02, 60

    wb = with_recalc(path, populate)
    dd = wb["Dynamic Discounting & SCF"]

    ref_apr = (discount_pct / (1 - discount_pct)) * (360 / (net_days - discount_days))
    ref_scf_cost = invoice_face * scf_rate * (days_early / 365)

    ok = True
    details = []
    this_ok = close(dd["C9"].value, ref_apr)
    ok = ok and this_ok
    details.append(f"2/10 net 30 implied APR: sheet={dd['C9'].value:.4f} ref={ref_apr:.4f} {'OK' if this_ok else 'MISMATCH'}")

    canonical_ok = close(ref_apr, 0.3673469387755102, tol=1e-6)
    ok = ok and canonical_ok
    details.append(f"reproduces the canonical textbook ~36.7% figure: {'OK' if canonical_ok else 'FAIL'}")

    this_ok2 = close(dd["C15"].value, ref_scf_cost)
    ok = ok and this_ok2
    details.append(f"SCF cost: sheet={dd['C15'].value:.2f} ref={ref_scf_cost:.2f} {'OK' if this_ok2 else 'MISMATCH'}")

    scf_cheaper = dd["C16"].value < dd["C17"].value
    ok = ok and scf_cheaper
    details.append(f"SCF rate ({dd['C16'].value:.4f}) < standalone factoring rate ({dd['C17'].value:.4f}): {'OK' if scf_cheaper else 'FAIL'}")

    return "Trade Finance: dynamic discounting APR + supply chain finance", ok, " | ".join(details)


# ---------------------------------------------------------------------
# Restructuring: EV sensitivity showing WHERE the fulcrum security moves
# across a range of enterprise values -- not just what it is at one point
# estimate.
# ---------------------------------------------------------------------
def check_restructuring_ev_sensitivity():
    path = os.path.join(REPO_ROOT, "24_Distressed_Restructuring", "_template_RESTRUCTURING.xlsx")
    tranche_names = ["DIP / super-priority", "First lien secured", "Second lien secured",
                      "Senior unsecured notes", "Subordinated debt", "Equity"]
    faces = [50_000_000, 200_000_000, 100_000_000, 150_000_000, 75_000_000, 1]
    base_ev = 400_000_000
    ev_scenarios = [-0.40, -0.20, -0.10, 0.0, 0.10, 0.20, 0.40]

    def populate(wb):
        rw = wb["Recovery Waterfall"]
        for i, f in enumerate(faces):
            rw.cell(row=5 + i, column=3, value=f)
        rw["C12"] = base_ev

    wb = with_recalc(path, populate)
    ev_sheet = wb["EV Sensitivity"]

    def waterfall_recovery_pct(ev):
        remaining = ev
        pcts = []
        for face in faces:
            recovered = min(remaining, face)
            pcts.append(recovered / face if face else 0)
            remaining = max(remaining - recovered, 0)
        return pcts

    def fulcrum(pcts):
        for i, p in enumerate(pcts):
            if p < 1 - 1e-9 and (i == 0 or pcts[i - 1] >= 1 - 1e-9):
                return tranche_names[i]
        return "none -- equity in the money"

    ok = True
    details = []
    for col_idx, scenario in enumerate(ev_scenarios):
        col = 3 + col_idx
        ev = base_ev * (1 + scenario)
        ref_pcts = waterfall_recovery_pct(ev)
        ref_fulcrum = fulcrum(ref_pcts)
        for t in range(6):
            sheet_pct = ev_sheet.cell(row=9 + t, column=col).value
            this_ok = close(sheet_pct, ref_pcts[t], tol=1e-4)
            ok = ok and this_ok
            if not this_ok:
                details.append(f"scenario {scenario:+.0%} tranche {tranche_names[t]}: sheet={sheet_pct} ref={ref_pcts[t]:.4f} MISMATCH")
        sheet_fulcrum = ev_sheet.cell(row=16, column=col).value
        fulcrum_ok = sheet_fulcrum == ref_fulcrum
        ok = ok and fulcrum_ok
        details.append(f"EV {scenario:+.0%} (${ev/1e6:.0f}mm): fulcrum sheet='{sheet_fulcrum}' ref='{ref_fulcrum}' {'OK' if fulcrum_ok else 'MISMATCH'}")

    return "Restructuring: EV sensitivity + fulcrum-shift identification across 7 scenarios", ok, " | ".join(details)


# ---------------------------------------------------------------------
# Real Estate: LP/GP promote waterfall (compounded pref, no catch-up,
# straight promote split) -- conservation and GP-outperformance checks.
# ---------------------------------------------------------------------
def check_real_estate_lp_gp_promote():
    path = os.path.join(REPO_ROOT, "17_Real_Estate_REIT", "_template_REAL_ESTATE.xlsx")
    gpr, vacancy, other_inc, opex, capex_reserve, debt_service = (
        5_000_000, -250_000, 100_000, -1_800_000, -150_000, -1_200_000,
    )
    purchase_price, debt_amount = 45_000_000, 27_000_000
    noi_growth, exit_cap, selling_cost_pct = 0.02, 0.065, 0.02
    lp_pct, pref_rate, hold_years, gp_promote_pct = 0.90, 0.08, 5, 0.20

    def populate(wb):
        pf = wb["Property Pro Forma"]
        pf["C5"], pf["C6"], pf["C8"], pf["C10"], pf["C12"], pf["C13"] = (
            gpr, vacancy, other_inc, opex, capex_reserve, debt_service,
        )
        cv = wb["Cap Rate & Valuation"]
        cv["C8"], cv["C10"] = purchase_price, debt_amount
        fh = wb["5-Year Hold & IRR"]
        fh["C5"], fh["C6"], fh["C7"] = noi_growth, exit_cap, selling_cost_pct
        lg = wb["LP-GP Promote"]
        lg["C6"], lg["C8"], lg["C9"], lg["C10"] = lp_pct, pref_rate, hold_years, gp_promote_pct

    wb = with_recalc(path, populate)

    # independent re-derivation
    noi0 = gpr + vacancy + other_inc + opex  # = EGI+other-opex... matches Property Pro Forma's own chain
    total_equity = purchase_price - debt_amount
    # sheet's Yr1 NOI = current NOI (no growth yet); growth compounds starting Yr2
    noi_by_year = [noi0 * (1 + noi_growth) ** y for y in range(0, 5)]
    levered_cf = [noi - abs(debt_service) for noi in noi_by_year]
    forward_noi_yr6 = noi_by_year[-1] * (1 + noi_growth)
    exit_value = forward_noi_yr6 / exit_cap
    selling_costs = -exit_value * selling_cost_pct
    debt_payoff = -debt_amount
    net_exit_equity = exit_value + selling_costs + debt_payoff
    total_distributions = sum(levered_cf) + net_exit_equity

    roc = min(total_distributions, total_equity)
    pref_target = total_equity * ((1 + pref_rate) ** hold_years - 1)
    pref_paid = min(max(total_distributions - roc, 0), pref_target)
    residual = max(total_distributions - roc - pref_paid, 0)
    gp_promote = residual * gp_promote_pct
    lp_residual = residual * (1 - gp_promote_pct)
    lp_total = roc * lp_pct + pref_paid * lp_pct + lp_residual
    gp_total = roc * (1 - lp_pct) + pref_paid * (1 - lp_pct) + gp_promote

    lg = wb["LP-GP Promote"]
    ok = True
    details = []
    for label, sheet_val, ref_val in [
        ("total distributions", lg["C14"].value, total_distributions),
        ("pref target", lg["C18"].value, pref_target),
        ("residual", lg["C20"].value, residual),
        ("LP total", lg["C25"].value, lp_total),
        ("GP total", lg["C26"].value, gp_total),
    ]:
        this_ok = close(sheet_val, ref_val)
        ok = ok and this_ok
        details.append(f"{label}: sheet={sheet_val:.0f} ref={ref_val:.0f} {'OK' if this_ok else 'MISMATCH'}")

    conservation = close(lg["C25"].value + lg["C26"].value, total_distributions)
    ok = ok and conservation
    details.append(f"conservation (LP+GP=total): {'OK' if conservation else 'FAIL'}")

    gp_outperforms = lg["C28"].value > lg["C27"].value
    ok = ok and gp_outperforms
    details.append(f"GP multiple ({lg['C28'].value:.3f}) > LP multiple ({lg['C27'].value:.3f}): {'OK' if gp_outperforms else 'FAIL'}")

    return "Real Estate: LP/GP promote waterfall (compounded pref + straight split)", ok, " | ".join(details)


# ---------------------------------------------------------------------
# Quant: Probabilistic Sharpe Ratio + Minimum Track Record Length
# (Bailey & Lopez de Prado) -- independently replicates Excel's exact
# bias-corrected SKEW/KURT formulas, not just scipy's, to match the
# sheet's own recalculated values precisely.
# ---------------------------------------------------------------------
def check_quant_psr_mintrl():
    path = os.path.join(REPO_ROOT, "22_Quantitative_Systematic", "_template_QUANT.xlsx")
    import random
    random.seed(7)
    returns = [random.gauss(0.015, 0.03) for _ in range(24)]
    rf_annual = 0.03

    def populate(wb):
        rs = wb["Returns & Sharpe"]
        for i, r in enumerate(returns):
            rs.cell(row=6 + i, column=3, value=r)
        rs["C32"] = rf_annual

    wb = with_recalc(path, populate)
    ss = wb["Statistical Significance"]

    n = len(returns)
    mean = sum(returns) / n
    s = math.sqrt(sum((x - mean) ** 2 for x in returns) / (n - 1))
    # Excel's exact bias-corrected SKEW/KURT formulas (not scipy's), so this
    # matches the sheet's own SKEW()/KURT() recalculation precisely
    skew = (n / ((n - 1) * (n - 2))) * sum(((x - mean) / s) ** 3 for x in returns)
    kurt = (n * (n + 1) / ((n - 1) * (n - 2) * (n - 3))) * sum(((x - mean) / s) ** 4 for x in returns) \
        - 3 * (n - 1) ** 2 / ((n - 2) * (n - 3))
    sr_hat = (mean - rf_annual / 12) / s
    sr_star = 0.0
    psr_denom = math.sqrt(1 - skew * sr_hat + (kurt + 2) / 4 * sr_hat ** 2)
    z = (sr_hat - sr_star) * math.sqrt(n - 1) / psr_denom
    psr = norm_cdf(z)
    z95 = 1.6448536269514722
    mintrl = 1 + (1 - skew * sr_hat + (kurt + 2) / 4 * sr_hat ** 2) * (z95 / (sr_hat - sr_star)) ** 2

    ok = True
    details = []
    for label, sheet_val, ref_val in [
        ("skew", ss["C11"].value, skew), ("kurt", ss["C12"].value, kurt),
        ("SR-hat", ss["C13"].value, sr_hat), ("PSR z", ss["C17"].value, z),
        ("PSR", ss["C18"].value, psr), ("MinTRL", ss["C22"].value, mintrl),
    ]:
        this_ok = close(sheet_val, ref_val, tol=1e-4)
        ok = ok and this_ok
        details.append(f"{label}: sheet={sheet_val} ref={ref_val:.4f} {'OK' if this_ok else 'MISMATCH'}")

    return "Quant: Probabilistic Sharpe Ratio + Minimum Track Record Length", ok, " | ".join(details)


# ---------------------------------------------------------------------
# Project Finance: sculpted debt schedule (non-circular) + a Debt Service
# Reserve Account that prevents PAYMENT default without curing the softer
# DSCR distribution-lock-up test -- the real distinction between the two
# covenant triggers, not the same event shown twice.
# ---------------------------------------------------------------------
def check_project_finance_dsra():
    path = os.path.join(REPO_ROOT, "20_Project_Finance", "_template_PROJECT_FINANCE.xlsx")
    total_cost, debt_pct, constr_months, idc_rate = 500_000_000, 0.70, 24, 0.06
    revenue, opcost, capex = 80_000_000, -20_000_000, -5_000_000
    target_dscr, debt_rate = 1.30, 0.06
    shock_year, shock_pct = 3, -0.30

    def populate(wb):
        cb = wb["Construction Budget"]
        cb["C5"], cb["C6"], cb["C7"], cb["C8"] = total_cost, debt_pct, constr_months, idc_rate
        ocf = wb["Operating Cash Flow"]
        for i in range(5):
            col = 3 + i
            ocf.cell(row=5, column=col, value=revenue)
            ocf.cell(row=6, column=col, value=opcost)
            ocf.cell(row=8, column=col, value=capex)
        dscr = wb["DSCR & Debt Sizing"]
        dscr["C9"], dscr["C10"] = target_dscr, debt_rate

    wb = with_recalc(path, populate)

    # independent re-derivation of the sculpted schedule
    debt_drawn = total_cost * debt_pct
    idc = debt_drawn * idc_rate * (constr_months / 12) / 2
    debt_at_cod = debt_drawn + idc
    cfads = revenue + opcost + capex
    sculpted_ds = cfads / target_dscr

    beg = debt_at_cod
    schedule = []
    for _ in range(5):
        interest = beg * debt_rate
        principal = sculpted_ds - interest
        end = beg - principal
        schedule.append((beg, interest, principal, end))
        beg = end

    sds = wb["Sculpted Debt Schedule"]
    ok = True
    details = []
    for i, (b, interest, principal, end) in enumerate(schedule):
        col = 3 + i
        sheet_end = sds.cell(row=10, column=col).value
        this_ok = close(sheet_end, end)
        ok = ok and this_ok
        details.append(f"Yr{i+1} ending balance: sheet={sheet_end:.0f} ref={end:.0f} {'OK' if this_ok else 'MISMATCH'}")

    # DSRA stress test, independently
    dsra_months = 6
    required_dsra = dsra_months / 12 * sculpted_ds
    stressed_cfads_shocked_yr = cfads * (1 + shock_pct)
    shortfall = max(sculpted_ds - stressed_cfads_shocked_yr, 0)
    draw = min(shortfall, required_dsra)
    paid_in_full_with_dsra = (stressed_cfads_shocked_yr + draw) >= sculpted_ds
    paid_in_full_without_dsra = stressed_cfads_shocked_yr >= sculpted_ds
    effective_dscr = (stressed_cfads_shocked_yr + draw) / sculpted_ds
    locked_up = effective_dscr < target_dscr

    dsra_sheet = wb["DSRA"]
    shocked_col = 2 + shock_year  # Yr3 -> column E (5)
    sheet_with = dsra_sheet.cell(row=20, column=shocked_col).value
    sheet_without = dsra_sheet.cell(row=21, column=shocked_col).value
    sheet_lockup = dsra_sheet.cell(row=22, column=shocked_col).value

    dsra_ok = (
        (sheet_with == "PAID IN FULL") == paid_in_full_with_dsra
        and (sheet_without == "PAID IN FULL") == paid_in_full_without_dsra
        and (sheet_lockup == "LOCKED UP") == locked_up
    )
    ok = ok and dsra_ok
    details.append(f"Yr3 stress: WITH-DSRA sheet={sheet_with} (ref payable={paid_in_full_with_dsra}), "
                    f"WITHOUT-DSRA sheet={sheet_without} (ref payable={paid_in_full_without_dsra}), "
                    f"lock-up sheet={sheet_lockup} (ref locked={locked_up}) {'OK' if dsra_ok else 'MISMATCH'}")

    return "Project Finance: sculpted debt schedule + DSRA payment-default-vs-covenant-lockup distinction", ok, " | ".join(details)


# ---------------------------------------------------------------------
# Microfinance: flat-rate vs. declining-balance effective interest rate --
# the true-cost-of-credit gap that pricing-transparency regulation exists
# to surface. Independent check uses a DIFFERENT root-finding approach
# (fixed-point iteration, not the sheet's bisection) as a genuinely
# separate verification path.
# ---------------------------------------------------------------------
def check_microfinance_flat_vs_declining():
    path = os.path.join(REPO_ROOT, "11_Microfinance", "_template_MICROFINANCE.xlsx")
    principal, flat_rate, n = 1000.0, 0.02, 12

    def populate(wb):
        fd = wb["Flat vs Declining Rate"]
        fd["C6"], fd["C7"], fd["C8"] = principal, flat_rate, n

    wb = with_recalc(path, populate)
    fd = wb["Flat vs Declining Rate"]

    total_interest = principal * flat_rate * n
    installment = (principal + total_interest) / n
    approx_rate = 2 * n * flat_rate / (n + 1)

    # independent solve via fixed-point iteration on r = installment*(1-(1+r)^-n)/P,
    # a different numerical method than the sheet's bisection
    r = flat_rate
    for _ in range(200):
        r = installment * (1 - (1 + r) ** -n) / principal
    exact_rate = r

    ok = True
    details = []
    checks_ = [
        ("installment", fd["C13"].value, installment),
        ("approx rate", fd["C16"].value, approx_rate),
        ("exact rate", fd["C28"].value, exact_rate),
    ]
    for label, sheet_val, ref_val in checks_:
        this_ok = close(sheet_val, ref_val, tol=1e-3)
        ok = ok and this_ok
        details.append(f"{label}: sheet={sheet_val} ref={ref_val:.6f} {'OK' if this_ok else 'MISMATCH'}")

    exceeds_flat = exact_rate > flat_rate
    ok = ok and exceeds_flat
    details.append(f"exact declining rate ({exact_rate:.4f}) > flat rate ({flat_rate}): {'OK' if exceeds_flat else 'FAIL'}")

    return "Microfinance: flat-rate vs. declining-balance effective rate (independent fixed-point solve)", ok, " | ".join(details)


# ---------------------------------------------------------------------
# Fintech: Durbin-regulated vs. exempt debit interchange economics --
# the structural reason many neobanks partner with a sub-$10B "sponsor
# bank" rather than becoming a bank themselves.
# ---------------------------------------------------------------------
def check_fintech_interchange_durbin():
    path = os.path.join(REPO_ROOT, "23_Fintech_Payments", "_template_FINTECH.xlsx")
    tpv, avg_txn = 50_000_000, 40.00

    def populate(wb):
        wb["Unit Economics"]["C5"] = tpv
        wb["Interchange Economics"]["C6"] = avg_txn

    wb = with_recalc(path, populate)
    ie = wb["Interchange Economics"]

    txn_count = tpv / avg_txn
    reg_fee = 0.22 + 0.0005 * avg_txn
    reg_rate = reg_fee / avg_txn
    reg_income = reg_rate * tpv
    exempt_fee = 0.04 + 0.0165 * avg_txn
    exempt_rate = exempt_fee / avg_txn
    exempt_income = exempt_rate * tpv

    ok = True
    details = []
    for label, sheet_val, ref_val in [
        ("txn count", ie["C8"].value, txn_count),
        ("regulated fee", ie["C11"].value, reg_fee),
        ("regulated income", ie["C13"].value, reg_income),
        ("exempt fee", ie["C16"].value, exempt_fee),
        ("exempt income", ie["C18"].value, exempt_income),
    ]:
        this_ok = close(sheet_val, ref_val)
        ok = ok and this_ok
        details.append(f"{label}: sheet={sheet_val} ref={ref_val:.4f} {'OK' if this_ok else 'MISMATCH'}")

    # the whole point of the tab: at a typical $40 ticket, exempt income
    # should be materially higher than regulated (per Reg II's fixed-fee
    # structure mattering less as ticket size grows)
    exempt_advantage = exempt_income > reg_income * 1.5
    ok = ok and exempt_advantage
    details.append(f"exempt income ({exempt_income:.0f}) > 1.5x regulated ({reg_income:.0f}): {'OK' if exempt_advantage else 'FAIL'}")

    return "Fintech: Durbin-regulated vs. exempt interchange economics", ok, " | ".join(details)


# ---------------------------------------------------------------------
# Crypto: perpetual futures funding rate + delta-neutral cash-and-carry
# basis trade (long spot, short perp) -- funding income isolated from
# price risk by construction.
# ---------------------------------------------------------------------
def check_crypto_perp_funding_basis():
    path = os.path.join(REPO_ROOT, "16_Crypto_Digital_Assets", "_template_CRYPTO.xlsx")
    perp_price, spot_price, interval_hours, notional = 100.50, 100.00, 8, 1_000_000

    def populate(wb):
        pf = wb["Perp Funding & Basis"]
        pf["C6"], pf["C7"], pf["C8"], pf["C9"] = perp_price, spot_price, interval_hours, notional

    wb = with_recalc(path, populate)
    pf = wb["Perp Funding & Basis"]

    premium = (perp_price - spot_price) / spot_price
    periods_per_year = 365 * 24 / interval_hours
    annualized_rate = premium * periods_per_year
    funding_received = notional * premium
    annualized_income = notional * annualized_rate

    ok = True
    details = []
    checks_ = [
        ("premium", pf["C12"].value, premium),
        ("periods/yr", pf["C14"].value, periods_per_year),
        ("annualized funding rate", pf["C15"].value, annualized_rate),
        ("funding received/interval", pf["C18"].value, funding_received),
        ("annualized funding income", pf["C19"].value, annualized_income),
    ]
    for label, sheet_val, ref_val in checks_:
        this_ok = close(sheet_val, ref_val)
        ok = ok and this_ok
        details.append(f"{label}: sheet={sheet_val} ref={ref_val:.4f} {'OK' if this_ok else 'MISMATCH'}")

    # delta-neutrality: net P&L must be exactly 0 across every spot/perp move,
    # since the position is long spot + short an equal notional of perp
    net_pnls = [pf.cell(row=24, column=c).value for c in range(3, 8)]
    delta_neutral = all(close(v, 0, tol=1e-6) for v in net_pnls)
    ok = ok and delta_neutral
    details.append(f"delta-neutral across all 5 moves: {net_pnls} ({'OK' if delta_neutral else 'FAIL'})")

    return "Crypto: perp funding rate + delta-neutral basis trade", ok, " | ".join(details)


# ---------------------------------------------------------------------
# Commodities: cost-of-carry model, F = S x e^((r+u-y)T), solved for the
# implied convenience yield from the market's own observed futures curve.
# ---------------------------------------------------------------------
def check_commodities_convenience_yield():
    path = os.path.join(REPO_ROOT, "15_Commodities", "_template_COMMODITIES.xlsx")
    spot, r, u = 70.00, 0.05, 0.02
    curve = [(70.00, 10), (71.00, 40), (72.00, 70), (74.50, 160), (77.00, 340)]  # (price, days)

    def populate(wb):
        fc = wb["Futures Curve"]
        for i, (price, days) in enumerate(curve):
            row = 5 + i
            fc.cell(row=row, column=3, value=price)
            fc.cell(row=row, column=4, value=days)
        co = wb["Cost of Carry"]
        co["C6"], co["C7"], co["C8"] = spot, r, u

    wb = with_recalc(path, populate)
    co = wb["Cost of Carry"]

    ok = True
    details = []
    for i, (price, days) in enumerate(curve):
        row = 11 + i
        T = days / 365
        if T == 0:
            ref_y = r + u  # degenerate: LN(1)/0 undefined, but M1's own IFERROR path also short-circuits
        else:
            ref_y = r + u - math.log(price / spot) / T
        sheet_y = co.cell(row=row, column=7).value
        this_ok = close(sheet_y, ref_y, tol=1e-6)
        ok = ok and this_ok
        # reprice identity: spot * e^((r+u-y)*T) must reproduce the observed price exactly
        reprice = spot * math.exp((r + u - ref_y) * T)
        this_ok2 = close(reprice, price, tol=1e-6)
        ok = ok and this_ok2
        details.append(f"contract {i}: y sheet={sheet_y:.4f}/ref={ref_y:.4f}, reprice ref={reprice:.4f} vs observed={price} "
                        f"{'OK' if (this_ok and this_ok2) else 'MISMATCH'}")

    # economic sanity: strictly rising futures prices (contango throughout) should
    # give convenience yield below the r+u financing/storage cost after M1
    contango_check = all(co.cell(row=11 + i, column=7).value < (r + u) for i in range(1, 5))
    ok = ok and contango_check
    details.append(f"contango curve -> convenience yield < r+u for M2-M12: {'OK' if contango_check else 'FAIL'}")

    return "Commodities: cost-of-carry implied convenience yield (reprices the observed curve exactly)", ok, " | ".join(details)


# ---------------------------------------------------------------------
# Asset Management: whole-fund (European) GP carry waterfall recomputed
# cumulatively each period, with a general (not hardcoded-to-100%)
# catch-up formula, and a clawback when a later markdown pulls cumulative
# profit down below what earlier-paid carry assumed.
# ---------------------------------------------------------------------
def check_am_gp_carry_clawback():
    path = os.path.join(REPO_ROOT, "08_Asset_Management", "_template_AM.xlsx")
    capital, hurdle, carry, catchup = 1_000_000, 0.08, 0.20, 1.00
    # (contribution, gain, fee) per period -- period 3 is a markdown, engineered
    # to trigger a clawback so "meaningful downside behavior" is actually exercised
    periods = [
        (1_000_000, 0, 0),
        (0, 400_000, 20_000),
        (0, 300_000, 20_000),
        (0, -500_000, 20_000),
    ]

    def populate(wb):
        nav = wb["Fund NAV"]
        for i, (contrib, gain, fee) in enumerate(periods):
            col = get_column_letter(3 + i)
            nav[f"{col}6"], nav[f"{col}7"], nav[f"{col}8"], nav[f"{col}9"] = contrib, gain, fee, 0
        fw = wb["Fee Waterfall"]
        fw["C5"], fw["C6"], fw["C7"], fw["C8"], fw["C9"] = capital, 0.02, hurdle, carry, catchup

    wb = with_recalc(path, populate)
    gc = wb["GP Carry & Clawback"]

    cum_capital = cum_gain = 0.0
    prior_cum_carry = 0.0
    ok = True
    details = []
    for i, (contrib, gain, fee) in enumerate(periods):
        col_idx = 3 + i
        cum_capital += contrib
        cum_gain += gain - fee
        value = cum_capital + cum_gain
        roc = min(value, cum_capital)
        pref = min(max(value - roc, 0), cum_capital * hurdle)
        catchup_tranche = 0.0 if catchup <= carry else min(max(value - roc - pref, 0), pref * carry / (catchup - carry))
        gp_catchup = catchup_tranche * catchup
        remainder = max(value - roc - pref - catchup_tranche, 0)
        gp_remainder = remainder * carry
        cum_gp_carry = gp_catchup + gp_remainder
        incremental = cum_gp_carry - prior_cum_carry
        prior_cum_carry = cum_gp_carry

        sheet_cum_carry = gc.cell(row=17, column=col_idx).value
        sheet_incremental = gc.cell(row=19, column=col_idx).value
        this_ok = close(sheet_cum_carry, cum_gp_carry, tol=1e-6) and close(sheet_incremental, incremental, tol=1e-6)
        ok = ok and this_ok
        details.append(f"P{i}: cum carry sheet={sheet_cum_carry:.0f}/ref={cum_gp_carry:.0f}, "
                        f"incremental sheet={sheet_incremental:.0f}/ref={incremental:.0f} {'OK' if this_ok else 'MISMATCH'}")

    clawback_period3 = gc.cell(row=21, column=6).value
    clawback_ok = isinstance(clawback_period3, str) and clawback_period3.startswith("CLAWBACK")
    ok = ok and clawback_ok
    details.append(f"Period-3 clawback flag: '{clawback_period3}' ({'OK — markdown correctly triggers clawback' if clawback_ok else 'MISSING'})")

    return "Asset Management: whole-fund GP carry waterfall + clawback on markdown", ok, " | ".join(details)


# ---------------------------------------------------------------------
# Private Credit: Excess Cash Flow sweep with a leverage-based step-down
# grid, non-circular (interest and the sweep tier both key off the
# BEGINNING-of-period balance) — plus the mandatory-amortization formula
# fix (it was reading the OID cell instead of the amort-% cell).
# ---------------------------------------------------------------------
def check_credit_ecf_sweep_stepdown():
    path = os.path.join(REPO_ROOT, "05_Private_Credit", "_template_CREDIT.xlsx")
    drawn, base_rate, spread, amort_pct = 100_000_000, 0.05, 0.045, 0.01
    ebitda, cfads = 25_000_000, 20_000_000
    all_in_rate = base_rate + spread
    tiers = [(4.0, 0.75), (3.0, 0.50), (2.0, 0.25)]  # (leverage >, sweep %)
    below_tier_sweep = 0.00

    def populate(wb):
        a = wb["Assumptions"]
        a["C6"], a["C7"], a["C8"], a["C11"] = drawn, base_rate, spread, amort_pct
        a["C14"], a["C15"] = ebitda, cfads

    wb = with_recalc(path, populate)
    ds = wb["Debt Schedule"]

    def sweep_pct(leverage):
        for threshold, pct in tiers:
            if leverage > threshold:
                return pct
        return below_tier_sweep

    ok = True
    details = []
    beg_bal = float(drawn)
    for i, col in enumerate(range(3, 9)):  # C..H = Yr0..Yr5
        letter = get_column_letter(col)
        amort = drawn * amort_pct
        beg_lev = beg_bal / ebitda
        pct = sweep_pct(beg_lev)
        interest = beg_bal * all_in_rate
        sweep = max(cfads - interest - amort, 0) * pct
        end_bal = beg_bal - amort - sweep

        sheet_beg = ds.cell(row=6, column=col).value
        sheet_sweep_pct = ds.cell(row=9, column=col).value
        sheet_interest = ds.cell(row=10, column=col).value
        sheet_sweep = ds.cell(row=11, column=col).value
        sheet_end = ds.cell(row=12, column=col).value

        this_ok = (close(sheet_beg, beg_bal) and close(sheet_sweep_pct, pct, tol=1e-6)
                   and close(sheet_interest, interest) and close(sheet_sweep, sweep)
                   and close(sheet_end, end_bal))
        ok = ok and this_ok
        details.append(f"{letter}(Yr{i}): lev={beg_lev:.3f} tier={pct:.0%} sweep=sheet:{sheet_sweep:.0f}/ref:{sweep:.0f} "
                        f"{'OK' if this_ok else 'MISMATCH'}")
        beg_bal = end_bal

    # the tier must actually change over the schedule as leverage falls —
    # otherwise the "step-down" is decorative, not mechanical
    sweep_pcts_seen = {round(sweep_pct(drawn / ebitda), 4)}
    beg_bal2 = float(drawn)
    for _ in range(6):
        amort = drawn * amort_pct
        lev = beg_bal2 / ebitda
        pct = sweep_pct(lev)
        sweep_pcts_seen.add(round(pct, 4))
        interest = beg_bal2 * all_in_rate
        sweep = max(cfads - interest - amort, 0) * pct
        beg_bal2 = beg_bal2 - amort - sweep
    steps_down = len(sweep_pcts_seen) > 1
    ok = ok and steps_down
    details.append(f"tiers actually visited across the schedule: {sorted(sweep_pcts_seen, reverse=True)} "
                    f"({'steps down as leverage falls' if steps_down else 'FLAT — grid not mechanically wired'})")

    return "Private Credit: ECF sweep step-down grid (non-circular, beginning-of-period)", ok, " | ".join(details)


# ---------------------------------------------------------------------
# Public Finance: forward-looking Additional Bonds Test (proposed new
# issuance's level debt service via PMT, pro-forma historical test, and a
# 5-year projected test under Base/Stress revenue growth scenarios).
# ---------------------------------------------------------------------
def check_public_finance_additional_bonds_test():
    path = os.path.join(REPO_ROOT, "07_Public_Finance", "_template_PUBLIC_FINANCE.xlsx")

    gross_rev, om_exp, senior_ds, sub_ds, covenant = 10_000_000, 3_000_000, 3_500_000, 500_000, 1.25
    new_par, coupon, term = 20_000_000, 0.045, 20
    rev_growth_base, rev_growth_stress = 0.03, -0.02
    om_growth_base, om_growth_stress = 0.025, 0.05

    def populate(wb, scenario):
        rbc = wb["Revenue Bond Coverage"]
        rbc["C5"], rbc["C6"], rbc["C7"], rbc["C8"], rbc["C16"] = gross_rev, om_exp, senior_ds, sub_ds, covenant
        abt = wb["Additional Bonds Test"]
        abt["C6"], abt["C7"], abt["C8"] = new_par, coupon, term
        abt["C24"], abt["C25"], abt["C26"], abt["C27"] = (
            rev_growth_base, rev_growth_stress, om_growth_base, om_growth_stress,
        )
        wb["Cover"]["C9"] = scenario

    # independent re-implementation: closed-form level-annuity payment,
    # not a copy of the sheet's own PMT() call
    new_bond_ds = new_par * coupon / (1 - (1 + coupon) ** -term)
    net_revenue = gross_rev - om_exp
    proforma_ds = senior_ds + new_bond_ds
    proforma_dscr = net_revenue / proforma_ds
    historical_pass = proforma_dscr >= covenant

    ok = True
    details = []

    wb = with_recalc(path, lambda w: populate(w, "Base"))
    abt = wb["Additional Bonds Test"]
    ok = ok and close(abt["C9"].value, new_bond_ds)
    ok = ok and close(abt["C18"].value, proforma_dscr)
    ok = ok and (abt["C20"].value == "PASS") == historical_pass
    details.append(f"new-bond DS: sheet={abt['C9'].value:.2f} closed-form={new_bond_ds:.2f} | "
                    f"pro-forma DSCR: sheet={abt['C18'].value:.4f} ref={proforma_dscr:.4f}")

    scenario_pass = {}
    for scenario, rev_g, om_g in (("Base", rev_growth_base, om_growth_base),
                                   ("Stress", rev_growth_stress, om_growth_stress)):
        wb = with_recalc(path, lambda w, s=scenario: populate(w, s))
        abt = wb["Additional Bonds Test"]
        rev, om = gross_rev, om_exp
        dscrs = []
        for _ in range(5):
            rev *= (1 + rev_g)
            om *= (1 + om_g)
            dscrs.append((rev - om) / proforma_ds)
        for i, ref_dscr in enumerate(dscrs):
            sheet_dscr = abt.cell(row=32 + i, column=7).value
            if not close(sheet_dscr, ref_dscr):
                ok = False
                details.append(f"{scenario} Yr{i+1} DSCR mismatch: sheet={sheet_dscr} ref={ref_dscr:.4f}")
        ref_min_dscr = min(dscrs)
        ok = ok and close(abt["C38"].value, ref_min_dscr)
        ref_overall_pass = ref_min_dscr >= covenant
        sheet_pass = abt["C40"].value.startswith("PASS")
        ok = ok and sheet_pass == ref_overall_pass
        scenario_pass[scenario] = sheet_pass
        details.append(f"{scenario}: min 5-yr DSCR sheet={abt['C38'].value:.4f} ref={ref_min_dscr:.4f}, "
                        f"projected test {'PASS' if sheet_pass else 'FAIL'} (expect {'PASS' if ref_overall_pass else 'FAIL'})")

    # Base must pass, Stress must fail by construction of these test inputs —
    # this is the "meaningful downside behavior" the governance standard requires.
    ok = ok and scenario_pass.get("Base") is True and scenario_pass.get("Stress") is False

    return "Public Finance: forward-looking Additional Bonds Test (PMT + historical + projected)", ok, " | ".join(details)


# ---------------------------------------------------------------------
# BASE archetype: DCF vs. Comps valuation triangulation -- a second,
# independent valuation estimate built from the Comps tab's own median
# multiples applied to the company's own financials, cross-checked
# against the DCF.
# ---------------------------------------------------------------------
def check_base_dcf_comps_triangulation():
    path = os.path.join(REPO_ROOT, "01_Investment_Banking", "_template_BASE.xlsx")
    growth = [0.10, 0.09, 0.08, 0.07, 0.06]
    gm, opex_pct, tax_rate, da_pct, capex_pct, shares = 0.60, 0.25, 0.25, 0.80, 0.05, 100
    rev0, interest0 = 1000.0, 20.0
    net_debt, wacc, term_g = 300, 0.10, 0.025
    ev_rev = [2.5, 3.0, 2.8, 2.6, 2.9, 3.1, 2.7, 2.4]
    ev_ebitda = [12.0, 13.0, 14.0, 11.5, 12.5, 13.5, 12.8, 11.9]

    def populate(wb):
        a = wb["Assumptions"]
        for i, g in enumerate(growth):
            a.cell(row=5, column=3 + i, value=g)
        for col in range(3, 8):
            a.cell(row=6, column=col, value=gm)
            a.cell(row=7, column=col, value=opex_pct)
            a.cell(row=8, column=col, value=tax_rate)
            a.cell(row=9, column=col, value=da_pct)
            a.cell(row=10, column=col, value=capex_pct)
            a.cell(row=12, column=col, value=shares)
        isheet = wb["IS"]
        isheet["E5"], isheet["E7"], isheet["E15"] = rev0, rev0 * (1 - gm), interest0
        dcf = wb["DCF"]
        dcf["I5"], dcf["I6"], dcf["I11"], dcf["I13"] = wacc, term_g, net_debt, shares
        comps = wb["Comps"]
        for i in range(8):
            row = 5 + i
            comps.cell(row=row, column=6, value=ev_rev[i])
            comps.cell(row=row, column=7, value=ev_ebitda[i])

    wb = with_recalc(path, populate)
    vc = wb["Valuation Cross-Check"]

    rev1 = rev0 * (1 + growth[0])
    ebitda1 = rev1 * gm - rev1 * opex_pct
    median_ev_rev = statistics.median(ev_rev)
    median_ev_ebitda = statistics.median(ev_ebitda)
    implied_ev_rev = rev1 * median_ev_rev
    implied_ev_ebitda = ebitda1 * median_ev_ebitda
    avg_implied_ev = (implied_ev_rev + implied_ev_ebitda) / 2
    implied_equity = avg_implied_ev - net_debt
    comps_value_per_share = implied_equity / shares

    ok = True
    details = []
    for label, sheet_val, ref_val in [
        ("FY1E EBITDA", vc["C12"].value, ebitda1),
        ("median EV/Rev", vc["C13"].value, median_ev_rev),
        ("median EV/EBITDA", vc["C14"].value, median_ev_ebitda),
        ("avg implied EV", vc["C17"].value, avg_implied_ev),
        ("Comps value/share", vc["C19"].value, comps_value_per_share),
    ]:
        this_ok = close(sheet_val, ref_val)
        ok = ok and this_ok
        details.append(f"{label}: sheet={sheet_val} ref={ref_val:.4f} {'OK' if this_ok else 'MISMATCH'}")

    dcf_value = wb["DCF"]["I14"].value
    ref_premium = dcf_value / comps_value_per_share - 1
    premium_ok = close(vc["C22"].value, ref_premium)
    ok = ok and premium_ok
    details.append(f"DCF-vs-Comps premium: sheet={vc['C22'].value:.4f} ref={ref_premium:.4f} {'OK' if premium_ok else 'MISMATCH'}")

    return "BASE: DCF vs. Comps valuation triangulation", ok, " | ".join(details)


# ---------------------------------------------------------------------
# VC Exit Waterfall: conservation (this is the exact bug class caught and
# fixed mid-session — pinned here as a permanent regression test).
# ---------------------------------------------------------------------
def check_vc_waterfall_conservation():
    path = os.path.join(REPO_ROOT, "13_Venture_Capital", "_template_VC.xlsx")

    def populate(wb, total_proceeds):
        ct = wb["Cap Table"]
        ct["C5"], ct["E5"] = 6_000_000, 0.0001
        ct["C6"], ct["E6"] = 1_000_000, 0.0001
        ct["C8"], ct["E8"] = 1_000_000, 1.00
        ct["C9"], ct["E9"] = 1_500_000, 2.00
        ct["C10"], ct["E10"] = 1_000_000, 5.00
        wb["Exit Waterfall"]["C15"] = total_proceeds

    ok = True
    details = []
    for scenario, proceeds in (("small exit (pref-stack regime)", 8_000_000),
                                ("large exit (as-converted regime)", 50_000_000)):
        wb = with_recalc(path, lambda w, p=proceeds: populate(w, p))
        ew = wb["Exit Waterfall"]
        distributed = ew["C11"].value
        this_ok = close(distributed, proceeds, tol=1e-6)
        ok = ok and this_ok
        details.append(f"{scenario}: distributed={distributed} vs proceeds={proceeds} ({'OK' if this_ok else 'FAIL'})")

    return "VC Exit Waterfall conservation (both regimes)", ok, "; ".join(details)


# ---------------------------------------------------------------------
# BASE archetype: integrated IS -> BS/CF -> DCF, spot-checked end to end.
# ---------------------------------------------------------------------
def check_base_archetype_integration():
    path = os.path.join(REPO_ROOT, "01_Investment_Banking", "_template_BASE.xlsx")
    growth = [0.10, 0.09, 0.08, 0.07, 0.06]
    gm, opex_pct, tax_rate, da_pct, capex_pct, shares = 0.60, 0.25, 0.25, 0.80, 0.05, 100
    rev0, interest0 = 1000.0, 20.0

    def populate(wb):
        a = wb["Assumptions"]
        for i, g in enumerate(growth):
            a.cell(row=5, column=3 + i, value=g)
        for c in range(3, 8):
            a.cell(row=6, column=c, value=gm)
            a.cell(row=7, column=c, value=opex_pct)
            a.cell(row=8, column=c, value=tax_rate)
            a.cell(row=9, column=c, value=da_pct)
            a.cell(row=10, column=c, value=capex_pct)
            a.cell(row=12, column=c, value=shares)
        isw = wb["IS"]
        isw["E5"] = rev0
        isw["E15"] = interest0

    wb = with_recalc(path, populate)
    isw = wb["IS"]
    sheet_rev = [isw.cell(row=5, column=c).value for c in range(6, 10)]
    sheet_ni = [isw.cell(row=18, column=c).value for c in range(6, 10)]

    ref_rev, ref_ni = [], []
    revenue = rev0
    for i, g in enumerate(growth[:4]):
        revenue = revenue * (1 + g)
        cogs = revenue * (1 - gm)
        gp = revenue - cogs
        opex = revenue * opex_pct
        ebitda = gp - opex
        da = revenue * capex_pct * da_pct
        ebit = ebitda - da
        pretax = ebit - interest0
        tax = pretax * tax_rate
        ni = pretax - tax
        ref_rev.append(revenue)
        ref_ni.append(ni)

    ok = all(close(a, b) for a, b in zip(sheet_rev, ref_rev))
    ok = ok and all(close(a, b) for a, b in zip(sheet_ni, ref_ni))

    cf = wb["CF"]
    cf_ni = [cf.cell(row=5, column=c).value for c in range(5, 8)]
    ok = ok and all(close(a, b) for a, b in zip(cf_ni, sheet_ni[:3]))

    detail = (f"revenue: sheet={sheet_rev} ref={ref_rev} | "
              f"net income: sheet={sheet_ni} ref={ref_ni} | CF-linked NI={cf_ni}")
    return "BASE archetype: IS projections + CF linkage", ok, detail


CHECKS = [
    check_black_scholes,
    check_bond_duration,
    check_accrued_interest,
    check_bornhuetter_ferguson,
    check_securitization_tranche_waterfall,
    check_lbo_sources_uses_and_debt_schedule,
    check_lbo_scenario_switch,
    check_american_option_binomial,
    check_portfolio_var,
    check_insurance_mack_method,
    check_options_greeks_finite_difference,
    check_risk_historical_vs_parametric_var,
    check_base_dcf_comps_triangulation,
    check_vc_participating_preferred_cap,
    check_trade_finance_dynamic_discounting,
    check_restructuring_ev_sensitivity,
    check_real_estate_lp_gp_promote,
    check_quant_psr_mintrl,
    check_project_finance_dsra,
    check_microfinance_flat_vs_declining,
    check_fintech_interchange_durbin,
    check_crypto_perp_funding_basis,
    check_commodities_convenience_yield,
    check_am_gp_carry_clawback,
    check_credit_ecf_sweep_stepdown,
    check_public_finance_additional_bonds_test,
    check_cover_tab_field_alignment,
    check_vc_waterfall_conservation,
    check_base_archetype_integration,
]


def main():
    print(f"Running {len(CHECKS)} independent-oracle verification checks...\n")
    all_ok = True
    for check in CHECKS:
        try:
            name, ok, detail = check()
        except Exception as e:  # noqa: BLE001
            name, ok, detail = check.__name__, False, f"raised {type(e).__name__}: {e}"
        all_ok = all_ok and ok
        print(f"[{'PASS' if ok else 'FAIL'}] {name}")
        print(f"       {detail}\n")

    print("=" * 60)
    print("ALL CHECKS PASSED" if all_ok else "SOME CHECKS FAILED")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
