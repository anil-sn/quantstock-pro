from typing import Any
import numpy as np
import pandas as pd
from .market_data import fetch_stock_data
from .technicals import calculate_advanced_technicals, calculate_algo_signal
from .fundamentals import get_fundamentals
from .context import get_market_context
from .ai import interpret_advanced
from .models import (
    AdvancedStockResponse, TechnicalStockResponse, RiskMetrics, 
    TradeSetup, TradeAction, RiskLevel, StockOverview, ScoreDetail, MarketContext
)

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

    # Use pure algo signal for technical-only overview
    action = TradeAction.BUY if algo_signal.overall_score.value > 20 else (TradeAction.SELL if algo_signal.overall_score.value < -20 else TradeAction.HOLD)
    
    if action == TradeAction.BUY:
        stop_loss = current_price - (technicals.atr * 2)
        target = current_price + (technicals.atr * 2)
        entry_zone = (current_price * 0.99, current_price * 1.01)
    elif action == TradeAction.SELL:
        stop_loss = current_price + (technicals.atr * 2)
        target = current_price - (technicals.atr * 2)
        entry_zone = (current_price * 0.99, current_price * 1.01)
    else:
        # HOLD/WAIT: Plan a pending entry at the best value area
        if algo_signal.trend_score.value > 0: # Bullish bias
            # Plan Long from Support
            entry_target = technicals.support_s1
            entry_zone = (entry_target * 0.995, entry_target * 1.005)
            stop_loss = technicals.support_s2
            target = technicals.resistance_r1
            action = TradeAction.WAIT
        else: # Bearish bias
            # Plan Short from Resistance
            entry_target = technicals.resistance_r1
            entry_zone = (entry_target * 0.995, entry_target * 1.005)
            stop_loss = technicals.resistance_r2
            target = technicals.support_s1
            action = TradeAction.WAIT

    overview = StockOverview(
        action=action,
        current_price=current_price,
        target_price=target,
        stop_loss=stop_loss,
        confidence=ScoreDetail(
            value=float(abs(algo_signal.overall_score.value)),
            min_value=0.0,
            max_value=100.0,
            label=(
                "Maximum Conviction" if abs(algo_signal.overall_score.value) >= 90 else
                "High Confidence" if abs(algo_signal.overall_score.value) >= 80 else
                "Normal Trade" if abs(algo_signal.overall_score.value) >= 70 else
                "NO TRADE / WAIT"
            ),
            legend="0-100 scale (Requires >= 70 to trade per Framework)"
        ),
        summary=f"Technical analysis for {ticker.upper()} shows a {action.value} signal. " + 
                ("Score meets confluence threshold." if abs(algo_signal.overall_score.value) >= 70 else "REJECTED: Insufficient confluence for trade.")
    )

    # Calculate Risk-Managed Position Size (1% Account Risk Rule)
    trade_risk_dist_pct = (abs(stop_loss - current_price) / current_price) * 100
    if trade_risk_dist_pct < 0.1: trade_risk_dist_pct = 0.1
    position_size_final = min(5.0, 1.0 / (trade_risk_dist_pct / 100))

    trade_setup = TradeSetup(
        action=action,
        confidence=ScoreDetail(
            value=float(abs(algo_signal.overall_score.value)),
            min_value=0.0,
            max_value=100.0,
            label=(
                "Maximum Conviction" if abs(algo_signal.overall_score.value) >= 90 else
                "High Confidence" if abs(algo_signal.overall_score.value) >= 80 else
                "Normal Trade" if abs(algo_signal.overall_score.value) >= 70 else
                "NO TRADE / WAIT"
            ),
            legend="0-100 scale (Requires >= 70 to trade per Framework)"
        ),
        entry_zone=entry_zone,
        stop_loss=stop_loss,
        stop_loss_pct=trade_risk_dist_pct,
        take_profit_targets=[target],
        risk_reward_ratio=2.0,
        position_size_pct=position_size_final,
        max_capital_at_risk=(position_size_final * trade_risk_dist_pct) / 100,
        setup_quality=algo_signal.volatility_risk
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
        risk_metrics=risk_metrics
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

    # Fetch fundamentals for non-intraday modes
    fundamentals = None
    if mode in ["swing", "positional", "longterm", "all"]:
        fundamentals = get_fundamentals(ticker)

    # Fetch market context (Analyst/Insider/Options)
    market_context = get_market_context(ticker)

    ai_analysis = await interpret_advanced(ticker, technicals, info, mode, fundamentals, market_context)
    if not ai_analysis:
        raise ValueError("AI Analysis failed to generate results.")

    # 5. Build Trade Setup (Swing as primary)
    action = TradeAction.BUY if algo_signal.overall_score.value > 20 else (TradeAction.SELL if algo_signal.overall_score.value < -20 else TradeAction.HOLD)
    
    if action == TradeAction.BUY:
        stop_loss = current_price - (technicals.atr * 2)
        tp_targets = [current_price + (technicals.atr * 2), current_price + (technicals.atr * 4)]
        entry_zone = (current_price * 0.99, current_price * 1.01)
    elif action == TradeAction.SELL:
        stop_loss = current_price + (technicals.atr * 2)
        tp_targets = [current_price - (technicals.atr * 2), current_price - (technicals.atr * 4)]
        entry_zone = (current_price * 0.99, current_price * 1.01)
    else:
        if algo_signal.trend_score.value > 0:
            entry_target = technicals.support_s1
            entry_zone = (entry_target * 0.995, entry_target * 1.005)
            stop_loss = technicals.support_s2
            tp_targets = [technicals.resistance_r1, technicals.resistance_r2]
            action = TradeAction.WAIT
        else:
            entry_target = technicals.resistance_r1
            entry_zone = (entry_target * 0.995, entry_target * 1.005)
            stop_loss = technicals.resistance_r2
            tp_targets = [technicals.support_s1, technicals.support_s2]
            action = TradeAction.WAIT

    # Calculate Risk-Managed Position Size (1% Account Risk Rule)
    trade_risk_dist_pct = (abs(stop_loss - current_price) / current_price) * 100
    if trade_risk_dist_pct < 0.1: trade_risk_dist_pct = 0.1
    position_size_final = min(5.0, 1.0 / (trade_risk_dist_pct / 100))

    trade_setup = TradeSetup(
        action=action,
        confidence=ScoreDetail(
            value=float(abs(algo_signal.overall_score.value)),
            min_value=0.0,
            max_value=100.0,
            label=(
                "Maximum Conviction" if abs(algo_signal.overall_score.value) >= 90 else
                "High Confidence" if abs(algo_signal.overall_score.value) >= 80 else
                "Normal Trade" if abs(algo_signal.overall_score.value) >= 70 else
                "NO TRADE / WAIT"
            ),
            legend="0-100 scale (Requires >= 70 to trade per Framework)"
        ),
        entry_zone=entry_zone,
        stop_loss=stop_loss,
        stop_loss_pct=trade_risk_dist_pct,
        take_profit_targets=tp_targets,
        risk_reward_ratio=2.0,
        position_size_pct=position_size_final,
        max_capital_at_risk=(position_size_final * trade_risk_dist_pct) / 100,
        setup_quality=algo_signal.volatility_risk
    )

    # 6. Build Overview (Preferring AI Swing perspective for the summary)
    overview = StockOverview(
        action=ai_analysis.swing.action,
        current_price=current_price,
        target_price=ai_analysis.swing.target_price,
        stop_loss=ai_analysis.swing.stop_loss,
        confidence=ai_analysis.swing.confidence,
        summary=ai_analysis.executive_summary
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
        market_context=market_context
    )

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
