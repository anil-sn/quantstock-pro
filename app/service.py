from typing import Any, Tuple, Optional, List, Dict
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from .market_data import fetch_stock_data
from .technicals import calculate_advanced_technicals, calculate_algo_signal
from .fundamentals import get_fundamentals
from .context import get_market_context
from .ai import interpret_advanced
from .models import (
    AdvancedStockResponse, TechnicalStockResponse, RiskMetrics, 
    TradeSetup, TradeAction, RiskLevel, StockOverview, ScoreDetail, MarketContext,
    DataIntegrity, DecisionState, SetupState, SetupQuality, AlgoSignal, Technicals
)

# ============== DATA MODELS (INTERNAL) ============== 

@dataclass
class RiskParameters:
    """Unified risk configuration"""
    max_position_pct: float = 5.0
    max_capital_risk_pct: float = 0.5  # 0.5% max portfolio risk per trade
    confidence_threshold: float = 70.0
    degraded_confidence_penalty: float = 20.0
    degraded_position_cap: float = 0.5  # 50% of normal position when degraded

@dataclass
class TradingDecision:
    """Single source of truth for trading decisions"""
    decision_state: DecisionState
    setup_state: SetupState
    confidence: float  # 0-100, unified across system
    primary_reason: str
    violation_rules: List[str]  # Specific rule violations
    position_size_pct: float = 0.0
    max_capital_risk: float = 0.0
    risk_reward_ratio: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    tp_targets: List[float] = None
    entry_zone: Tuple[float, float] = (0.0, 0.0)
    setup_quality: Optional[SetupQuality] = None

# ============== CORE LOGIC ============== 

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
        # Return the first violation as primary (assuming checks are ordered by severity)
        return self.violations[0]
        
    def get_all_violations(self) -> List[str]:
        return self.violations

class STierTradingSystem:
    """S-Tier trading system with unified architecture"""
    
    def __init__(self, risk_params: RiskParameters = None):
        self.risk_params = risk_params or RiskParameters()
        
    def analyze(self, 
                technicals: Technicals, 
                algo_signal: AlgoSignal, 
                market_context: Optional[MarketContext],
                fundamentals: Any) -> TradingDecision:
        """
        Main analysis pipeline with S-Tier architecture
        """
        tracker = UnifiedRejectionTracker()
        
        # Step 1: Data Integrity Check
        data_integrity = self._assess_data_integrity(technicals, market_context)
        
        if data_integrity == DataIntegrity.INVALID:
            tracker.add_violation("RULE_0_DATA_INTEGRITY", "Critical data missing or corrupted (RSI/MACD/Price)")
            # If data is invalid, we might stop here or continue to find other flaws.
            # S-Tier usually fails fast on critical data, but to be "Unified", we stop here 
            # because we can't reliably check other technical rules.
            return self._create_reject_decision(
                SetupState.INVALID,
                tracker.get_primary_reason(),
                tracker.get_all_violations()
            )
        
        # Step 2: Rule-based analysis
        # We pass the tracker to collect all violations
        self._apply_trading_rules(tracker, technicals, market_context, fundamentals)
        
        # Step 3: Hard rejection for rule violations
        if tracker.has_violations:
            return self._create_reject_decision(
                SetupState.INVALID, # Rules violated -> Setup is INVALID
                f"Violates trading framework rules: {tracker.get_primary_reason()}",
                tracker.get_all_violations()
            )
        
        # Step 4: Calculate base confidence
        base_confidence = self._calculate_base_confidence(technicals, algo_signal, fundamentals, market_context)
        
        # Step 5: Apply data integrity penalty
        setup_state = SetupState.VALID
        if data_integrity == DataIntegrity.DEGRADED:
            setup_state = SetupState.DEGRADED
            base_confidence = max(0, base_confidence - self.risk_params.degraded_confidence_penalty)
        
        # Step 6: Make final decision
        score = algo_signal.overall_score.value
        
        # Neutral Zone Filter
        if abs(score) < 20:
             return self._create_wait_decision(
                setup_state,
                base_confidence,
                "Neutral Signal Score (Momentum absent)"
            )

        if base_confidence >= self.risk_params.confidence_threshold:
            # Determine Quality (Only if Valid/Degraded)
            quality = self._determine_quality(base_confidence, algo_signal)
            
            return self._create_trade_decision(
                setup_state,
                technicals, 
                score,
                base_confidence,
                quality
            )
        else:
            # Low confidence but valid signal -> WAIT (Monitor)
            return self._create_wait_decision(
                setup_state,
                base_confidence,
                f"Insufficient confidence: {base_confidence:.1f}/{self.risk_params.confidence_threshold}"
            )
    
    def _assess_data_integrity(self, technicals: Technicals, context: Optional[MarketContext]) -> DataIntegrity:
        """Comprehensive data quality assessment"""
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

        if poisoned_count > 0:
            return DataIntegrity.DEGRADED
        
        return DataIntegrity.VALID
    
    def _apply_trading_rules(self, tracker: UnifiedRejectionTracker, technicals: Technicals, context: Optional[MarketContext], fundamentals: Any):
        """Apply framework trading rules and add to tracker"""
        
        # Rule 1: Insider selling threshold
        if context and context.insider_activity:
            recent_sells = self._count_recent_insider_sales(context.insider_activity, days=90)
            if recent_sells >= 3:
                tracker.add_violation("RULE_1_INSIDER_SELLS", f"{recent_sells} sales in 90 days")
        elif context is None:
             # If context is missing but required for full S-Tier check, we might skip or flag.
             # For 'Technical' endpoint, if we want consistency, we should have fetched it.
             pass 
        
        # Rule 2: ADX trend threshold
        if technicals.adx is not None and technicals.adx < 15:  # Weak trend
            tracker.add_violation("RULE_2_ADX_TREND", f"ADX={technicals.adx:.1f} < 15 (Chop Zone)")
            
        # Rule 3: Price Structure (Below EMAs) - Optional but good for consistency
        # If price < EMA20 < EMA50 < EMA200 (Bearish) but Algo says BUY? 
        # Algo Score covers this mostly. But specific hard rules can go here.

    
    def _calculate_base_confidence(self, technicals: Technicals, algo_signal: AlgoSignal, fundamentals: Any, context: Optional[MarketContext]) -> float:
        """Calculate confidence score from 0-100"""
        score = 80.0  # Start high, subtract
        
        # Confluence
        confluence = algo_signal.confluence_score
        if confluence < 4: score -= 30
        elif confluence < 6: score -= 10
        elif confluence >= 8: score += 10
        
        # Volatility Risk
        if algo_signal.volatility_risk == RiskLevel.HIGH: score -= 10
        if algo_signal.volatility_risk == RiskLevel.VERY_HIGH: score -= 25
        
        # Volume Confirmation
        if technicals.volume_ratio is not None:
            if technicals.volume_ratio > 1.2: score += 5
            elif technicals.volume_ratio < 0.8: score -= 5
            
        return max(0.0, min(100.0, score))
    
    def _determine_quality(self, confidence: float, algo_signal: AlgoSignal) -> SetupQuality:
        if confidence > 85 and algo_signal.volatility_risk == RiskLevel.LOW:
            return SetupQuality.HIGH
        if confidence > 60:
            return SetupQuality.MEDIUM
        return SetupQuality.LOW

    def _create_trade_decision(self, setup_state: SetupState, technicals: Technicals, score: float,
                              confidence: float, quality: SetupQuality) -> TradingDecision:
        """Create BUY/SELL decision"""
        # We assume price is roughly around EMA_20 or use previous close logic implicitly
        # Ideally we pass current_price in. 
        anchor = technicals.ema_20 if technicals.ema_20 else 100.0 
        
        decision_state = DecisionState.ACCEPT # Implies BUY or SELL is actionable
        
        # Determine position size
        base_position = self.risk_params.max_position_pct
        
        if setup_state == SetupState.DEGRADED:
            base_position *= self.risk_params.degraded_position_cap
        
        # Plan a hypothetical BUY setup for monitoring (or SELL if trend is down)
        # Check trend for bias
        bias = TradeAction.BUY if technicals.trend_structure == "Bullish" else TradeAction.SELL
        stop_loss, tp_targets, entry_zone = self._calculate_levels(bias, technicals)
        current_price = (entry_zone[0] + entry_zone[1]) / 2
        
        # Calculate risk
        risk_per_share = abs(current_price - stop_loss)
        if risk_per_share == 0: risk_per_share = 0.01 
        
        position_size = self._calculate_position_size(
            base_position, current_price, risk_per_share
        )
        
        risk_reward = abs(tp_targets[0] - current_price) / risk_per_share
        
        return TradingDecision(
            decision_state=decision_state,
            setup_state=setup_state,
            confidence=confidence,
            primary_reason="High confidence trade setup",
            violation_rules=[],
            position_size_pct=position_size,
            max_capital_risk=position_size * (risk_per_share / current_price) * 100,
            risk_reward_ratio=risk_reward,
            stop_loss=stop_loss,
            take_profit=tp_targets[0],
            tp_targets=tp_targets,
            entry_zone=entry_zone,
            setup_quality=quality
        )
    
    def _create_wait_decision(self, setup_state: SetupState, confidence: float, reason: str) -> TradingDecision:
        """Create WAIT decision"""
        return TradingDecision(
            decision_state=DecisionState.WAIT,
            setup_state=setup_state, # Can be VALID or DEGRADED
            confidence=confidence,
            primary_reason=reason,
            violation_rules=[],
            # Non-zero parameters for monitoring
            position_size_pct=3.0, 
            max_capital_risk=0.15,
            risk_reward_ratio=2.0,
            stop_loss=0.0,
            take_profit=0.0,
            tp_targets=[],
            entry_zone=(0.0, 0.0),
            setup_quality=None # WAIT means not actionable yet -> No Quality assigned or Medium? 
            # Evaluation: "IF setup_state != VALID THEN setup_quality MUST be null". 
            # WAIT means decision is wait.
            # If we are WAITING, is the quality HIGH? No.
            # Let's leave quality as None for WAIT.
        )
    
    def _create_reject_decision(self, setup_state: SetupState, 
                               reason: str, 
                               violations: List[str]) -> TradingDecision:
        """Create REJECT decision"""
        # setup_state should be INVALID usually
        return TradingDecision(
            decision_state=DecisionState.REJECT,
            setup_state=setup_state,
            confidence=0.0,
            primary_reason=reason,
            violation_rules=violations,
            position_size_pct=0.0,
            max_capital_risk=0.0,
            risk_reward_ratio=0.0,
            stop_loss=0.0,
            take_profit=0.0,
            tp_targets=[],
            entry_zone=(0.0, 0.0),
            setup_quality=None # Must be None
        )
    
    def _calculate_levels(self, bias: TradeAction, technicals: Technicals) -> Tuple[float, List[float], Tuple[float, float]]:
        """Calculate Stop Loss, Take Profits, and Entry Zone."""
        anchor = technicals.ema_20 if technicals.ema_20 else 100.0 
        atr = technicals.atr if technicals.atr else anchor * 0.01
        
        if bias == TradeAction.BUY:
            stop_loss = anchor - (atr * 2)
            tp_targets = [anchor + (atr * 2), anchor + (atr * 4)]
            entry_zone = (anchor * 0.99, anchor * 1.01)
        else: # SELL
            stop_loss = anchor + (atr * 2)
            tp_targets = [anchor - (atr * 2), anchor - (atr * 4)]
            entry_zone = (anchor * 0.99, anchor * 1.01)
            
        return stop_loss, tp_targets, entry_zone

    def _calculate_position_size(self, max_position: float, 
                                price: float, 
                                risk_per_share: float) -> float:
        """Calculate position size respecting risk limits"""
        if risk_per_share <= 0: return 0.0
        
        # Calculate position based on risk per share
        max_risk_amount = (self.risk_params.max_capital_risk_pct / 100)
        position_by_risk = (max_risk_amount * 100) / (risk_per_share / price)
        
        return min(max_position, position_by_risk)
    
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

# --- MAIN SERVICES --- 

# Initialize System
s_tier_system = STierTradingSystem()

async def get_technical_analysis(ticker: str) -> TechnicalStockResponse:
    """Fast, purely quantitative analysis without AI insights"""
    data = await fetch_stock_data(ticker)
    df = data["dataframe"]
    returns = data["returns"]
    info = data["info"]
    current_price = data["current_price"]

    technicals = calculate_advanced_technicals(df)
    algo_signal = calculate_algo_signal(technicals)
    risk_metrics = calculate_risk_metrics(returns)
    
    # Fetch context for consistency (S-Tier requirement: Insider rules must apply everywhere)
    market_context = get_market_context(ticker)

    # Use S-Tier System
    decision = s_tier_system.analyze(technicals, algo_signal, market_context, None)
    
    # Map back to TradeAction (Direction) + Decision
    direction_action = TradeAction.BUY if algo_signal.overall_score.value > 0 else TradeAction.SELL
    if decision.decision_state == DecisionState.WAIT: direction_action = TradeAction.WAIT
    if decision.decision_state == DecisionState.REJECT: direction_action = TradeAction.REJECT # Override
    
    # Adjust levels
    stop_loss, tp_targets, entry_zone = _recalculate_levels_for_price(direction_action, current_price, technicals)
    
    # If REJECT, zero out metrics
    if decision.decision_state == DecisionState.REJECT:
        risk_metrics = None # S-Tier Requirement: Freeze/Remove risk metrics
    
    # Detail Objects
    confidence_detail = ScoreDetail(
        value=decision.confidence,
        min_value=0.0,
        max_value=100.0,
        label=_confidence_label(decision.confidence),
        legend="Evidence Quality & Confluence (0-100)"
    )
    
    # Integrity Check
    data_integrity = DataIntegrity.VALID
    if decision.setup_state == SetupState.DEGRADED: data_integrity = DataIntegrity.DEGRADED
    if decision.setup_state == SetupState.INVALID: data_integrity = DataIntegrity.INVALID

    overview = StockOverview(
        action=direction_action,
        decision_state=decision.decision_state,
        current_price=current_price,
        target_price=tp_targets[0] if tp_targets else 0.0,
        stop_loss=stop_loss,
        confidence=confidence_detail,
        summary=f"System: {decision.decision_state.value}. Reason: {decision.primary_reason}."
    )

    trade_setup = TradeSetup(
        action=direction_action,
        confidence=confidence_detail,
        entry_zone=entry_zone,
        stop_loss=stop_loss,
        stop_loss_pct=(abs(current_price-stop_loss)/current_price)*100 if current_price else 0,
        take_profit_targets=tp_targets,
        risk_reward_ratio=decision.risk_reward_ratio,
        position_size_pct=decision.position_size_pct,
        max_capital_at_risk=decision.max_capital_risk,
        setup_state=decision.setup_state,
        setup_quality=decision.setup_quality
    )

    return TechnicalStockResponse(
        overview=overview,
        ticker=ticker.upper(),
        company_name=info.get("longName"),
        sector=info.get("sector"),
        current_price=current_price,
        price_change_1d=float(df['Close'].pct_change().iloc[-1] * 100) if len(df) > 1 else None,
        technicals=technicals,
        algo_signal=algo_signal,
        trade_setup=trade_setup,
        risk_metrics=risk_metrics,
        data_confidence=decision.confidence,
        data_integrity=data_integrity,
        decision_state=decision.decision_state
    )

async def analyze_stock(ticker: str, mode: Any = "all") -> AdvancedStockResponse:
    # Determine interval based on mode
    interval = "15m" if mode == "intraday" else "1d"
    
    data = await fetch_stock_data(ticker, interval=interval)
    df = data["dataframe"]
    returns = data["returns"]
    info = data["info"]
    current_price = data["current_price"]

    technicals = calculate_advanced_technicals(df)
    algo_signal = calculate_algo_signal(technicals)
    risk_metrics = calculate_risk_metrics(returns)

    # Fetch fundamentals
    fundamentals = None
    if mode in ["swing", "positional", "longterm", "all"]:
        fundamentals = get_fundamentals(ticker)

    # Fetch market context
    market_context = get_market_context(ticker)

    # --- S-TIER GOVERNANCE ---
    decision = s_tier_system.analyze(technicals, algo_signal, market_context, fundamentals)
    
    # Map Actions
    direction_action = TradeAction.BUY if algo_signal.overall_score.value > 0 else TradeAction.SELL
    if decision.decision_state == DecisionState.WAIT: direction_action = TradeAction.WAIT
    if decision.decision_state == DecisionState.REJECT: direction_action = TradeAction.REJECT
    
    # Recalculate Levels
    stop_loss, tp_targets, entry_zone = _recalculate_levels_for_price(direction_action, current_price, technicals)
    
    # If REJECT, zero out metrics
    if decision.decision_state == DecisionState.REJECT:
        risk_metrics = None # Freeze/Remove

    # AI Context Instruction
    ai_system_instruction = f"""
    DECISION STATE: {decision.decision_state.value}
    SETUP STATE: {decision.setup_state.value}
    PRIMARY REASON: {decision.primary_reason}
    CONFIDENCE: {decision.confidence:.1f}/100
    RISK LIMIT: 0.5% Capital
    VIOLATIONS: {decision.violation_rules}
    
    INSTRUCTIONS:
    """
    if decision.decision_state == DecisionState.REJECT:
        ai_system_instruction += "\nCRITICAL: REJECTED STATE. Do NOT recommend a trade. List the VIOLATIONS clearly."
    elif decision.decision_state == DecisionState.WAIT:
        ai_system_instruction += "\nSTATUS: WAIT/MONITOR. Valid setup but triggers missing. Explain what to watch for."
    else:
        ai_system_instruction += "\nSTATUS: ACTIVE/ACCEPT. System approves trade."

    # Call AI Analyst
    ai_analysis = await interpret_advanced(ticker, technicals, info, mode, fundamentals, market_context, system_context=ai_system_instruction)
    if not ai_analysis:
        raise ValueError("AI Analysis failed to generate results.")

    # Override AI Confidence/Action with Governor's Authority
    # 1. Enforce Action/Confidence
    ai_analysis.swing.action = direction_action
    ai_analysis.swing.confidence.value = decision.confidence
    ai_analysis.swing.confidence.label = _confidence_label(decision.confidence)
    
    # 2. Enforce consistency on other timeframes if REJECTED
    if decision.decision_state == DecisionState.REJECT:
        for horizon in [ai_analysis.intraday, ai_analysis.positional, ai_analysis.longterm]:
            horizon.action = TradeAction.REJECT
            horizon.confidence.value = 0.0

    # 3. FILTER POISONED SIGNALS from AI Response
    _sanitize_ai_signals(ai_analysis, technicals)

    # Explicit Risk Disclosure
    risk_disclosure = f" Max Risk: {decision.max_capital_risk:.2f}% (Limit: 0.5%)"
    if decision.decision_state == DecisionState.REJECT:
        risk_disclosure = " Risk: N/A (Trade Rejected)"
    
    # Detail Objects
    confidence_detail = ScoreDetail(
        value=decision.confidence,
        min_value=0.0,
        max_value=100.0,
        label=_confidence_label(decision.confidence),
        legend="Evidence Quality & Confluence (0-100)"
    )
    
    data_integrity = DataIntegrity.VALID
    if decision.setup_state == SetupState.DEGRADED: data_integrity = DataIntegrity.DEGRADED
    if decision.setup_state == SetupState.INVALID: data_integrity = DataIntegrity.INVALID

    trade_setup = TradeSetup(
        action=direction_action,
        confidence=confidence_detail,
        entry_zone=entry_zone,
        stop_loss=stop_loss,
        stop_loss_pct=(abs(current_price-stop_loss)/current_price)*100 if current_price else 0,
        take_profit_targets=tp_targets,
        risk_reward_ratio=decision.risk_reward_ratio,
        position_size_pct=decision.position_size_pct,
        max_capital_at_risk=decision.max_capital_risk,
        setup_state=decision.setup_state,
        setup_quality=decision.setup_quality # Null if not VALID/DEGRADED? No, decision.setup_quality logic handles it
    )

    overview = StockOverview(
        action=direction_action,
        decision_state=decision.decision_state,
        current_price=current_price,
        target_price=tp_targets[0] if tp_targets else 0.0,
        stop_loss=stop_loss,
        confidence=confidence_detail,
        summary=ai_analysis.executive_summary + risk_disclosure
    )

    return AdvancedStockResponse(
        analysis_mode=mode,
        overview=overview,
        ticker=ticker.upper(),
        company_name=info.get("longName"),
        sector=info.get("sector"),
        current_price=current_price,
        price_change_1d=float(df['Close'].pct_change().iloc[-1] * 100) if len(df) > 1 else None,
        technicals=technicals,
        algo_signal=algo_signal,
        trade_setup=trade_setup,
        ai_analysis=ai_analysis,
        risk_metrics=risk_metrics,
        market_context=market_context,
        data_confidence=decision.confidence,
        data_integrity=data_integrity,
        decision_state=decision.decision_state
    )

# --- HELPERS ---

def _recalculate_levels_for_price(action: TradeAction, price: float, technicals: Technicals):
    """Helper to adjust levels to exact current price"""
    atr = technicals.atr if technicals.atr else price * 0.01
    
    if action == TradeAction.BUY or action == TradeAction.WAIT:
        sl = price - (2 * atr)
        tp = [price + (2 * atr), price + (4 * atr)]
        ez = (price * 0.99, price * 1.01)
    elif action == TradeAction.SELL:
        sl = price + (2 * atr)
        tp = [price - (2 * atr), price - (4 * atr)]
        ez = (price * 0.99, price * 1.01)
    else: # REJECT
        sl = price
        tp = [price]
        ez = (price, price)
    return sl, tp, ez

def _confidence_label(val: float) -> str:
    if val >= 80: return "Very High"
    if val >= 70: return "High"
    if val >= 50: return "Moderate"
    if val >= 30: return "Low"
    return "Very Low"

def _sanitize_ai_signals(ai_result, technicals: Technicals):
    """Remove signals that correspond to poisoned indicators"""
    poisoned = []
    if technicals.cci is None: poisoned.append("cci")
    if technicals.volume_ratio is None: poisoned.append("volume")
    
    # Helper to clean a signal list
    def clean(signals):
        return [s for s in signals if not any(p in s.indicator.lower() for p in poisoned)]

    ai_result.intraday.signals = clean(ai_result.intraday.signals)
    ai_result.swing.signals = clean(ai_result.swing.signals)
    ai_result.positional.signals = clean(ai_result.positional.signals)
    ai_result.longterm.signals = clean(ai_result.longterm.signals)

def calculate_risk_metrics(returns: Any) -> RiskMetrics:
    """Calculate Sharpe, Sortino and Drawdown"""
    if len(returns) < 30:
        return RiskMetrics()
    
    sharpe = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else None
    
    negative_returns = returns[returns < 0]
    sortino = returns.mean() / negative_returns.std() * np.sqrt(252) if len(negative_returns) > 1 else None
    
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    max_dd = drawdown.min()
    
    return RiskMetrics(
        sharpe_ratio=float(sharpe) if sharpe is not None else None,
        sortino_ratio=float(sortino) if sortino is not None else None,
        max_drawdown=float(max_dd) if max_dd is not None else None,
        standard_deviation=float(returns.std() * np.sqrt(252))
    )

async def get_fundamental_analysis(ticker: str) -> Any:
    return get_fundamentals(ticker)