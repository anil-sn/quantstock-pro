import json
import re
import time
import hashlib
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
    """Sanitize text to prevent prompt injection and handle sensitive characters."""
    if not text: return ""
    # Remove potentially dangerous sequences
    text = text.replace("```", "'''")
    text = text.replace("${ ", "\\${ ")
    text = text.replace("#{ ", "\\#{ ")
    # Escape control characters
    text = "".join(ch for ch in text if ord(ch) >= 32 or ch in "\n\r\t")
    return text.strip()

def get_prompt_hash(prompt: str, system_instruct: str) -> str:
    """Generate a unique hash for the prompt configuration."""
    return hashlib.sha256(f"{prompt}{system_instruct}".encode()).hexdigest()

@alru_cache(maxsize=100, ttl=300)
async def _interpret_cached(ticker: str, prompt: str, system_instruct: str, cache_key: str) -> AIAnalysisResult | None:
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
        
        if not response or not response.text:
            pipeline_logger.log_error(ticker, "AI", "Gemini returned empty response.")
            return None

        text = response.text.strip()
        try:
            # Handle markdown code blocks
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
                
            result = json.loads(text)
            
            # --- Schema Unwrapping (Audit Fix) ---
            if isinstance(result, dict) and "AIAnalysisResult" in result:
                result = result["AIAnalysisResult"]
            
            # --- Defensive Coercion (Audit Fix) ---
            if isinstance(result, dict):
                # 1. Handle missing executive_summary
                if "executive_summary" not in result and "ticker" in result:
                    result["executive_summary"] = f"Analysis for {result['ticker']}"
                
                # 2. Handle non-dict market_sentiment
                if "market_sentiment" in result and not isinstance(result["market_sentiment"], dict):
                    lbl = str(result["market_sentiment"])
                    result["market_sentiment"] = {
                        "score": 50.0, "fear_greed_index": 50.0, "summary": lbl
                    }
                
                # 2b. Harden numeric sentiment fields (Audit Fix)
                if "market_sentiment" in result and isinstance(result["market_sentiment"], dict):
                    for field in ["score", "fear_greed_index"]:
                        val = result["market_sentiment"].get(field)
                        if val is not None:
                            try:
                                # Strip non-numeric and coerce
                                if isinstance(val, str):
                                    clean_val = re.sub(r'[^\d.]', '', val)
                                    result["market_sentiment"][field] = float(clean_val) if clean_val else 50.0
                                else:
                                    result["market_sentiment"][field] = float(val)
                            except:
                                result["market_sentiment"][field] = 50.0
                        else:
                            result["market_sentiment"][field] = 50.0
                
                # 3. Schema Repair for Horizons (Audit Fix)
                for h in ['intraday', 'swing', 'positional', 'longterm']:
                    if h in result and isinstance(result[h], dict):
                        # Ensure required fields are present and NOT None
                        if result[h].get("entry_price") is None: result[h]["entry_price"] = 0.0
                        if result[h].get("target_price") is None: result[h]["target_price"] = 0.0
                        if result[h].get("stop_loss") is None: result[h]["stop_loss"] = 0.0
                        if result[h].get("rationale") is None: result[h]["rationale"] = "Synthesis complete."
                        if result[h].get("signals") is None: result[h]["signals"] = []
                        if result[h].get("confidence") is None: result[h]["confidence"] = 0.0
        except json.JSONDecodeError as je:
            pipeline_logger.log_error(ticker, "AI", f"JSON Decode Error: {je}. Raw: {text[:200]}")
            return None
        
        # --- AUDIT FIX: DEFENSIVE SCHEMA COERCION ---
        if isinstance(result, dict):
            if isinstance(result.get('investment_thesis'), dict):
                result['investment_thesis'] = json.dumps(result['investment_thesis'])
                
            # Filter null indicators
            for horizon in ['intraday', 'swing', 'positional', 'longterm']:
                if horizon in result and isinstance(result[horizon], dict) and 'signals' in result[horizon]:
                    result[horizon]['signals'] = [s for s in result[horizon]['signals'] if isinstance(s, dict) and s.get('value_at_analysis') is not None]

            return AIAnalysisResult(**result)
        else:
            pipeline_logger.log_error(ticker, "AI", f"Result is not a dict: {type(result)}")
            return None
    except Exception as e:
        import traceback
        pipeline_logger.log_error(ticker, "AI", f"Gemini Execution/Validation Failed: {str(e)}")
        pipeline_logger.log_payload(ticker, "AI", "FULL_TRACEBACK", traceback.format_exc())
        return None

async def interpret_advanced(
    technical_response: TechnicalStockResponse,
    fundamental_response: Optional[AdvancedFundamentalAnalysis] = None,
    news_response: Optional[NewsResponse] = None,
    market_context: Optional[MarketContext] = None,
    mode: str = "all",
    system_instruction: str = "",
    force_ai: bool = False
) -> AIAnalysisResult | None:
    try:
        # --- OPTIMIZATION: DETERMINISTIC BYPASS ---
        if not force_ai:
            if technical_response.decision_state == "REJECT" or (technical_response.decision_state == "WAIT" and technical_response.data_confidence < 30):
                return _create_deterministic_analysis(technical_response, market_context)

        ticker = technical_response.ticker
        
        # Construct context blocks
        horizons_data = {}
        if technical_response.horizons:
            # MultiHorizonSetups has these exact fields
            for h_name in ['intraday', 'swing', 'positional', 'longterm']:
                h_obj = getattr(technical_response.horizons, h_name, None)
                if h_obj:
                    # Map TradeSetup to expected HorizonPerspective fields
                    horizons_data[h_name] = {
                        "action": h_obj.action.value if h_obj.action else "WAIT",
                        "confidence": h_obj.confidence.value if h_obj.confidence else 0.0,
                        "entry_price": h_obj.entry_zone[0] if h_obj.entry_zone else technical_response.current_price,
                        "target_price": h_obj.take_profit_targets[0] if h_obj.take_profit_targets else technical_response.current_price * 1.05,
                        "stop_loss": h_obj.stop_loss if h_obj.stop_loss else technical_response.current_price * 0.95,
                        "rationale": "Data provided by quantitative engine."
                    }
    
        tech_summary = {
            "price": technical_response.current_price,
            "primary_indicators": technical_response.technicals.model_dump(exclude_none=True) if technical_response.technicals else {},
            "primary_algo_signal": technical_response.algo_signal.model_dump() if technical_response.algo_signal else {},
            "multi_horizon_setups": horizons_data
        }
        
        fund_summary = fundamental_response.executive_summary if fundamental_response else "N/A"
        news_summary = [n.title for n in news_response.news[:10]] if news_response else []
        context_summary = market_context.model_dump(exclude_none=True) if market_context else {}

        prompt = f"""
        Perform a professional, multi-horizon financial analysis for {ticker} using the provided data.
        
        <MARKET_DATA>
        Ticker: {ticker}
        Analysis Mode: {mode.upper()}
        System Confidence: {technical_response.data_confidence:.1f}
        Decision State: {technical_response.decision_state.value}
        
        Technical Horizons & Signals:
        {json.dumps(tech_summary, indent=2)}
        
        Fundamental Assessment:
        {json.dumps(fund_summary, indent=2)}
        
        Smart Money Context:
        {json.dumps(context_summary, indent=2)}
        
        Latest News Headlines:
        {json.dumps(news_summary, indent=2)}
        </MARKET_DATA>

        STRICT INSTRUCTIONS:
        1. Base your analysis ONLY on the data provided inside the <MARKET_DATA> tags.
        2. STRUCTURE the 'executive_summary' field as a comprehensive Markdown report using this EXACT structure:
           ## Executive Summary
           - **Overall Action:** [BUY/SELL/HOLD/WAIT/REJECT]
           - **Primary Rationale:** [2-3 sentences combining key technical/fundamental drivers]
           - **System Confidence:** [≤{technical_response.data_confidence:.1f}]

           ## Multi-Horizon Analysis
           | Horizon | Action | Confidence | Target Price | Stop Loss | Rationale |
           |---------|--------|------------|--------------|-----------|-----------|
           | Intraday | [Action] | [Confidence] | [Price] | [Price] | [Technical: cite specific levels] |
           | Swing | [Action] | [Confidence] | [Price] | [Price] | [Technical: cite specific levels] |
           | Positional | [Action] | [Confidence] | [Price] | [Price] | [Technical + Fundamental mix] |
           | Long-Term | [Action] | [Confidence] | [Price] | [Price] | [Fundamental: cite specific metrics] |

           ## Key Evidence Synthesis
           **Technical:**
           - [Cite Price vs BB width, RSI, ADX, and primary algo signal]
           
           **Fundamental:**
           - [Cite Composite score, Grade, P/E, and capital efficiency/ROIC]
           
           **Market Context:**
           - [Cite Analyst consensus, price targets, and news sentiment]

           ## Risk Assessment
           - **Volatility:** [Cite ATR and % of price]
           - **Key Risks:** [List top 3 fundamental or technical risks]
           - **Max Capital at Risk:** [Evidentiary conclusion based on risk engines]

           ## Final Recommendation
           [Concise synthesis with explicit action for each horizon]

        3. POPULATE ALL horizon blocks (intraday, swing, positional, longterm) objects in the JSON to match the Markdown table exactly.
        4. Action MUST BE one of: BUY, SELL, HOLD, WAIT, REJECT.
        5. Confidence MUST NOT exceed the provided System Confidence ({technical_response.data_confidence:.1f}).
        6. Synthesis MUST be factual and evidentiary. Cite specific technical levels or fundamental ratios provided.
        7. Populate 'market_sentiment' based on the news flow and smart money context.
        8. ENFORCEMENT: If any provided data point violates the system constraints (e.g., confidence > {technical_response.data_confidence:.1f}), ADJUST it to the maximum allowed value ({technical_response.data_confidence:.1f}) and note the adjustment in the rationale.
        9. PRICE LEVEL CONSISTENCY: For Intraday and Swing horizons, calculate target/stop EXCLUSIVELY from the provided S1/S2/R1/R2 levels. Do not use engine-generated targets that contradict these levels.
        10. COMPLETE JSON: Every field in the AIAnalysisResult schema (intraday, swing, positional, longterm, market_sentiment) MUST be populated. Do not leave them null if data is available.
        """

        # Baked-in Constitution
        base_system = system_instruction or """You are AlphaCore v20.2, a Senior Quantitative Strategist.
        You MUST output a single valid JSON object following the AIAnalysisResult schema.
        Ensure 'executive_summary' contains the Markdown structured report requested in the prompt.
        
        CRITICAL SCHEMA RULES:
        1. 'executive_summary' and 'investment_thesis' MUST be strings.
        2. 'market_sentiment' MUST be an object with score and fear_greed_index.
        3. ALL four horizon perspectives (intraday, swing, positional, longterm) MUST be populated as objects.
        
        Do not include any text before or after the JSON block. Do not nest the result under a top-level key."""

        cache_key = get_prompt_hash(prompt, base_system)
        return await _interpret_cached(ticker, prompt, base_system, cache_key)
    except Exception as e:
        import traceback
        pipeline_logger.log_error(technical_response.ticker, "AI", f"Interpret Advanced Crash: {e}")
        pipeline_logger.log_payload(technical_response.ticker, "AI", "CRASH_TRACE", traceback.format_exc())
        return None

def _create_deterministic_analysis(tech_resp: TechnicalStockResponse, ctx: Optional[MarketContext]) -> AIAnalysisResult:
    """Generates a static AI analysis object for rejected trades."""
    reason = tech_resp.overview.summary
    action = tech_resp.trade_setup.action.value
    ticker = tech_resp.ticker
    
    null_perspective = {
        "action": action,
        "confidence": 0.0,
        "entry_price": 0.0, "target_price": 0.0, "stop_loss": 0.0,
        "signals": [],
        "rationale": f"System Veto: {reason}"
    }
    
    return AIAnalysisResult(
        executive_summary=f"AUTOMATED REJECTION: {reason}",
        investment_thesis=f"Governor blocked trading on {ticker}. Reason: {reason}",
        rejection_analysis=f"Violation: {reason}.",
        intraday=null_perspective, swing=null_perspective, positional=null_perspective, longterm=null_perspective,
        options_fno={
            "strategy": "NONE", 
            "status": "DATA_ABSENT", 
            "rationale": "Locked.",
            "expiration_view": "N/A",
            "risk_reward": "N/A"
        },
        market_sentiment={
            "score": 50.0, 
            "fear_greed_index": 50.0,
            "summary": "Deterministic Neutral"
        }
    )