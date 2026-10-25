# results.py
# What Second Look works out for products and offers, in plain words.
#   score_offer()  gathers an offer's facts and asks scoring.py for its tier.
#   card_words()   the words "Read aloud" says for one product card.
#   offer_words()  the words "Listen to the result" says for an offer.
# app.py and save_demo_cache.py both use this file. That way a saved
# Demo replay says exactly what the live app would say, word for word.
# The tier is still picked only by scoring.py.

from checks import find_product_by_name
from products import TIERS
from scoring import ACCESS_BADGES, assign_tier, tier_label
from voice_helper import dollars_in_words, number_words

# The amount used in every "worst year" example
EXAMPLE_AMOUNT = 10000

# What the heading says when a product has no normal tier
OFF_MAP_SENTENCE = "No tier: this needs a closer look."
NOT_RATED_SENTENCE = "No tier yet: we are missing facts."

# The last thing shown and said for every offer
OFFER_CLOSING_LINE = (
    "This is a first look, not advice. Before you sign anything, "
    "talk it over with someone you trust."
)


# ---------- Reading claude's answer safely ----------
# The prompt tells claude to write "unknown" whenever the offer doesn't say something.
# checks.py has already checked every quote before these helpers see the answer.

def get_part(answer, key):
    """One part of claude's answer, as a dictionary. Empty if it is missing."""
    part = answer.get(key)
    return part if isinstance(part, dict) else {}


def is_quoted(part):
    """True if claude gave a real quote from the offer.
    An empty quote or "unknown" does not count."""
    if not isinstance(part, dict):
        return False
    quote = part.get("quote")
    return isinstance(quote, str) and quote.strip().lower() not in ("", "unknown")


def as_number(value):
    """A number from claude's answer, like 1.3 or "1.3%".
    None if it isn't a number (for example "unknown")."""
    if isinstance(value, bool):  # True and False are not numbers here
        return None
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        try:
            return float(value.strip().rstrip("%").strip())
        except ValueError:
            return None
    return None


def yes_no_unknown(value):
    """Turn "yes" / "no" / "unknown" (or true / false) into True, False or None."""
    if value is True or value is False:
        return value
    if isinstance(value, str):
        word = value.strip().lower()
        if word == "yes":
            return True
        if word == "no":
            return False
    return None


def access_word(part):
    """claude's access value in lowercase, like "locked_years". Empty if missing."""
    value = part.get("value")
    return value.strip().lower() if isinstance(value, str) else ""


# ---------- An offer's facts and tier ----------

def build_offer_facts(answer):
    """Build the facts that scoring.py needs for this offer.
    Government backing, worst year and protections come ONLY from products.py.
    Access and costs come from the offer when a checked quote backs them up,
    otherwise from products.py.
    Returns (facts, matching product or None, list of where each fact came from)."""
    product = find_product_by_name(answer.get("category"))
    where_from = []

    # Start with "not known" for everything.
    facts = {
        "government_backed": None,
        "worst_year_loss_pct": None,
        "worst_year": "not known",
        "protections": None,
        "access": "unknown",
        "yearly_cost_pct": None,
        "sales_or_surrender_charge": False,
    }

    # 1. Copy the facts from the matching product.
    if product is not None:
        for key in facts:
            facts[key] = product[key]
        where_from.append(
            f"Government backing, worst year and protections: our product list ({product['name']})."
        )
    else:
        where_from.append(
            "Government backing, worst year and protections: not known, "
            "because the offer didn't match a product on our list."
        )

    # 2. Getting money out: use the offer's words if the quote was found.
    access = get_part(answer, "access")
    if is_quoted(access) and access_word(access) in ACCESS_BADGES:
        facts["access"] = access_word(access)
        where_from.append("Getting money out: the offer's own words.")
    elif product is not None:
        where_from.append("Getting money out: our product list.")
    else:
        where_from.append("Getting money out: not known.")

    # 3. Costs: use the offer's words if the quote was found.
    costs = get_part(answer, "yearly_costs")
    if is_quoted(costs):
        yearly = as_number(costs.get("value_pct"))
        if yearly is not None:
            facts["yearly_cost_pct"] = yearly
        surrender = yes_no_unknown(costs.get("has_surrender_or_sales_charge"))
        if surrender is not None:
            facts["sales_or_surrender_charge"] = surrender
        where_from.append("Costs: the offer's own words.")
    elif product is not None:
        where_from.append("Costs: our product list.")
    else:
        where_from.append("Costs: not known.")

    # 4. Promised return (used for the too-good-to-be-true check).
    promised = get_part(answer, "promised_return")
    if as_number(promised.get("value_pct")) is not None:
        where_from.append("Promised return: the offer's own words.")
    else:
        where_from.append("Promised return: the offer didn't promise a number.")

    return facts, product, where_from


def score_offer(answer):
    """The tier result for an offer reading.
    Run verify_quotes and apply_guards (checks.py) first.
    scoring.py picks the tier, using the promised return for the scam check.
    Returns (result, facts, matching product or None, where each fact came from)."""
    facts, product, where_from = build_offer_facts(answer)
    promised = get_part(answer, "promised_return")
    result = assign_tier(
        facts,
        promised_return_pct=as_number(promised.get("value_pct")),
        guaranteed=yes_no_unknown(promised.get("guaranteed")) is True,
    )
    return result, facts, product, where_from


# ---------- The words the voice says ----------

def get_tier_info(tier):
    """Find the tier's name and icon in products.py. None if it has no tier."""
    for t in TIERS:
        if t["number"] == tier:
            return t
    return None


def end_sentence(text):
    """Add a period at the end, unless the text already ends with . ! or ?"""
    text = str(text).strip()
    if not text or text[-1] in ".!?":
        return text
    return text + "."


def tier_name_and_sentence(tier):
    """The tier's name and its one sentence, for speaking."""
    info = get_tier_info(tier)
    if info is not None:
        return info["name"], info["sentence"]
    if tier == "off_map":
        return tier_label(tier), OFF_MAP_SENTENCE
    return tier_label(tier), NOT_RATED_SENTENCE


def badge_words(result):
    """The two badges, said with their titles so they make sense when heard."""
    return f"Getting money out: {result['access_badge']}. Cost: {result['cost_badge']}."


def card_words(product, result):
    """What Read aloud says for one product card:
    [tier name]. [tier sentence]. [product name]: [one_line].
    In its worst year, ten thousand dollars became [X]. [access badge]. [cost badge]."""
    name, sentence = tier_name_and_sentence(result["tier"])

    lost = result["worst_case_dollars"]
    if lost is None:
        worst = "We don't know its worst year yet."
    else:
        left_over = max(0, EXAMPLE_AMOUNT - lost)
        worst = f"In its worst year, ten thousand dollars became {dollars_in_words(left_over)}."

    parts = [
        end_sentence(name),
        end_sentence(sentence),
        end_sentence(f"{product['name']}: {product['one_line']}"),
        worst,
        badge_words(result),
    ]
    return " ".join(parts)


def offer_words(answer, result):
    """What Listen to the result says for an offer:
    the spoken summary, our label and its sentence, any warning signs,
    the two badges, and the closing reminder."""
    parts = []
    summary = answer.get("spoken_summary")
    if isinstance(summary, str) and summary.strip():
        parts.append(end_sentence(summary))

    name, sentence = tier_name_and_sentence(result["tier"])
    parts.append(end_sentence(f"Our label for this offer: {name}"))
    parts.append(end_sentence(sentence))

    count = answer.get("guards", {}).get("red_flag_count", 0)
    if count:
        signs = "sign" if count == 1 else "signs"
        parts.append(f"We found {number_words(count)} warning {signs} in this offer.")

    parts.append(badge_words(result))
    parts.append(OFFER_CLOSING_LINE)
    return " ".join(parts)