"""Interactive Streamlit dashboard for the Stock Market Data Analyzer."""

from __future__ import annotations

from datetime import date, timedelta
from io import BytesIO

import pandas as pd
import streamlit as st

from src.stock_analyzer.analyzer import (
    calculate_metrics,
    clean_data,
    generate_report_text,
    load_data,
    save_outputs,
    summarize,
    validate_date_range,
)
from src.stock_analyzer.backtesting import run_sma_backtest


st.set_page_config(page_title="Stock Market Data Analyzer", page_icon="📈", layout="wide")
st.markdown(
    """
    <style>
      :root {
        color-scheme: dark;
        --app-bg: #0b1220;
        --panel-bg: #142033;
        --card-bg: #1b2a41;
        --border-color: #3a4a61;
        --text-primary: #f8fafc;
        --text-secondary: #cbd5e1;
        --text-muted: #a8b6c9;
        --accent: #60a5fa;
      }
      .block-container {padding-top: 1.6rem; padding-bottom: 2rem; max-width: 1450px;}
      [data-testid="stAppViewContainer"], .stApp {background-color: var(--app-bg); color: var(--text-primary);}
      [data-testid="stHeader"] {background-color: var(--app-bg);}
      section[data-testid="stSidebar"] {background-color: #101a2b; border-right: 1px solid var(--border-color);}
      h1, h2, h3, h4, p, label, li, [data-testid="stMarkdownContainer"] {color: var(--text-primary);}
      h1, h2, h3 {font-weight: 650;}
      [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {color: var(--text-muted);}

      div[data-testid="stMetric"] {
        background-color: var(--card-bg);
        border: 1px solid var(--border-color);
        padding: 0.9rem 1rem;
        border-radius: 0.75rem;
        min-height: 6rem;
      }
      div[data-testid="stMetricLabel"], div[data-testid="stMetricLabel"] p {color: var(--text-secondary); font-weight: 600;}
      div[data-testid="stMetricValue"] {color: #ffffff; font-size: 2rem; font-weight: 750;}
      div[data-testid="stMetricDelta"] {color: #86efac;}

      [data-baseweb="input"] > div, [data-baseweb="select"] > div {
        background-color: var(--panel-bg);
        border-color: var(--border-color);
      }
      [data-baseweb="input"] input, [data-baseweb="select"] *,
      [data-testid="stRadio"] label, [data-testid="stCheckbox"] label {color: var(--text-primary);}
      [data-testid="stFileUploaderDropzone"] {background-color: var(--panel-bg); border-color: var(--border-color);}

      .stButton > button, .stDownloadButton > button {
        background-color: #1d4ed8;
        color: #ffffff;
        border: 1px solid #60a5fa;
        font-weight: 650;
      }
      .stButton > button:hover, .stDownloadButton > button:hover {background-color: #2563eb; color: #ffffff; border-color: #93c5fd;}
      .stButton > button:focus, .stDownloadButton > button:focus {outline: 2px solid #bfdbfe; outline-offset: 2px;}

      [data-testid="stAlert"] {background-color: var(--panel-bg); border: 1px solid var(--border-color); color: var(--text-primary);}
      [data-testid="stAlert"] p {color: var(--text-primary);}
      [data-testid="stDataFrame"], [data-testid="stTable"] {border: 1px solid var(--border-color); border-radius: 0.5rem;}
      a {color: var(--accent);}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Stock Market Data Analyzer")
st.caption("Explore historical prices, technical indicators and an educational backtest. Historical analysis only; not financial advice.")

with st.sidebar:
    st.header("Analysis settings")
    page = st.radio("Navigate", ["Analysis", "Backtesting", "About"])
    source_choice = st.radio("Data source", ["Yahoo Finance", "CSV upload"])
    if source_choice == "Yahoo Finance":
        ticker = st.text_input("Ticker", "RELIANCE.NS", key="ticker_yahoo").strip().upper()
    else:
        ticker = st.text_input("Dataset label", "CSV_UPLOAD", key="ticker_csv").strip().upper()
    start_date = st.date_input("Start date", value=date(2024, 1, 1))
    end_date = st.date_input("End date", value=date.today())
    uploaded_file = st.file_uploader("Price CSV", type=["csv"]) if source_choice == "CSV upload" else None
    run_analysis = st.button("Analyze Stock", type="primary", use_container_width=True)

if run_analysis:
    st.session_state["analysis_error"] = None
    try:
        validate_date_range(start_date, end_date)
        with st.spinner("Loading and analyzing historical prices…"):
            if source_choice == "Yahoo Finance":
                # The UI date range is inclusive; yfinance's end parameter is exclusive.
                prices, source = load_data(ticker, start_date.isoformat(), (end_date + timedelta(days=1)).isoformat())
            else:
                if uploaded_file is None:
                    raise ValueError("Choose a CSV file before starting the analysis.")
                frame = pd.read_csv(BytesIO(uploaded_file.getvalue()))
                prices = clean_data(frame)
                prices = prices.loc[(prices.index.date >= start_date) & (prices.index.date <= end_date)]
                if prices.empty:
                    raise ValueError("The CSV has no valid observations inside the selected date range.")
                source = "CSV upload"

            analyzed = calculate_metrics(prices)
            summary = summarize(analyzed, ticker or "CSV_UPLOAD", source)
            backtest_data, backtest_summary = run_sma_backtest(analyzed)
            save_outputs(analyzed, summary)
            st.session_state["analysis_data"] = analyzed
            st.session_state["analysis_summary"] = summary
            st.session_state["backtest_data"] = backtest_data
            st.session_state["backtest_summary"] = backtest_summary
            st.session_state["csv_bytes"] = analyzed.to_csv(index_label="Date", float_format="%.6f").encode("utf-8")
            st.session_state["report_text"] = generate_report_text(summary)
    except Exception as error:
        st.session_state["analysis_error"] = str(error)
        st.error(f"Analysis could not be completed: {error}")

summary = st.session_state.get("analysis_summary")
data = st.session_state.get("analysis_data")

if summary is not None and data is not None and st.session_state.get("analysis_error") and page != "About":
    st.warning(
        f"The latest analysis attempt failed. Showing the previous successful result for "
        f"{summary['ticker']} ({summary['source']}, {summary['start']} to {summary['end']})."
    )

if page == "About":
    st.subheader("About this project")
    st.write("A student-built Python application for inspecting historical stock prices, returns, moving averages, volatility and a simple crossover simulation.")
    st.info("Yahoo Finance provides historical downloads here; this application does not guarantee real-time data. Indicators are educational descriptions, not guaranteed signals or financial advice.")
elif summary is None or data is None:
    st.info("Choose a data source and date range in the sidebar, then select **Analyze Stock** to begin.")
elif page == "Analysis":
    st.subheader(f"{summary['ticker']} overview")
    st.caption(f"Source: {summary['source']} · {summary['start']} to {summary['end']} · {summary['observations']} records")
    first, second, third, fourth = st.columns(4)
    first.metric("Latest close", f"{summary['last_close']:.2f}")
    second.metric("Period return", f"{summary['period_return']:.2%}")
    vol = summary["annualized_volatility"]
    rolling_vol = summary["volatility_20d"]
    third.metric("Latest 20-day volatility", f"{rolling_vol:.2%}" if rolling_vol is not None else "N/A")
    fourth.metric("Average close", f"{summary['average_close']:.2f}")

    st.markdown("### Historical closing price")
    st.line_chart(data[["Close"]].rename(columns={"Close": "Closing price"}), width="stretch")
    st.markdown("### Moving averages")
    st.line_chart(data[["Close", "SMA 20", "SMA 50"]], width="stretch")
    st.markdown("### Daily returns")
    st.line_chart((data[["Daily Return"]] * 100).rename(columns={"Daily Return": "Daily return (%)"}), width="stretch")
    if "Volume" in data.columns and data["Volume"].notna().any():
        st.markdown("### Trading volume")
        st.bar_chart(data[["Volume"]].dropna(), width="stretch")
    else:
        st.info("No valid volume data was supplied, so the volume chart is unavailable.")
    st.markdown("### Risk and trend reading")
    st.write(summary["trend"])
    st.caption(f"Full-period annualized historical volatility: {vol:.2%}" if vol is not None else "Full-period volatility is unavailable for this short history.")
    if vol is not None:
        st.write(f"Latest 20-session annualized volatility: {data['Volatility 20d'].dropna().iloc[-1]:.2%}" if data["Volatility 20d"].notna().any() else "Rolling volatility is not available yet.")
    st.dataframe(data.tail(20), width="stretch")
    download_a, download_b = st.columns(2)
    download_a.download_button("Download analysis CSV", st.session_state["csv_bytes"], f"{summary['ticker']}_analysis.csv", "text/csv")
    download_b.download_button("Download analysis report", st.session_state["report_text"], f"{summary['ticker']}_report.txt", "text/plain")
elif page == "Backtesting":
    st.subheader("SMA 20/50 crossover backtest")
    backtest_summary = st.session_state.get("backtest_summary")
    backtest_data = st.session_state.get("backtest_data")
    if backtest_summary is not None and backtest_data is not None:
        left, right = st.columns(2)
        left.metric("Strategy total return", f"{backtest_summary['strategy_return']:.2%}")
        right.metric("Buy-and-hold total return", f"{backtest_summary['buy_and_hold_return']:.2%}")
        st.write(f"Signals: {backtest_summary['buy_signals']} buy · {backtest_summary['sell_signals']} sell")
        st.line_chart(backtest_data[["Strategy Equity", "Buy And Hold Equity"]], width="stretch")
        st.dataframe(backtest_data[["Close", "SMA 20", "SMA 50", "Signal", "Position", "Strategy Return"]].tail(30), width="stretch")
        st.warning("Illustrative historical simulation. Signals are applied to the next session to avoid look-ahead bias. No transaction costs are included. Past performance does not predict future results; this is not financial advice.")
    else:
        st.info("Run an analysis first to view its backtest.")
