import os
import json
import time
import argparse
import warnings

warnings.filterwarnings('ignore')
import yfinance as yf
from google import genai

def get_live_fallback_data():
    tickers = ["NVDA", "TSLA", "AAPL", "AMD", "META", "QQQ", "SPY", "^FTSE", "EWG", "^VIX"]
    data = {}
    for sym in tickers:
        try:
            t = yf.Ticker(sym)
            df = t.history(period="3d", interval="1d")
            if not df.empty:
                latest = float(df['Close'].iloc[-1])
                prev = float(df['Close'].iloc[-2]) if len(df) > 1 else latest
                pct = round(((latest - prev) / prev) * 100, 2)
                data[sym] = {"price": round(latest, 2), "change_pct": pct}
        except Exception:
            continue
    return data

def analyze_market():
    parser = argparse.ArgumentParser(description="Gemini AI Market Analysis")
    parser.add_argument("--focus", type=str, default="default", help="Analysis focus")
    args = parser.parse_args()

    watchlist_data = {}
    watchlist_path = "trader/watchlist.json"
    
    # Try reading watchlist.json
    if os.path.exists(watchlist_path):
        try:
            with open(watchlist_path, "r") as f:
                content = f.read().strip()
                if content and (content.startswith("{") or content.startswith("[")):
                    watchlist_data = json.loads(content)
        except Exception:
            pass

    # Self-healing: If json is empty or missing, fetch live data directly right here
    if not watchlist_data or len(watchlist_data) == 0:
        watchlist_data = get_live_fallback_data()

    watchlist_json_str = json.dumps(watchlist_data, indent=2)

    if args.focus == "index-macro":
        max_output_length = 1500
        prompt = f"""
You are a senior institutional macro risk manager. Analyze the global index benchmarks below.
Live Data:
{watchlist_json_str}
"""
    elif args.focus == "catalyst":
        max_output_length = 1500
        prompt = f"""
You are an expert market analyst. Evaluate the live market scan data provided below.
Generate a concise Discord report split strictly into TWO sections using ONLY these live prices.

⚡ TOP 5 DAY TRADE CATALYSTS (Intraday Volatility / Gappers)
Format each pick as: 1. $TICKER - [Bias: Long/Short] - Live Price & brief reason/trigger level

📈 TOP 5 SWING TRADE CATALYSTS (Multi-Day Framework)
Format each pick as: 1. $TICKER - [Bias: Bullish/Bearish] - Live Price & brief thesis/key level

Live Scan Data:
{watchlist_json_str}
"""
    elif args.focus == "macro":
        max_output_length = 1500
        prompt = f"""
You are an expert global macro and swing trader. Analyze the market watch list and provide a high-level macro prep report using the live data.
Live Data:
{watchlist_json_str}
"""
    else:
        max_output_length = 1500
        prompt = f"""
You are a professional day trading assistant. Review the intraday setup candidates and volume scans below using ONLY the live market prices provided.
Live Data:
{watchlist_json_str}
"""

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        return

    client = genai.Client(api_key=api_key)
    models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
    
    response_text = None
    for model in models:
        try:
            response = client.models.generate_content(model=model, contents=prompt)
            if response and response.text:
                response_text = response.text
                break
        except Exception:
            continue

    if response_text:
        if len(response_text) > max_output_length:
            response_text = response_text[:max_output_length] + "\n\n*(Report truncated)*"
        print(response_text)
    else:
        print("❌ All Gemini models failed to generate analysis.")

if __name__ == "__main__":
    analyze_market()
