# tests/check_scoring.py
# Checks that scoring.py gives the results we expect.
# Run from the project folder:  python tests\check_scoring.py

import os
import sys

# Let Python find products.py and scoring.py in the project folder.
PROJECT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_FOLDER)

from products import PRODUCTS
from scoring import (
    DROP_SELL,
    GOAL_SAFE,
    NEED_1_TO_5_YEARS,
    NEED_WITHIN_1_YEAR,
    NOTE_LOCKED,
    NOTE_NEED_SOON,
    NOTE_SAFE_GOAL,
    NOTE_WOULD_SELL,
    assign_tier,
    fit_notes,
    tier_label,
)

results = []  # One True (pass) or False (fail) per check.


def check(description, actual, expected):
    """Print PASS or FAIL for one check and remember the result."""
    if actual == expected:
        print(f"PASS  {description}: {actual}")
        results.append(True)
    else:
        print(f"FAIL  {description}: got {actual}, expected {expected}")
        results.append(False)


def find_product(key):
    """Find the product with this key in products.py. None if it is missing."""
    for product in PRODUCTS:
        if product["key"] == key:
            return product
    return None


def make_product(backed=False, worst=0, protections=True):
    """A pretend product for edge-case tests. Not real data."""
    return {
        "key": "test",
        "name": "Test product",
        "one_line": "",
        "government_backed": backed,
        "worst_year_loss_pct": worst,
        "worst_year": "test",
        "protections": protections,
        "access": "anytime",
        "access_note": "",
        "yearly_cost_pct": 0,
        "sales_or_surrender_charge": False,
        "cost_note": "",
        "gain_note": "",
        "insurance_note": "",
        "sources": [],
    }


def make_answers(need="Not for 5 years or more", drop="Stay calm", goal="Grow it over many years"):
    """Pretend answers from the Your situation page (Rosa-style, not real data).
    The defaults are answers that match none of the four rules."""
    return {
        "age": "70–74",
        "income": "Prefer not to say",
        "need": need,
        "drop": drop,
        "goal": goal,
    }


# ---------- Part 1: show every product's result ----------
print("=" * 60)
print("EVERY PRODUCT")
print("=" * 60)
for product in PRODUCTS:
    result = assign_tier(product)
    print(f"\n{product['name']} ({product['key']})")
    print(f"  Tier: {tier_label(result['tier'])}")
    print(f"  Access: {result['access_badge']}   Cost: {result['cost_badge']}")
    print(f"  Worst case on $10,000: {result['worst_case_dollars']}")
    for step in result["steps"]:
        print(f"    {step}")

# ---------- Part 2: expected results ----------
EXPECTED = {
    "savings": ("Safe Harbor", "Anytime", "Low"),
    "cd12": ("Safe Harbor", "Small penalty", "Low"),
    "tbill": ("Safe Harbor", "Anytime", "Low"),
    "ibond": ("Safe Harbor", "Small penalty", "Low"),
    "mmfund": ("Calm Bay", "Anytime", "Varies"),
    "fixedannuity": ("Calm Bay", "Locked for years", "High"),
    "bondindex": ("Coastal Waters", "Anytime", "Low"),
    "balanced": ("Coastal Waters", "Anytime", "Low"),
    "sp500": ("Open Sea", "Anytime", "Low"),
    "variableannuity": ("Open Sea", "Locked for years", "High"),
    "singlestock": ("Storm Waters", "Anytime", "Low"),
    "bitcoin": ("Uncharted Waters", "Anytime", "Varies"),
}

print("\n" + "=" * 60)
print("EXPECTED RESULTS")
print("=" * 60)
for key, expected in EXPECTED.items():
    found = find_product(key)
    if found is None:
        check(key, "missing from PRODUCTS", expected)
        continue
    result = assign_tier(found)
    actual = (tier_label(result["tier"]), result["access_badge"], result["cost_badge"])
    check(key, actual, expected)

# ---------- Part 3: edge cases ----------
print("\n" + "=" * 60)
print("EDGE CASES")
print("=" * 60)
edge_cases = [
    ("Worst year 10 gives Calm Bay",
     assign_tier(make_product(worst=10)), 2),
    ("Worst year 10.1 gives Coastal Waters",
     assign_tier(make_product(worst=10.1)), 3),
    ("Worst year 25 gives Coastal Waters",
     assign_tier(make_product(worst=25)), 3),
    ("Worst year 50 gives Open Sea",
     assign_tier(make_product(worst=50)), 4),
    ("Worst year 51 with protections gives Storm Waters",
     assign_tier(make_product(worst=51, protections=True)), 5),
    ("Worst year 51 without protections gives Uncharted Waters",
     assign_tier(make_product(worst=51, protections=False)), 6),
    ("government_backed None gives not_rated",
     assign_tier(make_product(backed=None, worst=None)), "not_rated"),
    ("Guaranteed 12% when T-bills are 4.1% gives off_map",
     assign_tier(make_product(worst=0), tbill_rate_pct=4.1,
                 promised_return_pct=12, guaranteed=True), "off_map"),
]
for description, result, expected_tier in edge_cases:
    check(description, result["tier"], expected_tier)

# ---------- Part 4: fit notes ----------
print("\n" + "=" * 60)
print("FIT NOTES")
print("=" * 60)
all_rules = make_answers(need=NEED_WITHIN_1_YEAR, drop=DROP_SELL, goal=GOAL_SAFE)
fit_cases = [
    ("No answers gives no notes",
     fit_notes(find_product("sp500"), None), []),
    ("Calm answers give no notes, even on Bitcoin",
     fit_notes(find_product("bitcoin"), make_answers()), []),
    ("Need within 1 year, Safe Harbor savings: no notes",
     fit_notes(find_product("savings"), make_answers(need=NEED_WITHIN_1_YEAR)), []),
    ("Need within 1 year, Calm Bay money market fund: no notes",
     fit_notes(find_product("mmfund"), make_answers(need=NEED_WITHIN_1_YEAR)), []),
    ("Need within 1 year, Coastal Waters bond fund",
     fit_notes(find_product("bondindex"), make_answers(need=NEED_WITHIN_1_YEAR)), [NOTE_NEED_SOON]),
    ("Need in 1 to 5 years, locked fixed annuity",
     fit_notes(find_product("fixedannuity"), make_answers(need=NEED_1_TO_5_YEARS)), [NOTE_LOCKED]),
    ("Need within 1 year, locked fixed annuity (Calm Bay, so only the locked note)",
     fit_notes(find_product("fixedannuity"), make_answers(need=NEED_WITHIN_1_YEAR)), [NOTE_LOCKED]),
    ("Would sell, Coastal Waters balanced fund: no notes",
     fit_notes(find_product("balanced"), make_answers(drop=DROP_SELL)), []),
    ("Would sell, Open Sea S&P 500 fund",
     fit_notes(find_product("sp500"), make_answers(drop=DROP_SELL)), [NOTE_WOULD_SELL]),
    ("Goal keep it safe, Calm Bay money market fund: no notes",
     fit_notes(find_product("mmfund"), make_answers(goal=GOAL_SAFE)), []),
    ("Goal keep it safe, Coastal Waters bond fund",
     fit_notes(find_product("bondindex"), make_answers(goal=GOAL_SAFE)), [NOTE_SAFE_GOAL]),
    ("All four rules match on the variable annuity",
     fit_notes(find_product("variableannuity"), all_rules),
     [NOTE_NEED_SOON, NOTE_LOCKED, NOTE_WOULD_SELL, NOTE_SAFE_GOAL]),
    ("Not rated product gets no tier notes",
     fit_notes(make_product(backed=None, worst=None), all_rules), []),
]
for description, actual, expected in fit_cases:
    check(description, actual, expected)

# ---------- Total ----------
passed = results.count(True)
failed = results.count(False)
print("\n" + "=" * 60)
print(f"TOTAL: {passed} passed, {failed} failed, out of {len(results)} checks")
print("=" * 60)

# Exit with an error code if anything failed.
if failed > 0:
    sys.exit(1)