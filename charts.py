# charts.py
# Every chart in Second Look, drawn with Altair (it comes with Streamlit).
#   show_worst_year_chart(rows)    Explore products: what $10,000 became in its worst year
#   show_fees_chart(rows)          Compare: what yearly fees add up to over 10 years
#   show_tier_totals_chart(items)  My products: how much money is in each label
#   show_returns_card(...)         History: every year's return since 1928
#   show_growth_card(...)          History: what $10,000 became, with interest reinvested
#   show_history_note(history)     History: the "past results" line under both charts
# rows is a list of (product, result) pairs from app.py, already in label order
# (Safe Harbor first, Uncharted Waters last).
# The tier always comes from scoring.py (inside each result). Nothing here picks a tier.

import csv
import os

import altair as alt
import streamlit as st

from products import TIERS, RISK_BENCHMARKS
from risk_metrics import calculate_risk
from scoring import tier_label

# ---------- How the charts look ----------
FONT = "Times New Roman"
NAVY = "#14213D"        # bars, gains, and the stocks line
BROWN = "#6B2D1F"       # losses, and the bonds line
GRAY = "#4A5260"        # the Treasury bills line
TEXT = "#1B1F24"        # axis words and the zero line
GRID = "#D5DAE1"        # thin grid lines
WHITE = "#FFFFFF"       # the chart's background (the card is white too)
LABEL_SIZE = 18         # axis labels and the words on the chart
TITLE_SIZE = 20         # axis titles
CHART_TITLE_SIZE = 24   # small titles inside a chart, like "1930s"
ROW_HEIGHT = 56         # pixels for each bar's row, so bars are easy to tell apart
BAR_THICKNESS = 32      # how thick each bar is
NAME_WIDTH = 420        # the longest a product name on the left may be, in pixels
DECADE_HEIGHT = 260     # how tall each decade's chart is on History
GROWTH_HEIGHT = 460     # how tall the "What $10,000 became" chart is

# ---------- Words ----------
EXAMPLE_AMOUNT = 10000
FEE_YEARS = 10
TABLE_LABEL = "Show these numbers as a table"
SEPARATOR = " · "       # between the parts of a bar's words
MINUS = "−"             # a real minus sign, read aloud as "minus"

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

TIER_TOTALS_TITLE = "How much of your money is in each label"
TIER_TOTALS_SENTENCE = (
    "Each bar is the money you entered for that label, with its share of your total. "
    "A label describes a kind of product, not a promise."
)

# ---------- History: the data ----------
PROJECT_FOLDER = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(PROJECT_FOLDER, "data", "history.csv")
HISTORY_SOURCE = "NYU Stern (Damodaran)"
HISTORY_SOURCE_URL = "https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/histretSP.html"

# The three choices, in the order they appear. "key" is the column in history.csv.
HISTORY_SERIES = [
    {"key": "stocks", "name": "U.S. stocks (S&P 500)", "short": "U.S. stocks", "color": NAVY,
     "dash": [1, 0], "shape": "circle"},
    {"key": "tbonds", "name": "10-year Treasury bonds", "short": "10-year Treasury bonds", "color": BROWN,
     "dash": [12, 6], "shape": "square"},
    {"key": "tbills", "name": "3-month Treasury bills", "short": "3-month Treasury bills", "color": GRAY,
     "dash": [3, 5], "shape": "triangle-up"},
]
SERIES_KEYS = [series["key"] for series in HISTORY_SERIES]

# Start years for "What $10,000 became", and how long it runs (0 means to the end).
START_YEARS = [1928, 1950, 1970, 1990, 2000, 2010]
RUN_LENGTHS = [5, 10, 20, 0]

GAIN_WORD = "Gain"
LOSS_WORD = "Loss"
HISTORY_NOTE = (
    "Past results don't predict the future. These are index results and ignore fees and taxes. "
    "Source: [{source}]({url}), {first}–{last}."
)
HISTORY_MISSING = "📂 The history numbers were not found. Check that data/history.csv exists."


# ---------- Small helpers ----------

def safe_text(text):
    """Keep $ signs as plain dollar signs (Streamlit treats $...$ as math)."""
    return str(text).replace("$", "\\$")


def dollars(amount):
    """A whole number of dollars, like 5620 → "$5,620"."""
    return f"${round(amount):,}"


def signed_percent(value):
    """A yearly return in words for the chart, like "+12.4%" or "−43.8%".
    Very small returns get two decimals, so a tiny loss never shows as "−0.0%"."""
    digits = 2 if abs(value) < 0.1 else 1
    sign = MINUS if value < 0 else "+"
    return f"{sign}{abs(value):.{digits}f}%"


def sources_text(product):
    """Every source of a product with its as-of date, on one line."""
    parts = [f"{source['label']} (as of {source['as_of']})" for source in product["sources"]]
    return "; ".join(parts) if parts else "No sources yet"


def series_info(key):
    """The name, color and line style for one of the three choices."""
    for series in HISTORY_SERIES:
        if series["key"] == key:
            return series
    return HISTORY_SERIES[0]


def apply_look(chart):
    """Fonts, sizes and colors for any chart. Altair charts don't animate, so nothing moves."""
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
        .configure_title(
            font=FONT,
            fontSize=CHART_TITLE_SIZE,
            color=NAVY,
            anchor="start",
        )
        .configure_view(stroke=None)
    )


def show_table(table):
    """The box you open to see a chart's numbers as a table."""
    with st.expander(TABLE_LABEL, icon="📋"):
        st.dataframe(table, hide_index=True)


def bar_chart(records, x_title, x_max, tooltip, description, tick_values=None):
    """One horizontal bar chart, used by the product charts.
    Each record needs: product, value (a number), has_bar (True or False)
    and bar_text (the words written next to the bar).
    x_max is a little bigger than the longest bar, so the words next to it fit."""
    data = alt.Data(values=records)

    # Names down the left side, in the same order as the records.
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

    # Navy bars. Records with no number (has_bar is False) get no bar.
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
        height=alt.Step(ROW_HEIGHT),       # one tall row per bar
        description=description,          # read by screen readers
    )
    return apply_look(chart)


def show_chart_card(key, title, sentence, chart, table):
    """A white card with the title, the one sentence, the chart,
    and a box you open to see the same numbers as a table."""
    # The key starts with "card_", so styles.py draws it as a card.
    with st.container(key=key):
        st.markdown(f"### {safe_text(title)}")
        st.markdown(safe_text(sentence))
        # theme=None: use our own fonts and colors, not Streamlit's.
        st.altair_chart(chart, theme=None)
        show_table(table)


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


# ---------- Chart 3: money in each label (My products) ----------

def tier_total_records(items):
    """One record per label for the My products chart.
    items is a list of (tier, dollars) pairs; the tier comes from scoring.py.
    All six labels are shown, from Safe Harbor to Uncharted Waters,
    so you can see which ones have nothing in them too."""
    totals = {}
    for tier, amount in items:
        totals[tier] = totals.get(tier, 0) + amount
    grand_total = sum(totals.values())

    order = [tier["number"] for tier in sorted(TIERS, key=lambda t: t["number"])]
    # Products with no normal label go last, only if there are any.
    for extra in ("off_map", "not_rated"):
        if extra in totals:
            order.append(extra)

    records = []
    for tier in order:
        amount = totals.get(tier, 0)
        share = round(amount / grand_total * 100) if grand_total else 0
        records.append({
            "product": tier_label(tier),
            "value": amount,
            "has_bar": amount > 0,
            "amount": dollars(amount),
            "share": f"{share}%",
            "bar_text": f"{dollars(amount)}{SEPARATOR}{share}% of your total",
        })
    return records


def show_tier_totals_chart(items):
    """My products: how much money is in each label."""
    if not items:
        return
    records = tier_total_records(items)

    # Room on the right for the words. At least $100, so tiny amounts still draw.
    biggest = max(record["value"] for record in records)
    x_max = max(biggest, 100) * 2

    tooltip = [
        alt.Tooltip("product:N", title="Label"),
        alt.Tooltip("amount:N", title="Amount"),
        alt.Tooltip("share:N", title="Share of your total"),
    ]
    chart = bar_chart(
        records,
        x_title="Dollars in this label",
        x_max=x_max,
        tooltip=tooltip,
        description=TIER_TOTALS_TITLE,
    )

    table = [
        {
            "Label": record["product"],
            "Amount": record["amount"],
            "Share of your total": record["share"],
        }
        for record in records
    ]
    show_chart_card("card_chart_tiers", TIER_TOTALS_TITLE, TIER_TOTALS_SENTENCE, chart, table)


# ---------- History: reading data/history.csv ----------

@st.cache_data(show_spinner=False)
def load_history():
    """Every year from data/history.csv, oldest first, as percents:
    [{"year": 1928, "stocks": 43.8, "tbonds": 0.8, "tbills": 3.1}, ...].
    An empty list if the file is missing or broken."""
    rows = []
    try:
        with open(HISTORY_FILE, encoding="utf-8") as file:
            for line in csv.DictReader(file):
                try:
                    row = {"year": int(line["year"])}
                    for key in SERIES_KEYS:
                        row[key] = float(line[key])
                except (KeyError, TypeError, ValueError):
                    continue  # skip a row that isn't complete
                rows.append(row)
    except OSError:
        return []

    # The file may hold decimals, like -0.4384 for a 43.84% loss.
    # If every value is between -1 and 1, they are decimals: turn them into percents.
    values = [row[key] for row in rows for key in SERIES_KEYS]
    if values and all(-1 <= value <= 1 for value in values):
        for row in rows:
            for key in SERIES_KEYS:
                row[key] = row[key] * 100

    rows.sort(key=lambda row: row["year"])
    return rows


def first_and_last_year(history):
    """The first and last year in the data, like (1928, 2025)."""
    return history[0]["year"], history[-1]["year"]


def count_losses(history, key):
    """How many years lost money, and how many years there are."""
    losses = sum(1 for row in history if row[key] < 0)
    return losses, len(history)


# ---------- History chart 1: every year since 1928 ----------

def return_records(history, key):
    """One record per year for the yearly-returns chart."""
    series = series_info(key)
    records = []
    for row in history:
        value = row[key]
        year = row["year"]
        records.append({
            "year": year,
            "left": year - 0.4,         # the bar's left edge
            "right": year + 0.4,        # the bar's right edge
            "zero": 0,                  # every bar starts at the zero line
            "decade": year // 10 * 10,
            "value": value,
            "label": signed_percent(value),
            "kind": LOSS_WORD if value < 0 else GAIN_WORD,
            "series": series["name"],
            "source": HISTORY_SOURCE,
        })
    return records


def returns_scale(records):
    """One up-and-down scale for every decade, so bar heights can be compared.
    It always shows the zero line, with room above and below for the words."""
    values = [record["value"] for record in records]
    low = min(0, min(values))
    high = max(0, max(values))
    room = (high - low) * 0.2 or 1
    return alt.Scale(domain=[low - room, high + room], nice=False)


def decade_chart(records, decade, y_scale):
    """The bars for one decade, like 1930 to 1939.
    Gains go up from the zero line in navy, losses go down in brown,
    and every bar has its number written on it, with a + or − sign."""
    data = alt.Data(values=[record for record in records if record["decade"] == decade])
    years = [record["year"] for record in records if record["decade"] == decade]

    # Ten places for the ten years of the decade, so bars are the same width
    # in every decade. Only years with numbers get a year under them.
    x_scale = alt.Scale(domain=[decade - 0.5, decade + 9.5], nice=False, zero=False)
    color = alt.Color(
        "kind:N",
        scale=alt.Scale(domain=[GAIN_WORD, LOSS_WORD], range=[NAVY, BROWN]),
        legend=None,
    )
    tooltip = [
        alt.Tooltip("year:O", title="Year"),
        alt.Tooltip("series:N", title="Choice"),
        alt.Tooltip("label:N", title="Return"),
        alt.Tooltip("kind:N", title="Gain or loss"),
        alt.Tooltip("source:N", title="Source"),
    ]

    bars = alt.Chart(data).mark_bar().encode(
        x=alt.X(
            "left:Q",
            scale=x_scale,
            axis=alt.Axis(values=years, format="d", title=None, grid=False, labelAngle=0),
        ),
        x2="right:Q",
        y=alt.Y(
            "value:Q",
            scale=y_scale,
            axis=alt.Axis(title="Yearly return", tickCount=5, labelExpr=f"(datum.value < 0 ? '{MINUS}' : '') + abs(datum.value) + '%'"),
        ),
        y2="zero:Q",
        color=color,
        tooltip=tooltip,
    )

    # The words: above a gain, below a loss.
    word_style = {"font": FONT, "fontSize": LABEL_SIZE, "fontWeight": "bold"}
    gain_words = (
        alt.Chart(data)
        .transform_filter("datum.value >= 0")
        .mark_text(baseline="bottom", dy=-6, **word_style)
        .encode(x=alt.X("year:Q", scale=x_scale), y=alt.Y("value:Q", scale=y_scale),
                text="label:N", color=color, tooltip=tooltip)
    )
    loss_words = (
        alt.Chart(data)
        .transform_filter("datum.value < 0")
        .mark_text(baseline="top", dy=6, **word_style)
        .encode(x=alt.X("year:Q", scale=x_scale), y=alt.Y("value:Q", scale=y_scale),
                text="label:N", color=color, tooltip=tooltip)
    )

    # The zero line, dark and thick, so "above" and "below" are easy to see.
    zero_line = alt.Chart(alt.Data(values=[{"zero": 0}])).mark_rule(
        color=TEXT, strokeWidth=2
    ).encode(y=alt.Y("zero:Q", scale=y_scale))

    chart = alt.layer(bars, zero_line, gain_words, loss_words).properties(
        title=f"{decade}s",
        width="container",
        height=DECADE_HEIGHT,
        description=f"Yearly returns in the {decade}s",
    )
    return apply_look(chart)


def show_returns_card(history, pick_series):
    """History: one bar per year for the choice picked.
    pick_series is app.py's function that draws the choice and returns its key.
    The years are split into one chart per decade, so every bar has room for its number."""
    first = first_and_last_year(history)[0]
    with st.container(key="card_chart_returns"):
        st.markdown(f"### Every year since {first}")
        key = pick_series()
        show_risk_details(history, key, series_info(key)["name"],
                          "These estimates use the full available annual benchmark history, independently of the growth chart's selected start year.")
        losses, total = count_losses(history, key)
        st.markdown(f"Bars below the line are losing years: {losses} of the {total} years shown.")

        records = return_records(history, key)
        y_scale = returns_scale(records)
        for decade in sorted({record["decade"] for record in records}):
            st.altair_chart(decade_chart(records, decade, y_scale), theme=None)

        table = [
            {
                "Year": record["year"],
                "Return": record["label"],
                "Gain or loss": record["kind"],
            }
            for record in records
        ]
        show_table(table)


# ---------- History chart 2: what $10,000 became ----------

def run_years(history, start, length):
    """The years the money is invested: from the start year,
    for length years (0 means to the last year in the data)."""
    first, last = first_and_last_year(history)
    end = last if length == 0 else min(start + length - 1, last)
    return [row["year"] for row in history if start <= row["year"] <= end]


def growth_points(history, start, length):
    """For each choice: the money at the start, then at the end of each year,
    with dividends and interest reinvested.
    Returns {"stocks": [(step, when, dollars), ...], ...}.
    step 0 is the start; step 1 is the end of the first year, and so on."""
    by_year = {row["year"]: row for row in history}
    years = run_years(history, start, length)
    points = {}
    for key in SERIES_KEYS:
        money = EXAMPLE_AMOUNT
        line = [(0, f"Start of {start}", money)]
        for step, year in enumerate(years, start=1):
            money = money * (1 + by_year[year][key] / 100)
            line.append((step, f"End of {year}", money))
        points[key] = line
    return points


def biggest_drop(values):
    """The biggest fall from a high point to a later low point.
    Returns (high, low), or None if the money never fell below an earlier high."""
    peak = values[0]
    best = None
    best_fall = 0
    for value in values:
        if value > peak:
            peak = value
        fall = (peak - value) / peak
        if fall > best_fall:
            best_fall = fall
            best = (peak, value)
    return best


def spread_labels(end_values, gap):
    """Heights for the words at the right end of each line, so they never sit
    on top of each other. Each is at least gap away from the one below it.
    end_values is {key: dollars}; returns {key: height}."""
    heights = {}
    below = None
    for key, value in sorted(end_values.items(), key=lambda item: item[1]):
        # The lowest words stay a little above the bottom line, so they aren't cut off.
        height = max(value, gap * 0.6) if below is None else max(value, below + gap)
        heights[key] = height
        below = height
    return heights


def growth_chart(points):
    """One line per choice, each with its own color, dash and dot shape,
    and its name and ending value written at its right end."""
    steps = len(points[SERIES_KEYS[0]]) - 1
    names = [series_info(key)["name"] for key in SERIES_KEYS]

    line_records = []
    for key in SERIES_KEYS:
        name = series_info(key)["name"]
        for step, when, money in points[key]:
            line_records.append({
                "series": name,
                "step": step,
                "when": when,
                "value": money,
                "amount": dollars(money),
                "source": HISTORY_SOURCE,
            })

    # The words at the right end of each line.
    end_values = {key: points[key][-1][2] for key in SERIES_KEYS}
    top = max(end_values.values())
    heights = spread_labels(end_values, gap=top * 0.07)
    end_records = [
        {
            "series": series_info(key)["name"],
            "step": steps,
            "label_y": heights[key],
            "text": f"{series_info(key)['short']}: {dollars(end_values[key])}",
        }
        for key in SERIES_KEYS
    ]

    # Room on the right for the words; the year numbers stop at the last year.
    x_scale = alt.Scale(domain=[0, max(steps, 1) * 1.6], nice=False)
    # A year number every 1, 5 or 10 years, so they never crowd each other.
    tick_step = 1 if steps <= 10 else 5 if steps <= 40 else 10
    ticks = list(range(0, steps + 1, tick_step))
    # Always show the last year's number. If it would crowd the one before it,
    # it takes that one's place.
    if ticks[-1] != steps:
        if len(ticks) > 1 and steps - ticks[-1] < tick_step / 2:
            ticks[-1] = steps
        else:
            ticks.append(steps)
    y_scale = alt.Scale(domain=[0, max(heights.values()) * 1.1], nice=False)

    # The same color, dash and shape for each choice in every layer.
    color = alt.Color("series:N", scale=alt.Scale(
        domain=names, range=[series_info(key)["color"] for key in SERIES_KEYS]), legend=None)
    dash = alt.StrokeDash("series:N", scale=alt.Scale(
        domain=names, range=[series_info(key)["dash"] for key in SERIES_KEYS]), legend=None)
    shape = alt.Shape("series:N", scale=alt.Scale(
        domain=names, range=[series_info(key)["shape"] for key in SERIES_KEYS]), legend=None)
    tooltip = [
        alt.Tooltip("series:N", title="Choice"),
        alt.Tooltip("when:N", title="When"),
        alt.Tooltip("amount:N", title="What $10,000 became"),
        alt.Tooltip("source:N", title="Source"),
    ]

    line_data = alt.Data(values=line_records)
    x = alt.X(
        "step:Q",
        scale=x_scale,
        axis=alt.Axis(values=ticks, format="d", title=f"Years since the start of {points_start(points)}"),
    )
    y = alt.Y("value:Q", scale=y_scale, axis=alt.Axis(format="$,.0f", title="Value", tickCount=6))

    lines = alt.Chart(line_data).mark_line(strokeWidth=4).encode(
        x=x, y=y, color=color, strokeDash=dash, tooltip=tooltip
    )
    # A dot at every year (each choice has its own shape), except on long runs,
    # where so many dots would hide the lines.
    dot_size = 90 if steps <= 20 else 0
    dots = alt.Chart(line_data).mark_point(filled=True, size=dot_size, opacity=1).encode(
        x=x, y=y, color=color, shape=shape, tooltip=tooltip
    )
    words = alt.Chart(alt.Data(values=end_records)).mark_text(
        align="left", baseline="middle", dx=14, font=FONT, fontSize=LABEL_SIZE, fontWeight="bold"
    ).encode(
        x=alt.X("step:Q", scale=x_scale),
        y=alt.Y("label_y:Q", scale=y_scale),
        text="text:N",
        color=color,
    )

    chart = alt.layer(lines, dots, words).properties(
        width="container",
        height=GROWTH_HEIGHT,
        description="What $10,000 became in stocks, bonds and Treasury bills",
    )
    return apply_look(chart)


def points_start(points):
    """The start year, read from the first point, like "Start of 1928" → "1928"."""
    return points[SERIES_KEYS[0]][0][1].replace("Start of ", "")


def show_growth_card(history, pick_start, pick_length):
    """History: what $10,000 became in each of the three, with interest reinvested.
    pick_start and pick_length are app.py's functions that draw the choices."""
    last = first_and_last_year(history)[1]
    with st.container(key="card_chart_growth"):
        st.markdown("### What $10,000 became")
        start = pick_start()
        length = pick_length(last)

        years = run_years(history, start, length)
        if not years:
            st.markdown(f"📂 We have no numbers for {start}.")
            return
        end = years[-1]
        points = growth_points(history, start, length)

        sentence = (
            f"Each line starts with $10,000 at the start of {start}; "
            f"the words at its right end show what it became by the end of {end}."
        )
        if length and len(years) < length:
            sentence += f" Our numbers end in {last}, so this shows {len(years)} years."
        st.markdown(safe_text(sentence))

        st.altair_chart(growth_chart(points), theme=None)

        # The biggest drop for stocks, in words.
        stock_values = [money for step, when, money in points["stocks"]]
        drop = biggest_drop(stock_values)
        stocks_name = series_info("stocks")["name"]
        if drop is None:
            line = f"{stocks_name}: no drop along the way. It never ended a year below an earlier high."
        else:
            line = (
                f"{stocks_name}: Biggest drop along the way: "
                f"from {dollars(drop[0])} to {dollars(drop[1])}."
            )
        st.markdown(f"📉 **{safe_text(line)}**")

        table = []
        for index, (step, when, money) in enumerate(points["stocks"]):
            row = {"When": when}
            for key in SERIES_KEYS:
                row[series_info(key)["name"]] = dollars(points[key][index][2])
            table.append(row)
        show_table(table)


def show_history_note(history):
    """The line under both History charts."""
    first, last = first_and_last_year(history)
    note = HISTORY_NOTE.format(source=HISTORY_SOURCE, url=HISTORY_SOURCE_URL, first=first, last=last)
    st.markdown(f"ℹ️ {note}")

# Expanders stay collapsed; figures are calculated from local annual returns.
def show_risk_details(history, series, label, note="", inline=False):
    with (st.container() if inline else st.expander("Risk in numbers — more details", expanded=False)):
        st.markdown(f"**Historical benchmark: {label}**")
        if note:
            st.markdown(note)
        try:
            risk = calculate_risk(history, series)
        except (ValueError, KeyError, TypeError, OverflowError):
            st.info("Risk estimates are unavailable. Check data/history.csv for at least 40 complete, consecutive annual observations.")
            return
        st.caption(f"{risk['start']}–{risk['end']} · {risk['observations']} calendar years · one-year horizon · 95% confidence · $10,000 illustration")
        st.table([
            {"Measure": "95% historical Value at Risk", "Estimate": f"{risk['var_pct']:.2f}%", "Per $10,000": f"${risk['var_dollars']:,.0f}"},
            {"Measure": "Expected Shortfall (worst 5%)", "Estimate": f"{risk['es_pct']:.2f}%", "Per $10,000": f"${risk['es_dollars']:,.0f}"},
            {"Measure": "Maximum year-end drawdown", "Estimate": f"{risk['drawdown_pct']:.2f}%", "Per $10,000": f"${risk['drawdown_dollars']:,.0f} from an illustrative peak"},
            {"Measure": "Frequency of losing years", "Estimate": f"{risk['loss_frequency_pct']:.1f}% ({risk['losing_years']} of {risk['observations']})", "Per $10,000": "Not applicable"},
        ])
        st.markdown(
            "**VaR** is the historical loss threshold at the 95th percentile. It is not a maximum possible loss. "
            "**Expected Shortfall** averages the worst 5% of annual outcomes. "
            "**Drawdown** measures the largest compounded fall from a prior year-end peak, including the initial investment. "
            "Actual losses within a year can be much larger."
        )
        st.caption("Method: annual returns in percent; nearest-rank empirical VaR; tail-average ES with fractional observation weights. Gains count as zero downside loss. A zero estimate does not mean no risk. Results exclude fees, taxes, inflation, withdrawal penalties and default scenarios absent from the data. Historical frequencies are not forecasts. The $10,000 drawdown example scales a peak balance, not necessarily the initial investment.")
        st.markdown(f"Source: [{HISTORY_SOURCE}]({HISTORY_SOURCE_URL}). Data window is the local CSV shown above. These estimates do not change the product's risk tier.")


def show_product_risk(product, history=None, inline=False):
    benchmark = RISK_BENCHMARKS.get(product.get("key"))
    if benchmark:
        show_risk_details(load_history() if history is None else history,
                          benchmark["series"], benchmark["label"], benchmark["note"], inline=inline)
    else:
        with (st.container() if inline else st.expander("Risk in numbers — more details", expanded=False)):
            st.markdown("No suitable historical return series is configured for this product. We do not infer VaR from its single worst-year figure.")
            st.markdown("Use the insurance, access, costs, and historical-loss information above. A product-specific return series or contract model is needed to calculate additional risk estimates.")
