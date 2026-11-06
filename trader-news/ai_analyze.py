#!/usr/bin/env python3
import os
import json
import time
import argparse
import warnings

warnings.filterwarnings('ignore')
import yfinance as yf
from google import genai
from google.genai import types

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
    parser = argparse.ArgumentParser(description="Gemini Combined Strategy Engine")
    args = parser.parse_args()

    target_json_str = ""
    if os.path.exists("trader/targets_watchlist.json"):
        try:
            with open("trader/targets_watchlist.json", "r") as f:
                target_json_str = f.read().strip()
        except Exception:
            pass

    if not target_json_str:
        target_json_str = json.dumps(get_live_fallback_data(), indent=2)

    # Master Consolidated Prompt: Gets Macro + Setups + Execution Plan in ONE API call
    prompt = f"""
You are a Senior Quantitative Analyst. Review these technical pivot & ATR targets:
{target_json_str}

Generate a 2-part trade strategy report. Use the exact split marker `===EXECUTION_SPLIT===` between Part 1 and Part 2.

PART 1 (Macro & High-Level Targets):
Title: 🌐 **GLOBAL MACRO & TARGET OVERVIEW**
- 2 bullet points covering Index/Macro sentiment (^FTSE, NQ=F, SPY, QQQ).
- 2 bullet points on top bullish/bearish candidates (GOOGL, AMZN, TSLA, AAPL, BP.L).

===EXECUTION_SPLIT===

PART 2 (Tactical Execution Plan):
Title: ⚙️ **TACTICAL EXECUTION PLAN**
For each primary setup (AMZN, TSLA, AAPL, GOOGL), give EXACTLY 2 concise bullets:
- Bullet 1: Entry Trigger & Stop-Loss Placement (Pivot/S1/R1 levels)
- Bullet 2: ATR Target & Risk:Reward Ratio
"""

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return

    # Enable automatic SDK network retries for status code 503/429
    http_opts = types.HttpOptions(
        retry_options=types.HttpRetryOptions(
            attempts=5,
            initial_delay=3.0,
            http_status_codes=[429, 500, 502, 503, 504]
        )
    )

    client = genai.Client(api_key=api_key, http_options=http_opts)

    # Current stable production models supported on free tier
    models_to_try = [
        "gemini-3.8-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.6-flash"
    ]

    response_text = None
    for model in models_to_try:
        try:
            response = client.models.generate_content(model=model, contents=prompt)
            if response and response.text:
                response_text = response.text
                break
        except Exception:
            time.sleep(3)
            continue

    if response_text:
        # Split into two separate files for Discord posting
        parts = response_text.split("===EXECUTION_SPLIT===")
        with open("ai_targets_out.txt", "w") as f:
            f.write(parts[0].strip())
        
        if len(parts) > 1:
            with open("ai_execution_out.txt", "w") as f:
                f.write(parts[1].strip())
    else:
        with open("ai_targets_out.txt", "w") as f:
            f.write("⚠️ **AI Generation Notice**: Free-tier API servers are under high load. Quantitative levels remain active above.")

if __name__ == "__main__":
    analyze_market()
