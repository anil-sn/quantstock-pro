from typing import Any
import pandas as pd
import pandas_ta as ta
import numpy as np
from .models import Technicals, TrendDirection, AlgoSignal, RiskLevel, ScoreDetail

def calculate_advanced_technicals(df: pd.DataFrame) -> Technicals:
    """Calculate comprehensive technical indicators"""
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
    
    # Check Price vs EMAs
    above_all = price > ema20 and price > ema50 and price > ema200
    below_all = price < ema20 and price < ema50 and price < ema200
    
    if above_all:
        ema_trend = "Bullish"
    elif below_all:
        ema_trend = "Bearish"
    elif price > ema200 and ema50 > ema200:
        ema_trend = "Bullish" # Structural uptrend holding
    elif price < ema200 and ema50 < ema200:
        ema_trend = "Bearish" # Structural downtrend
    else:
        ema_trend = "Neutral"
    
    return Technicals(
        rsi=float(latest['RSI']),
        rsi_signal=TrendDirection.BULLISH if latest['RSI'] < 30 else (TrendDirection.BEARISH if latest['RSI'] > 70 else TrendDirection.NEUTRAL),
        macd_line=float(latest['MACD']),
        macd_signal=float(latest['MACD_Signal']),
        macd_histogram=float(latest['MACD_Histogram']),
        adx=float(latest['ADX']),
        atr=float(latest['ATR']),
        atr_percent=float(latest['ATR_Percent']),
        cci=float(latest['CCI']),
        bb_upper=float(latest['BB_Upper']),
        bb_middle=float(latest['BB_Middle']),
        bb_lower=float(latest['BB_Lower']),
        bb_position=float(latest['BB_Position']),
        support_s1=float(s1),
        support_s2=float(s2),
        resistance_r1=float(r1),
        resistance_r2=float(r2),
        volume_avg_20d=float(latest['Volume_MA_20']),
        volume_current=float(latest['Volume']),
        volume_ratio=float(latest['Volume_Ratio']),
        ema_20=float(latest['EMA_20']),
        ema_50=float(latest['EMA_50']),
        ema_200=float(latest['EMA_200']),
        trend_structure=TrendDirection(ema_trend)
    )

def calculate_algo_signal(technicals: Technicals) -> AlgoSignal:
    """Calculate algorithmic trading signals based on technicals"""
    # Trend score
    trend_val = (
        (1 if technicals.trend_structure == TrendDirection.BULLISH else -1) * 30 +
        (1 if technicals.ema_50 > technicals.ema_200 else -1) * 20 +
        (technicals.adx / 100) * 20
    )
    trend_score = ScoreDetail(
        value=float(trend_val),
        min_value=-100.0,
        max_value=100.0,
        label="Bullish" if trend_val > 0 else "Bearish",
        legend="-100 to +100 (Negative = Bearish, Positive = Bullish)"
    )
    
    # Momentum score
    momentum_val = (
        (70 - technicals.rsi) * 0.5 +
        technicals.macd_histogram * 10 +
        technicals.cci / 10
    )
    momentum_score = ScoreDetail(
        value=float(momentum_val),
        min_value=-500.0,
        max_value=500.0,
        label="Strong" if abs(momentum_val) > 100 else "Moderate",
        legend="Typical range -500 to +500 (Directional strength)"
    )
    
    # Volatility score
    # Lower ATR % = More stable = Higher score
    volatility_val = 100 - (technicals.atr_percent * 20) # Sharper penalty
    volatility_val = max(-100, min(100, volatility_val))
    
    vol_label = "High Stability" if technicals.atr_percent < 1.5 else ("Moderate" if technicals.atr_percent < 3.0 else "High Volatility / Unstable")
    
    volatility_score = ScoreDetail(
        value=float(volatility_val),
        min_value=-100.0,
        max_value=100.0,
        label=vol_label,
        legend="-100 to +100 (Higher = More Price Stability)"
    )
    
    # Volume score
    volume_val = 20 if technicals.volume_ratio > 1.2 else (0 if technicals.volume_ratio > 0.8 else -10)
    volume_score = ScoreDetail(
        value=float(volume_val),
        min_value=-20.0,
        max_value=20.0,
        label="High Volume" if volume_val > 0 else "Low Volume",
        legend="-20 to +20 (Positive = Above average volume accumulation)"
    )
    
    overall_val = int(trend_val * 0.3 + momentum_val * 0.3 + volatility_val * 0.2 + volume_val * 0.2)
    overall_score = ScoreDetail(
        value=float(overall_val),
        min_value=-100.0,
        max_value=100.0,
        label="Strong Buy" if overall_val > 30 else ("Strong Sell" if overall_val < -30 else "Hold"),
        legend="-100 to +100 (Final weighted aggregate signal)"
    )
    
    return AlgoSignal(
        overall_score=overall_score,
        trend_score=trend_score,
        momentum_score=momentum_score,
        volatility_score=volatility_score,
        volume_score=volume_score,
        volatility_risk=RiskLevel.LOW if technicals.atr_percent < 1.5 else (RiskLevel.MODERATE if technicals.atr_percent < 3.0 else RiskLevel.HIGH),
        trend_strength="Strong" if technicals.adx > 25 else "Weak"
    )

def build_snapshot(df: pd.DataFrame) -> Any:
    """Compatibility wrapper for build_snapshot if needed, but preferred to use advanced technicals"""
    return calculate_advanced_technicals(df)
