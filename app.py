
import streamlit as st
from PIL import Image
import numpy as np
import pandas as pd
import io

from vision.preprocess import extract_price_panel, estimate_trend_slope, detect_sr_levels
from strategies.rules import suggest_strategies
from utils.backtest import simple_backtest_metrics

st.set_page_config(page_title="Chart → Paper Options Ideas (MVP)", layout="wide")

st.title("📈 Chart → Paper Options Ideas (Image-Only MVP)")
st.caption("Educational / paper trading only. Upload a candlestick chart image (e.g., Robinhood style).")

with st.sidebar:
    st.header("Inputs")
    ticker = st.text_input("Ticker", value="QQQ")
    timeframe = st.selectbox("Timeframe", ["Daily", "Weekly", "Monthly", "3-Month"])
    cur_price = st.number_input("Current underlying price (manual)", min_value=0.0, value=0.0, help="Provide latest price to size strikes/OTM %.")
    atr_hint = st.number_input("ATR estimate (optional)", min_value=0.0, value=0.0, help="If unknown, leave 0; we can estimate from uploaded CSV.")
    dte = st.slider("Days to expiry (paper)", 7, 30, 14)
    csv_file = st.file_uploader("Optional: Upload OHLCV CSV for backtest (columns: Date,Open,High,Low,Close,Volume)", type=["csv"])

uploaded = st.file_uploader("Upload chart image (PNG/JPG/WebP)", type=["png", "jpg", "jpeg", "webp"])

col1, col2 = st.columns([1,1])

if uploaded is not None:
    image = Image.open(uploaded).convert("RGB")
    col1.image(image, caption="Uploaded chart", use_container_width=True)

    # --- Vision extraction ---
    price_img = extract_price_panel(image)
    slope = estimate_trend_slope(price_img)
    sr_levels = detect_sr_levels(price_img, top_k=4)

    with col1.expander("Detected features", expanded=True):
        st.write(f"Trend slope (pixels per 100px width): **{slope:.2f}** (+: up, -: down)")
        st.write(f"Support/Resistance (relative rows): {sr_levels}")

    # --- Price & ATR from CSV if available ---
    ohlcv = None
    if csv_file is not None:
        try:
            df = pd.read_csv(csv_file)
            # Normalize columns
            cols = {c.lower(): c for c in df.columns}
            for want in ["date","open","high","low","close","volume"]:
                if want not in cols and want.capitalize() in df.columns:
                    cols[want] = want.capitalize()
            if all(k in cols for k in ["date","open","high","low","close"]):
                ohlcv = df.rename(columns={
                    cols["date"]:"Date",
                    cols["open"]:"Open",
                    cols["high"]:"High",
                    cols["low"]:"Low",
                    cols["close"]:"Close",
                    cols.get("volume", cols.get("Volume","Close")):"Volume"
                })
                ohlcv["Date"] = pd.to_datetime(ohlcv["Date"])
                ohlcv = ohlcv.sort_values("Date").reset_index(drop=True)
        except Exception as e:
            st.warning(f"CSV parse error: {e}")

    # Try to infer ATR if not provided and CSV exists
    inferred_atr = None
    if (atr_hint == 0.0 or np.isnan(atr_hint)) and ohlcv is not None and len(ohlcv) >= 20:
        high = ohlcv["High"].values
        low = ohlcv["Low"].values
        close = ohlcv["Close"].values
        prev_close = np.concatenate([[close[0]], close[:-1]])
        tr = np.maximum.reduce([high-low, np.abs(high-prev_close), np.abs(low-prev_close)])
        atr20 = pd.Series(tr).rolling(20).mean().iloc[-1]
        if pd.notna(atr20):
            inferred_atr = float(atr20)
    atr_used = atr_hint if atr_hint and atr_hint>0 else (inferred_atr if inferred_atr else 0.0)

    # If no manual price and CSV present, use last close
    px_used = cur_price if cur_price and cur_price>0 else (float(ohlcv["Close"].iloc[-1]) if ohlcv is not None else None)

    with col1.expander("Derived inputs", expanded=False):
        st.write(f"Price used: **{px_used}**")
        st.write(f"ATR used: **{atr_used}**")

    # --- Strategy suggestion (paper only) ---
    if px_used is None:
        st.info("Provide a current price (sidebar) or upload OHLCV CSV so we can size strikes.")
    else:
        ideas = suggest_strategies(
            ticker=ticker.upper(),
            slope=slope,
            sr_levels=sr_levels,
            price=px_used,
            atr=atr_used,
            dte=dte
        )

        # Optional: naive backtest over recent window
        if ohlcv is not None and len(ohlcv) > 40:
            ideas = simple_backtest_metrics(ohlcv, ideas, dte_days=dte)

        col2.subheader("📋 Paper trade ideas")
        st.dataframe(pd.DataFrame(ideas))

        st.caption("⚠️ For education/paper trading only. No financial advice. Models are heuristic and derived from images; expect noise.")
else:
    st.info("Upload a candlestick chart image to begin.")
