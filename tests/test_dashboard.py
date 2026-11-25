"""Streamlit UI flow tests using only the repository's labelled sample CSV."""

from datetime import date
from pathlib import Path
import unittest

from streamlit.testing.v1 import AppTest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_CSV = PROJECT_ROOT / "data" / "sample_prices.csv"


class DashboardTests(unittest.TestCase):
    def _load_sample_analysis(self) -> AppTest:
        app = AppTest.from_file(str(PROJECT_ROOT / "dashboard.py"), default_timeout=30).run()
        self.assertEqual(len(app.exception), 0)
        app.radio[1].set_value("CSV upload")
        app.run()
        app.text_input[0].set_value("DEMO")
        app.date_input[0].set_value(date(2024, 1, 1))
        app.date_input[1].set_value(date(2024, 1, 30))
        app.file_uploader[0].set_value(("sample_prices.csv", SAMPLE_CSV.read_bytes(), "text/csv"))
        app.run()
        app.button[0].click()
        app.run()
        return app

    def test_source_switch_uses_source_specific_label(self) -> None:
        app = AppTest.from_file(str(PROJECT_ROOT / "dashboard.py"), default_timeout=30).run()
        self.assertEqual(app.text_input[0].label, "Ticker")
        self.assertEqual(app.text_input[0].value, "RELIANCE.NS")
        app.radio[1].set_value("CSV upload")
        app.run()
        self.assertEqual(app.text_input[0].label, "Dataset label")
        self.assertEqual(app.text_input[0].value, "CSV_UPLOAD")

    def test_csv_analysis_navigation_and_downloads(self) -> None:
        app = self._load_sample_analysis()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual([metric.label for metric in app.metric], [
            "Latest close", "Period return", "Latest 20-day volatility", "Average close"
        ])
        self.assertEqual([button.label for button in app.get("download_button")], [
            "Download analysis CSV", "Download analysis report"
        ])
        self.assertIn(b"Daily Return", app.session_state["csv_bytes"])
        self.assertIn("not financial advice", app.session_state["report_text"].lower())

        app.radio[0].set_value("Backtesting")
        app.run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual([metric.label for metric in app.metric], [
            "Strategy total return", "Buy-and-hold total return"
        ])
        self.assertTrue(any("Past performance" in warning.value for warning in app.warning))

        app.radio[0].set_value("About")
        app.run()
        self.assertEqual(len(app.exception), 0)

    def test_upload_validation_message(self) -> None:
        app = AppTest.from_file(str(PROJECT_ROOT / "dashboard.py"), default_timeout=30).run()
        app.radio[1].set_value("CSV upload")
        app.run()
        app.file_uploader[0].set_value(("bad.csv", b"Timestamp,Price\n2024-01-01,10\n", "text/csv"))
        app.run()
        app.button[0].click()
        app.run()
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(any("Date" in error.value and "Close" in error.value for error in app.error))

    def test_failed_request_identifies_previous_result(self) -> None:
        app = self._load_sample_analysis()
        app.radio[1].set_value("Yahoo Finance")
        app.run()
        app.text_input[0].set_value("../invalid")
        app.run()
        app.button[0].click()
        app.run()
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(app.error)
        self.assertTrue(any("previous successful result" in warning.value for warning in app.warning))
        self.assertEqual(app.session_state["analysis_summary"]["ticker"], "DEMO")


if __name__ == "__main__":
    unittest.main()
