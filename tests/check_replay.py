# tests/check_replay.py
# Checks the saved Demo replay files in data/demo_cache/.
# Run save_demo_cache.py first, then from the project folder:
#   python tests\check_replay.py
# This never calls grok or Cartesia. It only reads the saved files.

import os
import sys

# Let Python find the project's files, and run from the project folder.
PROJECT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_FOLDER)
os.chdir(PROJECT_FOLDER)

from checks import apply_guards, verify_quotes
from demo_replay import (
    CACHE_FOLDER,
    REPLAY_OFFER,
    RESULT_FILE,
    UNKNOWN_DAY,
    banner_text,
    load_replay,
    load_speech_index,
    recorded_day,
    saved_audio,
)
from products import PRODUCTS
from results import card_words, offer_words, score_offer
from scoring import assign_tier
from welcome import WELCOME_WORDS

OFFERS_FILE = os.path.join(PROJECT_FOLDER, "data", "sample_offers.md")

results = []  # One True (pass) or False (fail) per check.


def check(description, ok):
    """Print PASS or FAIL for one check and remember the result."""
    print(f"{'PASS' if ok else 'FAIL'}  {description}")
    results.append(bool(ok))


def load_offer_text(name):
    """One offer's text from data/sample_offers.md, read the same way app.py does."""
    try:
        with open(OFFERS_FILE, encoding="utf-8") as file:
            text = file.read()
    except OSError:
        return None
    for part in text.split("## OFFER ")[1:]:
        number, _, body = part.partition("\n")
        if f"OFFER {number.strip()}" == name:
            return body.strip()
    return None


print("=" * 60)
print("1. The saved reading of", REPLAY_OFFER)
print("=" * 60)
check("offer1_result.json exists", os.path.exists(RESULT_FILE))
saved = load_replay()
check("offer1_result.json can be read", saved is not None)

if saved is not None:
    check(f"the banner names a real day ({recorded_day(saved)})", recorded_day(saved) != UNKNOWN_DAY)
    print(f"      Banner: {banner_text(saved)}")

    # The app only uses the saved run when the words match OFFER 1 exactly.
    sample_text = load_offer_text(REPLAY_OFFER)
    check(
        f"the saved words still match {REPLAY_OFFER} in data/sample_offers.md",
        sample_text is not None and sample_text == saved["offer_text"].strip(),
    )

    # The same steps the app runs on a replay: check quotes, guards, then scoring.py.
    guarded = apply_guards(verify_quotes(saved["offer_text"], saved["answer"]))
    result = score_offer(guarded)[0]
    check("Listen to the result has a saved voice", saved_audio(offer_words(guarded, result)) is not None)

print("\n" + "=" * 60)
print("2. The saved voice files")
print("=" * 60)
index = load_speech_index()
check("speech_index.json lists some voices", bool(index["files"]))
for file_name in index["files"]:
    path = os.path.join(CACHE_FOLDER, os.path.basename(file_name))
    check(f"{file_name} exists and is not empty", os.path.exists(path) and os.path.getsize(path) > 0)

print("\n" + "=" * 60)
print("3. Every Read aloud button has its saved voice")
print("=" * 60)
for product in PRODUCTS:
    words = card_words(product, assign_tier(product))
    check(f"Read aloud: {product['name']}", saved_audio(words) is not None)
check("Hear this page (Welcome)", saved_audio(WELCOME_WORDS) is not None)

passed = sum(results)
print("\n" + "=" * 60)
print(f"{passed} of {len(results)} checks passed.")
if passed == len(results):
    print("All good. Demo replay is ready.")
else:
    print("Something is missing. Run  python save_demo_cache.py  again, then this test.")
sys.exit(0 if passed == len(results) else 1)