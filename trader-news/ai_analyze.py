#!/usr/bin/env python3
import os
import json
import time
import argparse
import warnings

warnings.filterwarnings('ignore')
import yfinance as yf
from google import genai
from groq import Groq

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
    parser = argparse.ArgumentParser(description="Multi-Model Strategy Engine with Fallback")
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

    response_text = None

    # --- ATTEMPT 1: Google Gemini ---
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        try:
            client = genai.Client(api_key=gemini_key)
            models = ["gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-flash-latest"]
            for model in models:
                try:
                    res = client.models.generate_content(model=model, contents=prompt)
                    if res and res.text:
                        response_text = res.text
                        break
                except Exception:
                    continue
        except Exception:
            pass

    # --- ATTEMPT 2: Groq Fallback (If Gemini is blocked/503) ---
    if not response_text:
        groq_key = os.environ.get("GROQ_API_KEY")
        if groq_key:
            try:
                groq_client = Groq(api_key=groq_key)
                chat_completion = groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "You are a professional financial market strategist."},
                        {"role": "user", "content": prompt}
                    ],
                    model="llama-3.3-70b-versatile",
                )
                if chat_completion.choices and chat_completion.choices[0].message.content:
                    response_text = chat_completion.choices[0].message.content
            except Exception as e:
                print(f"Groq fallback notice: {e}")

    # Output writing
    if response_text:
        parts = response_text.split("===EXECUTION_SPLIT===")
        with open("ai_targets_out.txt", "w") as f:
            f.write(parts[0].strip())
        
        if len(parts) > 1:
            with open("ai_execution_out.txt", "w") as f:
                f.write(parts[1].strip())
        else:
            with open("ai_execution_out.txt", "w") as f:
                f.write("⚙️ **Execution Plan**: Generated via fallback model.")
    else:
        # Ultimate fallback if both APIs fail
        with open("ai_targets_out.txt", "w") as f:
            f.write("⚠️ **AI Generation Notice**: Both primary and fallback APIs are experiencing high volume. Quantitative levels remain fully active above.")
        with open("ai_execution_out.txt", "w") as f:
            f.write("⚙️ **Execution Plan**: Plan pending API recovery.")

if __name__ == "__main__":
    analyze_market()
