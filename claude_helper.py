# claude_helper.py
# Compatibility filename: existing app and demo scripts import this module.
# Live requests now use xAI Grok, not Anthropic.
# Every call to Grok lives here.
# Grok only READS an offer and quotes its words.
# The tier is never picked here. scoring.py always picks it.

import json

import os
import urllib.request
import urllib.error
import streamlit as st

from prompts import OFFER_PROMPT

# ---------- Settings ----------
def setting(name, default=""):
    try:
        return st.secrets.get(name, os.environ.get(name, default))
    except (FileNotFoundError, KeyError):
        return os.environ.get(name, default)

MODEL = setting("XAI_MODEL", "grok-4.7")
API_URL = "https://api.x.ai/v1/chat/completions"
MAX_TOKENS = 2000

# prompts.py started with this text before the real prompt was pasted in.
PROMPT_PLACEHOLDER = "PASTE THE OFFER PROMPT HERE"

# The keys we expect in Grok's JSON answer.
EXPECTED_KEYS = [
    "category",
    "government_backed",
    "loss_possible",
    "access",
    "yearly_costs",
    "promised_return",
    "red_flags",
    "questions_to_ask",
    "plain_summary",
    "spoken_summary",
]

# The exact JSON shape we send with every offer.
# The prompt says "using exactly the keys you are given": these are those keys.
# The access words match ACCESS_BADGES in scoring.py.
JSON_SHAPE = """{
  "category": "one name copied exactly from the list above, or \\"unknown\\"",
  "government_backed": {"value": "yes, no or unknown", "quote": "exact words from the offer, or unknown"},
  "loss_possible": {"value": "yes, no or unknown", "quote": "exact words from the offer, or unknown"},
  "access": {"value": "anytime, small_penalty, locked_years or unknown", "quote": "exact words from the offer, or unknown"},
  "yearly_costs": {"value_pct": "a number such as 1.3, or unknown", "has_surrender_or_sales_charge": "yes, no or unknown", "quote": "exact words from the offer, or unknown"},
  "promised_return": {"value_pct": "a number such as 5.1, or unknown", "guaranteed": "yes, no or unknown", "quote": "exact words from the offer, or unknown"},
  "red_flags": [{"flag": "the warning sign, in plain words", "quote": "exact words from the offer"}],
  "questions_to_ask": ["3 to 5 plain questions"],
  "plain_summary": "under 80 words",
  "spoken_summary": "under 60 words"
}"""

# What the access words mean, so Grok picks the right one.
ACCESS_MEANINGS = (
    'For access, "anytime" means money can come out anytime with no penalty; '
    '"small_penalty" means taking money out early costs a small amount, such as some interest; '
    '"locked_years" means surrender charges or a lock-up that last for years.'
)

# ---------- Friendly error messages (shown on the screen) ----------
ERROR_NO_PROMPT = "The offer prompt hasn't been added to prompts.py yet, so we can't check offers."
ERROR_NO_KEY = (
    "Second Look can't reach Grok because the API key is missing. "
    "Add XAI_API_KEY to .streamlit/secrets.toml."
)
ERROR_BAD_KEY = "Grok did not accept the API key. Check XAI_API_KEY in .streamlit/secrets.toml."
ERROR_CONNECTION = "Sorry, we couldn't reach Grok just now. Please wait a moment and click Check this offer again."
ERROR_BAD_ANSWER = "Sorry, we couldn't read Grok's answer. Please click Check this offer again."


def make_user_message(offer_text, categories):
    """The message we send: the allowed categories, the JSON shape, then the offer.
    The offer goes inside <offer> tags so Grok treats it as text to read,
    not as instructions to follow."""
    category_lines = "\n".join(f"- {name}" for name in categories)
    return (
        "Product categories (copy one name exactly, or write \"unknown\"):\n"
        f"{category_lines}\n\n"
        "Reply with JSON in exactly this shape:\n"
        f"{JSON_SHAPE}\n\n"
        f"{ACCESS_MEANINGS}\n\n"
        "The pasted text is between the <offer> tags:\n"
        f"<offer>\n{offer_text}\n</offer>"
    )


def strip_code_fences(text):
    """Remove ``` fences and any words before or after the JSON."""
    text = text.strip()
    # Remove an opening fence like ```json
    if text.startswith("```"):
        first_newline = text.find("\n")
        text = text[first_newline + 1:] if first_newline != -1 else ""
    # Remove a closing fence
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    # Keep only the part from the first { to the last }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        text = text[start:end + 1]
    return text


def parse_answer(raw):
    """Turn Grok's reply into a dictionary.
    Returns None if it isn't the JSON we expect."""
    try:
        answer = json.loads(strip_code_fences(raw))
    except json.JSONDecodeError as error:
        print(f"Could not parse Grok's reply as JSON: {error}")
        return None

    if not isinstance(answer, dict):
        print("Grok's reply was JSON, but not a dictionary.")
        return None

    for key in EXPECTED_KEYS:
        if key not in answer:
            print(f"Grok's reply is missing the key: {key}")
            return None

    return answer


def read_offer(offer_text, categories):
    """Read an offer with Grok; retain the existing (answer, error) interface."""
    if OFFER_PROMPT.strip().startswith(PROMPT_PLACEHOLDER):
        return None, ERROR_NO_PROMPT
    api_key = setting("XAI_API_KEY")
    if not isinstance(api_key, str) or not api_key.strip():
        return None, ERROR_NO_KEY

    payload = {
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "messages": [
            {"role": "system", "content": OFFER_PROMPT},
            {"role": "user", "content": make_user_message(offer_text, categories)},
        ],
        "response_format": {"type": "json_object"},
        "stream": False,
    }
    # Retry malformed model output once; never retry billing/auth errors.
    for attempt in range(2):
        request = urllib.request.Request(
            API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {api_key.strip()}",
                     "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                result = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            if error.code == 401:
                return None, ERROR_BAD_KEY
            if error.code in (402, 403):
                return None, "Grok denied this request. Check API credits and model permissions in your xAI console."
            if error.code == 429:
                return None, "Grok's request limit was reached. Check your API quota and try again later."
            if error.code in (400, 404):
                return None, "Grok could not accept this request. Check that XAI_MODEL is an available chat model in your xAI account."
            return None, ERROR_CONNECTION
        except (urllib.error.URLError, TimeoutError, OSError):
            return None, ERROR_CONNECTION
        except (ValueError, UnicodeError):
            continue

        try:
            choice = result["choices"][0]
            raw = choice["message"]["content"]
            if choice.get("finish_reason") == "length" or not isinstance(raw, str):
                continue
            answer = parse_answer(raw)
        except (KeyError, IndexError, TypeError):
            continue
        if answer is not None:
            # Validate the nested types expected by the existing safety checks.
            facts = ("government_backed", "loss_possible", "access", "yearly_costs", "promised_return")
            valid = (
                isinstance(answer["category"], str)
                and all(isinstance(answer[k], dict) for k in facts)
                and isinstance(answer["red_flags"], list)
                and all(isinstance(x, dict) for x in answer["red_flags"])
                and isinstance(answer["questions_to_ask"], list)
                and all(isinstance(x, str) for x in answer["questions_to_ask"])
                and all(isinstance(answer[k], str) for k in ("plain_summary", "spoken_summary"))
            )
            if valid:
                return answer, None
    return None, ERROR_BAD_ANSWER
