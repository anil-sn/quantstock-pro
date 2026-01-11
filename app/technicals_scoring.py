from .models import Technicals, TrendDirection, AlgoSignal, RiskLevel, ScoreDetail
from .logger import pipeline_logger

def calculate_algo_signal(technicals: Technicals) -> AlgoSignal:
    """Institutional Probabilistic Edge Engine (v19.2-BETA)"""
    
    # --- 1. DATA GATES ---
    if technicals.rsi is None or technicals.macd_histogram is None or technicals.ema_50 is None:
        return _empty_signal()

    def clamp(val, min_v, max_v): return max(min_v, min(max_v, val))

    # --- 2. REGIME CLASSIFICATION ---
    adx_val = technicals.adx or 0.0
    is_trending = adx_val >= 20.0
    atr_pct = technicals.atr_percent or 0.0
    
    # --- 3. BAYESIAN P_WIN CALCULATION ---
    p_win = 0.50 
    regime_desc = "Trend Following" if is_trending else "Mean Reversion / Range"

    if is_trending:
        if technicals.trend_structure == TrendDirection.BULLISH: p_win += 0.15
        if technicals.ema_50 is not None and technicals.ema_200 is not None:
            if technicals.ema_50 > technicals.ema_200: p_win += 0.10
        if technicals.macd_histogram > 0: p_win += 0.05
        if technicals.rsi > 75: p_win -= 0.10 
    else:
        if technicals.rsi < 30: p_win += 0.15
        if technicals.bb_position and technicals.bb_position < 0.1: p_win += 0.10
        if technicals.macd_histogram < -2.0: p_win -= 0.10

    if atr_pct > 3.5: p_win -= 0.15
    p_win = clamp(p_win, 0.1, 0.9)

    # --- 4. EXPECTANCY (EV) CALCULATION ---
    target_rr = 2.0
    ev = (p_win * target_rr) - (1 - p_win)
    
    # --- 5. DYNAMIC WEIGHTING ---
    opportunity_score = (p_win - 0.5) * 200 
    stability = clamp((2.5 - atr_pct) * 40, -100, 100)
    
    overall_val = opportunity_score * 0.7 + stability * 0.3
    confluence_score = int(p_win * 10)

    # --- 6. VOLUME CLASSIFICATION (Audit Fix: Z-Score Mapping) ---
    v_ratio = technicals.volume_ratio or 1.0
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
        volume_score=ScoreDetail(value=float(ev), min_value=-1, max_value=2, label=v_label, legend="Expected R:R"),
        volatility_risk=RiskLevel.LOW if atr_pct < 1.5 else (RiskLevel.MODERATE if atr_pct < 3.0 else RiskLevel.HIGH),
        trend_strength="Strong" if adx_val > 25 else "Weak",
        confluence_score=confluence_score
    )

def _empty_signal() -> AlgoSignal:
    return AlgoSignal(
        overall_score=ScoreDetail(value=0, min_value=-100, max_value=100, label="Insufficient Data", legend=""),
        trend_score=ScoreDetail(value=0, min_value=0, max_value=100, label="Unknown", legend=""),
        momentum_score=ScoreDetail(value=0, min_value=-100, max_value=100, label="Unknown", legend=""),
        volatility_score=ScoreDetail(value=0, min_value=-100, max_value=100, label="Unknown", legend=""),
        volume_score=ScoreDetail(value=0, min_value=-1, max_value=2, label="Unknown", legend=""),
        volatility_risk=RiskLevel.UNKNOWN, trend_strength="Unknown", confluence_score=0
    )
