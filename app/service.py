import asyncio
from typing import Any, Tuple, Optional, List, Dict
from datetime import datetime
import numpy as np
import pandas as pd
from .market_data import fetch_stock_data
from .technicals import calculate_advanced_technicals, calculate_algo_signal
from .fundamentals import get_fundamentals, get_news
from .context import get_market_context
from .models import (
    AdvancedStockResponse, TechnicalStockResponse, RiskMetrics, 
    TradeSetup, TradeAction, RiskLevel, StockOverview, ScoreDetail, MarketContext,
    DataIntegrity, DecisionState, SetupState, SetupQuality, AlgoSignal, Technicals,
    TradingDecision, NewsResponse, AdvancedFundamentalAnalysis, OHLCV, MultiHorizonSetups,
    TrendDirection, PipelineStageState, PipelineState, PipelineTrace, SensorStatus, ResearchReport,
    WeightDetail, AIAnalysisResult, HorizonPerspective, OptionsAdvice, MarketSentiment
)
from .risk import RiskEngine, RiskParameters
from .governor import SignalGovernor, UnifiedRejectionTracker
from .executor import TradeExecutor
from .logger import pipeline_logger

# ============== CORE LOGIC ============== 

class STierTradingSystem:
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

    def analyze(self, technicals: Technicals, algo_signal: AlgoSignal, market_context: Optional[MarketContext], fundamentals: Any) -> TradingDecision:
        tracker = UnifiedRejectionTracker()
        data_integrity = self.governor.assess_data_integrity(technicals, market_context)
        if data_integrity == DataIntegrity.INVALID:
            pipeline_logger.log_event("N/A", "LAYER_1", "FAILED", "Critical data missing")
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
        
        if abs(score) < 20 or base_confidence < self.risk_engine.params.confidence_threshold:
             return self._create_wait_decision(SetupState.VALID, base_confidence, "Insufficient signals")

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

s_tier_system = STierTradingSystem()

def _process_horizon(data_result: Dict[str, Any], market_context: Optional[MarketContext]) -> Tuple[Optional[TradeSetup], Optional[Technicals], Optional[AlgoSignal], Optional[TradingDecision]]:
    if not data_result: return None, None, None, None
    df, current_price = data_result["dataframe"], data_result["current_price"]
    tech = calculate_advanced_technicals(df)
    sig = calculate_algo_signal(tech)
    dec = s_tier_system.analyze(tech, sig, market_context, None)
    action = TradeAction.REJECT if dec.decision_state == DecisionState.REJECT else (TradeAction.WAIT if dec.decision_state == DecisionState.WAIT else (TradeAction.BUY if sig.overall_score.value > 0 else TradeAction.SELL))
    sl, tp, entry = s_tier_system.executor.calculate_levels(action, tech, current_price)
    setup = TradeSetup(action=action, confidence=s_tier_system.executor.create_score_detail(dec.confidence, "Evidence Quality"), entry_zone=entry, stop_loss=sl, stop_loss_pct=(abs(current_price-sl)/current_price)*100 if current_price and sl else None, take_profit_targets=tp, risk_reward_ratio=dec.risk_reward_ratio, position_size_pct=dec.position_size_pct, max_capital_at_risk=dec.max_capital_at_risk, setup_state=dec.setup_state, setup_quality=dec.setup_quality)
    return setup, tech, sig, dec

async def get_technical_analysis(ticker: str) -> TechnicalStockResponse:
    from fastapi.concurrency import run_in_threadpool
    requested_ticker = ticker.upper()
    market_context = await run_in_threadpool(lambda: get_market_context(requested_ticker))
    pre_decision = s_tier_system.pre_screen(market_context)
    if pre_decision:
        reject_setup = TradeSetup(action=TradeAction.REJECT, confidence=ScoreDetail(value=0, min_value=0, max_value=100, label="Rejected", legend=""), setup_state=SetupState.SKIPPED)
        horizons = MultiHorizonSetups(intraday=reject_setup, swing=reject_setup, positional=reject_setup, longterm=reject_setup)
        return TechnicalStockResponse(overview=StockOverview(action=TradeAction.REJECT, current_price=0.0, confidence=reject_setup.confidence, summary=pre_decision.primary_reason), requested_ticker=requested_ticker, ticker=requested_ticker, trade_setup=reject_setup, horizons=horizons, raw_data=None, pipeline_state=PipelineState(pre_screen=PipelineStageState.FAILED, technicals=PipelineStageState.SKIPPED, scoring=PipelineStageState.SKIPPED, execution=PipelineStageState.SKIPPED), decision_state=DecisionState.REJECT, data_integrity=DataIntegrity.NOT_EVALUATED)

    horizons_map = {"intraday": "60m", "swing": "1d", "positional": "1wk", "longterm": "1mo"}
    tasks = [fetch_stock_data(requested_ticker, interval=interval) for interval in horizons_map.values()]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    data_results = {key: (None if isinstance(results[i], Exception) else results[i]) for i, key in enumerate(horizons_map.keys())}
    setup_results, technical_results, signal_results, decision_results = {}, {}, {}, {}
    for key, data_res in data_results.items():
        if data_res:
             setup, tech, sig, dec = _process_horizon(data_res, market_context)
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

    primary_data = data_results["swing"]
    return TechnicalStockResponse(overview=StockOverview(action=setup_results["swing"].action, current_price=primary_data["current_price"], confidence=setup_results["swing"].confidence, summary=f"Audit complete. Confidence: {global_conf:.1f}%"), requested_ticker=requested_ticker, ticker=requested_ticker, company_name=primary_data["info"].get("longName"), sector=primary_data["info"].get("sector"), current_price=primary_data["current_price"], price_change_1d=float(primary_data["dataframe"]['Close'].pct_change().iloc[-1] * 100) if len(primary_data["dataframe"]) > 1 else None, technicals=technical_results["swing"], algo_signal=signal_results["swing"], trade_setup=setup_results["swing"], horizons=MultiHorizonSetups(intraday=setup_results["intraday"], swing=setup_results["swing"], positional=setup_results["positional"], longterm=setup_results["longterm"]), raw_data=[], pipeline_state=PipelineState(pre_screen=PipelineStageState.PASSED, technicals=PipelineStageState.PASSED, scoring=PipelineStageState.PASSED, execution=PipelineStageState.SKIPPED), data_confidence=global_conf, data_integrity=DataIntegrity.VALID if global_conf > 25 else DataIntegrity.DEGRADED, decision_state=primary_dec.decision_state if primary_dec else DecisionState.WAIT)

async def analyze_stock(ticker: str, mode: Any = "all") -> AdvancedStockResponse:
    from fastapi.concurrency import run_in_threadpool
    from .ai import interpret_advanced
    from .models import AIAnalysisResult, HorizonPerspective, OptionsAdvice, MarketSentiment, PipelineStageState, PipelineState, PipelineTrace, SensorStatus

    requested_ticker = ticker.upper()
    pipeline_logger.log_event(requested_ticker, "BRAIN", "START", f"Synthesis mode={mode}")
    market_context = await run_in_threadpool(lambda: get_market_context(requested_ticker))
    pipeline_logger.log_payload(requested_ticker, "LAYER_0", "CONTEXT", market_context)

    pre_dec = s_tier_system.pre_screen(market_context)
    if pre_dec:
        pipeline_logger.log_event(requested_ticker, "LAYER_0", "REJECT", pre_dec.primary_reason)
        try:
            data = await fetch_stock_data(requested_ticker, interval="1d")
            current_price, info, price_change = data["current_price"], data["info"], float(data["dataframe"]['Close'].pct_change().iloc[-1] * 100)
        except: current_price = price_change = 0.0; info = {}
        reject_setup = TradeSetup(action=TradeAction.REJECT, confidence=ScoreDetail(value=0, min_value=0, max_value=100, label="None", legend=""), setup_state=SetupState.SKIPPED)
        return AdvancedStockResponse(analysis_mode=mode, overview=StockOverview(action=TradeAction.REJECT, current_price=current_price, confidence=reject_setup.confidence, summary=pre_dec.primary_reason), requested_ticker=requested_ticker, ticker=requested_ticker, company_name=info.get("longName"), sector=info.get("sector"), current_price=current_price, price_change_1d=price_change, technicals=None, algo_signal=None, trade_setup=reject_setup, ai_analysis=AIAnalysisResult(executive_summary=pre_dec.primary_reason, investment_thesis="Rejected", intraday=None, swing=None, positional=None, longterm=None, options_fno=None, market_sentiment=None), pipeline_state=PipelineState(pre_screen=PipelineStageState.FAILED, technicals=PipelineStageState.SKIPPED, scoring=PipelineStageState.SKIPPED, execution=PipelineStageState.SKIPPED), decision_state=DecisionState.REJECT, data_integrity=DataIntegrity.NOT_EVALUATED)

    # --- NORMAL FLOW ---
    pipeline_logger.log_event(requested_ticker, "LAYER_1", "START", "Gathering multi-sensor analysis")
    tasks = [get_technical_analysis(requested_ticker), get_advanced_fundamental_analysis(requested_ticker) if mode != "intraday" else run_in_threadpool(lambda: None), get_news_analysis(requested_ticker)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    tech_resp = results[0]
    if isinstance(tech_resp, Exception): 
        pipeline_logger.error(requested_ticker, "LAYER_1", f"Technical analysis failed: {tech_resp}")
        raise tech_resp
    
    # --- AUDIT FIX: SENSOR FAILURE PROPAGATION ---
    data_integrity = tech_resp.data_integrity
    global_conf = tech_resp.data_confidence
    
    # Fundamental and News are non-fatal but impact integrity
    fund_resp = results[1] if not isinstance(results[1], Exception) else None
    if isinstance(results[1], Exception):
        data_integrity = DataIntegrity.DEGRADED
        pipeline_logger.log_event(requested_ticker, "LAYER_1", "DEGRADED", "Fundamental sensor failure. Data integrity downgraded.")
        
    news_resp = results[2] if not isinstance(results[2], Exception) else None
    if isinstance(results[2], Exception):
        data_integrity = DataIntegrity.DEGRADED
        pipeline_logger.log_event(requested_ticker, "LAYER_1", "DEGRADED", "News sensor failure. Data integrity downgraded.")

    # --- AUDIT FIX: CONFIDENCE CEILING & BLINDNESS CAP ---
    # If system is operating "partially dark" (Degraded), cap confidence at 40%
    if data_integrity == DataIntegrity.DEGRADED:
        global_conf = min(global_conf, 40.0)
        pipeline_logger.log_event(requested_ticker, "LAYER_4", "THROTTLE", "Integrity Degraded: Confidence capped at 40%.")

    # --- AUDIT FIX: GLOBAL AUTHORITY LAYER ---
    is_authorized = (global_conf >= 40.0) and (data_integrity == DataIntegrity.VALID)
    
    # --- CONFIDENCE KILL-SWITCH (Audit v18.0 / v20.0 Enforcement) ---
    if global_conf < 25:
        pipeline_logger.log_event(requested_ticker, "BRAIN", "ABORTED", f"Confidence {global_conf}% below floor. Skipping synthesis.")
        # Ensure tech_resp setup is also nulled if not already done
        tech_resp.trade_setup.entry_zone = None
        tech_resp.trade_setup.stop_loss = None
        tech_resp.trade_setup.take_profit_targets = None
        
        return AdvancedStockResponse(
            analysis_mode=mode, overview=tech_resp.overview, requested_ticker=requested_ticker, ticker=tech_resp.ticker,
            company_name=tech_resp.company_name, sector=tech_resp.sector, current_price=tech_resp.current_price,
            price_change_1d=tech_resp.price_change_1d, technicals=tech_resp.technicals, algo_signal=tech_resp.algo_signal,
            trade_setup=tech_resp.trade_setup, ai_analysis=None, risk_metrics=None, market_context=market_context,
            pipeline_state=tech_resp.pipeline_state, data_confidence=global_conf, is_trade_authorized=False,
            data_integrity=data_integrity, decision_state=tech_resp.decision_state
        )

    # Forensic Payload Logging
    pipeline_logger.log_payload(requested_ticker, "LAYER_1", "TECH_PAYLOAD", tech_resp)
    
    ai_analysis = await interpret_advanced(technical_response=tech_resp, fundamental_response=fund_resp, news_response=news_resp, market_context=market_context, mode=mode)
    if not ai_analysis: raise ValueError("AI Analysis failed")

    # --- AUDIT FIX: AUTHORITY ENFORCEMENT & CEILING ---
    ai_analysis.swing.action = tech_resp.trade_setup.action
    # Ceiling Enforcement: AI cannot exceed Global System Confidence
    global_dec = tech_resp.decision_state
    
    for h in [ai_analysis.intraday, ai_analysis.swing, ai_analysis.positional, ai_analysis.longterm]:
        if h:
            # Force matching action
            if global_dec != DecisionState.ACCEPT:
                h.action = TradeAction.REJECT if global_dec == DecisionState.REJECT else TradeAction.WAIT
            
            # HARD CLAMP: Reported confidence MUST respect the global ceiling
            h.confidence.value = min(h.confidence.value, global_conf)
            h.confidence.label = tech_resp.trade_setup.confidence.label
            
            # NULL OUT targets if not authorized
            if not is_authorized:
                h.entry_price = h.target_price = h.stop_loss = 0.0

    # Final exposure enforcement on top-level response
    if not is_authorized:
        tech_resp.trade_setup.position_size_pct = 0.0
        tech_resp.trade_setup.max_capital_at_risk = 0.0
        tech_resp.trade_setup.entry_zone = None
        tech_resp.trade_setup.stop_loss = None
        tech_resp.trade_setup.take_profit_targets = None

    _sanitize_ai_signals(ai_analysis, tech_resp.technicals)
    
    final_response = AdvancedStockResponse(
        analysis_mode=mode, overview=tech_resp.overview, requested_ticker=requested_ticker, ticker=tech_resp.ticker, company_name=tech_resp.company_name,
        sector=tech_resp.sector, current_price=tech_resp.current_price, price_change_1d=tech_resp.price_change_1d,
        technicals=tech_resp.technicals, algo_signal=tech_resp.algo_signal, trade_setup=tech_resp.trade_setup,
        ai_analysis=ai_analysis, risk_metrics=tech_resp.risk_metrics, market_context=market_context,
        pipeline_state=tech_resp.pipeline_state, data_confidence=global_conf, is_trade_authorized=is_authorized,
        data_integrity=data_integrity, decision_state=tech_resp.decision_state
    )
    pipeline_logger.log_payload(requested_ticker, "FINAL", "RESULT", final)
    return final
def _sanitize_ai_signals(ai_result, technicals: Optional[Technicals]):
    if not technicals: return
    poisoned = []
    if technicals.cci is None: poisoned.append("cci")
    if technicals.volume_ratio is None: poisoned.append("volume")
    def clean(signals): return [s for s in signals if not any(p in s.indicator.lower() for p in poisoned)]
    ai_result.intraday.signals = clean(ai_result.intraday.signals)
    ai_result.swing.signals = clean(ai_result.swing.signals)
    ai_result.positional.signals = clean(ai_result.positional.signals)
    ai_result.longterm.signals = clean(ai_result.longterm.signals)

def calculate_risk_metrics(returns: Any) -> RiskMetrics:
    if len(returns) < 30: return RiskMetrics()
    sharpe = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else None
    neg = returns[returns < 0]
    sortino = returns.mean() / neg.std() * np.sqrt(252) if len(neg) > 1 else None
    cum = (1 + returns).cumprod()
    max_dd = ((cum - cum.expanding().max()) / cum.expanding().max()).min()
    return RiskMetrics(sharpe_ratio=float(sharpe) if sharpe else None, sortino_ratio=float(sortino) if sortino else None, max_drawdown=float(max_dd) if max_dd else None, standard_deviation=float(returns.std() * np.sqrt(252)))

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

async def perform_deep_research(ticker: str) -> ResearchReport:
    from .research.engine import ResearchEngine
    async def google_api_search(query: str):
        try: return await google_web_search(query=query)
        except: return []
    return await ResearchEngine(search_tool=google_api_search).execute_deep_research(ticker)