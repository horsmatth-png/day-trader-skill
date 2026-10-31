import os
import json
import time
import argparse
from google import genai

def analyze_market():
    parser = argparse.ArgumentParser(description="Gemini AI Market Analysis")
    parser.add_argument("--focus", type=str, default="default", help="Analysis focus: macro, catalyst, index-macro, or default")
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
You are an expert global macro and swing trader analyzing a mixed universe of US and UK (FTSE 100) equities.
Analyze the following market watch list and provide a high-level macro prep report for the upcoming week.

Key Instructions:
1. Identify major macro themes (e.g., Tech vs. Energy/Commodities, US/UK Rate Divergence, Defensive Growth).
2. Note key technical levels (20-day breakouts, RSI oversold conditions).
3. If analyzing UK (.L) tickers, denote prices in £ (GBP) and highlight energy/commodity/banking drivers where relevant.

Market Watchlist / Scan Data:
{watchlist_data}
"""
    elif args.focus == "catalyst":
        prompt = f"""
You are an expert market analyst. Evaluate the market data, news, and fundamentals below.
Generate a concise Discord report split strictly into TWO sections with 5 top picks each. Keep descriptions brief and under 15 words per pick so they fit within output limits:

⚡ TOP 5 DAY TRADE CATALYSTS (Intraday Volatility / Earnings / Gappers)
1. $TICKER - [Bias: Long/Short] - Brief reason & trigger level
2. $TICKER - [Bias: Long/Short] - Brief reason & trigger level
3. $TICKER - [Bias: Long/Short] - Brief reason & trigger level
4. $TICKER - [Bias: Long/Short] - Brief reason & trigger level
5. $TICKER - [Bias: Long/Short] - Brief reason & trigger level

📈 TOP 5 SWING TRADE CATALYSTS (Multi-Day Fundamental & Macro Mispricings)
1. $TICKER - [Bias: Bullish/Bearish] - Brief thesis & key level
2. $TICKER - [Bias: Bullish/Bearish] - Brief thesis & key level
3. $TICKER - [Bias: Bullish/Bearish] - Brief thesis & key level
4. $TICKER - [Bias: Bullish/Bearish] - Brief thesis & key level
5. $TICKER - [Bias: Bullish/Bearish] - Brief thesis & key level

Market Watchlist / Scan Data:
{watchlist_data}
"""
    elif args.focus == "index-macro":
        prompt = f"""
You are a senior institutional macro risk manager. Analyze the current global index benchmarks and market data below. 
Your objective is to predict macro shifts, sector liquidations, or risk-off rotations across the **Nasdaq, S&P 500, FTSE 100, and DAX**.

Structure your Discord report into these concise sections:
1. 🚨 **Regime Shift & Risk Bias:** (State whether markets are facing Risk-On, Risk-Off, or Liquidation warning)
2. 💻 **Nasdaq & S&P 500 Outlook:** (Tech concentration, bond yield pressures, impending sell-off or dip-buying triggers)
3. 🏰 **European Anchors (FTSE 100 & DAX):** (Divergence against US markets, commodity/export tailwinds or domestic macro drags)
4. ⚡ **Indicator Warning Triggers:** (What specific price action or news catalyst will trigger the next major swing)

Keep formatting clean and tightly under 1,400 characters for Discord delivery.

Market Benchmarks & Data:
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
