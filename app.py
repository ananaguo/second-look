# app.py
# The screens of Second Look.
# Run it with:  streamlit run app.py

import streamlit as st

from products import PRODUCTS, TIERS
from scoring import assign_tier, tier_label

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

/* Product cards: a thick dark border, lots of room inside and between */
.stApp [class*="st-key-card_"] {
    border: 3px solid #111111;
    border-radius: 14px;
    padding: 28px 24px;
    margin-bottom: 2rem;
    background-color: #FFFFFF;
}

/* The block bars in the gauges */
.stApp .gauge {
    margin: 0.25rem 0;
}
.stApp .gauge-bar {
    font-size: 30px;
    letter-spacing: 4px;
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


def show_numbers(product, result):
    """Card part 6: every fact, step and source behind the label."""
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
    """Card part 7: the Compare checkbox and the Read aloud button."""
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
    for product, result in sorted_products():
        # The key gives this card a name, so the CSS above can draw its border.
        with st.container(key=f"card_{product['key']}"):
            show_tier_heading(result["tier"])
            show_product_name(product)
            show_gauge(result["tier"])
            show_badges(result)
            show_worst_year(product, result)
            show_numbers(product, result)
            show_card_actions(product)


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
elif st.session_state["view"] == "Explore products":
    show_explore()
else:
    show_coming_soon()

show_start_over()