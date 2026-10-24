# app.py
# The screens of Second Look.
# Run it with:  streamlit run app.py

import json
import os

import streamlit as st

from checks import (
    FOUND_TAG,
    GOV_CLAIM_WARNING,
    NOT_FOUND_TAG,
    SAFE_SENTENCE,
    apply_guards,
    find_product_by_name,
    quote_check_counts,
    verify_quotes,
)
from claude_helper import read_offer
from products import PRODUCTS, TIERS
from scoring import (
    ACCESS_BADGES,
    DROP_SELL,
    GOAL_SAFE,
    NEED_1_TO_5_YEARS,
    NEED_WITHIN_1_YEAR,
    assign_tier,
    fit_notes,
    tier_label,
)

# ---------- Page setup (this must be the first Streamlit command) ----------
st.set_page_config(
    page_title="Second Look",
    page_icon="🔎",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ---------- Demo mode ----------
# True: the six sample offers use saved readings from data/sample_answers.json,
#       so they work without calling Claude (no API credits needed).
# False: every offer, samples included, is read live by Claude.
DEMO_MODE = True

# ---------- The five views, in the order their buttons appear ----------
VIEWS = ["Welcome", "Your situation", "Explore products", "Compare", "Check an offer"]

# The notice shown at the top of every view
NOTICE = (
    "Second Look explains money products in plain language. "
    "It is educational, not professional financial advice."
)

# ---------- Your situation: the five questions ----------
# "key" is the name used in st.session_state["answers"].
# "short" is the name shown in the "Here's what you told us" summary.
# Some choices come from scoring.py, so the fit-note rules always match.
QUESTIONS = [
    {
        "key": "age",
        "short": "Age range",
        "question": "What is your age range?",
        "options": ["65–69", "70–74", "75–79", "80–84", "85 or older"],
    },
    {
        "key": "income",
        "short": "Monthly income from all sources",
        "question": "What is your monthly income from all sources?",
        "options": ["Under $2,000", "$2,000–$3,500", "Over $3,500", "Prefer not to say"],
    },
    {
        "key": "need",
        "short": "When you might need this money",
        "question": "When might you need this money?",
        "options": [NEED_WITHIN_1_YEAR, NEED_1_TO_5_YEARS, "Not for 5 years or more"],
    },
    {
        "key": "drop",
        "short": "If $10,000 dropped to $7,000, you would",
        "question": "If $10,000 you saved dropped to $7,000 for a while, you would…",
        "options": [DROP_SELL, "Worry but wait", "Stay calm"],
    },
    {
        "key": "goal",
        "short": "Main goal",
        "question": "What is your main goal for this money?",
        "options": [GOAL_SAFE, "Keep up with rising prices", "Grow it over many years", "Steady income"],
    },
]

PRIVACY_LINE = "Don't type your name, account numbers, or Social Security number. We never need them."

# ---------- Words for the "Worth thinking about" notes ----------
NOTES_TITLE = "💭 Worth thinking about"
NOTES_DISCLAIMER = "These notes come from simple rules, not advice."
NO_NOTES_LINE = "None of our simple rules matched your answers for this product."

# ---------- Words and icons for the Explore products cards ----------

# "Rough water" gauge: one word for each tier, from tier 1 to tier 6
ROUGH_WATER_WORDS = ["Very calm", "Calm", "Some waves", "Rough", "Very rough", "Extreme"]

# "Possible catch" gauge: one word for each of tiers 1 to 4
CATCH_WORDS = ["Small", "Modest", "Medium", "Large"]

# An icon for every access badge and cost badge (always shown with the word)
ACCESS_ICONS = {
    "Anytime": "🔓",
    "Small penalty": "⏳",
    "Locked for years": "🔒",
}
COST_ICONS = {
    "Low": "💲",
    "Medium": "💲💲",
    "High": "💲💲💲",
    "Varies": "❔",
}

# Special worst-year lines
SAFE_HARBOR_LINE = "Safe from losses, not from rising prices. Insured up to $250,000 per bank."
BIG_LOSS_LINE = "Could lose most or all."

# The amount used in every "worst year" example
EXAMPLE_AMOUNT = 10000

# ---------- Check an offer: settings and words ----------

DATA_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# Where the made-up sample offers live
SAMPLE_OFFERS_FILE = os.path.join(DATA_FOLDER, "sample_offers.md")

# Where the saved, hand-written readings of those samples live (for demo mode)
SAMPLE_ANSWERS_FILE = os.path.join(DATA_FOLDER, "sample_answers.json")

# The longest offer someone can paste (keeps Claude calls small)
OFFER_MAX_CHARS = 6000

OFFER_BOX_LABEL = "Paste what the salesperson or brochure said"
SAMPLE_LABEL = "Use a sample offer"
CHECK_BUTTON = "🔎 Check this offer"
SPINNER_TEXT = "Reading the offer…"
FLAGS_TITLE = "⚠️ Warning signs we noticed"
NO_FLAGS_LINE = "We didn't notice any warning signs in this text. That alone doesn't make it safe."
NOT_STATED_QUOTE = "*The offer doesn't say.*"
OFFER_CLOSING_LINE = (
    "This is a first look, not advice. Before you sign anything, "
    "talk it over with someone you trust."
)

# Tags next to each quote: always an icon AND words (the words come from checks.py)
FOUND_LINE = f"✅ {FOUND_TAG}"
NOT_FOUND_LINE = f"❓ {NOT_FOUND_TAG}"
UNSURE_FLAGS_LINE = (
    "We also looked for these, but couldn't find the exact words, so we don't count them:"
)

# Demo mode words (always an icon AND words)
DEMO_NOTICE = (
    "📼 **Demo mode is on.** The six sample offers use saved readings, "
    "so they work without Claude. Anything you paste or change is checked live by Claude."
)
DEMO_CARD_LINE = (
    "📼 **Demo mode:** this is a saved, hand-written reading of a sample offer, "
    "not a live check by Claude. The label still comes from our own rules."
)

# ---------- Safety cards (shown on Check an offer, Explore products and Compare) ----------

HELP_CARD_TITLE = "☎️ Before a big decision"
HELP_CARD_TEXT = (
    "Before a big decision, like moving savings or buying an annuity, talk with a licensed advisor. "
    "A fee-only fiduciary advisor is paid by you, not by sales commissions.\n\n"
    "Check anyone who sells investments on **FINRA BrokerCheck**: "
    "[brokercheck.finra.org](https://brokercheck.finra.org) or **800-289-9999**.\n\n"
    "Questions or worries about a brokerage account: **FINRA Securities Helpline for Seniors**, "
    "**844-574-3577** (weekdays, 9 a.m. to 5 p.m. Eastern).\n\n"
    "Annuities and insurance in California: **Department of Insurance**, **1-800-927-4357**."
)

SCAM_CARD_TITLE = "🚩 How to spot a scam"
SCAM_TOP_TITLE = "🚩 This offer shows warning signs"
SCAM_CARD_TEXT = (
    "Real investments never promise high returns with no risk. "
    "An honest seller won't pressure you to decide today, ask you to keep it secret, "
    "or ask you to pay by gift card, wire transfer or crypto.\n\n"
    "You can always take the papers home and ask someone you trust.\n\n"
    "In California, older buyers generally get 30 days to review an annuity and return it; "
    "check your contract."
)

WRONG_BUTTON = "🤔 Something looks wrong?"
WRONG_TEXT = (
    "Trust the official papers over this app. Ask the seller for the contract or prospectus, "
    "and go over the numbers with a licensed advisor or one of the helplines above."
)

# ---------- Look and feel: large text, high contrast, big buttons ----------
CSS = """
<style>
/* Base text size. Streamlit sizes many things in 'rem', so this scales them too. */
html { font-size: 22px; }

/* Body text: large, dark, roomy */
.stApp, .stApp p, .stApp li, .stApp label, .stApp span {
    font-size: 22px;
    line-height: 1.6;
    color: #111111;
}

/* Headings: at least 34px */
.stApp h1 {
    font-size: 44px !important;
    line-height: 1.25 !important;
    font-weight: 800 !important;
    color: #111111 !important;
}
.stApp h2, .stApp h3 {
    font-size: 34px !important;
    line-height: 1.3 !important;
    font-weight: 700 !important;
    color: #111111 !important;
}
/* Product names on the cards */
.stApp h4 {
    font-size: 28px !important;
    line-height: 1.3 !important;
    font-weight: 700 !important;
    color: #111111 !important;
}
/* Text inside a heading keeps the heading's size */
.stApp h1 span, .stApp h2 span, .stApp h3 span, .stApp h4 span {
    font-size: inherit !important;
}
/* Hide the little link icons Streamlit puts next to headings */
[data-testid="stHeaderActionElements"] {
    display: none !important;
}

/* Keep the page centered, but wide enough for five buttons in one row */
.stApp .block-container,
.stApp [data-testid="stMainBlockContainer"] {
    max-width: 960px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}

/* Generous space between sections */
.stApp [data-testid="stVerticalBlock"] { gap: 1.25rem; }
.stApp [data-testid="stHorizontalBlock"] { gap: 12px; }
.stApp hr {
    border: none;
    border-top: 2px solid #111111;
    margin: 1.5rem 0;
}

/* Cards (products, questions, summary, offer, help, scam): a thick dark border, lots of room */
.stApp [class*="st-key-card_"] {
    border: 3px solid #111111;
    border-radius: 14px;
    padding: 28px 24px;
    margin-bottom: 2rem;
    background-color: #FFFFFF;
}
/* The scam card: an extra-thick border, so it stands out without relying on color */
.stApp [class*="st-key-card_scam"] {
    border-width: 6px;
}

/* Boxes inside a card ("Worth thinking about", "Warning signs") */
.stApp [class*="st-key-notes_"] {
    border: 2px dashed #111111;
    border-radius: 10px;
    padding: 18px 20px;
}

/* The block bars in the gauges */
.stApp .gauge {
    margin: 0.25rem 0;
}
.stApp .gauge-bar {
    font-size: 30px;
    letter-spacing: 4px;
}

/* Your situation: the question text above the choices */
.stApp [data-testid="stRadio"] [data-testid="stWidgetLabel"] p {
    font-size: 28px !important;
    font-weight: 700;
    line-height: 1.3;
}
/* Space between the choices */
.stApp [data-testid="stRadio"] [role="radiogroup"] {
    gap: 12px;
}
/* Each choice is a big box that is easy to click */
.stApp [data-testid="stRadio"] [role="radiogroup"] label {
    width: 100%;
    min-height: 64px;
    padding: 12px 16px;
    border: 2px solid #111111;
    border-radius: 10px;
    align-items: center;
    cursor: pointer;
}
/* The round dot: one and a half times bigger */
.stApp [data-testid="stRadio"] [role="radiogroup"] label > div:first-child {
    transform: scale(1.5);
    margin-right: 14px;
}
.stApp [data-testid="stRadio"] [role="radiogroup"] label p {
    font-size: 24px !important;
}
/* The chosen answer: a thicker border and bold words, not just a color */
.stApp [data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) {
    border-width: 4px;
    background-color: #E8EEFC;
}
.stApp [data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) p {
    font-weight: 700;
}
/* Thick outline when moving between choices with the keyboard */
.stApp [data-testid="stRadio"] [role="radiogroup"] label:has(input:focus-visible) {
    outline: 4px solid #111111;
    outline-offset: 3px;
}

/* Check an offer: big labels on the text box and the dropdown */
.stApp [data-testid="stTextArea"] [data-testid="stWidgetLabel"] p,
.stApp [data-testid="stSelectbox"] [data-testid="stWidgetLabel"] p {
    font-size: 28px !important;
    font-weight: 700;
    line-height: 1.3;
}
/* The big text box: large dark text and a thick border */
.stApp textarea {
    font-size: 22px !important;
    line-height: 1.5 !important;
    color: #111111 !important;
    border: 2px solid #111111 !important;
}
/* The dropdown: tall and easy to click */
.stApp [data-testid="stSelectbox"] [data-baseweb="select"] > div {
    min-height: 60px;
    border: 2px solid #111111;
    font-size: 22px;
}
/* The small "Press Ctrl+Enter" and letter-count text: dark, not gray */
.stApp [data-testid="InputInstructions"],
.stApp [data-testid="InputInstructions"] * {
    color: #111111 !important;
    font-size: 18px !important;
}

/* "Show me the numbers": big title and a clear border */
.stApp [data-testid="stExpander"] details {
    border: 2px solid #111111;
    border-radius: 10px;
}
.stApp [data-testid="stExpander"] summary p {
    font-size: 24px !important;
    font-weight: 700;
}

/* The Compare checkbox label: big and bold, so it is easy to click */
.stApp [data-testid="stCheckbox"] label p {
    font-size: 24px !important;
    font-weight: 700;
}

/* All buttons: big, bold, outlined in blue */
.stApp .stButton > button {
    min-height: 60px;
    width: 100%;
    padding: 10px 14px;
    border: 3px solid #0B4FD6;
    border-radius: 10px;
    background-color: #FFFFFF;
    color: #0B4FD6;
    white-space: normal;  /* long labels wrap instead of being cut off */
}
.stApp .stButton > button * {
    color: inherit;
}
.stApp .stButton > button p {
    font-size: 24px !important;
    font-weight: 700;
    line-height: 1.25;
}
.stApp .stButton > button:hover {
    background-color: #E8EEFC;
}

/* Filled blue buttons (the page you are on, and main actions) */
.stApp .stButton > button[kind="primary"],
.stApp .stButton > button[data-testid="stBaseButton-primary"] {
    background-color: #0B4FD6;
    color: #FFFFFF;
}
.stApp .stButton > button[kind="primary"]:hover,
.stApp .stButton > button[data-testid="stBaseButton-primary"]:hover {
    background-color: #083BA3;
    border-color: #083BA3;
    color: #FFFFFF;
}

/* The five page buttons share one height, so the row looks even */
.stApp [class*="st-key-nav_"] .stButton > button {
    min-height: 88px;
}

/* Thick, easy-to-see outline when moving around with the Tab key */
.stApp button:focus-visible,
.stApp a:focus-visible,
.stApp input:focus-visible,
.stApp textarea:focus-visible,
.stApp summary:focus-visible {
    outline: 4px solid #111111 !important;
    outline-offset: 3px !important;
}

/* No light-gray text anywhere */
.stApp [data-testid="stCaptionContainer"],
.stApp small,
.stApp [data-testid="stAlert"] * {
    color: #111111 !important;
}

/* Hide Streamlit's menu, footer, top bar and sidebar */
#MainMenu,
footer,
header[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stSidebar"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"] {
    display: none !important;
}
</style>
"""


# ---------- Small helper functions ----------

def go_to(view_name):
    """Runs when a page button is clicked: remember which page to show."""
    st.session_state["view"] = view_name


def start_over():
    """Runs when Start over is clicked: forget everything except the page."""
    for key in list(st.session_state.keys()):
        if key != "view":
            del st.session_state[key]
    # A one-time flag so we can tell the person it worked
    st.session_state["just_cleared"] = True


def safe_text(text):
    """Streamlit shows text between two $ signs as math.
    A backslash in front of each $ keeps it a plain dollar sign."""
    return str(text).replace("$", "\\$")


def show_notice():
    """The educational notice at the top of every view."""
    st.info(NOTICE, icon="ℹ️")


def show_nav():
    """The row of five big page buttons."""
    current = st.session_state["view"]
    columns = st.columns(len(VIEWS), gap="small")

    for number, view_name in enumerate(VIEWS):
        is_current = view_name == current
        # The page you are on gets a pin icon and a filled blue button,
        # so it never depends on color alone.
        label = f"📍 {view_name}" if is_current else view_name
        with columns[number]:
            st.button(
                label,
                key=f"nav_{number}",
                on_click=go_to,
                args=(view_name,),
                type="primary" if is_current else "secondary",
                width="stretch",
            )


def show_heading():
    """The name of the current page, in large letters."""
    st.markdown("📍 **You are on this page:**")
    st.title(st.session_state["view"])


def show_welcome():
    """What Second Look does, in three short sentences."""
    st.markdown(
        "Every savings or investment product gets one plain label, "
        "from **Safe Harbor** to **Uncharted Waters**.\n\n"
        "You can always see the numbers behind every label.\n\n"
        "You can also check an offer that someone made you."
    )
    st.markdown(
        "🔒 **Nothing is saved.** When you close this page, "
        "everything you typed is gone."
    )
    st.markdown("Use the big buttons at the top to choose a page.")


def show_coming_soon():
    """Placeholder for views we have not built yet."""
    st.markdown("🚧 **Coming soon.** This page is still being built.")
    st.markdown("Use the big buttons at the top to choose another page.")


def show_start_over():
    """The Start over button at the bottom of every view."""
    st.divider()
    st.button("↺ Start over", key="start_over", on_click=start_over, width="stretch")
    # Confirm that it worked, then forget the flag
    if st.session_state.pop("just_cleared", False):
        st.success("Done. Everything you entered has been cleared.", icon="✅")


# ---------- Safety cards: help, scam, and "Something looks wrong?" ----------

def show_help_card():
    """Where to get a trusted second opinion."""
    with st.container(key="card_help"):
        st.markdown(f"### {HELP_CARD_TITLE}")
        st.markdown(HELP_CARD_TEXT)


def show_scam_card(key, found_count=0):
    """The scam warning card.
    found_count > 0 means it sits above an offer that showed warning signs."""
    with st.container(key=key):
        if found_count > 0:
            signs = "sign" if found_count == 1 else "signs"
            st.markdown(f"### {SCAM_TOP_TITLE}")
            st.markdown(
                f"**We found {found_count} warning {signs} in this offer.** "
                f"They are listed under **{FLAGS_TITLE}** below."
            )
        else:
            st.markdown(f"### {SCAM_CARD_TITLE}")
        st.markdown(SCAM_CARD_TEXT)


def toggle_wrong_text():
    """Runs when "Something looks wrong?" is clicked: show or hide its text."""
    st.session_state["show_wrong_text"] = not st.session_state.get("show_wrong_text", False)


def show_wrong_button():
    """The "Something looks wrong?" button. It sits under the help card,
    because its text points to "the helplines above"."""
    st.button(WRONG_BUTTON, key="something_wrong", on_click=toggle_wrong_text, width="stretch")
    if st.session_state.get("show_wrong_text"):
        st.info(WRONG_TEXT, icon="📄")


def show_safety_cards(include_scam=True):
    """The cards at the bottom of Check an offer, Explore products and Compare."""
    st.divider()
    if include_scam:
        show_scam_card("card_scam")
    show_help_card()
    show_wrong_button()


# ---------- Your situation: questions and summary ----------

def start_editing():
    """Runs when Edit is clicked: show the questions again."""
    st.session_state["editing_answers"] = True


def missing_question_numbers():
    """The numbers of the questions that have no answer picked yet."""
    missing = []
    for number, question in enumerate(QUESTIONS, start=1):
        if st.session_state.get(f"q_{question['key']}") is None:
            missing.append(str(number))
    return missing


def show_questions():
    """The five questions, each in its own big card, and a Save button."""
    st.warning(PRIVACY_LINE, icon="🛡️")
    st.markdown("Pick one answer for each question. You can change them later.")

    saved = st.session_state.get("answers") or {}

    for number, question in enumerate(QUESTIONS, start=1):
        radio_key = f"q_{question['key']}"
        # When editing, start each question on the answer saved before.
        if radio_key not in st.session_state and question["key"] in saved:
            st.session_state[radio_key] = saved[question["key"]]

        with st.container(key=f"card_q_{question['key']}"):
            st.markdown(f"**Question {number} of {len(QUESTIONS)}**")
            st.radio(
                safe_text(question["question"]),
                question["options"],
                index=None,  # nothing is picked until the person picks it
                key=radio_key,
                format_func=safe_text,  # keeps $ signs as plain dollar signs
            )

    if st.button("✅ Save my answers", key="save_answers", type="primary", width="stretch"):
        missing = missing_question_numbers()
        if missing:
            st.warning(
                f"Please answer every question before saving. Still empty: question {', '.join(missing)}.",
                icon="✋",
            )
        else:
            # Save all five answers together in one dictionary.
            answers = {}
            for question in QUESTIONS:
                answers[question["key"]] = st.session_state[f"q_{question['key']}"]
            st.session_state["answers"] = answers
            st.session_state["editing_answers"] = False
            st.rerun()  # draw the page again, now showing the summary


def show_answer_summary(answers):
    """The "Here's what you told us" card, with an Edit button."""
    with st.container(key="card_summary"):
        st.markdown("### 📋 Here's what you told us")
        lines = []
        for question in QUESTIONS:
            answer = answers.get(question["key"], "Not answered")
            lines.append(f"**{safe_text(question['short'])}:** {safe_text(answer)}")
        st.markdown("\n\n".join(lines))
        st.button("✏️ Edit my answers", key="edit_answers", on_click=start_editing, width="stretch")

    st.markdown(
        "🔒 Your answers stay on this page only, until you close it or click **Start over**."
    )
    st.markdown(
        f"Your answers add short notes under **{NOTES_TITLE}** on each product card."
    )
    st.button(
        "🧭 See the notes on Explore products",
        key="goto_explore",
        on_click=go_to,
        args=("Explore products",),
        type="primary",
        width="stretch",
    )


def show_situation():
    """The Your situation view: the questions, or a summary once saved."""
    answers = st.session_state.get("answers")
    editing = st.session_state.get("editing_answers", False)
    if answers and not editing:
        show_answer_summary(answers)
    else:
        show_questions()


# ---------- Explore products: helpers for one card ----------

def get_tier_info(tier):
    """Find the tier's name and icon in products.py. None if it has no tier."""
    for t in TIERS:
        if t["number"] == tier:
            return t
    return None


def tier_order(row):
    """Sorting number for a (product, result) pair: tier 1 first, tier 6 last.
    Products with no normal tier go at the very end."""
    tier = row[1]["tier"]
    if isinstance(tier, int):
        return tier
    return 7


def sorted_products():
    """Every product with its scoring.py result, from Safe Harbor to Uncharted Waters.
    Products in the same tier keep their order from products.py."""
    rows = []
    for product in PRODUCTS:
        rows.append((product, assign_tier(product)))
    rows.sort(key=tier_order)
    return rows


def draw_bar(filled, total):
    """A bar of filled and empty blocks, like ■■■□□□."""
    return "■" * filled + "□" * (total - filled)


def gauge_line(title, bar, word, count):
    """One gauge line. The bar is hidden from screen readers,
    because the word and the count already say the same thing."""
    return (
        f'<p class="gauge"><strong>{title}:</strong> '
        f'<span class="gauge-bar" aria-hidden="true">{bar}</span> '
        f"<strong>{word}</strong> ({count})</p>"
    )


def show_tier_heading(tier):
    """Card part 1: the tier icon and name, and 'Tier N of 6'."""
    info = get_tier_info(tier)
    if info is not None:
        st.markdown(f"### {info['icon']} {info['name']}\n\n**Tier {info['number']} of 6**")
    elif tier == "off_map":
        st.markdown(f"### ⚠️ {tier_label(tier)}\n\n**No tier: this needs a closer look**")
    else:
        st.markdown(f"### ❓ {tier_label(tier)}\n\n**No tier yet: we are missing facts**")


def show_product_name(product):
    """Card part 2: the product name and its one-line description."""
    st.markdown(f"#### {safe_text(product['name'])}\n\n{safe_text(product['one_line'])}")


def show_gauge(tier):
    """Card part 3: the two gauges, drawn with blocks AND words."""
    if not isinstance(tier, int):
        st.markdown("**Rough water:** not known yet\n\n**Possible catch:** not known yet")
        return

    # Rough water: tier 1 gets 1 block out of 6, tier 6 gets 6 blocks.
    rough = gauge_line("Rough water", draw_bar(tier, 6), ROUGH_WATER_WORDS[tier - 1], f"{tier} of 6")

    # Possible catch: a bar for tiers 1 to 4, just a word for tiers 5 and 6.
    if tier <= 4:
        catch = gauge_line("Possible catch", draw_bar(tier, 4), CATCH_WORDS[tier - 1], f"{tier} of 4")
    else:
        catch = '<p class="gauge"><strong>Possible catch:</strong> <strong>Unpredictable</strong></p>'

    st.markdown(rough + catch, unsafe_allow_html=True)


def show_badges(result):
    """Card part 4: the access badge and the cost badge, as big as the tier name."""
    access = result["access_badge"]
    cost = result["cost_badge"]
    left, right = st.columns(2, gap="medium")
    with left:
        st.markdown(f"**Getting money out**\n\n### {ACCESS_ICONS.get(access, '❔')} {access}")
    with right:
        st.markdown(f"**Cost**\n\n### {COST_ICONS.get(cost, '❔')} {cost}")


def show_worst_year(product, result):
    """Card part 5: what $10,000 would have become in the worst year."""
    tier = result["tier"]

    if tier == 1:
        st.markdown(f"**{safe_text(SAFE_HARBOR_LINE)}**")
        return

    lost = result["worst_case_dollars"]
    if lost is None:
        st.markdown("**In its worst year:** not known yet.")
    else:
        left_over = max(0, EXAMPLE_AMOUNT - lost)
        line = f"$10,000 → ${left_over:,} ({product['worst_year']})"
        st.markdown(f"**In its worst year:** {safe_text(line)}")

    if tier in (5, 6):
        st.markdown(f"⚠️ **{BIG_LOSS_LINE}**")


def show_fit_notes(product):
    """Card part 6: notes from the Your situation answers.
    Only shown once the person has saved their answers."""
    answers = st.session_state.get("answers")
    if not answers:
        return

    # scoring.py decides the notes. This function only shows them.
    notes = fit_notes(product, answers)

    with st.container(key=f"notes_{product['key']}"):
        st.markdown(f"#### {NOTES_TITLE}")
        if notes:
            st.markdown("\n".join(f"- {safe_text(note)}" for note in notes))
        else:
            st.markdown(NO_NOTES_LINE)
        st.markdown(NOTES_DISCLAIMER)


def show_numbers(product, result):
    """Card part 7: every fact, step and source behind the label."""
    with st.expander("Show me the numbers", icon="🔢"):
        # The facts from products.py
        loss = product["worst_year_loss_pct"]
        loss_text = "not known yet" if loss is None else f"{loss:g}%"

        cost = product["yearly_cost_pct"]
        cost_text = "Not known yet." if cost is None else f"{cost:g}% a year."

        st.markdown(
            f"**Worst year:** {safe_text(product['worst_year'])}\n\n"
            f"**Loss in that year:** {loss_text}\n\n"
            f"**What it might earn:** {safe_text(product['gain_note'])}\n\n"
            f"**Yearly cost:** {cost_text} {safe_text(product['cost_note'])}\n\n"
            f"**Getting money out:** {safe_text(product['access_note'])}\n\n"
            f"**Insurance:** {safe_text(product['insurance_note'])}"
        )

        # Every step sentence from scoring.py
        step_lines = ["**How we picked the label:**", ""]
        for step in result["steps"]:
            step_lines.append(f"- {safe_text(step)}")
        st.markdown("\n".join(step_lines))

        # Every source, as a link with its as-of date
        source_lines = ["**Sources:**", ""]
        for source in product["sources"]:
            source_lines.append(
                f"- [{safe_text(source['label'])}]({source['url']}), as of {source['as_of']}"
            )
        if not product["sources"]:
            source_lines.append("- No sources yet.")
        st.markdown("\n".join(source_lines))


def toggle_compare(product_key):
    """Runs when a Compare box is ticked or unticked.
    We keep the chosen products in our own list, so the choices
    are still there after visiting another page."""
    chosen = st.session_state.setdefault("compare_keys", [])
    is_ticked = st.session_state[f"compare_box_{product_key}"]
    if is_ticked and product_key not in chosen:
        chosen.append(product_key)
    if not is_ticked and product_key in chosen:
        chosen.remove(product_key)


def show_card_actions(product):
    """Card part 8: the Compare checkbox and the Read aloud button."""
    key = product["key"]
    box_key = f"compare_box_{key}"

    # When coming back to this page, tick the box again if it was chosen before.
    if box_key not in st.session_state:
        st.session_state[box_key] = key in st.session_state.get("compare_keys", [])

    left, right = st.columns(2, gap="medium", vertical_alignment="center")
    with left:
        st.checkbox("Compare", key=box_key, on_change=toggle_compare, args=(key,))
    with right:
        read_clicked = st.button("🔊 Read aloud", key=f"read_{key}", width="stretch")

    # Shown full width under the two columns
    if read_clicked:
        st.info("Coming in M8. Read aloud is not built yet.", icon="🚧")


def show_explore():
    """The Explore products view: one big card per product."""
    st.markdown(
        "Every product is listed here, from the calmest water (**⚓ Safe Harbor**) "
        "to the wildest (**⚠️ Uncharted Waters**).\n\n"
        "Open **Show me the numbers** on any card to see the facts and sources behind its label."
    )

    # No answers yet: explain where the notes come from, with a button to get there.
    if not st.session_state.get("answers"):
        st.markdown(
            f"💭 Answer the questions on **Your situation** to see short notes "
            f"on each card under **{NOTES_TITLE}**."
        )
        st.button(
            "🧭 Go to Your situation",
            key="goto_situation",
            on_click=go_to,
            args=("Your situation",),
            width="stretch",
        )

    for product, result in sorted_products():
        # The key gives this card a name, so the CSS above can draw its border.
        with st.container(key=f"card_{product['key']}"):
            show_tier_heading(result["tier"])
            show_product_name(product)
            show_gauge(result["tier"])
            show_badges(result)
            show_worst_year(product, result)
            show_fit_notes(product)
            show_numbers(product, result)
            show_card_actions(product)

    # The scam card, the help card and "Something looks wrong?"
    show_safety_cards()


# ---------- Compare (still being built) ----------

def show_compare():
    """The Compare view. Not built yet, but the safety cards are already here."""
    show_coming_soon()
    show_safety_cards()


# ---------- Check an offer: reading the sample files ----------

def load_sample_offers():
    """Read OFFER 1 to 6 from data/sample_offers.md.
    Returns a dictionary like {"OFFER 1": "the offer's text", ...}.
    Returns an empty dictionary if the file is missing."""
    samples = {}
    try:
        with open(SAMPLE_OFFERS_FILE, encoding="utf-8") as file:
            text = file.read()
    except OSError:
        return samples

    # Each offer starts with a heading like "## OFFER 1".
    for part in text.split("## OFFER ")[1:]:
        number, _, body = part.partition("\n")
        samples[f"OFFER {number.strip()}"] = body.strip()
    return samples


def load_demo_answers():
    """Read the saved readings from data/sample_answers.json.
    Returns a dictionary like {"OFFER 1": {...}, ...}.
    Returns an empty dictionary if the file is missing or broken."""
    try:
        with open(SAMPLE_ANSWERS_FILE, encoding="utf-8") as file:
            saved = json.load(file)
    except (OSError, json.JSONDecodeError):
        return {}
    return saved if isinstance(saved, dict) else {}


def find_demo_answer(text, samples, demo_answers):
    """The saved reading for this text, if it is exactly one of the sample offers.
    None if the text was pasted or changed, or if there is no saved reading."""
    for name, sample_text in samples.items():
        if text == sample_text.strip() and name in demo_answers:
            return demo_answers[name]
    return None


def load_sample(samples):
    """Runs when a sample is picked: put its text in the big box."""
    choice = st.session_state.get("sample_choice")
    if choice in samples:
        st.session_state["offer_text"] = samples[choice]


# ---------- Check an offer: reading Claude's answer safely ----------
# The prompt tells Claude to write "unknown" whenever the offer doesn't say something.
# checks.py has already checked every quote before these helpers see the answer.

def get_part(answer, key):
    """One part of Claude's answer, as a dictionary. Empty if it is missing."""
    part = answer.get(key)
    return part if isinstance(part, dict) else {}


def is_quoted(part):
    """True if Claude gave a real quote from the offer.
    An empty quote or "unknown" does not count."""
    if not isinstance(part, dict):
        return False
    quote = part.get("quote")
    return isinstance(quote, str) and quote.strip().lower() not in ("", "unknown")


def as_number(value):
    """A number from Claude's answer, like 1.3 or "1.3%".
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
    """Claude's access value in lowercase, like "locked_years". Empty if missing."""
    value = part.get("value")
    return value.strip().lower() if isinstance(value, str) else ""


# ---------- Check an offer: building the offer's facts ----------

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


# ---------- Check an offer: showing the result card ----------

def quote_md(text):
    """Show a quote from the offer in italics, safely.
    Escapes $, * and _ so they show as plain characters."""
    one_line = " ".join(str(text).split())
    clean = safe_text(one_line).replace("*", "\\*").replace("_", "\\_")
    return f"*“{clean}”*"


def check_line(part):
    """The quote and its tag, ready to show under a fact or a red flag."""
    check = part.get("check")
    if check == FOUND_TAG and is_quoted(part):
        return f"{quote_md(part['quote'])}  \n{FOUND_LINE}"
    if check == NOT_FOUND_TAG:
        line = NOT_FOUND_LINE
        if part.get("unverified_quote"):
            line += f": {quote_md(part['unverified_quote'])}"
        return line
    return NOT_STATED_QUOTE


def yes_no(value):
    """A yes / no / unknown answer as a word for the screen."""
    answer = yes_no_unknown(value)
    if answer is True:
        return "Yes"
    if answer is False:
        return "No"
    return "Not stated"


def costs_words(costs):
    """Claude's cost facts as one plain line."""
    parts = []
    yearly = as_number(costs.get("value_pct"))
    if yearly is not None:
        parts.append(f"{yearly:g}% a year")
    surrender = yes_no_unknown(costs.get("has_surrender_or_sales_charge"))
    if surrender is True:
        parts.append("has a surrender or sales charge")
    elif surrender is False:
        parts.append("no surrender or sales charge mentioned")
    return ", ".join(parts) if parts else "Not stated"


def promised_words(promised):
    """Claude's promised-return facts as one plain line."""
    value = as_number(promised.get("value_pct"))
    if value is None:
        return "No number promised"
    words = f"{value:g}% a year"
    if yes_no_unknown(promised.get("guaranteed")) is True:
        words += ", called guaranteed"
    return words


def show_fact(title, words, part):
    """One fact: its title, its value, the offer's own words, and the check tag."""
    st.markdown(f"**{title}:** {safe_text(words)}\n\n{check_line(part)}")


def show_offer_facts(answer):
    """What the offer says about each fact, with its quote."""
    st.markdown("#### 🔍 What the offer says")
    st.markdown(
        "These are the offer's own claims. The words in italics are quoted from it, "
        "and we checked that each quote is really there. "
        "The label above comes from our rules, not from these claims."
    )

    backed = get_part(answer, "government_backed")
    loss = get_part(answer, "loss_possible")
    access = get_part(answer, "access")
    costs = get_part(answer, "yearly_costs")
    promised = get_part(answer, "promised_return")

    # The titles say "Says…" so a claim is never mistaken for our own finding.
    show_fact("Says it's backed by the U.S. government?", yes_no(backed.get("value")), backed)
    show_fact("Says you could lose money?", yes_no(loss.get("value")), loss)
    show_fact("Getting money out", ACCESS_BADGES.get(access_word(access), "Not stated"), access)
    show_fact("Yearly costs", costs_words(costs), costs)
    show_fact("Promised return", promised_words(promised), promised)


def flag_line(item):
    """One red flag as a list line: the flag, its quote, and the check tag."""
    return f"- **{safe_text(item['flag'])}**  \n  {check_line(item)}"


def show_red_flags(answer):
    """The 'Warning signs we noticed' box.
    Only flags whose words were found in the offer count as warning signs."""
    flags = answer.get("red_flags")
    if not isinstance(flags, list):
        flags = []

    found = []
    unsure = []
    for item in flags:
        if not isinstance(item, dict) or not item.get("flag"):
            continue
        if item.get("check") == FOUND_TAG:
            found.append(item)
        else:
            unsure.append(item)

    with st.container(key="notes_red_flags"):
        st.markdown(f"#### {FLAGS_TITLE}")
        if found:
            st.markdown("\n".join(flag_line(item) for item in found))
        else:
            st.markdown(NO_FLAGS_LINE)
        if unsure:
            st.markdown(UNSURE_FLAGS_LINE)
            st.markdown("\n".join(flag_line(item) for item in unsure))


def show_questions_to_ask(answer):
    """The questions to ask before signing, as a numbered list."""
    questions = answer.get("questions_to_ask")
    if not isinstance(questions, list) or not questions:
        return
    st.markdown("#### 🙋 Questions to ask")
    lines = [f"{number}. {safe_text(q)}" for number, q in enumerate(questions, start=1)]
    st.markdown("\n".join(lines))


def show_plain_summary(answer):
    """The plain-language summary of the offer (already cleaned by checks.py)."""
    summary = answer.get("plain_summary")
    if isinstance(summary, str) and summary.strip():
        st.markdown(f"#### 📝 In plain words\n\n{safe_text(summary)}")


def show_offer_numbers(result, where_from, answer):
    """'Show me the numbers' for the offer: the steps, where each fact came from,
    and what the safety checks did."""
    with st.expander("Show me the numbers", icon="🔢"):
        step_lines = ["**How we picked the label:**", ""]
        for step in result["steps"]:
            step_lines.append(f"- {safe_text(step)}")
        st.markdown("\n".join(step_lines))

        source_lines = ["**Where each fact came from:**", ""]
        for item in where_from:
            source_lines.append(f"- {safe_text(item)}")
        st.markdown("\n".join(source_lines))

        # What checks.py did to this reading
        guards = answer.get("guards", {})
        found, not_found = quote_check_counts(answer)
        safety_lines = [
            "**Safety checks:**",
            "",
            f"- Quotes we found in the offer: {found}.",
            f"- Quotes we couldn't find, so we treat them as unknown: {not_found}.",
        ]
        if guards.get("not_rated"):
            safety_lines.append(
                "- The offer didn't match a product on our list, so it can't get a normal label."
            )
        if guards.get("gov_claim_warning"):
            safety_lines.append(f"- {GOV_CLAIM_WARNING}")
        if guards.get("summary_changed"):
            safety_lines.append(
                f"- A summary sentence sounded like advice, so we replaced it with: “{SAFE_SENTENCE}”"
            )
        st.markdown("\n".join(safe_text(line) for line in safety_lines))

        st.markdown(
            "The label never comes from the offer's own claims. "
            "Government backing, the worst year and protections always come from our product list."
        )


def show_offer_card(answer, is_demo):
    """The 'Your offer' card, built like the Explore cards.
    answer has already been through verify_quotes and apply_guards.
    is_demo is True when the reading is a saved one, not a live Claude check."""
    facts, product, where_from = build_offer_facts(answer)

    # scoring.py picks the tier, using the promised return for the scam check.
    promised = get_part(answer, "promised_return")
    result = assign_tier(
        facts,
        promised_return_pct=as_number(promised.get("value_pct")),
        guaranteed=yes_no_unknown(promised.get("guaranteed")) is True,
    )
    tier = result["tier"]

    if product is not None:
        compared_to = product["name"]
    else:
        compared_to = "none of the products on our list"

    with st.container(key="card_offer"):
        st.markdown("### 📄 Your offer")
        if is_demo:
            st.markdown(DEMO_CARD_LINE)
        st.markdown(f"**We compared this to:** {safe_text(compared_to)}")
        show_tier_heading(tier)
        show_gauge(tier)
        show_badges(result)
        # A worst-year number would be misleading on a possible scam.
        if tier != "off_map":
            show_worst_year(facts, result)
        show_offer_facts(answer)
        show_red_flags(answer)
        show_questions_to_ask(answer)
        show_plain_summary(answer)
        st.markdown(f"💬 {OFFER_CLOSING_LINE}")
        show_offer_numbers(result, where_from, answer)


def show_check_offer():
    """The Check an offer view: a text box, sample offers, a button, and the result."""
    st.warning(PRIVACY_LINE, icon="🛡️")
    st.markdown(
        "Paste the words from a letter, brochure, email or ad. "
        "Or pick one of our made-up sample offers."
    )

    # The sample dropdown fills the big text box.
    samples = load_sample_offers()
    demo_answers = load_demo_answers() if DEMO_MODE else {}

    if samples:
        st.selectbox(
            SAMPLE_LABEL,
            list(samples.keys()),
            index=None,
            placeholder="Choose OFFER 1 to 6",
            key="sample_choice",
            on_change=load_sample,
            args=(samples,),
        )
        if demo_answers:
            st.markdown(DEMO_NOTICE)
    else:
        st.markdown("📂 Sample offers not found. Check that data/sample_offers.md exists.")

    # Streamlit forgets a text box when you visit another page,
    # so we keep our own copy and put it back when you return.
    if "offer_text" not in st.session_state:
        st.session_state["offer_text"] = st.session_state.get("saved_offer_text", "")

    st.text_area(OFFER_BOX_LABEL, key="offer_text", height=320, max_chars=OFFER_MAX_CHARS)
    st.session_state["saved_offer_text"] = st.session_state["offer_text"]

    clicked = st.button(CHECK_BUTTON, key="check_offer", type="primary", width="stretch")

    text = st.session_state["offer_text"].strip()
    # Readings we already have, by offer text, so Claude is never asked twice.
    # Each one is stored as {"answer": ..., "is_demo": True or False}.
    cache = st.session_state.setdefault("offer_cache", {})

    if clicked and not text:
        st.warning("Please paste an offer or pick a sample first.", icon="✋")
    elif clicked and text not in cache:
        demo_answer = find_demo_answer(text, samples, demo_answers)
        if demo_answer is not None:
            # A sample offer in demo mode: use the saved reading, no Claude call.
            cache[text] = {"answer": demo_answer, "is_demo": True}
        else:
            # Anything else: ask Claude.
            with st.spinner(SPINNER_TEXT):
                product_names = [product["name"] for product in PRODUCTS]
                answer, error = read_offer(text, product_names)
            if error:
                st.error(error, icon="😕")
            else:
                cache[text] = {"answer": answer, "is_demo": False}

    # Show the card whenever we already have a reading for this exact text.
    scam_shown = False
    if text and text in cache:
        entry = cache[text]
        # The safety layer runs on EVERY reading, saved or live, before scoring:
        # 1. check each quote against the pasted text, 2. apply the guards.
        checked = verify_quotes(text, entry["answer"])
        guarded = apply_guards(checked)
        guards = guarded["guards"]

        # Any warning sign found: the scam card goes ABOVE the result.
        if guards["show_scam_card"]:
            show_scam_card("card_scam_top", found_count=guards["red_flag_count"])
            scam_shown = True

        show_offer_card(guarded, entry["is_demo"])

    # At the bottom: the scam card (unless it's already above), the help card,
    # and "Something looks wrong?"
    show_safety_cards(include_scam=not scam_shown)


# ---------- Build the page, top to bottom ----------

# Start on Welcome the first time (or if the saved view is unknown)
if st.session_state.get("view") not in VIEWS:
    st.session_state["view"] = "Welcome"

st.markdown(CSS, unsafe_allow_html=True)

show_notice()
show_nav()
show_heading()

if st.session_state["view"] == "Welcome":
    show_welcome()
elif st.session_state["view"] == "Your situation":
    show_situation()
elif st.session_state["view"] == "Explore products":
    show_explore()
elif st.session_state["view"] == "Compare":
    show_compare()
elif st.session_state["view"] == "Check an offer":
    show_check_offer()
else:
    show_coming_soon()

show_start_over()