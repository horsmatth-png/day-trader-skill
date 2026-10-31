import os
import json
import time
import argparse
import warnings

# Suppress library warnings globally
warnings.filterwarnings('ignore')

from google import genai

def analyze_market():
    parser = argparse.ArgumentParser(description="Gemini AI Market Analysis")
    parser.add_argument("--focus", type=str, default="default", help="Analysis focus: macro, catalyst, index-macro, or default")
    args = parser.parse_args()

    watchlist_data = "No watchlist.json found to analyze."
    watchlist_path = "trader/watchlist.json"
    if os.path.exists(watchlist_path):
        try:
            with open(watchlist_path, "r") as f:
                content = f.read()
                if content.strip().startswith("[") or content.strip().startswith("{"):
                    parsed = json.loads(content)
                    watchlist_data = json.dumps(parsed, indent=2)
                else:
                    watchlist_data = content
        except Exception as e:
            watchlist_data = f"Error reading watchlist.json: {e}"

    if args.focus == "index-macro":
        max_output_length = 1500
        prompt = f"""
You are a senior institutional macro risk manager. Analyze the current global index benchmarks below.
Predict macro shifts, sector liquidations, or risk-off rotations across the Nasdaq, S&P 500, FTSE 100, and DAX.

Structure your Discord report cleanly:
1. 🚨 **Regime Shift & Risk Bias:** (Risk-On / Risk-Off / Liquidation warning)
2. 💻 **Nasdaq & S&P 500 Outlook:** (Tech concentration, bond yield pressure)
3. 🏰 **European Anchors (FTSE 100 & DAX):** (Divergence, macro tailwinds/drags)
4. ⚡ **Indicator Warning Triggers:** (Price action or news catalyst to watch)

Data:
{watchlist_data}
"""
    elif args.focus == "catalyst":
        max_output_length = 1500
        prompt = f"""
You are an expert market analyst. Evaluate the market data, news, and fundamentals below.
Generate a concise Discord report split strictly into TWO sections with 5 top picks each (max 15 words per pick):

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

Data:
{watchlist_data}
"""
    elif args.focus == "macro":
        max_output_length = 1500
        prompt = f"""
You are an expert global macro and swing trader analyzing a mixed universe of US and UK equities.
Analyze the market watch list and provide a high-level macro prep report for the upcoming week.

Key Instructions:
1. Identify major macro themes (Tech vs. Energy/Commodities, Rate Divergence, Defensive Growth).
2. Note key technical levels (20-day breakouts, RSI oversold).
3. For UK tickers, denote prices in £ (GBP) and highlight energy/commodity/banking drivers.

Data:
{watchlist_data}
"""
    else:
        max_output_length = 1500
        prompt = f"""
You are a professional day trading assistant. Review the intraday setup candidates and volume scans below. Provide tactical entries, risk management context, and catalyst notes.

Data:
{watchlist_data}
"""

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        return

    client = genai.Client(api_key=api_key)
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
                if attempt < max_retries - 1:
                    time.sleep(backoff_factor * (2 ** attempt))
                else:
                    pass
        if response_text:
            break

    if response_text:
        if len(response_text) > max_output_length:
            response_text = response_text[:max_output_length] + "\n\n*(Report truncated)*"
        print(response_text)
    else:
        print("❌ All Gemini models failed to generate analysis.")

if __name__ == "__main__":
    analyze_market()
