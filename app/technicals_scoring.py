from .models import Technicals, TrendDirection, AlgoSignal, RiskLevel, ScoreDetail
from .logger import pipeline_logger

def calculate_algo_signal(technicals: Technicals) -> AlgoSignal:
    """
    Refactored Bayesian Likelihood Engine (v20.2)
    Uses Likelihood Ratios (LR) to update a Prior Probability.
    Posterior_Odds = Prior_Odds * LR1 * LR2 * ...
    """
    
    # --- 1. DATA GATES ---
    if technicals.rsi is None or technicals.macd_histogram is None or technicals.ema_50 is None:
        return get_empty_algo_signal()

    def clamp(val, min_v, max_v): return max(min_v, min(max_v, val))
    def p_to_odds(p): return p / (1 - p)
    def odds_to_p(o): return o / (1 + o)

    # --- 2. REGIME CLASSIFICATION ---
    adx_val = technicals.adx or 0.0
    is_trending = adx_val >= 20.0
    atr_pct = technicals.atr_percent or 0.0
    
    # --- 3. BAYESIAN UPDATE ENGINE ---
    # Prior Probability (Neutral baseline)
    prior_p = 0.50
    odds = p_to_odds(prior_p)
    
    regime_desc = "Trend Following" if is_trending else "Mean Reversion / Range"
    
    # Likelihood Ratios (Evidence Weights)
    if is_trending:
        # Trend Structure Alignment
        if technicals.trend_structure == TrendDirection.BULLISH: 
            odds *= 1.6 # Strong Bullish Evidence
        elif technicals.trend_structure == TrendDirection.BEARISH:
            odds *= 0.6 # Strong Bearish Evidence
            
        # Moving Average Support (Golden/Death Cross)
        if technicals.ema_50 is not None and technicals.ema_200 is not None:
            if technicals.ema_50 > technicals.ema_200: odds *= 1.25
            else: odds *= 0.8
            
        # Momentum Confirmation
        if technicals.macd_histogram > 0: odds *= 1.15
        
        # Overextension check (High RSI in trend is good, but >80 is danger)
        if technicals.rsi > 80: odds *= 0.7
        elif technicals.rsi > 60: odds *= 1.2 # Momentum strength
    else:
        # Mean Reversion Logic
        # RSI Oversold
        if technicals.rsi < 30: odds *= 1.7 # Strong Mean Reversion Signal
        elif technicals.rsi > 70: odds *= 0.6 # Overbought
        
        # Bollinger Band Position
        if technicals.bb_position is not None:
            if technicals.bb_position < 0.1: odds *= 1.4 # Bottom Band
            elif technicals.bb_position > 0.9: odds *= 0.7 # Top Band
            
        # Momentum Divergence
        if technicals.macd_histogram < -2.0: odds *= 0.8 # Falling Knife

    # Volatility Penalty (High ATR shreds probabilities)
    if atr_pct > 3.5: odds *= 0.75
    
    # Calculate Posterior Probability
    p_win = odds_to_p(odds)
    p_win = clamp(p_win, 0.1, 0.9)

    # --- 4. EXPECTANCY (EV) CALCULATION ---
    # Standard Reward:Risk of 2:1
    target_rr = 2.0
    ev = (p_win * target_rr) - (1 - p_win)
    
    # --- 5. DYNAMIC WEIGHTING ---
    # Opportunity score is centered around 50% (0 score)
    opportunity_score = (p_win - 0.5) * 200 
    stability = clamp((2.5 - atr_pct) * 40, -100, 100)
    
    overall_val = opportunity_score * 0.7 + stability * 0.3
    confluence_score = int(p_win * 10)

    # --- 6. VOLUME CLASSIFICATION ---
    v_ratio = technicals.volume_ratio or 1.0
    # Normalize volume ratio to 0-100 scale (1.0 = 50, 2.0 = 100)
    v_score_val = clamp((v_ratio - 1.0) * 50 + 50, 0, 100)
    
    if v_ratio < 0.8: v_label = "LOW"
    elif v_ratio <= 1.2: v_label = "NORMAL"
    elif v_ratio <= 1.5: v_label = "HIGH"
    else: v_label = "VERY_HIGH"

    trend_lbl = "Strong Trend" if adx_val > 30 else ("Weak Trend" if is_trending else "Mean Reversion")
    mom_lbl = "High Prob" if p_win > 0.65 else ("Speculative" if p_win > 0.5 else "Low Prob")
    
    return AlgoSignal(
        overall_score=ScoreDetail(value=float(overall_val), min_value=-100.0, max_value=100.0, label=regime_desc, legend=f"EV: {ev:.2f}"),
        trend_score=ScoreDetail(value=float(adx_val), min_value=0, max_value=100, label=trend_lbl, legend="ADX Intensity"),
        momentum_score=ScoreDetail(value=float(opportunity_score), min_value=-100, max_value=100, label=mom_lbl, legend="Normalized P_Win"),
        volatility_score=ScoreDetail(value=float(stability), min_value=-100, max_value=100, label="Stable" if stability > 0 else "High Risk", legend=""),
        volume_score=ScoreDetail(value=float(v_score_val), min_value=0, max_value=100, label=v_label, legend=f"Ratio: {v_ratio:.2f}"),
        volatility_risk=RiskLevel.LOW if atr_pct < 1.5 else (RiskLevel.MODERATE if atr_pct < 3.0 else RiskLevel.HIGH),
        trend_strength="Strong" if adx_val > 25 else "Weak",
        confluence_score=confluence_score
    )

def get_empty_algo_signal() -> AlgoSignal:
    return AlgoSignal(
        overall_score=ScoreDetail(value=0, min_value=-100, max_value=100, label="Insufficient Data", legend=""),
        trend_score=ScoreDetail(value=0, min_value=0, max_value=100, label="Unknown", legend=""),
        momentum_score=ScoreDetail(value=0, min_value=-100, max_value=100, label="Unknown", legend=""),
        volatility_score=ScoreDetail(value=0, min_value=-100, max_value=100, label="Unknown", legend=""),
        volume_score=ScoreDetail(value=0, min_value=-1, max_value=2, label="Unknown", legend=""),
        volatility_risk=RiskLevel.UNKNOWN, trend_strength="Unknown", confluence_score=0
    )
