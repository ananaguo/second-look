# demo_replay.py
# The files behind "Demo replay (no internet needed)".
# save_demo_cache.py records one real run into data/demo_cache/.
# When Demo replay is on, app.py plays that run back from these files,
# so it never needs Claude, Cartesia or the internet.
# This file only reads and writes files. It never calls Claude or Cartesia,
# and it never picks a tier (scoring.py always does that).

import datetime
import json
import os

# ---------- Where the saved run lives ----------
PROJECT_FOLDER = os.path.dirname(os.path.abspath(__file__))
CACHE_FOLDER = os.path.join(PROJECT_FOLDER, "data", "demo_cache")

# The sample offer that gets a real, saved run
REPLAY_OFFER = "OFFER 1"

# Claude's real reading of OFFER 1
RESULT_FILE = os.path.join(CACHE_FOLDER, "offer1_result.json")

# The voice for "Listen to the result" on OFFER 1
OFFER_AUDIO_NAME = "offer1_summary.wav"

# A list of which words each saved .wav file says
SPEECH_INDEX_FILE = os.path.join(CACHE_FOLDER, "speech_index.json")

# Words for dates, so the banner can say "recorded Saturday"
DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
UNKNOWN_DAY = "earlier"  # used if the saved date is missing


# ---------- Small helpers ----------

def read_json(path):
    """Read a JSON file. Returns a dictionary, or None if it is missing or broken."""
    try:
        with open(path, encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def write_json(path, data):
    """Write a dictionary to a JSON file, making the folder if needed."""
    os.makedirs(CACHE_FOLDER, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def same_words(text):
    """Words made easy to compare: single spaces, no spaces at the ends."""
    return " ".join(str(text).split())


# ---------- Reading the saved run (used by app.py) ----------

def load_replay():
    """The saved run of OFFER 1, or None if it is missing or broken.
    It holds "offer_text" (the offer that was read) and "answer" (Claude's reading)."""
    saved = read_json(RESULT_FILE)
    if saved is None:
        return None
    if not isinstance(saved.get("answer"), dict) or not isinstance(saved.get("offer_text"), str):
        return None
    return saved


def recorded_date(saved):
    """The date the run was saved, or None if we can't tell."""
    if not isinstance(saved, dict):
        return None
    try:
        return datetime.date.fromisoformat(str(saved.get("recorded_on")))
    except ValueError:
        return None


def recorded_day(saved):
    """The day the run was saved, like "Saturday"."""
    date = recorded_date(saved)
    return DAY_NAMES[date.weekday()] if date else UNKNOWN_DAY


def recorded_date_words(saved):
    """The full date the run was saved, like "Saturday, October 24, 2026"."""
    date = recorded_date(saved)
    if date is None:
        return UNKNOWN_DAY
    return f"{DAY_NAMES[date.weekday()]}, {MONTH_NAMES[date.month - 1]} {date.day}, {date.year}"


def banner_text(saved):
    """The banner shown on every page while Demo replay is on.
    The day comes from the saved file, so the banner is always true."""
    return f"Replay of a real run recorded {recorded_day(saved)}. Live mode is off."


def load_speech_index():
    """The list of saved voices: {"speed": ..., "files": {file name: words}}.
    Empty if it is missing."""
    index = read_json(SPEECH_INDEX_FILE) or {}
    if not isinstance(index.get("files"), dict):
        index["files"] = {}
    return index


def saved_audio(words):
    """The saved voice for these exact words, as WAV bytes.
    None if no saved file says exactly these words. That way the voice
    always matches the captions, even if a product's words changed."""
    wanted = same_words(words)
    for file_name, saved_words in load_speech_index()["files"].items():
        if same_words(saved_words) == wanted:
            # basename keeps the file inside data/demo_cache, whatever the list says
            path = os.path.join(CACHE_FOLDER, os.path.basename(file_name))
            try:
                with open(path, "rb") as file:
                    return file.read() or None
            except OSError:
                return None
    return None


# ---------- Saving the run (used by save_demo_cache.py) ----------

def save_result(record):
    """Save Claude's reading of OFFER 1 to offer1_result.json."""
    write_json(RESULT_FILE, record)


def save_wav(file_name, audio):
    """Save one voice recording into data/demo_cache."""
    os.makedirs(CACHE_FOLDER, exist_ok=True)
    with open(os.path.join(CACHE_FOLDER, file_name), "wb") as file:
        file.write(audio)


def save_speech_index(files, speed):
    """Save the list of which words each .wav file says."""
    write_json(SPEECH_INDEX_FILE, {
        "_about": "Which words each saved voice file says. Written by save_demo_cache.py.",
        "speed": speed,
        "files": files,
    })