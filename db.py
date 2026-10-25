# db.py
# Optional accounts with Supabase: sign in, sign out, saved answers,
# My products, offer history, downloading your data, and deleting your account.
# Guests never touch this file's saving: nothing is saved unless someone signs in.
#
# IMPORTANT: one Supabase client PER BROWSER SESSION, kept in st.session_state.
# Never use st.cache_resource or a global variable for the client,
# because then everyone would share one person's sign-in.
#
# Keys are read only from .streamlit/secrets.toml (through st.secrets).
# SUPABASE_KEY must be the "anon" / "publishable" key, never the service_role key.

import datetime

import streamlit as st
from supabase import create_client

# ---------- Names used in st.session_state ----------
CLIENT_KEY = "supabase_client"   # this browser's own Supabase client
ACCOUNT_KEY = "account"          # {"id": ..., "email": ...} while signed in

# The tables (see the SQL in the instructions)
PROFILES_TABLE = "profiles"          # each person's five answers
HOLDINGS_TABLE = "holdings"          # each person's products in My products
OFFER_CHECKS_TABLE = "offer_checks"  # summaries of offers they chose to save

# ---------- Your situation: which answer goes in which column ----------
# Left: the question "key" in QUESTIONS in app.py.
# Right: the column in the profiles table.
ANSWER_COLUMNS = {
    "age": "age_range",
    "income": "income_range",
    "need": "need_money",
    "drop": "drop_reaction",
    "goal": "goal",
}

# The only columns we ever write
HOLDING_FIELDS = ["product_key", "nickname", "company", "amount", "rate_pct", "start_date", "end_date"]
# Never the pasted text: only the category, label, badges and plain summary.
# app.py calls the summary "plain_summary". The table's column is named "summary".
OFFER_CHECK_FIELDS = ["category", "label", "access_badge", "cost_badge"]
SUMMARY_COLUMN = "summary"        # the column name in the offer_checks table
APP_SUMMARY_KEY = "plain_summary" # the name app.py uses for the same thing
MAX_SUMMARY = 1000  # the longest summary we save, in letters

# The database function that deletes the signed-in person and everything they saved
DELETE_ACCOUNT_FUNCTION = "delete_my_account"

# The shortest password we accept (Supabase's own minimum is 6)
MIN_PASSWORD_LENGTH = 8

# ---------- Friendly messages (shown on the screen) ----------
NO_SETUP = (
    "Accounts are turned off right now. Everything else works without one. "
    "(To turn them on, add SUPABASE_URL and SUPABASE_KEY to .streamlit/secrets.toml.)"
)
WRONG_PASSWORD = "That email and password don't match. Please check them and try again."
EMAIL_TAKEN = "That email already has an account. Please use Sign in instead."
CONFIRM_EMAIL = (
    "Almost done. We sent you an email. Open it and click the link, "
    "then come back and sign in."
)
NOT_CONFIRMED = "Please open the email we sent you and click the link first, then sign in."
WEAK_PASSWORD = f"Please choose a longer password, at least {MIN_PASSWORD_LENGTH} letters or numbers."
TOO_MANY = "Too many tries in a short time. Please wait a few minutes and try again."
TROUBLE = "We couldn't reach the account service just now. Please try again in a moment."
SAVED = "Your answers are saved to your account."
NOT_SAVED = "We couldn't save your answers just now. They are still on this page."
SIGNED_OUT_NOW = "You are not signed in. Please sign in again on My account."
HOLDINGS_NOT_LOADED = "We couldn't load your products just now. Please try again in a moment."
HOLDING_ADDED = "Saved. Your product is on your list."
HOLDING_CHANGED = "Saved. Your changes are on your list."
HOLDING_DELETED = "Deleted. That product is no longer on your list."
HOLDING_TROUBLE = "We couldn't save that just now. Nothing was changed. Please try again."
CHECK_SAVED = "Saved to My history. You can find it on My account."
CHECK_NOT_SAVED = "We couldn't save this to your history just now. Please try again."
CHECKS_NOT_LOADED = "We couldn't load your history just now. Please try again in a moment."
CHECK_DELETED = "Deleted. That check is no longer in your history."
CHECK_TROUBLE = "We couldn't delete that just now. Nothing was changed. Please try again."
EXPORT_TROUBLE = "We couldn't gather your data just now. Please try again in a moment."
ACCOUNT_DELETE_TROUBLE = (
    "We couldn't delete your account just now. Nothing was deleted. Please try again in a moment."
)


# ---------- Small helpers ----------

def has_secret(name):
    """True if this key is filled in .streamlit/secrets.toml."""
    try:
        return bool(str(st.secrets[name]).strip())
    except Exception:
        # No secrets file, or the key isn't in it.
        return False


def ready():
    """True if accounts are set up in secrets.toml."""
    return has_secret("SUPABASE_URL") and has_secret("SUPABASE_KEY")


def get_client():
    """This browser session's own Supabase client. None if accounts are off.
    It is made once per session and kept in st.session_state."""
    if not ready():
        return None
    if CLIENT_KEY not in st.session_state:
        st.session_state[CLIENT_KEY] = create_client(
            st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"]
        )
    return st.session_state[CLIENT_KEY]


def signed_in_client():
    """(client, user id) when someone is signed in, otherwise (None, None)."""
    client = get_client()
    user_id = current_user_id()
    if client is None or user_id is None:
        return None, None
    return client, user_id


def log_problem(where, error):
    """Print the full Supabase error in the terminal, so you can see WHY it failed.
    The screen only ever shows a calm message."""
    print(f"Supabase problem ({where}): {error}")
    # Supabase errors often carry extra clues. Print them too if they are there.
    for part in ("code", "message", "details", "hint"):
        value = getattr(error, part, None)
        if value:
            print(f"    {part}: {value}")


def friendly_error(error):
    """Turn a Supabase error into a calm message for the screen."""
    log_problem("account", error)  # the full detail, for you in the terminal
    code = str(getattr(error, "code", "") or "").lower()
    text = str(error).lower()
    if code == "invalid_credentials" or "invalid login credentials" in text:
        return WRONG_PASSWORD
    if code in ("user_already_exists", "email_exists") or "already registered" in text:
        return EMAIL_TAKEN
    if code == "email_not_confirmed" or "not confirmed" in text:
        return NOT_CONFIRMED
    if code == "weak_password" or ("password" in text and "at least" in text):
        return WEAK_PASSWORD
    if code.startswith("over_") or "rate limit" in text:
        return TOO_MANY
    return TROUBLE


def remember_user(user):
    """Keep the signed-in person's id and email in this session."""
    st.session_state[ACCOUNT_KEY] = {"id": user.id, "email": user.email}


def only_fields(record, fields):
    """Keep only the columns we allow, so nothing else is ever written."""
    return {field: record.get(field) for field in fields}


# ---------- Who is signed in ----------

def is_signed_in():
    """True while someone is signed in in this browser session."""
    return ACCOUNT_KEY in st.session_state


def current_email():
    """The signed-in person's email, or None."""
    return st.session_state.get(ACCOUNT_KEY, {}).get("email")


def current_user_id():
    """The signed-in person's id, or None."""
    return st.session_state.get(ACCOUNT_KEY, {}).get("id")


# ---------- Create an account, sign in, sign out ----------
# Each returns (True or False, a message for the screen).

def sign_up(email, password):
    """Create a new account."""
    client = get_client()
    if client is None:
        return False, NO_SETUP
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, WEAK_PASSWORD
    try:
        response = client.auth.sign_up({"email": email, "password": password})
    except Exception as error:
        return False, friendly_error(error)

    user = response.user
    if user is None:
        return False, TROUBLE
    # When email confirmation is on, Supabase doesn't say "already exists".
    # Instead it sends back a user with no identities.
    if getattr(user, "identities", None) == []:
        return False, EMAIL_TAKEN
    # No session yet means they must click the link in their email first.
    if response.session is None:
        return True, CONFIRM_EMAIL
    remember_user(user)
    return True, f"Welcome! You are signed in as {user.email}."


def sign_in(email, password):
    """Sign in with an email and password."""
    client = get_client()
    if client is None:
        return False, NO_SETUP
    try:
        response = client.auth.sign_in_with_password({"email": email, "password": password})
    except Exception as error:
        return False, friendly_error(error)
    if response.user is None:
        return False, WRONG_PASSWORD
    remember_user(response.user)
    return True, f"You are signed in as {response.user.email}."


def sign_out():
    """Sign out, and forget the account in this session."""
    client = st.session_state.get(CLIENT_KEY)
    if client is not None:
        try:
            client.auth.sign_out()
        except Exception as error:
            log_problem("sign out", error)
    st.session_state.pop(ACCOUNT_KEY, None)
    # A fresh client next time, so nothing from this sign-in is left behind.
    st.session_state.pop(CLIENT_KEY, None)


# ---------- Saved answers (the profiles table) ----------
# Columns: user_id, age_range, income_range, need_money, drop_reaction, goal, consented_at.
# One row per person, found by user_id.

def load_profile():
    """The signed-in person's whole profile row, or None."""
    client, user_id = signed_in_client()
    if client is None:
        return None
    try:
        response = (
            client.table(PROFILES_TABLE)
            .select("*")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
    except Exception as error:
        log_problem("load answers", error)
        return None
    rows = response.data or []
    return rows[0] if rows else None


def load_answers():
    """The signed-in person's saved answers, as a dictionary like
    {"age": "70–74", "income": ...}. None if there are none."""
    profile = load_profile()
    if profile is None:
        return None
    answers = {}
    for key, column in ANSWER_COLUMNS.items():
        answers[key] = profile.get(column)
    # Nothing saved yet in any column: treat it as no answers.
    if all(value is None for value in answers.values()):
        return None
    return answers


def save_answers(answers):
    """Save the five answers, each in its own column.
    Makes the row the first time, and changes it after that.
    consented_at is filled in by the database the first time and never changed.
    Returns (True or False, a message for the screen)."""
    client, user_id = signed_in_client()
    if client is None:
        return False, SIGNED_OUT_NOW
    row = {"user_id": user_id}
    for key, column in ANSWER_COLUMNS.items():
        row[column] = answers.get(key)
    try:
        # on_conflict="user_id": if this person already has a row, change it.
        client.table(PROFILES_TABLE).upsert(row, on_conflict="user_id").execute()
    except Exception as error:
        log_problem("save answers", error)
        return False, NOT_SAVED
    return True, SAVED


# ---------- My products (the holdings table) ----------
# Every call also filters by the person's own id. The table's safety
# policies (row level security) check the same thing a second time.

def list_holdings():
    """The signed-in person's products, oldest first.
    Returns (list of rows, None), or ([], a message) if something went wrong."""
    client, user_id = signed_in_client()
    if client is None:
        return [], SIGNED_OUT_NOW
    try:
        response = (
            client.table(HOLDINGS_TABLE)
            .select("*")
            .eq("user_id", user_id)
            .order("created_at")
            .execute()
        )
    except Exception as error:
        log_problem("load products", error)
        return [], HOLDINGS_NOT_LOADED
    return response.data or [], None


def add_holding(record):
    """Add one product. Returns (True or False, a message)."""
    client, user_id = signed_in_client()
    if client is None:
        return False, SIGNED_OUT_NOW
    row = only_fields(record, HOLDING_FIELDS)
    row["user_id"] = user_id
    try:
        client.table(HOLDINGS_TABLE).insert(row).execute()
    except Exception as error:
        log_problem("add product", error)
        return False, HOLDING_TROUBLE
    return True, HOLDING_ADDED


def update_holding(holding_id, record):
    """Change one of the person's own products. Returns (True or False, a message)."""
    client, user_id = signed_in_client()
    if client is None:
        return False, SIGNED_OUT_NOW
    try:
        response = (
            client.table(HOLDINGS_TABLE)
            .update(only_fields(record, HOLDING_FIELDS))
            .eq("id", holding_id)
            .eq("user_id", user_id)
            .execute()
        )
    except Exception as error:
        log_problem("change product", error)
        return False, HOLDING_TROUBLE
    if not response.data:
        return False, HOLDING_TROUBLE
    return True, HOLDING_CHANGED


def delete_holding(holding_id):
    """Delete one of the person's own products. Returns (True or False, a message)."""
    client, user_id = signed_in_client()
    if client is None:
        return False, SIGNED_OUT_NOW
    try:
        (
            client.table(HOLDINGS_TABLE)
            .delete()
            .eq("id", holding_id)
            .eq("user_id", user_id)
            .execute()
        )
    except Exception as error:
        log_problem("delete product", error)
        return False, HOLDING_TROUBLE
    return True, HOLDING_DELETED


# ---------- My history (the offer_checks table) ----------
# Columns: id, user_id, category, label, access_badge, cost_badge, summary, created_at.

def save_offer_check(record):
    """Save one offer check: category, label, badges and plain summary only.
    The pasted text is never part of record, and never saved.
    Returns (True or False, a message)."""
    client, user_id = signed_in_client()
    if client is None:
        return False, SIGNED_OUT_NOW
    row = only_fields(record, OFFER_CHECK_FIELDS)
    # app.py sends "plain_summary". The table's column is "summary".
    row[SUMMARY_COLUMN] = str(record.get(APP_SUMMARY_KEY) or "")[:MAX_SUMMARY]
    row["user_id"] = user_id
    try:
        client.table(OFFER_CHECKS_TABLE).insert(row).execute()
    except Exception as error:
        log_problem("save offer check", error)
        return False, CHECK_NOT_SAVED
    return True, CHECK_SAVED


def list_offer_checks():
    """The signed-in person's saved checks, newest first.
    Returns (list of rows, None), or ([], a message)."""
    client, user_id = signed_in_client()
    if client is None:
        return [], SIGNED_OUT_NOW
    try:
        response = (
            client.table(OFFER_CHECKS_TABLE)
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
    except Exception as error:
        log_problem("load offer checks", error)
        return [], CHECKS_NOT_LOADED
    rows = response.data or []
    # Give app.py the summary under the name it expects ("plain_summary").
    for row in rows:
        row[APP_SUMMARY_KEY] = row.pop(SUMMARY_COLUMN, None)
    return rows, None


def delete_offer_check(check_id):
    """Delete one of the person's own saved checks. Returns (True or False, a message)."""
    client, user_id = signed_in_client()
    if client is None:
        return False, SIGNED_OUT_NOW
    try:
        (
            client.table(OFFER_CHECKS_TABLE)
            .delete()
            .eq("id", check_id)
            .eq("user_id", user_id)
            .execute()
        )
    except Exception as error:
        log_problem("delete offer check", error)
        return False, CHECK_TROUBLE
    return True, CHECK_DELETED


# ---------- Download my data ----------

def export_my_data():
    """Everything saved for the signed-in person, in one dictionary:
    the profile, the holdings and the saved checks.
    Returns (dictionary, None), or (None, a message)."""
    client, user_id = signed_in_client()
    if client is None:
        return None, SIGNED_OUT_NOW
    holdings, error = list_holdings()
    if error:
        return None, EXPORT_TROUBLE
    checks, error = list_offer_checks()
    if error:
        return None, EXPORT_TROUBLE
    return {
        "_about": "Everything Second Look has saved for your account.",
        "exported_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "email": current_email(),
        "profile": load_profile(),
        "holdings": holdings,
        "offer_checks": checks,
    }, None


# ---------- Delete my account ----------

def delete_account():
    """Delete the signed-in person's account and everything saved for it,
    using the delete_my_account database function, then sign out.
    Returns (True or False, a message)."""
    client, user_id = signed_in_client()
    if client is None:
        return False, SIGNED_OUT_NOW
    try:
        client.rpc(DELETE_ACCOUNT_FUNCTION).execute()
    except Exception as error:
        log_problem("delete account", error)
        return False, ACCOUNT_DELETE_TROUBLE
    # The account is gone now, so signing out may complain. sign_out() catches that.
    sign_out()
    return True, ""