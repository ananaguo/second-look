# app.py
# The screens of Second Look.
# Run it with:  streamlit run app.py

import html
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
from footer import show_footer
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
from styles import apply_styles
from voice_helper import (
    DEFAULT_SPEED,
    SPEED_NORMAL,
    SPEED_SLOWER,
    dollars_in_words,
    get_speech,
    get_transcript,
    number_words,
)
from welcome import WELCOME_WORDS, show_welcome

# ---------- Page setup (this must be the first Streamlit command) ----------
st.set_page_config(
    page_title="Second Look",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# The look and feel: fonts, colors, sizes and spacing all live in styles.py.
apply_styles()

# ---------- Demo mode ----------
# True: the six sample offers use saved readings from data/sample_answers.json,
#       so they work without calling Claude (no API credits needed).
# False: every offer, samples included, is read live by Claude.
DEMO_MODE = True

# ---------- The five views, in the order their buttons appear ----------
VIEWS = ["Welcome", "Your situation", "Explore products", "Compare", "Check an offer"]

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

# The amount used in every "worst year" example
EXAMPLE_AMOUNT = 10000

# What the heading says when a product has no normal tier
OFF_MAP_SENTENCE = "No tier: this needs a closer look."
NOT_RATED_SENTENCE = "No tier yet: we are missing facts."

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

# The longest offer someone can paste (keeps Claude calls small)
OFFER_MAX_CHARS = 6000

# The left card: two numbered steps
STEP_ONE_TITLE = "Step 1 of 2: Get the offer's words in"
STEP_ONE_TEXT = (
    "Choose whichever of these three ways is easiest. "
    "A sample is checked right away. What you say or paste goes in the box, ready for step 2."
)
OFFER_PRIVACY_LINE = (
    "🛡️ **Keep it private:** don't type or say your name, account numbers, "
    "or Social Security number. We never need them."
)
STEP_TWO_TITLE = "Step 2 of 2: Check it"

# The three ways, in the order they appear
SAMPLE_LABEL = "📄 Try a made-up sample"
RECORD_LABEL = "🎙️ Or say it out loud"
OFFER_BOX_LABEL = "⌨️ Or paste or type the words"
OFFER_BOX_PLACEHOLDER = "Paste or type what the salesperson, letter or ad said."

CHECK_BUTTON = "🔎 Check this offer"
SPINNER_TEXT = "Reading the offer…"

# The warning signs box in the result
FLAGS_TITLE = "⚠️ Warning signs we noticed"
NO_FLAGS_LINE = "We didn't notice any warning signs in this text. That alone doesn't make it safe."
FLAGS_FOUND_LINE = (
    "Honest investments don't do these things. The **🚩 How to spot a scam** card "
    "at the bottom of this page says what to do next."
)
NOT_STATED_QUOTE = "*The offer doesn't say.*"
OFFER_CLOSING_LINE = (
    "This is a first look, not advice. Before you sign anything, "
    "talk it over with someone you trust."
)

# The card shown where the result will go, before anything has been checked
OFFER_WAITING_TITLE = "📄 Your result"
OFFER_WAITING_TEXT = (
    "Follow the two steps, and your result will appear here: our label, "
    "any warning signs, and questions to ask before you sign."
)

# Voice input on Check an offer
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
    "Done. What you said is now in the box below. "
    "Read it over, then click **🔎 Check this offer**."
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
    st.session_state.pop("now_speaking", None)


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
    """The educational notice at the top of every view, centered.
    The key "notice_top" lets styles.py draw its light box
    and put the sentence in the middle."""
    with st.container(key="notice_top"):
        st.markdown(f"ℹ️ {NOTICE}")


def show_nav():
    """The row of five big page buttons."""
    current = st.session_state["view"]
    columns = st.columns(len(VIEWS), gap="small")

    for number, view_name in enumerate(VIEWS):
        is_current = view_name == current
        # The page you are on gets a pin icon and a filled navy button,
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


def end_sentence(text):
    """Add a period at the end, unless the text already ends with . ! or ?"""
    text = str(text).strip()
    if not text or text[-1] in ".!?":
        return text
    return text + "."


def get_tier_info(tier):
    """Find the tier's name and icon in products.py. None if it has no tier."""
    for t in TIERS:
        if t["number"] == tier:
            return t
    return None


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


def show_voice(words):
    """If these words were asked for, play them and show them as captions.
    If the voice fails, the captions still show, with a calm message."""
    if st.session_state.get("now_speaking") != words:
        return

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


def show_numbers(product, result):
    """Card part 8: every fact, step and source behind the label."""
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
        ("What it might earn", [cell_text(product["gain_note"]) for product, result in rows]),
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


def load_sample(samples):
    """Runs when a sample is picked: put its text in the big box,
    and check it right away (no extra click needed)."""
    choice = st.session_state.get("sample_choice")
    if choice in samples:
        st.session_state["offer_text"] = samples[choice]
        st.session_state["check_now"] = True


# ---------- Check an offer: telling us out loud ----------
# 1. The person records with st.audio_input.
# 2. Cartesia turns the recording into words (once per recording).
# 3. We show "I heard: …". Only "Yes, use this" puts the words in the box.

def forget_recording():
    """Clear the recording and what we heard.
    A new number in the recorder's key gives a fresh, empty recorder."""
    st.session_state["recording_round"] = st.session_state.get("recording_round", 0) + 1
    for key in ("heard_for", "heard_text", "heard_error"):
        st.session_state.pop(key, None)


def use_heard_text():
    """Runs when "Yes, use this" is clicked: put what we heard in the offer box."""
    heard = st.session_state.get("heard_text") or ""
    st.session_state["offer_text"] = heard[:OFFER_MAX_CHARS]
    st.session_state["saved_offer_text"] = st.session_state["offer_text"]
    st.session_state["sample_choice"] = None  # it isn't a sample any more
    st.session_state["heard_used"] = True     # a one-time "Done" message
    forget_recording()


def show_voice_input():
    """The recorder, and the "I heard: …" box with its two buttons."""
    round_number = st.session_state.get("recording_round", 0)
    recording = st.audio_input(RECORD_LABEL, key=f"offer_audio_{round_number}")
    st.markdown(RECORD_HELP_LINE)

    # Just confirmed: say so, then forget the flag.
    if st.session_state.pop("heard_used", False):
        st.success(HEARD_USED_LINE, icon="✅")

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
    """The 'Your result' card, in the order people need it:
    our label, what the offer is in plain words, the warning signs,
    how rough the water is, questions to ask, and then the details.
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
        st.markdown(f"### {OFFER_WAITING_TITLE}")
        if is_demo:
            st.markdown(DEMO_CARD_LINE)

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

        # 6. The details, in two boxes you can open
        show_offer_facts(answer)
        show_offer_numbers(result, where_from, answer)


# ---------- Check an offer: the two columns ----------

def show_offer_input(samples, demo_answers):
    """The left card, in two steps.
    Step 1: get the offer's words in (a sample, the microphone, or typing).
    Step 2: check them. Clicking Check (or picking a sample) reads the offer here."""
    with st.container(key="card_offer_steps"):
        st.markdown(f"### {STEP_ONE_TITLE}")
        st.markdown(STEP_ONE_TEXT)
        st.markdown(OFFER_PRIVACY_LINE)

        # Way 1: a made-up sample. Picking one checks it right away.
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

        # Way 2: say it out loud (the box is only filled after "Yes, use this").
        show_voice_input()

        # Way 3: paste or type. Every way ends up in this box.
        # Streamlit forgets a text box when you visit another page,
        # so we keep our own copy and put it back when you return.
        if "offer_text" not in st.session_state:
            st.session_state["offer_text"] = st.session_state.get("saved_offer_text", "")

        st.text_area(
            OFFER_BOX_LABEL,
            key="offer_text",
            height=260,
            max_chars=OFFER_MAX_CHARS,
            placeholder=OFFER_BOX_PLACEHOLDER,
        )
        st.session_state["saved_offer_text"] = st.session_state["offer_text"]

        # Step 2: the Check button
        st.markdown(f"### {STEP_TWO_TITLE}")
        clicked = st.button(CHECK_BUTTON, key="check_offer", type="primary", width="stretch")
        # A sample that was just picked is checked right away, with no extra click.
        if st.session_state.pop("check_now", False):
            clicked = True

        text = st.session_state["offer_text"].strip()
        # Readings we already have, by offer text, so Claude is never asked twice.
        # Each one is stored as {"answer": ..., "is_demo": True or False}.
        cache = st.session_state.setdefault("offer_cache", {})

        if clicked and not text:
            st.warning("Please put an offer in the box first, using one of the three ways above.", icon="✋")
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


def show_offer_result():
    """The right column: the result card, or a card saying where it will appear."""
    text = st.session_state.get("offer_text", "").strip()
    cache = st.session_state.get("offer_cache", {})

    # Nothing checked yet for this exact text: say where the result will go.
    if not (text and text in cache):
        with st.container(key="card_offer_waiting"):
            st.markdown(f"### {OFFER_WAITING_TITLE}")
            st.markdown(OFFER_WAITING_TEXT)
        return

    entry = cache[text]
    # The safety layer runs on EVERY reading, saved or live, before scoring:
    # 1. check each quote against the pasted text, 2. apply the guards.
    checked = verify_quotes(text, entry["answer"])
    guarded = apply_guards(checked)
    show_offer_card(guarded, entry["is_demo"])


def show_check_offer():
    """The Check an offer view: the two steps on the left, the result on the right.
    styles.py puts them one under the other on smaller screens."""
    samples = load_sample_offers()
    demo_answers = load_demo_answers() if DEMO_MODE else {}

    # The left column runs first, so a click on Check is handled
    # before the right column draws the result.
    with st.container(key="layout_offer"):
        with st.container(key="offer_input"):
            show_offer_input(samples, demo_answers)
        with st.container(key="offer_result"):
            show_offer_result()

    # At the bottom: the scam card, the help card, and "Something looks wrong?"
    show_safety_cards()


# ---------- Build the page, top to bottom ----------

# Start on Welcome the first time (or if the saved view is unknown)
if st.session_state.get("view") not in VIEWS:
    st.session_state["view"] = "Welcome"

show_notice()
show_nav()
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
else:
    show_coming_soon()

show_start_over()
# The footer, on every view: help numbers and the "not advice" notice.
show_footer(NOTICE)