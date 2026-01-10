import json
import re
from typing import Any, List, Optional
from pathlib import Path
from google import genai
from google.genai import types
from async_lru import alru_cache
from .models import Technicals, AIAnalysisResult, MarketSentiment
from .settings import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY) if settings.GEMINI_API_KEY else None

def sanitize_prompt_text(text: str) -> str:
    """Sanitize text to prevent prompt injection by removing common escape sequences/tags."""
    if not text:
        return ""
    # Remove markers that could be used to escape blocks or inject system commands
    text = text.replace("```", "'''")
    text = text.replace("#", "-") # Prevent header injection
    return text

from .models import Technicals, AIAnalysisResult, MarketSentiment, TechnicalStockResponse, AdvancedFundamentalAnalysis, NewsResponse, MarketContext
from .settings import settings
from .logger import pipeline_logger

client = genai.Client(api_key=settings.GEMINI_API_KEY) if settings.GEMINI_API_KEY else None

def sanitize_prompt_text(text: str) -> str:
    """Sanitize text to prevent prompt injection by removing common escape sequences/tags."""
    if not text:
        return ""
    # Remove markers that could be used to escape blocks or inject system commands
    text = text.replace("```", "'''")
    text = text.replace("#", "-") # Prevent header injection
    return text

async def interpret_advanced(
    technical_response: TechnicalStockResponse,
    fundamental_response: Optional[AdvancedFundamentalAnalysis] = None,
    news_response: Optional[NewsResponse] = None,
    market_context: Optional[MarketContext] = None,
    mode: str = "all",
    system_instruction: str = ""
) -> AIAnalysisResult | None:
    if not client:
        return None

    # Extract Core Data
    ticker = technical_response.ticker
    technicals = technical_response.technicals
    
    # Construct Company Info
    company_info = {
        "longName": technical_response.company_name,
        "sector": technical_response.sector,
        "current_price": technical_response.current_price
    }

    # Sanitize inputs that could be malicious
    system_instruction = sanitize_prompt_text(system_instruction)
    ticker = sanitize_prompt_text(ticker)
    
    # Load Framework
    try:
        framework_path = Path(__file__).parent.parent / "docs/THE_COMPLETE_FRAMEWORK.md"
        framework_content = framework_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Warning: Could not load framework: {e}")
        framework_content = "Adhere to standard professional trading risk management rules."

    fundamentals_section = ""
    news_section = ""
    context_section = ""
    
    if fundamental_response:
        fundamentals_json = fundamental_response.model_dump_json(indent=2)
        fundamentals_section = f"""
    ## FUNDAMENTAL DATA & INFERENCES
    {fundamentals_json}
    """

    if news_response and news_response.news:
        news_list = "\n".join([f"- {sanitize_prompt_text(n.title)} ({sanitize_prompt_text(n.publisher)})" for n in news_response.news])
        intelligence_section = ""
        if news_response.intelligence:
            intel = news_response.intelligence
            intelligence_section = f"""
    ### NEWS INTELLIGENCE (SCANNED)
    - Signal Score: {intel.signal_score}
    - Noise Ratio: {intel.noise_ratio}%
    - Source Diversity: {intel.source_diversity}
    - Narrative Trap Warning: {intel.narrative_trap_warning}
    - Summary: {intel.summary}
    """
        
        news_section = f"""
    ## RECENT NEWS & CATALYSTS
    {news_list}
    {intelligence_section}
    """

    if market_context:
        context_section = f"""
    ## MARKET CONTEXT (SMART MONEY)
    {market_context.model_dump_json(indent=2)}
    """

    # If system instruction is empty, derive it from Technical Response
    is_diagnostic = technical_response.decision_state != "ACCEPT"
    
    if not system_instruction:
        decision_state = technical_response.decision_state.value
        reason = technical_response.overview.summary
        conf = technical_response.data_confidence
        
        system_instruction = f"""
        DECISION STATE: {decision_state}
        PRIMARY REASON: {reason}
        CONFIDENCE: {conf:.1f}/100
        """
        if is_diagnostic:
            system_instruction += "\nMODE: DIAGNOSTIC/POST-MORTEM. Do NOT suggest trades. Explain the VETO."

    # --- AUDIT FIX: THE DIAGNOSTIC CONTRACT ---
    diagnostic_constraint = ""
    if is_diagnostic:
        diagnostic_constraint = """
        CRITICAL: The system has issued a WAIT or REJECT order. 
        1. YOU ARE FORBIDDEN from writing an 'investment_thesis' that suggests upside or entry.
        2. Change 'investment_thesis' to 'rejection_analysis'.
        3. Your tone must be clinical and risk-focused.
        4. No directional 'action' other than WAIT or REJECT.
        """

    prompt = f"""
    # QUANTITATIVE STOCK ANALYSIS FRAMEWORK
    
    {diagnostic_constraint}
    
    ## S-TIER SYSTEM INSTRUCTIONS (MANDATORY)
    {system_instruction}
    
    ## OPERATIONAL MODE: {mode.upper()}
    You are strictly analyzing in {mode.upper()} mode. 
    - If INTRADAY: Focus ONLY on short-term price action, volume anomalies, and 15M/5M structure. Ignore long-term fundamentals.
    - If SWING: Focus on Daily structure, 4H trends, and key support/resistance. Incorporate valuation and growth metrics.
    - If LONGTERM: Focus on Weekly structure and major moving averages. Heavily weigh fundamental health (Debt, Margins, Growth).
    
    ## CONTEXTUAL INTELLIGENCE INSTRUCTIONS
    1. **Analyst Targets:** Compare the 'current_price' to the 'price_target.mean'. Is there implied upside? If upside > 50%, evaluate if it is realistic given the technical trend.
    2. **Smart Money:** Analyze 'insider_activity' and 'option_sentiment'. If more than 3 insiders sold in the last 3 months, this is a HEAVY BEARISH catalyst. Do not dismiss it as "trading plans."
    3. **Event Risk:** Check 'events.earnings_date'. If within 7 days, flag as HIGH RISK.
    4. **Consensus:** Use 'consensus' to gauge broad market sentiment (e.g., "Strong Buy" count).
    
    ## DATA VALIDATION & ACCOUNTABILITY RULES (STRICT)
    1. **Stale Data:** If 'analyst_ratings' are provided, they have already been filtered for freshness (< 2 years). Use them with confidence.
    2. **Volatility Anomaly:** If 'option_sentiment.implied_volatility' > 100%, FLAG AS DATA ERROR in your summary and do not base strategy on it.
    3. **Null Indicators:** If any technical indicator (e.g. 'cci', 'volume_ratio') is 'null', YOU ARE FORBIDDEN from describing it as 'Neutral'. Describe it as 'Data Unreliable' or 'Indicator Failure'.
    4. **No Cowardice:** If the system status is REJECTED or WAIT, you MUST set your response 'action' to 'REJECT' or 'WAIT'. 
    5. **Options Lock:** If 'option_sentiment' is null, YOU ARE FORBIDDEN from suggesting a strategy, strike price, or expiration. You must return status 'DATA_ABSENT' and strategy 'NONE'.
    6. **Confidence Ceiling:** Your horizon confidence values CANNOT exceed the System Confidence provided.
    7. **Indicator Semantics:** 'bb_position' values: 0.0 = Lower Band (Oversold/Support), 1.0 = Upper Band (Overbought/Resistance). A value of 0.01 is EXTREME OVERSOLD, not bearish.
    
    ## TRADING RULES & CONSTITUTION
    {framework_content}
    
    ## CONTEXT
    You are a professional multi-horizon trader. Analyze {ticker}.
    
    ## COMPANY OVERVIEW
    {json.dumps(company_info, indent=2)}
    
    ## QUANTITATIVE METRICS
    {technicals.model_dump_json(indent=2)}
    {fundamentals_section}
    {news_section}
    {context_section}
    ## OUTPUT FORMAT
    Return ONLY valid JSON matching this schema:
    {{
        "executive_summary": "string",
        "investment_thesis": "string",
        "intraday": {{
            "action": "STRICTLY ONE OF: BUY, SELL, HOLD, WAIT",
            "confidence": {{ "value": 0.0, "min_value": 0.0, "max_value": 100.0, "label": "string", "legend": "0-100 scale" }},
            "entry_price": 0.0,
            "target_price": 0.0,
            "stop_loss": 0.0,
                "signals": [
                    {{
                        "indicator": "RSI/MACD/CCI/BB/etc",
                        "direction": "Bullish OR Bearish OR Neutral",
                        "weight": 1-10,
                        "value_at_analysis": 0.0
                    }}
                ],
            "rationale": "string"
        }},
        "swing": {{ "action": "...", "confidence": {{ "value": 0.0, "min_value": 0.0, "max_value": 100.0, "label": "...", "legend": "..." }}, "entry_price": 0.0, "target_price": 0.0, "stop_loss": 0.0, "signals": [...], "rationale": "..." }},
        "positional": {{ "action": "...", "confidence": {{ "value": 0.0, "min_value": 0.0, "max_value": 100.0, "label": "...", "legend": "..." }}, "entry_price": 0.0, "target_price": 0.0, "stop_loss": 0.0, "signals": [...], "rationale": "..." }},
        "longterm": {{ "action": "...", "confidence": {{ "value": 0.0, "min_value": 0.0, "max_value": 100.0, "label": "...", "legend": "..." }}, "entry_price": 0.0, "target_price": 0.0, "stop_loss": 0.0, "signals": [...], "rationale": "..." }},
        "options_fno": {{
            "strategy": "string",
            "strike_price": 0.0,
            "expiration_view": "string",
            "rationale": "string",
            "risk_reward": "string"
        }},
        "market_sentiment": {{
            "score": {{ "value": 0.0, "min_value": 0.0, "max_value": 100.0, "label": "string", "legend": "0-100 (Fear to Greed)" }},
            "fear_greed_index": {{ "value": 0.0, "min_value": 0.0, "max_value": 100.0, "label": "string", "legend": "0-100" }}
        }},
        "institutional_insight": "string"
    }}
    """

    pipeline_logger.log_payload(ticker, "LAYER_3", "GEMINI_INPUT_PROMPT", prompt)

    try:
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=settings.GEMINI_TEMPERATURE,
                top_p=settings.GEMINI_TOP_P
            )
        )
        
        text = response.text.strip()
        clean_json = re.sub(r"```json\s?|\s?```", "", text).strip()
        pipeline_logger.log_payload(ticker, "LAYER_3", "GEMINI_OUTPUT_RAW", clean_json)
        result = json.loads(clean_json)
        
        return AIAnalysisResult(**result)
    except Exception as e:
        print(f"AI Analysis Error: {e}")
        return None

async def interpret(snapshot: Any) -> Any:
    """Compatibility shim if needed"""
    return await interpret_advanced("UNKNOWN", snapshot, {})

