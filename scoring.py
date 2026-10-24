# scoring.py
# This is the ONE place where a product's tier is decided.
# Claude never picks the tier. This file does it with simple, fixed math.
# It also holds the four simple rules for the "Worth thinking about" notes.

from products import TIERS

# Words shown on the "getting your money out" badge.
ACCESS_BADGES = {
    "anytime": "Anytime",
    "small_penalty": "Small penalty",
    "locked_years": "Locked for years",
}

# Words shown when a product doesn't get a normal tier.
OFF_MAP_LABEL = "Doesn't fit the map: check for a scam"
NOT_RATED_LABEL = "Not rated yet"

# ---------- Answers from the Your situation page ----------
# app.py shows these exact words as choices, so the rules below always match.
NEED_WITHIN_1_YEAR = "Within 1 year"
NEED_1_TO_5_YEARS = "In 1 to 5 years"
DROP_SELL = "Sell to stop the loss"
GOAL_SAFE = "Keep it safe"

# ---------- The four fit notes, word for word ----------
NOTE_NEED_SOON = (
    "You said you may need this money within a year. "
    "Products in this tier have lost 10% or more in a bad year."
)
NOTE_LOCKED = (
    "You said you may need this money within 5 years. "
    "This product usually charges you to leave early."
)
NOTE_WOULD_SELL = (
    "You said a drop to $7,000 would make you sell. "
    "This tier has dropped further than that."
)
NOTE_SAFE_GOAL = "Your goal is to keep it safe. This tier can lose money."


def tier_label(tier):
    """Turn a tier result (1-6, "off_map" or "not_rated") into words."""
    if tier == "off_map":
        return OFF_MAP_LABEL
    if tier == "not_rated":
        return NOT_RATED_LABEL
    for t in TIERS:
        if t["number"] == tier:
            return t["name"]
    return NOT_RATED_LABEL


def get_access_badge(product):
    """How easy is it to get money out?"""
    return ACCESS_BADGES.get(product["access"], "Unknown")


def get_cost_badge(product):
    """How much does it cost each year?"""
    cost = product["yearly_cost_pct"]
    # Any sales or surrender charge makes the cost High, no matter what.
    if product["sales_or_surrender_charge"]:
        return "High"
    # We don't know the yearly cost.
    if cost is None:
        return "Varies"
    if cost < 0.25:
        return "Low"
    if cost <= 1:
        return "Medium"
    return "High"


def get_worst_case_dollars(product, amount=10000):
    """How many dollars $10,000 would have lost in the worst year."""
    w = product["worst_year_loss_pct"]
    if w is None:
        return None
    return round(amount * w / 100)


def assign_tier(product, tbill_rate_pct=4.1, promised_return_pct=None, guaranteed=False):
    """Follow THE MATH and return the tier, two badges, worst case and steps."""
    steps = []  # Plain sentences explaining each step.
    tier = None
    backed = product["government_backed"]
    w = product["worst_year_loss_pct"]
    protections = product["protections"]

    # We need a government answer, and (if not backed) a worst-year number.
    missing_facts = backed is None or (backed is False and w is None)

    # Step 1: Is the U.S. government behind it?
    if backed is True:
        tier = 1
        steps.append("Step 1: the U.S. government stands behind it, so Safe Harbor.")
    elif backed is False:
        steps.append("Step 1: the U.S. government does not stand behind it, so we look at its worst year.")
    else:
        steps.append("Step 1: we don't know yet whether the U.S. government stands behind it.")

    # Step 2: Use the worst year (W) to pick tiers 2 to 6.
    if backed is True:
        steps.append("Step 2: skipped, because Step 1 already decided the tier.")
    elif missing_facts:
        steps.append("Step 2: skipped, because we are missing facts about this product.")
    else:
        if w <= 10:
            tier, reason = 2, "which is 10% or less"
        elif w <= 25:
            tier, reason = 3, "which is over 10% and up to 25%"
        elif w <= 50:
            tier, reason = 4, "which is over 25% and up to 50%"
        elif protections is True:
            tier, reason = 5, "which is over 50%, with standard protections"
        else:
            # No protections, or we don't know: treat it as the riskier tier.
            tier, reason = 6, "which is over 50%, without standard protections"
        steps.append(f"Step 2: the worst year was {w:g}%, {reason}, so {tier_label(tier)}.")

    # Step 3: Add the access badge and the cost badge.
    access = get_access_badge(product)
    cost = get_cost_badge(product)
    worst_dollars = get_worst_case_dollars(product)
    steps.append(f"Step 3: getting money out is '{access}', and the cost is '{cost}'.")
    if worst_dollars is not None:
        steps.append(f"Step 3: in the worst year, $10,000 would have lost about ${worst_dollars:,}.")

    # Step 4: Too good to be true?
    if backed is True:
        steps.append("Step 4: skipped, because Step 1 already decided the tier.")
    elif guaranteed and promised_return_pct is not None and promised_return_pct > 2 * tbill_rate_pct:
        tier = "off_map"
        steps.append(
            f"Step 4: it promises a guaranteed {promised_return_pct:g}%, which is more than double "
            f"the {tbill_rate_pct:g}% T-bill rate, so it doesn't fit the map: check for a scam."
        )
    else:
        steps.append("Step 4: no too-good-to-be-true promise found.")

    # Step 5: Missing facts means we can't rate it yet.
    if tier != "off_map" and missing_facts:
        tier = "not_rated"
        steps.append("Step 5: we are missing facts, so Not rated yet.")
    elif tier != "off_map":
        steps.append("Step 5: we have the facts we need.")

    return {
        "tier": tier,
        "access_badge": access,
        "cost_badge": cost,
        "worst_case_dollars": worst_dollars,
        "steps": steps,
    }


def fit_notes(product, answers):
    """Plain sentences that connect someone's answers to this product.
    Uses ONLY the four rules below. Returns an empty list if nothing matches."""
    notes = []

    # No answers yet: nothing to say.
    if not answers:
        return notes

    # The tier always comes from assign_tier above.
    tier = assign_tier(product)["tier"]
    # Products with no normal tier (off_map, not_rated) skip the tier rules.
    has_tier = isinstance(tier, int)

    need = answers.get("need")
    drop = answers.get("drop")
    goal = answers.get("goal")

    # Rule 1: need it within 1 year, and tier 3 or higher.
    if need == NEED_WITHIN_1_YEAR and has_tier and tier >= 3:
        notes.append(NOTE_NEED_SOON)

    # Rule 2: need it within 5 years (that includes within 1 year),
    # and the money is locked up for years.
    if need in (NEED_WITHIN_1_YEAR, NEED_1_TO_5_YEARS) and product["access"] == "locked_years":
        notes.append(NOTE_LOCKED)

    # Rule 3: would sell on a drop, and tier 4 or higher.
    if drop == DROP_SELL and has_tier and tier >= 4:
        notes.append(NOTE_WOULD_SELL)

    # Rule 4: goal is to keep it safe, and tier 3 or higher.
    if goal == GOAL_SAFE and has_tier and tier >= 3:
        notes.append(NOTE_SAFE_GOAL)

    return notes