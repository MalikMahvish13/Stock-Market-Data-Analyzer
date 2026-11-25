# Testing report

## Environment

- Python 3.14 from the existing project `.venv`.
- Core dependencies: pandas, NumPy, Matplotlib, yfinance, FastAPI and Uvicorn.
- Streamlit and `python-multipart` were missing initially and were installed into the existing `.venv` because the requested dashboard and CSV upload endpoint require them. Exact command:

```bash
"$PWD/.venv/bin/python" -m pip install 'streamlit>=1.30' 'python-multipart>=0.0.9'
```

## Automated tests

Command:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Result: **13 tests passed** (9 analyzer/backtest tests and 4 Streamlit AppTest flows). Coverage includes sample loading, returns/SMA/volatility calculations, short histories, CSV required-column errors, date/ticker validation, no silent sample fallback after Yahoo failure, optional volume, report and chart artifacts, prior-session backtest position timing, dashboard source-specific ticker/dataset labels, CSV upload/navigation/download payloads, upload errors, and clear handling of a failed run after a prior success.

## CLI runs

Sample CSV, offline:

```bash
.venv/bin/python main.py --ticker DEMO --csv data/sample_prices.csv
```

Result: **exit 0**, 20 sample rows, close 101.00 → 115.00, period return 13.86%, average close 106.80, annualized volatility 22.00%.

Yahoo Finance historical data:

```bash
.venv/bin/python main.py --ticker RELIANCE.NS --start 2025-01-01 --end 2025-11-26
```

Result: **exit 0**, source labeled Yahoo Finance, 224 observations from 2025-01-01 through 2025-11-25. Yahoo's end parameter is exclusive. The displayed close moved from 1210.79 to 1532.61 in the selected data; period return was 26.58%, average close 1357.48, full-period annualized historical volatility 20.16%, and latest SMA values 1500.55 / 1435.58.

An independent check of `outputs/analysis.csv` confirmed valid ascending dates, positive non-missing closes, valid nonnegative volume, and matches for daily returns (at exported six-decimal precision), SMA 20, SMA 50 and rolling 20-session volatility. The first daily return is blank; the first two rolling volatility entries are blank because there are not yet two returns. The report contains the Yahoo source, ticker and actual returned dates.

## API integration checks

The API was launched locally on `127.0.0.1:8765`; Swagger UI was opened through `/docs`. Results:

| Check | Result |
|---|---|
| `GET /` | HTTP 200 |
| `GET /health` | HTTP 200 |
| `GET /docs` | HTTP 200 |
| `GET /analyze/RELIANCE.NS` with selected dates | HTTP 200; Yahoo Finance source, 224 rows |
| `POST /analyze/csv` with sample CSV | HTTP 200; 20 sample rows |
| `GET /latest` after analysis | HTTP 200; most recent summary returned |
| `GET /backtest/RELIANCE.NS` | HTTP 200; strategy 15.97%, buy-and-hold 26.58%, 4 buys / 3 sells |
| Invalid date order | HTTP 422 with validation message |
| CSV missing `Date` / `Close` | HTTP 422 with required-column message |
| Well-formed but unknown ticker | HTTP 502; no sample data substituted |

The backtest result is a historical educational simulation; no trading costs are included and it is not a recommendation.

## Dashboard checks

- Streamlit server started on `127.0.0.1:8766`; page returned HTTP 200.
- Streamlit `AppTest` selected CSV upload, uploaded the sample CSV, clicked **Analyze Stock**, and displayed metrics without app exceptions.
- Analysis, Backtesting and About views rendered without app exceptions.
- The analysis view exposed both download buttons; generated CSV payload was 2,113 bytes and report payload was 1,052 bytes for the sample run.
- The backtest view displayed strategy and benchmark returns plus the educational disclaimer.
- A Streamlit AppTest used `RELIANCE.NS` with the 2025-01-01 through 2025-11-25 date selection. Yahoo Finance returned 224 rows, and the dashboard showed the expected source/date caption, 26.58% period return, 13.26% latest rolling volatility, volume chart, and report/download controls without app exceptions. Its backtest page showed strategy and benchmark results without app exceptions.
- Switching from Yahoo Finance to CSV selects a separate `CSV_UPLOAD` dataset label by default, avoiding accidental reuse of a Yahoo ticker for sample data.
- A failed analysis after a successful one displays a warning identifying the ticker/source/date range of the older results, preventing them from appearing to belong to the failed request.
- The missing-volume test confirmed analysis still completes and the saved volume image is an explicitly labeled unavailable-data placeholder.

AppTest verifies widget state and download payload creation, not the browser's final save dialog or layout at different screen sizes. Those are still useful manual presentation checks.

## Generated output files

The current CLI run writes:

- `outputs/analysis.csv`
- `outputs/summary.csv`
- `outputs/summary.txt`
- `outputs/closing_price.png`
- `outputs/moving_averages.png`
- `outputs/daily_returns.png`
- `outputs/daily_return_distribution.png`
- `outputs/trading_volume.png` (volume chart when valid volume exists; otherwise an unavailable-data placeholder)

The PNG outputs were verified as present after the CLI run. The output directory is ignored by Git by default; selectively include artifacts if needed for a demonstration.

## Warnings and limitations

- The first network request from the restricted shell could not resolve Yahoo Finance DNS. The authorized network retry succeeded; no source fallback was used.
- Streamlit `AppTest` emits a `missing ScriptRunContext` warning because it executes in bare test mode; the dashboard produced no app exceptions. Streamlit also prints a non-blocking suggestion to install Watchdog for faster file watching. Watchdog was not installed because it is optional and not needed for functionality.
- Matplotlib's default home cache was not writable in this environment. The analyzer now uses a temporary writable cache directory unless `MPLCONFIGDIR` is explicitly set.
- Yahoo Finance availability and historical adjustments can change. These are historical downloads, not guaranteed real-time prices.
- This project has no persistent database, authentication, multi-user portfolio/watchlist support, alert delivery, or Next.js frontend.
- The sample fixture is synthetic and should be called sample/demo data, not real market data.
