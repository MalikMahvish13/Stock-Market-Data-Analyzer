"""Educational moving-average crossover backtesting helpers."""

from __future__ import annotations

from typing import Any

import pandas as pd

from .analyzer import calculate_metrics


def run_sma_backtest(data: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Simulate a long/flat SMA 20/50 strategy without look-ahead bias.

    A crossover signal is recorded on its observation date. The resulting
    position is shifted one row before applying daily returns, so a signal
    calculated at a close can only affect the next session. No trading costs
    are applied; that limitation is included in the returned summary.
    """
    result = data.copy()
    if "Daily Return" not in result or "SMA 20" not in result or "SMA 50" not in result:
        result = calculate_metrics(result)

    above = result["SMA 20"] > result["SMA 50"]
    prior_above = above.shift(1, fill_value=False)
    result["Signal"] = "HOLD"
    result.loc[above & ~prior_above, "Signal"] = "BUY"
    result.loc[~above & prior_above, "Signal"] = "SELL"

    # Position decided at previous close is applied to this session's return.
    result["Position"] = above.shift(1, fill_value=False).astype(int)
    result["Strategy Return"] = result["Daily Return"].fillna(0) * result["Position"]
    result["Buy And Hold Return"] = result["Daily Return"].fillna(0)
    result["Strategy Equity"] = (1 + result["Strategy Return"]).cumprod()
    result["Buy And Hold Equity"] = (1 + result["Buy And Hold Return"]).cumprod()

    summary = {
        "strategy": "SMA 20/50 crossover, long/flat",
        "strategy_return": float(result["Strategy Equity"].iloc[-1] - 1),
        "buy_and_hold_return": float(result["Buy And Hold Equity"].iloc[-1] - 1),
        "observations": int(len(result)),
        "buy_signals": int((result["Signal"] == "BUY").sum()),
        "sell_signals": int((result["Signal"] == "SELL").sum()),
        "transaction_costs": "Not included",
        "execution_assumption": "Signals calculated at a close affect the next session's return.",
        "note": "Educational historical simulation only. Past performance does not predict future results; not financial advice.",
    }
    return result, summary
