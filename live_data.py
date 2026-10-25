# live_data.py
# Live public data from FRED (Federal Reserve Bank of St. Louis).
#   get_series(series_id)  the latest value and date of one FRED series
#   get_live_rates()       every rate Second Look shows, plus inflation
# This file never crashes the page: if FRED is slow or down,
# it returns None and the app shows the saved figures from products.py.
# It never picks a tier. scoring.py always does that.

import datetime
import io
import urllib.request

import pandas as pd  # comes with Streamlit, so nothing to install
import streamlit as st

from products import SAVED_RATES

# ---------- Settings ----------
FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={}"
FRED_SERIES_URL = "https://fred.stlouisfed.org/series/{}"
TIMEOUT_SECONDS = 10           # give up on FRED after 10 seconds
SIX_HOURS = 6 * 60 * 60        # keep good downloads for 6 hours
TEN_MINUTES = 10 * 60          # after a problem, try FRED again after 10 minutes

# The rates we show. "label" is the words in front of the rate on screen.
SERIES = {
    "tbill": {"id": "DGS3MO", "name": "3-month Treasury bill rate", "label": "Today's rate"},
    "cd12": {"id": "NDR12MCD", "name": "National average 12-month CD rate", "label": "National average today"},
    "savings": {"id": "SNDR", "name": "National average savings rate", "label": "National average today"},
    "ten_year": {"id": "DGS10", "name": "10-year Treasury rate", "label": "10-year Treasury rate today, for comparison"},
}
CPI_ID = "CPIAUCSL"           # prices people pay (Consumer Price Index)
CPI_NAME = "Consumer prices (CPI)"

# The fallback for the too-good-to-be-true rule if nothing else is known
LAST_RESORT_TBILL_PCT = 4.1

# ---------- Words shown on the screen ----------
UNAVAILABLE_NOTE = "Live data unavailable right now; showing saved figures."
SOURCE_LINE = "Source: FRED, Federal Reserve Bank of St. Louis."
NOT_AVAILABLE = "not available right now"


# ---------- Downloading ----------

@st.cache_data(ttl=SIX_HOURS, show_spinner=False)
def download_series(series_id):
    """Every (date, value) row of one FRED series, oldest first.
    Raises an error if anything goes wrong. Errors are NOT cached,
    so a short FRED outage doesn't hide live data for 6 hours."""
    url = FRED_CSV_URL.format(series_id)
    request = urllib.request.Request(url, headers={"User-Agent": "SecondLook/1.0"})
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        text = response.read().decode("utf-8")

    # dtype=str keeps "." as text, so we can spot and skip it
    table = pd.read_csv(io.StringIO(text), dtype=str)

    # FRED has used both names for the date column
    if "observation_date" in table.columns:
        date_column = "observation_date"
    elif "DATE" in table.columns:
        date_column = "DATE"
    else:
        raise ValueError(f"No date column in {series_id}")

    # The value column is the other column (FRED names it after the series)
    value_columns = [name for name in table.columns if name != date_column]
    if not value_columns:
        raise ValueError(f"No value column in {series_id}")
    value_column = value_columns[0]

    rows = []
    for date_text, value_text in zip(table[date_column], table[value_column]):
        # Skip empty values and "." (FRED's mark for "no number that day")
        if pd.isna(value_text) or str(value_text).strip() in ("", "."):
            continue
        date = datetime.date.fromisoformat(str(date_text).strip())
        rows.append((date, float(value_text)))

    if not rows:
        raise ValueError(f"No numbers in {series_id}")
    rows.sort()
    return rows


def get_series(series_id):
    """The latest value of one FRED series: {"value": 4.12, "date": date}.
    None on any error."""
    try:
        rows = download_series(series_id)
    except Exception as error:
        print(f"FRED problem with {series_id}: {error}")
        return None
    date, value = rows[-1]
    return {"value": value, "date": date}


def get_inflation_12m():
    """How much prices rose from the same month one year earlier to the
    latest month, in percent: {"value": 2.9, "date": date}. None on any error."""
    try:
        rows = download_series(CPI_ID)
    except Exception as error:
        print(f"FRED problem with {CPI_ID}: {error}")
        return None

    latest_date, latest_value = rows[-1]
    for date, value in rows:
        if date.year == latest_date.year - 1 and date.month == latest_date.month and value:
            return {"value": (latest_value / value - 1) * 100, "date": latest_date}
    return None


@st.cache_data(ttl=TEN_MINUTES, show_spinner=False)
def get_live_rates():
    """Every live figure: tbill, cd12, savings, ten_year and inflation_12m.
    Each one is {"value": ..., "date": ...}, or None if it couldn't be fetched.
    If one download fails, the rest are skipped this round, so a slow FRED
    never makes the page wait more than about 10 seconds."""
    rates = {name: None for name in SERIES}
    rates["inflation_12m"] = None

    for name, info in SERIES.items():
        rates[name] = get_series(info["id"])
        if rates[name] is None:
            return rates  # FRED seems down: stop here, show saved figures

    rates["inflation_12m"] = get_inflation_12m()
    return rates


# ---------- Writing the figures in words ----------

def short_date(date):
    """A date like "Oct 22, 2026"."""
    return f"{date.strftime('%b')} {date.day}, {date.year}"


def month_year(date):
    """A date like "October 2026"."""
    return date.strftime("%B %Y")


def percent(value):
    """A percent like 4.12 → "4.12%", rounded to 2 decimal places."""
    return f"{round(value, 2):g}%"


def rate_text(rates, key):
    """One rate: live if we have it, otherwise the saved figure from products.py.
    Like "4.12% (FRED, Oct 22, 2026)" or "4.1% (saved figure, Oct 23, 2026)"."""
    live = (rates or {}).get(key)
    if live is not None:
        return f"{percent(live['value'])} (FRED, {short_date(live['date'])})"

    saved = SAVED_RATES.get(key, {})
    if saved.get("pct") is None or not saved.get("as_of"):
        return NOT_AVAILABLE
    saved_date = datetime.date.fromisoformat(saved["as_of"])
    return f"{percent(saved['pct'])} (saved figure, {short_date(saved_date)})"


def rate_line(rates, key):
    """One rate with its label, like "Today's rate: 4.12% (FRED, Oct 22, 2026)"."""
    return f"{SERIES[key]['label']}: {rate_text(rates, key)}"


def inflation_line(rates):
    """The Safe Harbor sentence about prices. None if we don't have it."""
    live = (rates or {}).get("inflation_12m")
    if live is None:
        return None
    return (
        f"Prices rose {round(live['value'], 1):g}% over the past year "
        f"(FRED, as of {month_year(live['date'])})."
    )


def tbill_rate_for_scoring(rates):
    """The 3-month T-bill rate for scoring.py's too-good-to-be-true rule:
    live if we have it, otherwise the saved figure."""
    live = (rates or {}).get("tbill")
    if live is not None:
        return live["value"]
    saved = SAVED_RATES.get("tbill", {}).get("pct")
    return saved if saved is not None else LAST_RESORT_TBILL_PCT


def any_missing(rates):
    """True if any live figure couldn't be fetched."""
    return any(value is None for value in (rates or {}).values()) or not rates


def footer_rows(rates):
    """One row per series for the footer: (name, series id, date words, link)."""
    rows = []
    for key, info in SERIES.items():
        live = (rates or {}).get(key)
        when = short_date(live["date"]) if live else NOT_AVAILABLE
        rows.append((info["name"], info["id"], when, FRED_SERIES_URL.format(info["id"])))
    inflation = (rates or {}).get("inflation_12m")
    when = month_year(inflation["date"]) if inflation else NOT_AVAILABLE
    rows.append((CPI_NAME, CPI_ID, when, FRED_SERIES_URL.format(CPI_ID)))
    return rows