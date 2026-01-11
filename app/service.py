import asyncio
import time
from typing import Any, Tuple, Optional, List, Dict
from datetime import datetime, timedelta, timezone
import numpy as np
import pandas as pd
from .market_data import fetch_stock_data
from .technicals import calculate_advanced_technicals, calculate_algo_signal
from .technicals_scoring import get_empty_algo_signal
from .fundamentals import get_fundamentals, get_news
from .context import get_market_context
from .models import (
    AdvancedStockResponse, TechnicalStockResponse, RiskMetrics, 
    TradeSetup, TradeAction, RiskLevel, StockOverview, ScoreDetail, MarketContext,
    DataIntegrity, DecisionState, SetupState, SetupQuality, AlgoSignal, Technicals,
    TradingDecision, NewsResponse, AdvancedFundamentalAnalysis, OHLCV, MultiHorizonSetups,
    TrendDirection, PipelineStageState, PipelineState, PipelineTrace, SensorStatus, ResearchReport,
    WeightDetail, AIAnalysisResult, HorizonPerspective, OptionsAdvice, MarketSentiment,
    ResponseMeta, ExecutionBlock, SignalsBlock, LevelsBlock, ContextBlock, 
    HumanInsightBlock, SystemBlock, RiskLimits, SignalComponent, LevelItem, ValueZone
)
from .risk import RiskEngine, RiskParameters
from .governor import SignalGovernor, UnifiedRejectionTracker
from .executor import TradeExecutor
from .logger import pipeline_logger
from .settings import settings

# ============== TRADING SYSTEM ============== 

class QuantitativeTradingSystem:
    def __init__(self, risk_params: RiskParameters = None):
        self.risk_engine = RiskEngine(risk_params)
        self.governor = SignalGovernor()
        self.executor = TradeExecutor(self.risk_engine)
        
    def pre_screen(self, market_context: Optional[MarketContext]) -> Optional[TradingDecision]:
        tracker = UnifiedRejectionTracker()
        if market_context:
            self.governor.check_insider_trading(tracker, market_context)
            self.governor.check_earnings_risk(tracker, market_context)
        if tracker.has_violations:
            return self._create_reject_decision(SetupState.SKIPPED, f"Pre-Screen Reject: {tracker.get_primary_reason()}", tracker.get_all_violations())
        return None

    def analyze(self, technicals: Technicals, algo_signal: AlgoSignal, market_context: Optional[MarketContext], fundamentals: Any, ticker: str = "") -> TradingDecision:
        tracker = UnifiedRejectionTracker()
        data_integrity = self.governor.assess_data_integrity(technicals, market_context, ticker)
        if data_integrity == DataIntegrity.INVALID:
            return self._create_reject_decision(SetupState.INVALID, "Critical data missing", ["RULE_0_DATA_INTEGRITY"])
        
        atr_pct = technicals.atr_percent if technicals.atr_percent else 0
        adx_val = technicals.adx if technicals.adx else 0
        if atr_pct > 3.0 and adx_val < 20:
             return self._create_reject_decision(SetupState.INVALID, f"Market Regime Invalid: High Volatility ({atr_pct:.2f}%) with No Trend", ["REGIME_CAPITAL_SHREDDER"])
             
        self.governor.apply_trading_rules(tracker, technicals, market_context, fundamentals)
        if tracker.has_violations:
            return self._create_reject_decision(SetupState.INVALID, f"Violates framework rules: {tracker.get_primary_reason()}", tracker.get_all_violations())
        
        base_confidence = self._calculate_base_confidence(technicals, algo_signal, market_context)
        score = algo_signal.overall_score.value
        
        ev = algo_signal.volume_score.value
        if ev < 0.2:
            base_confidence = min(base_confidence, 40.0)
            if score > 0: score /= 2
        
        if abs(score) < 20 or base_confidence < self.risk_engine.params.confidence_threshold:
             return self._create_wait_decision(SetupState.VALID, base_confidence, "Insufficient signals or Low EV")

        return self._create_trade_decision(SetupState.VALID, technicals, score, base_confidence, self._determine_quality(base_confidence, algo_signal), market_context)
    
    def _calculate_base_confidence(self, technicals: Technicals, algo_signal: AlgoSignal, market_context: Optional[MarketContext] = None) -> float:
        score = 80.0
        confluence = algo_signal.confluence_score
        if confluence < 4: score -= 30
        elif confluence < 6: score -= 10
        elif confluence >= 8: score += 10
        if algo_signal.volatility_risk == RiskLevel.HIGH: score -= 10
        if market_context and market_context.consensus and not market_context.analyst_ratings: score -= 15
        return max(0.0, min(100.0, score))
    
    def _determine_quality(self, confidence: float, algo_signal: AlgoSignal) -> SetupQuality:
        if confidence > 85 and algo_signal.volatility_risk == RiskLevel.LOW: return SetupQuality.HIGH
        return SetupQuality.MEDIUM if confidence > 60 else SetupQuality.LOW

    def _create_trade_decision(self, setup_state: SetupState, technicals: Technicals, score: float, confidence: float, quality: SetupQuality, market_context: Optional[MarketContext] = None) -> TradingDecision:
        bias = TradeAction.BUY if technicals.trend_structure == "Bullish" else TradeAction.SELL
        current_price = (technicals.ema_20 if technicals.ema_20 else 100.0)
        stop_loss, tp_targets, entry_zone = self.executor.calculate_levels(bias, technicals, current_price)
        risk_per_share = max(abs(current_price - stop_loss), 0.01)
        e_date = market_context.events.earnings_date if (market_context and market_context.events) else None
        position_size = self.risk_engine.calculate_position_size(setup_state, current_price, risk_per_share, technicals.volume_avg_20d, earnings_date=e_date)
        max_risk = self.risk_engine.calculate_capital_at_risk(position_size, risk_per_share, current_price)
        return TradingDecision(decision_state=DecisionState.ACCEPT, setup_state=setup_state, confidence=confidence, primary_reason="Trade setup approved", violation_rules=[], position_size_pct=position_size, max_capital_at_risk=max_risk, risk_reward_ratio=abs(tp_targets[0] - current_price) / risk_per_share, stop_loss=stop_loss, take_profit=tp_targets[0], tp_targets=tp_targets, entry_zone=entry_zone, setup_quality=quality)
    
    def _create_wait_decision(self, setup_state: SetupState, confidence: float, reason: str) -> TradingDecision:
        return TradingDecision(decision_state=DecisionState.WAIT, setup_state=setup_state, confidence=confidence, primary_reason=reason, violation_rules=[], position_size_pct=0.0, max_capital_at_risk=0.0, risk_reward_ratio=0.0, stop_loss=None, take_profit=None, tp_targets=None, entry_zone=None, setup_quality=None)
    
    def _create_reject_decision(self, setup_state: SetupState, reason: str, violations: List[str]) -> TradingDecision:
        return TradingDecision(decision_state=DecisionState.REJECT, setup_state=setup_state, confidence=0.0, primary_reason=reason, violation_rules=violations, position_size_pct=0.0, max_capital_at_risk=0.0, risk_reward_ratio=0.0, stop_loss=None, take_profit=None, tp_targets=None, entry_zone=None, setup_quality=None)

# --- SERVICES ---

trading_system = QuantitativeTradingSystem()

def _process_horizon(data_result: Dict[str, Any], market_context: Optional[MarketContext], ticker: str = "") -> Tuple[Optional[TradeSetup], Optional[Technicals], Optional[AlgoSignal], Optional[TradingDecision]]:
    if not data_result: return None, None, None, None
    df, current_price = data_result["dataframe"], data_result["current_price"]
    tech = calculate_advanced_technicals(df)
    sig = calculate_algo_signal(tech)
    dec = trading_system.analyze(tech, sig, market_context, None, ticker)
    action = TradeAction.REJECT if dec.decision_state == DecisionState.REJECT else (TradeAction.WAIT if dec.decision_state == DecisionState.WAIT else (TradeAction.BUY if sig.overall_score.value > 0 else TradeAction.SELL))
    sl, tp, entry = trading_system.executor.calculate_levels(action, tech, current_price)
    
    rr_ratio = abs(tp[0] - current_price) / max(abs(current_price - sl), 0.01) if sl and tp else 0.0
    
    if dec.decision_state == DecisionState.ACCEPT and rr_ratio < 1.0:
        dec.decision_state = DecisionState.REJECT
        dec.primary_reason = f"Mathematically Invalid: R:R {rr_ratio:.2f} < 1.0"
        action = TradeAction.REJECT
        sl, tp, entry = None, None, None
        rr_ratio = 0.0
    
    if action == TradeAction.WAIT:
        dec.setup_state = SetupState.INVALID
        sl, tp, entry = None, None, None
        rr_ratio = 0.0
        dec.position_size_pct = 0.0
        dec.max_capital_at_risk = 0.0

    sl_pct = (abs(current_price-sl)/current_price)*100 if current_price and sl else None
    setup = TradeSetup(action=action, confidence=trading_system.executor.create_score_detail(dec.confidence, "Evidence Quality"), entry_zone=entry, stop_loss=sl, stop_loss_pct=sl_pct, take_profit_targets=tp, risk_reward_ratio=rr_ratio, position_size_pct=dec.position_size_pct, max_capital_at_risk=dec.max_capital_at_risk, setup_state=dec.setup_state, setup_quality=dec.setup_quality)
    return setup, tech, sig, dec

async def get_technical_analysis(ticker: str) -> TechnicalStockResponse:
    from fastapi.concurrency import run_in_threadpool
    requested_ticker = ticker.upper()
    market_context = await run_in_threadpool(lambda: get_market_context(requested_ticker))
    pre_decision = await run_in_threadpool(lambda: trading_system.pre_screen(market_context))
    
    # Audit Fix: Always try to get a current price for metadata/forensics
    fallback_price = 0.0
    try:
        # Fast, shallow fetch for price only
        shallow_data = await fetch_stock_data(requested_ticker, interval="1d")
        fallback_price = shallow_data.get("current_price", 0.0)
    except:
        pass

    if pre_decision:
        reject_setup = TradeSetup(action=TradeAction.REJECT, confidence=ScoreDetail(value=0, min_value=0, max_value=100, label="Rejected", legend=""), setup_state=SetupState.SKIPPED)
        horizons = MultiHorizonSetups(intraday=reject_setup, swing=reject_setup, positional=reject_setup, longterm=reject_setup)
        return TechnicalStockResponse(overview=StockOverview(action=TradeAction.REJECT, current_price=fallback_price, confidence=reject_setup.confidence, summary=pre_decision.primary_reason), requested_ticker=requested_ticker, ticker=requested_ticker, current_price=fallback_price, trade_setup=reject_setup, horizons=horizons, raw_data=None, pipeline_state=PipelineState(pre_screen=PipelineStageState.FAILED, technicals=PipelineStageState.SKIPPED, scoring=PipelineStageState.SKIPPED, execution=PipelineStageState.SKIPPED), decision_state=DecisionState.REJECT, data_integrity=DataIntegrity.NOT_EVALUATED)

    horizons_map = {"intraday": "60m", "swing": "1d", "positional": "1wk", "longterm": "1mo"}
    tasks = [fetch_stock_data(requested_ticker, interval=interval) for interval in horizons_map.values()]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    data_results = {key: (None if isinstance(results[i], Exception) else results[i]) for i, key in enumerate(horizons_map.keys())}
    setup_results, technical_results, signal_results, decision_results = {}, {}, {}, {}
    for key, data_res in data_results.items():
        if data_res:
             setup, tech, sig, dec = _process_horizon(data_res, market_context, requested_ticker)
             setup_results[key], technical_results[key], signal_results[key], decision_results[key] = setup, tech, sig, dec
        else: setup_results[key] = technical_results[key] = signal_results[key] = decision_results[key] = None

    primary_dec = decision_results.get("swing")
    global_conf = primary_dec.confidence if primary_dec else 0.0
    dirs = [1 if (signal_results[k].overall_score.value > 20) else (-1 if signal_results[k].overall_score.value < -20 else 0) for k in ["intraday", "swing", "positional"] if signal_results.get(k)]
    if len(set(dirs)) > 1 and 0 not in dirs: global_conf *= 0.5
    
    if global_conf < 25:
        for k in setup_results:
            if setup_results[k]:
                s = setup_results[k]
                s.entry_zone = s.stop_loss = s.take_profit_targets = None
                s.position_size_pct = s.max_capital_at_risk = 0.0

    primary_data = data_results.get("swing")
    if not primary_data:
        # Emergency Fallback if swing failed but others survived
        for k in ["intraday", "positional", "longterm"]:
            if data_results.get(k):
                primary_data = data_results[k]
                break
    
    if not primary_data:
        # All horizons failed
        return TechnicalStockResponse(overview=StockOverview(action=TradeAction.REJECT, current_price=0.0, confidence=ScoreDetail(value=0, min_value=0, max_value=100, label="Data Failure", legend=""), summary="All data horizons failed to fetch."), requested_ticker=requested_ticker, ticker=requested_ticker, current_price=0.0, trade_setup=reject_setup, horizons=horizons, raw_data=None, pipeline_state=PipelineState(pre_screen=PipelineStageState.PASSED, technicals=PipelineStageState.FAILED, scoring=PipelineStageState.SKIPPED, execution=PipelineStageState.SKIPPED), data_confidence=0.0, data_integrity=DataIntegrity.INVALID, decision_state=DecisionState.REJECT)

    c_price = float(primary_data.get("current_price", 0.0))
    return TechnicalStockResponse(overview=StockOverview(action=setup_results["swing"].action if setup_results.get("swing") else TradeAction.WAIT, current_price=c_price, confidence=setup_results["swing"].confidence if setup_results.get("swing") else ScoreDetail(value=0, min_value=0, max_value=100, label="N/A", legend=""), summary=f"Audit complete. Confidence: {global_conf:.1f}%"), requested_ticker=requested_ticker, ticker=requested_ticker, current_price=c_price, company_name=primary_data["info"].get("longName"), sector=primary_data["info"].get("sector"), price_change_1d=float(primary_data["dataframe"]['Close'].pct_change().iloc[-1] * 100) if len(primary_data["dataframe"]) > 1 else None, technicals=technical_results.get("swing"), algo_signal=signal_results.get("swing"), trade_setup=setup_results.get("swing") or reject_setup, horizons=MultiHorizonSetups(intraday=setup_results.get("intraday"), swing=setup_results.get("swing"), positional=setup_results.get("positional"), longterm=setup_results.get("longterm")), raw_data=[], pipeline_state=PipelineState(pre_screen=PipelineStageState.PASSED, technicals=PipelineStageState.PASSED, scoring=PipelineStageState.PASSED, execution=PipelineStageState.SKIPPED), data_confidence=global_conf, data_integrity=DataIntegrity.VALID if global_conf > 25 else DataIntegrity.DEGRADED, decision_state=primary_dec.decision_state if primary_dec else DecisionState.WAIT)

async def analyze_stock(ticker: str, mode: Any = "all", force_ai: bool = False) -> AdvancedStockResponse:
    from fastapi.concurrency import run_in_threadpool
    from .ai import interpret_advanced
    
    start_time = time.time()
    now_utc = datetime.now(timezone.utc)
    requested_ticker = ticker.upper()
    
    # --- STAGE 1: PARALLEL SENSOR INGESTION (L0 + L1 + L2) ---
    sensor_start = time.time()
    try:
        tasks = [
            run_in_threadpool(lambda: get_market_context(requested_ticker)),
            get_technical_analysis(requested_ticker),
            get_advanced_fundamental_analysis(requested_ticker) if mode == "all" else run_in_threadpool(lambda: None),
            get_news_analysis(requested_ticker)
        ]
        results = await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=30.0)
    except asyncio.TimeoutError:
        pipeline_logger.log_error(requested_ticker, "PIPELINE", "Sensor timeout (30s).")
        results = [None, None, None, None]
        
    sensor_latency = (time.time() - sensor_start) * 1000
    
    market_context = results[0] if len(results) > 0 and results[0] and not isinstance(results[0], Exception) else None
    tech_resp = results[1] if len(results) > 1 and results[1] and not isinstance(results[1], Exception) else None
    fund_resp = results[2] if len(results) > 2 and results[2] and not isinstance(results[2], Exception) else None
    news_resp = results[3] if len(results) > 3 and results[3] and not isinstance(results[3], Exception) else None

    # Handle sensor specific errors for forensics
    for i, res in enumerate(results):
        if isinstance(res, Exception):
            pipeline_logger.log_error(requested_ticker, "PIPELINE", f"Sensor {i} failed: {res}")

    if not tech_resp: 
        pipeline_logger.log_error(requested_ticker, "PIPELINE", "Technical sensor missing - Terminal Failure")
        raise ValueError("Critical sensor failure: Technical Analysis could not be completed.")
    
    # --- VETOS & DATA TAXONOMY ---
    vetoes = []
    adx_val = tech_resp.technicals.adx if (tech_resp.technicals and tech_resp.technicals.adx is not None) else 0
    price = tech_resp.current_price
    target = market_context.price_target.mean if (market_context and market_context.price_target) else None
    is_overvalued = target and (price > target * 1.04)
    
    if adx_val < 20 and is_overvalued:
        vetoes.append({"type": "REGIME_VALUATION_CONFLICT", "severity": "HARD", "message": "Weak trend + Overvaluation"})

    data_state_taxonomy = {}
    is_intl = ticker.endswith(".NS") or ticker.endswith(".BO") or "." in ticker
    
    if not (market_context and market_context.option_sentiment): 
        data_state_taxonomy["OPTIONS"] = "NOT_SUPPORTED_IN_REGION" if is_intl else "DATA_ABSENT"
    if not (market_context and market_context.insider_activity): 
        data_state_taxonomy["INSIDER"] = "NOT_SUPPORTED_IN_REGION" if is_intl else "DATA_ABSENT"
    
    if not tech_resp.technicals:
        data_state_taxonomy["TECHNICALS"] = "MISSING"
    elif tech_resp.technicals.cci is None: 
        data_state_taxonomy["CCI"] = "MISSING"

    data_integrity = tech_resp.data_integrity
    global_conf = tech_resp.data_confidence
    if data_integrity == DataIntegrity.DEGRADED: global_conf = min(global_conf, 40.0)
    
    # Missing Data Penalty
    missing_critical = len(data_state_taxonomy)
    if missing_critical > 0:
        global_conf *= (1 - 0.15 * missing_critical)
        data_integrity = DataIntegrity.DEGRADED

    is_authorized = (global_conf >= 40.0) and (data_integrity == DataIntegrity.VALID) and not vetoes and tech_resp.technicals is not None
    
    # --- SIGNAL MATH ---
    sig = tech_resp.algo_signal or get_empty_algo_signal() # Fallback for missing signal
    signal_strength = sig.overall_score.value / 100
    # Normalize expectancy_val to [-1, 1] range
    expectancy_val = (sig.volume_score.value - 50) / 50 if sig.confluence_score > 5 else 0.0
    
    # 30/20/25/25 Weighting
    t_comp = round(sig.trend_score.value/100, 3) if sig.trend_score.value > 0 else 0.0
    m_comp = round(sig.momentum_score.value/100, 3)
    v_comp = -1.0 if is_overvalued else 1.0 # Scale to full weight
    
    primary_signal = round((t_comp*0.3 + m_comp*0.2 + expectancy_val*0.25 + v_comp*0.25), 3)

    # --- STAGE 2: NARRATIVE ENGINE ---
    l3_start = time.time()
    ai_analysis = None
    fallback_used = False
    
    # Determine if we skip AI
    # Audit Fix: Never skip AI if there are active vetoes or conflicts, as human insight is required.
    has_conflicts = bool(vetoes) or (global_conf < 40)
    should_skip_ai = (primary_signal < 0.15 and not has_conflicts) or (time.time() - start_time) > 6 or (mode == "execution")
    should_skip_ai = should_skip_ai and not force_ai
    
    if should_skip_ai:
        pipeline_logger.log_event(requested_ticker, "AI", "BYPASS", "Fast path triggered.")
        fallback_used = True
    else:
        try:
            ai_task = interpret_advanced(technical_response=tech_resp, fundamental_response=fund_resp, news_response=news_resp, market_context=market_context, mode=mode, force_ai=force_ai)
            ai_analysis = await asyncio.wait_for(ai_task, timeout=30.0)
        except Exception as e:
            pipeline_logger.log_error(requested_ticker, "AI", f"Synthesis Error: {str(e)}")
            if not force_ai:
                fallback_used = True
            else:
                # In force_ai mode, we want to know it failed rather than silent fallback
                ai_analysis = None
                fallback_used = True

    if force_ai and not ai_analysis:
         pipeline_logger.log_error(requested_ticker, "AI", "Force AI failed to produce analysis.")
         fallback_used = True

    if ai_analysis:
        _enforce_confidence_ceiling(ai_analysis, global_conf, is_authorized, tech_resp.trade_setup.confidence.label)
        _sanitize_ai_signals(ai_analysis, tech_resp.technicals)

    total_latency = (time.time() - start_time) * 1000
    final_summary = ai_analysis.executive_summary if ai_analysis else f"Audit complete. Confidence: {global_conf:.1f}%"

    # Final Response Construction
    meta = ResponseMeta(ticker=requested_ticker, timestamp=now_utc, analysis_id=f"{requested_ticker}_{int(start_time)}", data_version="market_v3.2")
    
    execution = ExecutionBlock(
        action=tech_resp.trade_setup.action, authorized=is_authorized, 
        urgency=_calculate_urgency(is_authorized, global_conf), valid_until=now_utc + timedelta(minutes=30),
        risk_limits=RiskLimits(max_position_pct=settings.MAX_POSITION_PCT, max_capital_risk_pct=round(min(1.0, (tech_resp.technicals.atr_percent if tech_resp.technicals else 1.5)*0.67), 2), daily_loss_limit_pct=3.0),
        vetoes=vetoes
    )
    
    final_response = AdvancedStockResponse(
        meta=meta, execution=execution,
        signals=SignalsBlock(
            actionable=is_authorized, primary_signal_strength=primary_signal, required_strength=0.35,
            components={
                "trend": SignalComponent(score=round(sig.trend_score.value/100, 2), weight=0.3, signal=sig.trend_score.label),
                "momentum": SignalComponent(score=round(sig.momentum_score.value/100, 2), weight=0.2, signal=sig.momentum_score.label),
                "expectancy": SignalComponent(score=round(expectancy_val, 2), weight=0.25, signal="CALCULATED" if expectancy_val != 0 else "UNAVAILABLE"),
                "valuation": SignalComponent(score=float(v_comp), weight=0.25, signal="OVERVALUED" if is_overvalued else "VALUED")
            }
        ),
        levels=LevelsBlock(current=price, timestamp=now_utc, support=_calculate_support_levels(tech_resp), resistance=_calculate_resistance_levels(tech_resp), value_zones=_calculate_value_zones(price, tech_resp.technicals) if tech_resp.technicals else []),
        context=ContextBlock(regime="TRENDING" if adx_val > 25 else "RANGE_BOUND", regime_confidence=round(1 - abs(adx_val - 25)/50, 2), trend_strength_adx=adx_val, volatility_atr_pct=tech_resp.technicals.atr_percent if tech_resp.technicals else 0, volume_ratio=tech_resp.technicals.volume_ratio if tech_resp.technicals else 0),
        human_insight=HumanInsightBlock(summary=final_summary, key_conflicts=_identify_conflicts(tech_resp, market_context), scenarios=_generate_actionable_scenarios(tech_resp, market_context), monitor_triggers=["ADX > 25", "EMA20 Test"]),
        system=SystemBlock(confidence=round(global_conf, 1), data_quality=data_integrity, blocking_issues=[], data_state_taxonomy=data_state_taxonomy, latency_ms=total_latency, layer_timings={"l0_l1_l2_sensors": sensor_latency, "l3_synthesis": (time.time() - l3_start) * 1000}, next_update=now_utc + timedelta(minutes=15), latency_sla_violated=total_latency > 5000, fallback_used=fallback_used, engine_logic="HYBRID" if ai_analysis else "DETERMINISTIC"),
        market_context=market_context,
        ai_analysis=ai_analysis
    )
    
    pipeline_logger.log_payload(requested_ticker, "FINAL", "RESULT", final_response)
    return final_response

def _calculate_value_zones(current_price: float, tech: Technicals) -> List[ValueZone]:
    ema20 = tech.ema_20 or current_price
    if current_price < ema20: return [ValueZone(min=round(ema20 * 0.97, 2), max=round(ema20, 2), attractiveness=0.6, type="RECLAMATION_ZONE")]
    else: return [ValueZone(min=round(ema20, 2), max=round(ema20 * 1.03, 2), attractiveness=0.8, type="SUPPORT_ZONE")]

def _calculate_urgency(authorized: bool, confidence: float) -> str:
    if not authorized: return "LOW"
    return "IMMEDIATE" if confidence > 85 else ("HIGH" if confidence > 70 else "MEDIUM")

def _calculate_support_levels(tech: TechnicalStockResponse) -> List[LevelItem]:
    levels, p = [], tech.current_price
    if tech.technicals and tech.technicals.support_s1: levels.append(LevelItem(price=tech.technicals.support_s1, strength=0.7, type="PIVOT_S1", distance_pct=((tech.technicals.support_s1/p)-1)*100))
    if tech.trade_setup.stop_loss: levels.append(LevelItem(price=tech.trade_setup.stop_loss, strength=0.9, type="ATR_STOP", distance_pct=((tech.trade_setup.stop_loss/p)-1)*100))
    return levels

def _calculate_resistance_levels(tech: TechnicalStockResponse) -> List[LevelItem]:
    levels, p = [], tech.current_price
    if tech.technicals and tech.technicals.resistance_r1: levels.append(LevelItem(price=tech.technicals.resistance_r1, strength=0.7, type="PIVOT_R1", distance_pct=((tech.technicals.resistance_r1/p)-1)*100))
    return levels

def _create_rejected_response(ticker: str, mode: str, pre_dec: TradingDecision, context: MarketContext, l0_time: float) -> AdvancedStockResponse:
    now = datetime.now(timezone.utc)
    return AdvancedStockResponse(
        meta=ResponseMeta(ticker=ticker.upper(), timestamp=now, analysis_id=f"{ticker.upper()}_{int(time.time())}"),
        execution=ExecutionBlock(action=TradeAction.REJECT, authorized=False, urgency="LOW", valid_until=now + timedelta(hours=1), risk_limits=RiskLimits(max_position_pct=0, max_capital_risk_pct=0, daily_loss_limit_pct=0)),
        signals=SignalsBlock(actionable=False, primary_signal_strength=0, required_strength=0.25, components={}),
        levels=LevelsBlock(current=0, timestamp=now, support=[], resistance=[], value_zones=[]),
        context=ContextBlock(regime="UNKNOWN", regime_confidence=0, trend_strength_adx=0, volatility_atr_pct=0, volume_ratio=0),
        human_insight=HumanInsightBlock(summary=pre_dec.primary_reason, key_conflicts=[pre_dec.primary_reason], scenarios={}, monitor_triggers=[]),
        system=SystemBlock(confidence=0, data_quality=DataIntegrity.INVALID, blocking_issues=pre_dec.violation_rules, latency_ms=l0_time, layer_timings={"l0_context": l0_time}, next_update=now + timedelta(minutes=15)),
        market_context=context
    )

def _identify_conflicts(tech: TechnicalStockResponse, ctx: MarketContext) -> List[str]:
    conflicts = []
    if tech.technicals and tech.algo_signal and tech.algo_signal.overall_score.value > 20 and (tech.technicals.adx or 0) < 20: conflicts.append("Momentum/Trend conflict")
    if ctx and ctx.price_target and ctx.price_target.mean and tech.current_price > ctx.price_target.mean: conflicts.append(f"Valuation/Price conflict")
    return conflicts

def _generate_actionable_scenarios(tech: TechnicalStockResponse, ctx: MarketContext) -> Dict[str, Any]:
    price = tech.current_price
    atr = (tech.technicals.atr if tech.technicals else None) or price * 0.015
    r1 = (tech.technicals.resistance_r1 if tech.technicals else None) or price * 1.02
    s1 = (tech.technicals.support_s1 if tech.technicals else None) or price * 0.98
    
    # Audit Fix: Zero division guard
    bear_prob = round(min(0.3, (abs(price - s1) / atr) / 10), 2) if atr > 0 else 0.1
    bull_prob = 0.25
    return {"bullish": {"prob": bull_prob, "target": round(r1 * 1.05, 2), "trigger": f"Break above {r1:.2f}"}, "bearish": {"prob": bear_prob, "target": round(s1 * 0.95, 2), "trigger": f"Break below {s1:.2f}"}, "neutral": {"prob": round(1.0 - bull_prob - bear_prob, 2), "desc": "Range consolidation"}}

def _enforce_confidence_ceiling(ai_res: AIAnalysisResult, ceiling: float, is_authorized: bool, label: str):
    for h in [ai_res.intraday, ai_res.swing, ai_res.positional, ai_res.longterm]:
        if h:
            h.confidence = min(h.confidence, ceiling)
            if not is_authorized: h.entry_price = h.target_price = h.stop_loss = 0.0

def _sanitize_ai_signals(ai_result, technicals: Optional[Technicals]):
    if not technicals: return
    poisoned = [p for p in ["cci", "volume"] if getattr(technicals, p, None) is None]
    def clean(signals): return [s for s in signals if not any(p in s.indicator.lower() for p in poisoned)]
    if ai_result.intraday: ai_result.intraday.signals = clean(ai_result.intraday.signals)
    if ai_result.swing: ai_result.swing.signals = clean(ai_result.swing.signals)
    if ai_result.positional: ai_result.positional.signals = clean(ai_result.positional.signals)
    if ai_result.longterm: ai_result.longterm.signals = clean(ai_result.longterm.signals)

def calculate_risk_metrics(returns: Any) -> RiskMetrics:
    if len(returns) < 30: return RiskMetrics()
    sharpe = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else None
    neg = returns[returns < 0]
    sortino = returns.mean() / neg.std() * np.sqrt(252) if len(neg) > 1 else None
    cum = (1 + returns).cumprod()
    max_dd = ((cum - cum.expanding().max()) / cum.expanding().max()).min()
    return RiskMetrics(sharpe_ratio=float(sharpe) if sharpe else None, sortino_ratio=float(sortino) if sortino else None, max_drawdown=float(max_dd) if max_dd else None, standard_deviation=float(returns.std() * np.sqrt(252)))

async def perform_deep_research(ticker: str) -> ResearchReport:
    from .research.engine import ResearchEngine
    import httpx
    
    async def search_wrapper(query: str):
        pipeline_logger.log_event(ticker, "RESEARCH", "SEARCH", f"Query: {query}")
        
        # 1. Try Tavily (Preferred)
        if settings.TAVILY_API_KEY:
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        "https://api.tavily.com/search",
                        json={
                            "api_key": settings.TAVILY_API_KEY,
                            "query": query,
                            "search_depth": "advanced",
                            "include_answer": False,
                            "max_results": 5
                        },
                        timeout=10.0
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    return [{"title": r["title"], "link": r["url"], "snippet": r["content"]} for r in data.get("results", [])]
            except Exception as e:
                pipeline_logger.log_error(ticker, "RESEARCH", f"Tavily Error: {e}")

        # 2. Fallback to Google Custom Search
        if settings.GOOGLE_SEARCH_API_KEY and settings.GOOGLE_CSE_ID:
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(
                        "https://www.googleapis.com/customsearch/v1",
                        params={
                            "key": settings.GOOGLE_SEARCH_API_KEY,
                            "cx": settings.GOOGLE_CSE_ID,
                            "q": query,
                            "num": 5
                        },
                        timeout=10.0
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    return [{"title": r["title"], "link": r["link"], "snippet": r["snippet"]} for r in data.get("items", [])]
            except Exception as e:
                pipeline_logger.log_error(ticker, "RESEARCH", f"Google Search Error: {e}")

        return []
        
    return await ResearchEngine(search_tool=search_wrapper).execute_deep_research(ticker)

async def get_fundamental_analysis(ticker: str) -> Any:
    from fastapi.concurrency import run_in_threadpool
    return await run_in_threadpool(lambda: get_fundamentals(ticker))

async def get_advanced_fundamental_analysis(ticker: str) -> AdvancedFundamentalAnalysis:
    from fastapi.concurrency import run_in_threadpool
    from .fundamentals import get_advanced_fundamentals
    return await run_in_threadpool(lambda: get_advanced_fundamentals(ticker))

async def get_news_analysis(ticker: str) -> NewsResponse:
    from .news_fetcher import UnifiedNewsFetcher
    from .news_intelligence import NewsIntelligenceEngine
    news_items = await UnifiedNewsFetcher.fetch_all(ticker)
    intelligence = NewsIntelligenceEngine.analyze_feed(ticker, news_items)
    return NewsResponse(ticker=ticker.upper(), news=news_items, intelligence=intelligence)