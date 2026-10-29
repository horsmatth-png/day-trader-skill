import os
import json
import sys
import time
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

    # Extract ticker candidates robustly
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

    # Primary and fallback models for high availability
    models_to_try = ["gemini-3.8-flash", "gemini-2.5-flash", "gemini-2.5-flash-lite"]
    
    for model_name in models_to_try:
        success = False
        max_retries = 3
        
        for attempt in range(1, max_retries + 1):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                print("\n**🤖 GEMINI AI ANALYSIS REPORT**")
                print(response.text)
                success = True
                break
            except Exception as e:
                err_msg = str(e)
                if "503" in err_msg or "UNAVAILABLE" in err_msg:
                    wait_time = attempt * 10
                    print(f"⚠️ {model_name} busy (503). Retrying in {wait_time}s (Attempt {attempt}/{max_retries})...")
                    time.sleep(wait_time)
                else:
                    print(f"Gemini API error on {model_name}: {e}")
                    break  # Skip retries if error is not capacity-related (e.g. 404/auth)

        if success:
            break

if __name__ == "__main__":
    run_ai_analysis()
