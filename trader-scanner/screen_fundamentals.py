#!/usr/bin/env python3
import yfinance as yf
import json
import os

def main():
    symbols = []
    if os.path.exists("trader/universe.txt"):
        with open("trader/universe.txt", "r") as f:
            symbols = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    
    # Fallback if universe file is empty/missing
    if not symbols:
        symbols = ["NVDA", "TSLA", "AAPL", "AMD", "META", "MSFT", "GOOGL", "AMZN", "JPM", "V", "NFLX", "AVGO", "COST", "PEP", "ADBE", "CRM", "INTC", "QCOM", "TXN"]

    # Limit to first 40 symbols to keep GitHub Action runtime fast and avoid rate limits
    symbols = symbols[:40]
    results = []

    for sym in symbols:
        try:
            info = yf.Ticker(sym).info
            pe = info.get("trailingPE")
            ps = info.get("priceToSalesTrailing12Months")
            roe = info.get("returnOnEquity")
            price = info.get("currentPrice") or info.get("regularMarketPrice")
            
            # Filter for positive earnings, reasonable P/E, and attractive P/S ratios
            if pe and ps and price and pe > 0 and ps > 0:
                results.append({
                    "symbol": sym, 
                    "price": price, 
                    "pe": round(pe, 2), 
                    "ps": round(ps, 2), 
                    "roe": round(roe * 100, 1) if roe else 0
                })
        except Exception:
            continue
    
    # Sort by lowest Price-to-Sales (best fundamental value alignment)
    results.sort(key=lambda x: x["ps"])
    
    out = ["=== BROAD MARKET VALUE & GARP PROSPECTS ==="]
    for r in results[:8]:
        out.append(f"${r['symbol']:<6} | Price: ${r['price']:>7.2f} | P/E: {r['pe']:>6.1f} | P/S: {r['ps']:>5.2f} | ROE: {r['roe']}%")
    
    if len(out) == 1:
        out.append("No fundamental metrics retrieved in this batch.")

    text_output = "\n".join(out)
    with open("fundamentals_out.txt", "w") as f:
        f.write(text_output)
    print(text_output)

if __name__ == "__main__":
    main()
