# charts.py
# The two charts in Second Look, drawn with Altair (it comes with Streamlit).
#   show_worst_year_chart(rows)  Explore products: what $10,000 became in its worst year
#   show_fees_chart(rows)        Compare: what yearly fees add up to over 10 years
# rows is a list of (product, result) pairs from app.py, already in label order
# (Safe Harbor first, Uncharted Waters last).
# The tier always comes from scoring.py (inside each result). Nothing here picks a tier.

import altair as alt
import streamlit as st

from scoring import tier_label

# ---------- How the charts look ----------
FONT = "Times New Roman"
NAVY = "#14213D"        # the bars and the words on them
TEXT = "#1B1F24"        # axis words
GRID = "#D5DAE1"        # thin grid lines
WHITE = "#FFFFFF"       # the chart's background (the card is white too)
LABEL_SIZE = 18         # axis labels and the words next to each bar
TITLE_SIZE = 20         # axis titles
ROW_HEIGHT = 56         # pixels for each bar's row, so bars are easy to tell apart
BAR_THICKNESS = 32      # how thick each bar is
NAME_WIDTH = 420        # the longest a product name on the left may be, in pixels

# ---------- Words ----------
EXAMPLE_AMOUNT = 10000
FEE_YEARS = 10
TABLE_LABEL = "Show these numbers as a table"
SEPARATOR = " · "       # between the parts of a bar's words

WORST_TITLE = "In its worst year, what $10,000 became"
WORST_SENTENCE = (
    "Shorter bars lost more in their worst year. "
    "A label describes a kind of product, not a promise."
)
INSURED_TEXT = "insured"
BIG_LOSS_TEXT = "Could lose most or all"
NOT_KNOWN_TEXT = "Not known yet"

FEES_TITLE = "What yearly fees add up to on $10,000 over 10 years"
FEES_SENTENCE = (
    "Simplified: ignores growth, taxes and surrender charges. "
    "Small yearly fees add up."
)
SURRENDER_TEXT = "plus surrender charges"
VARIES_TEXT = "Varies"


# ---------- Small helpers ----------

def safe_text(text):
    """Keep $ signs as plain dollar signs (Streamlit treats $...$ as math)."""
    return str(text).replace("$", "\\$")


def dollars(amount):
    """A whole number of dollars, like 5620 → "$5,620"."""
    return f"${amount:,}"


def sources_text(product):
    """Every source of a product with its as-of date, on one line."""
    parts = [f"{source['label']} (as of {source['as_of']})" for source in product["sources"]]
    return "; ".join(parts) if parts else "No sources yet"


def bar_chart(records, x_title, x_max, tooltip, description, tick_values=None):
    """One horizontal bar chart, used by both charts.
    Each record needs: product, value (a number), has_bar (True or False)
    and bar_text (the words written next to the bar).
    x_max is a little bigger than the longest bar, so the words next to it fit."""
    data = alt.Data(values=records)

    # Product names down the left side, in the same order as the records.
    order = [record["product"] for record in records]
    y = alt.Y(
        "product:N",
        sort=order,
        title=None,
        axis=alt.Axis(labelLimit=NAME_WIDTH, labelPadding=12, ticks=False),
    )

    # The dollar line along the bottom.
    axis_settings = {"format": "$,.0f", "title": x_title}
    if tick_values is not None:
        axis_settings["values"] = tick_values
    else:
        axis_settings["tickCount"] = 5
    x_scale = alt.Scale(domain=[0, x_max])

    # Navy bars. Products with no number (has_bar is False) get no bar.
    bars = (
        alt.Chart(data)
        .transform_filter("datum.has_bar")
        .mark_bar(color=NAVY, size=BAR_THICKNESS)
        .encode(
            x=alt.X("value:Q", scale=x_scale, axis=alt.Axis(**axis_settings)),
            y=y,
            tooltip=tooltip,
        )
    )

    # The words written right after each bar, so nobody has to hover.
    words = (
        alt.Chart(data)
        .mark_text(
            align="left",
            baseline="middle",
            dx=10,
            color=NAVY,
            font=FONT,
            fontSize=LABEL_SIZE,
            fontWeight="bold",
        )
        .encode(
            x=alt.X("value:Q", scale=x_scale),
            y=y,
            text="bar_text:N",
            tooltip=tooltip,
        )
    )

    chart = alt.layer(bars, words).properties(
        width="container",                 # full width
        height=alt.Step(ROW_HEIGHT),       # one tall row per product
        description=description,          # read by screen readers
    )

    # Fonts, sizes and colors. Altair charts don't animate, so nothing moves.
    return (
        chart.configure(font=FONT, background=WHITE)
        .configure_axis(
            labelFont=FONT,
            titleFont=FONT,
            labelFontSize=LABEL_SIZE,
            titleFontSize=TITLE_SIZE,
            labelColor=TEXT,
            titleColor=TEXT,
            gridColor=GRID,
            domainColor=TEXT,
        )
        .configure_view(stroke=None)
    )


def show_chart_card(key, title, sentence, chart, table):
    """A white card with the title, the one sentence, the chart,
    and a box you open to see the same numbers as a table."""
    # The key starts with "card_", so styles.py draws it as a card.
    with st.container(key=key):
        st.markdown(f"### {safe_text(title)}")
        st.markdown(safe_text(sentence))
        # theme=None: use our own fonts and colors, not Streamlit's.
        st.altair_chart(chart, theme=None)
        with st.expander(TABLE_LABEL, icon="📋"):
            st.dataframe(table, hide_index=True)


# ---------- Chart 1: the worst year (Explore products) ----------

def worst_year_records(rows):
    """One record per product for the worst-year chart."""
    records = []
    for product, result in rows:
        tier = result["tier"]
        tier_name = tier_label(tier)
        lost = result["worst_case_dollars"]

        if tier == 1:
            # Safe Harbor: the U.S. government stands behind it.
            value = EXAMPLE_AMOUNT
            amount_words = f"{dollars(value)} ({INSURED_TEXT})"
        elif lost is None:
            value = None
            amount_words = NOT_KNOWN_TEXT
        else:
            # 10000 × (1 − worst_year_loss_pct / 100)
            value = max(0, EXAMPLE_AMOUNT - lost)
            amount_words = f"{dollars(value)} ({product['worst_year']})"

        parts = [amount_words, tier_name]
        if tier in (5, 6):
            parts.append(BIG_LOSS_TEXT)

        records.append({
            "product": product["name"],
            "tier": tier_name,
            "worst_year": product["worst_year"],
            "value": value if value is not None else 0,
            "has_bar": value is not None,
            "amount": dollars(value) if value is not None else NOT_KNOWN_TEXT,
            "bar_text": SEPARATOR.join(parts),
            "note": BIG_LOSS_TEXT if tier in (5, 6) else "",
            "source": sources_text(product),
        })
    return records


def show_worst_year_chart(rows):
    """Explore products: what $10,000 became in each product's worst year."""
    if not rows:
        return
    records = worst_year_records(rows)

    tooltip = [
        alt.Tooltip("product:N", title="Product"),
        alt.Tooltip("tier:N", title="Label"),
        alt.Tooltip("amount:N", title="What $10,000 became"),
        alt.Tooltip("worst_year:N", title="Worst year"),
        alt.Tooltip("source:N", title="Source"),
    ]
    chart = bar_chart(
        records,
        x_title="What $10,000 became in its worst year",
        # Room on the right for the words; the dollar line stops at $10,000.
        x_max=EXAMPLE_AMOUNT * 2,
        tick_values=[0, 2500, 5000, 7500, 10000],
        tooltip=tooltip,
        description=WORST_TITLE,
    )

    table = [
        {
            "Product": record["product"],
            "Label": record["tier"],
            "What $10,000 became": record["amount"],
            "Worst year": record["worst_year"],
            "Note": record["note"],
            "Source": record["source"],
        }
        for record in records
    ]
    show_chart_card("card_chart_worst", WORST_TITLE, WORST_SENTENCE, chart, table)


# ---------- Chart 2: fees over 10 years (Compare) ----------

def fee_records(rows):
    """One record per chosen product for the fees chart."""
    records = []
    for product, result in rows:
        cost = product["yearly_cost_pct"]
        surrender = product["sales_or_surrender_charge"]

        if cost is None:
            fee = None
            words = VARIES_TEXT
            yearly_words = "Not known"
        else:
            # yearly_cost_pct × $10,000 × 10 years
            fee = round(cost * EXAMPLE_AMOUNT * FEE_YEARS / 100)
            words = dollars(fee)
            yearly_words = f"{cost:g}% a year"
        if surrender:
            words += f" {SURRENDER_TEXT}"

        records.append({
            "product": product["name"],
            "tier": tier_label(result["tier"]),
            "value": fee if fee is not None else 0,
            "has_bar": fee is not None,
            "bar_text": words,
            "yearly": yearly_words,
            "surrender": "Yes" if surrender else "No",
            "note": product["cost_note"],
            "source": sources_text(product),
        })
    return records


def show_fees_chart(rows):
    """Compare: what yearly fees add up to over 10 years, for the chosen products."""
    if not rows:
        return
    records = fee_records(rows)

    # Room on the right for the words. At least $100, so all-zero fees still draw.
    biggest = max([record["value"] for record in records if record["has_bar"]] or [0])
    x_max = max(biggest, 100) * 2

    tooltip = [
        alt.Tooltip("product:N", title="Product"),
        alt.Tooltip("tier:N", title="Label"),
        alt.Tooltip("yearly:N", title="Yearly fee"),
        alt.Tooltip("bar_text:N", title="Fees over 10 years"),
        alt.Tooltip("surrender:N", title="Surrender or sales charge"),
        alt.Tooltip("note:N", title="Note"),
        alt.Tooltip("source:N", title="Source"),
    ]
    chart = bar_chart(
        records,
        x_title="Fees over 10 years on $10,000",
        x_max=x_max,
        tooltip=tooltip,
        description=FEES_TITLE,
    )

    table = [
        {
            "Product": record["product"],
            "Yearly fee": record["yearly"],
            "Fees over 10 years on $10,000": record["bar_text"],
            "Surrender or sales charge": record["surrender"],
            "Note": record["note"],
            "Source": record["source"],
        }
        for record in records
    ]
    show_chart_card("card_chart_fees", FEES_TITLE, FEES_SENTENCE, chart, table)