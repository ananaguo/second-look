# products.py
# All the facts about each product live here.
# The app reads this file. scoring.py uses these facts to pick a tier.

# ==========================================================================
# ==========================================================================
#
#   EDIT HERE: product data. Every number needs a source and an as-of date.
#
#   - Change a number?  Update its "sources" entry and "as_of" date too.
#   - "as_of" dates are written as "YYYY-MM-DD".
#   - Anything marked VERIFY still needs a human to double-check it.
#   - Use None when we don't know a value yet.
#
# ==========================================================================
# ==========================================================================


# The six tiers, from safest (1) to wildest (6).
# "icon" is the picture shown next to the name. We always show the icon
# AND the name together, never color alone.
TIERS = [
    {
        "number": 1,
        "name": "Safe Harbor",
        "icon": "⚓",
        "waves": 0,
        "sentence": "Your money is tied up at the dock: the U.S. government stands behind it, and it grows slowly.",
        "rule": "Backed by the U.S. government.",
    },
    {
        "number": 2,
        "name": "Calm Bay",
        "icon": "🌊",
        "waves": 1,
        "sentence": "Close to shore in still water: not government-insured, but losses have been small and rare.",
        "rule": "Worst year 10% or less.",
    },
    {
        "number": 3,
        "name": "Coastal Waters",
        "icon": "🌊🌊",
        "waves": 2,
        "sentence": "Along the coast: steady trips most years, but some rough seas.",
        "rule": "Worst year over 10% up to 25%.",
    },
    {
        "number": 4,
        "name": "Open Sea",
        "icon": "🌊🌊🌊",
        "waves": 3,
        "sentence": "Out on the open sea: the biggest catch over many years, and some very rough years.",
        "rule": "Worst year over 25% up to 50%.",
    },
    {
        "number": 5,
        "name": "Storm Waters",
        "icon": "🌊🌊🌊🌊",
        "waves": 4,
        "sentence": "Sailing into storms: big wins happen, and so do shipwrecks.",
        "rule": "Worst year over 50%, with standard protections.",
    },
    {
        "number": 6,
        "name": "Uncharted Waters",
        "icon": "🌊🌊🌊🌊🌊⚠️",
        "waves": 5,
        "sentence": "No map and no coast guard: anything can happen, and scams are common.",
        "rule": "Worst year over 50%, without standard protections.",
    },
]

# Saved rates, shown when live FRED data isn't available.
# Each one needs an as-of date ("YYYY-MM-DD"). Use None if we don't have one.
SAVED_RATES = {
    "tbill": {"pct": 4.1, "as_of": "2026-10-23"},     # TreasuryDirect / Trading Economics
    "cd12": {"pct": 1.73, "as_of": "2026-09-21"},     # FDIC national rates
    "savings": {"pct": 0.37, "as_of": "2026-09-21"},  # FDIC national rates
    "ten_year": {"pct": None, "as_of": None},         # VERIFY: no saved figure yet
}

# The products. Each one is a dictionary with the same keys.
# access must be one of: "anytime", "small_penalty", "locked_years"
PRODUCTS = [
    # 1. Savings account
    {
        "key": "savings",
        "name": "Savings account at an FDIC-insured bank",
        "one_line": "A bank account you can add to or take from anytime, insured up to $250,000.",
        "government_backed": True,
        "worst_year_loss_pct": 0,
        "worst_year": "none (insured)",
        "protections": True,
        "access": "anytime",
        "access_note": "Take money out anytime.",
        "yearly_cost_pct": 0,
        "sales_or_surrender_charge": False,
        "cost_note": "No yearly fee at most banks.",
        "gain_note": "The national average savings rate was 0.37% in September 2026; some insured banks pay much more.",
        "insurance_note": "FDIC-insured up to $250,000 per person, per bank, per ownership category.",
        "sources": [
            {
                "label": "FDIC",
                "url": "https://www.fdic.gov/resources/deposit-insurance/brochures/deposits-at-a-glance",
                "as_of": "2026-10-23",
            },
            {
                "label": "FDIC national rates",
                "url": "https://www.fdic.gov/national-rates-and-rate-caps",
                "as_of": "2026-09-21",
            },
        ],
    },
    # 2. 12-month CD
    {
        "key": "cd12",
        "name": "12-month CD at an FDIC-insured bank",
        "one_line": "You leave money at a bank for 12 months for a fixed rate, insured up to $250,000.",
        "government_backed": True,
        "worst_year_loss_pct": 0,
        "worst_year": "none (insured)",
        "protections": True,
        "access": "small_penalty",
        "access_note": "Taking money out early costs some interest; check the bank's penalty.",
        "yearly_cost_pct": 0,
        "sales_or_surrender_charge": False,
        "cost_note": "No yearly fee.",
        "gain_note": "The national average 12-month CD paid 1.73% in September 2026, about $173 a year on $10,000.",
        "insurance_note": "FDIC-insured up to $250,000 per person, per bank, per ownership category.",
        "sources": [
            {
                "label": "FDIC national rates",
                "url": "https://www.fdic.gov/national-rates-and-rate-caps",
                "as_of": "2026-09-21",
            },
            {
                "label": "YieldDocket",
                "url": "https://yielddocket.com/cd-rates/",
                "as_of": "2026-10-23",
            },
        ],
    },
    # 3. 3-month Treasury bill
    {
        "key": "tbill",
        "name": "3-month Treasury bill",
        "one_line": "A short loan to the U.S. government that pays you back in 3 months.",
        "government_backed": True,
        "worst_year_loss_pct": 0,
        "worst_year": "none if held to maturity",
        "protections": True,
        "access": "anytime",
        "access_note": "Matures in 3 months; selling early can change the price slightly.",
        "yearly_cost_pct": 0,
        "sales_or_surrender_charge": False,
        "cost_note": "No fee when bought at TreasuryDirect.",
        "gain_note": "About 4.1% a year in October 2026, about $410 a year on $10,000.",
        "insurance_note": "Backed by the U.S. government.",
        "sources": [
            {
                "label": "TreasuryDirect",
                "url": "https://www.treasurydirect.gov",
                "as_of": "2026-10-23",
            },
            {
                "label": "Trading Economics",
                "url": "https://tradingeconomics.com/united-states/3-month-bill-yield",
                "as_of": "2026-10-23",
            },
        ],
    },
    # 4. I bond
    {
        "key": "ibond",
        "name": "I bond (U.S. savings bond)",
        "one_line": "A U.S. savings bond whose interest rate follows inflation.",
        "government_backed": True,
        "worst_year_loss_pct": 0,
        "worst_year": "none",
        "protections": True,
        "access": "small_penalty",
        "access_note": "Can't be cashed in the first 12 months; cashing before 5 years loses the last 3 months of interest.",
        "yearly_cost_pct": 0,
        "sales_or_surrender_charge": False,
        "cost_note": "No fee.",
        "gain_note": "The rate changes every May and November; check TreasuryDirect for today's rate.",
        "insurance_note": "Backed by the U.S. government.",
        "sources": [
            {
                "label": "TreasuryDirect",
                "url": "https://www.treasurydirect.gov/savings-bonds/i-bonds/",
                "as_of": "2026-10-23",
            },
        ],
    },
    # 5. Money market fund
    {
        "key": "mmfund",
        "name": "Money market fund (at a brokerage)",
        "one_line": "A fund that holds very short-term loans. Not FDIC-insured.",
        "government_backed": False,
        "worst_year_loss_pct": 3,
        "worst_year": "2008 (one fund; VERIFY)",
        "protections": True,
        "access": "anytime",
        "access_note": "Sell any business day.",
        "yearly_cost_pct": None,
        "sales_or_surrender_charge": False,
        "cost_note": "Enter your fund's expense ratio here.",
        "gain_note": "Roughly follows Treasury bill rates minus the fund's fee; check its current yield.",
        "insurance_note": "Not FDIC-insured. A bank's money market account is a different, insured product.",
        "sources": [
            {
                "label": 'SEC.gov (VERIFY the 2008 figure: search "Reserve Primary Fund broke the buck")',
                "url": "https://www.sec.gov",
                "as_of": "2026-10-23",
            },
        ],
    },
    # 6. Fixed annuity
    {
        "key": "fixedannuity",
        "name": "Fixed annuity (multi-year guarantee)",
        "one_line": "A contract with an insurance company that pays a fixed rate for a set number of years.",
        "government_backed": False,
        "worst_year_loss_pct": 0,
        "worst_year": "none from markets (insurer guarantee)",
        "protections": False,
        "access": "locked_years",
        "access_note": "Surrender charges usually apply for several years; check the contract's schedule.",
        "yearly_cost_pct": 0,
        "sales_or_surrender_charge": True,
        "cost_note": "No yearly fee, but surrender charges to leave early.",
        "gain_note": "The guaranteed rate is in the contract; compare it with CD and Treasury rates.",
        "insurance_note": "Guaranteed by the insurance company, not the government. Not FDIC-insured.",
        "sources": [
            {
                "label": "California Department of Insurance",
                "url": "https://www.insurance.ca.gov/0150-seniors/0600informationguides/upload/Annuities-What-Seniors-Need-to-Know-01-17.pdf",
                "as_of": "2026-10-23",
            },
        ],
    },
    # 7. Total bond market index fund
    {
        "key": "bondindex",
        "name": "Total bond market index fund",
        "one_line": "A low-cost fund that owns thousands of U.S. bonds.",
        "government_backed": False,
        "worst_year_loss_pct": 13.0,
        "worst_year": "2022",
        "protections": True,
        "access": "anytime",
        "access_note": "Sell any business day; the price may be down.",
        "yearly_cost_pct": 0.05,
        "sales_or_surrender_charge": False,
        "cost_note": "Example value; enter your fund's expense ratio.",
        "gain_note": "10-year Treasury bonds averaged about 4.9% a year from 1928 to 2025.",
        "insurance_note": "Not FDIC-insured.",
        "sources": [
            {
                "label": "YCharts",
                "url": "https://ycharts.com/indices/%5EBBUSATR",
                "as_of": "2026-10-23",
            },
            {
                "label": "FinanceWonk",
                "url": "https://www.financewonk.com/references/historical-returns",
                "as_of": "2026-10-23",
            },
        ],
    },
    # 8. Balanced 60/40 fund
    {
        "key": "balanced",
        "name": "Balanced 60/40 index fund",
        "one_line": "A fund that holds about 60% stocks and 40% bonds.",
        "government_backed": False,
        "worst_year_loss_pct": 22.1,
        "worst_year": "2008",
        "protections": True,
        "access": "anytime",
        "access_note": "Sell any business day; the price may be down.",
        "yearly_cost_pct": 0.07,
        "sales_or_surrender_charge": False,
        "cost_note": "0.07% a year for Vanguard Balanced Index, Admiral shares.",
        "gain_note": "Historically landed between bonds and stocks.",
        "insurance_note": "Not FDIC-insured.",
        "sources": [
            {
                "label": "Yahoo Finance",
                "url": "https://finance.yahoo.com/quote/VBIAX/performance/",
                "as_of": "2026-10-23",
            },
        ],
    },
    # 9. S&P 500 index fund
    {
        "key": "sp500",
        "name": "S&P 500 index fund",
        "one_line": "A low-cost fund that owns the 500 largest U.S. companies.",
        "government_backed": False,
        "worst_year_loss_pct": 43.8,
        "worst_year": "1931",
        "protections": True,
        "access": "anytime",
        "access_note": "Sell any business day; the price may be down.",
        "yearly_cost_pct": 0.05,
        "sales_or_surrender_charge": False,
        "cost_note": "Example value; enter your fund's expense ratio.",
        "gain_note": "About 10% a year on average from 1928 to 2025 with dividends reinvested; about one year in four lost money.",
        "insurance_note": "Not FDIC-insured.",
        "sources": [
            {
                "label": "NYU Stern (Damodaran)",
                "url": "https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/histretSP.html",
                "as_of": "2026-10-23",
            },
            {
                "label": "WealthSim",
                "url": "https://www.wealthsim.app/blog/sp500-historical-returns",
                "as_of": "2026-10-23",
            },
        ],
    },
    # 10. Variable annuity
    {
        "key": "variableannuity",
        "name": "Variable annuity (stock funds)",
        "one_line": "An insurance contract whose value rises and falls with the stock funds inside it.",
        "government_backed": False,
        "worst_year_loss_pct": 43.8,
        "worst_year": "moves like stocks (1931)",
        "protections": True,
        "access": "locked_years",
        "access_note": "SEC example: a 7% surrender charge in year one, falling 1% a year.",
        "yearly_cost_pct": 1.25,
        "sales_or_surrender_charge": True,
        "cost_note": "Base fee about 1.25% a year, plus fund fees and optional extras.",
        "gain_note": "Grows with its stock funds, minus fees.",
        "insurance_note": "Not FDIC-insured.",
        "sources": [
            {
                "label": "SEC investor bulletin",
                "url": "https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins/updated-5",
                "as_of": "2026-10-23",
            },
        ],
    },
    # 11. One company's stock
    {
        "key": "singlestock",
        "name": "One company's stock",
        "one_line": "A share of a single company.",
        "government_backed": False,
        "worst_year_loss_pct": 100,
        "worst_year": "can go to zero",
        "protections": True,
        "access": "anytime",
        "access_note": "Sell any business day; the price may be down.",
        "yearly_cost_pct": 0,
        "sales_or_surrender_charge": False,
        "cost_note": "Most brokers charge little or nothing to trade.",
        "gain_note": "Can double in a year or lose everything; no average applies.",
        "insurance_note": "Not FDIC-insured.",
        "sources": [
            {
                "label": "SEC EDGAR",
                "url": "https://www.sec.gov/edgar/search/",
                "as_of": "2026-10-23",
            },
        ],
    },
    # 12. Bitcoin
    {
        "key": "bitcoin",
        "name": "Bitcoin",
        "one_line": "A digital currency with no government or company behind it.",
        "government_backed": False,
        "worst_year_loss_pct": 73,
        "worst_year": "2018",
        "protections": False,
        "access": "anytime",
        "access_note": "Sold on exchanges and apps; accounts can be frozen or hacked.",
        "yearly_cost_pct": None,
        "sales_or_surrender_charge": False,
        "cost_note": "Fees vary by app or exchange.",
        "gain_note": "Rose about 156% in 2023, but its history is short and its swings are extreme.",
        "insurance_note": "Not FDIC-insured and not covered by SIPC.",
        "sources": [
            {
                "label": "ChartRow",
                "url": "https://chartrow.com/bitcoin/returns",
                "as_of": "2026-10-23",
            },
            {
                "label": "Coinfuty",
                "url": "https://www.coinfuty.com/yearly-returns",
                "as_of": "2026-10-23",
            },
        ],
    },
]


# ==========================================================================
# END OF EDIT HERE SECTION
# ==========================================================================

# Historical series suitable for illustrating these product categories.
# These are benchmarks, not verified returns of an individual offered product.
RISK_BENCHMARKS = {
    "sp500": {"series": "stocks", "label": "U.S. stock-market historical benchmark",
              "note": "Benchmark returns, not the return history of a specific fund. Fees and tracking differences are excluded."},
    "tbill": {"series": "tbills", "label": "Treasury-bill historical benchmark",
              "note": "Annual returns from a Treasury-bill investment strategy, not the price risk of one bill held to maturity. Zero historical nominal losses do not mean zero inflation or early-sale risk."},
}
