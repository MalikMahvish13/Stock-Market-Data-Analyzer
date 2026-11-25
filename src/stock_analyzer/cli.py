"""Command-line interface."""

import argparse

from .analyzer import calculate_metrics, load_data, print_summary, save_outputs, summarize


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze historical stock prices and save charts and a report.")
    parser.add_argument("--ticker", default="AAPL", help="Yahoo Finance ticker, e.g. AAPL or MSFT")
    parser.add_argument("--start", default="2023-01-01", help="Start date, YYYY-MM-DD")
    parser.add_argument("--end", default="2024-01-01", help="End date (exclusive for Yahoo Finance), YYYY-MM-DD")
    parser.add_argument("--csv", help="Use a CSV with Date and Close columns instead of downloading")
    parser.add_argument("--output-dir", default="outputs", help="Where to save CSV, report, and charts")
    args = parser.parse_args()

    prices, source = load_data(args.ticker, args.start, args.end, args.csv)
    analyzed = calculate_metrics(prices)
    summary = summarize(analyzed, args.ticker, source)
    save_outputs(analyzed, summary, args.output_dir)
    print_summary(summary)
    print(f"\nSaved analysis files in: {args.output_dir}/")
