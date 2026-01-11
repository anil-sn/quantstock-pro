from enum import Enum
from typing import List, Optional, Dict, Tuple, Any, Literal, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime

# --- ENUMS ---
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
    NEUTRAL_TRANSITION = "Neutral / Transition"

class QualityGrade(str, Enum):
    A_PLUS = "A+"
    A = "A"
    A_MINUS = "A-"
    B_PLUS = "B+"
    B = "B"
    B_MINUS = "B-"
    C_PLUS = "C+"
    C = "C"
    C_MINUS = "C-"
    D = "D"
    F = "F"

class RiskLevel(str, Enum):
    LOW = "Low"
    MODERATE = "Moderate"
    HIGH = "High"
    VERY_HIGH = "Very High"
    UNKNOWN = "Unknown"

class SetupState(str, Enum):
    VALID = "VALID"
    DEGRADED = "DEGRADED"
    INVALID = "INVALID"
    SKIPPED = "SKIPPED"

class SetupQuality(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class DataIntegrity(str, Enum):
    VALID = "VALID"
    DEGRADED = "DEGRADED"
    INVALID = "INVALID"
    NOT_EVALUATED = "NOT_EVALUATED"

class PipelineStageState(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"
    PANIC = "PANIC"

class SensorStatus(BaseModel):
    status: PipelineStageState
    latency_ms: Optional[float] = None
    message: Optional[str] = None

class PipelineTrace(BaseModel):
    layer_0_prescreen: SensorStatus
    layer_1_sensors: Dict[str, SensorStatus]
    layer_2_scoring: SensorStatus
    layer_3_synthesis: SensorStatus
    layer_4_audit: SensorStatus

class PipelineState(BaseModel):
    pre_screen: PipelineStageState
    technicals: PipelineStageState
    scoring: PipelineStageState
    execution: PipelineStageState
    trace: Optional[PipelineTrace] = None

class DecisionState(str, Enum):
    ACCEPT = "ACCEPT"
    WAIT = "WAIT"
    REJECT = "REJECT"

class TradeAction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    WAIT = "WAIT"
    REJECT = "REJECT"
    PROBE = "PROBE"

    @classmethod
    def _missing_(cls, value: object) -> Any:
        if not isinstance(value, str):
            return super()._missing_(value)
        v = value.upper()
        if "ACCUMULATE" in v or "ADD" in v: return cls.BUY
        if "REDUCE" in v or "TRIM" in v: return cls.SELL
        if "NEUTRAL" in v: return cls.HOLD
        if "PROBE" in v: return cls.PROBE
        return super()._missing_(value)

# --- SUB-MODELS ---
class ExpectancyDetail(BaseModel):
    p_win: float
    expected_value: float
    regime_edge: str

class SentimentDetail(BaseModel):
    label: str
    score: float
    confidence: str

class InferenceDetail(BaseModel):
    label: str
    status: str
    description: str

class MetricItem(BaseModel):
    category: str
    metric: str
    value: str
    assessment: str
    percentile: Optional[float] = None

class Scenario(BaseModel):
    probability: float
    revenue_growth_assumption: float
    operating_margin_assumption: float
    target_price: float
    annualized_return: float
    time_horizon: str
    trigger_conditions: Optional[List[str]] = None

class PeerMetric(BaseModel):
    metric: str
    value: float
    sector_average: float
    percentile: float
    z_score: float
    status: str

class TrendDelta(BaseModel):
    metric: str
    current: float
    previous: float
    delta_pct: float
    status: str
    interpretation: str

class TrendAnalysis(BaseModel):
    deltas: List[TrendDelta]
    summary: str
    trajectory: str

class ReliabilityAssessment(BaseModel):
    score: float
    adjustment_factor: float
    confidence_level: str
    data_mix_quality: str

class ScoreDetail(BaseModel):
    value: float
    min_value: float
    max_value: float
    label: str
    legend: str

class AdvancedFundamentalAnalysis(BaseModel):
    analytical_engine: Dict[str, Any]
    analysis_header: Dict[str, Any]
    executive_summary: Dict[str, Any]
    comprehensive_metrics: Dict[str, Any]
    comparative_analysis: Dict[str, Any]
    trend_and_momentum: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    investment_decision_framework: Dict[str, Any]
    scenario_analysis: Dict[str, Any]
    data_quality_and_assumptions: Dict[str, Any]
    base_data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any]

class AnalystEstimates(BaseModel):
    target_mean_price: Optional[float] = None
    target_median_price: Optional[float] = None
    number_of_analysts: Optional[int] = None
    recommendation_key: Optional[str] = None
    recommendation_mean: Optional[float] = None

class FundamentalInferences(BaseModel):
    valuation: InferenceDetail
    growth: InferenceDetail
    health: InferenceDetail
    efficiency: InferenceDetail
    capital_allocation: InferenceDetail
    earnings_quality: InferenceDetail
    ownership_structure: InferenceDetail
    overall_sentiment: SentimentDetail

class RiskAssessment(BaseModel):
    level: RiskLevel
    score: int
    factors: List[str]

class FundamentalData(BaseModel):
    ticker: str
    asset_type: str = "Unknown"
    company_name: Optional[str] = None
    description: Optional[str] = None
    industry: Optional[str] = None
    sector: Optional[str] = None
    exchange: Optional[str] = None
    market_cap: Optional[float] = None
    enterprise_value: Optional[float] = None
    trailing_pe: Optional[float] = None
    forward_pe: Optional[float] = None
    rev_growth_adjusted_pe: Optional[float] = None
    price_to_sales: Optional[float] = None
    price_to_book: Optional[float] = None
    enterprise_to_ebitda: Optional[float] = None
    enterprise_to_revenue: Optional[float] = None
    earnings_yield: Optional[float] = None
    book_value: Optional[float] = None
    dividend_rate: Optional[float] = None
    profit_margin: Optional[float] = None
    gross_margins: Optional[float] = None
    operating_margins: Optional[float] = None
    ebitda_margins: Optional[float] = None
    ebitda: Optional[float] = None
    return_on_equity: Optional[float] = None
    return_on_assets: Optional[float] = None
    return_on_invested_capital: Optional[float] = None
    invested_capital: Optional[float] = None
    free_cash_flow: Optional[float] = None
    operating_cash_flow: Optional[float] = None
    net_income: Optional[float] = None
    total_revenue: Optional[float] = None
    free_cash_flow_margin: Optional[float] = None
    fcf_to_net_income_ratio: Optional[float] = None
    revenue_growth: Optional[float] = None
    earnings_growth: Optional[float] = None
    fcf_growth: Optional[float] = None
    lifecycle_stage: str = "Unknown"
    total_debt: Optional[float] = None
    total_cash: Optional[float] = None
    net_cash: Optional[float] = None
    net_cash_status: str = "Neutral"
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    interest_coverage: Optional[float] = None
    dividend_yield: Optional[float] = None
    payout_ratio: Optional[float] = None
    held_percent_institutions: Optional[float] = None
    held_percent_insiders: Optional[float] = None
    overall_risk_score: Optional[float] = None
    audit_risk_score: Optional[float] = None
    board_risk_score: Optional[float] = None
    shares_outstanding: Optional[int] = None
    float_shares: Optional[int] = None
    analyst_estimates: Optional[AnalystEstimates] = None
    inferences: Optional[FundamentalInferences] = None
    risk_assessment: Optional[RiskAssessment] = None
    trend_analysis: Optional[TrendAnalysis] = None
    quality_score: Optional["CompositeQualityScore"] = None
    last_updated: datetime = Field(default_factory=datetime.now)

class NewsItem(BaseModel):
    title: str
    publisher: str
    link: str
    publish_time: int

class NewsSignal(BaseModel):
    headline: str
    signal_strength: float
    impact_category: str
    is_primary_source: bool

class NewsIntelligence(BaseModel):
    signal_score: float
    noise_ratio: float
    source_diversity: float
    narrative_trap_warning: bool
    summary: str

class SourceCategory(str, Enum):
    ACADEMIC = "academic"
    GOVERNMENT = "government"
    PRIMARY_CORPORATE = "primary_corporate"
    NEWS = "news"
    ANALYSIS = "analyst_research"
    OTHER = "other"

class ResearchSource(BaseModel):
    title: str
    url: str
    category: SourceCategory
    credibility_score: float
    publisher: Optional[str] = None

class Finding(BaseModel):
    fact: str
    citation_indices: List[int]
    iteration: int

class SourceDiversity(BaseModel):
    category_distribution: Dict[SourceCategory, int]
    overall_diversity_score: float
    is_diversified: bool
    bias_warning: Optional[str] = None

class ResearchIteration(BaseModel):
    query: str
    findings: List[Finding]
    sources: List[ResearchSource]

class ResearchReport(BaseModel):
    ticker: str
    synthesis: str
    iterations: List[ResearchIteration]
    diversity_metrics: SourceDiversity
    total_sources: int
    timestamp: datetime = Field(default_factory=datetime.now)

class NewsResponse(BaseModel):
    ticker: str
    news: List[NewsItem]
    intelligence: Optional[NewsIntelligence] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class CompositeQualityScore(BaseModel):
    overall_score: float
    grade: QualityGrade
    profitability_score: float
    growth_score: float
    financial_strength_score: float
    business_model_score: float
    management_score: float
    consistency_score: float
    components: Dict[str, Any]

class BusinessModelAnalysis(BaseModel):
    model_type: str
    revenue_recurrence: float
    customer_stickiness: str
    competitive_advantages: List[str]
    scalability_rating: str
    market_position: str
    industry_outlook: str

class InvestmentThesis(BaseModel):
    bull_case: str
    bear_case: str
    base_case: str

class InvestmentRecommendation(BaseModel):
    action: str
    confidence: str
    position_sizing: str
    investment_horizon: str
    key_risks: List[str]
    monitoring_metrics: List[str]

class QualityAssessment(BaseModel):
    score: float
    grade: QualityGrade
    interpretation: str
    component_scores: Dict[str, float]

class Technicals(BaseModel):
    rsi: Optional[float] = None
    rsi_signal: TrendDirection
    macd_line: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    adx: Optional[float] = None
    atr: Optional[float] = None
    atr_percent: Optional[float] = None
    cci: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    bb_position: Optional[float] = None
    support_s1: Optional[float] = None
    support_s2: Optional[float] = None
    resistance_r1: Optional[float] = None
    resistance_r2: Optional[float] = None
    volume_avg_20d: Optional[float] = None
    volume_current: Optional[float] = None
    volume_ratio: Optional[float] = None
    ema_20: Optional[float] = None
    ema_50: Optional[float] = None
    ema_200: Optional[float] = None
    trend_structure: TrendDirection

class SignalImpact(BaseModel):
    indicator: str
    direction: Literal["Bullish", "Bearish", "Neutral"]
    weight: int = Field(..., ge=0, le=10)
    value_at_analysis: Union[float, str, None] = None

    @field_validator('direction', mode='before')
    @classmethod
    def normalize_direction(cls, v: str) -> str:
        if not isinstance(v, str): return v
        v_low = v.lower()
        if "bull" in v_low: return "Bullish"
        if "bear" in v_low: return "Bearish"
        return "Neutral"

class MarketSentiment(BaseModel):
    score: float
    fear_greed_index: float
    summary: Optional[str] = None

class TradeSetup(BaseModel):
    action: TradeAction
    confidence: ScoreDetail
    expectancy: Optional[ExpectancyDetail] = None
    entry_zone: Optional[Tuple[float, float]] = None
    stop_loss: Optional[float] = None
    stop_loss_pct: Optional[float] = None
    take_profit_targets: Optional[List[float]] = None
    risk_reward_ratio: Optional[float] = None
    position_size_pct: Optional[float] = None
    max_capital_at_risk: Optional[float] = None
    setup_state: SetupState = SetupState.INVALID
    setup_quality: Optional[SetupQuality] = None

class AlgoSignal(BaseModel):
    overall_score: ScoreDetail
    trend_score: ScoreDetail
    momentum_score: ScoreDetail
    volatility_score: ScoreDetail
    volume_score: ScoreDetail
    volatility_risk: RiskLevel
    trend_strength: str
    confluence_score: int = 0

class RiskMetrics(BaseModel):
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    var_95: Optional[float] = None
    beta: Optional[float] = None
    standard_deviation: Optional[float] = None

class HorizonPerspective(BaseModel):
    action: TradeAction
    confidence: float
    entry_price: float
    target_price: float
    stop_loss: float
    signals: List[SignalImpact]
    rationale: str

class OptionsAdvice(BaseModel):
    strategy: str
    strike_price: Optional[float] = None
    expiration_view: str
    rationale: str
    risk_reward: str
    status: Literal["ACTIVE", "NOT_RECOMMENDED", "DATA_ABSENT"] = "ACTIVE"

class WeightDetail(BaseModel):
    component: str
    weight: float
    contribution: float

class AIAnalysisResult(BaseModel):
    executive_summary: str
    investment_thesis: Optional[Union[str, Dict[str, Any]]] = None
    rejection_analysis: Optional[str] = None
    intraday: Optional[HorizonPerspective] = None
    swing: Optional[HorizonPerspective] = None
    positional: Optional[HorizonPerspective] = None
    longterm: Optional[HorizonPerspective] = None
    options_fno: Optional[OptionsAdvice] = None
    market_sentiment: Optional[MarketSentiment] = None
    institutional_insight: Optional[str] = None
    consensus_weights: Optional[List[WeightDetail]] = None

class StockOverview(BaseModel):
    action: TradeAction
    current_price: float
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    confidence: ScoreDetail
    summary: str

class OHLCV(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float

class MultiHorizonSetups(BaseModel):
    intraday: Optional[TradeSetup] = None
    swing: Optional[TradeSetup] = None
    positional: Optional[TradeSetup] = None
    longterm: Optional[TradeSetup] = None

class TechnicalStockResponse(BaseModel):
    overview: StockOverview
    requested_ticker: str
    ticker: str
    company_name: Optional[str] = None
    sector: Optional[str] = None
    current_price: float
    price_change_1d: Optional[float] = None
    technicals: Optional[Technicals] = None
    algo_signal: Optional[AlgoSignal] = None
    trade_setup: TradeSetup
    horizons: Optional[MultiHorizonSetups] = None
    raw_data: Optional[List[OHLCV]] = None
    risk_metrics: Optional[RiskMetrics] = None
    pipeline_state: Optional[PipelineState] = None
    data_confidence: float = 100.0
    is_trade_authorized: bool = False
    data_integrity: DataIntegrity = DataIntegrity.VALID
    decision_state: DecisionState = DecisionState.WAIT
    timestamp: datetime = Field(default_factory=datetime.now)

class AnalystRating(BaseModel):
    firm: str
    to_grade: str
    action: str
    date: str

class InsiderTrade(BaseModel):
    date: str
    insider_name: str
    position: str
    transaction_type: str
    shares: int
    value: Optional[float] = None

class OptionSentiment(BaseModel):
    put_call_ratio: float
    implied_volatility: float
    total_open_interest: int
    sentiment: str
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
    period: str
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
    ticker: Optional[str] = None
    analyst_ratings: List[AnalystRating] = []
    insider_activity: List[InsiderTrade] = []
    option_sentiment: Optional[OptionSentiment] = None
    price_target: Optional[AnalystPriceTarget] = None
    consensus: Optional[AnalystConsensus] = None
    events: Optional[UpcomingEvents] = None

class TradingDecision(BaseModel):
    decision_state: DecisionState
    setup_state: SetupState
    confidence: float
    primary_reason: str
    violation_rules: List[str]
    position_size_pct: Optional[float] = 0.0
    max_capital_at_risk: Optional[float] = 0.0
    risk_reward_ratio: Optional[float] = 0.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    tp_targets: Optional[List[float]] = None
    entry_zone: Optional[Tuple[float, float]] = None
    setup_quality: Optional[SetupQuality] = None

class ResponseMeta(BaseModel):
    ticker: str
    timestamp: datetime = Field(default_factory=datetime.now)
    version: str = "AlphaCore v20.2"
    analysis_id: str
    data_version: str = "market_v3.2"

class RiskLimits(BaseModel):
    max_position_pct: float
    max_capital_risk_pct: float
    daily_loss_limit_pct: float

class ExecutionBlock(BaseModel):
    action: TradeAction
    authorized: bool
    urgency: str # LOW, MEDIUM, HIGH, IMMEDIATE
    valid_until: datetime
    risk_limits: RiskLimits
    vetoes: List[Dict[str, Any]] = []

class SignalComponent(BaseModel):
    score: float # Normalized [-1, 1]
    weight: float
    signal: str

class SignalsBlock(BaseModel):
    actionable: bool
    primary_signal_strength: float # Normalized [0, 1]
    required_strength: float
    components: Dict[str, SignalComponent]
    normalization_method: str = "Z-SCORE_CLAMPED"
    expectancy_weighting: float = 0.25

class LevelItem(BaseModel):
    price: float
    strength: float
    type: str
    distance_pct: float

class ValueZone(BaseModel):
    min: float
    max: float
    attractiveness: float
    type: str

class LevelsBlock(BaseModel):
    current: float
    timestamp: datetime
    support: List[LevelItem]
    resistance: List[LevelItem]
    value_zones: List[ValueZone]

class ContextBlock(BaseModel):
    regime: str
    regime_confidence: float
    trend_strength_adx: float
    volatility_atr_pct: float
    volume_ratio: float
    transition_watch: List[str] = []

class HumanInsightBlock(BaseModel):
    summary: str
    key_conflicts: List[str]
    scenarios: Dict[str, Any]
    monitor_triggers: List[str]
    probability_basis: str = "HEURISTIC"

class SystemBlock(BaseModel):
    confidence: float # SINGLE SOURCE OF TRUTH
    data_quality: DataIntegrity
    blocking_issues: List[str]
    data_state_taxonomy: Dict[str, str] = {}
    latency_ms: float
    layer_timings: Dict[str, float] = {}
    next_update: datetime
    latency_sla_violated: bool = False
    sla_threshold_ms: float = 5000.0
    fallback_used: bool = False
    engine_logic: str = "DETERMINISTIC"

class AdvancedStockResponse(BaseModel):
    meta: ResponseMeta
    execution: ExecutionBlock
    signals: SignalsBlock
    levels: LevelsBlock
    context: ContextBlock
    human_insight: HumanInsightBlock
    system: SystemBlock
    market_context: Optional[MarketContext] = None 
    ai_analysis: Optional[AIAnalysisResult] = None

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})