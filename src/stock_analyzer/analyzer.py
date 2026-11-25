"""Data loading, cleaning, calculations, plots, and report creation."""

from __future__ import annotations

from datetime import date
import os
from pathlib import Path
import tempfile
from typing import Any

# Keep Matplotlib's cache writable in managed/student environments where the
# home directory may be read-only. Respect an explicitly configured cache.
os.environ.setdefault(
    "MPLCONFIGDIR",
    str(Path(tempfile.gettempdir()) / "stock_market_data_analyzer_mpl"),
)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


REQUIRED_COLUMNS = {"Date", "Close"}
OPTIONAL_NUMERIC_COLUMNS = ("Open", "High", "Low", "Volume")


def _standardize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy()
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    data.columns = [str(column).strip().title() for column in data.columns]
    if "Close" not in data and "Adj Close" in data:
        data = data.rename(columns={"Adj Close": "Close"})
    if "Date" not in data.columns:
        data = data.reset_index()
        data.columns = [str(column).strip().title() for column in data.columns]
    return data


def clean_data(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate and clean a price table without requiring a file or network."""
    if frame.empty:
        raise ValueError("The input contains no rows.")
    data = _standardize_columns(frame)
    missing = REQUIRED_COLUMNS - set(data.columns)
    if missing:
        raise ValueError(f"Input data must include columns: {', '.join(sorted(missing))}")
    data["Date"] = pd.to_datetime(data["Date"], errors="coerce", utc=True).dt.tz_convert(None)
    for column in ("Close", *OPTIONAL_NUMERIC_COLUMNS):
        if column in data.columns:
            data[column] = pd.to_numeric(data[column], errors="coerce")
    data = data.dropna(subset=["Date", "Close"])
    data = data[data["Close"] > 0].drop_duplicates(subset="Date", keep="last")
    data = data.sort_values("Date").set_index("Date")
    if data.empty:
        raise ValueError("No valid price rows remain after cleaning.")
    return data


def _clean(frame: pd.DataFrame) -> pd.DataFrame:
    """Backward-compatible alias for the original cleaning helper."""
    return clean_data(frame)


def validate_date_range(start: str | date, end: str | date) -> tuple[str, str]:
    """Return ISO date strings and require a non-empty, increasing interval."""
    try:
        first = start if isinstance(start, date) else date.fromisoformat(str(start))
        last = end if isinstance(end, date) else date.fromisoformat(str(end))
    except (TypeError, ValueError) as error:
        raise ValueError("Start and end must be valid dates in YYYY-MM-DD format.") from error
    if first >= last:
        raise ValueError("Start date must be earlier than end date.")
    return first.isoformat(), last.isoformat()


def validate_ticker(ticker: str) -> str:
    """Validate a provider ticker without allowing path or query syntax."""
    normalized = ticker.strip().upper()
    if not normalized or len(normalized) > 30 or not all(char.isalnum() or char in ".^=-_" for char in normalized):
        raise ValueError("Ticker must contain 1–30 letters, digits, dots, or standard ticker symbols.")
    return normalized


def load_data(ticker: str, start: str, end: str, csv_path: str | None = None) -> tuple[pd.DataFrame, str]:
    """Load an explicitly selected CSV or fetch the requested Yahoo Finance data."""
    if csv_path:
        path = Path(csv_path)
        try:
            return clean_data(pd.read_csv(path)), f"CSV: {path}"
        except FileNotFoundError as error:
            raise ValueError(f"CSV file not found: {path}") from error
        except pd.errors.EmptyDataError as error:
            raise ValueError(f"CSV file is empty: {path}") from error
        except pd.errors.ParserError as error:
            raise ValueError(f"CSV file could not be parsed: {error}") from error

    ticker = validate_ticker(ticker)
    start, end = validate_date_range(start, end)

    try:
        import yfinance as yf
    except ImportError as error:
        raise RuntimeError(
            "Yahoo Finance data requires yfinance. Install it with 'pip install yfinance', "
            "or provide a CSV with --csv."
        ) from error

    try:
        frame = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
        if frame is None or frame.empty:
            raise ValueError("Yahoo Finance returned no rows for this ticker and date range.")
        cleaned = clean_data(frame)
        return cleaned, f"Yahoo Finance ({ticker})"
    except Exception as error:
        raise RuntimeError(
            f"Could not load valid Yahoo Finance data for {ticker} from {start} to {end}: {error} "
            "Check the ticker and date range, or provide a CSV with --csv."
        ) from error


def calculate_metrics(data: pd.DataFrame) -> pd.DataFrame:
    result = data.copy()
    result["Daily Return"] = result["Close"].pct_change()
    result["SMA 20"] = result["Close"].rolling(20, min_periods=1).mean()
    result["SMA 50"] = result["Close"].rolling(50, min_periods=1).mean()
    result["Volatility 20d"] = result["Daily Return"].rolling(20, min_periods=2).std() * np.sqrt(252)
    return result


def backtest_sma(data: pd.DataFrame) -> dict[str, Any]:
    """Backward-compatible summary wrapper around the modular backtester."""
    from .backtesting import run_sma_backtest

    _results, summary = run_sma_backtest(data)
    return summary


def summarize(data: pd.DataFrame, ticker: str, source: str) -> dict[str, Any]:
    if data.empty:
        raise ValueError("Cannot summarize an empty price dataset.")
    close = data["Close"].dropna()
    returns = data["Daily Return"].dropna()
    first, last = float(close.iloc[0]), float(close.iloc[-1])
    change = last / first - 1 if first else float("nan")
    sma20, sma50 = data["SMA 20"].iloc[-1], data["SMA 50"].iloc[-1]
    if last > sma20 and sma20 > sma50:
        trend = "Upward: latest close is above both averages, and SMA 20 is above SMA 50"
    elif last < sma20 and sma20 < sma50:
        trend = "Downward: latest close is below both averages, and SMA 20 is below SMA 50"
    else:
        trend = "Mixed: price and moving averages do not show a consistent direction"
    volatility = float(returns.std() * np.sqrt(252)) if len(returns) > 1 else None
    rolling_volatility = data["Volatility 20d"].dropna() if "Volatility 20d" in data else pd.Series(dtype=float)
    volatility_20d = float(rolling_volatility.iloc[-1]) if not rolling_volatility.empty else None
    sma20_value = float(data["SMA 20"].iloc[-1])
    sma50_value = float(data["SMA 50"].iloc[-1])
    average_close = float(close.mean())
    observations = [
        f"Latest close is {('above' if last > sma20 else 'below' if last < sma20 else 'equal to')} the latest 20-session SMA.",
        f"Latest close is {('above' if last > sma50 else 'below' if last < sma50 else 'equal to')} the latest 50-session SMA.",
        f"Average close over the selected period was {average_close:.2f}.",
    ]
    volume = data["Volume"].dropna() if "Volume" in data.columns else pd.Series(dtype=float)
    volume_available = not volume.empty and bool((volume >= 0).all())
    if not volume_available:
        observations.append("No valid trading volume was available for this dataset.")
    return {
        "ticker": ticker.upper(), "source": source,
        "start": data.index.min().date().isoformat(), "end": data.index.max().date().isoformat(),
        "observations": int(len(data)), "first_close": first, "last_close": last,
        "period_return": change, "highest_close": float(close.max()),
        "highest_date": close.idxmax().date().isoformat(), "lowest_close": float(close.min()),
        "lowest_date": close.idxmin().date().isoformat(), "average_close": average_close,
        "sma_20": sma20_value, "sma_50": sma50_value,
        "annualized_volatility": volatility,
        "volatility_20d": volatility_20d,
        "best_day": float(returns.max()) if len(returns) else None,
        "worst_day": float(returns.min()) if len(returns) else None,
        "trend": trend, "volume_available": volume_available, "observations_notes": observations,
    }


def generate_report_text(summary: dict[str, Any]) -> str:
    """Build a plain-text report from values calculated from the selected data."""
    volatility = summary["annualized_volatility"]
    volatility_text = f"{volatility:.2%}" if volatility is not None else "Not available (need at least two daily returns)"
    best = summary["best_day"]
    worst = summary["worst_day"]
    best_worst = f"{best:.2%} / {worst:.2%}" if best is not None and worst is not None else "Not available"
    notes = summary.get("observations_notes", [])
    lines = [
        f"Stock Market Data Analyzer — {summary['ticker']}", "=" * 56,
        f"Data source: {summary['source']}",
        f"Analysis date range: {summary['start']} to {summary['end']}",
        f"Number of records: {summary['observations']}",
        f"First closing price: {summary['first_close']:.2f}",
        f"Latest closing price: {summary['last_close']:.2f}",
        f"Period return: {summary['period_return']:.2%}",
        f"Minimum closing price: {summary['lowest_close']:.2f} on {summary['lowest_date']}",
        f"Maximum closing price: {summary['highest_close']:.2f} on {summary['highest_date']}",
        f"Average closing price: {summary['average_close']:.2f}",
        f"Latest SMA 20: {summary['sma_20']:.2f}",
        f"Latest SMA 50: {summary['sma_50']:.2f}",
        f"Annualized historical volatility (full selected period): {volatility_text}",
        f"Latest 20-day annualized historical volatility: {summary['volatility_20d']:.2%}" if summary["volatility_20d"] is not None else "Latest 20-day annualized historical volatility: Not available (need at least two daily returns)",
        f"Trading volume data: {'available' if summary['volume_available'] else 'unavailable; the volume image is a labeled placeholder'}",
        f"Best / worst daily return: {best_worst}",
        f"Trend interpretation: {summary['trend']}",
        "", "Important observations:",
        *(f"- {note}" for note in notes),
        "", "Educational disclaimer:",
        "Historical data and indicators are for learning only. This report is not financial advice.",
        "Past performance does not predict future results.",
    ]
    return "\n".join(lines) + "\n"


def save_outputs(data: pd.DataFrame, summary: dict[str, Any], output_dir: str = "outputs") -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    data.to_csv(out / "analysis.csv", index_label="Date", float_format="%.6f")

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(data.index, data["Close"], label="Closing price", linewidth=1.8, color="#1769aa")
    ax.set(title=f"{summary['ticker']} Historical Closing Price", xlabel="Date", ylabel="Price (data currency)")
    ax.grid(alpha=0.25); ax.legend(); fig.autofmt_xdate(); fig.tight_layout(); fig.savefig(out / "closing_price.png", dpi=160); plt.close(fig)

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(data.index, data["Close"], label="Closing price", alpha=0.75, linewidth=1.5)
    ax.plot(data.index, data["SMA 20"], label="SMA 20", linewidth=1.7)
    ax.plot(data.index, data["SMA 50"], label="SMA 50", linewidth=1.7)
    ax.set(title=f"{summary['ticker']} Closing Price and Moving Averages", xlabel="Date", ylabel="Price (data currency)")
    ax.grid(alpha=0.25); ax.legend(); fig.autofmt_xdate(); fig.tight_layout(); fig.savefig(out / "moving_averages.png", dpi=160); plt.close(fig)

    returns = data["Daily Return"].dropna() * 100
    fig, ax = plt.subplots(figsize=(11, 4.5))
    if not returns.empty:
        ax.plot(returns.index, returns, color="#7b3294", linewidth=1.2, label="Daily return")
        ax.axhline(0, color="black", linewidth=0.8, alpha=0.7)
    ax.set(title=f"{summary['ticker']} Daily Returns", xlabel="Date", ylabel="Daily return (%)")
    ax.grid(alpha=0.25)
    if not returns.empty:
        ax.legend(loc="best")
    fig.autofmt_xdate(); fig.tight_layout(); fig.savefig(out / "daily_returns.png", dpi=160); plt.close(fig)

    # Keep the earlier distribution chart as well as the requested time-series view.
    fig, ax = plt.subplots(figsize=(9, 4.5))
    if not returns.empty:
        ax.hist(returns, bins=min(30, max(5, len(returns))), color="#3977a8", edgecolor="white")
    ax.set(title=f"{summary['ticker']} Daily Return Distribution", xlabel="Daily return (%)", ylabel="Trading days")
    ax.grid(axis="y", alpha=0.25); fig.tight_layout(); fig.savefig(out / "daily_return_distribution.png", dpi=160); plt.close(fig)

    volume = data["Volume"].dropna() if "Volume" in data.columns else pd.Series(dtype=float)
    if summary["volume_available"]:
        fig, ax = plt.subplots(figsize=(11, 4.5))
        ax.bar(volume.index, volume, width=1.0, color="#4c956c", label="Volume")
        ax.set(title=f"{summary['ticker']} Trading Volume", xlabel="Date", ylabel="Shares traded")
        ax.grid(axis="y", alpha=0.25); ax.legend(); fig.autofmt_xdate(); fig.tight_layout(); fig.savefig(out / "trading_volume.png", dpi=160); plt.close(fig)
    else:
        # Overwrite any prior run's volume chart so it cannot be mistaken for
        # current data when this dataset has no usable volume observations.
        fig, ax = plt.subplots(figsize=(11, 4.5))
        ax.text(0.5, 0.5, "No valid trading volume available\nfor this dataset", ha="center", va="center", fontsize=14)
        ax.set_title(f"{summary['ticker']} Trading Volume")
        ax.set_axis_off(); fig.tight_layout(); fig.savefig(out / "trading_volume.png", dpi=160); plt.close(fig)

    (out / "summary.txt").write_text(generate_report_text(summary), encoding="utf-8")
    pd.DataFrame([summary]).to_csv(out / "summary.csv", index=False)


def print_summary(summary: dict[str, Any]) -> None:
    print(f"\n{summary['ticker']} analysis ({summary['source']})")
    print(f"Period: {summary['start']} to {summary['end']} | rows: {summary['observations']}")
    print(f"Close: {summary['first_close']:.2f} -> {summary['last_close']:.2f} ({summary['period_return']:.2%})")
    print(f"Average close: {summary['average_close']:.2f} | SMA 20: {summary['sma_20']:.2f} | SMA 50: {summary['sma_50']:.2f}")
    print(f"High: {summary['highest_close']:.2f} on {summary['highest_date']} | Low: {summary['lowest_close']:.2f} on {summary['lowest_date']}")
    volatility = summary["annualized_volatility"]
    print(f"Annualized historical volatility: {volatility:.2%}" if volatility is not None else "Annualized historical volatility: unavailable")
    print(f"Trend reading: {summary['trend']}")
