import json
import re
from typing import Any
from pathlib import Path
from google import genai
from google.genai import types
from .models import Technicals, AIAnalysisResult, MarketSentiment
from .settings import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY) if settings.GEMINI_API_KEY else None

async def interpret_advanced(
    ticker: str, 
    technicals: Technicals, 
    company_info: dict
) -> AIAnalysisResult | None:
    if not client:
        return None

    # Load Framework
    try:
        framework_path = Path(__file__).parent.parent / "THE_COMPLETE_FRAMEWORK.md"
        framework_content = framework_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Warning: Could not load framework: {e}")
        framework_content = "Adhere to standard professional trading risk management rules."

    prompt = f"""
    # QUANTITATIVE STOCK ANALYSIS FRAMEWORK
    
    ## TRADING RULES & CONSTITUTION
    {framework_content}
    
    ## CONTEXT
    You are a professional multi-horizon trader. Analyze {ticker}.
    
    ## COMPANY OVERVIEW
    {json.dumps({k: company_info.get(k) for k in ['longName', 'sector', 'industry', 'marketCap']}, indent=2)}
    
    ## QUANTITATIVE METRICS
    {technicals.model_dump_json(indent=2)}
    
    ## OUTPUT FORMAT
    Return ONLY valid JSON matching this schema:
    {{
        "executive_summary": "string",
        "investment_thesis": "string",
        "intraday": {{
            "action": "BUY/SELL/HOLD/WAIT",
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
        result = json.loads(clean_json)
        
        return AIAnalysisResult(**result)
    except Exception as e:
        print(f"AI Analysis Error: {e}")
        return None

async def interpret(snapshot: Any) -> Any:
    """Compatibility shim if needed"""
    return await interpret_advanced("UNKNOWN", snapshot, {})

