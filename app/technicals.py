from typing import Any, Optional
import pandas as pd
import pandas_ta as ta
import numpy as np
from .models import Technicals, TrendDirection, AlgoSignal, RiskLevel, ScoreDetail

def calculate_advanced_technicals(df: pd.DataFrame) -> Technicals:
    """Calculate comprehensive technical indicators with Poison Detection"""
    df = df.copy()
    
    # Basic indicators
    df['RSI'] = ta.rsi(df['Close'], length=14)
    
    # MACD
    macd = ta.macd(df['Close'], fast=12, slow=26, signal=9)
    macd_col = [c for c in macd.columns if c.startswith('MACD_')][0]
    macd_s_col = [c for c in macd.columns if c.startswith('MACDs_')][0]
    macd_h_col = [c for c in macd.columns if c.startswith('MACDh_')][0]
    
    df['MACD'] = macd[macd_col]
    df['MACD_Signal'] = macd[macd_s_col]
    df['MACD_Histogram'] = macd[macd_h_col]
    
    # ADX
    adx = ta.adx(df['High'], df['Low'], df['Close'], length=14)
    adx_col = [c for c in adx.columns if c.startswith('ADX_')][0]
    df['ADX'] = adx[adx_col]
    
    # ATR
    df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
    df['ATR_Percent'] = (df['ATR'] / df['Close']) * 100
    
    # CCI
    df['CCI'] = ta.cci(df['High'], df['Low'], df['Close'], length=20)
    
    # Bollinger Bands
    bb = ta.bbands(df['Close'], length=20, std=2)
    
    # Robustly find columns by prefix
    bbu_col = [c for c in bb.columns if c.startswith('BBU')][0]
    bbm_col = [c for c in bb.columns if c.startswith('BBM')][0]
    bbl_col = [c for c in bb.columns if c.startswith('BBL')][0]
    
    df['BB_Upper'] = bb[bbu_col]
    df['BB_Middle'] = bb[bbm_col]
    df['BB_Lower'] = bb[bbl_col]
    df['BB_Position'] = (df['Close'] - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'])
    
    # Moving Averages
    df['EMA_20'] = ta.ema(df['Close'], length=20)
    df['EMA_50'] = ta.ema(df['Close'], length=50)
    df['EMA_200'] = ta.ema(df['Close'], length=200)
    
    # Volume
    df['Volume_MA_20'] = df['Volume'].rolling(20).mean()
    df['Volume_Ratio'] = df['Volume'] / df['Volume_MA_20']
    
    # Pivot Points
    latest = df.iloc[-1]
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
    adx = latest['ADX'] if not pd.isna(latest['ADX']) else 0
    
    # Check Price vs EMAs
    above_all = price > ema20 and price > ema50 and price > ema200
    below_all = price < ema20 and price < ema50 and price < ema200
    
    # --- Fix #3: ADX Gated Trend ---
    if adx < 20:
        ema_trend = "Neutral / Transition"
    elif above_all:
        ema_trend = "Bullish"
    elif below_all:
        ema_trend = "Bearish"
    elif price > ema200 and ema50 > ema200:
        ema_trend = "Bullish" # Structural uptrend holding
    elif price < ema200 and ema50 < ema200:
        ema_trend = "Bearish" # Structural downtrend
    else:
        ema_trend = "Neutral"

    # --- POISON DETECTION & HARD NULLING ---
    # CCI Poison Check
    cci_val = float(latest['CCI'])
    if abs(cci_val) > 500 or pd.isna(cci_val):
        cci_final = None
    else:
        cci_final = cci_val
        
    # Volume Poison Check
    vol_ratio_val = float(latest['Volume_Ratio'])
    if vol_ratio_val < 0 or vol_ratio_val > 50 or pd.isna(vol_ratio_val):
        vol_ratio_final = None
    else:
        vol_ratio_final = vol_ratio_val
        
    # Helper to safely float or None
    def safe_float(val):
        return float(val) if not pd.isna(val) else None

    return Technicals(
        rsi=safe_float(latest['RSI']),
        rsi_signal=TrendDirection.BULLISH if latest['RSI'] < 30 else (TrendDirection.BEARISH if latest['RSI'] > 70 else TrendDirection.NEUTRAL),
        macd_line=safe_float(latest['MACD']),
        macd_signal=safe_float(latest['MACD_Signal']),
        macd_histogram=safe_float(latest['MACD_Histogram']),
        adx=safe_float(latest['ADX']),
        atr=safe_float(latest['ATR']),
        atr_percent=safe_float(latest['ATR_Percent']),
        cci=cci_final, # Hard Null if poisoned
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
        volume_ratio=vol_ratio_final, # Hard Null if poisoned
        ema_20=safe_float(latest['EMA_20']),
        ema_50=safe_float(latest['EMA_50']),
        ema_200=safe_float(latest['EMA_200']),
        trend_structure=TrendDirection(ema_trend)
    )

def calculate_algo_signal(technicals: Technicals) -> AlgoSignal:
    """Calculate algorithmic trading signals with Strict Null Handling"""
    
    def norm(val, current_min, current_max):
        if val is None: return 0
        if current_max == current_min: return 0
        normalized = -100 + (val - current_min) * (200) / (current_max - current_min)
        return max(-100, min(100, normalized))

    # --- Indicator Health Check ---
    # If a value is None, it contributes 0 weight.
    valid_weights = 0.0
    
    # 1. Trend Score
    trend_val = 0.0
    trend_weight = 0.35
    
    if technicals.adx is not None and technicals.ema_50 is not None and technicals.ema_200 is not None:
        trend_raw = (
            (1 if technicals.trend_structure == TrendDirection.BULLISH else -1) * 40 +
            (1 if technicals.ema_50 > technicals.ema_200 else -1) * 40 +
            (technicals.adx / 100) * 20
        )
        trend_val = max(-100, min(100, trend_raw))
        valid_weights += trend_weight
    
    # 2. Momentum Score
    momentum_val = 0.0
    momentum_weight = 0.35
    
    # Check dependencies
    has_rsi = technicals.rsi is not None
    has_macd = technicals.macd_histogram is not None
    has_cci = technicals.cci is not None
    
    if has_rsi and has_macd:
        # Base momentum
        momentum_raw = (70 - technicals.rsi) * 0.5 + technicals.macd_histogram * 10
        
        # Add CCI if valid
        if has_cci:
            momentum_raw += (technicals.cci / 2)
            # Full weight
            momentum_val = norm(momentum_raw, -200, 200)
            valid_weights += momentum_weight
        else:
            # Partial weight (Degraded Momentum)
            momentum_val = norm(momentum_raw, -100, 100)
            valid_weights += (momentum_weight * 0.6) # Penalize for missing CCI

    # 3. Volatility Score
    vol_weight = 0.15
    volatility_val = 0.0
    if technicals.atr_percent is not None:
        volatility_val = norm(100 - (technicals.atr_percent * 20), -100, 100)
        valid_weights += vol_weight
    
    # 4. Volume Score
    vol_score_weight = 0.15
    volume_val = 0.0
    if technicals.volume_ratio is not None:
        volume_raw = (technicals.volume_ratio - 1.0) * 50
        volume_val = max(-50, min(50, volume_raw))
        valid_weights += vol_score_weight

    # 5. Weighted Aggregation (Normalized by valid weights)
    if valid_weights > 0.1: # Minimum threshold to even score
        overall_val = (
            trend_val * trend_weight + 
            momentum_val * momentum_weight + 
            volatility_val * vol_weight + 
            volume_val * vol_score_weight
        ) / valid_weights
    else:
        overall_val = 0

    # Final Clamp
    overall_val = max(-100, min(100, overall_val))
    
    # Confluence Scorecard (0-10)
    confluence_score = 0
    if technicals.trend_structure in [TrendDirection.BULLISH, TrendDirection.BEARISH]: confluence_score += 3
    
    if technicals.bb_position is not None:
        if technicals.bb_position < 0.1 or technicals.bb_position > 0.9: confluence_score += 3
        elif technicals.bb_position < 0.2 or technicals.bb_position > 0.8: confluence_score += 2
        
    if technicals.cci is not None and abs(technicals.cci) > 150: confluence_score += 2
    if technicals.volume_ratio is not None and technicals.volume_ratio > 1.2: confluence_score += 2
    
    # Override: High Confluence forces conviction
    if confluence_score >= 7 and abs(overall_val) < 50:
        boost = 30 if overall_val >= 0 else -30
        overall_val += boost

    # Labels
    trend_score = ScoreDetail(value=float(trend_val), min_value=-100.0, max_value=100.0, label="Bullish" if trend_val > 0 else "Bearish", legend="Normalized Trend strength")
    momentum_score = ScoreDetail(value=float(momentum_val), min_value=-100.0, max_value=100.0, label="Strong" if abs(momentum_val) > 50 else "Moderate", legend="Normalized Momentum")
    volatility_score = ScoreDetail(value=float(volatility_val), min_value=-100.0, max_value=100.0, label="Stable" if volatility_val > 0 else "Volatile", legend="Normalized Stability")
    volume_score = ScoreDetail(value=float(volume_val), min_value=-100.0, max_value=100.0, label="Accumulation" if volume_val > 0 else "Distribution", legend="Normalized Volume")
    
    overall_score = ScoreDetail(
        value=float(overall_val),
        min_value=-100.0,
        max_value=100.0,
        label="Strong Buy" if overall_val > 50 else ("Strong Sell" if overall_val < -50 else "Hold/Neutral"),
        legend="-100 to +100 (Final weighted aggregate signal)"
    )
    
    atr_val = technicals.atr_percent if technicals.atr_percent is not None else 0
    
    return AlgoSignal(
        overall_score=overall_score,
        trend_score=trend_score,
        momentum_score=momentum_score,
        volatility_score=volatility_score,
        volume_score=volume_score,
        volatility_risk=RiskLevel.LOW if atr_val < 1.5 else (RiskLevel.MODERATE if atr_val < 3.0 else RiskLevel.HIGH),
        trend_strength="Strong" if technicals.adx is not None and technicals.adx > 25 else "Weak",
        confluence_score=confluence_score
    )
