# app.py
# The screens of Second Look.
# Run it with:  streamlit run app.py

import streamlit as st

# ---------- Page setup (this must be the first Streamlit command) ----------
st.set_page_config(
    page_title="Second Look",
    page_icon="🔎",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ---------- The five views, in the order their buttons appear ----------
VIEWS = ["Welcome", "Your situation", "Explore products", "Compare", "Check an offer"]

# The notice shown at the top of every view
NOTICE = (
    "Second Look explains money products in plain language. "
    "It is educational, not professional financial advice."
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
.stApp textarea:focus-visible {
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
else:
    show_coming_soon()

show_start_over()