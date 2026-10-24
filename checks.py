# checks.py
# The safety layer for "Check an offer".
# Claude's answer is never trusted as it is. Before scoring.py picks a tier:
#   1. verify_quotes() checks that every quote is really in the pasted offer.
#   2. apply_guards() adds a few extra safety rules.
# Nothing in this file picks a tier. scoring.py always does that.

import copy
import re

from products import PRODUCTS

# ---------- Tags shown next to each quote ----------
FOUND_TAG = "Found in the offer"
NOT_FOUND_TAG = "We couldn't find these exact words, so we treat this as unknown"

# ---------- Words used by the guards ----------
GOV_CLAIM_WARNING = (
    "The offer claims government insurance, but this kind of product doesn't have it. "
    "Ask for proof in writing."
)
SAFE_SENTENCE = "We can't say whether this product is right for you."

# A summary sentence with any of these sounds like advice, so we replace it.
ADVICE_WORDS = ["buy", "best", "recommended"]
ADVICE_PHRASES = ["safe investment"]

# The five facts in Claude's answer that each come with a quote.
FACT_KEYS = ["government_backed", "loss_possible", "access", "yearly_costs", "promised_return"]

# The parts of a fact that hold Claude's answer (everything except the quote).
# These become "unknown" when the quote can't be found.
VALUE_FIELDS = ["value", "value_pct", "has_surrender_or_sales_charge", "guaranteed"]

# Curly quote marks, and the straight marks we swap them for.
CURLY_QUOTES = {
    "‘": "'",
    "’": "'",
    "“": '"',
    "”": '"',
}


# ---------- Small helpers ----------

def normalize(text):
    """Text made easy to compare: lowercase, straight quote marks, single spaces.
    For example, 'Our   “Plan”' becomes 'our "plan"'."""
    text = str(text).lower()
    for curly, straight in CURLY_QUOTES.items():
        text = text.replace(curly, straight)
    # split() breaks on any spaces or new lines; join puts back single spaces.
    return " ".join(text.split())


def has_quote(part):
    """True if this part holds a real quote (not empty and not "unknown")."""
    if not isinstance(part, dict):
        return False
    quote = part.get("quote")
    return isinstance(quote, str) and quote.strip().lower() not in ("", "unknown")


def quote_in_offer(quote, offer_text):
    """True if the quote appears in the offer, ignoring capitals,
    extra spaces, and curly versus straight quote marks."""
    # Quote marks that Claude put around the whole quote don't count.
    wanted = normalize(quote).strip("'\" ")
    if not wanted:
        return False
    return wanted in normalize(offer_text)


def find_product_by_name(category):
    """The product in products.py with this name, ignoring capitals and spaces.
    None if nothing matches (including "unknown")."""
    if not isinstance(category, str):
        return None
    for product in PRODUCTS:
        if normalize(product["name"]) == normalize(category):
            return product
    return None


def says_yes(value):
    """True if Claude answered "yes" (or true)."""
    if value is True:
        return True
    return isinstance(value, str) and value.strip().lower() == "yes"


def mark_unknown(part):
    """Set every answer in this fact to "unknown", and its quote too."""
    for field in VALUE_FIELDS:
        if field in part:
            part[field] = "unknown"
    part["quote"] = "unknown"


# ---------- Step 1: check the quotes ----------

def verify_quotes(offer_text, result):
    """Check every quote in Claude's answer against the pasted offer.
    Returns a NEW copy of the answer (the original is not changed) where:
      - each fact and red flag gets a "check" tag: FOUND_TAG or NOT_FOUND_TAG
        (or None for a fact Claude didn't quote at all);
      - a fact whose quote can't be found is set to "unknown";
      - the category is an exact name from products.py, or "unknown"."""
    checked = copy.deepcopy(result) if isinstance(result, dict) else {}

    # The category must be a name on our product list.
    product = find_product_by_name(checked.get("category"))
    checked["category"] = product["name"] if product is not None else "unknown"

    # The five facts.
    for key in FACT_KEYS:
        part = checked.get(key)
        if not isinstance(part, dict):
            part = {}
        if not has_quote(part):
            # No quote: the offer didn't say it. An answer we can't check
            # counts as unknown too.
            mark_unknown(part)
            part["check"] = None
        elif quote_in_offer(part["quote"], offer_text):
            part["check"] = FOUND_TAG
        else:
            # Keep Claude's words so the screen can show what we looked for.
            part["unverified_quote"] = part["quote"]
            mark_unknown(part)
            part["check"] = NOT_FOUND_TAG
        checked[key] = part

    # The red flags. A flag only counts if its words are really in the offer.
    flags = checked.get("red_flags")
    if not isinstance(flags, list):
        flags = []
    kept = []
    for item in flags:
        if not isinstance(item, dict) or not item.get("flag"):
            continue  # skip anything that isn't a real red flag
        if has_quote(item) and quote_in_offer(item["quote"], offer_text):
            item["check"] = FOUND_TAG
        else:
            if has_quote(item):
                item["unverified_quote"] = item["quote"]
            item["quote"] = "unknown"
            item["check"] = NOT_FOUND_TAG
        kept.append(item)
    checked["red_flags"] = kept

    return checked


def found_red_flags(result):
    """Only the red flags whose words were found in the offer."""
    flags = result.get("red_flags")
    if not isinstance(flags, list):
        return []
    return [item for item in flags if isinstance(item, dict) and item.get("check") == FOUND_TAG]


def quote_check_counts(result):
    """How many of Claude's quotes we found, and how many we couldn't.
    Returns (found, not_found). Run verify_quotes first."""
    found = 0
    not_found = 0
    parts = [result.get(key) for key in FACT_KEYS] + list(result.get("red_flags") or [])
    for part in parts:
        if not isinstance(part, dict) or part.get("from_guard"):
            continue  # the guard's own warning isn't one of Claude's quotes
        if part.get("check") == FOUND_TAG:
            found += 1
        elif part.get("check") == NOT_FOUND_TAG:
            not_found += 1
    return found, not_found


# ---------- Step 2: the guards ----------

def sounds_like_advice(sentence):
    """True if the sentence uses buy, best, recommended or "safe investment"."""
    # Just the words, in lowercase, with no punctuation.
    words = re.findall(r"[a-z]+", normalize(sentence))
    for word in words:
        if word in ADVICE_WORDS:
            return True
    # Spaces at both ends, so "safe investment" doesn't match "unsafe investment".
    joined = f" {' '.join(words)} "
    for phrase in ADVICE_PHRASES:
        if f" {phrase} " in joined or f" {phrase}s " in joined:
            return True
    return False


def clean_summary(text):
    """Replace any sentence that sounds like advice with SAFE_SENTENCE.
    If several sentences are replaced, SAFE_SENTENCE appears only once."""
    if not isinstance(text, str) or not text.strip():
        return text
    # Split after . ! or ? when the next word starts with a capital letter.
    # (So "the U.S. government" stays in one piece.)
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text.strip())
    kept = []
    for sentence in sentences:
        if sounds_like_advice(sentence):
            if SAFE_SENTENCE not in kept:
                kept.append(SAFE_SENTENCE)
        else:
            kept.append(sentence)
    return " ".join(kept)


def apply_guards(result):
    """Extra safety rules. Run verify_quotes first.
    Returns a NEW copy of the answer with a "guards" dictionary added:
      not_rated: True when the category is unknown, so it gets no normal label
      gov_claim_warning: True when the offer claims government backing
                         that this kind of product doesn't have
      red_flag_count: how many red flags were found in the offer
      show_scam_card: True when at least one red flag was found
      summary_changed: True when a summary sentence sounded like advice"""
    guarded = copy.deepcopy(result) if isinstance(result, dict) else {}
    guards = {
        "not_rated": False,
        "gov_claim_warning": False,
        "red_flag_count": 0,
        "show_scam_card": False,
        "summary_changed": False,
    }

    # Guard 1: unknown category means "Not rated yet".
    # scoring.py still picks the label. With no matching product it has no
    # government or worst-year facts, so it gives "Not rated yet".
    product = find_product_by_name(guarded.get("category"))
    if product is None:
        guarded["category"] = "unknown"
        guards["not_rated"] = True

    # Guard 2: the offer claims government backing (or FDIC insurance),
    # the quote was found, but this kind of product has none.
    backed = guarded.get("government_backed")
    claims_backing = (
        isinstance(backed, dict)
        and says_yes(backed.get("value"))
        and backed.get("check") == FOUND_TAG
    )
    if claims_backing and product is not None and product["government_backed"] is False:
        flags = guarded.get("red_flags")
        if not isinstance(flags, list):
            flags = []
        # Put it first, so it's the first warning sign people read.
        flags.insert(0, {
            "flag": GOV_CLAIM_WARNING,
            "quote": backed["quote"],
            "check": FOUND_TAG,
            "from_guard": True,
        })
        guarded["red_flags"] = flags
        guards["gov_claim_warning"] = True

    # Guard 3: any red flag found means we show the scam card.
    guards["red_flag_count"] = len(found_red_flags(guarded))
    guards["show_scam_card"] = guards["red_flag_count"] > 0

    # Guard 4: summaries must never sound like advice.
    # The spoken summary gets the same rule, because Read aloud will use it.
    for key in ("plain_summary", "spoken_summary"):
        before = guarded.get(key)
        after = clean_summary(before)
        if after != before:
            guarded[key] = after
            guards["summary_changed"] = True

    guarded["guards"] = guards
    return guarded