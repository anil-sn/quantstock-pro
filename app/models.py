from enum import Enum
from typing import List, Optional, Dict, Tuple, Any, Literal, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime

class AnalysisMode(str, Enum):
    INTRADAY = "intraday"
    SWING = "swing"
    POSITIONAL = "positional"
    LONGTERM = "longterm"
    ALL = "all"

class TrendDirection(str, Enum):
    BULLISH = "Bullish"
    BEARISH = "Bearish"
    NEUTRAL = "Neutral"
    SIDEWAYS = "Sideways"

class RiskLevel(str, Enum):
    LOW = "Low"
    MODERATE = "Moderate"
    HIGH = "High"
    VERY_HIGH = "Very High"

class TradeAction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    WAIT = "WAIT"

class Technicals(BaseModel):
    rsi: float
    rsi_signal: TrendDirection
    macd_line: float
    macd_signal: float
    macd_histogram: float
    adx: float
    atr: float
    atr_percent: float
    cci: float
    bb_upper: float
    bb_middle: float
    bb_lower: float
    bb_position: float
    support_s1: float
    support_s2: float
    resistance_r1: float
    resistance_r2: float
    volume_avg_20d: float
    volume_current: float
    volume_ratio: float
    ema_20: float
    ema_50: float
    ema_200: float
    trend_structure: TrendDirection

class SignalImpact(BaseModel):
    indicator: str
    direction: Literal["Bullish", "Bearish", "Neutral"]
    weight: int = Field(..., ge=1, le=10, description="Significance of this indicator to the thesis (1-10)")
    value_at_analysis: Union[float, str, None] = None

    @field_validator('direction', mode='before')
    @classmethod
    def normalize_direction(cls, v: str) -> str:
        if not isinstance(v, str):
            return v
        v_low = v.lower()
        if "bull" in v_low:
            return "Bullish"
        if "bear" in v_low:
            return "Bearish"
        return "Neutral"

class ScoreDetail(BaseModel):
    value: float
    min_value: float
    max_value: float
    label: str
    legend: str

class MarketSentiment(BaseModel):
    score: ScoreDetail
    fear_greed_index: ScoreDetail

class TradeSetup(BaseModel):
    action: TradeAction
    confidence: ScoreDetail
    entry_zone: Tuple[float, float]
    stop_loss: float
    stop_loss_pct: float
    take_profit_targets: List[float]
    risk_reward_ratio: float
    position_size_pct: float
    max_capital_at_risk: float
    setup_quality: RiskLevel

class AlgoSignal(BaseModel):
    overall_score: ScoreDetail
    trend_score: ScoreDetail
    momentum_score: ScoreDetail
    volatility_score: ScoreDetail
    volume_score: ScoreDetail
    volatility_risk: RiskLevel
    trend_strength: str

class RiskMetrics(BaseModel):
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    var_95: Optional[float] = None
    beta: Optional[float] = None
    standard_deviation: Optional[float] = None

class HorizonPerspective(BaseModel):
    action: TradeAction
    confidence: ScoreDetail
    entry_price: float
    target_price: float
    stop_loss: float
    signals: List[SignalImpact]
    rationale: str

class OptionsAdvice(BaseModel):
    strategy: str  # e.g., "Bull Call Spread", "Naked Put"
    strike_price: float
    expiration_view: str
    rationale: str
    risk_reward: str

class AIAnalysisResult(BaseModel):
    executive_summary: str
    investment_thesis: str
    intraday: HorizonPerspective
    swing: HorizonPerspective
    positional: HorizonPerspective
    longterm: HorizonPerspective
    options_fno: OptionsAdvice
    market_sentiment: MarketSentiment
    institutional_insight: Optional[str] = None

class StockOverview(BaseModel):
    action: TradeAction
    current_price: float
    target_price: float
    stop_loss: float
    confidence: ScoreDetail
    summary: str

class TechnicalStockResponse(BaseModel):
    overview: StockOverview
    ticker: str
    company_name: Optional[str] = None
    sector: Optional[str] = None
    current_price: float
    price_change_1d: Optional[float] = None
    technicals: Technicals
    algo_signal: AlgoSignal
    trade_setup: TradeSetup
    risk_metrics: RiskMetrics
    timestamp: datetime = Field(default_factory=datetime.now)

class AnalystRating(BaseModel):
    firm: str
    to_grade: str
    action: str  # e.g., "up", "down", "init"
    date: str

class InsiderTrade(BaseModel):
    date: str
    insider_name: str
    position: str
    transaction_type: str  # "Buy" or "Sell"
    shares: int
    value: float

class OptionSentiment(BaseModel):
    put_call_ratio: float
    implied_volatility: float
    total_open_interest: int
    sentiment: str  # "Bullish", "Bearish", "Neutral"
    max_pain: Optional[float] = None
    highest_call_oi_strike: Optional[float] = None
    highest_put_oi_strike: Optional[float] = None

class AnalystPriceTarget(BaseModel):
    current: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    mean: Optional[float] = None
    median: Optional[float] = None

class AnalystConsensus(BaseModel):
    period: str  # e.g. "0m"
    strong_buy: int = 0
    buy: int = 0
    hold: int = 0
    sell: int = 0
    strong_sell: int = 0

class UpcomingEvents(BaseModel):
    earnings_date: Optional[str] = None
    earnings_avg_estimate: Optional[float] = None
    earnings_low_estimate: Optional[float] = None
    earnings_high_estimate: Optional[float] = None
    revenue_avg_estimate: Optional[int] = None

class MarketContext(BaseModel):
    analyst_ratings: List[AnalystRating] = []
    insider_activity: List[InsiderTrade] = []
    option_sentiment: Optional[OptionSentiment] = None
    price_target: Optional[AnalystPriceTarget] = None
    consensus: Optional[AnalystConsensus] = None
    events: Optional[UpcomingEvents] = None
    
class AdvancedStockResponse(BaseModel):
    analysis_mode: AnalysisMode = AnalysisMode.ALL
    overview: StockOverview
    ticker: str
    company_name: Optional[str] = None
    sector: Optional[str] = None
    current_price: float
    price_change_1d: Optional[float] = None
    technicals: Technicals
    algo_signal: AlgoSignal
    trade_setup: TradeSetup
    ai_analysis: AIAnalysisResult
    risk_metrics: RiskMetrics
    market_context: Optional[MarketContext] = None
    timestamp: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
