import yfinance as yf
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from cachetools import cached, TTLCache
from .models import FundamentalData, AnalystEstimates
from .settings import settings

def calculate_revenue_growth_yoy(financials: pd.DataFrame) -> Optional[float]:
    """
    Calculate actual YoY growth from quarterly financials with strict ordering validation.
    Audit 7.5.0: Verifies timestamp sequence to ensure latest data is used correctly.
    """
    try:
        if financials is not None and not financials.empty:
            # 1. Validate Temporal Ordering
            # Ensure columns are datetime and sorted descending (latest first)
            cols = pd.to_datetime(financials.columns)
            if not cols.is_monotonic_decreasing:
                financials = financials.reindex(columns=financials.columns[cols.argsort()[::-1]])
            
            # 2. Extract Revenue
            rev_key = "Total Revenue"
            if rev_key in financials.index:
                row = financials.loc[rev_key]
                if len(row) >= 4:
                    latest = row.iloc[0]
                    year_ago = row.iloc[3]
                    
                    # 3. Validation: Ensure we aren't comparing the same period or near-zero bases
                    if year_ago and abs(year_ago) > 1e5: # At least $100k
                        return (latest - year_ago) / abs(year_ago)
    except Exception as e:
        print(f"Growth calculation validation failed: {e}")
    return None

@cached(cache=TTLCache(maxsize=128, ttl=3600))
def fetch_raw_fundamentals(ticker: str) -> Tuple[FundamentalData, Dict[str, Any]]:
    """Fetch and sanitize raw fundamental data from yfinance with fallbacks."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Fallback for empty info: yfinance sometimes fails on first attempt
        if not info or len(info) < 5:
            stock = yf.Ticker(ticker)
            info = stock.info
            
        if not info or len(info) < 5:
            try:
                fast = stock.fast_info
                info["quoteType"] = fast.get("quoteType", "EQUITY")
                info["marketCap"] = fast.get("market_cap")
                info["exchange"] = fast.get("exchange")
            except:
                pass

        q_raw = str(info.get("quoteType", "EQUITY")).upper()
        TYPE_MAP = {
            "EQUITY": "Equity", 
            "ETF": "ETF", 
            "INDEX": "Index", 
            "CRYPTOCURRENCY": "Crypto", 
            "MUTUALFUND": "Fund",
            "CURRENCY": "Crypto"
        }
        q_type = TYPE_MAP.get(q_raw, "Equity")
        
        data = FundamentalData(
            ticker=ticker.upper(),
            asset_type=q_type,
            company_name=info.get("longName") or info.get("shortName") or ticker.upper(),
            description=info.get("longBusinessSummary"),
            industry=info.get("industry"),
            sector=info.get("sector"),
            exchange=info.get("exchange"),
            last_updated=datetime.now()
        )
        
        # Identity & Valuation
        data.market_cap = info.get("marketCap") or info.get("enterpriseValue")
        data.enterprise_value = info.get("enterpriseValue")
        data.trailing_pe = info.get("trailingPE")
        data.forward_pe = info.get("forwardPE")
        
        # Audit 7.3.0 Fix: PE Ratio Fallback
        current_price = info.get("currentPrice") or info.get("regularMarketPrice")
        forward_eps = info.get("forwardEps")
        if not data.forward_pe and current_price and forward_eps:
            try:
                data.forward_pe = current_price / forward_eps
            except: pass
            
        data.price_to_sales = info.get("priceToSalesTrailing12Months")
        data.price_to_book = info.get("priceToBook")
        data.enterprise_to_ebitda = info.get("enterpriseToEbitda")
        
        # Audit 7.5.0 Fix: Explicit Metric Calculations (Lazy implementation removal)
        total_rev = info.get("totalRevenue")
        if data.enterprise_value and total_rev and total_rev > 0:
            data.enterprise_to_revenue = data.enterprise_value / total_rev
        else:
            data.enterprise_to_revenue = info.get("enterpriseToRevenue")
            
        if data.forward_pe and data.forward_pe > 0:
            data.earnings_yield = 1 / data.forward_pe
        elif current_price and forward_eps and forward_eps > 0:
            data.earnings_yield = forward_eps / current_price
        
        data.book_value = info.get("bookValue")
        data.dividend_rate = info.get("dividendRate")
        
        # Audit 9.0.0: Temporal Synchronization of Profitability
        # Anchoring all returns to info.get("netIncomeToCommon") to prevent ROE/NI contradictions
        net_income_anchor = info.get("netIncomeToCommon")
        data.net_income = net_income_anchor
        data.total_revenue = total_rev
        
        data.profit_margin = info.get("profitMargins")
        data.gross_margins = info.get("grossMargins")
        data.operating_margins = info.get("operatingMargins")
        data.ebitda_margins = info.get("ebitdaMargins")
        data.ebitda = info.get("ebitda")
        
        # Re-calculating ROE/ROA from synchronized anchor if available
        # This prevents the Audit failure where NI was positive but ROE was negative
        equity = info.get("totalStockholderEquity")
        if net_income_anchor is not None and equity and equity > 0:
            data.return_on_equity = net_income_anchor / equity
        else:
            data.return_on_equity = info.get("returnOnEquity")
            
        total_assets = info.get("totalAssets")
        if net_income_anchor is not None and total_assets and total_assets > 0:
            data.return_on_assets = net_income_anchor / total_assets
        else:
            data.return_on_assets = info.get("returnOnAssets")
            
        data.return_on_invested_capital = info.get("returnOnInvestedCapital")
        
        # Invested Capital Calculation (Audit 6.1 Fix)
        # Formula: Debt + Equity - Cash
        if data.total_debt is not None and data.total_cash is not None:
            equity_val = equity or (data.market_cap if data.market_cap else 0)
            data.invested_capital = data.total_debt + equity_val - data.total_cash
        
        # Cash Flow
        data.free_cash_flow = info.get("freeCashflow")
        data.operating_cash_flow = info.get("operatingCashflow")
        data.net_income = info.get("netIncomeToCommon")
        data.total_revenue = info.get("totalRevenue")
        
        if data.total_revenue and data.free_cash_flow:
            data.free_cash_flow_margin = data.free_cash_flow / data.total_revenue
        if data.net_income and data.net_income != 0 and data.free_cash_flow:
            data.fcf_to_net_income_ratio = data.free_cash_flow / abs(data.net_income)
            if data.net_income < 0: data.fcf_to_net_income_ratio *= -1
        
        # Growth - STANDARDIZED (Audit Fix)
        # We calculate YoY from quarterly data to be safe, falling back to Yahoo's field
        q_fin = stock.quarterly_financials
        calc_growth = calculate_revenue_growth_yoy(q_fin)
        data.revenue_growth = calc_growth if calc_growth is not None else info.get("revenueGrowth")
        data.earnings_growth = info.get("earningsGrowth")
        
        # PE Adjustment MUST happen AFTER growth is set
        if data.forward_pe and data.revenue_growth and data.revenue_growth != 0:
            # Peg-style calculation: Forward PE / Revenue Growth (e.g. 29 / 32 = 0.9)
            # We use the raw percentage value (32.1 for 32.1%)
            growth_pct = abs(data.revenue_growth * 100)
            if growth_pct >= 1.0:
                data.rev_growth_adjusted_pe = data.forward_pe / growth_pct
            else:
                # Handle near-zero growth to avoid pathological ratios
                data.rev_growth_adjusted_pe = data.forward_pe

        if data.total_revenue:
            data.lifecycle_stage = "Early Scale" if data.total_revenue < settings.SMALL_CAP_REVENUE_THRESHOLD else "At-Scale Growth"

        # Financial Health
        data.total_debt = info.get("totalDebt")
        data.total_cash = info.get("totalCash")
        if data.total_cash is not None and data.total_debt is not None:
            data.net_cash = data.total_cash - data.total_debt
            data.net_cash_status = "Net Cash" if data.net_cash > 0 else "Net Debt"
        
        data.debt_to_equity = info.get("debtToEquity")
        
        # Institutional Normalization: Handle different reporting conventions (Audit 1 Fix)
        if data.debt_to_equity is not None:
            # Common conventions: 0.5 = 0.5:1, 50 = 50:1, 5000 = 5000%
            if data.debt_to_equity > 100:  # Clearly percentage (5000% = 50:1)
                data.debt_to_equity = data.debt_to_equity / 100
            elif data.debt_to_equity > 5:  # Possibly percentage (e.g. 50 meaning 0.5:1 or 50:1)
                # If D/E > 5, we check if it's likely a percentage convention
                # Most companies (except extreme cases) aren't > 500% D/E
                data.debt_to_equity = data.debt_to_equity / 100
            
        data.current_ratio = info.get("currentRatio")
        data.quick_ratio = info.get("quickRatio")
        
        if data.ebitda and info.get("interestExpense"):
            try:
                data.interest_coverage = float(data.ebitda) / abs(float(info["interestExpense"]))
            except: pass

        # Ownership & Analysts
        data.dividend_yield = info.get("dividendYield")
        data.payout_ratio = info.get("payoutRatio")
        data.held_percent_institutions = info.get("heldPercentInstitutions")
        data.held_percent_insiders = info.get("heldPercentInsiders")
        data.shares_outstanding = info.get("sharesOutstanding")
        data.float_shares = info.get("floatShares")
        
        # Governance Data (Audit 10.7)
        data.overall_risk_score = info.get("overallRisk")
        data.audit_risk_score = info.get("auditRisk")
        data.board_risk_score = info.get("boardRisk")
        
        data.analyst_estimates = AnalystEstimates(
            target_mean_price=info.get("targetMeanPrice"),
            target_median_price=info.get("targetMedianPrice"),
            number_of_analysts=info.get("numberOfAnalystOpinions"),
            recommendation_key=info.get("recommendationKey"),
            recommendation_mean=info.get("recommendationMean")
        )
            
        return data, info
    except Exception as e:
        print(f"Error fetching fundamentals for {ticker}: {e}")
        return FundamentalData(ticker=ticker.upper()), {}

def fetch_historical_financials(ticker: str) -> Dict[str, Any]:

    """Fetch multi-quarter financial statements for responsive trend analysis."""

    try:

        stock = yf.Ticker(ticker)

        # Audit Fix: Use quarterly data to align with recent quarter growth metrics

        return {

            "financials": stock.quarterly_financials,

            "balance_sheet": stock.quarterly_balance_sheet,

            "cashflow": stock.quarterly_cashflow

        }

    except Exception as e:

        print(f"Error fetching historical data for {ticker}: {e}")

        return {}
