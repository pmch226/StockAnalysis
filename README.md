
# Chart → Paper Options Ideas (Image MVP)

**Purpose:** Upload a candlestick chart image (e.g., Robinhood style) and get heuristic, **paper-only** options ideas (spreads) for short-term expirations. This MVP reads image features (trend, rough S/R) and maps them to simple strategies. Optionally, upload OHLCV CSV to infer ATR and compute naive backtest metrics.

⚠️ **Disclaimer:** Educational / paper trading only. Not financial advice. Vision heuristics are noisy; confirm with real data if you extend this.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL shown in the terminal.

## Inputs
- **Chart image** (PNG/JPG/WebP) — candlestick style works best.
- **Ticker** (default QQQ)
- **Timeframe** (Daily/Weekly/Monthly/3-Month)
- **Current price** — used to size strikes (if missing, and CSV uploaded, we use last close).
- **ATR estimate** (optional) — used to scale OTM %; if missing and CSV uploaded, we infer ATR(20).
- **Optional OHLCV CSV** — columns: `Date,Open,High,Low,Close,Volume`

## Output
- Detected **trend slope** and **support/resistance levels** (relative).
- 1–3 **paper options ideas** (e.g., bull put spread, call debit spread, iron condor), with strikes sized by % of price.
- If CSV provided, a **naive** backtest % P/L proxy.

## Extend to V1
- Replace heuristics with a small ViT/CNN classifier trained on synthetic + real chart tiles.
- Add options chain & IV via an API; simulate realistic spread P/L paths.
- Better S/R detection; parse axis numbers when available.
- Persist runs (SQLite/Postgres).

## File layout
```
app.py
vision/
  preprocess.py
strategies/
  rules.py
utils/
  backtest.py
requirements.txt
README.md
```
