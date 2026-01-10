from typing import Optional
from dataclasses import dataclass
from .models import SetupState
from .settings import settings

@dataclass
class RiskParameters:
    """Unified risk configuration"""
    max_position_pct: float = settings.MAX_POSITION_PCT
    max_capital_risk_pct: float = settings.MAX_CAPITAL_RISK_PCT
    confidence_threshold: float = settings.CONFIDENCE_THRESHOLD
    degraded_confidence_penalty: float = settings.DEGRADED_CONFIDENCE_PENALTY
    degraded_position_cap: float = settings.DEGRADED_POSITION_CAP

class RiskEngine:
    def __init__(self, params: RiskParameters = None):
        self.params = params or RiskParameters()

    def calculate_position_size(self, 
                              setup_state: SetupState,
                              price: float, 
                              risk_per_share: float,
                              avg_volume: Optional[float] = None,
                              earnings_date: Optional[str] = None) -> float:
        """Calculate position size respecting risk limits, liquidity, and earnings lock."""
        if risk_per_share <= 0: return 0.0
        
        # Determine base position cap
        max_position = self.params.max_position_pct
        if setup_state == SetupState.DEGRADED:
            max_position *= self.params.degraded_position_cap

        # 1. Risk-based sizing
        max_risk_amount = (self.params.max_capital_risk_pct / 100)
        position_by_risk = (max_risk_amount * 100) / (risk_per_share / price)
        
        size = min(max_position, position_by_risk)
        
        # 2. Liquidity penalty
        if avg_volume is not None:
            liquidity_factor = min(1.0, avg_volume / settings.VOLUME_LIQUIDITY_BASELINE)
            size *= liquidity_factor

        # 3. Hard Volatility Cap
        if (risk_per_share / price) > 0.05:
            size *= 0.5
            
        # 4. Institutional Earnings Lock (Audit v13.0 Fix)
        # If earnings are within 21 days, reduce size linearly.
        if earnings_date:
            try:
                from datetime import datetime
                e_date = datetime.strptime(earnings_date.split(' ')[0], '%Y-%m-%d').date()
                days_to_e = (e_date - datetime.now().date()).days
                if 0 <= days_to_e <= 21:
                    # Linearly decay from 100% (21 days) to 0% (0 days)
                    earnings_factor = days_to_e / 21.0
                    size *= earnings_factor
            except:
                pass
            
        return size

    def calculate_capital_at_risk(self, position_size_pct: float, risk_per_share: float, price: float) -> float:
        """Returns the percentage of total capital at risk: (Position Size % * SL %)"""
        if price <= 0: return 0.0
        return round(position_size_pct * (risk_per_share / price), 4)
