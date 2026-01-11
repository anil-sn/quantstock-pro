from newsapi import NewsApiClient
import feedparser
import asyncio
import httpx
from typing import List
from datetime import datetime
from async_lru import alru_cache
from .models import NewsItem
from .settings import settings
import urllib.parse

class UnifiedNewsFetcher:
    """Fetches and merges news from multiple sources (Yahoo, Google, NewsAPI)"""

    @classmethod
    async def fetch_news_api(cls, ticker: str) -> List[NewsItem]:
        """Fetch high-relevancy articles from NewsAPI.org with SSL resilience"""
        if not settings.NEWS_API_KEY:
            return []
            
        async def do_fetch(verify_ssl: bool = True):
            async with httpx.AsyncClient(verify=verify_ssl, timeout=10.0) as client:
                resp = await client.get(
                    "https://newsapi.org/v2/everything",
                    params={
                        "q": ticker,
                        "language": "en",
                        "sortBy": "relevancy",
                        "pageSize": 10,
                        "apiKey": settings.NEWS_API_KEY
                    }
                )
                resp.raise_for_status()
                return resp.json()

        try:
            # 1. Try Secure Fetch
            all_articles = await do_fetch(verify_ssl=True)
        except httpx.ConnectError as e:
            # 2. Handle specific SSL verification failure
            if "CERTIFICATE_VERIFY_FAILED" in str(e):
                print(f"WARNING: SSL Verification failed for NewsAPI. Retrying with verification DISABLED. (Run 'pip install certifi' to fix)")
                try:
                    all_articles = await do_fetch(verify_ssl=False)
                except Exception as ex:
                    print(f"NewsAPI Final Failure: {ex}")
                    return []
            else:
                print(f"NewsAPI Connection Error: {e}")
                return []
        except Exception as e:
            print(f"NewsAPI Fetch Error: {e}")
            return []
            
        items = []
        for article in all_articles.get('articles', []):
            # Parse timestamp: '2024-01-11T12:00:00Z'
            try:
                dt = datetime.strptime(article['publishedAt'], '%Y-%m-%dT%H:%M:%SZ')
                ts = int(dt.timestamp())
            except:
                ts = int(datetime.now().timestamp())

            items.append(NewsItem(
                title=article['title'],
                publisher=article['source'].get('name', 'NewsAPI'),
                link=article['url'],
                publish_time=ts
            ))
        return items

    @classmethod
    async def fetch_google_news(cls, ticker: str) -> List[NewsItem]:
        """Fetch news from Google News RSS"""
        query = urllib.parse.quote(f"{ticker} stock market analysis")
        url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
        
        try:
            loop = asyncio.get_event_loop()
            feed = await loop.run_in_executor(None, feedparser.parse, url)
            
            items = []
            for entry in feed.entries[:10]:
                try:
                    dt = datetime(*entry.published_parsed[:6])
                    ts = int(dt.timestamp())
                except:
                    ts = int(datetime.now().timestamp())

                items.append(NewsItem(
                    title=entry.title,
                    publisher=entry.source.get('title', 'Google News'),
                    link=entry.link,
                    publish_time=ts
                ))
            return items
        except Exception as e:
            print(f"Google News Fetch Error: {e}")
            return []

    @classmethod
    @alru_cache(maxsize=128, ttl=3600)
    async def fetch_all(cls, ticker: str) -> List[NewsItem]:
        """Fetch from all sources and deduplicate by title (1-hour cache)"""
        from .fundamentals import get_news as get_yahoo_news
        
        # Run in parallel
        yahoo_task = asyncio.get_event_loop().run_in_executor(None, get_yahoo_news, ticker)
        google_task = cls.fetch_google_news(ticker)
        newsapi_task = cls.fetch_news_api(ticker)
        
        results = await asyncio.gather(yahoo_task, google_task, newsapi_task)
        
        all_news = results[0] + results[1] + results[2]
        
        # Deduplicate
        seen_titles = set()
        unique_news = []
        for n in all_news:
            title_clean = n.title.lower().strip()
            if title_clean not in seen_titles:
                unique_news.append(n)
                seen_titles.add(title_clean)
                
        # Sort by time
        unique_news.sort(key=lambda x: x.publish_time, reverse=True)
        return unique_news[:20] # Return top 20
