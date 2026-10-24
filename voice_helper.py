# voice_helper.py
# Every call to Cartesia (the voice service) lives here.
#   speak(text)        turns words into speech (WAV audio bytes).
#   listen(audio_file) turns a recording into words.
# app.py calls get_speech() and get_transcript(). They never crash:
# if anything goes wrong, they return a calm message instead.

import cartesia
import streamlit as st

# ---------- Settings ----------
TTS_MODEL = "sonic-3.6"     # the voice model that speaks
STT_MODEL = "ink-whisper"   # the model that listens
LANGUAGE = "en"

# WAV audio that every browser can play.
WAV_FORMAT = {"container": "wav", "encoding": "pcm_s16le", "sample_rate": 44100}

# Voice speeds. Sonic-3 models take generation_config["speed"],
# from 0.6 to 1.5, where 1.0 is normal (docs.cartesia.ai,
# "Volume, Speed, and Emotion").
SPEED_SLOWER = "Slower"
SPEED_NORMAL = "Normal"
SPEEDS = {SPEED_SLOWER: 0.85, SPEED_NORMAL: 1.0}
DEFAULT_SPEED = SPEED_SLOWER

# ---------- Calm messages (shown on the screen) ----------
VOICE_NO_KEY = (
    "The voice is turned off right now, but everything is still written on this page. "
    "(To turn it on, add CARTESIA_API_KEY and CARTESIA_VOICE_ID to .streamlit/secrets.toml.)"
)
VOICE_BAD_KEY = (
    "The voice isn't working right now, but everything is still written on this page. "
    "(Cartesia did not accept the key. Check CARTESIA_API_KEY in .streamlit/secrets.toml.)"
)
VOICE_BAD_SETTINGS = (
    "The voice isn't working right now, but everything is still written on this page. "
    "(Cartesia did not accept the request. Check CARTESIA_VOICE_ID in .streamlit/secrets.toml.)"
)
VOICE_TROUBLE = (
    "The voice isn't working right now, but everything is still written on this page. "
    "You can try again in a moment."
)
LISTEN_NO_KEY = (
    "Listening is turned off right now. You can still type or paste the offer in the box. "
    "(To turn it on, add CARTESIA_API_KEY to .streamlit/secrets.toml.)"
)
LISTEN_BAD_KEY = (
    "We couldn't listen to your recording just now. You can still type or paste the offer in the box. "
    "(Cartesia did not accept the key. Check CARTESIA_API_KEY in .streamlit/secrets.toml.)"
)
LISTEN_TROUBLE = (
    "We couldn't listen to your recording just now. "
    "You can try again, or type or paste the offer in the box."
)
LISTEN_NOTHING_HEARD = (
    "We couldn't hear any words in that recording. "
    "Please try again, a little closer to the microphone."
)


# ---------- Small helpers ----------

def has_secret(name):
    """True if this key is filled in .streamlit/secrets.toml."""
    try:
        return bool(str(st.secrets[name]).strip())
    except Exception:
        # No secrets file, or the key isn't in it.
        return False


# Words for numbers, so the voice and the captions say the same thing.
SMALL_NUMBERS = [
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
    "seventeen", "eighteen", "nineteen",
]
TENS_WORDS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]


def number_words(n):
    """A whole number from 0 to 999,999 in words, like 7790 → 'seven thousand seven hundred ninety'."""
    n = int(n)
    if n < 20:
        return SMALL_NUMBERS[n]
    if n < 100:
        tens, ones = divmod(n, 10)
        return TENS_WORDS[tens] if ones == 0 else f"{TENS_WORDS[tens]}-{SMALL_NUMBERS[ones]}"
    if n < 1000:
        hundreds, rest = divmod(n, 100)
        words = f"{SMALL_NUMBERS[hundreds]} hundred"
        return words if rest == 0 else f"{words} {number_words(rest)}"
    thousands, rest = divmod(n, 1000)
    words = f"{number_words(thousands)} thousand"
    return words if rest == 0 else f"{words} {number_words(rest)}"


def dollars_in_words(amount):
    """Dollars in words, like 5620 → 'five thousand six hundred twenty dollars'."""
    amount = max(0, int(round(amount)))
    return "one dollar" if amount == 1 else f"{number_words(amount)} dollars"


# ---------- Speaking (text to speech) ----------

@st.cache_data(show_spinner=False, max_entries=200)
def speak(text, speed=DEFAULT_SPEED):
    """Turn text into WAV audio bytes with Cartesia.
    Saved (cached), so the same words at the same speed are only paid for once.
    A failure is NOT saved: it raises an error, and get_speech() catches it."""
    client = cartesia.Cartesia(api_key=st.secrets["CARTESIA_API_KEY"])
    response = client.tts.generate(
        model_id=TTS_MODEL,
        transcript=text,
        voice=st.secrets["CARTESIA_VOICE_ID"],
        output_format=WAV_FORMAT,
        language=LANGUAGE,
        generation_config={"speed": SPEEDS.get(speed, SPEEDS[DEFAULT_SPEED])},
    )
    return response.read()


def get_speech(text, speed=DEFAULT_SPEED):
    """What app.py calls. Returns (audio bytes, None) when it works,
    or (None, calm message) when it doesn't."""
    if not isinstance(text, str) or not text.strip():
        return None, VOICE_TROUBLE
    if not (has_secret("CARTESIA_API_KEY") and has_secret("CARTESIA_VOICE_ID")):
        return None, VOICE_NO_KEY

    try:
        audio = speak(text, speed)
    except cartesia.AuthenticationError as error:
        print(f"Cartesia key problem: {error}")
        return None, VOICE_BAD_KEY
    except (cartesia.BadRequestError, cartesia.NotFoundError, cartesia.UnprocessableEntityError) as error:
        print(f"Cartesia did not accept the voice request: {error}")
        return None, VOICE_BAD_SETTINGS
    except Exception as error:
        # Anything else: no internet, Cartesia busy, and so on.
        print(f"Cartesia voice problem: {error}")
        return None, VOICE_TROUBLE

    if not audio:
        return None, VOICE_TROUBLE
    return audio, None


# ---------- Listening (speech to text) ----------

def listen(audio_file):
    """Turn a recording from st.audio_input into text with Cartesia.
    Raises an error if something goes wrong; get_transcript() catches it."""
    client = cartesia.Cartesia(api_key=st.secrets["CARTESIA_API_KEY"])
    result = client.stt.transcribe(
        # (file name, the recording's bytes, its type)
        file=("recording.wav", audio_file.getvalue(), "audio/wav"),
        model=STT_MODEL,
        language=LANGUAGE,
    )
    return (result.text or "").strip()


def get_transcript(audio_file):
    """What app.py calls. Returns (text, None) when it works,
    or (None, calm message) when it doesn't."""
    if audio_file is None:
        return None, LISTEN_NOTHING_HEARD
    if not has_secret("CARTESIA_API_KEY"):
        return None, LISTEN_NO_KEY

    try:
        text = listen(audio_file)
    except cartesia.AuthenticationError as error:
        print(f"Cartesia key problem: {error}")
        return None, LISTEN_BAD_KEY
    except Exception as error:
        print(f"Cartesia listening problem: {error}")
        return None, LISTEN_TROUBLE

    if not text:
        return None, LISTEN_NOTHING_HEARD
    return text, None