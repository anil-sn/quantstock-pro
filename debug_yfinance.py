import yfinance as yf
import pandas as pd

tickers = ["RELIANCE.NS", "ZOMATO.NS", "AAPL"]

for t in tickers:
    print(f"\n--- Testing {t} ---")
    stock = yf.Ticker(t)
    
    # Test 1: History
    print(f"Testing History (period='1y', interval='1d')...")
    hist = stock.history(period="1y", interval="1d")
    print(f"Rows: {len(hist)}")
    
    # Test 2: Info
    print(f"Testing Info...")
    try:
        info = stock.info
        print(f"Info keys: {len(info) if info else 0}")
    except Exception as e:
        print(f"Info Error: {e}")

    # Test 3: Financials
    print(f"Testing Financials...")
    try:
        fin = stock.income_stmt
        print(f"Financials rows: {len(fin) if not fin.empty else 0}")
    except Exception as e:
        print(f"Financials Error: {e}")
