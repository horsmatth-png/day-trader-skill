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

    with open(watchlist_path, "r") as f:
        data = json.load(f)

    # Extract ticker candidates robustly across list or dict formats
    top_tickers = []
    if isinstance(data, list):
        top_tickers = data[:5]
    elif isinstance(data, dict):
        candidates = data.get("hits") or data.get("symbols") or data.get("watchlist") or []
        top_tickers = candidates[:5]

    if not top_tickers:
        print("Watchlist empty or no valid ticker hits parsed.")
        return

    print(f"Analyzing top candidates with Gemini: {top_tickers}")

    # Check command line flags for macro vs day trading focus
    cli_args = " ".join(sys.argv)
    is_macro = "--focus macro" in cli_args or "macro" in cli_args

    if is_macro:
        prompt = f"""
        You are a seasoned portfolio manager and macro strategist. Analyze these top breakout candidates for multi-week swing trading and long-term potential:
        {json.dumps(top_tickers, indent=2)}

        Provide a structured breakdown covering:
        1. Macro headwinds/tailwinds impacting these assets.
        2. Fundamental strength and valuation notes.
        3. A multi-week outlook verdict (Accumulate / Hold / Avoid).
        Keep it concise and formatted for Discord markdown.
        """
    else:
        prompt = f"""
        You are an expert intraday trader. Analyze these top Opening Range Breakout (ORB) / volume setup candidates:
        {json.dumps(top_tickers, indent=2)}

        Provide a 1-2 sentence quick tactical assessment for each ticker:
        - 🔥 BULLISH MOMENTUM (Safe for intraday continuation / gap-and-go)
        - ⚠️ DANGER / CATALYST RISK (Avoid or watch for fakeout/reversal)
        - ℹ️ NEUTRAL
        Keep it concise and formatted for Discord markdown.
        """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        print("\n--- GEMINI AI INTEL REPORT ---")
        print(response.text)
    except Exception as e:
        print(f"Gemini API error: {e}")

if __name__ == "__main__":
    run_ai_analysis()
