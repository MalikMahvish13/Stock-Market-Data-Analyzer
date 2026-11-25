# Project and college demonstration guide

## 1. Introduction

Stock Market Data Analyzer is an educational Python project that loads historical security prices from Yahoo Finance or a CSV and turns them into calculations, charts and a short report. It has three ways to use the same analysis package: command line, FastAPI and Streamlit.

## 2. Problem statement

Raw price tables contain many observations and are difficult to scan manually. A learner needs a repeatable way to clean a historical time series, calculate common indicators, visualize the movement, and explain both the findings and the limitations.

## 3. Why it was developed

The project combines Python programming and data analysis in a finance-themed application without requiring a paid terminal. The sample CSV supports an offline classroom demonstration; Yahoo Finance can provide public historical downloads when network access is available.

## 4. Objectives

- Load and validate historical price observations.
- Calculate daily returns, 20/50 session moving averages, and historical volatility.
- Summarize selected-period price behavior and show it in labeled charts.
- Demonstrate a simple, time-aligned historical strategy simulation.
- Present the same functions through CLI, FastAPI, and Streamlit.
- Practice Python modules, input validation, documentation, and testable code.

## 5. Technologies and their roles

| Technology | Role |
|---|---|
| Python | Application logic and interfaces |
| pandas | CSV handling, time-indexed data, rolling indicators |
| NumPy | Numerical calculations and volatility annualization |
| Matplotlib | Exportable PNG figures |
| yfinance | Public Yahoo Finance historical download adapter |
| FastAPI | HTTP endpoints, validation and Swagger UI |
| Streamlit | Interactive student-facing dashboard and downloads |
| Uvicorn | Local ASGI server for FastAPI |
| unittest | Standard-library automated checks |

## 6. Architecture and step-by-step workflow

```text
Ticker/date range or CSV
        ↓
Load selected source and validate input
        ↓
Clean dates and closing prices; sort chronologically
        ↓
Daily returns + SMA 20 + SMA 50 + rolling volatility
        ↓
Summary + charts + CSV/report + backtest
        ↓
CLI, FastAPI JSON/Swagger, or Streamlit dashboard
```

1. Select Yahoo Finance with ticker and dates, or explicitly choose a CSV.
2. Validate and clean dates, closing prices, duplicates and optional columns.
3. Calculate `close.pct_change()` for daily returns.
4. Calculate the 20- and 50-observation simple moving averages.
5. Calculate the 20-observation standard deviation of daily returns and annualize with `sqrt(252)`.
6. Summarize the selected period and create price, moving-average, return and optional volume charts.
7. Simulate an SMA crossover using yesterday's position for today's return, then compare with buy-and-hold.
8. Review saved outputs or access results in the API/dashboard.

See [architecture.md](architecture.md) for detailed component and sequence diagrams.

## 7. Indicator explanations

### SMA 20 and SMA 50

An SMA is the arithmetic mean of recent closing prices. SMA 20 averages up to the latest 20 observations; SMA 50 averages up to 50. The current implementation uses available observations for early rows, so a chart with fewer than 50 rows does not yet have a full 50-session average. A moving average smooths prices and lags them; it is not a forecast.

### Daily return

Daily return is `(today's close / prior close) - 1`. It describes the percentage change between adjacent observed sessions. The first row has no prior close and is therefore blank.

### Historical volatility

The 20-day volatility column is the rolling sample standard deviation of daily percentage returns multiplied by `sqrt(252)`, a conventional approximate number of trading sessions per year. The first values are blank until two returns exist. The summary also includes the selected-period annualized return standard deviation. Volatility measures past variability, not total risk or future movement.

### Trend interpretation

The project compares the most recent close and SMAs. Its short text label is descriptive, simple, and not a buy/sell recommendation.

## 8. Backtesting

The educational long/flat strategy uses SMA 20 above SMA 50 as its position condition. It records a `BUY` when the condition changes from false to true and a `SELL` when it changes from true to false; otherwise it reports `HOLD`. A signal calculated using a closing observation is applied to the following session's return by shifting position one row. This avoids applying a close-based signal to a return that occurred before that signal was known.

Strategy and buy-and-hold returns are compounded over the same selected data. The model does not include trading costs, taxes, slippage, dividends, liquidity, position sizing, or market impact. It is an educational simulation only. Past results do not guarantee future performance.

## 9. Running the application

From the repository root on macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py --ticker DEMO --csv data/sample_prices.csv
python -m streamlit run dashboard.py
# In a separate terminal with the same venv activated:
uvicorn src.stock_analyzer.api:app --reload
```

The CLI's Yahoo Finance example is `python main.py --ticker RELIANCE.NS --start 2025-01-01 --end 2025-11-26`. The end date is exclusive for Yahoo; the selected Streamlit end date is inclusive.

## 10. Outputs

The default `outputs/` contains `analysis.csv`, `summary.csv`, `summary.txt`, `closing_price.png`, `moving_averages.png`, `daily_returns.png`, `daily_return_distribution.png`, and `trading_volume.png` when valid volume is supplied. Charts are generated into a requested output directory; optional volume data is handled without blocking the rest of the analysis.

## 11. Limitations and future scope

This is not a production trading system. Yahoo data availability and adjustments can vary. There is no guaranteed live feed, persistent database, authentication, multi-user portfolio, alert delivery, or web client in Next.js. The backtest omits transaction costs and execution realities. Future study could add configurable costs, more robust risk measures, data persistence, additional validation, and a separate web frontend.

## 12. College demonstration sequence

1. **Introduction:** explain the problem and show the project folders.
2. **Offline source:** run the sample CSV command and point out the source label.
3. **Data and indicators:** open the generated CSV and explain daily return, SMA 20, SMA 50 and volatility.
4. **Charts/report:** show price, moving-average, daily-return and volume charts, then the text report.
5. **Dashboard:** select CSV upload, choose `data/sample_prices.csv`, set the date interval covering January 2024, and click **Analyze Stock**. Show the Overview and Backtesting pages and download buttons.
6. **API:** start Uvicorn and open `/docs`; demonstrate health and CSV analysis, then `/latest`.
7. **Limitations:** explain end-exclusive Yahoo dates, non-real-time data, backtest assumptions and the educational disclaimer.

## 13. Likely viva questions and simple answers

1. **What does your project do?** It analyzes historical stock prices and creates indicators, charts, reports, and a basic backtest.
2. **Why did you choose this project?** It lets me apply Python and time-series analysis to a familiar public-data problem.
3. **What is OHLCV?** Open, high, low, close, and volume for an observation period.
4. **What is a daily return?** The close-to-close percentage change between adjacent observations.
5. **Why calculate returns instead of only price changes?** Percentages make movement more comparable across different price levels.
6. **What is SMA 20?** The mean of up to the most recent 20 closing observations.
7. **What is SMA 50?** The mean of up to the most recent 50 closing observations.
8. **Why do moving averages lag?** They summarize past prices, so a change takes time to affect the average.
9. **What is volatility in this project?** A rolling standard deviation of daily returns, annualized using the square root of 252.
10. **Why use 252?** It is a common approximation for trading sessions in a year.
11. **Why is the first daily return empty?** There is no earlier close for comparison.
12. **Why are early volatility entries empty?** At least two daily returns are needed to calculate a standard deviation.
13. **How do you clean input data?** Parse dates and numbers, require Date/Close, discard invalid closes, remove duplicate dates and sort.
14. **What if volume is missing?** The analyzer skips the volume chart and continues with other analysis.
15. **Why support CSV?** It enables offline tests and user-provided data without paid terminals.
16. **What is the role of yfinance?** It downloads historical observations from Yahoo Finance when available.
17. **Is this real-time data?** No. The project uses historical downloads and cannot guarantee real-time updates.
18. **What is a backtest?** A simulation of a defined strategy on past observations.
19. **How does your crossover strategy work?** It is long when SMA 20 is above SMA 50 and moves to cash when it crosses below.
20. **How do you avoid look-ahead bias?** A signal at one close affects only the next session's return.
21. **Does the backtest include transaction costs?** No; that limitation is stated in the results and documentation.
22. **What is buy-and-hold?** A benchmark that remains invested across the selected interval.
23. **Why use pandas?** It provides tabular and time-indexed operations such as cleaning, rolling means and returns.
24. **Why use NumPy?** It supports efficient numeric calculations, including volatility annualization.
25. **Why use Matplotlib?** It generates labeled charts that can be saved and shared as image files.
26. **What does FastAPI provide?** HTTP endpoints and automatically generated OpenAPI/Swagger documentation.
27. **What does Streamlit provide?** A quick interactive Python dashboard with controls, charts and download buttons.
28. **What does the `/latest` endpoint return?** The most recent analysis summary kept in memory by that API process.
29. **What happens if Yahoo fails?** The request returns an understandable error; the app does not substitute sample prices.
30. **What are the main limitations?** Historical data can be incomplete, indicators lag, and the backtest omits real execution costs and constraints.
31. **Can the trend label predict price direction?** No. It is a descriptive rule based on past prices.
32. **How would you improve the project?** Add configurable fees, broader validation, persistent storage, more risk measures and additional automated tests.
33. **Is this financial advice?** No. It is an educational software project, not a recommendation or guarantee.
