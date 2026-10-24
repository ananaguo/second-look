# tests/check_scoring.py
# Checks that scoring.py gives the results we expect.
# Run from the project folder:  python tests\check_scoring.py

import os
import sys

# Let Python find products.py and scoring.py in the project folder.
PROJECT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_FOLDER)

from products import PRODUCTS
from scoring import assign_tier, tier_label

results = []  # One True (pass) or False (fail) per check.


def check(description, actual, expected):
    """Print PASS or FAIL for one check and remember the result."""
    if actual == expected:
        print(f"PASS  {description}: {actual}")
        results.append(True)
    else:
        print(f"FAIL  {description}: got {actual}, expected {expected}")
        results.append(False)


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
    # Find the product with this key.
    found = None
    for product in PRODUCTS:
        if product["key"] == key:
            found = product
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

# ---------- Total ----------
passed = results.count(True)
failed = results.count(False)
print("\n" + "=" * 60)
print(f"TOTAL: {passed} passed, {failed} failed, out of {len(results)} checks")
print("=" * 60)

# Exit with an error code if anything failed.
if failed > 0:
    sys.exit(1)