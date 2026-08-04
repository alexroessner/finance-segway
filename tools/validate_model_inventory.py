"""
validate_model_inventory.py — checks maturity CLAIMS in
standards/model_inventory.json against actual repo evidence.

This is the mechanism that keeps "M2" / "M3" from being vibes. It does not
grade financial correctness (that's verify_reference_calcs.py's job); it
checks that the *structural* evidence a claimed maturity level requires
actually exists on disk:

  M1 -- builder + workbook template exist.
  M2 -- M1, plus every listed reference_checks name is both defined in
        tools/verify_reference_calcs.py and registered in its CHECKS list
        (so it actually runs, not just exists as dead code).
  M3 -- M2, plus the workbook template has "Sources" and "Checks" sheets,
        and model_card.md + validation.md exist for the domain.
  M4 -- M3, plus at least two populated instance workbooks are listed and
        exist on disk.

A domain fails validation if its CLAIMED maturity exceeds what the evidence
supports. It is not an error to claim less than the evidence would support
(conservative claims are fine) -- only overclaiming fails.

Usage:
    python3 tools/validate_model_inventory.py
Exit code is 0 iff every claim is supported by evidence.
"""
import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INVENTORY_PATH = os.path.join(REPO_ROOT, "standards", "model_inventory.json")
VERIFY_PATH = os.path.join(REPO_ROOT, "tools", "verify_reference_calcs.py")

MATURITY_RANK = {"M0": 0, "M1": 1, "M2": 2, "M3": 3, "M4": 4}


def load_verify_source():
    with open(VERIFY_PATH) as f:
        return f.read()


def registered_checks(source):
    defined = set(re.findall(r"^def (check_\w+)\(", source, re.MULTILINE))
    m = re.search(r"CHECKS\s*=\s*\[(.*?)\]", source, re.DOTALL)
    registered = set(re.findall(r"(check_\w+)", m.group(1))) if m else set()
    return defined, registered


def evaluate_domain(entry, verify_source):
    defined_checks, registered_list = registered_checks(verify_source)
    reasons = []
    achieved = "M0"

    builder_ok = os.path.exists(os.path.join(REPO_ROOT, entry["builder"]))
    if not builder_ok:
        reasons.append(f"builder missing: {entry['builder']}")

    template_paths = [
        os.path.join(REPO_ROOT, folder, entry["workbook_template"])
        for folder in entry["folders"]
    ]
    template_ok = builder_ok and any(os.path.exists(p) for p in template_paths)
    if builder_ok and not template_ok:
        reasons.append(f"no workbook template found in {entry['folders']}")

    if not (builder_ok and template_ok):
        return achieved, reasons
    achieved = "M1"

    checks = entry.get("reference_checks", [])
    checks_ok = len(checks) > 0
    for name in checks:
        if name not in defined_checks:
            checks_ok = False
            reasons.append(f"reference check '{name}' not defined in verify_reference_calcs.py")
        elif name not in registered_list:
            checks_ok = False
            reasons.append(f"reference check '{name}' defined but not registered in CHECKS list")
    if not checks:
        reasons.append("no reference_checks listed (M2 requires >=1 independent-oracle check)")
    if not checks_ok:
        return achieved, reasons
    achieved = "M2"

    existing_template = next((p for p in template_paths if os.path.exists(p)), None)
    sheets_ok = False
    if existing_template:
        try:
            import openpyxl
            wb = openpyxl.load_workbook(existing_template, read_only=True)
            names = set(wb.sheetnames)
            sheets_ok = "Sources" in names and "Checks" in names
            if not sheets_ok:
                missing = {"Sources", "Checks"} - names
                reasons.append(f"workbook missing sheet(s): {sorted(missing)}")
        except Exception as e:  # noqa: BLE001
            reasons.append(f"could not open workbook to check sheets: {e}")

    primary_folder = os.path.join(REPO_ROOT, entry["folders"][0])
    card_ok = os.path.exists(os.path.join(primary_folder, "model_card.md"))
    validation_ok = os.path.exists(os.path.join(primary_folder, "validation.md"))
    if not card_ok:
        reasons.append(f"missing {entry['folders'][0]}/model_card.md")
    if not validation_ok:
        reasons.append(f"missing {entry['folders'][0]}/validation.md")

    if not (sheets_ok and card_ok and validation_ok):
        return achieved, reasons
    achieved = "M3"

    instances = entry.get("instances", [])
    existing_instances = [i for i in instances if os.path.exists(os.path.join(REPO_ROOT, i))]
    if len(existing_instances) < 2:
        reasons.append(f"only {len(existing_instances)} populated instance(s) on disk, M4 requires >=2")
        return achieved, reasons
    achieved = "M4"

    return achieved, reasons


def main():
    with open(INVENTORY_PATH) as f:
        inventory = json.load(f)
    verify_source = load_verify_source()

    all_ok = True
    print(f"Validating {len(inventory['domains'])} domains against claimed maturity...\n")
    for entry in inventory["domains"]:
        claimed = entry["maturity"]
        achieved, reasons = evaluate_domain(entry, verify_source)
        overclaimed = MATURITY_RANK[claimed] > MATURITY_RANK[achieved]
        all_ok = all_ok and not overclaimed
        status = "FAIL" if overclaimed else "ok"
        print(f"[{status}] {entry['id']}: claimed={claimed} evidence-supports={achieved}")
        if overclaimed:
            for r in reasons:
                print(f"        - {r}")
        print()

    print("=" * 60)
    print("ALL CLAIMS SUPPORTED" if all_ok else "SOME CLAIMS OVERSTATE THE EVIDENCE")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
