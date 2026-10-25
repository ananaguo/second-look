# tests/check_history.py
# Checks the History numbers and charts in charts.py.
# It doesn't call grok or Cartesia (no credits used, no internet needed).
# Run from the project folder:  python tests\check_history.py
# (Streamlit may print a "No runtime found" warning. That is normal here.)

import os
import sys

# Let Python find charts.py in the project folder.
PROJECT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_FOLDER)

from charts import (
    RUN_LENGTHS,
    SERIES_KEYS,
    START_YEARS,
    biggest_drop,
    count_losses,
    decade_chart,
    growth_chart,
    growth_points,
    load_history,
    return_records,
    returns_scale,
    run_years,
    signed_percent,
    spread_labels,
)

results = []  # One True (pass) or False (fail) per check.


def check(description, ok):
    """Print PASS or FAIL for one check and remember the result."""
    print(f"{'PASS' if ok else 'FAIL'}  {description}")
    results.append(ok)


def close(a, b, within=0.01):
    """True if two numbers are nearly the same."""
    return abs(a - b) <= within


# ---------- Part 1: reading data/history.csv ----------
print("=" * 60)
print("READING THE DATA")
print("=" * 60)
history = load_history()
check(f"data/history.csv has {len(history)} years", len(history) > 0)
if not history:
    print("\nNo history numbers. Check that data/history.csv exists.")
    sys.exit(1)

years = [row["year"] for row in history]
check(f"first year is 1928 (got {years[0]})", years[0] == 1928)
check(f"last year is 2025 (got {years[-1]})", years[-1] == 2025)
check("no year is missing in between", years == list(range(years[0], years[-1] + 1)))

by_year = {row["year"]: row for row in history}
check(f"decimals became percents: 1931 stocks is about -43.84 (got {by_year[1931]['stocks']:.2f})",
      close(by_year[1931]["stocks"], -43.84))
losses, total = count_losses(history, "stocks")
print(f"      Stocks lost money in {losses} of the {total} years.")
check("Treasury bills never lost money in a year", count_losses(history, "tbills")[0] == 0)

# ---------- Part 2: the words and the math ----------
print("\n" + "=" * 60)
print("WORDS AND MATH")
print("=" * 60)
check("a loss has a real minus sign", signed_percent(-43.837) == "−43.8%")
check("a gain has a plus sign", signed_percent(12.44) == "+12.4%")
check("a tiny loss is never shown as -0.0%", signed_percent(-0.0167) == "−0.02%")

one_year = growth_points(history, 1931, 1)["stocks"]
check(f"$10,000 in stocks during 1931 became about $5,616 (got ${one_year[-1][2]:,.0f})",
      close(one_year[-1][2], 5616, within=1))
check("the first point is the start, at $10,000", one_year[0] == (0, "Start of 1931", 10000))

check("biggest drop: 10,000 → 12,000 → 6,000 → 9,000 is from 12,000 to 6,000",
      biggest_drop([10000, 12000, 6000, 9000]) == (12000, 6000))
check("biggest drop: money that only rises has none",
      biggest_drop([10000, 11000, 12000]) is None)

check("2010 for 20 years stops at 2025 (16 years)", len(run_years(history, 2010, 20)) == 16)
check("'To 2025' from 1928 runs every year", len(run_years(history, 1928, 0)) == len(history))

heights = spread_labels({"a": 100, "b": 101, "c": 500}, gap=50)
check("end-of-line words never sit on top of each other",
      heights["b"] - heights["a"] >= 50 and heights["c"] - heights["b"] >= 50)

# ---------- Part 3: every chart can be drawn ----------
print("\n" + "=" * 60)
print("CHARTS")
print("=" * 60)
problems = []
for key in SERIES_KEYS:
    records = return_records(history, key)
    scale = returns_scale(records)
    for decade in sorted({record["decade"] for record in records}):
        try:
            decade_chart(records, decade, scale).to_dict()
        except Exception as error:
            problems.append(f"{key} {decade}s: {error}")
check(f"every decade chart draws for all three choices ({len(problems)} problems)", not problems)

problems = []
for start in START_YEARS:
    for length in RUN_LENGTHS:
        try:
            growth_chart(growth_points(history, start, length)).to_dict()
        except Exception as error:
            problems.append(f"{start} for {length}: {error}")
check(f"every 'What $10,000 became' choice draws ({len(problems)} problems)", not problems)
for problem in problems:
    print(f"      {problem}")

# ---------- Total ----------
passed = results.count(True)
failed = results.count(False)
print("\n" + "=" * 60)
print(f"TOTAL: {passed} passed, {failed} failed, out of {len(results)} checks")
print("=" * 60)

# Exit with an error code if anything failed.
if failed > 0:
    sys.exit(1)