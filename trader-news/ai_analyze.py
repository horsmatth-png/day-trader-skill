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
        watchlist = json.load(f)

    top_tickers = watchlist[:5] if isinstance(watchlist, list) else []
    if not top_tickers:
        print("Watchlist empty.")
        return

    # Check if this run was triggered with macro/swing focus
    is_macro = "--focus macro" in " ".join(sys.argv)

    if is_macro:
        prompt = f"""
        You are a seasoned portfolio manager and macro strategist. Analyze these watchlist assets for multi-week swing trading and long-term investment potential, keeping macroeconomic conditions, sector trends, and fundamental strength in mind:
        {json.dumps(top_tickers, indent=2)}

        Provide a structured breakdown covering:
        1. Macroeconomic headwinds/tailwinds impacting these assets.
        2. Fundamental strength or valuation notes based on available context.
        3. A multi-week outlook verdict (Accumulate / Hold / Avoid).
        Keep it concise and formatted for Discord markdown.
        """
    else:
        prompt = f"""
        You are an expert day trader. Analyze these setups focusing on short-term RSI, volume, and intraday catalysts:
        {json.dumps(top_tickers, indent=2)}

        Provide a 1-2 sentence verdict per ticker:
        - 🔥 BULLISH MOMENTUM (Safe for intraday continuation)
        - ⚠️ DANGER / CATALYST RISK (Avoid or watch for reversals)
        - ℹ️ NEUTRAL
        Keep it short and formatted for Discord markdown.
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
