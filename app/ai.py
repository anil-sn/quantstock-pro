import json
import re
import time
from typing import Any, List, Optional, Union, Dict
from pathlib import Path
from google import genai
from google.genai import types
from async_lru import alru_cache
from .models import Technicals, AIAnalysisResult, MarketSentiment, TechnicalStockResponse, AdvancedFundamentalAnalysis, NewsResponse, MarketContext
from .settings import settings
from .logger import pipeline_logger

client = genai.Client(api_key=settings.GEMINI_API_KEY) if settings.GEMINI_API_KEY else None

def sanitize_prompt_text(text: str) -> str:
    """Sanitize text to prevent prompt injection."""
    if not text: return ""
    text = text.replace("```", "'''")
    text = text.replace("#", "-") 
    return text

@alru_cache(maxsize=100, ttl=300)
async def _interpret_cached(ticker: str, prompt: str, system_instruct: str) -> AIAnalysisResult | None:
    """Cached execution of the Gemini inference with strict schema validation."""
    if not client: return None
        
    pipeline_logger.log_payload(ticker, "LAYER_3", "GEMINI_INPUT_PROMPT", prompt)

    try:
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruct,
                temperature=settings.GEMINI_TEMPERATURE,
                top_p=settings.GEMINI_TOP_P,
                response_mime_type="application/json"
            )
        )
        
        text = response.text.strip()
        result = json.loads(text)
        
        # --- AUDIT FIX: DEFENSIVE SCHEMA COERCION ---
        # Handle cases where LLM returns dict for thesis instead of string
        if isinstance(result.get('investment_thesis'), dict):
            result['investment_thesis'] = json.dumps(result['investment_thesis'])
            
        # Filter null indicators
        for horizon in ['intraday', 'swing', 'positional', 'longterm']:
            if horizon in result and result[horizon] and 'signals' in result[horizon]:
                result[horizon]['signals'] = [s for s in result[horizon]['signals'] if s.get('value_at_analysis') is not None]

        return AIAnalysisResult(**result)
    except Exception as e:
        pipeline_logger.log_error(ticker, "AI", f"Synthesis Validation Failed: {e}")
        return None

async def interpret_advanced(
    technical_response: TechnicalStockResponse,
    fundamental_response: Optional[AdvancedFundamentalAnalysis] = None,
    news_response: Optional[NewsResponse] = None,
    market_context: Optional[MarketContext] = None,
    mode: str = "all",
    system_instruction: str = ""
) -> AIAnalysisResult | None:
    
    # --- OPTIMIZATION: DETERMINISTIC BYPASS ---
    if technical_response.decision_state == "REJECT" or (technical_response.decision_state == "WAIT" and technical_response.data_confidence < 30):
        return _create_deterministic_analysis(technical_response, market_context)

    ticker = technical_response.ticker
    
    # Construct minimalist context (Audit Fix: Token Optimization)
    tech_summary = {
        "price": technical_response.current_price,
        "indicators": technical_response.technicals.model_dump(exclude_none=True) if technical_response.technicals else {},
        "algo_signal": technical_response.algo_signal.model_dump() if technical_response.algo_signal else {}
    }
    
    prompt = f"""
    Analyze {ticker} ({mode.upper()}).
    SYSTEM_CONFIDENCE: {technical_response.data_confidence:.1f}
    DECISION_STATE: {technical_response.decision_state.value}
    
    DATA: {json.dumps(tech_summary)}
    """

    # Baked-in Constitution (Audit Fix: Link-style instruction)
    base_system = """You are AlphaCore v20.2. Follow THE_COMPLETE_FRAMEWORK.
    1. Confidence MUST NOT exceed SYSTEM_CONFIDENCE.
    2. Exclude missing indicator signals.
    3. Action must match DECISION_STATE.
    4. Required: 'executive_summary' (str), 'investment_thesis' (str)."""

    return await _interpret_cached(ticker, prompt, base_system)

def _create_deterministic_analysis(tech_resp: TechnicalStockResponse, ctx: Optional[MarketContext]) -> AIAnalysisResult:
    """Generates a static AI analysis object for rejected trades."""
    reason = tech_resp.overview.summary
    action = tech_resp.trade_setup.action.value
    
    null_perspective = {
        "action": action,
        "confidence": {"value": 0.0, "min_value": 0.0, "max_value": 100.0, "label": "None", "legend": "Deterministic"},
        "entry_price": 0.0, "target_price": 0.0, "stop_loss": 0.0,
        "signals": [],
        "rationale": f"System Veto: {reason}"
    }
    
    return AIAnalysisResult(
        executive_summary=f"AUTOMATED REJECTION: {reason}",
        investment_thesis=f"Governor blocked trading on {tech_resp.ticker}. Reason: {reason}",
        rejection_analysis=f"Violation: {reason}.",
        intraday=null_perspective, swing=null_perspective, positional=null_perspective, longterm=null_perspective,
        options_fno={"strategy": "NONE", "status": "DATA_ABSENT", "rationale": "Locked."},
        market_sentiment={"score": {"value": 50.0, "label": "Neutral"}, "fear_greed_index": {"value": 50.0, "label": "Neutral"}}
    )