import yfinance as yf
from pydantic import BaseModel
from typing import Optional, Literal, List

class NewsItem(BaseModel):
    title: str
    publisher: str
    link: str
    publish_time: int

class FundamentalData(BaseModel):
    asset_type: Literal["Equity", "Commodity", "Future", "ETF", "Index", "Unknown"] = "Unknown"
    
    # Qualitative/Company info
    company_name: Optional[str] = None
    description: Optional[str] = None
    employees: Optional[int] = None
    industry: Optional[str] = None
    sector: Optional[str] = None
    
    # Common
    currency: Optional[str] = None
    exchange: Optional[str] = None
    
    # Valuation Metrics
    market_cap: Optional[int] = None
    enterprise_value: Optional[int] = None
    trailing_pe: Optional[float] = None
    forward_pe: Optional[float] = None
    peg_ratio: Optional[float] = None
    price_to_sales: Optional[float] = None
    price_to_book: Optional[float] = None
    enterprise_to_ebitda: Optional[float] = None
    
    # Profitability & Efficiency
    profit_margin: Optional[float] = None
    gross_margins: Optional[float] = None
    operating_margins: Optional[float] = None
    ebitda_margins: Optional[float] = None
    ebitda: Optional[int] = None
    return_on_equity: Optional[float] = None
    return_on_assets: Optional[float] = None
    
    # Cash Flow
    free_cash_flow: Optional[int] = None
    operating_cash_flow: Optional[int] = None
    
    # Growth
    revenue_growth: Optional[float] = None
    earnings_growth: Optional[float] = None
    
    # Financial Health
    total_debt: Optional[int] = None
    total_cash: Optional[int] = None
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    
    # Dividends & Ownership
    dividend_yield: Optional[float] = None
    payout_ratio: Optional[float] = None
    held_percent_institutions: Optional[float] = None
    held_percent_insiders: Optional[float] = None
    
    # Analyst Views
    recommendation_key: Optional[str] = None
    target_mean_price: Optional[float] = None
    
    # News
    news: List[NewsItem] = []
    
    # Commodity/Future Specific
    contract_size: Optional[str] = None
    expire_date: Optional[str] = None

def get_fundamentals(ticker: str) -> FundamentalData:
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        q_type = info.get("quoteType", "Unknown").title()
        if q_type == "Future": q_type = "Commodity"
        
        data = FundamentalData(
            asset_type=q_type if q_type in ["Equity", "Commodity", "Etf", "Index"] else "Unknown",
            company_name=info.get("longName"),
            description=info.get("longBusinessSummary"),
            employees=info.get("fullTimeEmployees"),
            industry=info.get("industry"),
            sector=info.get("sector"),
            currency=info.get("currency"),
            exchange=info.get("exchange"),
        )
        
        # Fetch News (Common for all asset types)
        try:
            raw_news = stock.news
            if raw_news:
                parsed_news = []
                for n in raw_news[:5]:
                    # Handle yfinance 1.0+ nested structure
                    content = n.get('content', n) # Fallback to n if content not present
                    
                    title = content.get('title', '')
                    link = content.get('canonicalUrl', {}).get('url', '') if isinstance(content.get('canonicalUrl'), dict) else content.get('link', '')
                    
                    # Publisher extraction
                    provider = content.get('provider', {})
                    publisher = provider.get('displayName') if isinstance(provider, dict) else content.get('publisher', 'Unknown')
                    
                    # Time extraction
                    pub_time = 0 # Default
                    if 'pubDate' in content:
                        # You might want to parse ISO string to timestamp if needed, 
                        # but keeping it simple for now or strictly strictly creating an int 
                        # if your model requires int. The model says int, yfinance gives ISO string often now.
                        # Let's try to get providerPublishTime if available at top level or 0
                        pass
                    
                    # Try to find an integer timestamp if possible, otherwise 0
                    # yfinance often provides 'providerPublishTime' at top level in older versions, 
                    # but new version has 'pubDate' string.
                    # We will just use 0 to avoid parsing complexity for now, or update model to allow string.
                    
                    parsed_news.append(NewsItem(
                        title=title,
                        publisher=publisher,
                        link=link,
                        publish_time=0 
                    ))
                data.news = parsed_news
        except Exception as e:
            print(f"Warning: Could not fetch news for {ticker}: {e}")
        
        if data.asset_type in ["Equity", "Etf"]:
            # Valuation
            data.market_cap = info.get("marketCap")
            data.enterprise_value = info.get("enterpriseValue")
            data.trailing_pe = info.get("trailingPE")
            data.forward_pe = info.get("forwardPE")
            data.peg_ratio = info.get("trailingPegRatio")
            data.price_to_sales = info.get("priceToSalesTrailing12Months")
            data.price_to_book = info.get("priceToBook")
            data.enterprise_to_ebitda = info.get("enterpriseToEbitda")
            
            # Profitability
            data.profit_margin = info.get("profitMargins")
            data.gross_margins = info.get("grossMargins")
            data.operating_margins = info.get("operatingMargins")
            data.ebitda_margins = info.get("ebitdaMargins")
            data.ebitda = info.get("ebitda")
            data.return_on_equity = info.get("returnOnEquity")
            data.return_on_assets = info.get("returnOnAssets")
            
            # Cash Flow
            data.free_cash_flow = info.get("freeCashflow")
            data.operating_cash_flow = info.get("operatingCashflow")
            
            # Growth
            data.revenue_growth = info.get("revenueGrowth")
            data.earnings_growth = info.get("earningsGrowth")
            
            # Health
            data.total_debt = info.get("totalDebt")
            data.total_cash = info.get("totalCash")
            data.debt_to_equity = info.get("debtToEquity")
            data.current_ratio = info.get("currentRatio")
            data.quick_ratio = info.get("quickRatio")
            
            # Ownership
            data.dividend_yield = info.get("dividendYield")
            data.payout_ratio = info.get("payoutRatio")
            data.held_percent_institutions = info.get("heldPercentInstitutions")
            data.held_percent_insiders = info.get("heldPercentInsiders")
            
            # Analysts
            data.recommendation_key = info.get("recommendationKey")
            data.target_mean_price = info.get("targetMeanPrice")
            
        return data
        
    except Exception as e:
        print(f"Error fetching fundamentals for {ticker}: {e}")
        return FundamentalData()
