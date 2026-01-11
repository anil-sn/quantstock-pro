from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from .models import (
    TradeAction, RiskLevel, DataIntegrity, DecisionState, SetupState, 
    TechnicalStockResponse, AdvancedFundamentalAnalysis, NewsResponse, 
    MarketContext, ResearchReport, AIAnalysisResult, ScoreDetail, OHLCV,
    HumanInsightBlock, SystemBlock, LevelsBlock, SignalsBlock, ContextBlock
)

class AnalysisMode(str, Enum):
    FULL = "full"
    EXECUTION = "execution"
    INTRADAY = "intraday"
    SWING = "swing"
    POSITIONAL = "positional"
    LONGTERM = "longterm"

class TimeHorizon(str, Enum):
    INTRADAY = "intraday"
    SWING = "swing"
    POSITIONAL = "positional"
    LONGTERM = "longterm"

class TimeInterval(str, Enum):
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    D1 = "1d"
    W1 = "1wk"
    MO1 = "1mo"

class BulkAnalysisRequest(BaseModel):
    tickers: List[str] = Field(..., max_length=10)
    mode: AnalysisMode = AnalysisMode.FULL

class MetaInfo(BaseModel):
    ticker: str
    timestamp: datetime
    version: str = "2.0.0"
    analysis_id: str

class AnalysisResponse(BaseModel):
    meta: MetaInfo
    execution: Dict[str, Any]
    technicals: Optional[TechnicalStockResponse] = None
    fundamentals: Optional[AdvancedFundamentalAnalysis] = None
    news: Optional[NewsResponse] = None
    context: Optional[MarketContext] = None
    ai_insights: Optional[AIAnalysisResult] = None
    human_insight: Optional[HumanInsightBlock] = None
    system: Optional[SystemBlock] = None
    levels: Optional[LevelsBlock] = None
    signals: Optional[SignalsBlock] = None
    context_v2: Optional[ContextBlock] = Field(None, alias="context_block")

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    components: Dict[str, str]
    version: str
    uptime_seconds: Optional[float] = None

class BulkAnalysisResponse(BaseModel):
    task_id: str
    status: str
    message: str

class APILimitsResponse(BaseModel):
    rate_limit: int
    requests_remaining: int
    reset_in_seconds: int
