# save_demo_cache.py
# A one-time script that records a real run for "Demo replay (no internet needed)".
# It reads OFFER 1 live with claude, then saves into data/demo_cache/:
#   offer1_result.json   claude's real reading of OFFER 1
#   offer1_summary.wav   the voice for "Listen to the result"
#   read_<product>.wav   the voice for each product card's "Read aloud"
#   welcome.wav          the voice for "Hear this page" on Welcome
#   speech_index.json    which words each .wav file says
#
# Run it once, with the internet on, from the project folder:
#   python save_demo_cache.py
# It uses API credits: one claude call and about 14 short Cartesia calls.
# Keys are read only from .streamlit/secrets.toml (through st.secrets).
# (Streamlit may print "No runtime found" warnings. That is normal here.)

import datetime
import os
import sys

# st.secrets looks for .streamlit/secrets.toml in the folder we run from,
# so we always run from the project folder.
PROJECT_FOLDER = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_FOLDER)

from checks import apply_guards, quote_check_counts, verify_quotes
from claude_helper import MODEL, read_offer
from demo_replay import (
    CACHE_FOLDER,
    OFFER_AUDIO_NAME,
    REPLAY_OFFER,
    banner_text,
    save_result,
    save_speech_index,
    save_wav,
)
from products import PRODUCTS
from results import card_words, offer_words, score_offer
from scoring import assign_tier, tier_label
from voice_helper import DEFAULT_SPEED, get_speech
from welcome import WELCOME_WORDS

SAMPLE_OFFERS_FILE = os.path.join(PROJECT_FOLDER, "data", "sample_offers.md")


def load_offer_one():
    """OFFER 1's text from data/sample_offers.md, read the same way app.py does.
    None if the file or the offer is missing."""
    try:
        with open(SAMPLE_OFFERS_FILE, encoding="utf-8") as file:
            text = file.read()
    except OSError:
        return None
    for part in text.split("## OFFER ")[1:]:
        number, _, body = part.partition("\n")
        if f"OFFER {number.strip()}" == REPLAY_OFFER:
            return body.strip()
    return None


def save_voice(file_name, words, files):
    """Ask Cartesia to speak these words, then save the recording.
    Adds the file to the list and returns True when it works."""
    audio, error = get_speech(words, DEFAULT_SPEED)
    if error:
        print(f"  Skipped {file_name}: {error}")
        return False
    save_wav(file_name, audio)
    files[file_name] = words
    print(f"  Saved {file_name}")
    return True


def main():
    """Record the run. Returns 0 if everything was saved, 1 if not."""
    print("Step 1 of 4: reading OFFER 1 from data/sample_offers.md")
    offer_text = load_offer_one()
    if not offer_text:
        print("  Stopped: OFFER 1 was not found in data/sample_offers.md.")
        return 1

    print("Step 2 of 4: asking claude to read OFFER 1 (live)...")
    product_names = [product["name"] for product in PRODUCTS]
    answer, error = read_offer(offer_text, product_names)
    if error:
        print(f"  Stopped: {error}")
        return 1

    # The same safety checks and scoring the app uses, so we can show the result.
    guarded = apply_guards(verify_quotes(offer_text, answer))
    result = score_offer(guarded)[0]
    found, not_found = quote_check_counts(guarded)
    print(f"  Label from scoring.py: {tier_label(result['tier'])}")
    print(f"  Quotes found in the offer: {found}. Not found: {not_found}.")
    if not_found:
        print("  (That's fine: the app shows those as unknown, live or in replay.)")

    # We save claude's answer exactly as it came back.
    # The app checks its quotes and picks the label again every time it is replayed.
    now = datetime.datetime.now()
    record = {
        "_about": (
            "A real, live run of the FICTIONAL sample OFFER 1, saved by "
            "save_demo_cache.py for Demo replay. Not real personal data."
        ),
        "recorded_on": now.date().isoformat(),
        "recorded_at": now.strftime("%Y-%m-%d %H:%M"),
        "model": MODEL,
        "offer_name": REPLAY_OFFER,
        "offer_text": offer_text,
        "answer": answer,
    }
    save_result(record)
    print("  Saved offer1_result.json")

    files = {}  # file name: the exact words it says
    all_saved = True

    print("Step 3 of 4: saving the voice for Listen to the result...")
    all_saved &= save_voice(OFFER_AUDIO_NAME, offer_words(guarded, result), files)

    print("Step 4 of 4: saving the voice for every Read aloud button...")
    for product in PRODUCTS:
        words = card_words(product, assign_tier(product))
        all_saved &= save_voice(f"read_{product['key']}.wav", words, files)
    all_saved &= save_voice("welcome.wav", WELCOME_WORDS, files)

    save_speech_index(files, DEFAULT_SPEED)
    print("  Saved speech_index.json")

    print("\nDone. Everything is in:", CACHE_FOLDER)
    print(f"The banner will say: {banner_text(record)}")
    if not all_saved:
        print("Some voices were skipped (see above). Fix the problem and run this again.")
        return 1
    print("Next: run  python tests\\check_replay.py  to check the saved files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())