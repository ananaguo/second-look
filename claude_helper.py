# claude_helper.py
# Every call to Claude lives here.
# Claude only READS an offer and quotes its words.
# The tier is never picked here. scoring.py always picks it.

import json

import anthropic
import streamlit as st

from prompts import OFFER_PROMPT

# ---------- Settings ----------
MODEL = "claude-sonnet-5-5"
MAX_TOKENS = 2000

# prompts.py started with this text before the real prompt was pasted in.
PROMPT_PLACEHOLDER = "PASTE THE OFFER PROMPT HERE"

# The keys we expect in Claude's JSON answer.
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

# What the access words mean, so Claude picks the right one.
ACCESS_MEANINGS = (
    'For access, "anytime" means money can come out anytime with no penalty; '
    '"small_penalty" means taking money out early costs a small amount, such as some interest; '
    '"locked_years" means surrender charges or a lock-up that last for years.'
)

# ---------- Friendly error messages (shown on the screen) ----------
ERROR_NO_PROMPT = "The offer prompt hasn't been added to prompts.py yet, so we can't check offers."
ERROR_NO_KEY = (
    "Second Look can't reach Claude because the API key is missing. "
    "Add ANTHROPIC_API_KEY to .streamlit/secrets.toml."
)
ERROR_BAD_KEY = "Claude did not accept the API key. Check ANTHROPIC_API_KEY in .streamlit/secrets.toml."
ERROR_CONNECTION = "Sorry, we couldn't reach Claude just now. Please wait a moment and click Check this offer again."
ERROR_BAD_ANSWER = "Sorry, we couldn't read Claude's answer. Please click Check this offer again."


def make_user_message(offer_text, categories):
    """The message we send: the allowed categories, the JSON shape, then the offer.
    The offer goes inside <offer> tags so Claude treats it as text to read,
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
    """Turn Claude's reply into a dictionary.
    Returns None if it isn't the JSON we expect."""
    try:
        answer = json.loads(strip_code_fences(raw))
    except json.JSONDecodeError as error:
        print(f"Could not parse Claude's reply as JSON: {error}")
        return None

    if not isinstance(answer, dict):
        print("Claude's reply was JSON, but not a dictionary.")
        return None

    for key in EXPECTED_KEYS:
        if key not in answer:
            print(f"Claude's reply is missing the key: {key}")
            return None

    return answer


def read_offer(offer_text, categories):
    """Ask Claude to read one offer.
    Returns (answer, None) when it works,
    or (None, friendly message) when it doesn't."""
    # No prompt yet: don't spend an API call.
    if OFFER_PROMPT.strip().startswith(PROMPT_PLACEHOLDER):
        return None, ERROR_NO_PROMPT

    # Read the key ONLY from st.secrets (.streamlit/secrets.toml).
    try:
        client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    except Exception:
        return None, ERROR_NO_KEY

    user_message = make_user_message(offer_text, categories)

    # Try up to two times: the first try, plus one retry if parsing fails.
    for attempt in (1, 2):
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=OFFER_PROMPT,
                messages=[{"role": "user", "content": user_message}],
            )
        except anthropic.AuthenticationError as error:
            print(f"Claude API key problem: {error}")
            return None, ERROR_BAD_KEY
        except anthropic.APIError as error:
            print(f"Claude API error: {error}")
            return None, ERROR_CONNECTION

        # Join all the text parts of the reply.
        raw = "".join(block.text for block in response.content if block.type == "text")

        # While we're developing: show the raw reply in the terminal.
        print(f"\n===== Claude's raw reply (attempt {attempt}, stop reason: {response.stop_reason}) =====")
        print(raw)
        print("===== end of reply =====\n")

        answer = parse_answer(raw)
        if answer is not None:
            return answer, None

        if attempt == 1:
            print("Parsing failed. Asking Claude one more time...")

    return None, ERROR_BAD_ANSWER