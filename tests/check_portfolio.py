# tests/check_portfolio.py
# Checks the seven rules in portfolio.py, and the check on Grok's wording.
# It never calls Grok (no credits used, no internet needed).
# Every holding below is made up for Rosa, our fictional persona.
# Run from the project folder:  python tests\check_portfolio.py
# (Streamlit may print a "No runtime found" warning. That is normal here.)

import datetime
import os
import sys

PROJECT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_FOLDER)

from portfolio import check_explanation, check_portfolio, findings_for_ai
from scoring import DROP_SELL, GOAL_SAFE, NEED_1_TO_5_YEARS

results = []
TODAY = datetime.date(2026, 10, 25)


def check(description, ok):
    """Print PASS or FAIL for one check and remember the result."""
    print(f"{'PASS' if ok else 'FAIL'}  {description}")
    results.append(bool(ok))


def rules_found(findings):
    """The rule numbers that matched, like [1, 2, 4]."""
    return sorted({finding["rule"] for finding in findings})


# Rosa's made-up holdings
ROSA = [
    {"product_key": "cd12", "nickname": "Rosa CD", "company": "Bayside Community Bank",
     "amount": 200000, "rate_pct": 1.0, "end_date": "2026-11-20"},
    {"product_key": "savings", "nickname": "Rosa savings", "company": "bayside community bank ",
     "amount": 60000, "rate_pct": 0.5, "end_date": None},
    {"product_key": "variableannuity", "nickname": "Golden Years", "company": "Harborlight Mutual Life",
     "amount": 100000, "rate_pct": None, "end_date": None},
    {"product_key": "bitcoin", "nickname": "Coins", "company": "Lumacoin Vault",
     "amount": 5000, "rate_pct": None, "end_date": None},
]
ANSWERS = {"age": "70–74", "income": "Prefer not to say", "need": NEED_1_TO_5_YEARS,
           "drop": "Stay calm", "goal": "Grow it over many years"}
RATES = {"inflation_12m": {"value": 2.9, "date": TODAY}, "cd12": {"value": 1.73, "date": TODAY}}

print("=" * 60)
print("THE SEVEN RULES")
print("=" * 60)
findings = check_portfolio(ROSA, ANSWERS, RATES, today=TODAY)
for finding in findings:
    print(f"      Rule {finding['rule']}: {finding['sentence']}")
check("Rules 1, 2, 4, 5, 6 and 7 match Rosa's list", rules_found(findings) == [1, 2, 4, 5, 6, 7])
check("Rule 2: the annuity's fee is $1,250 a year",
      any("$1,250 a year" in f["sentence"] for f in findings if f["rule"] == 2))
check("Rule 6: the two Bayside deposits add up to $260,000",
      any("$260,000" in f["sentence"] for f in findings if f["rule"] == 6))
check("No answers: rules 1 and 3 don't run",
      not {1, 3} & set(rules_found(check_portfolio(ROSA, None, RATES, today=TODAY))))
check("No inflation figure: rule 4 doesn't run",
      4 not in rules_found(check_portfolio(ROSA, ANSWERS, {}, today=TODAY)))

rough = [{"product_key": "sp500", "nickname": "", "company": "A", "amount": 80000},
         {"product_key": "savings", "nickname": "", "company": "B", "amount": 20000}]
check("Rule 3: 80% in Open Sea, and would sell, matches",
      3 in rules_found(check_portfolio(rough, {"drop": DROP_SELL}, {}, today=TODAY)))
check("Rule 3: the same, but calm answers, doesn't match",
      3 not in rules_found(check_portfolio(rough, {"drop": "Stay calm"}, {}, today=TODAY)))
check("Rule 3: goal keep it safe also matches",
      3 in rules_found(check_portfolio(rough, {"goal": GOAL_SAFE}, {}, today=TODAY)))
check("Nothing at all gives no findings", check_portfolio([], ANSWERS, RATES, today=TODAY) == [])

print("\n" + "=" * 60)
print("WHAT GROK SEES")
print("=" * 60)
text = findings_for_ai(findings)
private = ["Rosa CD", "Rosa savings", "Golden Years", "Coins", "Bayside", "Harborlight", "Lumacoin"]
check("No nickname or company name is sent to Grok",
      not any(word.lower() in text.lower() for word in private))

print("\n" + "=" * 60)
print("CHECKING GROK'S WORDING")
print("=" * 60)
check("Numbers from the findings are fine",
      check_explanation("Your fees are about $1,250 a year, which is 1.25% of $100,000.", text)[0])
check("A made-up dollar amount is caught",
      not check_explanation("You could save $999 a year.", text)[0])
check("A made-up percent is caught",
      not check_explanation("Some accounts pay 5.5 percent.", text)[0])
check("The word 'sell' is caught", not check_explanation("You should sell it.", text)[0])
check("The word 'best' is caught", not check_explanation("The best choice is clear.", text)[0])
check("'selling can have tax effects' is allowed",
      check_explanation("Selling can have tax effects.", text)[0])

passed = results.count(True)
print("\n" + "=" * 60)
print(f"TOTAL: {passed} passed, {len(results) - passed} failed, out of {len(results)} checks")
print("=" * 60)
sys.exit(0 if passed == len(results) else 1)