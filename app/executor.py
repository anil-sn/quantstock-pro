from typing import Tuple, List
from .models import Technicals, TradeAction, SetupState, SetupQuality, DecisionState, ScoreDetail
from .risk import RiskEngine

class TradeExecutor:
    """Handles level calculation and final decision formatting"""

    def __init__(self, risk_engine: RiskEngine):
        self.risk_engine = risk_engine

    def calculate_levels(self, action: TradeAction, technicals: Technicals, current_price: float) -> Tuple[float, List[float], Tuple[float, float]]:
        """Helper to adjust levels based on price and ATR"""
        atr = technicals.atr if technicals.atr else current_price * 0.01
        
        if action == TradeAction.BUY or action == TradeAction.WAIT:
            sl = current_price - (2 * atr)
            tp = [current_price + (2 * atr), current_price + (4 * atr)]
            ez = (current_price * 0.99, current_price * 1.01)
        elif action == TradeAction.SELL:
            sl = current_price + (2 * atr)
            tp = [current_price - (2 * atr), current_price - (4 * atr)]
            ez = (current_price * 0.99, current_price * 1.01)
        else: # REJECT
            sl = current_price
            tp = [current_price]
            ez = (current_price, current_price)
        return sl, tp, ez

    def confidence_label(self, val: float) -> str:
        if val >= 80: return "Very High"
        if val >= 70: return "High"
        if val >= 50: return "Moderate"
        if val >= 30: return "Low"
        return "Very Low"

    def create_score_detail(self, value: float, legend: str) -> ScoreDetail:
        return ScoreDetail(
            value=value,
            min_value=0.0,
            max_value=100.0,
            label=self.confidence_label(value),
            legend=legend
        )
