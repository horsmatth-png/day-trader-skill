#!/usr/bin/env python3
import os
import json
import time
import random
import argparse
import warnings

warnings.filterwarnings('ignore')
import yfinance as yf
from google import genai
from google.genai import types

def get_live_fallback_data():
    """Fallback ticker retriever if watchlist files are missing or empty."""
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
    parser = argparse.ArgumentParser(description="Gemini AI Market Analysis Engine")
    parser.add_argument("--focus", type=str, default="default", help="Analysis focus: macro, catalyst, value, target, execution, index-macro")
    args = parser.parse_args()

    # Load standard watchlist json if present
    watchlist_data = {}
    watchlist_path = "trader/watchlist.json"
    if os.path.exists(watchlist_path):
        try:
            with open(watchlist_path, "r") as f:
                content = f.read().strip()
                if content and (content.startswith("{") or content.startswith("[")):
                    watchlist_data = json.loads(content)
        except Exception:
            pass

    if not watchlist_data:
        watchlist_data = get_live_fallback_data()

    watchlist_json_str = json.dumps(watchlist_data, indent=2)

    # Load fundamental screening text if present
    fund_data = ""
    if os.path.exists("fundamentals_out.txt"):
        try:
            with open("fundamentals_out.txt", "r") as f:
                fund_data = f.read().strip()
        except Exception:
            pass

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
        target_json_str = ""
        if os.path.exists("trader/targets_watchlist.json"):
            try:
                with open("trader/targets_watchlist.json", "r") as f:
                    target_json_str = f.read().strip()
            except Exception:
                pass
        if not target_json_str:
            target_json_str = watchlist_json_str

        prompt = (
            f"You are a Senior Trading Strategist & Quantitative Risk Officer. "
            f"Review these technical levels, daily ATR targets, and fundamental valuations for our 10-asset custom basket:\n\n"
            f"{target_json_str}\n\n"
            f"Provide a concise Discord report titled '🎯 DAILY TARGETS & MACRO OVERVIEW'.\n"
            f"1. **Macro & Index Bias**: 2 short bullet points on FTSE 100 (^FTSE), NQ Futures (NQ=F), SPY, QQQ, VUSA.L.\n"
            f"2. **Top Stock Setups**: 2 short bullet points highlighting top Bullish and Bearish target setups among GOOGL, AMZN, TSLA, AAPL, BP.L."
        )
    elif args.focus == "execution":
        target_json_str = ""
        if os.path.exists("trader/targets_watchlist.json"):
            try:
                with open("trader/targets_watchlist.json", "r") as f:
                    target_json_str = f.read().strip()
            except Exception:
                pass
        if not target_json_str:
            target_json_str = watchlist_json_str

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
        prompt = f"You are a professional day trading assistant. Review these market scans and provide tactical entries and risk context:\n{watchlist_json_str}"

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return

    # Configure client HTTP options for automatic exponential backoff on 503 and 429 errors
    http_opts = types.HttpOptions(
        retry_options=types.HttpRetryOptions(
            attempts=5,
            initial_delay=2.0,
            http_status_codes=[408, 429, 500, 502, 503, 504]
        )
    )

    client = genai.Client(api_key=api_key, http_options=http_opts)

    models_to_try = [
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-3.8-flash",
        "gemini-flash-latest"
    ]

    response_text = None
    
    # Retry loop across model tags with backoff & jitter
    for attempt in range(3):
        for model in models_to_try:
            try:
                response = client.models.generate_content(model=model, contents=prompt)
                if response and response.text:
                    response_text = response.text
                    break
            except Exception:
                # Add jitter pause between model switches to avoid thundering herd on free tier
                time.sleep(2 + random.uniform(0.5, 1.5))
                continue
        if response_text:
            break
        time.sleep(5 + random.uniform(1.0, 2.0))

    if response_text:
        print(response_text)
    else:
        print("⚠️ **AI Generation Notice**: Free-tier API servers are experiencing high demand. Quantitative levels remain fully active above.")

if __name__ == "__main__":
    analyze_market()
