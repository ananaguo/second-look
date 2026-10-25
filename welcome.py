# welcome.py
# The Welcome view, laid out like a landing page:
#   1. A headline band with two big buttons
#   2. "How it works" in three steps
#   3. A band with the six labels, from Safe Harbor to Uncharted Waters
#   4. "Common questions", with the voice card beside it
# app.py calls show_welcome(). All the styling lives in styles.py.
# The labels themselves come from TIERS in products.py, never from here.
# PRIVACY_NOTICE lives here too, so Welcome and My account always say the same thing.

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

# The privacy notice, shown on Welcome and on My account (the same words in both places).
PRIVACY_NOTICE = (
    "Using Second Look without an account saves nothing. If you create an account, "
    "we save your answers, the products you add, and summaries of offers you check, "
    "in a database set up so only you can see them. We never ask for account numbers "
    "or Social Security numbers. You can download or delete everything at any time. "
    "When you check an offer or ask for an explanation, the text is sent to "
    "an external AI service for analysis; voice recordings are sent to Cartesia for processing."
)

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
    {"question": "Do you save my information?", "answer": PRIVACY_NOTICE},
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
        f"{PRIVACY_NOTICE}"
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
    """Native disclosure cards: flip without scripts, API calls or reruns."""
    cards = []
    for tier in tiers_in_order():
        name = html.escape(tier["name"])
        sentence = html.escape(tier["sentence"])
        rule = html.escape(tier["rule"])
        cards.append(
            '<li class="sl-flip-item"><details class="sl-flip-card">'
            '<summary class="sl-flip-toggle">'
            '<span class="sl-flip-front">'
            f'<span class="sl-flip-kicker">Tier {tier["number"]} of {len(TIERS)}</span>'
            f'<span class="sl-flip-icon" aria-hidden="true">{html.escape(tier["icon"])}</span>'
            f'<span class="sl-flip-name">{name}</span>'
            f'<span class="sl-flip-waves">{html.escape(wave_words(tier))}</span>'
            '<span class="sl-flip-hint">Click to learn more</span></span>'
            '<span class="sl-flip-back" aria-hidden="true">'
            f'<span class="sl-flip-back-name">{name}</span>'
            f'<span class="sl-flip-description">{sentence}</span>'
            f'<span class="sl-flip-rule"><strong>How it is classified</strong><br>{rule}</span>'
            '<span class="sl-flip-hint">Click to turn back</span></span>'
            '</summary>'
            f'<div class="sl-flip-sr">{sentence} Classification rule: {rule}</div>'
            '</details></li>'
        )
    return '<ul class="sl-flip-grid" aria-label="Six financial risk labels">' + ''.join(cards) + '</ul>'


def show_tiers():
    """Six responsive, reversible flashcards using the canonical tier data."""
    with st.container(key="band_light_tiers"):
        st.markdown(f"## {TIERS_TITLE}")
        st.markdown(TIERS_INTRO)
        st.caption("Click or tap a card to learn about its label. Click again to turn it back. Keyboard: Tab to a card, then Enter or Space.")
        st.markdown(
            """
            <style>
            .stApp .st-key-tier_note,
            .stApp .st-key-tier_note [data-testid="stCaptionContainer"],
            .stApp .st-key-tier_note [data-testid="stMarkdownContainer"],
            .stApp .st-key-tier_note p {
                width: 100% !important;
                max-width: none !important;
                box-sizing: border-box !important;
            }
            .stApp .st-key-tier_note p {
                white-space: normal !important;
            }
            .stApp .sl-flip-grid {
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 20px;
                width: 100%;
                max-width: none;
                padding: 0;
                margin: 24px 0;
                list-style: none;
            }
            .stApp .sl-flip-item { min-width: 0; margin: 0; padding: 0; list-style: none; }
            .stApp .sl-flip-card { perspective: 1200px; border: 0; padding: 0; }
            .stApp .sl-flip-toggle {
                position: relative;
                display: block;
                height: 390px;
                padding: 0;
                margin: 0;
                border: 0;
                border-radius: 14px;
                cursor: pointer;
                list-style: none;
                transform-style: preserve-3d;
                transition: transform 450ms ease;
                font-family: "Times New Roman", Times, serif;
            }
            .stApp .sl-flip-toggle::-webkit-details-marker { display: none; }
            .stApp .sl-flip-toggle::marker { content: ""; }
            .stApp .sl-flip-toggle:focus-visible {
                outline: 3px solid #a7834c;
                outline-offset: 5px;
            }
            .stApp .sl-flip-card[open] > .sl-flip-toggle { transform: rotateY(180deg); }
            .stApp .sl-flip-front, .stApp .sl-flip-back {
                position: absolute;
                inset: 0;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                gap: 14px;
                padding: 26px;
                box-sizing: border-box;
                border: 1px solid #d8dde5;
                border-radius: 14px;
                backface-visibility: hidden;
                -webkit-backface-visibility: hidden;
                text-align: center;
                box-shadow: 0 4px 16px rgba(20,33,61,0.05);
                overflow-y: auto;
            }
            .stApp .sl-flip-front { background: #faf9f6; color: #14213d; }
            .stApp .sl-flip-back { background: #14213d; color: #ffffff; transform: rotateY(180deg); }
            .stApp .sl-flip-kicker, .stApp .sl-flip-waves { font-size: 17px; line-height: 1.4; }
            .stApp .sl-flip-icon { font-size: 30px; line-height: 1.4; }
            .stApp .sl-flip-name { font-size: clamp(24px, 2vw, 32px); font-weight: 700; line-height: 1.2; }
            .stApp .sl-flip-back-name { font-size: 25px; font-weight: 700; line-height: 1.2; color: #ffffff; }
            .stApp .sl-flip-description, .stApp .sl-flip-rule { font-size: 19px; line-height: 1.45; color: #ffffff; }
            .stApp .sl-flip-rule { padding-top: 12px; border-top: 1px solid #59667d; }
            .stApp .sl-flip-rule strong { color: #ffffff; }
            .stApp .sl-flip-hint { font-size: 15px; line-height: 1.4; text-decoration: underline; text-underline-offset: 3px; }
            .stApp .sl-flip-sr {
                position: absolute; width: 1px; height: 1px; padding: 0;
                margin: -1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap;
            }
            @media (max-width: 1000px) {
                .stApp .sl-flip-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
            }
            @media (max-width: 600px) {
                .stApp .sl-flip-grid { grid-template-columns: minmax(0, 1fr); }
            }
            @media (prefers-reduced-motion: reduce) {
                .stApp .sl-flip-toggle { transition: none; }
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(tiers_html(), unsafe_allow_html=True)
        with st.container(key="tier_note"):
            st.caption("Labels describe product categories, not predictions. Review costs, access restrictions and the numbers before making a decision.")


# ---------- Part 4: Common questions ----------

def show_faq():
    """Each question opens to show its answer, and the privacy notice below them,
    always in view, so nobody has to open anything to read it."""
    with st.container(key="section_faq"):
        st.markdown(f"## {FAQ_TITLE}")
        for item in FAQ:
            with st.expander(item["question"]):
                answer = item["answer"].strip()
                st.markdown(safe_text(answer) if answer else MISSING_ANSWER)
        st.info(PRIVACY_NOTICE, icon="🔒")


# ---------- The whole Welcome view ----------

def show_welcome(go_to, show_voice_card):
    """Draw the Welcome view, top to bottom.
    go_to: app.py's function that switches pages.
    show_voice_card: app.py's function that draws the voice speed card."""
    show_hero(go_to)
    show_steps()
    show_tiers()
    # Common questions on the left, the voice card on the right.
    # The key starts with "split_", so styles.py puts them side by side
    # (one under the other on smaller screens).
    with st.container(key="split_welcome"):
        show_faq()
        show_voice_card()