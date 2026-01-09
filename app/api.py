from fastapi import APIRouter, HTTPException, Query
from .service import analyze_stock, get_technical_analysis, get_fundamental_analysis
from .context import get_market_context
from .models import AdvancedStockResponse, TechnicalStockResponse, AnalysisMode, MarketContext
from .fundamentals import FundamentalData

router = APIRouter()

@router.get("/analyze/{ticker}", response_model=AdvancedStockResponse)
async def analyze(ticker: str, mode: AnalysisMode = Query(AnalysisMode.ALL)):
    try:
        return await analyze_stock(ticker, mode)
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

@router.get("/fundamentals/{ticker}", response_model=FundamentalData)
async def fundamentals(ticker: str):
    try:
        return await get_fundamental_analysis(ticker)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/context/{ticker}", response_model=MarketContext)
async def context(ticker: str):
    try:
        return get_market_context(ticker)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
