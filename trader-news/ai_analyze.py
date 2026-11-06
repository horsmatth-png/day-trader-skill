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
    parser = argparse.ArgumentParser(description="Multi-Model Strategy Engine")
    parser.add_argument("--focus", type=str, default="default", help="Analysis focus: macro, catalyst, value, target, execution, index-macro")
    args = parser.parse_args()

    watchlist_data = {}
    if os.path.exists("trader/watchlist.json"):
        try:
            with open("trader/watchlist.json", "r") as f:
                watchlist_data = json.loads(f.read().strip())
        except Exception:
            pass
    if not watchlist_data:
        watchlist_data = get_live_fallback_data()

    watchlist_json_str = json.dumps(watchlist_data, indent=2)

    target_json_str = ""
    if os.path.exists("trader/targets_watchlist.json"):
        try:
            with open("trader/targets_watchlist.json", "r") as f:
                target_json_str = f.read().strip()
        except Exception:
            pass
    if not target_json_str:
        target_json_str = watchlist_json_str

    fund_data = ""
    if os.path.exists("fundamentals_out.txt"):
        try:
            with open("fundamentals_out.txt", "r") as f:
                fund_data = f.read().strip()
        except Exception:
            pass

    # Build prompt based on focus
    if args.focus == "index-macro":
        prompt = f"You are a senior institutional macro risk manager. Analyze these global index benchmarks and give a concise Discord report:\n{watchlist_json_str}"
    elif args.focus == "catalyst":
        prompt = (
            f"You are an expert market analyst. Generate a concise Discord report split into two sections "
            f"(⚡ TOP 5 DAY TRADE CATALYSTS and 📈 TOP 5 SWING TRADE CATALYSTS) using ONLY these live prices:\n{watchlist_json_str}"
        )
    elif args.focus == "macro":
        prompt = f"You are an expert global macro trader. Provide a high-level macro prep report using this live data:\n{watchlist_json_str}"
    elif args.focus == "value":
        prompt = (
            f"You are a senior fundamental analyst & portfolio manager. Review these market valuation screeners and live prices:\n\n"
            f"FUNDAMENTAL METRICS:\n{fund_data}\n\n"
            f"LIVE BENCHMARK METRICS:\n{watchlist_json_str}\n\n"
            f"Provide a concise Discord report titled '💎 TOP FORWARD VALUE & GARP PROSPECTS'. "
            f"Select the top 3-4 stocks from the fundamental screen with the strongest forward risk/reward (considering P/E, P/S, ROE vs price). "
            f"For each pick, give maximum 2 bullet points detailing key fundamental strengths and strategic accumulation zone."
        )
    elif args.focus == "target":
        prompt = (
            f"You are a Senior Trading Strategist & Quantitative Risk Officer. "
            f"Review these technical levels, daily ATR targets, and fundamental valuations for our 10-asset custom basket:\n\n"
            f"{target_json_str}\n\n"
            f"Provide a concise Discord report titled '🎯 DAILY TARGETS & MACRO OVERVIEW'.\n"
            f"1. **Macro & Index Bias**: 2 short bullet points on FTSE 100 (^FTSE), NQ Futures (NQ=F), SPY, QQQ, VUSA.L.\n"
            f"2. **Top Stock Setups**: 2 short bullet points highlighting top Bullish and Bearish target setups among GOOGL, AMZN, TSLA, AAPL, BP.L."
        )
    elif args.focus == "execution":
        prompt = (
            f"You are a Senior Quantitative Execution Trader. "
            f"Using these calculated pivot levels, ATR expansion targets, and support/resistance data:\n\n"
            f"{target_json_str}\n\n"
            f"Provide a punchy Discord report titled '⚙️ TACTICAL EXECUTION PLAN'.\n"
            f"For each key mover (e.g. AMZN, TSLA, AAPL, GOOGL), limit your output to EXACTLY 2 bullet points:\n"
            f"• Bullet 1: Entry Trigger & Stop-Loss Placement (Pivot / S1 / R1 levels)\n"
            f"• Bullet 2: ATR Profit Target & Risk:Reward Ratio\n"
            f"Keep text tight and ultra-concise."
        )
    else:
        prompt = f"""
You are a Senior Quantitative Analyst. Review these technical pivot & ATR targets:
{target_json_str}

Generate a 2-part trade strategy report. Use the exact split marker `===EXECUTION_SPLIT===` between Part 1 and Part 2.

PART 1 (Macro & High-Level Targets):
Title: 🌐 **GLOBAL MACRO & TARGET OVERVIEW**
- 2 bullet points covering Index/Macro sentiment (^FTSE, NQ=F, SPY, QQQ).
- 2 bullet points on top bullish/bearish candidates.

===EXECUTION_SPLIT===

PART 2 (Tactical Execution Plan):
Title: ⚙️ **TACTICAL EXECUTION PLAN**
For each primary setup (AMZN, TSLA, AAPL, GOOGL), give EXACTLY 2 concise bullets.
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
                pass

    # --- 3. Output Handling ---
    if not response_text:
        response_text = "⚠️ **AI Generation Notice**: Primary and fallback models are temporarily busy. Quantitative levels remain active above."

    # Handle file splitting for default daily targets, print to stdout for focused workflows
    if args.focus == "default" and "===EXECUTION_SPLIT===" in response_text:
        parts = response_text.split("===EXECUTION_SPLIT===")
        with open("ai_targets_out.txt", "w") as f:
            f.write(parts[0].strip())
        with open("ai_execution_out.txt", "w") as f:
            f.write(parts[1].strip() if len(parts) > 1 else "")
    else:
        print(response_text)

if __name__ == "__main__":
    analyze_market()
