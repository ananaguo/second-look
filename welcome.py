# welcome.py
# The Welcome view, laid out like a landing page:
#   1. A headline band with two big buttons
#   2. "How it works" in three steps
#   3. A band with the six labels, from Safe Harbor to Uncharted Waters
#   4. "Common questions"
# app.py calls show_welcome(). All the styling lives in styles.py.
# The labels themselves come from TIERS in products.py, never from here.

import html

import streamlit as st

from products import TIERS
from voice_helper import number_words

# ==========================================================================
# ==========================================================================
#
#   EDIT HERE: the words on the Welcome view.
#
#   - Paste each Common questions answer between its quote marks.
#   - For an answer with several paragraphs, use three quote marks
#     at each end (""" like this """) and leave a blank line between paragraphs.
#   - An empty answer shows MISSING_ANSWER instead.
#
# ==========================================================================
# ==========================================================================

HEADLINE = "Know what you're being offered."
SUBHEADLINE = (
    "Second Look gives every savings and investment product one plain label, "
    "from Safe Harbor to Uncharted Waters, and shows the numbers behind it."
)
EXPLORE_BUTTON = "🧭 Explore products"
CHECK_BUTTON = "🔎 Check an offer"

STEPS_TITLE = "How it works"
STEPS = [
    {
        "icon": "person",
        "title": "Tell us your situation",
        "sentence": "Answer five short questions about when you might need the money "
                    "and how you feel about losses.",
    },
    {
        "icon": "label",
        "title": "See each product's label",
        "sentence": "Every product gets one label from Safe Harbor to Uncharted Waters, "
                    "with the numbers behind it.",
    },
    {
        "icon": "magnifier",
        "title": "Check an offer someone made you",
        "sentence": "Paste it or say it out loud, and we point out warning signs "
                    "and questions to ask.",
    },
]

TIERS_TITLE = "The six labels"
TIERS_INTRO = "From the calmest water to the wildest. Every product gets exactly one."

FAQ_TITLE = "Common questions"
FAQ = [
    {"question": "What do the labels mean?", "answer": ""},
    {"question": "Where do the numbers come from?", "answer": ""},
    {"question": "Is this financial advice?", "answer": ""},
    {"question": "Do you save my information?", "answer": ""},
]
MISSING_ANSWER = "📝 This answer is still being written."

# ==========================================================================
# END OF EDIT HERE SECTION
# ==========================================================================


# ---------- Navy line icons for "How it works" ----------
# Simple drawings made of lines. "currentColor" means they use the
# text color set in styles.py (navy). aria-hidden: screen readers skip them,
# because the heading next to each one already says what it means.
ICON_PATHS = {
    # A person: a head and shoulders
    "person": '<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4.4 3.6-7 8-7s8 2.6 8 7"/>',
    # A price tag
    "label": '<path d="M20.6 13.4l-7.2 7.2a2 2 0 0 1-2.8 0L3 13V3h10l7.6 7.6a2 2 0 0 1 0 2.8z"/>'
             '<circle cx="7.5" cy="7.5" r="1.5"/>',
    # A magnifying glass
    "magnifier": '<circle cx="11" cy="11" r="7"/><path d="M20 20l-4.3-4.3"/>',
}


def line_icon(name):
    """One navy line icon, as a small SVG drawing."""
    return (
        '<svg class="step-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" '
        'aria-hidden="true" focusable="false">'
        f"{ICON_PATHS[name]}"
        "</svg>"
    )


def safe_text(text):
    """Keep $ signs as plain dollar signs (Streamlit treats $...$ as math)."""
    return str(text).replace("$", "\\$")


def tiers_in_order():
    """The six tiers from products.py, from tier 1 to tier 6."""
    return sorted(TIERS, key=lambda tier: tier["number"])


def wave_words(tier):
    """The tier's wave count in words, like "No waves" or "3 waves"."""
    count = tier["waves"]
    if count == 0:
        words = "No waves"
    elif count == 1:
        words = "1 wave"
    else:
        words = f"{count} waves"
    if "⚠️" in tier["icon"]:
        words += " and a warning sign"
    return words


# ---------- What "Hear this page" says ----------

def welcome_words():
    """Everything on the Welcome view, written to be spoken aloud."""
    step_parts = []
    for number, step in enumerate(STEPS, start=1):
        step_parts.append(f"Step {number_words(number)}: {step['title']}. {step['sentence']}")

    names = [tier["name"] for tier in tiers_in_order()]
    tier_list = ", ".join(names[:-1]) + f", and {names[-1]}"

    return (
        f"Welcome to Second Look. {HEADLINE} {SUBHEADLINE} "
        f"{STEPS_TITLE}. {' '.join(step_parts)} "
        f"{TIERS_TITLE}, from calmest to wildest: {tier_list}. "
        "Nothing is saved. When you close this page, everything you typed is gone."
    )


WELCOME_WORDS = welcome_words()


# ---------- Part 1: the headline band ----------

def show_hero(go_to):
    """The navy band at the top: the headline, one sentence, two big buttons.
    go_to is the function in app.py that switches pages."""
    # The key starts with "band_dark_", so styles.py makes it a full-width navy band.
    with st.container(key="band_dark_hero"):
        st.markdown("📍 **You are on this page:** Welcome")
        st.markdown(f"# {HEADLINE}")
        st.markdown(SUBHEADLINE)
        with st.container(key="hero_buttons"):
            left, right = st.columns(2, gap="medium")
            with left:
                st.button(
                    EXPLORE_BUTTON,
                    key="hero_explore",
                    on_click=go_to,
                    args=("Explore products",),
                    type="primary",
                    width="stretch",
                )
            with right:
                st.button(
                    CHECK_BUTTON,
                    key="hero_check",
                    on_click=go_to,
                    args=("Check an offer",),
                    width="stretch",
                )


# ---------- Part 2: How it works ----------

def steps_html():
    """The three steps as a numbered list. styles.py lays them out
    in three columns, or one column on a phone."""
    items = []
    for number, step in enumerate(STEPS, start=1):
        items.append(
            "<li>"
            '<div class="step-top">'
            f'<span class="step-number">{number}</span>'
            f"{line_icon(step['icon'])}"
            "</div>"
            f'<h3 class="step-title">{html.escape(step["title"])}</h3>'
            f'<p>{html.escape(step["sentence"])}</p>'
            "</li>"
        )
    # Everything on one line: Streamlit could misread spaces at the start of a line.
    return f'<ol class="step-grid" role="list">{"".join(items)}</ol>'


def show_steps():
    """The "How it works" section."""
    with st.container(key="section_steps"):
        st.markdown(f"## {STEPS_TITLE}")
        st.markdown(steps_html(), unsafe_allow_html=True)


# ---------- Part 3: the six labels ----------

def tiers_html():
    """The six tiers in order, each with its number, icon, name and wave count.
    The icon is hidden from screen readers, because the words say the same thing."""
    items = []
    for tier in tiers_in_order():
        items.append(
            "<li>"
            f'<p class="tier-number">Tier {tier["number"]} of {len(TIERS)}</p>'
            f'<p class="tier-icon" aria-hidden="true">{html.escape(tier["icon"])}</p>'
            f'<p class="tier-name">{html.escape(tier["name"])}</p>'
            f'<p class="tier-waves">{html.escape(wave_words(tier))}</p>'
            "</li>"
        )
    return f'<ol class="tier-grid" role="list">{"".join(items)}</ol>'


def show_tiers():
    """The white full-width band with the six labels."""
    # The key starts with "band_light_", so styles.py makes it a full-width white band.
    with st.container(key="band_light_tiers"):
        st.markdown(f"## {TIERS_TITLE}")
        st.markdown(TIERS_INTRO)
        st.markdown(tiers_html(), unsafe_allow_html=True)


# ---------- Part 4: Common questions ----------

def show_faq():
    """Each question opens to show its answer."""
    with st.container(key="section_faq"):
        st.markdown(f"## {FAQ_TITLE}")
        for item in FAQ:
            with st.expander(item["question"]):
                answer = item["answer"].strip()
                st.markdown(safe_text(answer) if answer else MISSING_ANSWER)


# ---------- The whole Welcome view ----------

def show_welcome(go_to, show_voice_card):
    """Draw the Welcome view, top to bottom.
    go_to: app.py's function that switches pages.
    show_voice_card: app.py's function that draws the voice speed card."""
    show_hero(go_to)
    show_steps()
    show_tiers()
    show_faq()
    show_voice_card()