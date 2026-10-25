# footer.py
# The footer at the bottom of every view:
# where to get help, when the live data was last updated,
# and the reminder that Second Look is not advice.
# app.py calls show_footer(NOTICE, get_live_rates()) once, at the very end of the page.

import html

import streamlit as st

from live_data import SOURCE_LINE, UNAVAILABLE_NOTE, any_missing, footer_rows

FOOTER_TITLE = "☎️ Help and a second opinion"
DATA_TITLE = "📡 Data last updated"
NEW_TAB = "(opens in a new tab)"

# The same numbers are in HELP_CARD_TEXT in app.py. If one changes, change both.
HELP_LINES = [
    {
        "name": "FINRA BrokerCheck",
        "number": "800-289-9999",
        "what": "Check anyone who sells investments.",
        "link": "https://brokercheck.finra.org",
        "link_text": "brokercheck.finra.org",
    },
    {
        "name": "FINRA Securities Helpline for Seniors",
        "number": "844-574-3577",
        "what": "Questions or worries about a brokerage account. "
                "Weekdays, 9 a.m. to 5 p.m. Eastern.",
    },
    {
        "name": "California Department of Insurance",
        "number": "1-800-927-4357",
        "what": "Annuities and insurance in California.",
    },
]


def help_html():
    """The three help lines. styles.py puts them side by side,
    or one under another on a phone."""
    items = []
    for line in HELP_LINES:
        parts = [
            f'<p class="help-name">{html.escape(line["name"])}</p>',
            f'<p class="help-number">{html.escape(line["number"])}</p>',
            f'<p>{html.escape(line["what"])}</p>',
        ]
        if line.get("link"):
            parts.append(
                f'<p><a href="{html.escape(line["link"])}" target="_blank" '
                f'rel="noopener noreferrer">{html.escape(line["link_text"])}</a> {NEW_TAB}</p>'
            )
        items.append(f'<div class="help-item">{"".join(parts)}</div>')
    # Everything on one line: Streamlit could misread spaces at the start of a line.
    return f'<div class="help-grid">{"".join(items)}</div>'


def data_html(rates):
    """Each FRED series with its date and a link to its page on FRED."""
    items = []
    for name, series_id, when, link in footer_rows(rates):
        items.append(
            f"<li><strong>{html.escape(name)}</strong>: {html.escape(when)}. "
            f'<a href="{html.escape(link)}" target="_blank" rel="noopener noreferrer">'
            f"{html.escape(series_id)} on FRED</a> {NEW_TAB}</li>"
        )
    # Everything on one line: Streamlit could misread spaces at the start of a line.
    return f'<ul>{"".join(items)}</ul>'


def show_footer(notice, rates=None):
    """The navy footer band. notice is the "educational, not advice" sentence from app.py.
    rates comes from get_live_rates() in live_data.py."""
    # The key starts with "band_dark_", so styles.py makes it a full-width navy band.
    with st.container(key="band_dark_footer"):
        st.markdown(f"## {FOOTER_TITLE}")
        st.markdown(help_html(), unsafe_allow_html=True)

        st.markdown(f"### {DATA_TITLE}")
        st.markdown(data_html(rates), unsafe_allow_html=True)
        st.markdown(SOURCE_LINE)
        if any_missing(rates):
            st.markdown(f"📡 **{UNAVAILABLE_NOTE}**")

        st.markdown(f"ℹ️ **{notice}**")