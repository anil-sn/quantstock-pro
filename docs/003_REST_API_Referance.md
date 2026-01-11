# QuantStock-Pro API Reference (v2.0)

## Base URL
`http://localhost:8000/api/v2`

## Authentication
All endpoints (except `/health`) require an API Key.
*   **Header**: `X-API-Key`
*   **Value**: Your configured `API_KEY` in `.env`.

---

## 🔧 Service Status Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | System health and component status (Public). |
| `/status` | GET | Detailed service metrics and environment. |
| `/limits` | GET | Current API rate limits and usage. |

---

## 📊 Stock Analysis (Comprehensive)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/analysis/{ticker}` | GET | Flagship multi-horizon report (Technical + Fundamental + AI). |
| `/analysis/bulk` | POST | Async batch analysis for multiple tickers. |
| `/analysis/{ticker}/technical` | GET | Just technical indicators from the analysis pipeline. |
| `/analysis/{ticker}/fundamental`| GET | Just fundamental metrics from the analysis pipeline. |
| `/analysis/{ticker}/execution` | GET | Just trading signals and execution levels. |

---

## 🎯 Technical Analysis

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/technical/{ticker}` | GET | Indicators across all 4 time horizons. |
| `/technical/{ticker}/{interval}` | GET | Indicators for a specific interval (1d, 1h, 15m). |
| `/technical/{ticker}/signals` | GET | Just trading signals (Trend, Momentum). |
| `/technical/{ticker}/levels` | GET | Just price levels (Support, Resistance). |

---

## 📈 Fundamental Analysis

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/fundamental/{ticker}` | GET | Complete fundamental dive (DCF + Quality). |
| `/fundamental/{ticker}/valuation`| GET | Intrinsic valuation models only (DCF, Graham). |
| `/fundamental/{ticker}/quality` | GET | Quality grade and scoring only. |
| `/fundamental/{ticker}/ratios` | GET | Core financial ratios only. |

---

## 📰 News & Sentiment

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/news/{ticker}` | GET | Aggregated filtered news headlines. |
| `/news/{ticker}/signal` | GET | Institutional-grade signal news only. |
| `/news/{ticker}/sentiment` | GET | Aggregated sentiment scores. |
| `/news/{ticker}/trending` | GET | Emerging trending topics. |

---

## 🤖 AI & Research

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/research/{ticker}` | POST | Start Deep Research loop (Async). |
| `/research/{ticker}/status` | GET | Check research task status. |
| `/research/{ticker}/report` | GET | Retrieve full research synthesis. |
| `/ai/analyze` | POST | Custom AI-driven analysis prompt. |
| `/ai/explain/{signal}` | GET | AI narrative explaining a specific signal. |

---

## 💼 Market Context

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/context/{ticker}` | GET | Complete Smart Money context. |
| `/context/{ticker}/analysts` | GET | Analyst ratings and price targets. |
| `/context/{ticker}/insiders` | GET | Recent material insider activity. |
| `/context/{ticker}/options` | GET | Options market sentiment (PCR, IV). |
| `/context/{ticker}/institutions` | GET | Institutional ownership data. |

---

## ⚡ Real-time & Streaming (Beta)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/ws/analysis` | WS | Real-time analysis updates. |
| `/ws/levels` | WS | Real-time price level shifts. |
| `/stream/{ticker}/signals` | GET | SSE stream for trading signals. |