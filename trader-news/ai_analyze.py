import os
import json
import sys
from google import genai

def run_ai_analysis():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("⚠️ No GEMINI_API_KEY found. Skipping AI analysis.")
        return

    client = genai.Client(api_key=api_key)

    watchlist_path = "trader/watchlist.json"
    if not os.path.exists(watchlist_path):
        print("No watchlist.json found to analyze.")
        return

    try:
        with open(watchlist_path, "r") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading watchlist.json: {e}")
        return

    # Extract ticker candidates robustly across dict and list structures
    top_tickers = []
    if isinstance(data, list):
        top_tickers = data[:5]
    elif isinstance(data, dict):
        candidates = (
            data.get("hits") or 
            data.get("symbols") or 
            data.get("watchlist") or 
            data.get("tickers") or []
        )
        top_tickers = candidates[:5]

    if not top_tickers:
        print("Watchlist empty or no valid ticker hits parsed.")
        return

    cli_args = " ".join(sys.argv)
    is_macro = "--focus macro" in cli_args or "macro" in cli_args

    if is_macro:
        prompt = f"""
        You are a portfolio manager evaluating long-term & swing opportunities.
        Analyze these breakout tickers:
        {json.dumps(top_tickers, indent=2)}

        Provide a breakdown covering:
        1. Macro / Sector trends.
        2. Fundamental strength or valuation concerns.
        3. Multi-week verdict (Accumulate / Hold / Avoid).
        Format cleanly for Discord markdown.
        """
    else:
        prompt = f"""
        You are an elite intraday momentum trader. 
        Analyze these top Opening Range Breakout (ORB) / volume setup candidates:
        {json.dumps(top_tickers, indent=2)}

        Provide a 1-2 sentence quick tactical trade assessment for each ticker:
        - 🔥 BULLISH MOMENTUM (Safe for intraday continuation / gap-and-go)
        - ⚠️ DANGER / CATALYST RISK (Avoid or watch for fakeout/reversal)
        - ℹ️ NEUTRAL
        Keep it concise, actionable, and formatted for Discord markdown.
        """

    try:
        # Updated model ID to current active endpoint
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt
        )
        print("\n**🤖 GEMINI AI ANALYSIS REPORT**")
        print(response.text)
    except Exception as e:
        print(f"Gemini API error: {e}")

if __name__ == "__main__":
    run_ai_analysis()
