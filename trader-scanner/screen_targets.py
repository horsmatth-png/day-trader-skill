#!/usr/bin/env python3
import os
import json
import warnings
warnings.filterwarnings('ignore')
import yfinance as yf

def calculate_levels(df, info):
    """Calculates Daily Pivot Points, Support/Resistance, and ATR Target Projections."""
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest
    
    high = float(prev['High'])
    low = float(prev['Low'])
    close = float(prev['Close'])
    curr_price = float(latest['Close'])
    
    # Classic Floor Pivot Points
    pivot = (high + low + close) / 3.0
    r1 = (2.0 * pivot) - low
    s1 = (2.0 * pivot) - high
    
    # 14-day ATR estimation for daily volatility expansion
    df['TR'] = df.apply(lambda row: max(row['High'] - row['Low'], 
                                        abs(row['High'] - row['Close']), 
                                        abs(row['Low'] - row['Close'])), axis=1)
    atr = float(df['TR'].tail(14).mean())
    
    # Projected Daily Targets
    bull_target = curr_price + (atr * 0.85)
    bear_target = curr_price - (atr * 0.85)
    
    pe = info.get("trailingPE", "N/A")
    ps = info.get("priceToSalesTrailing12Months", "N/A")
    if isinstance(pe, (int, float)): pe = round(pe, 1)
    if isinstance(ps, (int, float)): ps = round(ps, 1)

    return {
        "price": round(curr_price, 2),
        "pct_change": round(((curr_price - float(prev['Close'])) / float(prev['Close'])) * 100, 2),
        "pivot": round(pivot, 2),
        "r1": round(r1, 2),
        "s1": round(s1, 2),
        "bull_target": round(bull_target, 2),
        "bear_target": round(bear_target, 2),
        "pe": pe,
        "ps": ps
    }

def main():
    # Your custom 10-asset basket
    watchlist = [
        "^FTSE",    # FTSE 100 Index
        "NQ=F",     # Nasdaq-100 Futures
        "SPY",      # SPDR S&P 500 ETF (SPTRD)
        "QQQ",      # Invesco QQQ Trust
        "VUSA.L",   # Vanguard S&P 500 UCITS ETF (LSE)
        "BP.L",     # BP plc (LSE)
        "GOOGL",    # Alphabet Inc
        "AMZN",     # Amazon.com Inc
        "TSLA",     # Tesla Inc
        "AAPL"      # Apple Inc
    ]

    results = {}
    summary_lines = ["=== DAILY MACRO, FUNDAMENTAL & TECHNICAL TARGETS ==="]

    for sym in watchlist:
        try:
            t = yf.Ticker(sym)
            df = t.history(period="1mo", interval="1d")
            if df.empty or len(df) < 2:
                continue
            
            info = {}
            try:
                info = t.info
            except Exception:
                pass

            metrics = calculate_levels(df, info)
            results[sym] = metrics
            
            clean_sym = sym.replace(".L", "").replace("=F", "").replace("^", "")
            line = (
                f"${clean_sym:<6} | Last: ${metrics['price']:>7.2f} ({metrics['pct_change']:>+5.2f}%) | "
                f"Bull: ${metrics['bull_target']:>7.2f} | Bear: ${metrics['bear_target']:>7.2f} | "
                f"Pivot: ${metrics['pivot']:>7.2f} | P/E: {str(metrics['pe']):>5}"
            )
            summary_lines.append(line)
        except Exception:
            continue

    text_output = "\n".join(summary_lines)
    
    os.makedirs("trader", exist_ok=True)
    with open("trader/targets_watchlist.json", "w") as f:
        json.dump(results, f, indent=2)
        
    with open("targets_out.txt", "w") as f:
        f.write(text_output)
        
    print(text_output)

if __name__ == "__main__":
    main()
