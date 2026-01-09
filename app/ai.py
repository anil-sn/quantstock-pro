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
    company_info: dict,
    mode: str = "all",
    fundamentals: Any = None,
    market_context: Any = None,
    system_context: str = ""
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

    fundamentals_section = ""
    news_section = ""
    context_section = ""
    
    if fundamentals:
        # Extract news to format it nicely
        news_items = getattr(fundamentals, 'news', [])
        if news_items:
            news_list = "\n".join([f"- {n.title} ({n.publisher})" for n in news_items])
            news_section = f"""
    ## RECENT NEWS & CATALYSTS
    {news_list}
    """
            fund_dict = fundamentals.model_dump()
            fund_dict.pop('news', None)
            fundamentals_json = json.dumps(fund_dict, indent=2)
        else:
            fundamentals_json = fundamentals.model_dump_json(indent=2)
            
        fundamentals_section = f"""
    ## FUNDAMENTAL DATA
    {fundamentals_json}
    """

    if market_context:
        context_section = f"""
    ## MARKET CONTEXT (SMART MONEY)
    {market_context.model_dump_json(indent=2)}
    """

    prompt = f"""
    # QUANTITATIVE STOCK ANALYSIS FRAMEWORK
    
    ## S-TIER SYSTEM INSTRUCTIONS (MANDATORY)
    {system_context}
    
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
    3. **Null Indicators:** If any technical indicator (e.g. 'cci', 'volume_ratio') is 'null' in the provided JSON, it means it is POISONED or DATA UNAVAILABLE. **Do NOT include it in the 'signals' list.** You must mention the missing data in the 'risk' or 'rationale' section instead.
    4. **No Cowardice:** If the system status is REJECTED, you MUST set your response 'action' to 'REJECT'. You are forbidden from recommending a BUY/SELL.
    5. **Rejection Protocol:** If the system status is REJECTED, do NOT discuss potential upside targets or 'what if' scenarios. Focus ONLY on the risks that triggered the rejection (e.g., Insider Selling, Weak Trend, Low Volume). Your output must be a 'risk report', not a 'trade plan'.
    6. **Semantic Purity:** If an indicator value is extreme (e.g. CCI > 500) or flagged as invalid/null, do NOT describe it as 'extreme oversold'. Describe it as 'Data Unreliable' or 'Indicator Failure'. Do not build a thesis on broken data.
    
    ## TRADING RULES & CONSTITUTION
    {framework_content}
    
    ## CONTEXT
    You are a professional multi-horizon trader. Analyze {ticker}.
    
    ## COMPANY OVERVIEW
    {json.dumps({k: company_info.get(k) for k in ['longName', 'sector', 'industry', 'marketCap']}, indent=2)}
    
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

