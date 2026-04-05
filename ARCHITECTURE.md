## Component Details

### 1. Data Platform Layer
- **sec_pipeline.py** — Downloads SEC EDGAR filings for 20 S&P 500 companies
- **yfinance** — Fetches daily OHLCV stock prices 2021–2023
- **Chunking** — 300-word sliding window with 50-word overlap
- **SQLite** — Stores 100K+ chunks with metadata + stock price tables

### 2. Retrieval System
- **ChromaDB** — Persistent vector store with cosine similarity
- **sentence-transformers** — Local `all-MiniLM-L6-v2` embeddings (no API cost)
- **BM25** — `rank-bm25` for keyword matching
- **RRF Fusion** — Reciprocal Rank Fusion merges BM25 + vector results
- **Re-ranking** — Second-pass cosine similarity for final ordering

### 3. Agent Pipeline
| Agent | Role |
|---|---|
| Planner | Decomposes query, identifies tickers + sections needed |
| Retriever | Runs hybrid search + SQL aggregations |
| Analyst | Synthesizes answer from context |
| Critic | Scores quality, triggers retry if score < 0.6 |

### 4. API Layer
- FastAPI with 5 endpoints
- Full web UI embedded in Python (no separate frontend build)

### 5. Observability
- JSONL logs per session
- Logs: query → planner decision → retrieval → analyst → critic → final answer
