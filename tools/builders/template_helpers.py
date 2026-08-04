"""Shared styling helpers — imported by every build_*_template.py script."""
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

BLUE = Font(name="Arial", size=10, color="0000FF")
BLACK = Font(name="Arial", size=10, color="000000")
GREEN = Font(name="Arial", size=10, color="008000")
BOLD = Font(name="Arial", size=10, bold=True)
BOLD_WHITE = Font(name="Arial", size=11, bold=True, color="FFFFFF")
TITLE = Font(name="Arial", size=16, bold=True)
ITALIC_GRAY = Font(name="Arial", size=8, italic=True, color="808080")
YELLOW_FILL = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
HEADER_FILL = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
GRAY_FILL = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

CUR = '$#,##0;($#,##0);"-"'
CUR2 = '$#,##0.00;($#,##0.00);"-"'
PCT = '0.0%;(0.0%);"-"'
PCT2 = '0.00%;(0.00%);"-"'
MULT = '0.0x'
NUM = '#,##0;(#,##0);"-"'


def style_header_row(ws, row, ncols, start_col=1):
    for c in range(start_col, start_col + ncols):
        cell = ws.cell(row=row, column=c)
        cell.font = BOLD_WHITE
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal="center")


def set_col_widths(ws, widths):
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w


def add_refresh_log(wb):
    ws = wb.create_sheet("RefreshLog")
    set_col_widths(ws, [4, 14, 16, 30, 30, 16])
    ws["B2"] = "Refresh Log"; ws["B2"].font = TITLE
    for i, h in enumerate(["", "Date", "Trigger", "What changed", "Reviewer notes", "Next check"], start=1):
        ws.cell(row=4, column=i, value=h)
    style_header_row(ws, 4, 5, start_col=2)
    for r in range(5, 15):
        for c in range(2, 7):
            ws.cell(row=r, column=c).border = BORDER
    ws.sheet_view.showGridLines = False
    return ws


def add_cover(wb, title, fields):
    """fields: list of (label, default_value) tuples"""
    ws = wb.create_sheet("Cover")
    set_col_widths(ws, [4, 30, 40, 4])
    ws["B2"] = title; ws["B2"].font = TITLE
    r = 4
    for label, default in fields:
        ws.cell(row=r, column=2, value=label).font = BOLD
        c = ws.cell(row=r, column=3, value=default)
        c.font = BLUE
        r += 1
    ws.sheet_view.showGridLines = False
    return ws


def add_sources_checks(wb, sources, checks):
    """M3 evidence-pack sheet pair (docs/MODEL_GOVERNANCE_STANDARD.md).

    sources: list of (assumption, source, as_of, note) tuples -- where each
        material input/convention in the model actually comes from.
    checks: list of (label, formula_str, expect_str) tuples -- live
        in-workbook reconciliation identities (not a copy of the model's
        own output; things that must independently tie, e.g. a waterfall
        summing back to total proceeds, a triangle's row totals matching
        its diagonal). formula_str is an Excel formula string (with the
        leading '='); expect_str describes what a passing result looks
        like, in words, for a human reviewer.
    """
    ws = wb.create_sheet("Sources")
    set_col_widths(ws, [4, 34, 30, 14, 46])
    ws["B2"] = "Sources"; ws["B2"].font = TITLE
    ws["B3"] = "What each material assumption or convention in this model comes from."
    ws["B3"].font = ITALIC_GRAY
    headers = ["", "Assumption / convention", "Source", "As of", "Note"]
    for i, h in enumerate(headers, start=1):
        ws.cell(row=5, column=i, value=h)
    style_header_row(ws, 5, 4, start_col=2)
    r = 6
    for assumption, source, as_of, note in sources:
        ws.cell(row=r, column=2, value=assumption).font = BLACK
        ws.cell(row=r, column=3, value=source).font = BLACK
        ws.cell(row=r, column=4, value=as_of).font = BLACK
        ws.cell(row=r, column=5, value=note).font = ITALIC_GRAY
        for c in range(2, 6):
            ws.cell(row=r, column=c).border = BORDER
        r += 1
    ws.sheet_view.showGridLines = False

    ws2 = wb.create_sheet("Checks")
    set_col_widths(ws2, [4, 40, 18, 46])
    ws2["B2"] = "Checks"; ws2["B2"].font = TITLE
    ws2["B3"] = "Live reconciliation identities -- independent of the model's own formulas, must tie."
    ws2["B3"].font = ITALIC_GRAY
    headers2 = ["", "Check", "Result", "Passes when"]
    for i, h in enumerate(headers2, start=1):
        ws2.cell(row=5, column=i, value=h)
    style_header_row(ws2, 5, 3, start_col=2)
    r = 6
    for label, formula, expect in checks:
        ws2.cell(row=r, column=2, value=label).font = BLACK
        c = ws2.cell(row=r, column=3, value=formula)
        c.font = BOLD; c.border = BORDER
        ws2.cell(row=r, column=4, value=expect).font = ITALIC_GRAY
        ws2.cell(row=r, column=2).border = BORDER
        ws2.cell(row=r, column=4).border = BORDER
        r += 1
    ws2.sheet_view.showGridLines = False
    return ws, ws2
