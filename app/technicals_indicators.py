from typing import Any, Optional
import pandas as pd
import pandas_ta as ta
import numpy as np
from .models import Technicals, TrendDirection
from .settings import settings

def calculate_advanced_technicals(df: pd.DataFrame) -> Technicals:
    """Calculate comprehensive technical indicators with Strict Data Validation"""
    print(f"DEBUG: calculate_advanced_technicals called with DF size {len(df)}")
    # --- 1. STOP THE WORLD: Data Integrity Check ---
    if df.empty or len(df) < 50:
        print(f"DEBUG: Data too shallow ({len(df)})")
        # Not enough data to calculate reliable EMA_50/200 or RSI
        return Technicals(
            rsi=None, rsi_signal=TrendDirection.NEUTRAL,
            macd_line=None, macd_signal=None, macd_histogram=None,
            adx=None, atr=None, atr_percent=None, cci=None,
            bb_upper=None, bb_middle=None, bb_lower=None, bb_position=None,
            support_s1=None, support_s2=None, resistance_r1=None, resistance_r2=None,
            volume_avg_20d=None, volume_current=None, volume_ratio=None,
            ema_20=None, ema_50=None, ema_200=None,
            trend_structure=TrendDirection.NEUTRAL
        )

    df = df.copy()
    
    # Basic indicators
    df['RSI'] = ta.rsi(df['Close'], length=14)
    
    # MACD
    macd = ta.macd(df['Close'], fast=12, slow=26, signal=9)
    if macd is not None and not macd.empty:
        macd_col = [c for c in macd.columns if c.startswith('MACD_')][0]
        macd_s_col = [c for c in macd.columns if c.startswith('MACDs_')][0]
        macd_h_col = [c for c in macd.columns if c.startswith('MACDh_')][0]
        
        df['MACD'] = macd[macd_col]
        df['MACD_Signal'] = macd[macd_s_col]
        df['MACD_Histogram'] = macd[macd_h_col]
    else:
        df['MACD'] = None
        df['MACD_Signal'] = None
        df['MACD_Histogram'] = None
    
    # ADX
    adx = ta.adx(df['High'], df['Low'], df['Close'], length=14)
    if adx is not None and not adx.empty:
        adx_col = [c for c in adx.columns if c.startswith('ADX_')][0]
        df['ADX'] = adx[adx_col]
    else:
        df['ADX'] = None
    
    # ATR
    df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
    df['ATR_Percent'] = (df['ATR'] / df['Close']) * 100
    
    # CCI
    try:
        # 1. Try standard pandas-ta
        cci_series = ta.cci(high=df['High'], low=df['Low'], close=df['Close'], length=20)
        
        # 2. Check if result is invalid (None or all NaN)
        if cci_series is None or cci_series.isna().all():
            print("DEBUG: Primary CCI failed, triggering fallback")
            # CCI = (Typical Price - 20-period SMA of TP) / (.015 * Mean Deviation)
            tp = (df['High'] + df['Low'] + df['Close']) / 3
            sma_tp = tp.rolling(window=20).mean()
            # Mean Absolute Deviation fallback
            mad_tp = tp.rolling(window=20).apply(lambda x: np.abs(x - x.mean()).mean())
            # Replace 0 MAD with epsilon to avoid division by zero
            mad_tp = mad_tp.replace(0, 1e-9)
            cci_series = (tp - sma_tp) / (0.015 * mad_tp)
        
        # 3. Last stand: Final NaN cleanup for the series
        df['CCI'] = cci_series.fillna(0.0) 
        print(f"DEBUG: CCI column set. Latest: {df['CCI'].iloc[-1]}")
    except Exception as e:
        print(f"DEBUG: CCI Calculation Failed: {e}")
        df['CCI'] = pd.Series([0.0] * len(df)) # Absolute fallback to zeros
    
    # Bollinger Bands
    bb = ta.bbands(df['Close'], length=20, std=2)
    if bb is not None and not bb.empty:
        # Robustly find columns by prefix
        bbu_col = [c for c in bb.columns if c.startswith('BBU')][0]
        bbm_col = [c for c in bb.columns if c.startswith('BBM')][0]
        bbl_col = [c for c in bb.columns if c.startswith('BBL')][0]
        
        df['BB_Upper'] = bb[bbu_col]
        df['BB_Middle'] = bb[bbm_col]
        df['BB_Lower'] = bb[bbl_col]
        df['BB_Position'] = (df['Close'] - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'])
    else:
        df['BB_Upper'] = None
        df['BB_Middle'] = None
        df['BB_Lower'] = None
        df['BB_Position'] = None
    
    # Moving Averages
    df['EMA_20'] = ta.ema(df['Close'], length=20)
    df['EMA_50'] = ta.ema(df['Close'], length=50)
    df['EMA_200'] = ta.ema(df['Close'], length=200)
    
    # Volume
    df['Volume_MA_20'] = df['Volume'].rolling(20).mean()
    df['Volume_Ratio'] = df['Volume'] / df['Volume_MA_20']
    
    # Audit Fix: Forward fill and Fillna indicators AFTER all calculations are done
    tech_cols = ['RSI', 'MACD', 'MACD_Signal', 'MACD_Histogram', 'ADX', 'ATR', 'CCI', 'BB_Upper', 'BB_Middle', 'BB_Lower', 'EMA_20', 'EMA_50', 'EMA_200']
    df[tech_cols] = df[tech_cols].ffill().fillna(0.0)

    # --- 2. ROW EXTRACTION & FALLBACK ---
    # Extract latest row after all columns are added
    latest = df.iloc[-1]
    
    # DEBUG: Inspect latest row values
    if pd.isna(latest.get('CCI')) or latest.get('CCI') is None:
        print(f"DEBUG: Latest Row CCI is NULL. Rows in DF: {len(df)}")
        print(f"DEBUG: Last 5 CCI values:\n{df['CCI'].tail(5)}")

    # Fallback to previous row if current is incomplete (e.g. market just opened)
    if (pd.isna(latest['Close']) or pd.isna(latest.get('CCI'))) and len(df) > 1:
        latest = df.iloc[-2]

    # Pivot Points
    pivot = (latest['High'] + latest['Low'] + latest['Close']) / 3
    r1 = (2 * pivot) - latest['Low']
    r2 = pivot + (latest['High'] - latest['Low'])
    s1 = (2 * pivot) - latest['High']
    s2 = pivot - (latest['High'] - latest['Low'])
    
    # Trend determination - ROBUST VERSION
    price = latest['Close']
    ema20 = latest['EMA_20']
    ema50 = latest['EMA_50']
    ema200 = latest['EMA_200']
    adx_val = latest['ADX'] if not pd.isna(latest['ADX']) else 0
    
    # Helper to safe check comparisons
    def safe_gt(a, b): return a > b if pd.notna(a) and pd.notna(b) else False
    def safe_lt(a, b): return a < b if pd.notna(a) and pd.notna(b) else False
    
    # Check Price vs EMAs
    above_all = safe_gt(price, ema20) and safe_gt(price, ema50) and safe_gt(price, ema200)
    below_all = safe_lt(price, ema20) and safe_lt(price, ema50) and safe_lt(price, ema200)
    
    # --- Fix #3: ADX Gated Trend ---
    if adx_val < 20:
        ema_trend = "Neutral / Transition"
    elif above_all:
        ema_trend = "Bullish"
    elif below_all:
        ema_trend = "Bearish"
    elif safe_gt(price, ema200) and safe_gt(ema50, ema200):
        ema_trend = "Bullish" # Structural uptrend holding
    elif safe_lt(price, ema200) and safe_lt(ema50, ema200):
        ema_trend = "Bearish" # Structural downtrend
    else:
        ema_trend = "Neutral"

    # --- POISON DETECTION & HARD NULLING ---
    # Fix #2: CCI Hard Clamp Validation
    cci_val = latest.get('CCI')
    latest_cci = float(cci_val) if cci_val is not None and not pd.isna(cci_val) else None
    
    final_cci = None
    if latest_cci is not None:
        # Physically impossible CCI check (Typical range +/- 100, extreme +/- 300)
        if abs(latest_cci) < 5000: # Increased from 1500 after forensic trace found 3200+
            final_cci = latest_cci
        
    # Volume Poison Check
    vol_ratio_val = float(latest['Volume_Ratio']) if not pd.isna(latest['Volume_Ratio']) else None
    if vol_ratio_val is not None and (vol_ratio_val < 0 or vol_ratio_val > 100):
        vol_ratio_final = None
    else:
        vol_ratio_final = vol_ratio_val
        
    # Helper to safely float or None
    def safe_float(val):
        try:
            return float(val) if not pd.isna(val) else None
        except:
            return None

    # RSI Signal Logic (Regime Aware Mean Reversion)
    # < 30: Oversold (Potential Buy/Bullish)
    # > 70: Overbought (Potential Sell/Bearish)
    # 30-70: Neutral
    rsi_val = safe_float(latest['RSI'])
    if rsi_val is not None:
        if rsi_val < 30:
            # Audit Fix: If price is below EMA_50, oversold is a "Falling Knife" danger, not Bullish
            if safe_lt(price, ema50):
                rsi_sig = TrendDirection.NEUTRAL # Block bullish signal in breakdown
            else:
                rsi_sig = TrendDirection.BULLISH
        elif rsi_val > 70:
            rsi_sig = TrendDirection.BEARISH
        else:
            rsi_sig = TrendDirection.NEUTRAL
    else:
        rsi_sig = TrendDirection.NEUTRAL

    return Technicals(
        rsi=rsi_val,
        rsi_signal=rsi_sig,
        macd_line=safe_float(latest['MACD']),
        macd_signal=safe_float(latest['MACD_Signal']),
        macd_histogram=safe_float(latest['MACD_Histogram']),
        adx=safe_float(latest['ADX']),
        atr=safe_float(latest['ATR']),
        atr_percent=safe_float(latest['ATR_Percent']),
        cci=final_cci, 
        bb_upper=safe_float(latest['BB_Upper']),
        bb_middle=safe_float(latest['BB_Middle']),
        bb_lower=safe_float(latest['BB_Lower']),
        bb_position=safe_float(latest['BB_Position']),
        support_s1=safe_float(s1),
        support_s2=safe_float(s2),
        resistance_r1=safe_float(r1),
        resistance_r2=safe_float(r2),
        volume_avg_20d=safe_float(latest['Volume_MA_20']),
        volume_current=safe_float(latest['Volume']),
        volume_ratio=vol_ratio_final, 
        ema_20=safe_float(latest['EMA_20']),
        ema_50=safe_float(latest['EMA_50']),
        ema_200=safe_float(latest['EMA_200']),
        trend_structure=TrendDirection(ema_trend)
    )
