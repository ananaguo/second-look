# tests/check_replay.py
# Checks the saved run for Demo replay in data/demo_cache/.
# It doesn't call Claude or Cartesia (no credits used, no internet needed).
# Run from the project folder:  python tests\check_replay.py
# Run it after save_demo_cache.py, and again after you edit products.py,
# because a saved voice only plays when its words still match exactly.
# (Streamlit may print a "No runtime found" warning. That is normal here.)

import os
import sys

# Let Python find the project's files in the project folder.
PROJECT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_FOLDER)

from checks import apply_guards, quote_check_counts, verify_quotes
from claude_helper import EXPECTED_KEYS
from demo_replay import (
    OFFER_AUDIO_NAME,
    REPLAY_OFFER,
    banner_text,
    load_replay,
    load_speech_index,
    recorded_day,
    saved_audio,
)
from products import PRODUCTS
from results import card_words, offer_words, score_offer
from scoring import assign_tier, tier_label
from welcome import WELCOME_WORDS

OFFERS_FILE = os.path.join(PROJECT_FOLDER, "data", "sample_offers.md")
RERUN_HINT = (
    "If a saved voice doesn't match, its words changed after recording "
    "(for example in products.py). Run  python save_demo_cache.py  again."
)

results = []  # One True (pass) or False (fail) per check.


def check(description, ok):
    """Print PASS or FAIL for one check and remember the result."""
    print(f"{'PASS' if ok else 'FAIL'}  {description}")
    results.append(ok)


def finish():
    """Print the total and stop, with an error code if anything failed."""
    passed = results.count(True)
    failed = results.count(False)
    print("\n" + "=" * 60)
    print(f"TOTAL: {passed} passed, {failed} failed, out of {len(results)} checks")
    print("=" * 60)
    if failed > 0:
        print(RERUN_HINT)
        sys.exit(1)
    sys.exit(0)


def load_offers():
    """Read OFFER 1 to 6 from the sample file, the same way app.py does."""
    with open(OFFERS_FILE, encoding="utf-8") as file:
        text = file.read()
    offers = {}
    for part in text.split("## OFFER ")[1:]:
        number, _, body = part.partition("\n")
        offers[f"OFFER {number.strip()}"] = body.strip()
    return offers


# ---------- Part 1: the banner words (no files needed) ----------
print("=" * 60)
print("BANNER")
print("=" * 60)
check("A run saved on Saturday, October 24, 2026 gives the exact banner",
      banner_text({"recorded_on": "2026-10-24"})
      == "Replay of a real run recorded Saturday. Live mode is off.")
check("A missing date says 'earlier' instead of guessing a day",
      recorded_day({}) == "earlier")

# ---------- Part 2: the saved result ----------
print("\n" + "=" * 60)
print("SAVED RESULT")
print("=" * 60)
saved = load_replay()
check("offer1_result.json is there and readable", saved is not None)
if saved is None:
    print("\nNo saved run yet. With the internet on, run:  python save_demo_cache.py")
    finish()

answer = saved["answer"]
missing = [key for key in EXPECTED_KEYS if key not in answer]
check(f"the saved answer has every key Claude should send (missing: {missing or 'none'})",
      not missing)
check("the saved offer text still matches OFFER 1 in data/sample_offers.md",
      saved["offer_text"].strip() == load_offers().get(REPLAY_OFFER, "").strip())

# The same steps the app runs on a replay: check quotes, guards, then scoring.py.
guarded = apply_guards(verify_quotes(saved["offer_text"], answer))
result = score_offer(guarded)[0]
found, not_found = quote_check_counts(guarded)
print(f"      Banner: {banner_text(saved)}")
print(f"      Label from scoring.py: {tier_label(result['tier'])}")
print(f"      Quotes found: {found}. Not found: {not_found}.")
check("at least one of Claude's quotes was found in the offer", found > 0)

# ---------- Part 3: the saved voices ----------
print("\n" + "=" * 60)
print("SAVED VOICES")
print("=" * 60)
files = load_speech_index()["files"]
check(f"speech_index.json lists {len(files)} saved voices", len(files) > 0)
check(f"{OFFER_AUDIO_NAME} is on the list", OFFER_AUDIO_NAME in files)

offer_audio = saved_audio(offer_words(guarded, result))
check("Listen to the result: the saved voice matches today's words", offer_audio is not None)
if offer_audio:
    check("  ...and it is a WAV file", offer_audio[:4] == b"RIFF")

for product in PRODUCTS:
    audio = saved_audio(card_words(product, assign_tier(product)))
    check(f"Read aloud, {product['name']}: the saved voice matches", audio is not None)

check("Hear this page (Welcome): the saved voice matches", saved_audio(WELCOME_WORDS) is not None)
check("Words that were never saved get no voice",
      saved_audio("These words were never saved.") is None)

finish()