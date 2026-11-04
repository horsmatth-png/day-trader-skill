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
    
    if os.path.exists(watchlist_path):
        try:
            with open(watchlist_path, "r") as f:
                content = f.read().strip()
                if content and (content.startswith("{") or content.startswith("[")):
                    watchlist_data = json.loads(content)
        except Exception:
            pass

    if not watchlist_data:
        watchlist_data = get_live_fallback_data()

    watchlist_json_str = json.dumps(watchlist_data, indent=2)

    if args.focus == "index-macro":
        prompt = f"You are a senior institutional macro risk manager. Analyze these global index benchmarks and give a concise Discord report:\n{watchlist_json_str}"
    elif args.focus == "catalyst":
        prompt = f"You are an expert market analyst. Generate a concise Discord report split into two sections (⚡ TOP 5 DAY TRADE CATALYSTS and 📈 TOP 5 SWING TRADE CATALYSTS) using ONLY these live prices:\n{watchlist_json_str}"
    elif args.focus == "macro":
        prompt = f"You are an expert global macro trader. Provide a high-level macro prep report using this live data:\n{watchlist_json_str}"
    else:
        prompt = f"You are a professional day trading assistant. Review these market scans and provide tactical entries and risk context:\n{watchlist_json_str}"

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        return

    client = genai.Client(api_key=api_key)
    
    # Cascading fallback model list to handle rate limits gracefully
    models_to_try = [
        "gemini-3.8-flash",
        "gemini-3.5-flash-lite",
        "gemini-flash-latest"
    ]
    
    response_text = None
    for model in models_to_try:
        try:
            response = client.models.generate_content(model=model, contents=prompt)
            if response and response.text:
                response_text = response.text
                break
        except Exception as e:
            err_str = str(e)
            # If it's a rate limit or resource exhausted issue, try the next model model tier
            if "429" in err_str or "ResourceExhausted" in err_str or "quota" in err_str.lower():
                continue
            continue

    if response_text:
        if len(response_text) > 1500:
            response_text = response_text[:1500] + "\n\n*(Report truncated)*"
        print(response_text)
    else:
        # Graceful fallback: outputs market pricing summary if quota is completely exhausted
        print("⚠️ **AI Quota Resting (Rate Limit Reached)**\n\n=== LIVE MARKET METRICS FALLBACK ===\n" + watchlist_json_str)

if __name__ == "__main__":
    analyze_market()
