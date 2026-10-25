# app.py
# The screens of Second Look.
# Run it with:  streamlit run app.py

import datetime
import html
import json
import os
import time

import streamlit as st
import streamlit.components.v1 as components

from charts import (
    HISTORY_MISSING,
    HISTORY_SERIES,
    RUN_LENGTHS,
    SERIES_KEYS,
    START_YEARS,
    load_history,
    show_fees_chart,
    show_product_risk,
    show_growth_card,
    show_history_note,
    show_returns_card,
    show_worst_year_chart,
)
from checks import (
    FOUND_TAG,
    GOV_CLAIM_WARNING,
    NOT_FOUND_TAG,
    SAFE_SENTENCE,
    apply_guards,
    quote_check_counts,
    verify_quotes,
)
# claude_helper.py keeps its old name, but it now asks Grok to read offers.
from claude_helper import read_offer
# Optional accounts (Supabase). Guests never need them.
import db
from demo_replay import (
    REPLAY_OFFER,
    banner_text,
    load_replay,
    recorded_date_words,
    saved_audio,
)
from footer import show_footer
from live_data import (
    UNAVAILABLE_NOTE,
    any_missing,
    get_live_rates,
    inflation_line,
    rate_line,
    tbill_rate_for_scoring,
)
# The My products view (for signed-in people) lives in my_products.py.
import my_products
from products import PRODUCTS
# The words the voice says, and the helpers that read the AI's answer,
# live in results.py, so the app and save_demo_cache.py always match.
from results import (
    EXAMPLE_AMOUNT,
    NOT_RATED_SENTENCE,
    OFF_MAP_SENTENCE,
    OFFER_CLOSING_LINE,
    access_word,
    as_number,
    build_offer_facts,
    card_words,
    get_part,
    get_tier_info,
    is_quoted,
    offer_words,
    score_offer,
    yes_no_unknown,
)
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
from styles import apply_styles
from voice_helper import (
    DEFAULT_SPEED,
    SPEED_NORMAL,
    SPEED_SLOWER,
    get_speech,
    get_transcript,
)
# PRIVACY_NOTICE lives in welcome.py, so Welcome and My account say the same thing.
from welcome import PRIVACY_NOTICE, WELCOME_WORDS, show_welcome

# ---------- Page setup (this must be the first Streamlit command) ----------
st.set_page_config(
    page_title="Second Look",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# The look and feel: fonts, colors, sizes and spacing all live in styles.py.
apply_styles()

# Let content and notices use the available page width. Existing columns
# still control their own layout, and text wraps normally on small screens.
st.markdown(
    """
    <style>
    /* Captions and privacy paragraphs use their full parent width. */
    .stApp p,
    .stApp [data-testid="stCaptionContainer"],
    .stApp [data-testid="stCaptionContainer"] p,
    .stApp .stCaption {
        max-width: none !important;
    }
    .stApp [data-testid="stCaptionContainer"],
    .stApp [data-testid="stCaptionContainer"] p {
        width: 100% !important;
        box-sizing: border-box !important;
        white-space: normal !important;
    }
    /* Modal and backdrop must sit above the fixed navigation header. */
    [data-testid="stDialog"], [data-baseweb="modal"] {
        z-index: 2000000 !important;
    }
    [data-testid="stDialog"] [role="dialog"] {
        max-height: calc(100dvh - 48px) !important;
        overflow-y: auto !important;
    }
    .stApp [data-testid="stMainBlockContainer"],
    .stApp .main .block-container,
    .stApp .stMain .block-container {
        width: 100% !important;
        max-width: none !important;
        padding-left: clamp(1rem, 3vw, 3rem) !important;
        padding-right: clamp(1rem, 3vw, 3rem) !important;
        box-sizing: border-box !important;
    }
    .stApp [data-testid="stMarkdownContainer"],
    .stApp [data-testid="stMarkdownContainer"] p,
    .stApp [data-testid="stMarkdownContainer"] ul,
    .stApp [data-testid="stMarkdownContainer"] ol {
        max-width: none !important;
    }
    .stApp [data-testid="stAlert"],
    .stApp [data-testid="stAlertContainer"],
    .stApp [data-testid="stAlertContent"],
    .stApp [data-testid="stAlert"] [data-testid="stMarkdownContainer"],
    .stApp [data-testid="stAlertContainer"] [data-testid="stMarkdownContainer"] {
        width: 100% !important;
        max-width: none !important;
        min-width: 0 !important;
        box-sizing: border-box !important;
    }
    .stApp [data-testid="stAlert"] p,
    .stApp [data-testid="stAlertContainer"] p {
        max-width: none !important;
        white-space: normal !important;
        overflow-wrap: break-word !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Demo mode ----------
# True: the six sample offers use saved readings from data/sample_answers.json,
#       so they work without calling the AI (no API credits needed).
# False: every offer, samples included, is read live by the AI.
DEMO_MODE = True

# ---------- Demo replay (the big switch at the top of every page) ----------
# When it is on, the app plays back one real run saved by save_demo_cache.py:
# the AI's reading of OFFER 1 and the saved voices. No AI, no Cartesia.
REPLAY_ON_BUTTON = "📼 Demo replay is OFF. Click to turn it on (no internet needed)"
REPLAY_OFF_BUTTON = "📼 Demo replay is ON. Click to go back to live mode"
REPLAY_MISSING = (
    "Demo replay has no saved run yet. With the internet on, run "
    "`python save_demo_cache.py` once from the project folder, then reload this page."
)
REPLAY_NO_VOICE = (
    "Demo replay has no saved voice for these exact words. "
    "The captions below show what would be said."
)
REPLAY_NO_RECORDING = (
    "Saying it out loud needs the internet, so it is off during Demo replay. "
    "Pick a sample instead, or turn Demo replay off."
)
REPLAY_LIVE_OFF = (
    f"During Demo replay, only the samples can be checked. {REPLAY_OFFER} uses a real saved run. "
    "Turn Demo replay off to check other words live."
)
REPLAY_SAMPLE_NOTICE = (
    f"📼 **Demo replay is on.** {REPLAY_OFFER} plays back a real, saved run by the AI. "
    "The other samples use saved, hand-written readings."
)

# ---------- The eight views, in the order their buttons appear ----------
VIEWS = [
    "Welcome",
    "Your situation",
    "Explore products",
    "Compare",
    "Check an offer",
    "History",
    "My products",
    "My account",
]

# The notice shown at the top of every view (and again in the footer).
# One sentence, so it fits on one line on a wide screen.
NOTICE = (
    "Second Look explains money products in plain language "
    "and is educational, not professional financial advice."
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

# The titles above the two badges
ACCESS_TITLE = "Getting money out"
COST_TITLE = "Cost"

# Special worst-year lines
SAFE_HARBOR_LINE = "Safe from losses, not from rising prices. Insured up to $250,000 per bank."
BIG_LOSS_LINE = "Could lose most or all."

# Which live rate belongs to which product (keys from SERIES in live_data.py)
RATE_FOR_PRODUCT = {
    "savings": "savings",
    "cd12": "cd12",
    "tbill": "tbill",
    "bondindex": "ten_year",
}


def todays_rate(product):
    """This product's rate line, live or saved. None if it has no rate."""
    rate_key = RATE_FOR_PRODUCT.get(product.get("key"))
    if rate_key is None:
        return None
    return rate_line(get_live_rates(), rate_key)


# ---------- Voice: words and settings ----------
SPEED_LABEL = "Voice speed"
SPEED_CHOICES = [SPEED_SLOWER, SPEED_NORMAL]
SPEED_ICONS = {SPEED_SLOWER: "🐢", SPEED_NORMAL: "🚶"}

READ_BUTTON = "🔊 Read aloud"
LISTEN_BUTTON = "🔊 Listen to the result"
WELCOME_LISTEN_BUTTON = "🔊 Hear this page"
STOP_BUTTON = "⏹️ Stop and hide the voice"
VOICE_SPINNER = "Getting the voice ready…"
CAPTIONS_TITLE = "💬 Captions: the words being spoken"

# What "Hear this page" says on the Welcome view lives in welcome.py (WELCOME_WORDS).

# ---------- Check an offer: settings and words ----------

DATA_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# Where the made-up sample offers live
SAMPLE_OFFERS_FILE = os.path.join(DATA_FOLDER, "sample_offers.md")

# Where the saved, hand-written readings of those samples live (for demo mode)
SAMPLE_ANSWERS_FILE = os.path.join(DATA_FOLDER, "sample_answers.json")

# The longest offer someone can paste (keeps the AI calls small)
OFFER_MAX_CHARS = 6000

# Step 1: choose one of three ways
STEP_ONE_TITLE = "Step 1 of 3: Choose how to give us the offer"
STEP_ONE_TEXT = "Pick one way. You can switch to another way at any time."
WAY_LABEL = "How would you like to give us the offer?"
WAY_TYPE = "⌨️ Paste or type it"
WAY_SAY = "🎙️ Say it out loud"
WAY_SAMPLE = "📄 Try a made-up sample"
WAYS = [WAY_TYPE, WAY_SAY, WAY_SAMPLE]
OFFER_PRIVACY_LINE = (
    "🛡️ **Keep it private:** don't type or say your name, account numbers, "
    "or Social Security number. We never need them."
)

# Step 2: its title depends on the way chosen in step 1
STEP_TWO_TITLES = {
    WAY_TYPE: "Step 2 of 3: Paste or type the offer",
    WAY_SAY: "Step 2 of 3: Tell us what was said",
    WAY_SAMPLE: "Step 2 of 3: Pick a sample",
}
TYPE_HELP = (
    "Copy the words from a letter, email or ad and paste them in the box, "
    "or type what the salesperson said. Then press **🔎 Check this offer**."
)
OFFER_BOX_LABEL = "The offer's words"
OFFER_BOX_PLACEHOLDER = "Paste or type what the salesperson, letter or ad said."
SAMPLE_HELP = (
    "These six offers are made up for practice. "
    "Pick one, and its result appears right away in step 3."
)
SAMPLE_LABEL = "📄 Sample offer"
SAMPLE_WORDS_LABEL = "Read this sample's words"
CHECK_BUTTON = "🔎 Check this offer"
SPINNER_TEXT = "Reading the offer…"
EMPTY_WARNING = "Please put the offer's words in the box first."
RESULT_READY_LINE = "⬇️ **Your result is ready** in step 3, just below."

# Step 3: the result
RESULT_TITLE = "Step 3 of 3: Your result"
OFFER_WAITING_TEXT = (
    "Your result will appear here after step 2: our label, "
    "any warning signs, and questions to ask before you sign."
)

# "Risk in numbers", inside the offer's "Show me the numbers" box
RISK_NUMBERS_TITLE = "📊 Risk in numbers"
RISK_NUMBERS_NOTE = (
    "These numbers come from the past years of the kind of product we compared this offer to, "
    "not from this exact offer. They don't change our label."
)
RISK_NUMBERS_OFF_MAP = (
    "⚠️ **No risk numbers for this offer.** It shows warning signs of a possible scam, "
    "so past numbers from a real product could make it look safer than it is."
)
RISK_NUMBERS_NOT_RATED = (
    "❓ **No risk numbers for this offer.** It didn't match a product on our list, "
    "so we have no past years to measure it against."
)

# Saving a check to My history (signed-in people only)
SAVE_HISTORY_BUTTON = "💾 Save to my history"
SAVE_HISTORY_NOTE = (
    "Only the category, our label, the two badges and the plain summary are saved. "
    "The words you pasted or said are never saved."
)
SAVED_HISTORY_LINE = "💾 **Saved to My history.** You can find it, or delete it, on **My account**."

# The warning signs box in the result
FLAGS_TITLE = "⚠️ Warning signs we noticed"
NO_FLAGS_LINE = "We didn't notice any warning signs in this text. That alone doesn't make it safe."
FLAGS_FOUND_LINE = (
    "Honest investments don't do these things. The **🚩 How to spot a scam** card "
    "at the bottom of this page says what to do next."
)
NOT_STATED_QUOTE = "*The offer doesn't say.*"

# Voice input on Check an offer
RECORD_LABEL = "🎙️ Your recording"
RECORD_HELP_LINE = (
    "Press the microphone, say what you were told (or read the letter aloud), "
    "then press stop. Your recording is sent to Cartesia, a voice service, to turn it into words."
)
LISTEN_SPINNER = "Listening to your recording…"
HEARD_TITLE = "👂 I heard:"
HEARD_CHECK_LINE = "Is this right? Nothing goes in the box until you say yes."
USE_HEARD_BUTTON = "✅ Yes, use this"
TRY_AGAIN_BUTTON = "🔁 Try again"
HEARD_USED_LINE = (
    "Done. Here is what you said. Fix any words that are wrong, "
    "then press **🔎 Check this offer**."
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
    "so they work without the AI. Anything you paste or change is checked live by the AI."
)
DEMO_CARD_LINE = (
    "📼 **Demo mode:** this is a saved, hand-written reading of a sample offer, "
    "not a live check by the AI. The label still comes from our own rules."
)

# ---------- History: words for the choices ----------
HISTORY_INTRO = (
    "See how U.S. stocks, Treasury bonds and Treasury bills did in every year since 1928, "
    "and what $10,000 would have become."
)
HISTORY_SERIES_LABEL = "Which one?"
START_YEAR_LABEL = "📅 Start year"
RUN_LENGTH_LABEL = "For how long?"

# ---------- My account: words ----------
ACCOUNT_CONSENT = (
    "I agree that Second Look saves my answers, the products I add, and summaries "
    "of offers I check, so I can see them next time. I can download or delete "
    "everything at any time."
)
ACCOUNT_INTRO = (
    "An account is optional. Without one, every page still works. "
    "With one, your answers and your products are waiting for you next time."
)
MY_HISTORY_TITLE = "🗂️ My history"
MY_HISTORY_EMPTY = (
    "You haven't saved any offer checks yet. After you check an offer, "
    "press **💾 Save to my history** to keep a summary here."
)
DOWNLOAD_TITLE = "⬇️ Download my data"
DOWNLOAD_TEXT = (
    "One file with everything saved for your account: your answers, your products, "
    "and your saved offer checks."
)
DOWNLOAD_BUTTON = "⬇️ Download my data"
DOWNLOAD_FILE_NAME = "second-look-my-data.json"
DELETE_ACCOUNT_TITLE = "🗑️ Delete my account"
DELETE_ACCOUNT_TEXT = (
    "This deletes your account and everything saved for it: your answers, your products "
    "and your saved offer checks. It can't be undone. You may want to download your data first."
)
DELETE_CONFIRM_LABEL = "To confirm, type DELETE in capital letters"
DELETE_ACCOUNT_BUTTON = "🗑️ Delete my account and everything saved"
DELETE_CONFIRM_WORD = "DELETE"
ACCOUNT_DELETED = "Your account and all your saved information have been deleted."

# ---------- Safety cards (shown on Check an offer, Explore products and Compare) ----------

HELP_CARD_TITLE = "☎️ Before a big decision"
# The same numbers are in HELP_LINES in footer.py. If one changes, change both.
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


# ---------- Small helper functions ----------

def go_to(view_name):
    """Runs when a page button is clicked: remember which page to show.
    Any voice that was playing stops, so it never starts again by surprise."""
    st.session_state["view"] = view_name
    st.session_state["scroll_to_top_request"] = time.time_ns()
    st.session_state.pop("now_speaking", None)


def start_over():
    """Runs when Start over is clicked: forget everything except
    the page, the Demo replay switch, and the sign-in (if any).
    Saved products and history stay in the account; they are loaded again when needed."""
    keep = ("view", "replay_on", db.CLIENT_KEY, db.ACCOUNT_KEY)
    for key in list(st.session_state.keys()):
        if key not in keep:
            del st.session_state[key]
    # A one-time flag so we can tell the person it worked
    st.session_state["just_cleared"] = True


def safe_text(text):
    """Streamlit shows text between two $ signs as math.
    A backslash in front of each $ keeps it a plain dollar sign."""
    return str(text).replace("$", "\\$")


def safe_key(text):
    """Letters, numbers and _ only, so it can be part of a button's key."""
    return "".join(letter if letter.isalnum() else "_" for letter in str(text))


def show_notice():
    """The educational notice at the top of every view, centered.
    The key "notice_top" lets styles.py draw its light box
    and put the sentence in the middle."""
    with st.container(key="notice_top"):
        st.markdown(f"ℹ️ {NOTICE}")


def show_nav():
    """Eight compact page buttons, with single-line labels on desktop."""
    # Scope these overrides to navigation so other controls keep their styles.
    st.markdown(
        """
        <style>
        /* A full-width header anchored to the viewport, without a top gap. */
        [data-testid="stHeader"] {
            display: none !important;
        }
        .st-key-main_nav {
            position: fixed !important;
            inset: 0 0 auto 0 !important;
            width: 100% !important;
            max-width: none !important;
            height: 64px !important;
            box-sizing: border-box !important;
            z-index: 1000000 !important;
            background: #fbfaf7 !important;
            border: 0 !important;
            border-bottom: 1px solid #dedfdc !important;
            border-radius: 0 !important;
            padding: 8px clamp(8px, 1.5vw, 24px) !important;
            margin: 0 !important;
            box-shadow: 0 2px 8px rgba(22, 35, 63, 0.04) !important;
            overflow-x: hidden !important;
            overflow-y: hidden !important;
        }
        .st-key-main_nav [data-testid="stHorizontalBlock"] {
            display: grid !important;
            grid-template-columns: 0.85fr 1.15fr 1.4fr 0.85fr 1.2fr 0.75fr 1.1fr 1.05fr !important;
            gap: 4px !important;
            width: 100% !important;
            max-width: none !important;
            margin: 0 auto !important;
        }
        .st-key-main_nav [data-testid="stColumn"] {
            min-width: 0 !important;
            width: 100% !important;
        }
        .st-key-main_nav button {
            box-sizing: border-box !important;
            width: 100% !important;
            height: 48px !important;
            min-height: 48px !important;
            padding: 6px 4px !important;
            border: 1px solid transparent !important;
            border-radius: 8px !important;
            background: transparent !important;
            color: #536074 !important;
            box-shadow: none !important;
            white-space: nowrap !important;
            overflow: visible !important;
            transition: background 150ms ease, color 150ms ease !important;
        }
        .st-key-main_nav button:hover {
            background: #eeefed !important;
            color: #17243e !important;
        }
        .st-key-main_nav button[kind="primary"],
        .st-key-main_nav [data-testid="stBaseButton-primary"] {
            background: #17243e !important;
            color: #ffffff !important;
            border-color: #17243e !important;
        }
        .st-key-main_nav button:focus-visible {
            outline: 3px solid #ad8750 !important;
            outline-offset: -3px !important;
        }
        .st-key-main_nav button [data-testid="stMarkdownContainer"],
        .st-key-main_nav button [data-testid="stMarkdownContainer"] p {
            width: 100% !important;
            min-width: 0 !important;
            height: auto !important;
            max-height: none !important;
            white-space: nowrap !important;
            overflow: visible !important;
            text-overflow: clip !important;
            -webkit-line-clamp: unset !important;
            display: block !important;
            text-align: center !important;
            font-family: "Times New Roman", Times, serif !important;
            font-size: clamp(12px, 1.1vw, 18px) !important;
            font-weight: 600 !important;
            letter-spacing: 0 !important;
            line-height: 1.3 !important;
            color: inherit !important;
            margin: 0 !important;
        }
        /* Reserve the header height once, without an additional spacer. */
        [data-testid="stMainBlockContainer"],
        .main .block-container,
        .stMain .block-container {
            padding-top: 64px !important;
        }
        .st-key-notice_top {
            margin-top: 0 !important;
        }
        @media (max-width: 700px) {
            .st-key-main_nav { height: 112px !important; }
            .st-key-main_nav [data-testid="stHorizontalBlock"] {
                grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
            }
            .st-key-main_nav button [data-testid="stMarkdownContainer"],
            .st-key-main_nav button [data-testid="stMarkdownContainer"] p {
                font-size: 12px !important;
            }
            [data-testid="stMainBlockContainer"],
            .main .block-container, .stMain .block-container {
                padding-top: 112px !important;
            }
        }
        @media (prefers-reduced-motion: reduce) {
            .st-key-main_nav button { transition: none !important; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    current = st.session_state["view"]
    with st.container(key="main_nav"):
        columns = st.columns(len(VIEWS), gap="small")
        for number, view_name in enumerate(VIEWS):
            is_current = view_name == current
            label = view_name
            if is_current:
                label = f"**{label}**"
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


# ---------- Demo replay: the switch and the banner ----------

def replay_on():
    """True while Demo replay is switched on."""
    return st.session_state.get("replay_on", False)


def toggle_replay():
    """Runs when the Demo replay button is clicked: switch it on or off.
    Old results and any playing voice are cleared, so live and replay never mix."""
    st.session_state["replay_on"] = not replay_on()
    st.session_state.pop("now_speaking", None)
    st.session_state.pop("offer_cache", None)


def show_replay_switch():
    """The big Demo replay button, and the banner while it is on.
    The button's words always say whether replay is ON or OFF."""
    if replay_on():
        label, kind = REPLAY_OFF_BUTTON, "primary"
    else:
        label, kind = REPLAY_ON_BUTTON, "secondary"
    st.button(label, key="replay_switch", on_click=toggle_replay, type=kind, width="stretch")

    if replay_on():
        # The key "replay_banner" lets styles.py use the full width for the banner.
        with st.container(key="replay_banner"):
            saved = load_replay()
            if saved is not None:
                st.info(banner_text(saved), icon="📼")
            else:
                st.warning(REPLAY_MISSING, icon="📂")


# ---------- Voice: speaking out loud, with captions ----------
# Only one thing speaks at a time. st.session_state["now_speaking"] holds
# the exact words being spoken. A player appears wherever those words belong.

def current_speed():
    """The voice speed picked on the Welcome view ("Slower" unless changed)."""
    return st.session_state.get("voice_speed", DEFAULT_SPEED)


def save_speed():
    """Runs when the speed is changed. We keep our own copy,
    because Streamlit forgets a choice when you visit another page."""
    st.session_state["voice_speed"] = st.session_state["voice_speed_choice"]


def start_speaking(words):
    """Runs when a Read aloud or Listen button is clicked."""
    st.session_state["now_speaking"] = words


def stop_speaking():
    """Runs when Stop is clicked: hide the player, which stops the sound."""
    st.session_state.pop("now_speaking", None)


def show_voice(words):
    """If these words were asked for, play them and show them as captions.
    In Demo replay, the voice comes from a saved file, never from Cartesia.
    If the voice fails, the captions still show, with a calm message."""
    if st.session_state.get("now_speaking") != words:
        return

    if replay_on():
        audio = saved_audio(words)
        error = None if audio else REPLAY_NO_VOICE
    else:
        with st.spinner(VOICE_SPINNER):
            audio, error = get_speech(words, current_speed())

    if error:
        st.info(error, icon="🔇")
    else:
        # It plays by itself once. The player's buttons replay or pause it.
        st.audio(audio, format="audio/wav", autoplay=True)

    # The captions: exactly the words being spoken
    with st.container(key="notes_captions"):
        st.markdown(f"#### {CAPTIONS_TITLE}")
        st.markdown(safe_text(words))

    st.button(STOP_BUTTON, key="stop_speaking", on_click=stop_speaking, width="stretch")


# ---------- Welcome: the voice card ----------
# The rest of the Welcome view lives in welcome.py.

def show_speed_setting():
    """The voice card: the speed choice, and a button to try the voice."""
    # Put back the saved choice when coming back to this page.
    if "voice_speed_choice" not in st.session_state:
        st.session_state["voice_speed_choice"] = current_speed()

    with st.container(key="card_voice"):
        st.markdown("### 🔊 Voice")
        st.markdown(
            "Second Look can read to you. Every product card has a **🔊 Read aloud** button, "
            "and **Check an offer** has **🔊 Listen to the result**. "
            "You can also tell us about an offer out loud."
        )
        st.radio(
            SPEED_LABEL,
            SPEED_CHOICES,
            key="voice_speed_choice",
            on_change=save_speed,
            format_func=lambda choice: f"{SPEED_ICONS[choice]} {choice}",
        )
        st.button(
            WELCOME_LISTEN_BUTTON,
            key="read_welcome",
            on_click=start_speaking,
            args=(WELCOME_WORDS,),
            type="primary",
            width="stretch",
        )
        show_voice(WELCOME_WORDS)


# ---------- Safety cards: help, scam, and "Something looks wrong?" ----------

def show_help_card():
    """Where to get a trusted second opinion."""
    with st.container(key="card_help"):
        st.markdown(f"### {HELP_CARD_TITLE}")
        st.markdown(HELP_CARD_TEXT)


def show_scam_card(key):
    """The "How to spot a scam" card."""
    with st.container(key=key):
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


def show_safety_cards():
    """The cards at the bottom of Check an offer, Explore products and Compare:
    the scam card and the help card, side by side on wide screens."""
    st.divider()
    with st.container(key="split_safety"):
        show_scam_card("card_scam")
        with st.container(key="safety_help"):
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
    # The top of the page: what to do (left) and the privacy reminder (right).
    with st.container(key="split_questions"):
        with st.container(key="questions_intro"):
            st.markdown(
                "Pick one answer for each question. You can change them later.\n\n"
                f"Your answers add short notes under **{NOTES_TITLE}** on each product card."
            )
        st.warning(PRIVACY_LINE, icon="🛡️")

    saved = st.session_state.get("answers") or {}

    # The five question cards. styles.py puts them in two columns on wide screens,
    # in reading order: 1 and 2, then 3 and 4, then 5.
    with st.container(key="grid_questions"):
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
            # Signed in: also save them to the account. Guests: nothing is saved.
            if db.is_signed_in():
                ok, message = db.save_answers(answers)
                st.session_state["save_note"] = (ok, message)
            st.rerun()  # draw the page again, now showing the summary


def show_answer_summary(answers):
    """The "Here's what you told us" card (left) and what happens next (right)."""
    with st.container(key="split_summary"):
        with st.container(key="card_summary"):
            st.markdown("### 📋 Here's what you told us")
            lines = []
            for question in QUESTIONS:
                answer = answers.get(question["key"], "Not answered")
                lines.append(f"**{safe_text(question['short'])}:** {safe_text(answer)}")
            st.markdown("\n\n".join(lines))
            st.button("✏️ Edit my answers", key="edit_answers", on_click=start_editing, width="stretch")

        with st.container(key="card_next"):
            st.markdown("### 🧭 What happens next")
            st.markdown(
                f"Your answers add short notes under **{NOTES_TITLE}** on each product card."
            )
            # Did saving to the account just work? Say so once, with an icon and words.
            note = st.session_state.pop("save_note", None)
            if note is not None:
                ok, message = note
                if ok:
                    st.success(message, icon="✅")
                else:
                    st.warning(message, icon="⚠️")
            if db.is_signed_in():
                st.markdown(
                    f"💾 Your answers are saved to your account ({safe_text(db.current_email())})."
                )
            else:
                st.markdown(
                    "🔒 Your answers stay on this page only, until you close it or click **Start over**."
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
        st.markdown(f"### ⚠️ {tier_label(tier)}\n\n**{OFF_MAP_SENTENCE}**")
    else:
        st.markdown(f"### ❓ {tier_label(tier)}\n\n**{NOT_RATED_SENTENCE}**")


def show_product_name(product):
    """Card part 2: the product name and its one-line description."""
    st.markdown(f"#### {safe_text(product['name'])}\n\n{safe_text(product['one_line'])}")


def show_read_aloud(product, result):
    """Card part 3: the Read aloud button, near the top so it is easy to find.
    When clicked, the voice and the captions appear right under it."""
    words = card_words(product, result)
    st.button(
        READ_BUTTON,
        key=f"read_{product['key']}",
        on_click=start_speaking,
        args=(words,),
        type="primary",
        width="stretch",
    )
    show_voice(words)


def show_gauge(tier):
    """Card part 4: the two gauges, drawn with blocks AND words."""
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


def badge_html(title, icon, word):
    """One badge: its title, then its icon and word side by side.
    The icon is hidden from screen readers, because the word says the same thing."""
    return (
        '<div class="badge">'
        f'<p class="badge-title">{html.escape(title)}</p>'
        '<p class="badge-value">'
        f'<span class="badge-icon" aria-hidden="true">{html.escape(icon)}</span>'
        f"<span>{html.escape(word)}</span>"
        "</p>"
        "</div>"
    )


def show_badges(result):
    """Card part 5: the access badge and the cost badge, as big as the tier name.
    styles.py puts them side by side when they fit, or one under the other
    when the card is narrow. Each icon always stays next to its word."""
    access = result["access_badge"]
    cost = result["cost_badge"]
    row = (
        '<div class="badge-row">'
        f"{badge_html(ACCESS_TITLE, ACCESS_ICONS.get(access, '❔'), access)}"
        f"{badge_html(COST_TITLE, COST_ICONS.get(cost, '❔'), cost)}"
        "</div>"
    )
    # Everything on one line: Streamlit could misread spaces at the start of a line.
    st.markdown(row, unsafe_allow_html=True)


def show_worst_year(product, result):
    """Card part 6: what $10,000 would have become in the worst year."""
    tier = result["tier"]

    if tier == 1:
        st.markdown(f"**{safe_text(SAFE_HARBOR_LINE)}**")
        # How much prices rose this past year, from FRED
        prices = inflation_line(get_live_rates())
        if prices:
            st.markdown(f"📈 {safe_text(prices)}")
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
    """Card part 7: notes from the Your situation answers.
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


@st.dialog("Show me the numbers", width="large")
def show_numbers(product, result):
    """One popup containing the product facts and quantitative risk details."""
    st.markdown(f"### {safe_text(product['name'])}")
    st.markdown("#### Product details")
    # The facts from products.py
    loss = product["worst_year_loss_pct"]
    loss_text = "not known yet" if loss is None else f"{loss:g}%"

    cost = product["yearly_cost_pct"]
    cost_text = "Not known yet." if cost is None else f"{cost:g}% a year."

    # Today's rate, only for products that have one
    rate = todays_rate(product)
    rate_part = f"**📡 {safe_text(rate)}**\n\n" if rate else ""

    st.markdown(
        f"**Worst year:** {safe_text(product['worst_year'])}\n\n"
        f"**Loss in that year:** {loss_text}\n\n"
        f"**What it might earn:** {safe_text(product['gain_note'])}\n\n"
        + rate_part
        + f"**Yearly cost:** {cost_text} {safe_text(product['cost_note'])}\n\n"
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

    st.divider()
    st.markdown("#### Risk in numbers")
    show_product_risk(product, inline=True)
    st.divider()
    if st.button("Close", key="close_product_numbers", width="stretch"):
        st.rerun()


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


def show_compare_box(product):
    """Card part 9: the Compare checkbox."""
    key = product["key"]
    box_key = f"compare_box_{key}"

    # When coming back to this page, tick the box again if it was chosen before.
    if box_key not in st.session_state:
        st.session_state[box_key] = key in st.session_state.get("compare_keys", [])

    st.checkbox("Compare", key=box_key, on_change=toggle_compare, args=(key,))


def show_notes_prompt():
    """Explore's side card: where the "Worth thinking about" notes come from."""
    with st.container(key="card_notes_prompt"):
        st.markdown(f"#### {NOTES_TITLE}")
        if st.session_state.get("answers"):
            st.markdown("Your answers are saved, so every card below shows short notes for you.")
            st.button(
                "📋 See my answers",
                key="goto_situation",
                on_click=go_to,
                args=("Your situation",),
                width="stretch",
            )
        else:
            st.markdown(
                "Answer the five questions on **Your situation** to see short notes "
                "on each card below."
            )
            st.button(
                "🧭 Go to Your situation",
                key="goto_situation",
                on_click=go_to,
                args=("Your situation",),
                type="primary",
                width="stretch",
            )


def show_explore():
    """The Explore products view: one big card per product."""
    # The top of the page: what this page shows (left) and the notes card (right).
    with st.container(key="split_explore"):
        with st.container(key="explore_intro"):
            st.markdown(
                "Every product is listed here, from the calmest water (**⚓ Safe Harbor**) "
                "to the wildest (**⚠️ Uncharted Waters**).\n\n"
                "Press **🔊 Read aloud** on any card to hear it. "
                "Open **Show me the numbers** to see the facts and sources behind its label.\n\n"
                "Tick **Compare** on any cards to see them side by side on the **Compare** page."
            )
        show_notes_prompt()

    # The worst-year chart (charts.py), above the cards.
    show_worst_year_chart(sorted_products())

    # One card per product. styles.py lays them out in a grid:
    # three per row on wide screens, two on medium screens, one on phones.
    with st.container(key="grid_products"):
        for product, result in sorted_products():
            # The key gives this card a name, so styles.py can draw its border.
            with st.container(key=f"card_{product['key']}"):
                show_tier_heading(result["tier"])
                show_product_name(product)
                show_read_aloud(product, result)
                show_gauge(result["tier"])
                show_badges(result)
                show_worst_year(product, result)
                show_fit_notes(product)
                if st.button("Show me the numbers", key=f"numbers_{product['key']}", width="stretch"):
                    show_numbers(product, result)
                show_compare_box(product)

    # The scam card, the help card and "Something looks wrong?"
    show_safety_cards()


# ---------- Compare: a side-by-side table ----------
# The products come from the Compare boxes ticked on Explore products.
# The table is plain HTML, so styles.py can draw it like a comparison page.

COMPARE_EMPTY = (
    "You haven't picked any products yet. On **Explore products**, tick the "
    "**Compare** box on each product you want to see side by side."
)
COMPARE_HOW = "To add or remove a product, tick or untick its **Compare** box on **Explore products**."
COMPARE_ONE_MORE = "Tick at least one more product to see them side by side."
COMPARE_SCROLL_HINT = (
    "↔️ If the table is wider than your screen, slide it sideways to see every product."
)
COMPARE_LABEL_NOTE = (
    "Every label comes from our published rules, never from a salesperson. "
    "Open **Show me the numbers** on any card in Explore products to see how it was picked."
)

# Yes, no or not known: always an icon AND a word.
# The marks are neutral (✔ means yes, ✖ means no), not "good" or "bad".
YES_NO_CELLS = {
    True: ("✔", "Yes"),
    False: ("✖", "No"),
    None: ("❓", "Not known"),
}


def cell_text(text):
    """Text that is safe to put inside the table's HTML.
    &#36; is a plain dollar sign, so Streamlit never treats it as math."""
    return html.escape(str(text)).replace("$", "&#36;")


def icon_html(icon):
    """An icon that screen readers skip, because a word always comes with it."""
    return f'<span class="cmp-icon" aria-hidden="true">{cell_text(icon)}</span>'


def yes_no_cell(value):
    """A yes / no / not known fact as an icon and a word."""
    icon, word = YES_NO_CELLS.get(value, YES_NO_CELLS[None])
    return f"{icon_html(icon)} <strong>{word}</strong>"


def tier_cell(tier):
    """The label: its icon, its name, and 'Tier N of 6'."""
    info = get_tier_info(tier)
    if info is not None:
        return (
            f"{icon_html(info['icon'])} <strong>{cell_text(info['name'])}</strong>"
            f"<br>Tier {info['number']} of 6"
        )
    if tier == "off_map":
        return f"{icon_html('⚠️')} <strong>{cell_text(tier_label(tier))}</strong>"
    return f"{icon_html('❓')} <strong>{cell_text(tier_label(tier))}</strong>"


def worst_year_cell(product, result):
    """What $10,000 became in the worst year, and which year that was."""
    lost = result["worst_case_dollars"]
    if lost is None:
        return "Not known yet"
    left_over = max(0, EXAMPLE_AMOUNT - lost)
    line = f"$10,000 → ${left_over:,}"
    return f"<strong>{cell_text(line)}</strong><br>{cell_text(product['worst_year'])}"


def access_cell(product, result):
    """The access badge with its icon, and the note from products.py."""
    access = result["access_badge"]
    icon = ACCESS_ICONS.get(access, "❔")
    return f"{icon_html(icon)} <strong>{cell_text(access)}</strong><br>{cell_text(product['access_note'])}"


def cost_cell(product, result):
    """The cost badge with its icon, the yearly percent, and the note."""
    badge = result["cost_badge"]
    icon = COST_ICONS.get(badge, "❔")
    cost = product["yearly_cost_pct"]
    cost_text = "Not known yet." if cost is None else f"{cost:g}% a year."
    return (
        f"{icon_html(icon)} <strong>{cell_text(badge)}</strong><br>"
        f"{cell_text(cost_text)} {cell_text(product['cost_note'])}"
    )


def notes_cell(product, answers):
    """The "Worth thinking about" notes for this product (scoring.py decides them)."""
    notes = fit_notes(product, answers)
    if not notes:
        return cell_text(NO_NOTES_LINE)
    return "<br><br>".join(cell_text(note) for note in notes)


def sources_cell(product):
    """Every source as a link, with its as-of date."""
    links = []
    for source in product["sources"]:
        links.append(
            f'<a href="{cell_text(source["url"])}" target="_blank" rel="noopener noreferrer">'
            f'{cell_text(source["label"])}</a>, as of {cell_text(source["as_of"])}'
        )
    if not links:
        return "No sources yet."
    return "<br>".join(links)


def earn_cell(product):
    """What it might earn, plus today's rate when the product has one."""
    text = cell_text(product["gain_note"])
    rate = todays_rate(product)
    if rate:
        text += f"<br><strong>📡 {cell_text(rate)}</strong>"
    return text


def compare_table_rows(rows):
    """Every row of the table: (row label, one cell per product).
    rows is a list of (product, result) pairs."""
    table = [
        ("Label", [tier_cell(result["tier"]) for product, result in rows]),
        ("What it is", [cell_text(product["one_line"]) for product, result in rows]),
        ("Backed by the U.S. government",
         [yes_no_cell(product["government_backed"]) for product, result in rows]),
        ("In its worst year", [worst_year_cell(product, result) for product, result in rows]),
        ("Getting money out", [access_cell(product, result) for product, result in rows]),
        ("Cost", [cost_cell(product, result) for product, result in rows]),
        ("Sales or surrender charge",
         [yes_no_cell(product["sales_or_surrender_charge"]) for product, result in rows]),
        ("Standard protections", [yes_no_cell(product["protections"]) for product, result in rows]),
        ("What it might earn", [earn_cell(product) for product, result in rows]),
        ("Insurance", [cell_text(product["insurance_note"]) for product, result in rows]),
    ]

    # The notes row only appears once the person has saved their answers.
    answers = st.session_state.get("answers")
    if answers:
        table.append((NOTES_TITLE, [notes_cell(product, answers) for product, result in rows]))

    table.append(("Sources (open in a new tab)", [sources_cell(product) for product, result in rows]))
    return table


def compare_table_html(rows):
    """The whole table as HTML: product names across the top,
    row labels down the left side."""
    names = "".join(f'<th scope="col">{cell_text(product["name"])}</th>' for product, result in rows)
    parts = [
        f'<thead><tr><th scope="col" class="cmp-corner">Compared</th>{names}</tr></thead>',
        "<tbody>",
    ]
    for label, cells in compare_table_rows(rows):
        tds = "".join(f"<td>{cell}</td>" for cell in cells)
        parts.append(f'<tr><th scope="row">{cell_text(label)}</th>{tds}</tr>')
    parts.append("</tbody>")

    # Everything on one line: Streamlit could misread spaces at the start of a line.
    # tabindex="0" lets the Tab key reach the table, so the arrow keys can slide it.
    return (
        '<div class="cmp-scroll" role="region" aria-label="Comparison table" tabindex="0">'
        f'<table class="cmp-table">{"".join(parts)}</table>'
        "</div>"
    )


def show_compare():
    """The Compare view: the chosen products side by side."""
    chosen = st.session_state.get("compare_keys", [])
    # In label order, from Safe Harbor to Uncharted Waters.
    rows = [(product, result) for product, result in sorted_products() if product["key"] in chosen]

    # The top of the page: what is being compared (left) and how to change it (right).
    with st.container(key="split_compare"):
        with st.container(key="compare_intro"):
            if not rows:
                st.markdown(COMPARE_EMPTY)
            else:
                count = len(rows)
                things = "product" if count == 1 else "products"
                st.markdown(
                    f"Comparing **{count} {things}**, from the calmest water to the wildest.\n\n"
                    f"{COMPARE_LABEL_NOTE}"
                )
                if count == 1:
                    st.markdown(COMPARE_ONE_MORE)
                else:
                    st.markdown(COMPARE_SCROLL_HINT)

        with st.container(key="card_compare_change"):
            st.markdown("#### ➕ Choose what to compare")
            st.markdown(COMPARE_HOW)
            st.button(
                "🧭 Go to Explore products",
                key="compare_go_explore",
                on_click=go_to,
                args=("Explore products",),
                type="primary",
                width="stretch",
            )

    if rows:
        st.markdown(compare_table_html(rows), unsafe_allow_html=True)
        if st.session_state.get("answers"):
            st.markdown(NOTES_DISCLAIMER)
        # The fees chart (charts.py), under the table.
        show_fees_chart(rows)
        for product, _ in rows:
            st.markdown(f"**{safe_text(product['name'])}**")
            show_product_risk(product)

    # The scam card, the help card and "Something looks wrong?"
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


# ---------- Check an offer: the offer's words ----------
# st.session_state["offer_words"] always holds the words we are working with,
# whichever way they came in (typed, said out loud, or a sample).
# It is our own copy, so it is never lost when the text box isn't on screen.

def current_words():
    """The offer's words we are working with (empty if none yet)."""
    return st.session_state.get("offer_words", "")


def set_words(text):
    """Put new words in place of the old ones.
    The text box starts over from these words the next time it is drawn."""
    st.session_state["offer_words"] = (text or "")[:OFFER_MAX_CHARS]
    st.session_state.pop("offer_box", None)


def load_sample(samples):
    """Runs when a sample is picked: use its words, and check them right away."""
    choice = st.session_state.get("sample_choice")
    if choice in samples:
        set_words(samples[choice])
        st.session_state["voice_ready"] = False
        st.session_state["check_now"] = True


def save_way():
    """Runs when the way in step 1 is changed. We keep our own copy,
    because Streamlit forgets a choice when you visit another page."""
    st.session_state["offer_way_saved"] = st.session_state["offer_way"]


# ---------- Check an offer: telling us out loud ----------
# 1. The person records with st.audio_input.
# 2. Cartesia turns the recording into words (once per recording).
# 3. We show "I heard: …". Only "Yes, use this" uses those words.

def forget_recording():
    """Clear the recording and what we heard.
    A new number in the recorder's key gives a fresh, empty recorder."""
    st.session_state["recording_round"] = st.session_state.get("recording_round", 0) + 1
    for key in ("heard_for", "heard_text", "heard_error"):
        st.session_state.pop(key, None)
    st.session_state["voice_ready"] = False


def use_heard_text():
    """Runs when "Yes, use this" is clicked: use what we heard as the offer's words."""
    set_words(st.session_state.get("heard_text") or "")
    forget_recording()
    # After forget_recording, so it stays True: the words are ready to check.
    st.session_state["voice_ready"] = True


def show_voice_input():
    """The recorder, and the "I heard: …" box with its two buttons."""
    round_number = st.session_state.get("recording_round", 0)
    recording = st.audio_input(RECORD_LABEL, key=f"offer_audio_{round_number}")
    st.markdown(RECORD_HELP_LINE)

    if recording is None:
        return

    # Send each recording to Cartesia only once, not on every click.
    if st.session_state.get("heard_for") != recording.file_id:
        with st.spinner(LISTEN_SPINNER):
            heard, error = get_transcript(recording)
        st.session_state["heard_for"] = recording.file_id
        st.session_state["heard_text"] = heard
        st.session_state["heard_error"] = error

    heard = st.session_state.get("heard_text")
    error = st.session_state.get("heard_error")

    # A dashed box inside the card, so it looks different from the card around it.
    with st.container(key="notes_heard"):
        if error:
            st.info(error, icon="🎙️")
            st.button(TRY_AGAIN_BUTTON, key="heard_try_again", on_click=forget_recording, width="stretch")
            return

        st.markdown(f"#### {HEARD_TITLE}")
        st.markdown(quote_md(heard))
        st.markdown(HEARD_CHECK_LINE)
        left, right = st.columns(2, gap="medium")
        with left:
            st.button(USE_HEARD_BUTTON, key="heard_yes", on_click=use_heard_text,
                      type="primary", width="stretch")
        with right:
            st.button(TRY_AGAIN_BUTTON, key="heard_try_again", on_click=forget_recording,
                      width="stretch")


# ---------- Check an offer: showing the result card ----------
# The helpers that read the AI's answer (get_part, is_quoted, as_number,
# yes_no_unknown, access_word, build_offer_facts) live in results.py.

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
    """The AI's cost facts as one plain line."""
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
    """The AI's promised-return facts as one plain line."""
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
    """What the offer says about each fact, with its quote.
    It sits in a box you open, because it is detail most people check last."""
    with st.expander("What the offer says, word for word", icon="🔍"):
        st.markdown(
            "These are the offer's own claims. The words in italics are quoted from it, "
            "and we checked that each quote is really there. "
            "Our label comes from our rules, not from these claims."
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
    """The warning signs box. Only flags whose words were found in the offer count.
    When we found some, the box gets a thick solid border (styles.py),
    so it stands out by its shape, not just its words."""
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

    key = "notes_flags_found" if found else "notes_flags_none"
    with st.container(key=key):
        if found:
            count = len(found)
            signs = "sign" if count == 1 else "signs"
            st.markdown(f"#### 🚩 We noticed {count} warning {signs}")
            st.markdown("\n".join(flag_line(item) for item in found))
            st.markdown(FLAGS_FOUND_LINE)
        else:
            st.markdown(f"#### {FLAGS_TITLE}")
            st.markdown(NO_FLAGS_LINE)
        if unsure:
            st.markdown(UNSURE_FLAGS_LINE)
            st.markdown("\n".join(flag_line(item) for item in unsure))


def show_questions_to_ask(answer):
    """The questions to ask before signing, as a numbered list."""
    questions = answer.get("questions_to_ask")
    if not isinstance(questions, list) or not questions:
        return
    st.markdown("#### 🙋 Questions to ask before you sign")
    lines = [f"{number}. {safe_text(q)}" for number, q in enumerate(questions, start=1)]
    st.markdown("\n".join(lines))


def show_plain_summary(answer):
    """The plain-language summary of the offer (already cleaned by checks.py)."""
    summary = answer.get("plain_summary")
    if isinstance(summary, str) and summary.strip():
        st.markdown(f"#### 📝 In plain words\n\n{safe_text(summary)}")


def show_offer_risk_numbers(product, tier):
    """The "Risk in numbers" part, at the bottom of the offer's "Show me the numbers" box.
    It is drawn inline (not in its own box), because Streamlit
    does not allow a box that opens inside another box."""
    st.divider()
    st.markdown(f"#### {RISK_NUMBERS_TITLE}")

    # A possible scam: past numbers from a real product would be misleading.
    if tier == "off_map":
        st.markdown(RISK_NUMBERS_OFF_MAP)
        return

    # No match on our list: nothing to measure it against.
    if product is None or tier == "not_rated":
        st.markdown(RISK_NUMBERS_NOT_RATED)
        return

    st.markdown(RISK_NUMBERS_NOTE)
    st.markdown(f"**We compared it to:** {safe_text(product['name'])}")
    # The table itself comes from charts.py, the same one Explore products uses.
    show_product_risk(product, inline=True)


def show_offer_numbers(result, where_from, answer, product):
    """'Show me the numbers' for the offer, all in one box: the steps,
    where each fact came from, what the safety checks did, and the risk in numbers."""
    tier = result["tier"]
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

        # The risk numbers, in the same box
        show_offer_risk_numbers(product, tier)


def score_offer_card(answer):
    """The tier for an offer. scoring.py always picks it.
    Live: it also uses today's Treasury bill rate.
    Demo replay: it uses score_offer from results.py, exactly as
    save_demo_cache.py did, so the label and the saved voice match.
    Returns (result, facts, matching product or None, where each fact came from)."""
    if replay_on():
        return score_offer(answer)

    facts, product, where_from = build_offer_facts(answer)
    promised = get_part(answer, "promised_return")
    result = assign_tier(
        facts,
        tbill_rate_pct=tbill_rate_for_scoring(get_live_rates()),
        promised_return_pct=as_number(promised.get("value_pct")),
        guaranteed=yes_no_unknown(promised.get("guaranteed")) is True,
    )
    return result, facts, product, where_from


def show_source_line(source):
    """One line saying where this reading came from, with an icon and words.
    source is "live", "demo" (hand-written) or "replay" (a real saved run)."""
    if source == "demo":
        st.markdown(DEMO_CARD_LINE)
    elif source == "replay":
        day = recorded_date_words(load_replay())
        st.markdown(
            f"📼 **Demo replay:** this is the AI's real reading of {REPLAY_OFFER}, "
            f"recorded {day}. It is not a live check. The label still comes from our own rules."
        )


# ---------- Check an offer: saving to My history ----------

def save_check_to_history(record, offer_text):
    """Runs when "Save to my history" is clicked.
    record holds only the category, label, badges and plain summary.
    offer_text stays on this page only, so we know this check was saved;
    it is never sent to the database."""
    ok, message = db.save_offer_check(record)
    st.session_state["offer_save_note"] = (offer_text, ok, message)
    if ok:
        st.session_state.setdefault("saved_offer_texts", []).append(offer_text)
        st.session_state.pop("history_rows", None)  # My history loads fresh next time


def show_save_to_history(answer, product, result):
    """The "Save to my history" button, for signed-in people only."""
    if not (db.ready() and db.is_signed_in()):
        return
    offer_text = current_words().strip()
    summary = answer.get("plain_summary")
    record = {
        "category": product["name"] if product is not None else "unknown",
        "label": tier_label(result["tier"]),
        "access_badge": result["access_badge"],
        "cost_badge": result["cost_badge"],
        "plain_summary": summary if isinstance(summary, str) else "",
    }

    if offer_text in st.session_state.get("saved_offer_texts", []):
        st.markdown(SAVED_HISTORY_LINE)
    else:
        st.button(SAVE_HISTORY_BUTTON, key="save_offer_history", on_click=save_check_to_history,
                  args=(record, offer_text), width="stretch")
        note = st.session_state.get("offer_save_note")
        if note is not None and note[0] == offer_text and not note[1]:
            st.warning(note[2], icon="⚠️")
    st.markdown(f"🔒 {SAVE_HISTORY_NOTE}")


def show_offer_card(answer, source):
    """Step 3: the result card, in the order people need it:
    our label, what the offer is in plain words, the warning signs,
    how rough the water is, questions to ask, and then the details.
    answer has already been through verify_quotes and apply_guards."""
    result, facts, product, where_from = score_offer_card(answer)
    tier = result["tier"]

    if product is not None:
        compared_to = product["name"]
    else:
        compared_to = "none of the products on our list"

    with st.container(key="card_offer"):
        st.markdown(f"### {RESULT_TITLE}")
        show_source_line(source)

        # 1. Our label (from scoring.py), and what we compared the offer to
        st.markdown("**Our label for this offer:**")
        show_tier_heading(tier)
        st.markdown(f"**We compared it to:** {safe_text(compared_to)}")

        # Listen to the result: near the top, so it is easy to find.
        words = offer_words(answer, result)
        st.button(
            LISTEN_BUTTON,
            key="listen_offer",
            on_click=start_speaking,
            args=(words,),
            type="primary",
            width="stretch",
        )
        show_voice(words)

        # 2. What the offer is, in plain words
        show_plain_summary(answer)

        # 3. Warning signs, right where they can't be missed
        show_red_flags(answer)

        # 4. How rough the water is, getting money out, cost, and the worst year
        show_gauge(tier)
        show_badges(result)
        # A worst-year number would be misleading on a possible scam.
        if tier != "off_map":
            show_worst_year(facts, result)

        # 5. What to ask before signing
        show_questions_to_ask(answer)
        st.markdown(f"💬 {OFFER_CLOSING_LINE}")

        # 6. The details, in two boxes you can open.
        #    "Show me the numbers" now also holds the risk in numbers.
        show_offer_facts(answer)
        show_offer_numbers(result, where_from, answer, product)

        # 7. Signed in: save a summary (never the pasted words) to My history
        show_save_to_history(answer, product, result)


# ---------- Check an offer: the three steps, one under another ----------

def check_words(samples, demo_answers):
    """Read the offer's words. In this order:
    1. Demo replay and the words are OFFER 1: the AI's real saved run.
    2. A sample with a saved, hand-written reading.
    3. Demo replay is on: stop here (no internet calls).
    4. Otherwise: a live call to the AI (Grok).
    Problems show right here, next to the step."""
    text = current_words().strip()
    # Readings we already have, by offer text, so the AI is never asked twice.
    # Each one is stored as {"answer": ..., "source": "live", "demo" or "replay"}.
    cache = st.session_state.setdefault("offer_cache", {})

    if not text:
        st.warning(EMPTY_WARNING, icon="✋")
        return
    if text in cache:
        return

    if replay_on():
        saved = load_replay()
        if saved is not None and text == saved["offer_text"].strip():
            cache[text] = {"answer": saved["answer"], "source": "replay"}
            return

    demo_answer = find_demo_answer(text, samples, demo_answers)
    if demo_answer is not None:
        # A sample offer in demo mode: use the saved reading, no AI call.
        cache[text] = {"answer": demo_answer, "source": "demo"}
        return

    if replay_on():
        st.info(REPLAY_LIVE_OFF, icon="📼")
        return

    # Anything else: ask the AI.
    with st.spinner(SPINNER_TEXT):
        product_names = [product["name"] for product in PRODUCTS]
        answer, error = read_offer(text, product_names)
    if error:
        st.error(error, icon="😕")
    else:
        cache[text] = {"answer": answer, "source": "live"}


def show_result_ready():
    """A line saying the result is ready below, once these exact words are checked."""
    text = current_words().strip()
    if text and text in st.session_state.get("offer_cache", {}):
        st.markdown(RESULT_READY_LINE)


def show_words_box():
    """The text box with the offer's words, ready to read over or change."""
    # Start the box from our own copy of the words.
    if "offer_box" not in st.session_state:
        st.session_state["offer_box"] = current_words()
    words = st.text_area(
        OFFER_BOX_LABEL,
        key="offer_box",
        height=260,
        max_chars=OFFER_MAX_CHARS,
        placeholder=OFFER_BOX_PLACEHOLDER,
    )
    # Whatever is in the box now is the offer's words.
    st.session_state["offer_words"] = words


def show_check_button(samples, demo_answers):
    """The big Check button, and what happened when it was pressed."""
    if st.button(CHECK_BUTTON, key="check_offer", type="primary", width="stretch"):
        check_words(samples, demo_answers)
    show_result_ready()


def show_way_step():
    """Step 1: choose one of three ways. Returns the way chosen."""
    # Put back the saved choice when coming back to this page.
    if "offer_way" not in st.session_state:
        st.session_state["offer_way"] = st.session_state.get("offer_way_saved", WAY_TYPE)

    with st.container(key="card_offer_way"):
        st.markdown(f"### {STEP_ONE_TITLE}")
        st.markdown(STEP_ONE_TEXT)
        # Three big boxes side by side (styles.py). The label is still there for
        # screen readers; it is hidden on screen because the step title says it.
        st.radio(
            WAY_LABEL,
            WAYS,
            key="offer_way",
            on_change=save_way,
            horizontal=True,
            label_visibility="collapsed",
        )
        st.markdown(OFFER_PRIVACY_LINE)
    return st.session_state["offer_way"]


def show_input_step(way, samples, demo_answers):
    """Step 2: only the one way chosen in step 1."""
    with st.container(key="card_offer_input"):
        st.markdown(f"### {STEP_TWO_TITLES[way]}")

        if way == WAY_SAMPLE:
            st.markdown(SAMPLE_HELP)
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
                if replay_on():
                    st.markdown(REPLAY_SAMPLE_NOTICE)
                elif demo_answers:
                    st.markdown(DEMO_NOTICE)
            else:
                st.markdown("📂 Sample offers not found. Check that data/sample_offers.md exists.")

            # A sample that was just picked is checked right away, with no extra click.
            if st.session_state.pop("check_now", False):
                check_words(samples, demo_answers)

            # Let people read the sample's words, if they want to.
            choice = st.session_state.get("sample_choice")
            if choice in samples:
                with st.expander(SAMPLE_WORDS_LABEL, icon="📄"):
                    st.markdown(safe_text(samples[choice]))
            show_result_ready()

        elif way == WAY_SAY:
            if replay_on():
                # Turning speech into words needs Cartesia, so it is off in replay.
                st.info(REPLAY_NO_RECORDING, icon="📼")
                return
            show_voice_input()
            # Once the person says "Yes, use this", the words appear here to read over.
            if st.session_state.get("voice_ready"):
                st.success(HEARD_USED_LINE, icon="✅")
                show_words_box()
                show_check_button(samples, demo_answers)

        else:
            st.markdown(TYPE_HELP)
            show_words_box()
            show_check_button(samples, demo_answers)


def show_result_step():
    """Step 3: the result card, or a card saying where it will appear."""
    text = current_words().strip()
    cache = st.session_state.get("offer_cache", {})

    # Nothing checked yet for these exact words: say where the result will go.
    if not (text and text in cache):
        with st.container(key="card_offer_waiting"):
            st.markdown(f"### {RESULT_TITLE}")
            st.markdown(OFFER_WAITING_TEXT)
        return

    entry = cache[text]
    # The safety layer runs on EVERY reading, saved or live, before scoring:
    # 1. check each quote against the pasted text, 2. apply the guards.
    checked = verify_quotes(text, entry["answer"])
    guarded = apply_guards(checked)
    show_offer_card(guarded, entry["source"])


def show_check_offer():
    """The Check an offer view: three steps, one under another."""
    samples = load_sample_offers()
    demo_answers = load_demo_answers() if DEMO_MODE else {}

    way = show_way_step()
    show_input_step(way, samples, demo_answers)
    show_result_step()

    # At the bottom: the scam card, the help card, and "Something looks wrong?"
    show_safety_cards()


# ---------- History: the choices above the two charts ----------
# The charts themselves live in charts.py. These functions only draw the
# choices and hand back what was picked.

def remember_choice(key):
    """Runs when a History choice changes. We keep our own copy,
    because Streamlit forgets a choice when you visit another page."""
    st.session_state[f"{key}_saved"] = st.session_state[key]


def restore_choice(key, default):
    """Put back the saved choice when coming back to this page."""
    if key not in st.session_state:
        st.session_state[key] = st.session_state.get(f"{key}_saved", default)


def series_name(key):
    """The words for one choice, like "U.S. stocks (S&P 500)"."""
    for series in HISTORY_SERIES:
        if series["key"] == key:
            return series["name"]
    return key


def pick_history_series():
    """Big radio buttons: stocks, bonds or bills. Returns the key picked."""
    restore_choice("history_series", SERIES_KEYS[0])
    with st.container(key="history_series_choices"):
        return st.radio(
            HISTORY_SERIES_LABEL,
            SERIES_KEYS,
            key="history_series",
            on_change=remember_choice,
            args=("history_series",),
            format_func=series_name,
            horizontal=True,
        )


def pick_start_year():
    """A big drop-down list of start years. Returns the year picked."""
    restore_choice("history_start", START_YEARS[0])
    return st.selectbox(
        START_YEAR_LABEL,
        START_YEARS,
        key="history_start",
        on_change=remember_choice,
        args=("history_start",),
        format_func=str,
    )


def pick_run_length(last_year):
    """Big radio buttons: 5, 10 or 20 years, or to the last year.
    Returns the number of years (0 means to the last year)."""
    restore_choice("history_length", RUN_LENGTHS[1])

    def length_words(length):
        return f"To {last_year}" if length == 0 else f"{length} years"

    return st.radio(
        RUN_LENGTH_LABEL,
        RUN_LENGTHS,
        key="history_length",
        on_change=remember_choice,
        args=("history_length",),
        format_func=length_words,
    )


def show_history():
    """The History view: every year's return, and what $10,000 became."""
    history = load_history()
    if not history:
        st.markdown(HISTORY_MISSING)
        return

    # Override reading-width limits and vertical radio styling only here.
    st.markdown(
        """
        <style>
        .st-key-history_intro,
        .st-key-history_intro [data-testid="stMarkdownContainer"],
        .st-key-history_intro p,
        .st-key-history_series_choices,
        .st-key-history_series_choices [data-testid="stRadio"] {
            width: 100% !important;
            max-width: none !important;
        }
        .st-key-history_intro p {
            white-space: normal !important;
        }
        .st-key-history_series_choices [role="radiogroup"] {
            display: grid !important;
            grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
            gap: 1rem !important;
            width: 100% !important;
            max-width: none !important;
        }
        .st-key-history_series_choices [role="radiogroup"] > label {
            box-sizing: border-box !important;
            width: 100% !important;
            min-width: 0 !important;
            max-width: none !important;
            height: auto !important;
            margin: 0 !important;
            align-self: stretch !important;
            align-items: center !important;
        }
        .st-key-history_series_choices [data-testid="stMarkdownContainer"],
        .st-key-history_series_choices [data-testid="stMarkdownContainer"] p {
            min-width: 0 !important;
            max-width: none !important;
            white-space: normal !important;
            overflow: visible !important;
            text-overflow: clip !important;
            overflow-wrap: anywhere !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    with st.container(key="history_intro"):
        st.markdown(safe_text(HISTORY_INTRO))
    show_returns_card(history, pick_history_series)
    show_growth_card(history, pick_start_year, pick_run_length)
    # Under both charts: past results, fees and taxes, and the source.
    show_history_note(history)


# ---------- My account (optional) ----------
# Guests can use every other page without an account. Nothing is saved for guests.
# All the Supabase calls live in db.py.

def clean_saved_answers(saved):
    """Saved answers, but only if every one is a real choice from QUESTIONS.
    None if anything is missing or odd, so nothing strange reaches the page."""
    if not isinstance(saved, dict):
        return None
    answers = {}
    for question in QUESTIONS:
        value = saved.get(question["key"])
        if value not in question["options"]:
            return None
        answers[question["key"]] = value
    return answers


def load_account_answers():
    """After signing in: put the saved answers into Your situation.
    If the account has none yet, keep whatever is on the page now."""
    saved = clean_saved_answers(db.load_answers())
    if saved is None:
        return
    st.session_state["answers"] = saved
    st.session_state["editing_answers"] = False
    # The question boxes start over from the saved answers next time.
    for question in QUESTIONS:
        st.session_state.pop(f"q_{question['key']}", None)


def set_account_message(ok, message):
    """Remember a message to show on My account after the page redraws."""
    st.session_state["account_message"] = (ok, message)


def forget_personal_data():
    """Clear this person's answers, products and history from the page,
    so the next person at this computer sees nothing of theirs."""
    for key in ("answers", "editing_answers", "save_note", "history_rows",
                "saved_offer_texts", "offer_save_note", "delete_confirm"):
        st.session_state.pop(key, None)
    for question in QUESTIONS:
        st.session_state.pop(f"q_{question['key']}", None)
    my_products.forget_all()


def do_sign_in():
    """Validate required credentials, then sign in and report the result."""
    email = st.session_state.get("signin_email", "").strip()
    password = st.session_state.get("signin_password", "")
    st.session_state["signin_attempted"] = True
    if not email or len(password) < 8:
        return
    ok, message = db.sign_in(email, password)
    st.session_state["signin_password"] = ""
    st.session_state["signin_attempted"] = False
    if ok:
        st.session_state["signin_attempted"] = False
        load_account_answers()
        my_products.reload_holdings()
        st.session_state.pop("history_rows", None)
        set_account_message(True, "You have successfully signed in. Welcome back!")
    else:
        set_account_message(False, message or "Sign-in failed. Please check your email and password and try again.")


def do_sign_up():
    """Validate both passwords before sending an account creation request."""
    email = st.session_state.get("signup_email", "").strip()
    password = st.session_state.get("signup_password", "")
    again = st.session_state.get("signup_password_again", "")
    agreed = st.session_state.get("signup_agree", False)
    minimum = max(8, db.MIN_PASSWORD_LENGTH)

    st.session_state["signup_attempted"] = True
    if not email or len(password) < minimum or password != again or not agreed:
        return

    ok, message = db.sign_up(email, password)
    st.session_state["signup_password"] = ""
    st.session_state["signup_password_again"] = ""
    st.session_state["signup_attempted"] = False
    if ok:
        st.session_state["signup_attempted"] = False
        if db.is_signed_in():
            if st.session_state.get("answers"):
                db.save_answers(st.session_state["answers"])
            set_account_message(True, "Your account has been created successfully, and you are now signed in.")
        else:
            # Keep the provider's instructions, including email confirmation.
            details = message or "If email confirmation is required, check your inbox before signing in."
            set_account_message(True, f"Your account has been created successfully. {details}")
    else:
        set_account_message(False, message or "We could not create your account. Please try again.")


def do_sign_out():
    """Runs when Sign out is clicked."""
    db.sign_out()
    forget_personal_data()
    set_account_message(True, "You are signed out. Nothing from your account is on this page now.")


def do_delete_check(check_id):
    """Runs when Delete is clicked on one saved check in My history."""
    ok, message = db.delete_offer_check(check_id)
    st.session_state.pop("history_rows", None)
    set_account_message(ok, message)


def do_delete_account():
    """Runs when Delete my account is clicked: only if DELETE was typed."""
    typed = st.session_state.get("delete_confirm", "").strip()
    if typed != DELETE_CONFIRM_WORD:
        set_account_message(
            False, "To delete your account, type DELETE in capital letters in the box first."
        )
        return
    ok, message = db.delete_account()
    if not ok:
        set_account_message(False, message)
        return
    forget_personal_data()
    set_account_message(True, ACCOUNT_DELETED)


def show_account_message():
    """The message from the last button press, with an icon and words."""
    note = st.session_state.pop("account_message", None)
    if note is None:
        return
    ok, message = note
    if ok:
        st.success(message, icon="✅")
    else:
        st.error(message, icon="😕")


def show_account_styles():
    """Big, clear email and password boxes, and a big download button (only on this page)."""
    st.markdown(
        """
        <style>
        .stApp [data-testid="stTextInput"] [data-testid="stWidgetLabel"] p {
            font-size: 24px !important;
            font-weight: 700;
            color: var(--navy) !important;
        }
        .stApp [data-testid="stTextInput"] input {
            font-size: 22px !important;
            min-height: 56px;
            color: var(--text) !important;
            background-color: var(--card) !important;
        }
        .stApp [data-testid="stTextInput"] [data-baseweb="input"] {
            border: 2px solid var(--text-secondary) !important;
            border-radius: 12px !important;
        }
        .stApp [data-testid="stCheckbox"] label p {
            font-weight: 400;
            font-size: 22px !important;
        }
        /* The download button looks like every other big button */
        .stApp [data-testid="stDownloadButton"] > button {
            min-height: 60px;
            width: 100%;
            padding: 10px 16px;
            background-color: var(--navy);
            color: var(--white);
            border: 3px solid var(--navy);
            border-radius: 12px;
            white-space: normal;
        }
        .stApp [data-testid="stDownloadButton"] > button * {
            color: inherit !important;
        }
        .stApp [data-testid="stDownloadButton"] > button p {
            font-size: 24px !important;
            font-weight: 700;
            margin: 0;
        }
        .stApp [data-testid="stDownloadButton"] > button:hover {
            background-color: var(--navy-hover);
            border-color: var(--navy-hover);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def show_signed_out():
    """One focused account panel, with only the chosen form visible."""
    with st.container(key="account_intro_full"):
        st.markdown("Accounts are optional. Create one to save your answers and products for next time.")
    show_account_message()
    st.markdown(
        """
        <style>
        .stApp .st-key-account_intro_full,
        .stApp .st-key-account_intro_full [data-testid="stMarkdownContainer"],
        .stApp .st-key-account_intro_full p {
            width: 100% !important;
            max-width: none !important;
        }
        .stApp .st-key-account_intro_full p {
            white-space: normal !important;
        }
        .stApp .st-key-account_auth {
            width: 100% !important;
            max-width: none !important;
            margin: 1rem 0 2rem !important;
            padding: clamp(1.25rem, 3vw, 2rem) !important;
            box-sizing: border-box !important;
            background: #ffffff !important;
            border: 1px solid #d9dde4 !important;
            border-radius: 16px !important;
            box-shadow: 0 8px 30px rgba(23,36,62,0.05) !important;
        }
        .stApp .st-key-account_auth [data-testid="stVerticalBlock"] {
            gap: 1rem !important;
        }
        .stApp .st-key-account_auth h3 {
            font-family: "Times New Roman", Times, serif !important;
            font-size: 1.75rem !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        .stApp .st-key-account_auth [data-testid="stTextInput"] {
            margin: 0 !important;
            padding: 0 !important;
            min-height: 0 !important;
        }
        .stApp .st-key-account_auth [data-testid="stWidgetLabel"] p {
            font-size: 1.1rem !important;
            line-height: 1.4 !important;
            margin: 0 0 0.35rem !important;
            color: #17243e !important;
        }
        .stApp .st-key-account_auth [data-baseweb="input"] {
            display: flex !important;
            min-height: 54px !important;
            height: 54px !important;
            border: 1px solid #8995a7 !important;
            border-radius: 8px !important;
            background: #ffffff !important;
            overflow: hidden !important;
        }
        .stApp .st-key-account_auth [data-baseweb="base-input"] {
            background: #ffffff !important;
        }
        .stApp .st-key-account_auth [data-testid="stTextInput"] input {
            font-size: 1.1rem !important;
            min-height: 0 !important;
            height: 52px !important;
            padding: 0.7rem 0.85rem !important;
            box-sizing: border-box !important;
            color: #17243e !important;
            background: #ffffff !important;
        }
        .stApp .st-key-account_auth [data-baseweb="input"]:focus-within {
            border-color: #17243e !important;
            outline: 2px solid #c1cad7 !important;
            outline-offset: 2px !important;
        }
        .stApp .st-key-account_auth [role="radiogroup"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: wrap !important;
            gap: 0.5rem !important;
            width: 100% !important;
        }
        .stApp .st-key-account_auth [role="radiogroup"] > label {
            flex: 1 1 10rem !important;
            width: auto !important;
            margin: 0 !important;
            padding: 0.65rem !important;
            min-height: 48px !important;
            border-radius: 8px !important;
        }
        .stApp .st-key-account_auth [data-testid="stCheckbox"] p {
            font-size: 1rem !important;
            line-height: 1.5 !important;
        }
        .stApp .st-key-account_auth [data-testid="stButton"] button {
            min-height: 52px !important;
            border-radius: 8px !important;
            margin: 0 !important;
        }
        .stApp .st-key-account_auth [data-testid="stButton"] button p {
            font-size: 1.15rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    with st.container(key="account_auth"):
        mode = st.radio(
            "Account action", ["Sign in", "Create account"],
            key="account_auth_mode", horizontal=True,
            label_visibility="collapsed",
        )
        if mode == "Sign in":
            st.markdown("### Welcome back")
            st.caption("Sign in to access your saved products and history.")
            if st.session_state.get("signin_attempted") and not st.session_state.get("signin_email", "").strip():
                st.warning("Please enter your email.")
            st.text_input("Email", key="signin_email", autocomplete="email",
                          placeholder="you@example.com")
            if st.session_state.get("signin_attempted") and len(st.session_state.get("signin_password", "")) < 8:
                st.warning("Please enter a password with at least 8 characters.")
            st.text_input("Password", key="signin_password", type="password",
                          autocomplete="current-password", placeholder="Enter your password")
            st.button("Sign in", key="signin_button", on_click=do_sign_in,
                      type="primary", width="stretch")
        else:
            st.markdown("### Create your account")
            st.caption("Save your products and return to your offer history.")
            attempted = st.session_state.get("signup_attempted", False)
            if attempted and not st.session_state.get("signup_email", "").strip():
                st.warning("Please enter your email.")
            st.text_input("Email", key="signup_email", autocomplete="email",
                          placeholder="you@example.com")
            password = st.session_state.get("signup_password", "")
            confirmation = st.session_state.get("signup_password_again", "")
            minimum = max(8, db.MIN_PASSWORD_LENGTH)
            if attempted and len(password) < minimum:
                st.warning(f"Your password must be at least {minimum} characters long.")
            st.text_input("Password", key="signup_password", type="password",
                          autocomplete="new-password",
                          help=f"Use at least {max(8, db.MIN_PASSWORD_LENGTH)} characters.",
                          placeholder=f"At least {max(8, db.MIN_PASSWORD_LENGTH)} characters")
            if attempted and not confirmation:
                st.warning("Please enter your password again to confirm it.")
            elif attempted and password != confirmation:
                st.warning("Your passwords do not match. Enter the same password in both fields.")
            st.text_input("Confirm password", key="signup_password_again",
                          type="password", autocomplete="new-password",
                          placeholder="Enter your password again")
            if attempted and not st.session_state.get("signup_agree", False):
                st.warning("Please tick the agreement box before creating an account.")
            st.checkbox(ACCOUNT_CONSENT, key="signup_agree")
            st.button("Create account", key="signup_button", on_click=do_sign_up,
                      type="primary", width="stretch")
        st.divider()
        st.caption(PRIVACY_NOTICE)


def date_words_from(value):
    """A saved date and time from Supabase, as words like "Oct 25, 2026"."""
    try:
        when = datetime.datetime.fromisoformat(str(value))
    except ValueError:
        return "an unknown date"
    return f"{when.strftime('%b')} {when.day}, {when.year}"


def show_my_history():
    """My history: every saved offer check, newest first, each with Delete."""
    if "history_rows" not in st.session_state:
        rows, error = db.list_offer_checks()
        st.session_state["history_rows"] = rows
        if error:
            st.warning(error, icon="⚠️")
    rows = st.session_state["history_rows"]

    with st.container(key="card_my_history"):
        st.markdown(f"### {MY_HISTORY_TITLE}")
        if not rows:
            st.markdown(MY_HISTORY_EMPTY)
            return
        count = len(rows)
        st.markdown(f"You have **{count} saved {'check' if count == 1 else 'checks'}**, newest first.")
        for row in rows:
            with st.container(key=f"notes_check_{safe_key(row['id'])}"):
                st.markdown(
                    f"#### 🔎 {safe_text(row.get('label') or 'No label')}\n\n"
                    f"**Checked on:** {date_words_from(row.get('created_at'))}\n\n"
                    f"**We compared it to:** {safe_text(row.get('category') or 'unknown')}\n\n"
                    f"**Getting money out:** {safe_text(row.get('access_badge') or 'Unknown')} · "
                    f"**Cost:** {safe_text(row.get('cost_badge') or 'Unknown')}"
                )
                if row.get("plain_summary"):
                    st.markdown(f"**In plain words:** {safe_text(row['plain_summary'])}")
                st.button("🗑️ Delete this check", key=f"delete_check_{safe_key(row['id'])}",
                          on_click=do_delete_check, args=(row["id"],), width="stretch")


def show_download_data():
    """Download my data: one JSON file with the profile, holdings and saved checks."""
    with st.container(key="card_download"):
        st.markdown(f"### {DOWNLOAD_TITLE}")
        st.markdown(DOWNLOAD_TEXT)
        data, error = db.export_my_data()
        if error:
            st.warning(error, icon="⚠️")
            return
        st.download_button(
            DOWNLOAD_BUTTON,
            data=json.dumps(data, indent=2, ensure_ascii=False, default=str),
            file_name=DOWNLOAD_FILE_NAME,
            mime="application/json",
            key="download_my_data",
            width="stretch",
        )


def show_delete_account():
    """Delete my account: the person types DELETE, then presses the button."""
    with st.container(key="card_delete_account"):
        st.markdown(f"### {DELETE_ACCOUNT_TITLE}")
        st.warning(DELETE_ACCOUNT_TEXT, icon="⚠️")
        st.text_input(DELETE_CONFIRM_LABEL, key="delete_confirm", max_chars=10)
        st.button(DELETE_ACCOUNT_BUTTON, key="delete_account_button",
                  on_click=do_delete_account, width="stretch")


def show_signed_in():
    """Who is signed in, My history, Download my data and Delete my account."""
    show_account_message()
    with st.container(key="card_account"):
        st.markdown(f"### 👤 Signed in as {safe_text(db.current_email())}")
        st.info(PRIVACY_NOTICE, icon="🔒")
        st.button("📋 Go to My products", key="account_go_products", on_click=go_to,
                  args=("My products",), type="primary", width="stretch")
        st.button("🚪 Sign out", key="signout_button", on_click=do_sign_out, width="stretch")

    show_my_history()
    show_download_data()
    show_delete_account()


def show_account():
    """The My account view."""
    if not db.ready():
        st.info(db.NO_SETUP, icon="🔌")
        st.info(PRIVACY_NOTICE, icon="🔒")
        return
    show_account_styles()
    if db.is_signed_in():
        show_signed_in()
    else:
        show_signed_out()


# ---------- Build the page, top to bottom ----------

# Start on Welcome the first time (or if the saved view is unknown)
if st.session_state.get("view") not in VIEWS:
    st.session_state["view"] = "Welcome"

show_nav()
show_notice()
# The Demo replay switch, and its banner while it is on, on every page.
show_replay_switch()
# If FRED is slow or down, say so in words (with an icon), never just a color.
if any_missing(get_live_rates()):
    st.info(UNAVAILABLE_NOTE, icon="📡")
# Welcome has its own big headline (in welcome.py), so it skips the normal title.
if st.session_state["view"] != "Welcome":
    show_heading()

if st.session_state["view"] == "Welcome":
    show_welcome(go_to, show_speed_setting)
elif st.session_state["view"] == "Your situation":
    show_situation()
elif st.session_state["view"] == "Explore products":
    show_explore()
elif st.session_state["view"] == "Compare":
    show_compare()
elif st.session_state["view"] == "Check an offer":
    show_check_offer()
elif st.session_state["view"] == "History":
    show_history()
elif st.session_state["view"] == "My products":
    # The cards reuse this file's tier heading, badges, voice and help card.
    my_products.show_my_products(
        go_to, show_tier_heading, show_badges,
        start_speaking, show_voice, show_help_card,
    )
elif st.session_state["view"] == "My account":
    show_account()
else:
    show_coming_soon()

show_start_over()
# The footer, on every view: help numbers and the "not advice" notice.
show_footer(NOTICE, get_live_rates())

# Navigation callbacks request scrolling after the new page has been rendered.
# A unique request ID makes the component execute on every click, even when
# the visitor clicks the current page's button again.
scroll_request = st.session_state.pop("scroll_to_top_request", None)
if scroll_request is not None:
    components.html(
        """
        <script>
        // Navigation request: REQUEST_ID
        (() => {
            const resetScroll = () => {
                try {
                    const doc = window.parent.document;
                    const targets = new Set([
                        doc.scrollingElement,
                        doc.documentElement,
                        doc.body,
                        ...doc.querySelectorAll(
                            '[data-testid="stMain"], .stMain, '
                            + '[data-testid="stAppViewContainer"], '
                            + 'section.main'
                        )
                    ]);
                    targets.forEach(el => {
                        if (!el) return;
                        const previous = el.style.scrollBehavior;
                        el.style.scrollBehavior = 'auto';
                        el.scrollTop = 0;
                        el.style.scrollBehavior = previous;
                    });
                    window.parent.scrollTo({top: 0, left: 0, behavior: 'instant'});
                } catch (error) {
                    console.warn('Second Look could not reset page scroll.', error);
                }
            };
            resetScroll();
            requestAnimationFrame(resetScroll);
            setTimeout(resetScroll, 150);
        })();
        </script>
        """.replace("REQUEST_ID", str(scroll_request)),
        height=0,
        scrolling=False,
    )