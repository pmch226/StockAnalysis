
import pandas as pd
import numpy as np
from typing import List, Dict

def simple_backtest_metrics(ohlcv: pd.DataFrame, ideas: List[Dict], dte_days: int = 14) -> List[Dict]:
    """Naive backtest: for each idea, simulate holding until DTE using underlying P/L approx.
    No IV/greeks; assume options spread P/L mirrors % move bounded by strikes."""
    if len(ohlcv) < dte_days + 1:
        return ideas

    close = ohlcv["Close"].values
    last = close[-1]
    future_idx = -1 + min(dte_days, len(close)-1)
    future = close[future_idx]

    pct_change = (future - last) / last

    out = []
    for idea in ideas:
        strat = idea["Strategy"]
        # Crude mapping to P/L in % of width
        if strat in ("Bull Put Spread", "Bear Call Spread", "Iron Condor"):
            # premium strategy: profit if move small / in favorable direction
            pnl = (0.02 - abs(pct_change))  # cap at ~2%
        elif strat in ("Call Debit Spread",):
            pnl = max(0.0, pct_change)  # benefit only up moves (naive)
        else:
            pnl = pct_change * 0.5

        idea2 = dict(idea)
        idea2["Naive_PnL_%"] = round(100*pnl, 2)
        idea2["Underlying_%Move@DTE"] = round(100*pct_change, 2)
        out.append(idea2)
    return out
