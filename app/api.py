from fastapi import APIRouter, HTTPException
from .service import analyze_stock, get_technical_analysis
from .models import AdvancedStockResponse, TechnicalStockResponse

router = APIRouter()

@router.get("/analyze/{ticker}", response_model=AdvancedStockResponse)
async def analyze(ticker: str):
    try:
        return await analyze_stock(ticker)
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
