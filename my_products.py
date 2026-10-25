# my_products.py
# The "My products" view: a tracker for signed-in people.
#   1. At the top: the total, and a bar chart of how much is in each label.
#   2. A large form to add (or edit) a product.
#   3. One card per product, with Edit and Delete.
# Guests see a short note instead. Nothing is saved for guests.
# All Supabase calls live in db.py. The tier always comes from scoring.py.

import datetime
import re

import streamlit as st

import db
from charts import show_tier_totals_chart
from live_data import get_live_rates
import portfolio
from products import PRODUCTS
from scoring import assign_tier

# ---------- Words ----------
PRIVACY_LINE = "Don't enter account numbers."
GUEST_LINE = (
    "My products is for people with an account. It keeps a list of what you have, "
    "with each product's label. Everything else in Second Look works without an account."
)
GUEST_BUTTON = "👤 Go to My account to sign in"
ADD_TITLE = "➕ Add a product"
EDIT_TITLE = "✏️ Change this product"
ADD_BUTTON = "✅ Save this product"
SAVE_CHANGES_BUTTON = "✅ Save my changes"
CANCEL_BUTTON = "↩️ Cancel, don't change it"
EMPTY_LINE = "You haven't added any products yet. Use the form above to add your first one."
LIST_TITLE = "📋 Your products"
CONFIRM_LINE = "Are you sure? This removes the product from your list for good."
YES_DELETE = "🗑️ Yes, delete it"
NO_KEEP = "↩️ No, keep it"
NOT_ON_LIST = "This kind of product is no longer on our list, so it can't get a label."

# ---------- Limits ----------
MAX_AMOUNT = 100_000_000      # the largest amount we accept, in dollars
MAX_RATE = 100                # the largest interest rate we accept, in percent
MAX_NAME = 80                 # the longest nickname or company name, in letters
EARLIEST_DATE = datetime.date(1950, 1, 1)
LATEST_DATE = datetime.date(2100, 12, 31)

# 6 or more digits in a row (spaces or dashes allowed between them)
# looks like an account number, so we don't accept it.
LONG_NUMBER = re.compile(r"(\d[\s-]?){6,}")

# The form's boxes, and what each one starts with when empty
FORM_DEFAULTS = {
    "hold_kind": None,
    "hold_nickname": "",
    "hold_company": "",
    "hold_amount": None,
    "hold_rate": None,
    "hold_start": None,   # filled with today's date when the form starts
    "hold_end": None,
}


# ---------- Small helpers ----------

def safe_text(text):
    """Keep $ signs as plain dollar signs (Streamlit treats $...$ as math)."""
    return str(text).replace("$", "\\$")


def product_by_key(key):
    """The product in products.py with this key. None if it is missing."""
    for product in PRODUCTS:
        if product["key"] == key:
            return product
    return None


def key_for_name(name):
    """The product key for a product name from the drop-down. None if not found."""
    for product in PRODUCTS:
        if product["name"] == name:
            return product["key"]
    return None


def money(amount):
    """Dollars and cents, like 12500 → "$12,500.00"."""
    return f"${float(amount):,.2f}"


def to_date(value):
    """A date from Supabase ("2026-10-25") or a date. None if empty or odd."""
    if isinstance(value, datetime.date):
        return value
    try:
        return datetime.date.fromisoformat(str(value))
    except ValueError:
        return None


def date_words(date):
    """A date like "Oct 25, 2026"."""
    return f"{date.strftime('%b')} {date.day}, {date.year}"


def end_words(end):
    """The end date, plus how far away it is."""
    days = (end - datetime.date.today()).days
    if days > 1:
        when = f"in {days} days"
    elif days == 1:
        when = "tomorrow"
    elif days == 0:
        when = "today"
    else:
        when = "already passed"
    return f"{date_words(end)} ({when})"


def card_key(holding_id):
    """A container key made from a holding's id (letters, numbers and _ only)."""
    return "card_holding_" + re.sub(r"[^A-Za-z0-9]", "_", str(holding_id))


def set_message(ok, text):
    """Remember a message to show after the page redraws."""
    st.session_state["products_message"] = (ok, text)


def show_message():
    """The message from the last button press, with an icon and words."""
    note = st.session_state.pop("products_message", None)
    if note is None:
        return
    ok, text = note
    if ok:
        st.success(text, icon="✅")
    else:
        st.error(text, icon="✋")


# ---------- Loading the list ----------

def get_holdings():
    """The signed-in person's products. Loaded from Supabase once,
    then kept in st.session_state until something changes."""
    if "holdings" not in st.session_state:
        rows, error = db.list_holdings()
        st.session_state["holdings"] = rows
        if error:
            set_message(False, error)
    return st.session_state["holdings"]


def reload_holdings():
    """Forget the saved copy, so the list is loaded fresh next time."""
    st.session_state.pop("holdings", None)


def forget_all():
    """Clear everything this view keeps. app.py calls this on Sign out."""
    for key in list(FORM_DEFAULTS) + ["holdings", "editing_holding", "confirm_delete",
                                      "products_message", "portfolio_explain_for",
                                      "portfolio_explained"]:
        st.session_state.pop(key, None)


# ---------- The form ----------

def reset_form():
    """Empty every box in the form. Start date goes back to today."""
    for key, value in FORM_DEFAULTS.items():
        st.session_state[key] = value
    st.session_state["hold_start"] = datetime.date.today()
    st.session_state.pop("editing_holding", None)


def start_edit(holding):
    """Runs when Edit is clicked: put this product's facts in the form."""
    product = product_by_key(holding.get("product_key"))
    st.session_state["hold_kind"] = product["name"] if product else None
    st.session_state["hold_nickname"] = holding.get("nickname") or ""
    st.session_state["hold_company"] = holding.get("company") or ""
    st.session_state["hold_amount"] = float(holding["amount"]) if holding.get("amount") is not None else None
    st.session_state["hold_rate"] = float(holding["rate_pct"]) if holding.get("rate_pct") is not None else None
    st.session_state["hold_start"] = to_date(holding.get("start_date")) or datetime.date.today()
    st.session_state["hold_end"] = to_date(holding.get("end_date"))
    st.session_state["editing_holding"] = holding["id"]
    st.session_state.pop("confirm_delete", None)


def cancel_edit():
    """Runs when Cancel is clicked: empty the form, change nothing."""
    reset_form()


def form_problems():
    """Everything wrong with the form, as a list of plain sentences."""
    problems = []
    if key_for_name(st.session_state.get("hold_kind")) is None:
        problems.append("Please choose the kind of product.")

    nickname = st.session_state.get("hold_nickname", "").strip()
    company = st.session_state.get("hold_company", "").strip()
    if not company:
        problems.append("Please type the bank or company name.")
    for label, text in (("nickname", nickname), ("bank or company name", company)):
        if len(text) > MAX_NAME:
            problems.append(f"Please keep the {label} to {MAX_NAME} letters or fewer.")
        if LONG_NUMBER.search(text):
            problems.append(f"The {label} has a long number in it. Please don't enter account numbers.")

    amount = st.session_state.get("hold_amount")
    if amount is None or amount <= 0:
        problems.append("Please type an amount in dollars, more than zero.")
    elif amount > MAX_AMOUNT:
        problems.append("That amount is larger than we can track. Please check it.")

    rate = st.session_state.get("hold_rate")
    if rate is not None and not 0 <= rate <= MAX_RATE:
        problems.append(f"Please type an interest rate from 0 to {MAX_RATE} percent.")

    start = st.session_state.get("hold_start")
    end = st.session_state.get("hold_end")
    if start is None:
        problems.append("Please choose a start date.")
    elif end is not None and end < start:
        problems.append("The end date is before the start date. Please check them.")
    return problems


def form_record():
    """The form's facts, ready to save in the holdings table."""
    nickname = st.session_state.get("hold_nickname", "").strip()
    rate = st.session_state.get("hold_rate")
    end = st.session_state.get("hold_end")
    return {
        "product_key": key_for_name(st.session_state["hold_kind"]),
        "nickname": nickname or None,
        "company": st.session_state["hold_company"].strip(),
        "amount": round(float(st.session_state["hold_amount"]), 2),
        "rate_pct": round(float(rate), 3) if rate is not None else None,
        "start_date": st.session_state["hold_start"].isoformat(),
        "end_date": end.isoformat() if end is not None else None,
    }


def save_form():
    """Runs when Save is clicked: check the form, then add or change the product."""
    problems = form_problems()
    if problems:
        set_message(False, " ".join(problems))
        return

    editing = st.session_state.get("editing_holding")
    if editing:
        ok, text = db.update_holding(editing, form_record())
    else:
        ok, text = db.add_holding(form_record())
    set_message(ok, text)
    if ok:
        reset_form()
        reload_holdings()


def show_form_styles():
    """Big, clear boxes for typing, numbers and dates (only on this page)."""
    st.markdown(
        """
        <style>
        .stApp [data-testid="stTextInput"] [data-testid="stWidgetLabel"] p,
        .stApp [data-testid="stNumberInput"] [data-testid="stWidgetLabel"] p,
        .stApp [data-testid="stDateInput"] [data-testid="stWidgetLabel"] p {
            font-size: 24px !important;
            font-weight: 700;
            color: var(--navy) !important;
        }
        .stApp [data-testid="stTextInput"] input,
        .stApp [data-testid="stNumberInput"] input,
        .stApp [data-testid="stDateInput"] input {
            font-size: 22px !important;
            min-height: 56px;
            color: var(--text) !important;
            background-color: var(--card) !important;
        }
        .stApp [data-testid="stTextInput"] [data-baseweb="input"],
        .stApp [data-testid="stNumberInput"] [data-baseweb="input"],
        .stApp [data-testid="stDateInput"] [data-baseweb="input"] {
            border: 2px solid var(--text-secondary) !important;
            border-radius: 12px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def show_form():
    """The large form to add a product, or to change one."""
    # The first time, fill the form with its empty values.
    if "hold_start" not in st.session_state:
        reset_form()

    editing = st.session_state.get("editing_holding")
    with st.container(key="card_holding_form"):
        st.markdown(f"### {EDIT_TITLE if editing else ADD_TITLE}")
        st.warning(PRIVACY_LINE, icon="🛡️")

        st.selectbox(
            "Kind of product",
            [product["name"] for product in PRODUCTS],
            index=None,
            placeholder="Choose a kind of product",
            key="hold_kind",
        )
        st.text_input(
            "Nickname (optional)",
            key="hold_nickname",
            placeholder="For example: CD at the credit union",
            max_chars=MAX_NAME,
        )
        st.text_input("Bank or company name", key="hold_company", max_chars=MAX_NAME)
        st.number_input(
            "Amount in dollars",
            key="hold_amount",
            min_value=0.0,
            max_value=float(MAX_AMOUNT),
            step=100.0,
            format="%.2f",
            placeholder="For example: 10000",
        )
        st.number_input(
            "Interest rate in percent (optional)",
            key="hold_rate",
            min_value=0.0,
            max_value=float(MAX_RATE),
            step=0.05,
            format="%.2f",
            placeholder="For example: 4.00",
        )
        st.date_input(
            "Start date",
            key="hold_start",
            min_value=EARLIEST_DATE,
            max_value=LATEST_DATE,
            format="MM/DD/YYYY",
        )
        st.date_input(
            "End or maturity date (optional)",
            key="hold_end",
            min_value=EARLIEST_DATE,
            max_value=LATEST_DATE,
            format="MM/DD/YYYY",
            help="Leave it empty if this product has no end date.",
        )

        st.button(SAVE_CHANGES_BUTTON if editing else ADD_BUTTON, key="hold_save",
                  on_click=save_form, type="primary", width="stretch")
        if editing:
            st.button(CANCEL_BUTTON, key="hold_cancel", on_click=cancel_edit, width="stretch")


# ---------- Delete ----------

def ask_delete(holding_id):
    """Runs when Delete is clicked: ask "Are you sure?" first."""
    st.session_state["confirm_delete"] = holding_id


def cancel_delete():
    """Runs when "No, keep it" is clicked."""
    st.session_state.pop("confirm_delete", None)


def confirm_delete(holding_id):
    """Runs when "Yes, delete it" is clicked."""
    ok, text = db.delete_holding(holding_id)
    set_message(ok, text)
    st.session_state.pop("confirm_delete", None)
    if st.session_state.get("editing_holding") == holding_id:
        reset_form()
    reload_holdings()


# ---------- The cards ----------

def holding_tier(holding):
    """The tier result from scoring.py for this holding's kind of product.
    None if the kind is no longer in products.py."""
    product = product_by_key(holding.get("product_key"))
    if product is None:
        return None, None
    return product, assign_tier(product)


def show_holding_card(holding, show_tier_heading, show_badges):
    """One product card: its label and badges, amount, dates, Edit and Delete."""
    product, result = holding_tier(holding)
    holding_id = holding["id"]

    with st.container(key=card_key(holding_id)):
        title = holding.get("nickname") or (product["name"] if product else "A product")
        st.markdown(f"#### {safe_text(title)}")

        # The label always comes from scoring.py, never from the person or the AI.
        if result is not None:
            show_tier_heading(result["tier"])
        else:
            show_tier_heading("not_rated")
            st.markdown(NOT_ON_LIST)

        lines = []
        if product is not None:
            lines.append(f"**Kind:** {safe_text(product['name'])}")
        lines.append(f"**Bank or company:** {safe_text(holding.get('company') or 'Not given')}")
        lines.append(f"**Amount:** {safe_text(money(holding['amount']))}")
        if holding.get("rate_pct") is not None:
            lines.append(f"**Interest rate:** {float(holding['rate_pct']):g}% a year")
        start = to_date(holding.get("start_date"))
        if start is not None:
            lines.append(f"**Started:** {date_words(start)}")
        end = to_date(holding.get("end_date"))
        lines.append(f"**Ends:** {end_words(end)}" if end else "**Ends:** no end date")
        st.markdown("\n\n".join(lines))

        if result is not None:
            show_badges(result)

        if st.session_state.get("confirm_delete") == holding_id:
            st.warning(CONFIRM_LINE, icon="⚠️")
            left, right = st.columns(2, gap="medium")
            with left:
                st.button(YES_DELETE, key=f"yes_delete_{card_key(holding_id)}",
                          on_click=confirm_delete, args=(holding_id,),
                          type="primary", width="stretch")
            with right:
                st.button(NO_KEEP, key=f"no_delete_{card_key(holding_id)}",
                          on_click=cancel_delete, width="stretch")
        else:
            left, right = st.columns(2, gap="medium")
            with left:
                st.button("✏️ Edit", key=f"edit_{card_key(holding_id)}",
                          on_click=start_edit, args=(holding,), width="stretch")
            with right:
                st.button("🗑️ Delete", key=f"delete_{card_key(holding_id)}",
                          on_click=ask_delete, args=(holding_id,), width="stretch")


# ---------- The whole view ----------

def show_guest(go_to):
    """What guests see: what this page is for, and where to sign in."""
    with st.container(key="card_products_guest"):
        st.markdown("### 👤 Sign in to use My products")
        st.markdown(GUEST_LINE)
        st.button(GUEST_BUTTON, key="products_go_account", on_click=go_to,
                  args=("My account",), type="primary", width="stretch")


def show_my_products(go_to, show_tier_heading, show_badges,
                     start_speaking, show_voice, show_help_card):
    """Draw the My products view.
    All six are app.py's own functions, so the cards, the voice and the
    help card look and work exactly like everywhere else."""
    if not db.ready():
        st.info(db.NO_SETUP, icon="🔌")
        return
    if not db.is_signed_in():
        show_guest(go_to)
        return

    show_form_styles()
    holdings = get_holdings()
    show_message()

    # 1. The total and the chart, at the top
    totals = []
    for holding in holdings:
        product, result = holding_tier(holding)
        tier = result["tier"] if result else "not_rated"
        totals.append((tier, float(holding["amount"])))
    if totals:
        total = sum(amount for tier, amount in totals)
        count = len(totals)
        things = "product" if count == 1 else "products"
        st.markdown(f"### 💰 Total: {safe_text(money(total))} in {count} {things}")
        show_tier_totals_chart(totals)
        # Things worth a look: from the seven published rules in portfolio.py.
        portfolio.show_portfolio_check(
            holdings, st.session_state.get("answers"), get_live_rates(),
            start_speaking, show_voice,
        )

    # 2. The form
    show_form()

    # 3. One card per product
    st.markdown(f"### {LIST_TITLE}")
    if not holdings:
        st.markdown(EMPTY_LINE)
    else:
        with st.container(key="grid_holdings"):
            for holding in holdings:
                show_holding_card(holding, show_tier_heading, show_badges)

    # At the bottom: where to get a trusted second opinion.
    st.divider()
    show_help_card()