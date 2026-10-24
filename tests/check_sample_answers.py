# tests/check_sample_answers.py
# Checks the hand-written demo readings in data/sample_answers.json.
# Every quote must appear word for word in data/sample_offers.md.
# Run from the project folder:  python tests\check_sample_answers.py

import json
import os
import sys

# Let Python find products.py in the project folder.
PROJECT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_FOLDER)

from products import PRODUCTS

OFFERS_FILE = os.path.join(PROJECT_FOLDER, "data", "sample_offers.md")
ANSWERS_FILE = os.path.join(PROJECT_FOLDER, "data", "sample_answers.json")

# The five facts that each have a quote.
FACT_KEYS = ["government_backed", "loss_possible", "access", "yearly_costs", "promised_return"]

results = []  # One True (pass) or False (fail) per check.


def check(description, ok):
    """Print PASS or FAIL for one check and remember the result."""
    print(f"{'PASS' if ok else 'FAIL'}  {description}")
    results.append(ok)


def load_offers():
    """Read OFFER 1 to 6 from the sample file, the same way app.py does."""
    with open(OFFERS_FILE, encoding="utf-8") as file:
        text = file.read()
    offers = {}
    for part in text.split("## OFFER ")[1:]:
        number, _, body = part.partition("\n")
        offers[f"OFFER {number.strip()}"] = body.strip()
    return offers


def is_real_quote(quote):
    """True if this is a real quote, not empty and not "unknown"."""
    return isinstance(quote, str) and quote.strip().lower() not in ("", "unknown")


offers = load_offers()
with open(ANSWERS_FILE, encoding="utf-8") as file:
    answers = json.load(file)

product_names = [product["name"] for product in PRODUCTS]

for name, offer_text in offers.items():
    print("\n" + "=" * 60)
    print(name)
    print("=" * 60)

    answer = answers.get(name)
    check("has a saved reading", answer is not None)
    if answer is None:
        continue

    # The category must be a real product name, or "unknown".
    category = answer["category"]
    check(f"category is on the list or unknown: {category}",
          category in product_names or category == "unknown")

    # Every real quote must be in the offer, and 25 words or fewer.
    quotes = [answer[key]["quote"] for key in FACT_KEYS]
    quotes += [flag["quote"] for flag in answer["red_flags"]]
    for quote in quotes:
        if is_real_quote(quote):
            check(f'quote is in the offer: "{quote}"', quote in offer_text)
            check(f"  ...and is {len(quote.split())} words (25 or fewer)", len(quote.split()) <= 25)

    # Lengths from the prompt's rules.
    count = len(answer["questions_to_ask"])
    check(f"{count} questions to ask (3 to 5)", 3 <= count <= 5)
    plain = len(answer["plain_summary"].split())
    check(f"plain summary is {plain} words (under 80)", plain < 80)
    spoken = len(answer["spoken_summary"].split())
    check(f"spoken summary is {spoken} words (under 60)", spoken < 60)

# ---------- Total ----------
passed = results.count(True)
failed = results.count(False)
print("\n" + "=" * 60)
print(f"TOTAL: {passed} passed, {failed} failed, out of {len(results)} checks")
print("=" * 60)

# Exit with an error code if anything failed.
if failed > 0:
    sys.exit(1)