# Model Card — Fixed Income / Rates

## Decision this model is designed to support
Three linked questions about a bond position: (1) what is it worth today
given its coupon, maturity, and the market yield (Bond Pricing), (2) how
much does that price move for a small parallel yield change -- the
first-order (duration) AND -- the new addition -- second-order (convexity)
sensitivity, both cross-checked two independent ways -- and (3) what does
the buyer actually pay at settlement once accrued interest between coupon
dates is included (clean vs. dirty price).

## Owner
unassigned

## Risk tier
Tier 1 (pricing / risk decision) for a populated instance. Blank template
is Tier 3.

## Methodology
- **Bond pricing**: standard level-coupon bullet bond PV (Excel `PV`
  function on a per-period coupon and yield).
- **Duration & convexity -- two independent methods, cross-checked**:
  1. *Numerical (finite-difference)*: reprice the bond at YTM +/- a shock
     (default 50bp) and take the standard central-difference formulas for
     modified duration and convexity. Simple, no cash-flow table required,
     but an approximation whose accuracy depends on shock size.
  2. *Closed-form (the new addition)*: build the bond's actual
     period-by-period cash flow schedule (up to 120 periods) and sum
     `t x PV(CF_t)` and `t(t+1) x PV(CF_t)` directly -- the textbook
     definitions of Macaulay/modified duration and convexity. Exact given
     the bond's stated cash flows; this is the reference the numerical
     method is approximating, not a second guess.
  Both methods are shown side by side with an explicit diff row, and the
  Checks sheet requires them to agree closely (a large diff would indicate
  a real formula bug, not just discretization noise -- see validation.md
  for how this caught exactly that).
- **Accrued interest / clean-dirty price**: 30/360 (standard for most
  corporate/municipal bonds) and Actual/Actual (standard for U.S.
  Treasuries) day-count conventions, both computed and shown to
  legitimately disagree on the identical settlement date.

## Conventions and units
USD. Semi-annual coupon default (typical for US bonds), but coupon
frequency is a free input. Closed-form cash flow schedule supports up to
120 periods (covers e.g. 60y semi-annual, 30y quarterly, 10y monthly) --
see Boundary conditions.

## Material assumptions
- Option-free (bullet) bond -- no call, put, or conversion features.
- Flat, parallel yield shocks for duration/convexity -- does not model
  curve reshaping (twist, butterfly) or key-rate duration.
- A single YTM discounts every cash flow -- no credit-spread-vs-risk-free
  decomposition.

## Boundary conditions / when this breaks
- The closed-form cash flow schedule is built for up to 120 periods
  (coupon frequency x years to maturity). Inputs implying more periods
  than that will silently truncate the closed-form sums -- the on-sheet
  "closed-form price" row is the tell (it will stop matching Bond
  Pricing's own price) and is included specifically so this failure mode
  is visible, not silent.
- The numerical (finite-difference) convexity estimate at the default
  50bp shock carries real (not huge, but non-trivial) approximation
  error relative to the closed-form value -- verified during this
  validation pass at ~0.02% relative error for a typical 10y bond (see
  validation.md); do not assume the FD convexity number is exact to the
  same precision as the FD duration number, which is materially more
  accurate at the same shock size.

## Known limitations
- No yield-curve bootstrapping -- the Yield Curve tab takes benchmark
  yields and spreads as direct inputs, it does not derive spot/forward
  curves from par yields.
- No embedded optionality (callable/putable/convertible) -- an
  option-adjusted spread (OAS) model would be needed for those.
- No populated instance yet.

## When this model should not be used
Not a substitute for a full fixed-income risk system, which would handle
callable/putable structures via OAS, key-rate (not just parallel-shift)
duration for curve-reshaping risk, and a real yield-curve bootstrap
instead of directly input benchmark yields.

## Stakeholder perspectives represented
- **Portfolio manager / trader**: price, duration, convexity, and the
  actual settlement (dirty) price.
Not represented: **risk manager's key-rate/curve-shape view**, **issuer's
funding-cost view**.

## Version
Built by `tools/builders/build_fixed_income_template.py`. Closed-form
convexity cross-check shipped alongside `check_bond_convexity` in
`tools/verify_reference_calcs.py` (joining the pre-existing
`check_bond_duration` and `check_accrued_interest`).
