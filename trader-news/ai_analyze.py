import os
import json
import time
import argparse
from google import genai

def analyze_market():
    parser = argparse.ArgumentParser(description="Gemini AI Market Analysis")
    parser.add_argument("--focus", type=str, default="default", help="Analysis focus: macro, catalyst, or default")
    args = parser.parse_args()

    # Load watchlist if present
    watchlist_data = "No watchlist.json found to analyze."
    watchlist_path = "trader/watchlist.json"
    if os.path.exists(watchlist_path):
        try:
            with open(watchlist_path, "r") as f:
                content = f.read()
                # Handle both JSON array/dict or plain text structures safely
                if content.strip().startswith("[") or content.strip().startswith("{"):
                    parsed = json.loads(content)
                    watchlist_data = json.dumps(parsed, indent=2)
                else:
                    watchlist_data = content
        except Exception as e:
            watchlist_data = f"Error reading watchlist.json: {e}"

    # Build prompt configuration based on focus flag
    if args.focus == "macro":
        prompt = f"""
You are an expert macro and swing trader. Analyze the following market watch list and market data to provide a high-level macro prep report for the upcoming week. Focus on sector rotation, key technical levels, and macro catalysts.

Market Watchlist / Scan Data:
{watchlist_data}
"""
    elif args.focus == "catalyst":
        prompt = f"""
You are an expert market analyst. Evaluate the market data, news, and fundamentals below.
Generate a concise Discord report split strictly into TWO sections with 5 top picks each:

⚡ TOP 5 DAY TRADE CATALYSTS (Intraday Volatility / Earnings / Gappers)
1. $TICKER - [Bias: Long/Short] - Catalyst Reason & Intraday Trigger Level
2. $TICKER - [Bias: Long/Short] - Catalyst Reason & Intraday Trigger Level
3. $TICKER - [Bias: Long/Short] - Catalyst Reason & Intraday Trigger Level
4. $TICKER - [Bias: Long/Short] - Catalyst Reason & Intraday Trigger Level
5. $TICKER - [Bias: Long/Short] - Catalyst Reason & Intraday Trigger Level

📈 TOP 5 SWING TRADE CATALYSTS (Multi-Day Fundamental & Macro Mispricings)
1. $TICKER - [Bias: Bullish/Bearish] - Fundamental/Macro Thesis & Key Level
2. $TICKER - [Bias: Bullish/Bearish] - Fundamental/Macro Thesis & Key Level
3. $TICKER - [Bias: Bullish/Bearish] - Fundamental/Macro Thesis & Key Level
4. $TICKER - [Bias: Bullish/Bearish] - Fundamental/Macro Thesis & Key Level
5. $TICKER - [Bias: Bullish/Bearish] - Fundamental/Macro Thesis & Key Level

Keep overall output concise so it fits cleanly inside Discord payloads.

Market Watchlist / Scan Data:
{watchlist_data}
"""
    else:
        prompt = f"""
You are a professional day trading assistant. Review the following intraday setup candidates and volume scans. Provide tactical entries, risk management context, and catalyst notes.

Market Watchlist / Scan Data:
{watchlist_data}
"""

    # Initialize GenAI Client using the official Google GenAI SDK
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        return

    client = genai.Client(api_key=api_key)

    # Model fallback sequence with exponential backoff retries
    models = ["gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.5-flash-lite"]
    max_retries = 3
    backoff_factor = 12

    response_text = None

    for model in models:
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt
                )
                if response and response.text:
                    response_text = response.text
                    break
            except Exception as e:
                print(f"⚠️ {model} error on attempt {attempt+1}/{max_retries}: {e}")
                if attempt < max_retries - 1:
                    sleep_time = backoff_factor * (2 ** attempt)
                    print(f"Retrying in {sleep_time}s...")
                    time.sleep(sleep_time)
                else:
                    print(f"Exhausted retries for {model}. Falling back to next model...")
        if response_text:
            break

    if response_text:
        print(response_text)
    else:
        print("❌ All Gemini models and fallback attempts failed to generate analysis.")

if __name__ == "__main__":
    analyze_market()
