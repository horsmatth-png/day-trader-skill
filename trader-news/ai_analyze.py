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
    parser = argparse.ArgumentParser(description="Multi-Model Strategy Engine with Guaranteed Output")
    parser.add_argument("--focus", type=str, default="default", help="Analysis focus: macro, catalyst, value, target, execution, index-macro")
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
You are a Senior Quantitative Trading Strategist. Review these technical pivot & ATR targets for our 10-asset basket:
{target_json_str}

Provide a concise 2-part trade report. Use the exact split marker `===EXECUTION_SPLIT===` between Part 1 and Part 2.

PART 1:
🎯 **DAILY TARGETS & MACRO OVERVIEW**
- 2 bullet points on Index/Macro bias (^FTSE, NQ=F, SPY, QQQ).
- 2 bullet points on top stock setups (GOOGL, AMZN, TSLA, AAPL, BP.L).

===EXECUTION_SPLIT===

PART 2:
⚙️ **TACTICAL EXECUTION PLAN**
For key tickers (AMZN, TSLA, AAPL, GOOGL), give EXACTLY 2 bullets each:
• Entry Trigger & Stop-Loss (Pivot / S1 / R1)
• ATR Target & Risk:Reward
"""

    response_text = None

    # --- 1. Try Gemini First ---
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        try:
            client = genai.Client(api_key=gemini_key)
            for model in ["gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-flash-latest"]:
                try:
                    res = client.models.generate_content(model=model, contents=prompt)
                    if res and res.text:
                        response_text = res.text
                        break
                except Exception:
                    continue
        except Exception:
            pass

    # --- 2. Try Groq Fallback if Gemini failed ---
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
                print(f"Groq error: {e}")

    # --- 3. Guaranteed Fallback Text so files are never empty ---
    if not response_text:
        response_text = (
            "🎯 **DAILY TARGETS & MACRO OVERVIEW**\n"
            "- ⚠️ **API Notice**: Free-tier Gemini and Groq fallback models are temporarily rate-limited.\n"
            "- Quantitative pivot levels and ATR bands displayed in the matrix above remain fully active for session execution.\n"
            "===EXECUTION_SPLIT===\n"
            "⚙️ **TACTICAL EXECUTION PLAN**\n"
            "- Rely on standard S1/R1 pivot boundaries and 14-day ATR expansion targets calculated above.\n"
            "- Monitor volume at key support and resistance handles for confirmation."
        )

    # Split and write out files so GitHub Actions posts them unconditionally
    parts = response_text.split("===EXECUTION_SPLIT===")
    
    with open("ai_targets_out.txt", "w") as f:
        f.write(parts[0].strip())
    
    if len(parts) > 1:
        with open("ai_execution_out.txt", "w") as f:
            f.write(parts[1].strip())
        print("Successfully generated and split AI analysis files.")
    else:
        with open("ai_execution_out.txt", "w") as f:
            f.write("⚙️ **Execution Plan**: Standard pivot execution rules active.")

if __name__ == "__main__":
    analyze_market()
