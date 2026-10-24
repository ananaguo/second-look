# tests/check_safety.py
# Checks that checks.py (the safety layer) gives the results we expect.
# Run from the project folder:  python tests\check_safety.py

import copy
import json
import os
import sys

# Let Python find checks.py and products.py in the project folder.
PROJECT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_FOLDER)

from checks import (
    FOUND_TAG,
    GOV_CLAIM_WARNING,
    NOT_FOUND_TAG,
    SAFE_SENTENCE,
    apply_guards,
    clean_summary,
    quote_check_counts,
    quote_in_offer,
    verify_quotes,
)

OFFERS_FILE = os.path.join(PROJECT_FOLDER, "data", "sample_offers.md")
ANSWERS_FILE = os.path.join(PROJECT_FOLDER, "data", "sample_answers.json")

results = []  # One True (pass) or False (fail) per check.


def check(description, actual, expected):
    """Print PASS or FAIL for one check and remember the result."""
    if actual == expected:
        print(f"PASS  {description}")
        results.append(True)
    else:
        print(f"FAIL  {description}: got {actual!r}, expected {expected!r}")
        results.append(False)


def load_offers():
    """Read OFFER 1 to 6 from the sample file, the same way app.py does."""
    with open(OFFERS_FILE, encoding="utf-8") as file:
        text = file.read()
    offers = {}
    for part in text.split("## OFFER ")[1:]:
        number, _, body = part.partition("\n")
        offers[f"OFFER {number.strip()}"] = body.strip()
    return offers


offers = load_offers()
with open(ANSWERS_FILE, encoding="utf-8") as file:
    answers = json.load(file)

# ---------- Part 1: how quotes are matched ----------
print("=" * 60)
print("MATCHING QUOTES")
print("=" * 60)
check("Capitals are ignored",
      quote_in_offer("OUR PROGRAM PAYS", "Our program pays 12%"), True)
check("Extra spaces and new lines are ignored",
      quote_in_offer("our   program\n pays", "Our program pays 12%"), True)
check("Curly apostrophe matches a straight one",
      quote_in_offer("90 days’ interest", "a penalty of 90 days' interest applies"), True)
check("Curly double quotes match straight ones",
      quote_in_offer('it is “no risk”', 'He said it is "no risk" today'), True)
check("Made-up words are not found",
      quote_in_offer("guaranteed 50%", "Our program pays 12%"), False)
check("An empty quote is not found",
      quote_in_offer("", "Our program pays 12%"), False)

# ---------- Part 2: the six sample offers ----------
print("\n" + "=" * 60)
print("SAMPLE OFFERS")
print("=" * 60)
# (not rated, government-claim warning, scam card) for each offer
EXPECTED_GUARDS = {
    "OFFER 1": (False, False, True),
    "OFFER 2": (False, False, False),
    "OFFER 3": (True, False, True),
    "OFFER 4": (False, False, False),
    "OFFER 5": (False, False, True),
    "OFFER 6": (True, False, True),
}
for name, expected in EXPECTED_GUARDS.items():
    checked = verify_quotes(offers[name], answers[name])
    found, not_found = quote_check_counts(checked)
    check(f"{name}: every quote found ({found} found)", not_found, 0)
    guards = apply_guards(checked)["guards"]
    actual = (guards["not_rated"], guards["gov_claim_warning"], guards["show_scam_card"])
    check(f"{name}: not rated, insurance warning, scam card", actual, expected)

# Offer 6 says "a safe investment" in its summary, so that sentence is replaced.
guarded6 = apply_guards(verify_quotes(offers["OFFER 6"], answers["OFFER 6"]))
check("OFFER 6: summary now has the safe sentence",
      SAFE_SENTENCE in guarded6["plain_summary"], True)
check("OFFER 6: summary no longer says 'safe investment'",
      "safe investment" in guarded6["plain_summary"], False)
check("OFFER 6: summary_changed is True", guarded6["guards"]["summary_changed"], True)

guarded2 = apply_guards(verify_quotes(offers["OFFER 2"], answers["OFFER 2"]))
check("OFFER 2: summary is unchanged",
      guarded2["plain_summary"], answers["OFFER 2"]["plain_summary"])

# ---------- Part 3: words that aren't in the offer ----------
print("\n" + "=" * 60)
print("MADE-UP QUOTES")
print("=" * 60)
fake = copy.deepcopy(answers["OFFER 2"])
fake["government_backed"]["quote"] = "backed by the full faith and credit of the U.S. government"
checked = verify_quotes(offers["OFFER 2"], fake)
check("Made-up quote gets the not-found tag", checked["government_backed"]["check"], NOT_FOUND_TAG)
check("...and its answer becomes unknown", checked["government_backed"]["value"], "unknown")
check("...and its quote becomes unknown", checked["government_backed"]["quote"], "unknown")
check("The original answer was not changed", fake["government_backed"]["value"], "yes")
check("A real quote next to it is still found", checked["access"]["check"], FOUND_TAG)

fake_flag = copy.deepcopy(answers["OFFER 2"])
fake_flag["red_flags"] = [{"flag": "Pressure to decide quickly", "quote": "act now or lose out"}]
guarded = apply_guards(verify_quotes(offers["OFFER 2"], fake_flag))
check("A red flag with made-up words doesn't count", guarded["guards"]["show_scam_card"], False)
check("...but it is kept, with the not-found tag", guarded["red_flags"][0]["check"], NOT_FOUND_TAG)

fake_category = copy.deepcopy(answers["OFFER 2"])
fake_category["category"] = "Magic money box"
checked = verify_quotes(offers["OFFER 2"], fake_category)
check("A category not on our list becomes unknown", checked["category"], "unknown")
check("...so the offer is not rated", apply_guards(checked)["guards"]["not_rated"], True)

# ---------- Part 4: false government-insurance claims ----------
print("\n" + "=" * 60)
print("FALSE INSURANCE CLAIMS")
print("=" * 60)
# A made-up version of Offer 4 that wrongly says it is FDIC insured.
claim_text = offers["OFFER 4"] + "\n\nYour money is insured by the FDIC."
claim = copy.deepcopy(answers["OFFER 4"])
claim["government_backed"] = {"value": "yes", "quote": "Your money is insured by the FDIC"}
guarded = apply_guards(verify_quotes(claim_text, claim))
check("Fixed annuity claiming FDIC gets the warning", guarded["guards"]["gov_claim_warning"], True)
check("...as the first red flag", guarded["red_flags"][0]["flag"], GOV_CLAIM_WARNING)
check("...and the scam card shows", guarded["guards"]["show_scam_card"], True)

# The same claim, but the words aren't really in the offer: no warning.
guarded = apply_guards(verify_quotes(offers["OFFER 4"], claim))
check("Claim with made-up words gives no warning", guarded["guards"]["gov_claim_warning"], False)

# ---------- Part 5: advice words in the summary ----------
print("\n" + "=" * 60)
print("SUMMARY WORDS")
print("=" * 60)
check("'best' is replaced",
      clean_summary("This CD is the best choice. It pays 4% a year."),
      f"{SAFE_SENTENCE} It pays 4% a year.")
check("Two advice sentences give one safe sentence",
      clean_summary("You could buy it today. It is recommended. It pays 4%."),
      f"{SAFE_SENTENCE} It pays 4%.")
check("'U.S.' doesn't split a sentence",
      clean_summary("It is backed by the U.S. government. It pays 4%."),
      "It is backed by the U.S. government. It pays 4%.")
check("'buyers' is a different word, so it stays",
      clean_summary("Older buyers get 30 days."), "Older buyers get 30 days.")
check("'unsafe investment' is not 'safe investment'",
      clean_summary("He calls it an unsafe investment."), "He calls it an unsafe investment.")

# ---------- Total ----------
passed = results.count(True)
failed = results.count(False)
print("\n" + "=" * 60)
print(f"TOTAL: {passed} passed, {failed} failed, out of {len(results)} checks")
print("=" * 60)

# Exit with an error code if anything failed.
if failed > 0:
    sys.exit(1)