from typing import Dict, Any, List, Tuple
from .models import (
    FundamentalData, QualityGrade, CompositeQualityScore, 
    BusinessModelAnalysis, FundamentalInferences, InvestmentThesis,
    SentimentDetail, RiskLevel, InvestmentRecommendation, MetricItem,
    RiskAssessment
)
from .settings import settings

def calculate_quality_grade(data: FundamentalData, inferences: Any = None, sector: str = "Default") -> Tuple[CompositeQualityScore, SentimentDetail]:
    """
    Audit 9.0.0: Strict Scoring Functional Equation.
    Score = (Profit*0.30 + Growth*0.20 + Strength*0.30 + Consistency*0.20) - GovernancePenalty
    """
    raw_scores = {"profitability": 0.0, "financial_strength": 0.0, "growth": 0.0, "consistency": 0.0}
    
    bench = settings.SECTOR_BENCHMARKS.get(sector, settings.SECTOR_BENCHMARKS["Default"])
    
    # 1. PROFITABILITY (Scaled 0-100)
    p_metrics = []
    gm = data.gross_margins or 0
    om = data.operating_margins or 0
    roe = data.return_on_equity or 0
    
    p_metrics.append(min(100, (gm / 0.70) * 100)) # GM target 70%
    p_metrics.append(min(100, max(0, (om / 0.20) * 100))) # OM target 20%
    
    # ROE Neutralization for Growth Phase
    if roe < 0 and (data.revenue_growth or 0) > 0.20 and gm > 0.50:
        p_metrics.append(50.0) # Investment Phase Neutral
    else:
        p_metrics.append(min(100, max(0, (roe / 0.15) * 100)))
        
    raw_scores["profitability"] = sum(p_metrics) / len(p_metrics)
    
    # 2. GROWTH (Scaled 0-100)
    rg = data.revenue_growth or 0
    fcf_m = data.free_cash_flow_margin or 0
    g_score = min(100, (rg / 0.40) * 100)
    if fcf_m < 0: g_score *= 0.8 # Penalty for cash-burn growth
    raw_scores["growth"] = g_score
    
    # 3. FINANCIAL STRENGTH (Scaled 0-100)
    s_metrics = []
    if data.net_cash_status == "Net Cash" and data.market_cap:
        nc_pct = data.net_cash / data.market_cap
        s_metrics.append(min(100, (nc_pct / 0.25) * 100)) # 25% MC Net Cash = 100
    else:
        cr = data.current_ratio or 1.0
        s_metrics.append(min(100, (cr / 2.0) * 100))
        
    raw_scores["financial_strength"] = sum(s_metrics) / len(s_metrics)
    
    # 4. CONSISTENCY & EFFICIENCY (Scaled 0-100)
    c_metrics = []
    roic = data.return_on_invested_capital or 0
    c_metrics.append(min(100, max(0, (roic / 0.15) * 100)))
    if (data.operating_margins or 0) > 0.10: c_metrics.append(100)
    else: c_metrics.append(50)
    
    raw_scores["consistency"] = sum(c_metrics) / len(c_metrics)
    
    # FINAL WEIGHTED CALCULATION
    weighted_score = (
        raw_scores["profitability"] * 0.30 +
        raw_scores["growth"] * 0.20 +
        raw_scores["financial_strength"] * 0.30 +
        raw_scores["consistency"] * 0.20
    )
    
    # GOVERNANCE PENALTY (Audit 10.7)
    audit_risk = getattr(data, 'audit_risk_score', 2)
    board_risk = getattr(data, 'board_risk_score', 2)
    
    gov_penalty = (max(audit_risk, board_risk) / 10) * 10 
    
    # Audit 9.2.0: Pathological Compensation Penalty
    # If compensation risk is max (10) while ROE is negative, apply extra haircut
    if board_risk >= 10 and (data.return_on_equity or 0) < 0:
        gov_penalty += 10.0 # Additional "Leadership Failure" penalty
    
    overall_score = round(max(0, min(100, weighted_score - gov_penalty)), 1)
    
    # Audit 9.1.0: Profitability Reconciliation Bridge (Remediation 10.2)
    reconciliation_bridge = None
    if om > 0 and roe < 0:
        reconciliation_bridge = "Operating profit neutralized by non-operating expenses (likely SBC, Interest, or Tax drag)."
    elif om < 0 and fcf_m > 0:
        reconciliation_bridge = "Operating loss masked by high non-cash charges (Depreciation/Amortization) or working capital inflows."

    # Audit 3.2 Fix: Margin Fragility Hard Cap
    if (data.operating_margins or 0) < (bench["margin"] * 0.5) and (data.free_cash_flow or 0) < 0:
        overall_score = min(overall_score, 65.0)
    
    if overall_score >= 80: grade, label = QualityGrade.A, "Strong Buy"
    elif overall_score >= 65: grade, label = QualityGrade.B, "Buy"
    elif overall_score >= 50: grade, label = QualityGrade.C, "Hold / Watchlist"
    elif overall_score >= 35: grade, label = QualityGrade.D, "Sell"
    else: grade, label = QualityGrade.F, "Avoid"

    sentiment = SentimentDetail(label=label, score=overall_score, confidence="High")
    return CompositeQualityScore(
        overall_score=overall_score, 
        grade=grade, 
        profitability_score=round(raw_scores["profitability"], 1), 
        growth_score=round(raw_scores["growth"], 1), 
        financial_strength_score=round(raw_scores["financial_strength"], 1), 
        business_model_score=50.0, 
        management_score=round(100 - (gov_penalty*10), 1),
        consistency_score=round(raw_scores["consistency"], 1), 
        components={**raw_scores, "reconciliation_bridge": reconciliation_bridge}
    ), sentiment
    
    # Audit 3.2 Fix: Margin Fragility Hard Cap
    # If Operating margin < 50% of sector AND FCF YoY < 0 (deteriorating cash conversion)
    fcf_yoy = 0
    if data.trend_analysis:
        for delta in data.trend_analysis.deltas:
            if delta.metric == "Free Cash Flow":
                fcf_yoy = delta.delta_pct
                break
    
    if om < (bench["margin"] * 0.5) and fcf_yoy < 0:
        overall_score = min(overall_score, 65.0)
    
    if overall_score >= 80: grade, label = QualityGrade.A, "Strong Buy"
    elif overall_score >= 65: grade, label = QualityGrade.B, "Buy"
    elif overall_score >= 50: grade, label = QualityGrade.C, "Hold / Watchlist"
    elif overall_score >= 35: grade, label = QualityGrade.D, "Sell"
    else: grade, label = QualityGrade.F, "Avoid"

    sentiment = SentimentDetail(label=label, score=round(overall_score, 1), confidence="High")
    return CompositeQualityScore(overall_score=round(overall_score, 1), grade=grade, profitability_score=round((scores["profitability"]/25)*100, 1), growth_score=round((scores["growth"]/15)*100, 1), financial_strength_score=round((scores["financial_strength"]/30)*100, 1), business_model_score=round((scores["business_model"]/15)*100, 1), management_score=round((scores["management"]/5)*100, 1), consistency_score=round((scores["consistency"]/10)*100, 1), components=scores), sentiment

def analyze_business_model(data: FundamentalData) -> BusinessModelAnalysis:
    desc = (data.description or "").lower()
    industry = (data.industry or "").lower()
    if "software" in industry or "saas" in desc: model_type = "SaaS/Software"
    elif "infrastructure" in industry: model_type = "Infrastructure"
    else: model_type = "Traditional"
    return BusinessModelAnalysis(model_type=model_type, revenue_recurrence=0.8 if "software" in model_type.lower() else 0.4, customer_stickiness="High" if "platform" in desc else "Medium", competitive_advantages=["High Margin"] if (data.gross_margins or 0) > 0.5 else [], scalability_rating="High" if "software" in model_type.lower() else "Moderate", market_position="Major Player" if (data.total_revenue or 0) > 1e9 else "Emerging Player", industry_outlook="Favorable" if data.sector == "Technology" else "Neutral")

def derive_executive_lists(data: FundamentalData, quality: CompositeQualityScore) -> Tuple[List[MetricItem], List[MetricItem]]:
    strengths, concerns = [], []
    if (data.revenue_growth or 0) > 0.25: strengths.append(MetricItem(category="Growth", metric="Revenue Growth", value=f"+{data.revenue_growth*100:.1f}%", assessment="Exceptional"))
    if data.net_cash_status == "Net Cash": strengths.append(MetricItem(category="Financial Health", metric="Net Cash Position", value=f"${data.net_cash/1e6:.1f}M", assessment="Very Strong"))
    if (data.return_on_invested_capital or 0) > 0.15: strengths.append(MetricItem(category="Efficiency", metric="ROIC", value=f"{data.return_on_invested_capital*100:.1f}%", assessment="High Capital Efficiency"))
    
    if (data.operating_margins or 0) < 0.10: concerns.append(MetricItem(category="Profitability", metric="Operating Margin", value=f"{data.operating_margins*100:.2f}%", assessment="Below Sector"))
    if (data.forward_pe or 0) > 25: concerns.append(MetricItem(category="Valuation", metric="Forward P/E", value=f"{data.forward_pe:.1f}x", assessment="Premium Multiple"))
    if (data.return_on_invested_capital or 0) < 0.05 and (data.return_on_invested_capital is not None): concerns.append(MetricItem(category="Efficiency", metric="ROIC", value=f"{data.return_on_invested_capital*100:.1f}%", assessment="Poor Capital Returns"))
    
    # Audit 7.5.0: Model Integrity Warning
    if data.inferences and "Medium" in data.inferences.overall_sentiment.confidence:
        concerns.append(MetricItem(category="Integrity", metric="Model Confidence", value="Reduced", assessment="Fundamental instability detected in valuation inputs."))
        
    return strengths, concerns

def generate_investment_recommendation(
    data: FundamentalData, 
    inferences: FundamentalInferences, 
    quality_score: CompositeQualityScore, 
    business_analysis: BusinessModelAnalysis,
    risk: RiskAssessment = None
) -> InvestmentRecommendation:
    """Unified decision engine mapping quality scores to actions, gated by Risk Committee rules."""
    
    # Audit 7.5.0: Strict Threshold Gating
    action_map = {
        QualityGrade.A_PLUS: "Strong Buy", 
        QualityGrade.A: "Buy", 
        QualityGrade.A_MINUS: "Buy", 
        QualityGrade.B: "Buy", 
        QualityGrade.C: "Hold / Watchlist", 
        QualityGrade.D: "Sell", 
        QualityGrade.F: "Avoid"
    }
    
    # Force Sell/Avoid if score is low
    if quality_score.overall_score < 40: action = "Avoid"
    elif quality_score.overall_score < 50: action = "Sell"
    else: action = action_map.get(quality_score.grade, "Hold / Watchlist")
    
    # Audit 9.2.0: DATA HOLD Override
    # If reliability indicates rejection, we cannot recommend holding or buying
    if inferences and inferences.overall_sentiment.confidence == "DATA_INTEGRITY_REJECTED":
        action = "Avoid"
        confidence = "DATA_REJECTED"
        return InvestmentRecommendation(
            action=action,
            confidence=confidence,
            position_sizing="0% (No Allocation)",
            investment_horizon="N/A",
            key_risks=["CRITICAL: Data Integrity Failure. Security is uninvestable until financials are reconciled."],
            monitoring_metrics=["Data Pipeline Reconciliation", "Audit Verification"]
        )

    # Audit 3.1: Confidence Gating
    confidence = "High"
    if risk and risk.score > 40:
        confidence = "Medium-High"
    if inferences and "Medium" in inferences.overall_sentiment.confidence:
        confidence = "Medium"
    
    # Risk Gating (Institutional Rule: Risk Committee Overrides)
    if risk:
        if risk.level == RiskLevel.VERY_HIGH:
            action = "Avoid"
            confidence = "Low (Risk Cap)"
        elif risk.level == RiskLevel.HIGH and "Buy" in action:
            action = "Hold / Watchlist"
            confidence = "Medium (Risk Gate)"
        
        # Risk-Adjusted Confidence
        if risk.score > 60:
            confidence = "Medium"
        elif risk.score > 80:
            confidence = "Low"

    # Momentum/Trend Overrides
    if data.trend_analysis:
        if data.trend_analysis.trajectory in ["Decay", "Unstable Inflection"] and "Buy" in action:
            action = "Hold / Watchlist"
            confidence = "Medium (Shaky Trend)"
        if data.trend_analysis.trajectory == "Unprofitable Growth" and action == "Strong Buy":
            action = "Buy"

    # Audit 4.2: Reconciliation check (Consensus vs Model)
    # If analysts target is 40% lower than DCF, downgrade confidence
    if data.analyst_estimates and data.analyst_estimates.target_mean_price:
        # We need the dcf_value which isn't passed here yet, 
        # but we can add monitoring metrics to flag it.
        pass

    # Sizing Logic
    if action == "Strong Buy": sizing = "Core Position (5-7%)"
    elif action == "Buy": sizing = "Satellite Position (2-4%)"
    elif action == "Hold / Watchlist": sizing = "Watchlist / Tactical (0-1%)"
    else: sizing = "No Allocation"

    return InvestmentRecommendation(
        action=action, 
        confidence=confidence, 
        position_sizing=sizing, 
        investment_horizon="3-5 years (Growth story)" if (data.revenue_growth or 0) > 0.2 else "2-3 years", 
        key_risks=risk.factors if risk else ["Data Insufficiency"], 
        monitoring_metrics=[
            "Revenue Growth Sustainability", 
            "Operating Margin Convergence", 
            "DCF vs Analyst Target Reconciliation",
            "Terminal Value Dominance Level"
        ]
    )

def generate_investment_thesis(data: FundamentalData, scores: Dict) -> InvestmentThesis:
    return InvestmentThesis(bull_case="If company sustains growth while expanding margins, strong balance sheet enables strategic investments", bear_case="Growth decelerates while margins remain compressed, valuation contracts significantly", base_case="Moderate growth continues with gradual margin improvement, supported by strong financial position")
