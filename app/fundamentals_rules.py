from typing import Tuple
from .models import (
    FundamentalData, FundamentalInferences, RiskAssessment, 
    RiskLevel, SentimentDetail, InferenceDetail
)
from .settings import settings

def derive_qualitative_inferences(data: FundamentalData) -> Tuple[FundamentalInferences, RiskAssessment]:
    """Enhanced multi-factor inference engine with sector-relative benchmarking."""
    
    scores = {"val": 0, "gro": 0, "health": 0, "eff": 0, "qual": 0}
    risk_factors = []
    
    sector = data.sector if data.sector in settings.SECTOR_BENCHMARKS else "Default"
    bench = settings.SECTOR_BENCHMARKS[sector]

    # 1. Valuation
    pe = data.forward_pe or data.trailing_pe
    if pe:
        if pe < bench["pe"] * 0.6: 
            v_label, v_status = "Deep Value", "Bullish"
            v_desc = f"Significant discount to {sector} avg ({pe:.1f} vs {bench['pe']})"
            scores["val"] += 2
        elif pe < bench["pe"] * 1.2:
            v_label, v_status = "Fair Value", "Neutral"
            v_desc = f"Pricing aligns with {sector} peers"
            scores["val"] += 1
        else:
            v_label, v_status = "Premium", "Bearish"
            v_desc = f"Premium pricing relative to sector ({pe:.1f})"
            scores["val"] -= 1
    else:
        v_label, v_status = "Speculative", "Neutral"
        v_desc = "No PE available; driven by non-earnings factors"
        if (data.revenue_growth or 0) > 0.2: scores["val"] += 1

    # 2. Growth
    rev_g = data.revenue_growth or 0
    if rev_g >= settings.GROWTH_EXPLOSIVE_THRESHOLD: 
        g_label, g_status = "High Growth", "Bullish"
        g_desc = f"Strong expansion phase ({rev_g*100:.1f}%)"
        scores["gro"] += 2
    elif rev_g >= settings.GROWTH_STEADY_THRESHOLD: 
        g_label, g_status = "Steady", "Neutral"
        g_desc = f"Healthy organic expansion ({rev_g*100:.1f}%)"
        scores["gro"] += 1
    else: 
        g_label, g_status = "Stagnant", "Bearish"
        g_desc = "Revenue contraction or saturation"
        scores["gro"] -= 1

    # 3. Financial Health
    # Audit Fix: Fortress requires substantial net cash relative to size or FCF
    is_fortress = False
    if data.net_cash and data.net_cash_status == "Net Cash":
        if data.market_cap and data.net_cash > 0.25 * data.market_cap: is_fortress = True
        elif (data.free_cash_flow or 0) > 0 and data.net_cash > 1.5 * data.free_cash_flow: is_fortress = True

    if is_fortress:
        h_label, h_status = "Fortress", "Bullish"
        h_desc = f"Superior Net Cash position relative to size/FCF (${data.net_cash/1e6:.0f}M)"
        scores["health"] += 2
    elif data.net_cash_status == "Net Cash":
        h_label, h_status = "Strong", "Bullish"
        h_desc = f"Net Cash position (${data.net_cash/1e6:.0f}M)"
        scores["health"] += 1
    elif data.debt_to_equity is not None and data.debt_to_equity < bench["de"]:
        h_label, h_status = "Strong", "Bullish"
        h_desc = "Conservative leverage relative to sector"
        scores["health"] += 1
    elif (data.current_ratio or 0) >= 1.0:
        h_label, h_status = "Stable", "Neutral"
        h_desc = "Adequate liquidity"
    else:
        h_label, h_status = "Strained", "Bearish"
        h_desc = "Potential liquidity risk; current ratio < 1.0"
        scores["health"] -= 2
        risk_factors.append("Liquidity Risk: Low current ratio")

    # 4. Efficiency
    om = data.operating_margins or 0
    if om >= bench["margin"]:
        e_label, e_status = "High Efficiency", "Bullish"
        e_desc = f"Outperforming {sector} benchmarks ({om*100:.1f}%)"
        scores["eff"] += 2
    elif (data.return_on_equity or 0) < 0 and (data.revenue_growth or 0) > 0.25 and (data.gross_margins or 0) > 0.5:
        e_label, e_status = "Investment Phase", "Neutral"
        e_desc = "Margin Expansion Expected; prioritising reinvestment"
        scores["eff"] += 1
    elif (data.return_on_equity or 0) > 0:
        e_label, e_status = "Moderate", "Neutral"
        e_desc = "Standard operational performance"
    else:
        e_label, e_status = "Inefficient", "Bearish"
        e_desc = "Sub-par capital returns"
        scores["eff"] -= 1

    # 5. Earnings Quality (Audit 3.2 Fix)
    if (data.net_income or 0) < 0 and (data.free_cash_flow or 0) > 0:
        q_label = "Investment Phase Earnings"
        q_status = "Neutral"
        q_desc = "Positive FCF despite negative Net Income; typical of high-reinvestment growth phase"
        scores["qual"] += 1
    elif data.fcf_to_net_income_ratio:
        if data.fcf_to_net_income_ratio > settings.EARNINGS_QUALITY_THRESHOLD:
            q_label, q_status = "High Quality", "Bullish"
            q_desc = f"Cash-backed earnings (Ratio: {data.fcf_to_net_income_ratio:.2f})"
            scores["qual"] += 1
        else:
            q_label, q_status = "Low Quality", "Bearish"
            q_desc = "Accounting earnings not reflected in cash"
            scores["qual"] -= 1
    elif (data.free_cash_flow or 0) > 0:
        q_label, q_status = "Cash Generative", "Bullish"
        q_desc = "Positive FCF despite net income fluctuations"
        scores["qual"] += 1
    else:
        q_label, q_status = "Unverified", "Neutral"
        q_desc = "Insufficient history"

    # 7. Multi-Factor Fundamental Risk Assessment (v9.1.0 Institutional Matrix)
    # Weights for the 100-point Risk Score
    risk_weights = {
        "valuation": 0.15, "profitability": 0.15, "leverage": 0.15,
        "liquidity": 0.10, "growth_stability": 0.10, "margin_compression": 0.10,
        "capital_efficiency": 0.10, "governance": 0.10, "revenue_quality": 0.05
    }
    
    r_scores = {}
    
    # --- 1. VALUATION RISKS ---
    if not data.forward_pe: r_scores["valuation"] = 0.7
    elif data.forward_pe > settings.PE_PREMIUM_THRESHOLD: r_scores["valuation"] = 0.9
    elif data.rev_growth_adjusted_pe and data.rev_growth_adjusted_pe > 2.0: r_scores["valuation"] = 0.8
    else: r_scores["valuation"] = 0.2
    
    # --- 2. PROFITABILITY RISKS ---
    if (data.operating_margins or 0) <= 0: r_scores["profitability"] = 1.0
    elif (data.operating_margins or 0) < (bench["margin"] * 0.5): r_scores["profitability"] = 0.7
    else: r_scores["profitability"] = 0.2
    
    # --- 3. LEVERAGE RISKS ---
    if data.net_cash_status == "Net Cash": r_scores["leverage"] = 0.1
    elif (data.debt_to_equity or 0) > 2.0: r_scores["leverage"] = 0.9
    else: r_scores["leverage"] = 0.5
    
    # --- 4. LIQUIDITY RISKS ---
    if (data.current_ratio or 0) < 1.0: r_scores["liquidity"] = 1.0
    elif (data.current_ratio or 0) < 1.5: r_scores["liquidity"] = 0.6
    else: r_scores["liquidity"] = 0.1
    
    # --- 5. GROWTH & MARGIN RISKS ---
    if (data.revenue_growth or 0) < 0: r_scores["growth_stability"] = 1.0
    else: r_scores["growth_stability"] = 0.3
    
    # Margin Compression
    if (data.operating_margins or 0) < (bench["margin"] * 0.7):
        r_scores["margin_compression"] = 0.8
    else:
        r_scores["margin_compression"] = 0.2

    # --- 6. CAPITAL EFFICIENCY (NEW) ---
    roic = data.return_on_invested_capital or 0
    if roic < 0.05: r_scores["capital_efficiency"] = 0.9
    else: r_scores["capital_efficiency"] = 0.2

    # --- 7. GOVERNANCE & QUALITY (NEW) ---
    r_scores["governance"] = 0.5 # Default
    r_scores["revenue_quality"] = 0.4 if (data.fcf_to_net_income_ratio or 1) > 0.5 else 0.9

    # Weighted Total Score
    total_risk_score = sum(r_scores.get(k, 0.5) * risk_weights[k] for k in risk_weights)
    
    # Audit 9.1.0: Specific Institutional Risk Factors (Evidence-Based)
    factors = []
    # Profitability Bridge Check
    if (data.operating_margins or 0) > 0 and (data.return_on_equity or 0) < 0:
        factors.append("ROE/Margin Contradiction: Positive operations but negative equity returns.")
    
    if (data.free_cash_flow or 0) < 0: factors.append("Negative Free Cash Flow")
    if (data.operating_margins or 0) < bench["margin"]: factors.append("Sub-sector Operating Margins")
    if (data.debt_to_equity or 0) > bench["de"] * 2: factors.append("High Relative Leverage")
    if (data.current_ratio or 0) < 1.2: factors.append("Tight Liquidity Profile")
    if (data.revenue_growth or 0) < bench["growth"]: factors.append("Growth Lagging Sector")
    if (data.forward_pe or 0) > bench["pe"] * 1.5: factors.append("Significant Valuation Premium")
    if (data.held_percent_insiders or 0) < 0.01: factors.append("Low Management Alignment (Skin in game)")
    if (data.return_on_invested_capital or 0) < 0.08: factors.append("Poor Capital Efficiency (ROIC < 8%)")
    if (data.fcf_to_net_income_ratio or 1) < 0.5: factors.append("Low Accrual Quality (NI not converting to FCF)")
    if data.net_cash and data.market_cap and data.net_cash < 0.05 * data.market_cap: factors.append("Minimal Cash Buffer relative to size")
    
    # Trend-based risks
    if data.trend_analysis:
        for delta in data.trend_analysis.deltas:
            if delta.metric == "Free Cash Flow" and delta.delta_pct < -10:
                factors.append("Material FCF Contraction YoY")
            if delta.metric == "Operating Profit" and delta.delta_pct < 0 and (data.revenue_growth or 0) > 0:
                factors.append("Negative Operating Leverage (Costs outstripping revenue)")

    if total_risk_score < 0.35: r_level = RiskLevel.LOW
    elif total_risk_score < 0.55: r_level = RiskLevel.MODERATE
    elif total_risk_score < 0.75: r_level = RiskLevel.HIGH
    else: r_level = RiskLevel.VERY_HIGH

    # Fixed: Cumulative Risk Factor Tracking
    risk_factors = factors # Direct assignment of our expanded matrix

    # Signal Integrity Check: Trend vs Reality (Audit 3.3)
    conf_label = "High"
    if data.trend_analysis and data.trend_analysis.trajectory == "Accelerating":
        if (data.return_on_equity or 0) < 0 or (data.operating_margins or 0) < (bench["margin"] * 0.5):
            conf_label = "Medium (Trend/Margin Mismatch)"
            if "Fundamental Contradiction: Scaling but Unprofitable" not in risk_factors:
                risk_factors.append("Fundamental Contradiction: Scaling but Unprofitable")

    inferences = FundamentalInferences(
        valuation=InferenceDetail(label=v_label, status=v_status, description=v_desc),
        growth=InferenceDetail(label=g_label, status=g_status, description=g_desc),
        health=InferenceDetail(label=h_label, status=h_status, description=h_desc),
        efficiency=InferenceDetail(label=e_label, status=e_status, description=e_desc),
        earnings_quality=InferenceDetail(label=q_label, status=q_status, description=q_desc),
        capital_allocation=InferenceDetail(
            label="Income" if data.dividend_yield else "Growth",
            status="Bullish" if data.dividend_yield else "Neutral",
            description=f"Yield: {data.dividend_yield*100:.1f}%" if data.dividend_yield else "Reinvesting for growth"
        ),
        ownership_structure=InferenceDetail(
            label="Crowded" if (data.held_percent_institutions or 0) > 0.8 else "Available",
            status="Neutral",
            description=f"Institutional: {(data.held_percent_institutions or 0)*100:.1f}%"
        ),
        overall_sentiment=SentimentDetail(label="Neutral", score=0, confidence=conf_label) 
    )
    
    risk = RiskAssessment(
        level=r_level, score=int(total_risk_score * 100), factors=risk_factors
    )
    
    return inferences, risk
