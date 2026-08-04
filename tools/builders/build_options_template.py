import openpyxl
from template_helpers import *

wb = openpyxl.Workbook()
wb.remove(wb.active)

add_cover(wb, "[UNDERLYING] — Options Model", [
    ("Underlying:", "[fill in]"),
    ("Option type covered:", "Equity / index / FX / commodity options"),
    ("Last refreshed:", "[date]"),
    ("Next expiry to watch:", "[date]"),
    ("Refresh cadence:", "Weekly (daily near expiry)"),
])

# ---------------- BLACK-SCHOLES PRICER ----------------
ws = wb.create_sheet("BS Pricer")
set_col_widths(ws, [4, 26, 14, 4, 26, 16])
ws["B2"] = "Black-Scholes Pricer"; ws["B2"].font = TITLE
ws["B4"] = "Inputs"; ws["B4"].font = BOLD; ws["B4"].fill = GRAY_FILL
inputs = [
    ("Spot price (S)", 100, CUR2),
    ("Strike price (K)", 100, CUR2),
    ("Time to expiry (yrs, T)", 0.25, '0.0000'),
    ("Risk-free rate (r)", 0.045, PCT2),
    ("Dividend yield (q)", 0.0, PCT2),
    ("Implied volatility (sigma)", 0.30, PCT),
]
r = 5
for label, default, fmt in inputs:
    ws.cell(row=r, column=2, value=label).font = BLACK
    c = ws.cell(row=r, column=3, value=default); c.font = BLUE; c.fill = YELLOW_FILL
    c.number_format = fmt; c.border = BORDER
    r += 1

# Named-ish cell refs: S=C5, K=C6, T=C7, r=C8, q=C9, sigma=C10
ws["E4"] = "Intermediate"; ws["E4"].font = BOLD; ws["E4"].fill = GRAY_FILL
ws["E5"] = "d1"
ws["F5"] = "=(LN(C5/C6)+(C8-C9+0.5*C10^2)*C7)/(C10*SQRT(C7))"
ws["E6"] = "d2"
ws["F6"] = "=F5-C10*SQRT(C7)"
ws["E7"] = "N(d1)"
ws["F7"] = "=NORMSDIST(F5)"
ws["E8"] = "N(d2)"
ws["F8"] = "=NORMSDIST(F6)"
ws["E9"] = "N(-d1)"
ws["F9"] = "=NORMSDIST(-F5)"
ws["E10"] = "N(-d2)"
ws["F10"] = "=NORMSDIST(-F6)"
for row in range(5, 11):
    ws.cell(row=row, column=6).number_format = '0.0000'
    ws.cell(row=row, column=6).border = BORDER

ws["B12"] = "Outputs"; ws["B12"].font = BOLD; ws["B12"].fill = GRAY_FILL
ws["B13"] = "Call price"
ws["C13"] = "=C5*EXP(-C9*C7)*F7-C6*EXP(-C8*C7)*F8"
ws["B14"] = "Put price"
ws["C14"] = "=C6*EXP(-C8*C7)*F10-C5*EXP(-C9*C7)*F9"
for row in (13, 14):
    ws.cell(row=row, column=3).font = BOLD
    ws.cell(row=row, column=3).number_format = CUR2
    ws.cell(row=row, column=3).border = BORDER
ws.sheet_view.showGridLines = False

# ---------------- GREEKS ----------------
ws = wb.create_sheet("Greeks")
set_col_widths(ws, [4, 20, 16, 16, 40])
ws["B2"] = "Greeks (linked to BS Pricer inputs)"; ws["B2"].font = TITLE
for i, h in enumerate(["", "Greek", "Call", "Put", "Interpretation"], start=1):
    ws.cell(row=4, column=i, value=h)
style_header_row(ws, 4, 4)

S, K, T, rr, q, sig = "'BS Pricer'!$C$5", "'BS Pricer'!$C$6", "'BS Pricer'!$C$7", \
                       "'BS Pricer'!$C$8", "'BS Pricer'!$C$9", "'BS Pricer'!$C$10"
d1, d2 = "'BS Pricer'!$F$5", "'BS Pricer'!$F$6"
Nd1, Nd2, Nnd1, Nnd2 = "'BS Pricer'!$F$7", "'BS Pricer'!$F$8", "'BS Pricer'!$F$9", "'BS Pricer'!$F$10"

greek_rows = [
    ("Delta", f"=EXP(-{q}*{T})*{Nd1}", f"=-EXP(-{q}*{T})*{Nnd1}", "Price sensitivity to $1 move in underlying"),
    ("Gamma", f"=EXP(-{q}*{T})*(EXP(-({d1})^2/2)/SQRT(2*PI()))/({S}*{sig}*SQRT({T}))",
              f"=EXP(-{q}*{T})*(EXP(-({d1})^2/2)/SQRT(2*PI()))/({S}*{sig}*SQRT({T}))", "Rate of change of delta"),
    ("Vega (per 1% vol)", f"={S}*EXP(-{q}*{T})*(EXP(-({d1})^2/2)/SQRT(2*PI()))*SQRT({T})/100",
                          f"={S}*EXP(-{q}*{T})*(EXP(-({d1})^2/2)/SQRT(2*PI()))*SQRT({T})/100", "Sensitivity to 1pt vol change"),
    ("Theta (per day)", f"=(-{S}*(EXP(-({d1})^2/2)/SQRT(2*PI()))*{sig}*EXP(-{q}*{T})/(2*SQRT({T}))-{rr}*{K}*EXP(-{rr}*{T})*{Nd2}+{q}*{S}*EXP(-{q}*{T})*{Nd1})/365",
                        f"=(-{S}*(EXP(-({d1})^2/2)/SQRT(2*PI()))*{sig}*EXP(-{q}*{T})/(2*SQRT({T}))+{rr}*{K}*EXP(-{rr}*{T})*{Nnd2}-{q}*{S}*EXP(-{q}*{T})*{Nnd1})/365",
                        "Time decay per calendar day"),
    ("Rho (per 1%)", f"={K}*{T}*EXP(-{rr}*{T})*{Nd2}/100", f"=-{K}*{T}*EXP(-{rr}*{T})*{Nnd2}/100", "Sensitivity to 1pt rate change"),
]
r = 5
for label, call_f, put_f, note in greek_rows:
    ws.cell(row=r, column=2, value=label).font = BLACK
    ws.cell(row=r, column=3, value=call_f).number_format = '0.0000'
    ws.cell(row=r, column=4, value=put_f).number_format = '0.0000'
    ws.cell(row=r, column=5, value=note).font = ITALIC_GRAY
    for c in (3, 4):
        ws.cell(row=r, column=c).border = BORDER
    r += 1
ws.sheet_view.showGridLines = False

# ---------------- STRATEGY PAYOFFS ----------------
ws = wb.create_sheet("Strategy Payoffs")
set_col_widths(ws, [4, 14] + [12]*9)
ws["B2"] = "Payoff at Expiry — Long Straddle Example"; ws["B2"].font = TITLE
ws["B4"] = "Underlying price at expiry ->"; ws["B4"].font = BOLD
prices = list(range(70, 131, 10))
for i, p in enumerate(prices, start=3):
    c = ws.cell(row=4, column=i, value=p); c.font = BOLD; c.fill = GRAY_FILL; c.number_format = CUR

ws["B5"] = "Long call payoff"; ws["B6"] = "Long put payoff"; ws["B7"] = "Net payoff (straddle)"
ws["B8"] = "Less: premium paid"; ws["B9"] = "Net P&L"
for i, p in enumerate(prices, start=3):
    col = get_column_letter(i)
    ws.cell(row=5, column=i, value=f"=MAX({col}4-'BS Pricer'!$C$6,0)").number_format = CUR
    ws.cell(row=6, column=i, value=f"=MAX('BS Pricer'!$C$6-{col}4,0)").number_format = CUR
    ws.cell(row=7, column=i, value=f"={col}5+{col}6").number_format = CUR
    ws.cell(row=8, column=i, value="='BS Pricer'!$C$13+'BS Pricer'!$C$14").number_format = CUR
    ws.cell(row=9, column=i, value=f"={col}7-{col}8").font = BOLD
    ws.cell(row=9, column=i).number_format = CUR
for row in range(5, 10):
    for c in range(3, 12):
        ws.cell(row=row, column=c).border = BORDER
ws["B11"] = "Note: swap the payoff formulas per leg to model spreads, collars, condors, etc."
ws["B11"].font = ITALIC_GRAY
ws.sheet_view.showGridLines = False

# ---------------- IMPLIED VOLATILITY SOLVER ----------------
# In practice this runs more often than forward BS pricing: the market
# quotes a price, and the question is what volatility it implies. Excel's
# native tool for this is Goal Seek, which isn't scriptable/reproducible in
# a committed workbook. Newton-Raphson unrolled across a fixed number of
# iteration columns gets the same answer deterministically, with no
# iterative-calculation setting and no circular reference — each column
# only reads the previous one.
ws = wb.create_sheet("Implied Volatility")
set_col_widths(ws, [4, 26] + [11] * 9 + [40])
ws["B2"] = "Implied Volatility — Newton-Raphson Solver"; ws["B2"].font = TITLE
ws["B4"] = "Inputs"; ws["B4"].font = BOLD; ws["B4"].fill = GRAY_FILL
iv_inputs = [
    ("Option type (Call or Put)", "Call", None),
    ("Spot price (S)", 100, CUR2),
    ("Strike price (K)", 100, CUR2),
    ("Time to expiry (yrs, T)", 0.25, "0.0000"),
    ("Risk-free rate (r)", 0.045, PCT2),
    ("Dividend yield (q)", 0.0, PCT2),
    ("Observed market price (target)", 6.52, CUR2),
]
r = 5
for label, default, fmt in iv_inputs:
    ws.cell(row=r, column=2, value=label).font = BLACK
    c = ws.cell(row=r, column=3, value=default)
    c.font = BLUE
    c.fill = YELLOW_FILL
    if fmt:
        c.number_format = fmt
    c.border = BORDER
    r += 1
type_row, S_row, K_row, T_row, r_row, q_row, target_row = range(5, 12)

ws["B13"] = "Newton-Raphson iterations (converges to machine precision in 2-3 steps for any reasonable option; 9 shown as a safety margin)"
ws["B13"].font = ITALIC_GRAY
for i in range(9):
    col = get_column_letter(3 + i)
    ws.cell(row=14, column=3 + i, value=f"Iter {i}").font = BOLD
    ws.cell(row=14, column=3 + i).fill = GRAY_FILL
    ws.cell(row=14, column=3 + i).alignment = Alignment(horizontal="center")

ws["B15"] = "Sigma (vol estimate)"
ws["B16"] = "d1"
ws["B17"] = "d2"
ws["B18"] = "Price at this sigma"
ws["B19"] = "Vega (dPrice/dSigma, raw)"

S, K, T, rr, q = f"$C${S_row}", f"$C${K_row}", f"$C${T_row}", f"$C${r_row}", f"$C${q_row}"
target = f"$C${target_row}"
opt_type = f"$C${type_row}"

for i in range(9):
    col = get_column_letter(3 + i)
    if i == 0:
        # Brenner-Subrahmanyam closed-form approximation as the starting guess.
        ws[f"{col}15"] = f"=SQRT(2*PI()/{T})*({target}/{S})"
    else:
        prev = get_column_letter(3 + i - 1)
        ws[f"{col}15"] = f"={prev}15-({prev}18-{target})/{prev}19"
    ws[f"{col}15"].number_format = PCT2

    ws[f"{col}16"] = f"=(LN({S}/{K})+({rr}-{q}+0.5*{col}15^2)*{T})/({col}15*SQRT({T}))"
    ws[f"{col}16"].number_format = "0.0000"
    ws[f"{col}17"] = f"={col}16-{col}15*SQRT({T})"
    ws[f"{col}17"].number_format = "0.0000"
    ws[f"{col}18"] = (
        f'=IF({opt_type}="Call",'
        f"{S}*EXP(-{q}*{T})*NORMSDIST({col}16)-{K}*EXP(-{rr}*{T})*NORMSDIST({col}17),"
        f"{K}*EXP(-{rr}*{T})*NORMSDIST(-{col}17)-{S}*EXP(-{q}*{T})*NORMSDIST(-{col}16))"
    )
    ws[f"{col}18"].number_format = CUR2
    ws[f"{col}19"] = f"={S}*EXP(-{q}*{T})*(EXP(-{col}16^2/2)/SQRT(2*PI()))*SQRT({T})"
    ws[f"{col}19"].number_format = "0.0000"
    for row in (15, 16, 17, 18, 19):
        ws.cell(row=row, column=3 + i).border = BORDER

ws["B21"] = "Implied volatility (final iteration)"
ws["C21"] = "=K15"
ws["C21"].font = BOLD
ws["C21"].fill = YELLOW_FILL
ws["C21"].number_format = PCT2
ws["C21"].border = BORDER
ws["B22"] = "Convergence check (final price vs. target, should be ~0)"
ws["C22"] = "=K18-C11"
ws["C22"].number_format = CUR2
ws["C22"].border = BORDER
ws.sheet_view.showGridLines = False

# ---------------- AMERICAN OPTION (BINOMIAL TREE) ----------------
# Black-Scholes is European-only by construction (it assumes exercise can
# happen only at expiry). American options can be exercised any time before
# expiry, and for a put (or a call on a dividend payer) that early-exercise
# right has real value the BS formula structurally cannot price. A
# Cox-Ross-Rubinstein binomial tree handles it directly: at every node,
# compare holding the option (discounted expected continuation value)
# against exercising immediately, and take the greater.
#
# N=10 steps here — a fixed, modest tree size chosen so the whole thing fits
# legibly in one sheet (a production desk would run hundreds of steps for
# convergence to a fraction of a cent; 10 steps gets within roughly 1-3% of
# the true value, which is enough to see the early-exercise premium clearly
# without an unreadable 200-column tree). European binomial value is built
# alongside it as both a comparison and a sanity check: it should converge
# toward the closed-form Black-Scholes price as a cross-verification that
# the tree mechanics are right before trusting the American branch.
ws = wb.create_sheet("American Option (Binomial)")
N = 10
set_col_widths(ws, [4, 30] + [10] * (N + 1) + [40])
ws["B2"] = f"American Option Pricing — {N}-Step Binomial Tree (Cox-Ross-Rubinstein)"
ws["B2"].font = TITLE

ws["B4"] = "Inputs"; ws["B4"].font = BOLD; ws["B4"].fill = GRAY_FILL
am_inputs = [
    ("Option type (Call or Put)", "Put", None),
    ("Spot price (S)", 100, CUR2),
    ("Strike price (K)", 100, CUR2),
    ("Time to expiry (yrs, T)", 1.0, "0.0000"),
    ("Risk-free rate (r)", 0.045, PCT2),
    ("Dividend yield (q)", 0.0, PCT2),
    ("Implied volatility (sigma)", 0.30, PCT),
]
r = 5
for label, default, fmt in am_inputs:
    ws.cell(row=r, column=2, value=label).font = BLACK
    c = ws.cell(row=r, column=3, value=default)
    c.font = BLUE
    c.fill = YELLOW_FILL
    if fmt:
        c.number_format = fmt
    c.border = BORDER
    r += 1
opt_row, S_row, K_row, T_row, r_row, q_row, sig_row = range(5, 12)

ws["B14"] = "Derived tree parameters"; ws["B14"].font = BOLD; ws["B14"].fill = GRAY_FILL
ws["B15"] = "Time step (dt = T/N)"
ws["C15"] = f"=$C${T_row}/{N}"; ws["C15"].number_format = "0.00000"
ws["B16"] = "Up factor (u = e^(sigma*sqrt(dt)))"
ws["C16"] = f"=EXP($C${sig_row}*SQRT(C15))"; ws["C16"].number_format = "0.00000"
ws["B17"] = "Down factor (d = 1/u)"
ws["C17"] = "=1/C16"; ws["C17"].number_format = "0.00000"
ws["B18"] = "Risk-neutral up-probability (p)"
ws["C18"] = f"=(EXP(($C${r_row}-$C${q_row})*C15)-C17)/(C16-C17)"; ws["C18"].number_format = "0.00000"
ws["B19"] = "Per-step discount factor"
ws["C19"] = f"=EXP(-$C${r_row}*C15)"; ws["C19"].number_format = "0.00000"
for rr2 in (15, 16, 17, 18, 19):
    ws.cell(row=rr2, column=3).border = BORDER

u_cell, d_cell, p_cell, disc_cell = "$C$16", "$C$17", "$C$18", "$C$19"
S_cell, K_cell, opt_cell = f"$C${S_row}", f"$C${K_row}", f"$C${opt_row}"

und_row0 = 22
am_row0 = und_row0 + N + 1 + 2
eu_row0 = am_row0 + N + 1 + 2

ws.cell(row=und_row0 - 1, column=2, value="Underlying Price Tree").font = BOLD
ws.cell(row=am_row0 - 1, column=2, value="American Option Value Tree (exercise-or-hold at every node)").font = BOLD
ws.cell(row=eu_row0 - 1, column=2, value="European Option Value Tree (hold-only — comparison / BS cross-check)").font = BOLD

for i in range(N + 1):
    ws.cell(row=und_row0 + i, column=2, value=f"t={i}")
    ws.cell(row=am_row0 + i, column=2, value=f"t={i}")
    ws.cell(row=eu_row0 + i, column=2, value=f"t={i}")
    for j in range(i + 1):
        col = get_column_letter(3 + j)
        u_row = und_row0 + i
        # Underlying price at node (i,j): S x u^j x d^(i-j).
        cell = ws.cell(row=u_row, column=3 + j, value=f"={S_cell}*{u_cell}^{j}*{d_cell}^{i - j}")
        cell.number_format = CUR2
        cell.border = BORDER
        cell.font = GREEN

        und_ref = f"{col}{u_row}"
        intrinsic = (f'IF({opt_cell}="Call",MAX({und_ref}-{K_cell},0),'
                     f'MAX({K_cell}-{und_ref},0))')

        a_row = am_row0 + i
        e_row = eu_row0 + i
        if i == N:
            # Terminal payoff — same for both trees, no continuation value.
            a_formula = f"={intrinsic}"
            e_formula = f"={intrinsic}"
        else:
            next_col_up = get_column_letter(3 + j + 1)
            a_cont = (f"{disc_cell}*({p_cell}*{next_col_up}{a_row + 1}"
                      f"+(1-{p_cell})*{col}{a_row + 1})")
            e_cont = (f"{disc_cell}*({p_cell}*{next_col_up}{e_row + 1}"
                      f"+(1-{p_cell})*{col}{e_row + 1})")
            a_formula = f"=MAX({intrinsic},{a_cont})"
            e_formula = f"={e_cont}"
        a_cell = ws.cell(row=a_row, column=3 + j, value=a_formula)
        a_cell.number_format = CUR2
        a_cell.border = BORDER
        e_cell = ws.cell(row=e_row, column=3 + j, value=e_formula)
        e_cell.number_format = CUR2
        e_cell.border = BORDER

summary_row = eu_row0 + N + 1 + 2
ws.cell(row=summary_row, column=2, value="American option value (today, t=0)").font = BOLD
c = ws.cell(row=summary_row, column=3, value=f"=C{am_row0}")
c.font = BOLD; c.number_format = CUR2; c.fill = YELLOW_FILL; c.border = BORDER
ws.cell(row=summary_row + 1, column=2, value="European (binomial) option value (today, t=0)")
c = ws.cell(row=summary_row + 1, column=3, value=f"=C{eu_row0}")
c.number_format = CUR2; c.border = BORDER
ws.cell(row=summary_row + 2, column=2, value="Early-exercise premium (American - European)")
c = ws.cell(row=summary_row + 2, column=3, value=f"=C{summary_row}-C{summary_row + 1}")
c.font = BOLD; c.number_format = CUR2; c.border = BORDER
ws.cell(row=summary_row + 2, column=4,
        value="Should be ~0 for a call with no dividends (early exercise is never optimal) and positive for a put")
ws.cell(row=summary_row + 2, column=4).font = ITALIC_GRAY
ws.cell(row=summary_row + 3, column=2, value="Closed-form Black-Scholes (European) cross-check")
c = ws.cell(row=summary_row + 3, column=3,
            value=(f'=IF({opt_cell}="Call",'
                   f"{S_cell}*EXP(-$C${q_row}*$C${T_row})*NORMSDIST((LN({S_cell}/{K_cell})"
                   f"+($C${r_row}-$C${q_row}+0.5*$C${sig_row}^2)*$C${T_row})/($C${sig_row}*SQRT($C${T_row})))"
                   f"-{K_cell}*EXP(-$C${r_row}*$C${T_row})*NORMSDIST((LN({S_cell}/{K_cell})"
                   f"+($C${r_row}-$C${q_row}+0.5*$C${sig_row}^2)*$C${T_row})/($C${sig_row}*SQRT($C${T_row}))"
                   f"-$C${sig_row}*SQRT($C${T_row})),"
                   f"{K_cell}*EXP(-$C${r_row}*$C${T_row})*NORMSDIST(-((LN({S_cell}/{K_cell})"
                   f"+($C${r_row}-$C${q_row}+0.5*$C${sig_row}^2)*$C${T_row})/($C${sig_row}*SQRT($C${T_row}))"
                   f"-$C${sig_row}*SQRT($C${T_row})))"
                   f"-{S_cell}*EXP(-$C${q_row}*$C${T_row})*NORMSDIST(-((LN({S_cell}/{K_cell})"
                   f"+($C${r_row}-$C${q_row}+0.5*$C${sig_row}^2)*$C${T_row})/($C${sig_row}*SQRT($C${T_row})))))"))
c.number_format = CUR2; c.border = BORDER
ws.cell(row=summary_row + 3, column=4,
        value="The European binomial value above should sit close to this — both price the same no-early-exercise option two different ways")
ws.cell(row=summary_row + 3, column=4).font = ITALIC_GRAY
ws.sheet_view.showGridLines = False

add_refresh_log(wb)

out_path = "OPTIONS_template.xlsx"
wb.save(out_path)
print("saved", out_path)
