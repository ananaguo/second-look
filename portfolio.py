# portfolio.py
# The portfolio check on My products: "Things worth a look".
# Every finding comes from the SEVEN published rules below, never from the AI.
#   check_portfolio(holdings, answers, live_rates)  the findings, as a list
#   findings_for_ai(findings)                       the findings as text for claude
#                                                   (no email, nicknames or company names)
#   check_explanation(answer, findings_text)        is claude's wording safe to show?
#   show_portfolio_check(...)                       draws the section on My products
# claude only rewrites the findings in plain words. If its wording uses any dollar
# amount or percent that isn't in the findings, or says buy, sell, best or
# recommended, we don't show it.

import datetime
import re

import streamlit as st

from claude_helper import explain_findings
from products import PRODUCTS, SAVED_RATES
from scoring import (
    DROP_SELL,
    GOAL_SAFE,
    NEED_1_TO_5_YEARS,
    NEED_WITHIN_1_YEAR,
    assign_tier,
)

# ---------- The numbers the rules use ----------
COST_LIMIT_PCT = 1            # rule 2: yearly cost over 1%
ROUGH_TIER = 4                # rule 3: Open Sea (tier 4) or rougher
ROUGH_SHARE_PCT = 50          # rule 3: more than 50% of the total
ENDING_SOON_DAYS = 60         # rule 5: an end date within 60 days
FDIC_LIMIT = 250000           # rule 6: the FDIC limit per bank
UNCHARTED_TIER = 6            # rule 7: Uncharted Waters
# Rule 6 only counts bank deposits. Treasury bills and I bonds are
# Safe Harbor too, but they are not deposits at a bank.
BANK_DEPOSIT_KEYS = ("savings", "cd12")

# ---------- The seven published rules ----------
RULES = {
    1: {
        "name": "Locked money you may need",
        "text": "A product is locked for years, and you said you may need money within 5 years.",
        "option": (
            "Before deciding anything, ask the company for your surrender schedule in writing. "
            "Leaving early can cost a surrender charge."
        ),
    },
    2: {
        "name": "High yearly cost",
        "text": f"A product's yearly cost is over {COST_LIMIT_PCT}%.",
        "option": (
            "Ask for every yearly fee in writing, and compare with lower-cost products "
            "in the same tier."
        ),
    },
    3: {
        "name": "Rough water versus comfort",
        "text": (
            f"More than {ROUGH_SHARE_PCT}% of your total is in Open Sea or rougher, and you said "
            "you would sell on a drop or that your goal is to keep it safe."
        ),
        "option": (
            "Some people keep money they may need soon in calmer tiers. A fee-only fiduciary "
            "advisor can help you decide; selling can have tax effects."
        ),
    },
    4: {
        "name": "Earning less than prices are rising",
        "text": "A Safe Harbor product's interest rate is below how much prices rose over the past year.",
        "option": "",  # built in rule_inflation, because it includes today's CD rate
    },
    5: {
        "name": "Ending soon",
        "text": f"A product's end date is within {ENDING_SOON_DAYS} days.",
        "option": (
            "Decide before it renews automatically. Many banks give a short grace period "
            "after a CD ends; ask yours."
        ),
    },
    6: {
        "name": "Possibly above the insurance limit",
        "text": f"Safe Harbor bank deposits at the same bank add up to more than ${FDIC_LIMIT:,}.",
        "option": "Check your coverage with the FDIC's EDIE tool at edie.fdic.gov, or ask the bank.",
    },
    7: {
        "name": "Uncharted Waters",
        "text": "A product is in Uncharted Waters (tier 6).",
        "option": "Only money you could afford to lose belongs here. Watch for scams.",
    },
}

# ---------- Words shown on the screen ----------
SECTION_TITLE = "🔍 Things worth a look"
SECTION_INTRO = (
    "These come from seven published rules, not from the AI. "
    "They are not advice, and they are not a full review."
)
NOTHING_LINE = "Nothing stood out under our seven rules. This is not a full review."
NO_ANSWERS_LINE = (
    "Rules 1 and 3 use your answers on **Your situation**. "
    "Answer those questions to include these two checks."
)
NO_INFLATION_LINE = (
    "Rule 4 needs the past year's price rise from FRED, which isn't available right now, "
    "so it was skipped this time."
)
OPTIONS_TITLE = "Options to consider"
WORKED_TITLE = "How we worked this out"
EXPLAIN_BUTTON = "💬 Explain this in plain words"
EXPLAIN_SPINNER = "Writing it in plain words…"
EXPLAIN_TITLE = "💬 In plain words"
EXPLAIN_NOTE = (
    "Written by the AI from the findings above, then checked by us: "
    "every dollar amount and percent in it is in the findings."
)
EXPLAIN_TROUBLE = (
    "We couldn't get a plain-words explanation just now. "
    "The findings above are complete on their own."
)
EXPLAIN_UNSAFE = (
    "We didn't show the AI's wording, because it used a number or a word "
    "that isn't in the findings. The findings above come from our rules and are complete on their own."
)
READ_BUTTON = "🔊 Read aloud"

# ---------- What the safety check looks for in claude's answer ----------
# Dollar amounts like "$12,500" or "$1,250.50"
DOLLAR_PATTERN = re.compile(r"\$\s?(\d[\d,]*(?:\.\d+)?)")
# Percents like "4.1%" or "4.1 percent"
PERCENT_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s?(?:%|percent\b)", re.IGNORECASE)
# Words claude must never use. ("selling" is allowed: rule 3's option says
# "selling can have tax effects".)
BANNED_WORDS = {"buy", "buys", "buying", "sell", "sells", "best", "recommend", "recommends", "recommended"}


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


def money(amount):
    """Dollars, like 12500 → "$12,500" and 1250.5 → "$1,250.50"."""
    amount = float(amount)
    if abs(amount - round(amount)) < 0.005:
        return f"${round(amount):,}"
    return f"${amount:,.2f}"


def percent(value, digits=2):
    """A percent, like 4.1 → "4.1%"."""
    return f"{round(float(value), digits):g}%"


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


def first_upper(text):
    """The same words with a capital first letter, to start a sentence."""
    return text[:1].upper() + text[1:]


def same_bank(name):
    """A bank name made easy to compare: lowercase, single spaces."""
    return " ".join(str(name).lower().split())


def holding_rows(holdings):
    """Each holding with what the rules need. Holdings whose kind of product
    is missing from products.py, or with no real amount, are skipped.
    screen_name may use the nickname (shown only to the person).
    private_name never does (it is what claude sees)."""
    rows = []
    for number, holding in enumerate(holdings or [], start=1):
        product = product_by_key(holding.get("product_key"))
        try:
            amount = float(holding.get("amount"))
        except (TypeError, ValueError):
            continue
        if product is None or amount <= 0:
            continue
        try:
            rate = float(holding["rate_pct"]) if holding.get("rate_pct") is not None else None
        except (TypeError, ValueError):
            rate = None
        nickname = (holding.get("nickname") or "").strip()
        rows.append({
            "product": product,
            # The tier always comes from scoring.py.
            "tier": assign_tier(product)["tier"],
            "amount": amount,
            "rate": rate,
            "end": to_date(holding.get("end_date")),
            "company": (holding.get("company") or "").strip(),
            "screen_name": nickname or f"your {product['name']}",
            "private_name": f"product {number}: {product['name']}",
        })
    return rows


def make_finding(rule, sentence, private_sentence, numbers, option=None):
    """One finding: the rule, the sentence (for the screen), the same sentence
    without nicknames or company names (for claude), the numbers used, and one option."""
    return {
        "rule": rule,
        "name": RULES[rule]["name"],
        "rule_text": RULES[rule]["text"],
        "sentence": sentence,
        "private_sentence": private_sentence,
        "numbers": numbers,  # a list of (what it is, the value as words)
        "option": option if option is not None else RULES[rule]["option"],
    }


# ---------- The seven rules ----------

def rule_locked(rows, answers):
    """Rule 1: locked for years, and may need money within 5 years."""
    need = (answers or {}).get("need")
    if need not in (NEED_WITHIN_1_YEAR, NEED_1_TO_5_YEARS):
        return []
    findings = []
    for row in rows:
        if row["product"]["access"] != "locked_years":
            continue
        def words(name):
            return (f"You have {money(row['amount'])} in {name}, which is locked for years, "
                    "and you said you may need money within 5 years.")
        findings.append(make_finding(
            1, words(row["screen_name"]), words(row["private_name"]),
            [("Amount", money(row["amount"])), ("When you may need money", need)],
        ))
    return findings


def rule_cost(rows):
    """Rule 2: yearly cost over 1%."""
    findings = []
    for row in rows:
        cost = row["product"]["yearly_cost_pct"]
        if cost is None or cost <= COST_LIMIT_PCT:
            continue
        fee = row["amount"] * cost / 100
        def words(name):
            return (f"{first_upper(name)} costs about {money(fee)} a year in fees "
                    f"({percent(cost)} of {money(row['amount'])}).")
        findings.append(make_finding(
            2, words(row["screen_name"]), words(row["private_name"]),
            [("Amount", money(row["amount"])), ("Yearly cost", percent(cost)),
             ("Fees a year (amount × yearly cost)", money(fee))],
        ))
    return findings


def rule_rough(rows, answers):
    """Rule 3: more than 50% in Open Sea or rougher, and would sell or wants it safe."""
    answers = answers or {}
    said = []
    if answers.get("drop") == DROP_SELL:
        said.append("you would sell to stop the loss if $10,000 dropped to $7,000")
    if answers.get("goal") == GOAL_SAFE:
        said.append("your main goal is to keep it safe")
    total = sum(row["amount"] for row in rows)
    if not said or total <= 0:
        return []
    rough = sum(row["amount"] for row in rows
                if isinstance(row["tier"], int) and row["tier"] >= ROUGH_TIER)
    share = rough / total * 100
    if share <= ROUGH_SHARE_PCT:
        return []
    sentence = f"{percent(share, 1)} of your money is in Open Sea or rougher, and you said {' and '.join(said)}."
    return [make_finding(
        3, sentence, sentence,
        [("Total", money(total)), ("In Open Sea or rougher", money(rough)),
         ("Share of your total", percent(share, 1))],
    )]


def cd_rate_words(live_rates):
    """Today's national average 12-month CD rate, from FRED, or the saved figure."""
    live = (live_rates or {}).get("cd12")
    if live is not None:
        return f"Today's national average 12-month CD rate is {percent(live['value'])} (FRED)."
    saved = SAVED_RATES.get("cd12", {})
    if saved.get("pct") is None:
        return ""
    return (f"The last saved national average 12-month CD rate is {percent(saved['pct'])} "
            f"(FDIC, as of {saved['as_of']}).")


def rule_inflation(rows, live_rates):
    """Rule 4: a Safe Harbor product earning less than prices rose over the past year."""
    inflation = (live_rates or {}).get("inflation_12m")
    if inflation is None:
        return []
    prices_rose = round(inflation["value"], 1)
    option = (
        "Insured options that have paid more recently include high-yield savings accounts, "
        f"CDs and Treasury bills. {cd_rate_words(live_rates)}"
    ).strip()
    findings = []
    for row in rows:
        if row["tier"] != 1 or row["rate"] is None or row["rate"] >= prices_rose:
            continue
        def words(name):
            return (f"{first_upper(name)} earns {percent(row['rate'])}, while prices rose "
                    f"{percent(prices_rose, 1)} over the past year.")
        findings.append(make_finding(
            4, words(row["screen_name"]), words(row["private_name"]),
            [("Its interest rate", percent(row["rate"])),
             ("Price rise over the past year (FRED)", percent(prices_rose, 1))],
            option,
        ))
    return findings


def rule_ending(rows, today):
    """Rule 5: an end date within 60 days."""
    findings = []
    for row in rows:
        if row["end"] is None:
            continue
        days = (row["end"] - today).days
        if not 0 <= days <= ENDING_SOON_DAYS:
            continue
        def words(name):
            return f"{first_upper(name)} ends on {date_words(row['end'])}."
        findings.append(make_finding(
            5, words(row["screen_name"]), words(row["private_name"]),
            [("End date", date_words(row["end"])), ("Days from today", str(days))],
        ))
    return findings


def rule_fdic(rows):
    """Rule 6: Safe Harbor bank deposits at the same bank above $250,000."""
    banks = {}
    for row in rows:
        if row["tier"] != 1 or row["product"]["key"] not in BANK_DEPOSIT_KEYS:
            continue
        key = same_bank(row["company"])
        if not key:
            continue
        bank = banks.setdefault(key, {"name": row["company"], "total": 0})
        bank["total"] += row["amount"]
    findings = []
    for bank in banks.values():
        if bank["total"] <= FDIC_LIMIT:
            continue
        def words(name):
            return (f"You have {money(bank['total'])} at {name}, above the {money(FDIC_LIMIT)} "
                    "FDIC limit per person, per bank, per ownership category.")
        findings.append(make_finding(
            6, words(bank["name"]), words("one bank"),
            [("Bank deposits at this bank", money(bank["total"])), ("FDIC limit", money(FDIC_LIMIT))],
        ))
    return findings


def rule_uncharted(rows):
    """Rule 7: any money in Uncharted Waters."""
    amount = sum(row["amount"] for row in rows if row["tier"] == UNCHARTED_TIER)
    if amount <= 0:
        return []
    sentence = f"{money(amount)} is in Uncharted Waters, which has few protections."
    return [make_finding(7, sentence, sentence, [("In Uncharted Waters", money(amount))])]


def check_portfolio(holdings, answers, live_rates, today=None):
    """Run the seven published rules. Returns a list of findings, in rule order.
    today can be set by the tests; the app always uses today's date."""
    today = today or datetime.date.today()
    rows = holding_rows(holdings)
    return (
        rule_locked(rows, answers)
        + rule_cost(rows)
        + rule_rough(rows, answers)
        + rule_inflation(rows, live_rates)
        + rule_ending(rows, today)
        + rule_fdic(rows)
        + rule_uncharted(rows)
    )


# ---------- What claude sees, and checking what it says ----------

def findings_for_ai(findings):
    """The findings as plain text for claude: no email, no nicknames, no company names."""
    if not findings:
        return "There are no findings."
    parts = []
    for number, finding in enumerate(findings, start=1):
        numbers = "; ".join(f"{what}: {value}" for what, value in finding["numbers"])
        parts.append(
            f"Finding {number} ({finding['name']}): {finding['private_sentence']}\n"
            f"Numbers used: {numbers}\n"
            f"Option to consider: {finding['option']}"
        )
    return "\n\n".join(parts)


def to_number(text):
    """"12,500" → 12500.0"""
    return float(text.replace(",", ""))


def numbers_in(text):
    """Every dollar amount and percent in the text, as ("$", 12500.0) or ("%", 4.1)."""
    found = [("$", to_number(match)) for match in DOLLAR_PATTERN.findall(text)]
    found += [("%", to_number(match)) for match in PERCENT_PATTERN.findall(text)]
    return found


def check_explanation(answer, findings_text):
    """True if claude's wording is safe to show: every dollar amount and percent
    in it is also in the findings, and it never says buy, sell, best or recommended.
    Returns (True or False, the reason, for the terminal)."""
    if not isinstance(answer, str) or not answer.strip():
        return False, "empty answer"
    allowed = numbers_in(findings_text)
    for kind, value in numbers_in(answer):
        if not any(kind == ok_kind and abs(value - ok_value) < 0.005 for ok_kind, ok_value in allowed):
            return False, f"number not in the findings: {kind}{value:g}"
    words = set(re.findall(r"[a-z]+", answer.lower()))
    banned = words & BANNED_WORDS
    if banned:
        return False, f"banned word: {', '.join(sorted(banned))}"
    return True, ""


def get_explanation(findings):
    """Ask claude to explain the findings, then check its wording.
    Returns (the explanation, None), or (None, a calm message)."""
    text = findings_for_ai(findings)
    answer, error = explain_findings(text)
    if error:
        print(f"Portfolio explanation problem: {error}")
        return None, EXPLAIN_TROUBLE
    ok, reason = check_explanation(answer, text)
    if not ok:
        print(f"Portfolio explanation not shown: {reason}")
        return None, EXPLAIN_UNSAFE
    return answer, None


# ---------- On the screen ----------

def ask_for_explanation(findings_text):
    """Runs when "Explain this in plain words" is clicked."""
    st.session_state["portfolio_explain_for"] = findings_text


def show_finding(number, finding):
    """One finding: its sentence, the option to consider, and how we worked it out."""
    with st.container(key=f"notes_finding_{number}"):
        st.markdown(f"#### 🔍 {safe_text(finding['name'])}")
        st.markdown(safe_text(finding["sentence"]))
        st.markdown(f"**{OPTIONS_TITLE}:** {safe_text(finding['option'])}")
        with st.expander(WORKED_TITLE, icon="🔢"):
            lines = [f"**Rule {finding['rule']} of 7:** {safe_text(finding['rule_text'])}", ""]
            for what, value in finding["numbers"]:
                lines.append(f"- {safe_text(what)}: {safe_text(value)}")
            st.markdown("\n".join(lines))


def show_explanation(findings, start_speaking, show_voice):
    """The Explain button, and claude's checked wording once asked for.
    Each set of findings is only sent to claude once."""
    findings_text = findings_for_ai(findings)
    st.button(EXPLAIN_BUTTON, key="portfolio_explain", on_click=ask_for_explanation,
              args=(findings_text,), type="primary", width="stretch")

    if st.session_state.get("portfolio_explain_for") != findings_text:
        return
    saved = st.session_state.setdefault("portfolio_explained", {})
    if findings_text not in saved:
        with st.spinner(EXPLAIN_SPINNER):
            saved[findings_text] = get_explanation(findings)
    explanation, message = saved[findings_text]

    if message:
        st.info(message, icon="💬")
        return
    with st.container(key="notes_portfolio_explained"):
        st.markdown(f"#### {EXPLAIN_TITLE}")
        st.markdown(safe_text(explanation))
        st.markdown(f"*{EXPLAIN_NOTE}*")
        st.button(READ_BUTTON, key="portfolio_read", on_click=start_speaking,
                  args=(explanation,), width="stretch")
        show_voice(explanation)


def show_portfolio_check(holdings, answers, live_rates, start_speaking, show_voice):
    """The "Things worth a look" section on My products.
    start_speaking and show_voice are app.py's voice functions."""
    findings = check_portfolio(holdings, answers, live_rates)
    with st.container(key="card_portfolio"):
        st.markdown(f"### {SECTION_TITLE}")
        st.markdown(SECTION_INTRO)
        if not answers:
            st.markdown(f"📝 {NO_ANSWERS_LINE}")
        if (live_rates or {}).get("inflation_12m") is None:
            st.markdown(f"📡 {NO_INFLATION_LINE}")

        if findings:
            for number, finding in enumerate(findings, start=1):
                show_finding(number, finding)
        else:
            st.markdown(f"✅ {NOTHING_LINE}")

        show_explanation(findings, start_speaking, show_voice)