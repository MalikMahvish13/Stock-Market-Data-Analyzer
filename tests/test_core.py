"""Focused tests using the repository's clearly labelled sample CSV."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from src.stock_analyzer.analyzer import (
    calculate_metrics,
    generate_report_text,
    load_data,
    save_outputs,
    summarize,
    validate_date_range,
)
from src.stock_analyzer.backtesting import run_sma_backtest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_CSV = PROJECT_ROOT / "data" / "sample_prices.csv"


class AnalyzerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.prices, self.source = load_data("DEMO", "2024-01-01", "2024-02-01", str(SAMPLE_CSV))
        self.data = calculate_metrics(self.prices)

    def test_sample_load_and_indicators(self) -> None:
        self.assertEqual(len(self.data), 20)
        self.assertEqual(self.source, f"CSV: {SAMPLE_CSV}")
        self.assertTrue(self.data.index.is_monotonic_increasing)
        self.assertAlmostEqual(self.data["Daily Return"].iloc[1], self.data["Close"].iloc[1] / self.data["Close"].iloc[0] - 1)
        self.assertAlmostEqual(self.data["SMA 20"].iloc[-1], self.data["Close"].tail(20).mean())
        self.assertAlmostEqual(self.data["SMA 50"].iloc[-1], self.data["Close"].tail(50).mean())
        self.assertTrue(self.data["Volatility 20d"].notna().iloc[-1])

    def test_insufficient_history_is_handled(self) -> None:
        short = calculate_metrics(self.prices.iloc[:3])
        self.assertEqual(len(short), 3)
        self.assertTrue(short["SMA 20"].notna().all())
        self.assertTrue(short["SMA 50"].notna().all())
        self.assertTrue(short["Volatility 20d"].notna().iloc[-1])

    def test_missing_volume_is_supported(self) -> None:
        without_volume = calculate_metrics(self.prices.drop(columns=["Volume"]))
        with tempfile.TemporaryDirectory() as directory:
            summary = summarize(without_volume, "DEMO", "CSV test")
            save_outputs(without_volume, summary, directory)
            self.assertTrue((Path(directory) / "closing_price.png").is_file())
            self.assertFalse(summary["volume_available"])
            self.assertTrue((Path(directory) / "trading_volume.png").is_file())

    def test_report_and_outputs(self) -> None:
        summary = summarize(self.data, "DEMO", self.source)
        report = generate_report_text(summary)
        for item in ("DEMO", "CSV:", "SMA 20", "SMA 50", "Important observations", "not financial advice"):
            self.assertIn(item.lower(), report.lower())
        with tempfile.TemporaryDirectory() as directory:
            save_outputs(self.data, summary, directory)
            for name in ("analysis.csv", "summary.csv", "summary.txt", "closing_price.png", "moving_averages.png", "daily_returns.png", "daily_return_distribution.png", "trading_volume.png"):
                self.assertTrue((Path(directory) / name).is_file(), name)

    def test_backtest_uses_prior_session_position(self) -> None:
        result, summary = run_sma_backtest(self.data)
        expected_positions = (result["SMA 20"] > result["SMA 50"]).shift(1, fill_value=False).astype(int)
        pd.testing.assert_series_equal(result["Position"], expected_positions, check_names=False)
        self.assertAlmostEqual(summary["strategy_return"], result["Strategy Equity"].iloc[-1] - 1)
        self.assertIn("Not included", summary["transaction_costs"])

    def test_invalid_date_order_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "earlier"):
            validate_date_range("2024-02-01", "2024-01-01")
        with self.assertRaisesRegex(ValueError, "YYYY-MM-DD"):
            validate_date_range("not-a-date", "2024-02-01")

    def test_csv_missing_required_columns_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bad_csv = Path(directory) / "bad.csv"
            bad_csv.write_text("Timestamp,Price\n2024-01-01,10\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Close, Date"):
                load_data("CSV_UPLOAD", "2024-01-01", "2024-02-01", str(bad_csv))

    def test_invalid_ticker_is_rejected_before_download(self) -> None:
        with self.assertRaisesRegex(ValueError, "Ticker"):
            load_data("../private", "2024-01-01", "2024-02-01")

    def test_yahoo_failure_does_not_use_sample_fallback(self) -> None:
        with patch("yfinance.download", return_value=pd.DataFrame()):
            with self.assertRaisesRegex(RuntimeError, "DEMO.*returned no rows"):
                load_data("DEMO", "2024-01-01", "2024-02-01")


if __name__ == "__main__":
    unittest.main()
