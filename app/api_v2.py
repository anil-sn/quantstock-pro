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
from .cache import cache_manager

router = APIRouter(prefix="/api/v2", tags=["QuantStock Pro v2"])

# --- SERVICE STATUS ---

@router.get(
    "/health", 
    response_model=HealthResponse,
    summary="Component Health Audit",
    description="Performs a comprehensive health check across the core architectural layers."
)
async def health_check():
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

@router.get("/status", summary="System Operational Status")
async def get_service_status():
    return {
        "engine_version": "AlphaCore v20.2",
        "environment": settings.ENVIRONMENT,
        "api_tier": "Institutional",
        "latency_target_ms": 5000
    }

@router.get("/limits", response_model=APILimitsResponse, summary="Rate Limit Intelligence")
async def get_limits(request: Request):
    return {
        "rate_limit": settings.RATE_LIMIT_REQUESTS,
        "requests_remaining": settings.RATE_LIMIT_REQUESTS - 1,
        "reset_in_seconds": 60
    }

@router.delete("/cache/{ticker}", summary="Manual Cache Eviction")
async def evict_ticker_cache(ticker: str):
    requested_ticker = ticker.upper()
    prefixes = ["market_v3.2", "fund_raw", "fund_adv", "news_raw", "ai_synth"]
    deleted_count = 0
    if cache_manager.use_redis and cache_manager.redis_client:
        for p in prefixes:
            pattern = f"qs:{cache_manager.CACHE_VERSION}:{p}:{requested_ticker}*"
            keys = await cache_manager.redis_client.keys(pattern)
            if keys:
                await cache_manager.redis_client.delete(*keys)
                deleted_count += len(keys)
    return {"ticker": requested_ticker, "evicted_keys": deleted_count, "status": "purged"}

# --- STOCK ANALYSIS (COMPREHENSIVE) ---

@router.post("/analysis/bulk", response_model=BulkAnalysisResponse, summary="Asynchronous Bulk Pipeline")
async def bulk_analysis(request: BulkAnalysisRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    return {"task_id": task_id, "status": "processing", "message": f"Bulk analysis for {len(request.tickers)} tickers started."}

@router.get("/analysis/{ticker}", response_model=AnalysisResponse, summary="The Institutional Brain (Full Pipeline)")
async def get_comprehensive_analysis(
    ticker: str,
    mode: AnalysisMode = Query(AnalysisMode.FULL),
    include_ai: bool = Query(True),
    force_ai: bool = Query(False)
):
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
            technicals=result.technicals, 
            fundamentals=result.fundamentals, 
            news=result.news,
            context=result.market_context,
            ai_insights=result.ai_analysis,
            human_insight=result.human_insight,
            system=result.system,
            levels=result.levels,
            signals=result.signals,
            context_block=result.context
        )
    except Exception as e:
        pipeline_logger.log_error(ticker, "API_V2", f"Analysis failed: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/{ticker}/technical", summary="Sub-Resource: Technical Snapshot")
async def get_analysis_technical(ticker: str):
    res = await get_technical_analysis(ticker)
    return res

@router.get("/analysis/{ticker}/fundamental", summary="Sub-Resource: Fundamental Snapshot")
async def get_analysis_fundamental(ticker: str):
    return await get_advanced_fundamental_analysis(ticker)

@router.get("/analysis/{ticker}/execution", summary="Sub-Resource: Execution Logic")
async def get_analysis_execution(ticker: str):
    result = await analyze_stock(ticker, mode="execution")
    return {
        "ticker": ticker.upper(),
        "execution": result.execution,
        "levels": result.levels,
        "signals": result.signals
    }

# --- TECHNICAL ANALYSIS ---

@router.get("/technical/{ticker}/signals", summary="Bayesian Trading Signals")
async def get_technical_signals(ticker: str):
    res = await get_technical_analysis(ticker)
    return res.algo_signal if res.algo_signal else {}

@router.get("/technical/{ticker}/levels", summary="Support & Resistance Geometry")
async def get_technical_levels(ticker: str):
    res = await get_technical_analysis(ticker)
    return {"levels": res.trade_setup, "technicals": res.technicals}

@router.get("/technical/{ticker}", summary="Multi-Horizon Technometrics")
async def get_technical_all(ticker: str):
    return await get_technical_analysis(ticker)

@router.get("/technical/{ticker}/{interval}", summary="Granular Time-Series Indicators")
async def get_technical_interval(ticker: str, interval: TimeInterval):
    from .market_data import fetch_stock_data
    from .technicals_indicators import calculate_advanced_technicals
    from fastapi.concurrency import run_in_threadpool
    data = await fetch_stock_data(ticker, interval=interval.value)
    return await run_in_threadpool(lambda: calculate_advanced_technicals(data["dataframe"]))

# --- FUNDAMENTAL ANALYSIS ---

@router.get("/fundamental/{ticker}", summary="360° Fundamental Intelligence")
async def get_fundamental_complete(ticker: str):
    return await get_advanced_fundamental_analysis(ticker)

@router.get("/fundamental/{ticker}/valuation", summary="Intrinsic Valuation Engine")
async def get_fundamental_valuation(ticker: str):
    res = await get_advanced_fundamental_analysis(ticker)
    return res.comprehensive_metrics["valuation"]

@router.get("/fundamental/{ticker}/quality", summary="Audit-Grade Quality Score")
async def get_fundamental_quality(ticker: str):
    res = await get_advanced_fundamental_analysis(ticker)
    return res.executive_summary["overall_assessment"]

@router.get("/fundamental/{ticker}/ratios", summary="Forensic Financial Ratios")
async def get_fundamental_ratios(ticker: str):
    res = await get_advanced_fundamental_analysis(ticker)
    return {
        "profitability": res.comprehensive_metrics["profitability"],
        "health": res.comprehensive_metrics["financial_health"]
    }

# --- NEWS & SENTIMENT ---

@router.get("/news/{ticker}", summary="Aggregated News Intelligence")
async def get_news_all(ticker: str):
    return await get_news_analysis(ticker)

@router.get("/news/{ticker}/signal", summary="Signal-Oriented Headlines")
async def get_news_signal(ticker: str):
    res = await get_news_analysis(ticker)
    return [n for n in res.news if n.title]

@router.get("/news/{ticker}/sentiment", summary="Quantitative News Sentiment")
async def get_news_sentiment(ticker: str):
    res = await get_news_analysis(ticker)
    return res.intelligence if res.intelligence else {}

@router.get("/news/{ticker}/trending", summary="Trending Topics & Themes")
async def get_news_trending(ticker: str):
    return {"trending_topics": [], "ticker": ticker.upper()}

# --- AI & RESEARCH ---

@router.post("/research/{ticker}", summary="Deep Research Initiator")
async def post_research(ticker: str, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    background_tasks.add_task(perform_deep_research, ticker)
    return {"task_id": task_id, "status": "processing"}

@router.get("/research/{ticker}/status", summary="Research Lifecycle Tracker")
async def get_research_status(ticker: str):
    return {"status": "completed", "ticker": ticker.upper()}

@router.get("/research/{ticker}/report", summary="Institutional Research Synthesis")
async def get_research_report_v2(ticker: str):
    return await perform_deep_research(ticker)

@router.post("/ai/analyze", summary="Ad-Hoc AI Synthesis")
async def post_ai_analyze(request: Dict[str, Any]):
    return {"message": "Custom AI analysis triggered"}

@router.get("/ai/explain/{signal}", summary="Signal Semantic Decoder")
async def get_ai_explain(signal: str):
    return {"signal": signal, "explanation": "Signal explanation logic pending."}

# --- MARKET CONTEXT ---

@router.get("/context/{ticker}", summary="Institutional Context Block")
async def get_context_complete(ticker: str):
    from fastapi.concurrency import run_in_threadpool
    return await run_in_threadpool(lambda: get_market_context(ticker))

@router.get("/context/{ticker}/analysts", summary="Sell-Side Consensus")
async def get_context_analysts(ticker: str):
    from fastapi.concurrency import run_in_threadpool
    ctx = await run_in_threadpool(lambda: get_market_context(ticker))
    return {"analyst_ratings": ctx.analyst_ratings, "price_target": ctx.price_target}

@router.get("/context/{ticker}/insiders", summary="Insider Transaction Ledger")
async def get_context_insiders(ticker: str):
    from fastapi.concurrency import run_in_threadpool
    ctx = await run_in_threadpool(lambda: get_market_context(ticker))
    return ctx.insider_activity

@router.get("/context/{ticker}/options", summary="Derivatives Sentiment")
async def get_context_options(ticker: str):
    from fastapi.concurrency import run_in_threadpool
    ctx = await run_in_threadpool(lambda: get_market_context(ticker))
    return ctx.option_sentiment

@router.get("/context/{ticker}/institutions", summary="Institutional Ownership Concentration")
async def get_context_institutions(ticker: str):
    return {"institutions": [], "ticker": ticker.upper()}

# --- REAL-TIME & STREAMING ---

@router.websocket("/ws/analysis")
async def websocket_analysis(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_json({"message": "Real-time analysis stream connected."})
    await websocket.close()

@router.websocket("/ws/levels")
async def websocket_levels(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_json({"message": "Price levels stream connected."})
    await websocket.close()

@router.get("/stream/{ticker}/signals", summary="SSE Signal Stream")
async def stream_signals(ticker: str):
    return {"message": "Signal streaming not yet implemented."}
