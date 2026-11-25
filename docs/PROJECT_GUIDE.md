# Project Guide

## 1. What this project does

In simple terms, a stock market data analyzer takes historical prices and turns them into understandable summaries and charts. Instead of looking through a long table, a user can inspect the closing-price trend, moving averages, returns, and a historical volatility estimate.

Technically, the program obtains OHLCV (open, high, low, close, volume) observations from Yahoo Finance or a CSV, validates and orders the rows, computes percentage returns and rolling statistics with pandas/NumPy, then writes chart images, an enriched CSV, and a text/CSV summary.

It can help investors, analysts, traders, and finance teams organize market observations, compare periods, monitor trends, and communicate research. Companies may use market data in research, portfolio monitoring, risk reviews, and decision support. This small educational project does not make decisions or place trades. Its indicators are descriptive and do not predict future returns.

### Workflow

`collect prices → clean and validate → inspect trends → calculate averages and returns → estimate historical risk → visualize → write a report`

Daily return is `today's close / previous close - 1`. A simple moving average (SMA) is the mean of recent closes. Volatility here is the standard deviation of daily returns multiplied by the square root of 252 trading days; it is a historical estimate, not a forecast.

## 2. Technology choices

| Option | Tools | Difficulty | Expected result |
|---|---|---:|---|
| A: Easy | Python, CSV, pandas, Matplotlib | Beginner | One ticker analysis and saved charts |
| B: Intermediate (this project) | Python, pandas, NumPy, Matplotlib, yfinance, CLI, FastAPI and Streamlit | Beginner to intermediate | Reusable historical analyzer, CSV input, report, charts, API and interactive dashboard |
| C: Advanced | This repo includes a small FastAPI API and illustrative crossover backtest; PostgreSQL, scheduled ingestion, Next.js/Plotly, containers and deployment are extensions | Advanced | HTTP endpoints now, with a path toward a multi-user service and web dashboard |

Option B is a good student starting point: its calculations are visible and it runs locally without paid terminals. Yahoo Finance access is subject to the provider's availability and terms. The sample CSV makes the analysis path usable offline.

## 3. Architecture and data flow

```text
Ticker + date range ──┐
                      ├─> Yahoo historical loader ─┐
CSV file ─────────────┘                    ├─> cleaning/validation
                                           └─> returns + SMA + volatility
                                                  ├─> analysis.csv
                                                  ├─> summary.txt / summary.csv
                                                  └─> PNG charts
```

Input: ticker/date range or CSV containing `Date` and `Close` (other OHLCV columns are optional). Processing validates and sorts data, calculates daily returns, SMAs and rolling volatility, then produces a report, enriched CSV and charts. FastAPI exposes health, analysis, CSV upload, latest summary and backtest endpoints. Streamlit provides a local interactive view.

The original larger product idea also mentions live feeds, watchlists, portfolios, alerts, and a Next.js client. Those require a persistent database, scheduling or streaming service, alert rules, user-facing authentication, and a separate JavaScript app; they are extension work, not included in this course-sized local MVP. Yahoo Finance downloads are historical snapshots, not a guaranteed real-time feed.

## 4. Build plan, expected results, and common mistakes

| Phase | Work and why | Expected output | Common beginner mistake |
|---|---|---|---|
| 1. Setup | Install Python and create an isolated environment | Working project environment | Installing packages into a different Python than the IDE uses |
| 2. Folders | Keep source, data, reports, and outputs separate | Clear repository layout | Committing `.venv` or mixing generated output with source |
| 3. Collection | Fetch a ticker/date range or load CSV | Raw dated prices | Assuming internet/provider access always succeeds |
| 4. Cleaning | Parse dates/numbers, remove invalid rows and duplicates | Chronologically sorted data | Treating missing values as zero or forgetting date order |
| 5. EDA | Check row count, date range, and price distribution | Basic data understanding | Drawing conclusions from too few observations |
| 6. Moving averages | Calculate 20/50 session means | Trend context in a chart | Calling an SMA a forecast or signal guarantee |
| 7. Returns/risk | Calculate percentage returns and volatility | Performance and variability summary | Comparing raw prices across different tickers |
| 8. Visuals | Save labeled charts | PNG charts in `outputs/` | Omitting units, dates, or chart titles |
| 9. Report | Summarize period, extremes, returns, and volatility | Text and CSV summaries | Describing historical results as future performance |
| 10. GitHub | Commit source, docs, sample data, selected outputs | Reproducible portfolio repo | Committing secrets or large unnecessary files |

## 5. Folder map

```text
Stock-Market-Data-Analyzer/
├── data/                 # Small, permitted sample input data
├── notebooks/            # Optional experiments and EDA notebooks
├── src/stock_analyzer/   # Reusable analysis, backtest, CLI and API modules
├── tests/                # Sample-data and validation checks
├── outputs/              # Generated CSV, reports, and charts (ignored by default)
├── images/               # README screenshots and presentation images
├── reports/              # Curated report artifacts for GitHub
├── docs/                 # This project guide
├── main.py               # CLI entry point
├── requirements.txt
├── .gitignore
└── README.md
```

## 6. Installation and usage

Install Python 3.10 or newer. In the project folder, create and activate a virtual environment:

**Windows PowerShell**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**macOS/Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Use live data (internet required):

```bash
python main.py --ticker AAPL --start 2023-01-01 --end 2024-01-01
```

Use the included offline sample:

```bash
python main.py --ticker DEMO --csv data/sample_prices.csv
```

Use a custom CSV and output directory:

```bash
python main.py --ticker MY_STOCK --csv data/my_prices.csv --output-dir outputs/my_stock
```

CSV must have `Date` and `Close` columns; date strings should be parseable and close values numeric and positive. The end date for Yahoo Finance follows its exclusive-end convention. A download failure is reported; sample data is used only when a CSV is explicitly selected.

## 7. Outputs and example interpretation

The CLI prints the source, date range, row count, first/latest/average closes, period return, high/low close, averages, volatility and trend. It creates `analysis.csv`, `summary.csv`, `summary.txt`, price/SMA/daily-return/distribution charts, plus a volume chart when valid volume is present.

With the included fixture, the close moves from 101 to 115, so the sample period return is about 13.86%. This is synthetic demonstration data, not a real ticker history. The precise volatility and dates are calculated by the program.

To capture the system simulation, run a live request or the sample CSV command, inspect the enriched output CSV, and open each PNG. The figures show the observed path and return distribution; the text file records the summary. Use clearly labeled screenshots and identify whether each run used real or sample data.

### Streamlit dashboard

Install dependencies with `python -m pip install -r requirements.txt`, then run `python -m streamlit run dashboard.py`. Choose Yahoo Finance or CSV upload in the sidebar, set dates, and select **Analyze Stock**. The Analysis, Backtesting and About views include charts, summary metrics, signal results and CSV/report downloads.

### FastAPI endpoints

Install requirements, then run `uvicorn src.stock_analyzer.api:app --reload`. Open `http://127.0.0.1:8000/docs`. Routes: `GET /`, `GET /health`, `GET /analyze/{ticker}`, `POST /analyze/csv`, `GET /latest`, and `GET /backtest/{ticker}`. Date parameters use ISO strings and an exclusive end. The backtest compares a long/flat 20/50 SMA crossover with buy-and-hold, excludes transaction costs, and is not a forecast.

## 8. GitHub and proof-of-work plan

Suggested repository name: `stock-market-data-analyzer`. Description: `Educational Python project for historical stock data analysis, returns, moving averages, volatility, charts, reports, and a small FastAPI service.` Suggested topics: `python`, `pandas`, `numpy`, `matplotlib`, `yfinance`, `fastapi`, `data-analysis`, `finance`, `beginner-project`.

Create an empty GitHub repository, then from the project directory:

```bash
git init
git add .
git commit -m "Build stock market data analyzer"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/stock-market-data-analyzer.git
git push -u origin main
```

Six-day learning/proof schedule:

| Day | Commit | Evidence screenshot |
|---|---|---|
| 1 Setup | `chore: create project structure and environment docs` | Folder tree and installed environment (hide personal paths) |
| 2 Data | `feat: add Yahoo Finance and CSV data loading` | Dataset preview with source identified |
| 3 Cleaning/EDA | `feat: clean and inspect historical prices` | Date range and cleaned CSV preview |
| 4 Indicators | `feat: calculate returns moving averages and volatility` | Summary output and indicator columns |
| 5 Charts | `feat: save price return and moving average charts` | Closing, SMA, and returns charts |
| 6 Report/docs | `docs: add project guide and usage examples` | README and repository page |

Create the repository, connect it to the local folder, commit in small meaningful steps, and push. Commit the small sample CSV and a few carefully selected screenshot/report examples if useful. Avoid committing virtual environments, API keys, or large generated datasets. To include an output artifact despite the ignore rule, use `git add -f outputs/summary.txt` (and only the files you intend to publish).

### Screenshot checklist

Capture: project folder tree; sample dataset preview; terminal run; closing price chart; moving average chart; daily returns chart; volatility summary in terminal/report; final `summary.txt`; and the GitHub repository page. Keep ticker, dates, source, and sample/live status visible where possible. Save polished screenshots in `images/` and link them from the README.

## 9. Interview preparation

1. **Explain your project.** “I built a Python stock data analyzer that loads historical OHLCV prices from Yahoo Finance or CSV, cleans and sorts them, calculates daily returns, 20/50 day moving averages and historical volatility, then saves charts and a concise report. I used pandas and NumPy for calculations and Matplotlib for visuals. It is an educational analysis tool, not a trading recommendation.”
2. **What is a daily return?** The percentage change from one close to the next, `close.pct_change()`. It makes price movement easier to compare across different price levels.
3. **What does an SMA show?** The average close over a fixed number of trading observations. It smooths short-term movement but lags and does not predict the future.
4. **How is volatility estimated here?** Standard deviation of daily percentage returns, annualized with `sqrt(252)`. It summarizes historical variability and relies on assumptions; it is not a complete measure of risk.
5. **How did you handle missing or duplicate data?** Parse dates and numeric fields, drop rows with invalid dates or close prices, keep the last row for a duplicated date, and sort chronologically.
6. **Why support CSV in addition to an API?** CSV permits offline runs, reproducible examples, and data from other permitted sources; a source label is retained in the summary.
7. **Why use pandas and NumPy?** They provide clear tabular operations and efficient numerical calculations such as returns, rolling means, and standard deviation.
8. **What is a limitation?** Historical observations may be incomplete or adjusted; provider availability varies, indicators are descriptive, and the project omits transaction costs, taxes, and portfolio constraints.
9. **How would you test or extend it?** Add unit tests for cleaning/calculations, compare against hand-calculated sample values, add structured logging and validation, then build an API and dashboard with suitable data storage.
10. **How would you present results to a nontechnical stakeholder?** Lead with date range and data source, show clearly labeled charts, explain return and volatility in plain language, and separate observed facts from interpretation.

**HR explanation:** “I chose a project that connects Python programming with financial data. I planned the data flow, built a reusable command-line tool, documented how to reproduce it, and learned to explain both its value and limitations.”

**Technical explanation:** “The CLI accepts a ticker, date window, optional CSV path, and output directory. The loader normalizes input columns, the cleaner validates Date/Close and sorts observations, and the calculation layer adds returns, rolling SMAs, and annualized rolling volatility. The output layer writes CSVs, PNGs, and a text report.”

## 10. Disclaimer

This project is for education and demonstration only. It is not financial advice, an offer, or a recommendation to buy or sell any security. Market data can be delayed, incomplete, adjusted, or inaccurate. Make financial decisions with qualified guidance and appropriate research.
