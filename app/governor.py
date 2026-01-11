from typing import List, Optional, Any
from datetime import datetime, timedelta
from .models import Technicals, MarketContext, DataIntegrity
from .settings import settings

class UnifiedRejectionTracker:
    """Track and unify rejection reasons across all endpoints"""
    
    def __init__(self):
        self.violations = []
    
    def add_violation(self, rule_code: str, description: str):
        self.violations.append(f"{rule_code}: {description}")
    
    @property
    def has_violations(self) -> bool:
        return len(self.violations) > 0
    
    def get_primary_reason(self) -> str:
        if not self.violations:
            return "None"
        return self.violations[0]
        
    def get_all_violations(self) -> List[str]:
        return self.violations

class SignalGovernor:
    """Enforces S-Tier trading rules and data integrity"""

    def assess_data_integrity(self, technicals: Technicals, context: Optional[MarketContext], ticker: str = "") -> DataIntegrity:
        """Comprehensive data quality assessment with locale awareness"""
        # Check for critical missing data
        if technicals.rsi is None or technicals.macd_histogram is None:
            return DataIntegrity.INVALID
        
        # Check for poisoned indicators
        poisoned_count = 0
        if technicals.cci is None: poisoned_count += 1
        if technicals.volume_ratio is None: poisoned_count += 1
        
        # Context checks
        if context and context.option_sentiment and context.option_sentiment.implied_volatility > 200:
             poisoned_count += 1

        # Locale Awareness: International tickers often lack Options/Insider data in yfinance
        is_international = ticker.endswith(".NS") or ticker.endswith(".BO") or "." in ticker
        
        if poisoned_count > 0:
            if is_international and technicals.cci is not None:
                # If it's international and the only "poison" is missing context data, allow VALID
                return DataIntegrity.VALID
            return DataIntegrity.DEGRADED
        
        return DataIntegrity.VALID

    def check_insider_trading(self, tracker: UnifiedRejectionTracker, context: Optional[MarketContext]):
        """Check for excessive insider selling (Rule 1)"""
        if context and context.insider_activity:
            recent_sells = self._count_recent_insider_sales(context.insider_activity, days=settings.INSIDER_SELL_WINDOW_DAYS)
            if recent_sells >= settings.INSIDER_SELL_THRESHOLD:
                tracker.add_violation("RULE_1_INSIDER_SELLS", f"{recent_sells} sales in {settings.INSIDER_SELL_WINDOW_DAYS} days")

    def check_earnings_risk(self, tracker: UnifiedRejectionTracker, context: Optional[MarketContext]):
        """Evaluate proximity to earnings (Rule 4)"""
        if context and context.events and context.events.earnings_date:
            try:
                # Handle YFinance date format (often YYYY-MM-DD or similar)
                e_date_str = context.events.earnings_date.split(' ')[0]
                e_date = datetime.strptime(e_date_str, '%Y-%m-%d').date()
                today = datetime.now().date()
                
                days_to_earnings = (e_date - today).days
                
                if 0 <= days_to_earnings <= 14:
                    tracker.add_violation("RULE_4_EARNINGS_PROXIMITY", f"Earnings in {days_to_earnings} days. Binary risk too high.")
                elif days_to_earnings < 0:
                    # Recently reported, check if it's very recent (e.g. today)
                    if days_to_earnings == -1:
                        tracker.add_violation("RULE_4_EARNINGS_PROXIMITY", "Earnings reported yesterday. High volatility zone.")
            except Exception as e:
                # If date parsing fails, skip rule but don't crash
                pass

    def check_accrual_quality(self, tracker: UnifiedRejectionTracker, fundamentals: Any):
        """Check for earnings manipulation risk via Sloan Ratio (Rule 5)"""
        if fundamentals and hasattr(fundamentals, 'net_income') and hasattr(fundamentals, 'operating_cash_flow') and hasattr(fundamentals, 'total_assets'):
            from .fundamentals_analytics import AccrualQualityAnalyzer
            sloan = AccrualQualityAnalyzer.calculate_sloan_ratio(
                fundamentals.net_income, 
                fundamentals.operating_cash_flow, 
                fundamentals.total_assets
            )
            if sloan["status"] == "MANIPULATION_RISK_HIGH":
                tracker.add_violation("RULE_5_EARNINGS_QUALITY_LOW", f"Sloan Ratio {sloan['ratio']:.2f} exceeds 0.10 threshold.")

    def apply_trading_rules(self, tracker: UnifiedRejectionTracker, technicals: Technicals, context: Optional[MarketContext], fundamentals: Any):
        """Apply framework trading rules and add to tracker"""
        
        # Rule 1: Insider selling threshold (Redundant if pre-screened, but safe)
        self.check_insider_trading(tracker, context)
        
        # Rule 2: ADX trend threshold
        if technicals.adx is not None and technicals.adx < settings.ADX_TREND_THRESHOLD:  # Weak trend
            tracker.add_violation("RULE_2_ADX_TREND", f"ADX={technicals.adx:.1f} < {settings.ADX_TREND_THRESHOLD} (Chop Zone)")

        # Rule 4: Earnings Risk
        self.check_earnings_risk(tracker, context)
        
        # Rule 5: Accrual Quality (Audit v20.2)
        self.check_accrual_quality(tracker, fundamentals)

    def get_veto_state(self, technicals: Technicals, context: Optional[MarketContext], fundamentals: Any = None, ticker: str = "") -> dict:
        """Returns a serializable state of all active vetoes/violations."""
        tracker = UnifiedRejectionTracker()
        self.apply_trading_rules(tracker, technicals, context, fundamentals)
        integrity = self.assess_data_integrity(technicals, context, ticker)
        
        return {
            "has_violations": tracker.has_violations,
            "violations": tracker.get_all_violations(),
            "data_integrity": integrity.value,
            "is_untradeable_regime": (technicals.atr_percent or 0) > 3.0 and (technicals.adx or 0) < 20
        }

    def _count_recent_insider_sales(self, activity: List[Any], days: int) -> int:
        """Count recent insider sales"""
        cutoff = datetime.now() - timedelta(days=days)
        count = 0
        for transaction in activity:
            if transaction.transaction_type == 'Sell':
                try:
                    trans_date = datetime.strptime(str(transaction.date).split(' ')[0], '%Y-%m-%d')
                    if trans_date >= cutoff:
                        count += 1
                except:
                    pass
        return count
