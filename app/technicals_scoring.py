from .models import Technicals, TrendDirection, AlgoSignal, RiskLevel, ScoreDetail
from .logger import pipeline_logger

def calculate_algo_signal(technicals: Technicals) -> AlgoSignal:
    """Institutional Probabilistic Edge Engine (v19.0-ALPHA)"""
    
    # --- 1. DATA GATES ---
    if technicals.rsi is None or technicals.macd_histogram is None or technicals.ema_50 is None:
        return _empty_signal()

    def clamp(val, min_v, max_v): return max(min_v, min(max_v, val))

    # --- 2. REGIME CLASSIFICATION ---
    adx_val = technicals.adx or 0.0
    is_trending = adx_val >= 20.0
    atr_pct = technicals.atr_percent or 0.0
    
    # --- 3. BAYESIAN P_WIN CALCULATION ---
    # We estimate P(Win) based on the regime
    p_win = 0.50 # Bayesian Prior (Coin Flip)
    regime_desc = ""

    if is_trending:
        regime_desc = "Trend Following"
        # Trend Confirmation
        if technicals.trend_structure == TrendDirection.BULLISH: p_win += 0.15
        if technicals.ema_50 is not None and technicals.ema_200 is not None:
            if technicals.ema_50 > technicals.ema_200: p_win += 0.10
        # Momentum Alignment
        if technicals.macd_histogram > 0: p_win += 0.05
        # Over-extension Risk
        if technicals.rsi > 75: p_win -= 0.10 
    else:
        regime_desc = "Mean Reversion / Range"
        # Mean Reversion Edge (RSI/BB stretch)
        if technicals.rsi < 30: p_win += 0.15
        if technicals.bb_position and technicals.bb_position < 0.1: p_win += 0.10
        # Counter-trend Momentum penalty
        if technicals.macd_histogram < -2.0: p_win -= 0.10

    # Volatility Penalty
    if atr_pct > 3.5: p_win -= 0.15
    
    p_win = clamp(p_win, 0.1, 0.9)

    # --- 4. EXPECTANCY (EV) CALCULATION ---
    # We assume a target R:R of 2.0 for the model's baseline expectancy
    target_rr = 2.0
    ev = (p_win * target_rr) - (1 - p_win)
    
    # --- 5. DYNAMIC WEIGHTING (Opportunity vs Regime) ---
    opportunity_score = (p_win - 0.5) * 200 # Normalized to -100 to 100
    
    # Stability Score (Penalty Vector)
    stability = clamp((2.5 - atr_pct) * 40, -100, 100)
    
    # --- 6. FINAL ALPHA ALLOCATION ---
    overall_val = opportunity_score * 0.7 + stability * 0.3
    
    # Confluence (Audit Fix: Directional Agreement)
    confluence_score = int(p_win * 10) # 0 to 10 scale

    # Forensic Trace
    pipeline_logger.log_payload("N/A", "LAYER_2", "ALPHA_EXPECTANCY_BREAKDOWN", {
        "regime": regime_desc,
        "p_win": round(p_win, 4),
        "expectancy_ev": round(ev, 4),
        "opportunity_score": opportunity_score
    })

    # Labels
    trend_lbl = "Strong Trend" if adx_val > 30 else ("Weak Trend" if is_trending else "Mean Reversion")
    mom_lbl = "High Prob" if p_win > 0.65 else ("Speculative" if p_win > 0.5 else "Low Prob")
    
    return AlgoSignal(
        overall_score=ScoreDetail(value=float(overall_val), min_value=-100.0, max_value=100.0, label=regime_desc, legend=f"EV: {ev:.2f}"),
        trend_score=ScoreDetail(value=float(adx_val), min_value=0, max_value=100, label=trend_lbl, legend="ADX Intensity"),
        momentum_score=ScoreDetail(value=float(opportunity_score), min_value=-100, max_value=100, label=mom_lbl, legend="Normalized P_Win"),
        volatility_score=ScoreDetail(value=float(stability), min_value=-100, max_value=100, label="Stable" if stability > 0 else "High Risk", legend=""),
        volume_score=ScoreDetail(value=float(ev), min_value=-1, max_value=2, label="Expectancy", legend="Expected R:R"),
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

def calculate_algo_signal_old(technicals: Technicals) -> AlgoSignal:
    """Calculate algorithmic trading signals with Invariant Quant Math (v17.0)"""

    # --- 2. Trend Score (ADX Gated) ---
    trend_val = 0.0
    adx_val = technicals.adx if technicals.adx is not None else 0.0
    
    # ADX Dampening: Square law to aggressively punish low-trend regimes
    adx_dampening = min((adx_val / 20.0) ** 2, 1.0)

    if adx_val >= 20.0:
        struct_score = 100 if technicals.trend_structure == TrendDirection.BULLISH else (-100 if technicals.trend_structure == TrendDirection.BEARISH else 0)
        ma_score = 0
        if technicals.ema_50 and technicals.ema_200:
            ma_score = 100 if technicals.ema_50 > technicals.ema_200 else -100
        
        adx_strength = min(adx_val / 40.0, 1.0)
        trend_val = (struct_score * 0.8 + ma_score * 0.2) * adx_strength
    
    # --- 3. Momentum Score (ADX Dampened) ---
    rsi_score = clamp((technicals.rsi - 50) * 2, -100, 100)
    macd_score = 0
    if technicals.macd_histogram is not None:
        base_macd = 25 if technicals.macd_histogram > 0 else -25
        if technicals.macd_signal and abs(technicals.macd_histogram) > abs(technicals.macd_signal):
             base_macd *= 2
        macd_score = base_macd

    # Weighted Momentum Aggregate
    if technicals.cci is not None:
        momentum_raw = (rsi_score * 0.4) + (macd_score * 0.3) + (clamp(technicals.cci, -100, 100) * 0.3)
    else:
        momentum_raw = (rsi_score * 0.6) + (macd_score * 0.4)
        
    # Momentum is noise if trend is invalid (Audit Fix)
    momentum_val = momentum_raw * adx_dampening

    # --- 4. Volatility Score (Invariant Penalty Vector) ---
    # Positive = Stability, Negative = Risk
    volatility_val = 0.0
    if technicals.atr_percent is not None:
        volatility_val = clamp((2.0 - technicals.atr_percent) * 50, -100, 100)
    
    # --- 5. Volume Score ---
    volume_val = 0.0
    if technicals.volume_ratio is not None:
        volume_val = clamp((technicals.volume_ratio - 1.0) * 100, -100, 100)

    # --- 6. Orthogonal Scoring (Audit Fix) ---
    # Split Signal Strength (Opportunity) from Tradeability (Regime)
    opportunity_score = (trend_val * 0.5 + momentum_val * 0.5)
    regime_score = (volatility_val * 0.7 + volume_val * 0.3)
    
    overall_val = clamp((opportunity_score * 0.6 + regime_score * 0.4), -100, 100)
    
    # --- 7. Real Confluence (Sign Consensus) ---
    signs = []
    for v in [trend_val, momentum_val, volume_val]:
        if abs(v) > 10: signs.append(1 if v > 0 else -1)
    
    # Confluence = Ratio of agreement scaled 0-10
    confluence_score = int((len([s for s in signs if s == signs[0]]) / len(signs)) * 10) if len(signs) >= 2 else 0

    # Forensic Math Logging
    math_trace = {
        "adx_dampening": round(adx_dampening, 4),
        "opportunity": {"val": round(opportunity_score, 2), "trend": round(trend_val, 2), "momentum": round(momentum_val, 2)},
        "regime": {"val": round(regime_score, 2), "volatility": round(volatility_val, 2), "volume": round(volume_val, 2)},
        "confluence_consensus": confluence_score
    }
    pipeline_logger.log_payload("N/A", "LAYER_2", "QUANT_MATH_BREAKDOWN", math_trace)

    # Labels - CANONICAL SEMANTICS
    trend_lbl = "Trending" if adx_val >= 20 else "Range/Chop"
    mom_lbl = "Bullish" if momentum_val > 20 else ("Bearish" if momentum_val < -20 else "Stall")
    vol_lbl = "Stable" if volatility_val > 0 else "Risky (High Vol)"
    vol_score_lbl = "High Liquidity" if volume_val > 0 else "Low Liquidity"
    
    overall_lbl = "Strong Buy" if overall_val > 60 else (
        "Buy" if overall_val > 20 else (
        "Strong Sell" if overall_val < -60 else (
        "Sell" if overall_val < -20 else "No Signal")))

    atr_val = technicals.atr_percent if technicals.atr_percent is not None else 0
    
    return AlgoSignal(
        overall_score=ScoreDetail(value=float(overall_val), min_value=-100.0, max_value=100.0, label=overall_lbl, legend="-100 to +100 (Weighted Aggregate)"),
        trend_score=ScoreDetail(value=float(trend_val), min_value=-100.0, max_value=100.0, label=trend_lbl, legend="Trend Strength"),
        momentum_score=ScoreDetail(value=float(momentum_val), min_value=-100.0, max_value=100.0, label=mom_lbl, legend="Momentum Strength"),
        volatility_score=ScoreDetail(value=float(volatility_val), min_value=-100.0, max_value=100.0, label=vol_lbl, legend="Stability Score"),
        volume_score=ScoreDetail(value=float(volume_val), min_value=-100.0, max_value=100.0, label=vol_score_lbl, legend="Volume Flow"),
        volatility_risk=RiskLevel.LOW if atr_val < 1.5 else (RiskLevel.MODERATE if atr_val < 3.0 else RiskLevel.HIGH),
        trend_strength="Strong" if technicals.adx is not None and technicals.adx > 25 else "Weak",
        confluence_score=confluence_score
    )