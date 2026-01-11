import yfinance as yf
import pandas as pd
import numpy as np
import math
from typing import List, Optional
from datetime import datetime, timedelta
from cachetools import cached, TTLCache
from .models import MarketContext, AnalystRating, InsiderTrade, OptionSentiment, AnalystPriceTarget, AnalystConsensus, UpcomingEvents

def sanitize(val):
    """Convert NaN/Inf floats to None for JSON compliance"""
    if val is None: return None
    if isinstance(val, float) and (math.isnan(val) or np.isnan(val) or math.isinf(val)):
        return None
    return val

@cached(cache=TTLCache(maxsize=128, ttl=300))
def get_market_context(ticker: str) -> MarketContext:
    # Per-request ticker instance for thread safety
    stock = yf.Ticker(ticker)
    context = MarketContext(ticker=ticker.upper())
    
    # 1. Analyst Ratings (Upgrades/Downgrades History)
    try:
        upgrades = stock.upgrades_downgrades
        if upgrades is not None and not upgrades.empty:
            # Get latest 10 to filter from
            latest = upgrades.tail(10).sort_index(ascending=False)
            cutoff_date = datetime.now().date() - timedelta(days=730) # 2 years
            
            for idx, row in latest.iterrows():
                try:
                    rating_date = idx.date() if hasattr(idx, 'date') else datetime.strptime(str(idx).split(' ')[0], '%Y-%m-%d').date()
                    
                    if rating_date < cutoff_date:
                        continue # Skip stale ratings
                        
                    date_str = str(rating_date)
                    
                    context.analyst_ratings.append(AnalystRating(
                        firm=str(row['Firm']),
                        to_grade=str(row['ToGrade']),
                        action=str(row['Action']),
                        date=date_str
                    ))
                except Exception as e:
                    from .logger import pipeline_logger
                    pipeline_logger.log_error(ticker, "CONTEXT", f"Individual Rating Row failure: {e}")
                    continue
    except Exception as e:
        from .logger import pipeline_logger
        pipeline_logger.log_error(ticker, "CONTEXT", f"Analyst Ratings block failure: {e}")
        pass 

    # 2. Analyst Price Targets
    try:
        targets = stock.analyst_price_targets
        if targets is not None:
            context.price_target = AnalystPriceTarget(
                current=sanitize(targets.get('current')),
                high=sanitize(targets.get('high')),
                low=sanitize(targets.get('low')),
                mean=sanitize(targets.get('mean')),
                median=sanitize(targets.get('median'))
            )
    except Exception as e:
        from .logger import pipeline_logger
        pipeline_logger.log_error(ticker, "CONTEXT", f"Price Targets failure: {e}")
        pass

    # 3. Consensus (Votes)
    try:
        rec_summary = stock.recommendations_summary
        if rec_summary is not None and not rec_summary.empty:
            # Take the current month (first row, usually period='0m')
            curr = rec_summary.iloc[0]
            context.consensus = AnalystConsensus(
                period=str(curr.get('period', '0m')),
                strong_buy=int(curr.get('strongBuy', 0)),
                buy=int(curr.get('buy', 0)),
                hold=int(curr.get('hold', 0)),
                sell=int(curr.get('sell', 0)),
                strong_sell=int(curr.get('strongSell', 0))
            )
    except Exception as e:
        from .logger import pipeline_logger
        pipeline_logger.log_error(ticker, "CONTEXT", f"Consensus failure: {e}")
        pass

    # 4. Earnings / Events
    try:
        cal = stock.calendar
        if cal:
            def get_cal_val(key):
                val = cal.get(key)
                if isinstance(val, list) and len(val) > 0: return val[0]
                return val

            earnings_dates = get_cal_val("Earnings Date")
            next_date = str(earnings_dates[0]) if isinstance(earnings_dates, list) and len(earnings_dates) > 0 else str(earnings_dates)

            context.events = UpcomingEvents(
                earnings_date=next_date,
                earnings_avg_estimate=sanitize(get_cal_val("Earnings Average")),
                earnings_low_estimate=sanitize(get_cal_val("Earnings Low")),
                earnings_high_estimate=sanitize(get_cal_val("Earnings High")),
                revenue_avg_estimate=sanitize(get_cal_val("Revenue Average"))
            )
    except Exception as e:
        from .logger import pipeline_logger
        pipeline_logger.log_error(ticker, "CONTEXT", f"Earnings/Events failure: {e}")
        pass

    # 5. Insider Activity
    try:
        insiders = stock.insider_transactions
        if insiders is not None and not insiders.empty:
            latest = insiders.head(10) # Look deeper
            material_trades = []
            
            for _, row in latest.iterrows():
                val = float(row.get('Value', 0.0) or 0.0)
                shares = int(row.get('Shares', 0) or 0)
                
                # Filter noise: Only care about > $100k or > 5000 shares
                if val < 100000 and shares < 5000:
                    continue
                    
                txn_text = row.get('Text', '')
                txn_type = "Buy" if "Purchase" in txn_text or "Buy" in txn_text else "Sell"
                
                material_trades.append(InsiderTrade(
                    date=str(row.get('Start Date', '')),
                    insider_name=row.get('Insider', 'Unknown'),
                    position=row.get('Position', ''),
                    transaction_type=txn_type,
                    shares=shares,
                    value=sanitize(val)
                ))
            
            context.insider_activity = material_trades[:5] # Keep top 5 material
    except Exception as e:
        from .logger import pipeline_logger
        pipeline_logger.log_error(ticker, "CONTEXT", f"Insider Activity failure: {e}")
        pass

    # 6. Option Sentiment
    try:
        opts = stock.options
        if opts:
            chain = stock.option_chain(opts[0])
            calls = chain.calls
            puts = chain.puts
            
            call_vol = calls['volume'].sum() if 'volume' in calls else 0
            put_vol = puts['volume'].sum() if 'volume' in puts else 0
            
            total_oi = (calls['openInterest'].sum() if 'openInterest' in calls else 0) + \
                       (puts['openInterest'].sum() if 'openInterest' in puts else 0)

            if call_vol > 0:
                pc_ratio = put_vol / call_vol
                sentiment = "Bearish" if pc_ratio > 1.0 else ("Bullish" if pc_ratio < 0.7 else "Neutral")
                
                avg_iv = calls['impliedVolatility'].mean() if 'impliedVolatility' in calls else 0.0
                
                # --- Fix #5: High Compression Flag instead of Kill-Switch ---
                iv_val = sanitize(round(avg_iv * 100, 2))
                if iv_val and iv_val > 100:
                    sentiment = f"High Compression ({sentiment})"
                # ------------------------------------------------------------

                # Identify Option Walls (Support/Resistance)
                max_call_oi = 0
                max_call_strike = 0.0
                if 'openInterest' in calls and not calls.empty:
                    idx = calls['openInterest'].idxmax()
                    max_call_strike = calls.loc[idx, 'strike']
                    
                max_put_oi = 0
                max_put_strike = 0.0
                if 'openInterest' in puts and not puts.empty:
                    idx = puts['openInterest'].idxmax()
                    max_put_strike = puts.loc[idx, 'strike']

                context.option_sentiment = OptionSentiment(
                    put_call_ratio=sanitize(round(pc_ratio, 2)),
                    implied_volatility=iv_val,
                    total_open_interest=int(total_oi),
                    sentiment=sentiment,
                    highest_call_oi_strike=sanitize(max_call_strike),
                    highest_put_oi_strike=sanitize(max_put_strike)
                )
    except Exception as e:
        from .logger import pipeline_logger
        pipeline_logger.log_error(ticker, "CONTEXT", f"Options failure: {e}")
        pass

    return context