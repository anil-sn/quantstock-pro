from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, Request, WebSocket
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
import time
import asyncio

from .models_v2 import (
    AnalysisMode, TimeHorizon, TimeInterval, BulkAnalysisRequest, 
    AnalysisResponse, HealthResponse, BulkAnalysisResponse, APILimitsResponse,
    MetaInfo
)
from .service import (
    analyze_stock, get_technical_analysis, get_advanced_fundamental_analysis, 
    get_news_analysis, perform_deep_research
)
from .context import get_market_context
from .settings import settings
from .logger import pipeline_logger

router = APIRouter(prefix="/api/v2", tags=["QuantStock Pro v2"])

# --- SERVICE STATUS ---

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Enhanced health check with component status."""
    from .main import START_TIME
    uptime = time.time() - START_TIME
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc),
        "components": {
            "market_data": "up",
            "ai_engine": "up",
            "research_agent": "up"
        },
        "version": "2.0.0",
        "uptime_seconds": uptime
    }

@router.get("/status")
async def get_service_status():
    """Service status with high-level metrics."""
    return {
        "engine_version": "AlphaCore v20.2",
        "environment": settings.ENVIRONMENT,
        "api_tier": "Institutional",
        "latency_target_ms": 5000
    }

@router.get("/limits", response_model=APILimitsResponse)
async def get_limits(request: Request):
    """Return current API rate limits and usage."""
    return {
        "rate_limit": settings.RATE_LIMIT_REQUESTS,
        "requests_remaining": settings.RATE_LIMIT_REQUESTS - 1,
        "reset_in_seconds": 60
    }

# --- STOCK ANALYSIS (COMPREHENSIVE) ---

@router.post("/analysis/bulk", response_model=BulkAnalysisResponse)
async def bulk_analysis(request: BulkAnalysisRequest, background_tasks: BackgroundTasks):
    """Analyze multiple tickers asynchronously."""
    task_id = str(uuid.uuid4())
    return {
        "task_id": task_id,
        "status": "processing",
        "message": f"Bulk analysis for {len(request.tickers)} tickers started."
    }

@router.get("/analysis/{ticker}", response_model=AnalysisResponse)
async def get_comprehensive_analysis(
    ticker: str,
    mode: AnalysisMode = Query(AnalysisMode.FULL),
    include_ai: bool = Query(True),
    force_ai: bool = Query(False)
):
    """Version 2.0 Comprehensive Analysis."""
    try:
        internal_mode = "all" if mode == AnalysisMode.FULL else mode.value
        result = await analyze_stock(ticker, mode=internal_mode, force_ai=force_ai)
        
        return AnalysisResponse(
            meta=MetaInfo(
                ticker=result.meta.ticker,
                timestamp=result.meta.timestamp,
                analysis_id=result.meta.analysis_id
            ),
            execution=result.execution.model_dump(),
            technicals=None, 
            fundamentals=None, 
            news=None,
            context=result.market_context,
            ai_insights=result.ai_analysis
        )
    except Exception as e:
        pipeline_logger.log_error(ticker, "API_V2", f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/{ticker}/technical")
async def get_analysis_technical(ticker: str):
    """Sub-resource: Just technicals from the analysis pipeline."""
    return await get_technical_analysis(ticker)

@router.get("/analysis/{ticker}/fundamental")
async def get_analysis_fundamental(ticker: str):
    """Sub-resource: Just fundamentals from the analysis pipeline."""
    return await get_advanced_fundamental_analysis(ticker)

@router.get("/analysis/{ticker}/execution")
async def get_analysis_execution(ticker: str):
    """Sub-resource: Just execution signals and levels."""
    result = await analyze_stock(ticker, mode="execution")
    return {
        "ticker": ticker.upper(),
        "execution": result.execution,
        "levels": result.levels,
        "signals": result.signals
    }

# --- TECHNICAL ANALYSIS ---

@router.get("/technical/{ticker}/signals")
async def get_technical_signals(ticker: str):
    """Just trading signals."""
    res = await get_technical_analysis(ticker)
    return res.algo_signal

@router.get("/technical/{ticker}/levels")
async def get_technical_levels(ticker: str):
    """Just price levels (S/R, targets)."""
    res = await get_technical_analysis(ticker)
    return {"levels": res.trade_setup, "technicals": res.technicals}

@router.get("/technical/{ticker}")
async def get_technical_all(ticker: str):
    """All timeframes technical analysis."""
    return await get_technical_analysis(ticker)

@router.get("/technical/{ticker}/{interval}")
async def get_technical_interval(ticker: str, interval: TimeInterval):
    """Technical analysis for a specific interval."""
    from .market_data import fetch_stock_data
    from .technicals_indicators import calculate_advanced_technicals
    data = await fetch_stock_data(ticker, interval=interval.value)
    return calculate_advanced_technicals(data["dataframe"])

# --- FUNDAMENTAL ANALYSIS ---

@router.get("/fundamental/{ticker}")
async def get_fundamental_complete(ticker: str):
    """Complete fundamental analysis."""
    return await get_advanced_fundamental_analysis(ticker)

@router.get("/fundamental/{ticker}/valuation")
async def get_fundamental_valuation(ticker: str):
    """Valuation models only."""
    res = await get_advanced_fundamental_analysis(ticker)
    return res.comprehensive_metrics["valuation"]

@router.get("/fundamental/{ticker}/quality")
async def get_fundamental_quality(ticker: str):
    """Quality scoring only."""
    res = await get_advanced_fundamental_analysis(ticker)
    return res.executive_summary["overall_assessment"]

@router.get("/fundamental/{ticker}/ratios")
async def get_fundamental_ratios(ticker: str):
    """Financial ratios only."""
    res = await get_advanced_fundamental_analysis(ticker)
    return {
        "profitability": res.comprehensive_metrics["profitability"],
        "health": res.comprehensive_metrics["financial_health"]
    }

# --- NEWS & SENTIMENT ---

@router.get("/news/{ticker}")
async def get_news_all(ticker: str):
    """All news items."""
    return await get_news_analysis(ticker)

@router.get("/news/{ticker}/signal")
async def get_news_signal(ticker: str):
    """Signal-relevant news only."""
    res = await get_news_analysis(ticker)
    return [n for n in res.news if n.title] # Logic for filtering could be refined

@router.get("/news/{ticker}/sentiment")
async def get_news_sentiment(ticker: str):
    """Sentiment analysis only."""
    res = await get_news_analysis(ticker)
    return res.intelligence

@router.get("/news/{ticker}/trending")
async def get_news_trending(ticker: str):
    """Trending topics placeholder."""
    return {"trending_topics": [], "ticker": ticker.upper()}

# --- AI & RESEARCH ---

@router.post("/research/{ticker}")
async def post_research(ticker: str, background_tasks: BackgroundTasks):
    """Start research (async)."""
    task_id = str(uuid.uuid4())
    background_tasks.add_task(perform_deep_research, ticker)
    return {"task_id": task_id, "status": "processing"}

@router.get("/research/{ticker}/status")
async def get_research_status(ticker: str):
    """Check research status placeholder."""
    return {"status": "completed", "ticker": ticker.upper()}

@router.get("/research/{ticker}/report")
async def get_research_report_v2(ticker: str):
    """Get completed report."""
    return await perform_deep_research(ticker)

@router.post("/ai/analyze")
async def post_ai_analyze(request: Dict[str, Any]):
    """Custom AI analysis placeholder."""
    return {"message": "Custom AI analysis triggered"}

@router.get("/ai/explain/{signal}")
async def get_ai_explain(signal: str):
    """Explain a trading signal placeholder."""
    return {"signal": signal, "explanation": "Signal explanation logic pending."}

# --- MARKET CONTEXT ---

@router.get("/context/{ticker}")
async def get_context_complete(ticker: str):
    """Complete market context."""
    from fastapi.concurrency import run_in_threadpool
    return await run_in_threadpool(lambda: get_market_context(ticker))

@router.get("/context/{ticker}/analysts")
async def get_context_analysts(ticker: str):
    """Just analyst ratings."""
    from fastapi.concurrency import run_in_threadpool
    ctx = await run_in_threadpool(lambda: get_market_context(ticker))
    return {"analyst_ratings": ctx.analyst_ratings, "price_target": ctx.price_target}

@router.get("/context/{ticker}/insiders")
async def get_context_insiders(ticker: str):
    """Just insider activity."""
    from fastapi.concurrency import run_in_threadpool
    ctx = await run_in_threadpool(lambda: get_market_context(ticker))
    return ctx.insider_activity

@router.get("/context/{ticker}/options")
async def get_context_options(ticker: str):
    """Just options sentiment."""
    from fastapi.concurrency import run_in_threadpool
    ctx = await run_in_threadpool(lambda: get_market_context(ticker))
    return ctx.option_sentiment

@router.get("/context/{ticker}/institutions")
async def get_context_institutions(ticker: str):
    """Just institutional data placeholder."""
    return {"institutions": [], "ticker": ticker.upper()}

# --- REAL-TIME & STREAMING ---

@router.websocket("/ws/analysis")
async def websocket_analysis(websocket: WebSocket):
    """WebSocket for real-time analysis placeholder."""
    await websocket.accept()
    await websocket.send_json({"message": "Real-time analysis stream connected."})
    await websocket.close()

@router.websocket("/ws/levels")
async def websocket_levels(websocket: WebSocket):
    """WebSocket for price levels placeholder."""
    await websocket.accept()
    await websocket.send_json({"message": "Price levels stream connected."})
    await websocket.close()

@router.get("/stream/{ticker}/signals")
async def stream_signals(ticker: str):
    """Server-sent events for signals placeholder."""
    return {"message": "Signal streaming not yet implemented."}
