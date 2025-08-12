
from typing import List, Dict

def _near_support(rel_levels, price_pos=0.5):
    # price_pos unknown from image; assume mid-upper region ~0.6 for trending up context
    if not rel_levels:
        return False
    return any(abs(l - price_pos) < 0.08 for l in rel_levels)

def _near_resistance(rel_levels, price_pos=0.5):
    if not rel_levels:
        return False
    return any(abs(l - price_pos) < 0.08 for l in rel_levels)

def suggest_strategies(ticker: str, slope: float, sr_levels: List[float], price: float, atr: float, dte: int) -> List[Dict]:
    """Map features to simple paper options ideas. Uses delta-like OTM % heuristics."""
    ideas = []
    # Rough OTM sizing
    otm_pct = 0.02 if atr and atr>0 else 0.01
    price_pos = 0.6 if slope>0 else (0.4 if slope<0 else 0.5)
    near_sup = _near_support(sr_levels, price_pos)
    near_res = _near_resistance(sr_levels, price_pos)

    # Uptrend cases
    if slope > 0.25 and near_sup:
        strike_short = round(price * (1 - 2*otm_pct), 2)
        strike_long  = round(price * (1 - 4*otm_pct), 2)
        ideas.append({
            "Ticker": ticker,
            "Setup": "Uptrend pullback near support",
            "Strategy": "Bull Put Spread",
            "Expiration(DTE)": dte,
            "Strikes": f"Sell {strike_short}, Buy {strike_long}",
            "Rationale": "Uptrend + near support → positive skew; defined risk income play."
        })
    if slope > 0.25:
        strike_buy = round(price * (1.00), 2)
        strike_sell = round(price * (1 + 2*otm_pct), 2)
        ideas.append({
            "Ticker": ticker,
            "Setup": "Uptrend / potential breakout",
            "Strategy": "Call Debit Spread",
            "Expiration(DTE)": dte,
            "Strikes": f"Buy {strike_buy}, Sell {strike_sell}",
            "Rationale": "Directional long with limited theta; benefits from follow-through."
        })

    # Range/neutral
    if -0.15 <= slope <= 0.15:
        lower = round(price * (1 - 3*otm_pct), 2)
        upper = round(price * (1 + 3*otm_pct), 2)
        ideas.append({
            "Ticker": ticker,
            "Setup": "Range / mean-revert",
            "Strategy": "Iron Condor",
            "Expiration(DTE)": dte,
            "Strikes": f"Short ~{lower}-{upper} (approx)",
            "Rationale": "Sideways behavior; harvest premium in range with defined risk."
        })

    # Downtrend
    if slope < -0.25 and near_res:
        strike_short = round(price * (1 + 2*otm_pct), 2)
        strike_long  = round(price * (1 + 4*otm_pct), 2)
        ideas.append({
            "Ticker": ticker,
            "Setup": "Downtrend rejection at resistance",
            "Strategy": "Bear Call Spread",
            "Expiration(DTE)": dte,
            "Strikes": f"Sell {strike_short}, Buy {strike_long}",
            "Rationale": "Trend down + resistance rejection; defined risk bearish income."
        })

    # Fallback
    if not ideas:
        strike_buy = round(price, 2)
        strike_sell = round(price * (1 + 2*otm_pct), 2)
        ideas.append({
            "Ticker": ticker,
            "Setup": "Unclear / noisy",
            "Strategy": "Call Debit Spread (conservative)",
            "Expiration(DTE)": dte,
            "Strikes": f"Buy {strike_buy}, Sell {strike_sell}",
            "Rationale": "Image signals ambiguous; choose defined-risk directional idea."
        })

    return ideas
