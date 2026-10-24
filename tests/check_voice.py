# tests/check_voice.py
# Checks voice_helper.py WITHOUT calling Cartesia (no credits used, no internet needed).
# Run from the project folder:  python tests\check_voice.py
# (Streamlit may print a "No runtime found" warning. That is normal here.)

import os
import sys

# Let Python find voice_helper.py in the project folder.
PROJECT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_FOLDER)

import voice_helper
from voice_helper import (
    LISTEN_NOTHING_HEARD,
    LISTEN_TROUBLE,
    SPEEDS,
    VOICE_TROUBLE,
    dollars_in_words,
    get_speech,
    get_transcript,
)

results = []  # One True (pass) or False (fail) per check.


def check(description, actual, expected):
    """Print PASS or FAIL for one check and remember the result."""
    if actual == expected:
        print(f"PASS  {description}")
        results.append(True)
    else:
        print(f"FAIL  {description}: got {actual!r}, expected {expected!r}")
        results.append(False)


# ---------- Part 1: numbers said as words ----------
print("=" * 60)
print("DOLLARS IN WORDS")
print("=" * 60)
check("10,000", dollars_in_words(10000), "ten thousand dollars")
check("5,620 (S&P 500 worst year)", dollars_in_words(5620), "five thousand six hundred twenty dollars")
check("7,790 (balanced fund worst year)", dollars_in_words(7790), "seven thousand seven hundred ninety dollars")
check("8,700 (bond fund worst year)", dollars_in_words(8700), "eight thousand seven hundred dollars")
check("2,700 (Bitcoin worst year)", dollars_in_words(2700), "two thousand seven hundred dollars")
check("0 (one stock can go to zero)", dollars_in_words(0), "zero dollars")
check("1", dollars_in_words(1), "one dollar")
check("21", dollars_in_words(21), "twenty-one dollars")
check("105", dollars_in_words(105), "one hundred five dollars")

# ---------- Part 2: speed settings ----------
print("\n" + "=" * 60)
print("VOICE SPEEDS")
print("=" * 60)
for name, value in SPEEDS.items():
    check(f"{name} speed {value} is between 0.6 and 1.5", 0.6 <= value <= 1.5, True)
check("Slower is slower than Normal", SPEEDS["Slower"] < SPEEDS["Normal"], True)

# ---------- Part 3: problems give calm messages, never a crash ----------
print("\n" + "=" * 60)
print("CALM MESSAGES")
print("=" * 60)


def pretend_trouble(*args, **kwargs):
    """Acts like Cartesia when the internet is down."""
    raise RuntimeError("pretend network trouble")


class PretendRecording:
    """Acts like a recording from st.audio_input."""
    def getvalue(self):
        return b"not really audio"


# Pretend the keys are filled in, and that Cartesia always fails.
voice_helper.has_secret = lambda name: True
voice_helper.speak = pretend_trouble
voice_helper.listen = pretend_trouble

check("Empty words give a calm message", get_speech("   "), (None, VOICE_TROUBLE))
check("Cartesia trouble while speaking gives a calm message",
      get_speech("Safe Harbor."), (None, VOICE_TROUBLE))
check("No recording gives a calm message", get_transcript(None), (None, LISTEN_NOTHING_HEARD))
check("Cartesia trouble while listening gives a calm message",
      get_transcript(PretendRecording()), (None, LISTEN_TROUBLE))

# Cartesia worked but heard nothing.
voice_helper.listen = lambda audio_file: ""
check("A silent recording asks to try again",
      get_transcript(PretendRecording()), (None, LISTEN_NOTHING_HEARD))

# Cartesia worked and heard words.
voice_helper.listen = lambda audio_file: "It pays guaranteed 12% a year."
check("Words heard are returned",
      get_transcript(PretendRecording()), ("It pays guaranteed 12% a year.", None))

# ---------- Total ----------
passed = results.count(True)
failed = results.count(False)
print("\n" + "=" * 60)
print(f"TOTAL: {passed} passed, {failed} failed, out of {len(results)} checks")
print("=" * 60)

# Exit with an error code if anything failed.
if failed > 0:
    sys.exit(1)