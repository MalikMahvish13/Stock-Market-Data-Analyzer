"""FastAPI endpoints for historical stock analysis and CSV upload."""

from __future__ import annotations

from datetime import date
from io import BytesIO
from typing import Any

import pandas as pd
from fastapi import FastAPI, File, HTTPException, Query, UploadFile

from .analyzer import (
    calculate_metrics,
    clean_data,
    load_data,
    summarize,
    validate_date_range,
    validate_ticker,
)
from .backtesting import run_sma_backtest


app = FastAPI(
    title="Stock Market Data Analyzer API",
    description="Educational historical-price analysis. Data is not guaranteed to be real time; not financial advice.",
    version="1.1.0",
)
MAX_CSV_BYTES = 5 * 1024 * 1024
_latest_summary: dict[str, Any] | None = None


def _remember_summary(summary: dict[str, Any]) -> dict[str, Any]:
    global _latest_summary
    _latest_summary = summary
    return summary


def _analyze_frame(prices: pd.DataFrame, ticker: str, source: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    analyzed = calculate_metrics(prices)
    return analyzed, _remember_summary(summarize(analyzed, ticker, source))


def _date_window(start: date, end: date) -> tuple[str, str]:
    try:
        return validate_date_range(start, end)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.get("/", tags=["Info"])
def root() -> dict[str, str]:
    return {
        "application": "Stock Market Data Analyzer",
        "description": "Historical stock analysis API for educational use.",
        "documentation": "/docs",
        "data_note": "Yahoo Finance data is historical and is not guaranteed real time.",
    }


@app.get("/health", tags=["Info"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/analyze/{ticker}", tags=["Analysis"])
def analyze(
    ticker: str,
    start: date = Query(default=date(2023, 1, 1)),
    end: date = Query(default=date(2024, 1, 1), description="Exclusive end date, following Yahoo Finance convention"),
) -> dict[str, Any]:
    try:
        ticker = validate_ticker(ticker)
        start_text, end_text = _date_window(start, end)
        prices, source = load_data(ticker, start_text, end_text)
        _analyzed, summary = _analyze_frame(prices, ticker, source)
        return summary
    except HTTPException:
        raise
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=f"Could not retrieve valid Yahoo Finance data for {ticker} in the requested date range.",
        ) from error


@app.post("/analyze/csv", tags=["Analysis"])
async def analyze_csv(
    file: UploadFile = File(..., description="CSV file with Date and Close columns"),
    ticker: str = Query(default="CSV_UPLOAD", min_length=1, max_length=30),
) -> dict[str, Any]:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=415, detail="Upload a file with a .csv extension.")
    content = await file.read(MAX_CSV_BYTES + 1)
    if len(content) > MAX_CSV_BYTES:
        raise HTTPException(status_code=413, detail="CSV upload exceeds the 5 MB limit.")
    try:
        ticker = validate_ticker(ticker)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    try:
        frame = pd.read_csv(BytesIO(content))
        prices = clean_data(frame)
        _analyzed, summary = _analyze_frame(prices, ticker, "CSV upload")
        return summary
    except (ValueError, pd.errors.EmptyDataError, pd.errors.ParserError) as error:
        raise HTTPException(status_code=422, detail=f"Invalid CSV: {error}") from error
    finally:
        await file.close()


@app.get("/latest", tags=["Analysis"])
def latest_summary() -> dict[str, Any]:
    if _latest_summary is None:
        raise HTTPException(status_code=404, detail="No analysis has been run in this API process yet.")
    return _latest_summary


@app.get("/backtest/{ticker}", tags=["Backtesting"])
def backtest(
    ticker: str,
    start: date = Query(default=date(2023, 1, 1)),
    end: date = Query(default=date(2024, 1, 1)),
) -> dict[str, Any]:
    try:
        ticker = validate_ticker(ticker)
        start_text, end_text = _date_window(start, end)
        prices, _source = load_data(ticker, start_text, end_text)
        analyzed = calculate_metrics(prices)
        _results, summary = run_sma_backtest(analyzed)
        return summary
    except HTTPException:
        raise
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"Could not retrieve valid Yahoo Finance data for {ticker}.") from error
