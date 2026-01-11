import numpy as np
from typing import List, Dict, Optional, Any, Tuple
from functools import lru_cache
from .settings import settings

class IntrinsicValuationEngine:
    """Institutional-grade valuation engine with model fail-safes and first-principles math."""

    @staticmethod
    def calculate_dcf(
        fcf: float, 
        revenue_growth: float, 
        shares: int, 
        total_revenue: float = None,
        fcf_margin: float = None,
        sector: str = "Default"
    ) -> Dict[str, Any]:
        """
        Multi-stage DCF model with strict kill-switch for sensitivity failure.
        Audit 9.0.0: DCF is DISCARDED if TV Dominance > 50%.
        """
        if not fcf or fcf <= 0 or not shares:
            return {"value": None, "status": "FCF_NEGATIVE", "terminal_value_dominance": 0.0}
        
        effective_revenue = total_revenue if total_revenue and total_revenue > 0 else (fcf / 0.1)
        bench = settings.SECTOR_BENCHMARKS.get(sector, settings.SECTOR_BENCHMARKS["Default"])
        
        # Hard defensive bounds
        growth_cap = min(0.25, bench["growth"] * 1.5)
        safe_growth = min(growth_cap, revenue_growth)
        
        discount_rate = settings.DEFAULT_DISCOUNT_RATE
        terminal_growth = settings.DEFAULT_TERMINAL_GROWTH
        
        # Risk Uplift
        op_margin = fcf_margin or (fcf / effective_revenue)
        if op_margin < 0.10: discount_rate += 0.03
        
        target_margin = max(0.05, min(0.25, (op_margin + bench.get("fcf_margin", 0.10)) / 2))
        
        def compute_pv_components(dr: float, tg: float) -> Tuple[float, float]:
            stage_pv = 0
            temp_rev = effective_revenue
            temp_margin = op_margin
            annual_fcf = fcf
            for i in range(1, 11):
                growth = safe_growth if i <= 5 else (safe_growth - (safe_growth-tg)*((i-5)/5))
                temp_rev *= (1 + growth)
                temp_margin += (target_margin - op_margin) / 10
                annual_fcf = temp_rev * temp_margin
                stage_pv += annual_fcf / ((1 + dr) ** i)
            
            terminal_val = (annual_fcf * (1 + tg)) / (dr - tg)
            terminal_pv = terminal_val / ((1 + dr) ** 10)
            return stage_pv + terminal_pv, terminal_pv

        total_pv, terminal_pv = compute_pv_components(discount_rate, terminal_growth)
        tv_dominance = (terminal_pv / total_pv) if total_pv > 0 else 0
        
        # Institutional Kill-Switch (Remediation 10.4)
        if tv_dominance > 0.50:
            return {
                "value": None,
                "status": "MATHEMATICALLY_ILL_POSED",
                "reason": f"Terminal Value dominance ({tv_dominance*100:.1f}%) exceeds institutional stability threshold (50%).",
                "terminal_value_dominance": round(tv_dominance * 100, 1)
            }
        
        fair_price = total_pv / shares
        # Sensitivity Matrix
        sensitivity = {
            "bull": compute_pv_components(discount_rate - 0.01, terminal_growth + 0.005)[0] / shares,
            "bear": compute_pv_components(discount_rate + 0.01, terminal_growth - 0.005)[0] / shares
        }

        # Audit 9.3.0: Explicit Terminal Growth Sensitivity Table
        tg_sensitivity = {}
        for tg in [0.02, 0.025, 0.03, 0.035, 0.04]:
            val, _ = compute_pv_components(discount_rate, tg)
            tg_sensitivity[f"{tg*100:.1f}%"] = round(val / shares, 2)

        status = "OPERATIONAL"
        return {
            "value": round(fair_price, 2) if status == "OPERATIONAL" else None,
            "status": status,
            "raw_value": round(fair_price, 2),
            "range": [round(sensitivity["bear"], 2), round(sensitivity["bull"], 2)],
            "terminal_value_dominance": round(tv_dominance * 100, 1),
            "terminal_growth_sensitivity": tg_sensitivity,
            "assumptions": {
                "terminal_growth": terminal_growth,
                "discount_rate": discount_rate,
                "target_margin": round(target_margin, 3),
                "growth_cap_applied": safe_growth < revenue_growth
            }
        }

    @staticmethod
    def calculate_graham_number(eps: float, bvps: float, ticker_history: Any = None) -> Dict[str, Any]:
        """
        Strict Graham validity. Undefined for non-positive inputs.
        """
        if eps is None or bvps is None or eps <= 0 or bvps <= 0:
            return {"value": None, "status": "UNDEFINED", "reason": "Formula sqrt(22.5 * EPS * BVPS) requires positive real inputs."}
        return {"value": round((22.5 * eps * bvps) ** 0.5, 2), "status": "VALID"}

class FCFQualityAnalyzer:
    """Classifies the divergence between Cash Flow and Net Income (Audit 10.3)."""
    
    @staticmethod
    def classify_divergence(data: Any) -> Dict[str, str]:
        ni = data.net_income or 0
        fcf = data.free_cash_flow or 0
        if ni == 0: return {"classification": "Neutral", "risk": "Low"}
        
        ratio = fcf / abs(ni)
        if ratio > 1.5:
            return {"classification": "Cash Rich / Accounting Distortion", "risk": "Elevated", "detail": "FCF exceeds NI significantly; likely due to non-cash charges or favorable working capital. Audit recommended."}
        elif ratio < 0.5:
            return {"classification": "Structural Decay / Working Capital Burn", "risk": "High", "detail": "NI does not convert to cash; investigate revenue quality or rising inventory/receivables."}
        return {"classification": "Balanced", "risk": "Low"}

class CapitalAllocationEngine:
    """Calculates position sizing using Kelly Criterion and risk-parity concepts."""

    @staticmethod
    def calculate_kelly(win_rate: float, risk_reward: float) -> float:
        """Kelly Criterion: f = (bp - q) / b where b is odds (RR), p is win rate, q is fail rate."""
        if not risk_reward or risk_reward <= 0: return 0.0
        p = win_rate
        q = 1 - p
        b = risk_reward
        f = (b * p - q) / b
        return round(max(0, f) * 100, 1) # Percent

class StatisticalAnalysis:
    """Statistical methods for financial analysis with sector distance rigor."""
    
    @staticmethod
    def derive_peer_metrics(data: Any, sector_bench: Dict[str, float]) -> List[Any]:
        from .models import PeerMetric
        metrics = []
        mapping = {
            "forward_pe": "pe",
            "operating_margins": "margin",
            "revenue_growth": "growth",
            "free_cash_flow_margin": "fcf_margin",
            "return_on_equity": "roe",
            "return_on_invested_capital": "roe"
        }
        
        # Sector-specific expected variability (Institutional Sigma)
        sector_variability = {
            "pe": 0.40,      
            "margin": 0.25,  
            "growth": 0.50,  
            "roe": 0.30
        }
        
        for field, bench_key in mapping.items():
            val = getattr(data, field, None)
            bench_val = sector_bench.get(bench_key)
            
            if val is not None and bench_val:
                sigma = bench_val * sector_variability.get(bench_key, 0.30)
                if sigma == 0: sigma = 0.01
                
                # Calculate Sector Distance (Audit 9.1.0 Fix)
                # We move away from pure Z-score labels to 'Sector Distance'
                # This explicitly shows how many 'Standard Deviations' from the mean
                distance = (val - bench_val) / sigma
                
                if bench_key == "pe":
                    # Invert for PE: distance > 0 means extended, < 0 means discount
                    status = "Extended Multiple" if distance > 0.5 else ("Value Discount" if distance < -0.5 else "In-Line")
                    # Percentile mapping (High distance = Low percentile for value)
                    percentile = round(50 - (distance * 34), 1)
                else:
                    status = "Outperforming" if distance > 0.5 else ("Lagging Sector" if distance < -0.5 else "In-Line")
                    percentile = round(50 + (distance * 34), 1)
                
                percentile = min(99.0, max(1.0, percentile))
                
                metrics.append(PeerMetric(
                    metric=field.replace("_", " ").title(),
                    value=round(val, 4),
                    sector_average=bench_val,
                    percentile=percentile,
                    z_score=round(distance, 2), # Internal use, label changed in output context
                    status=status
                ))
        return metrics

class DataIntegrityValidator:
    """Institutional data integrity checker for detecting contradictory financial signals."""
    
    @staticmethod
    def validate_cross_metrics(data: Any) -> Dict[str, Any]:
        issues = []
        status = "VALID"
        
        # 1. Net Income vs ROE Consistency (Audit 9.2.0 Fix)
        ni = data.net_income or 0
        roe = data.return_on_equity or 0
        if ni > 0 and roe < 0:
            issues.append("Sign Paradox: Positive Net Income with Negative ROE.")
            status = "DATA_HOLD" 
            
        # 2. Margin Sanity
        if data.gross_margins and data.operating_margins:
            if data.operating_margins > data.gross_margins:
                issues.append("Operating margin exceeding gross margin (Impossible).")
                status = "DATA_HOLD"
                
        # 3. Cash Flow vs Net Income (Extreme Divergence)
        if data.fcf_to_net_income_ratio and abs(data.fcf_to_net_income_ratio) > 5:
            issues.append("Extreme divergence between FCF and Net Income.")

        return {"issues": issues, "status": status}

class DataReliabilityEngine:
    @staticmethod
    def calculate_reliability(data: Any) -> Any:
        from .models import ReliabilityAssessment
        score = 0.5 
        mix = []
        
        # Basic Coverage
        if data.free_cash_flow and data.total_revenue:
            score += 0.3
            mix.append("Verified Financials")
        if data.analyst_estimates and data.analyst_estimates.number_of_analysts:
            if data.analyst_estimates.number_of_analysts > 5:
                score += 0.2
                mix.append("High Analyst Coverage")
        
        # Cross-Metric Consistency Check (Audit 9.2.0 Forensic Implementation)
        integrity = DataIntegrityValidator.validate_cross_metrics(data)
        if integrity["issues"]:
            score -= 0.2 * len(integrity["issues"])
            mix.append(f"Integrity Flags: {', '.join(integrity['issues'])}")
            
        # Hard cap reliability if status is DATA_HOLD
        confidence_level = "High" if score > 0.8 else ("Medium" if score > 0.5 else "Low")
        if integrity["status"] == "DATA_HOLD":
            confidence_level = "DATA_INTEGRITY_REJECTED"
            score = 0.1 # Minimum floor

        # Audit 3.1 Fix: Fundamental Confidence Downgrade
        warning_count = 0
        if (data.return_on_equity or 0) < 0.05: warning_count += 1
        if (data.free_cash_flow_margin or 0) < 0.05: warning_count += 1
        if (data.operating_margins or 0) < 0.10: warning_count += 1
        
        if warning_count >= 2 and confidence_level == "High":
            confidence_level = "Medium (Fundamental Instability)"
            score *= 0.8 

        score = max(0.1, min(1.0, score))
        return ReliabilityAssessment(
            score=round(score, 2),
            adjustment_factor=1.0,
            confidence_level=confidence_level,
            data_mix_quality=", ".join(mix)
        )

class FundamentalTrendEngine:
    @staticmethod
    def calculate_yoy_trends(ticker: str, history: Dict[str, Any]) -> Any:
        from .models import TrendAnalysis, TrendDelta
        fin = history.get("financials")
        if fin is None or fin.empty or fin.shape[1] < 2: return None
        
        metrics_map = {
            "Total Revenue": "Revenue", 
            "Operating Income": "Operating Profit", 
            "Net Income": "Net Income", 
            "Free Cash Flow": "Free Cash Flow"
        }
        
        deltas = []
        rev_growth, profit_growth, fcf_growth = 0.0, 0.0, 0.0
        
        for yf_label, display in metrics_map.items():
            try:
                row = None
                if yf_label in fin.index: row = fin.loc[yf_label]
                elif "cashflow" in history and yf_label in history["cashflow"].index: 
                    row = history["cashflow"].loc[yf_label]
                
                if row is not None and len(row) >= 2:
                    curr, prev = row.iloc[0], row.iloc[1]
                    if prev is not None and not np.isnan(curr) and not np.isnan(prev):
                        # Base Effect Normalization
                        if abs(prev) < 1e6: # Less than $1M
                            d_pct = 1.0 if curr > prev else -1.0
                            interpretation = f"{display} turned {'positive' if curr > 0 else 'negative'} from a near-zero base"
                        else:
                            d_pct = (curr - prev) / abs(prev)
                            if d_pct > 10.0:
                                interpretation = f"{display} expanded significantly (+{d_pct*100:.0f}%) due to low base effects"
                            else:
                                interpretation = f"{display} {'expanded' if d_pct > 0 else 'contracted'} by {abs(d_pct)*100:.1f}% YoY"
                        
                        if display == "Revenue": rev_growth = d_pct
                        if display == "Operating Profit": profit_growth = d_pct
                        if display == "Free Cash Flow": fcf_growth = d_pct
                        
                        status = "Improving" if d_pct > 0.02 else ("Deteriorating" if d_pct < -0.02 else "Stable")
                        deltas.append(TrendDelta(
                            metric=display, 
                            current=float(curr), 
                            previous=float(prev),
                            delta_pct=round(d_pct * 100, 2), 
                            status=status,
                            interpretation=interpretation
                        ))
            except: continue
            
        if not deltas: return None
        
        summary, trajectory = "Stable fundamentals", "Consistent"
        if rev_growth > 0.05 and profit_growth > rev_growth:
            # Audit 3.4 Fix: Check for weak cash conversion
            if fcf_growth < 0:
                trajectory, summary = "Unstable Inflection", "Early profitability inflection with weak cash conversion."
            else:
                trajectory, summary = "Accelerating", "Operating Leverage Expansion: Profits growing faster than top-line."
        elif rev_growth < -0.05 and profit_growth < -0.05:
            trajectory, summary = "Decay", "Fundamental Decay: Significant deterioration in both top and bottom lines."
        elif rev_growth > 0.10 and profit_growth < 0:
            trajectory, summary = "Unprofitable Growth", "Scaling at the expense of margins; profitability is lagging revenue expansion."
            
        return TrendAnalysis(deltas=deltas, summary=summary, trajectory=trajectory)
