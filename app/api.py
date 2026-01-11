from fastapi import APIRouter, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from .service import analyze_stock, get_technical_analysis, get_fundamental_analysis, get_news_analysis, get_advanced_fundamental_analysis, perform_deep_research
from .context import get_market_context
from .models import AdvancedStockResponse, TechnicalStockResponse, AnalysisMode, MarketContext, NewsResponse, AdvancedFundamentalAnalysis, ResearchReport

router = APIRouter()

@router.get("/research/{ticker}", response_model=ResearchReport)
async def research(ticker: str):
    try:
        return await perform_deep_research(ticker)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/analyze/{ticker}", response_model=AdvancedStockResponse)
async def analyze(ticker: str, mode: AnalysisMode = Query(AnalysisMode.ALL), force_ai: bool = Query(False)):
    try:
        return await analyze_stock(ticker, mode, force_ai)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/technical/{ticker}", response_model=TechnicalStockResponse)
async def technical(ticker: str):
    try:
        return await get_technical_analysis(ticker)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/fundamentals/{ticker}", response_model=AdvancedFundamentalAnalysis)
async def fundamentals(ticker: str):
    try:
        return await get_advanced_fundamental_analysis(ticker)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/news/{ticker}", response_model=NewsResponse)
async def news(ticker: str):
    try:
        return await get_news_analysis(ticker)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/context/{ticker}", response_model=MarketContext)
async def context(ticker: str):
    try:
        return await run_in_threadpool(lambda: get_market_context(ticker))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
