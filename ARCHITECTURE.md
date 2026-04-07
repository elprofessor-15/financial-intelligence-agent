# System Architecture

## End-to-End Flow

```
Data Sources → Ingestion Pipeline → Storage Layer → Hybrid Retrieval → Agent Pipeline → FastAPI Output
```

---

## 1. Data Sources

- **SEC EDGAR** — 10-K filing structure for 20 major S&P 500 companies across 4 sections (risk_factors, revenue, business_overview, md_and_a) and 3 fiscal years (2021, 2022, 2023)
- **Yahoo Finance** — Daily OHLCV stock prices for all 20 tickers from 2021 to 2023 via the yfinance library

---

## 2. Ingestion Pipeline

**File:** `src/ingestion/sec_pipeline.py`

Steps:
1. Generate structured text per company, per year, per section based on 10-K filing templates
2. Split each section using a sliding window of 300 words with 50-word overlap
3. Deduplicate chunks using MD5 hash of (ticker + year + section + chunk index)
4. Insert all chunks into SQLite table `filing_chunks` with columns: id, ticker, company_name, filing_type, fiscal_year, section, chunk_index, text, word_count
5. Fetch stock prices using yfinance and insert into SQLite table `stock_prices` with columns: ticker, date, open, high, low, close, volume

Result: 100,000+ document chunks and ~15,000 stock price rows stored in `data/processed/filings.db`

---

## 3. Storage Layer

### ChromaDB (Vector Store)
- **File:** `data/embeddings/chroma/`
- Stores embeddings generated from all 100K+ chunks
- Embedding model: sentence-transformers all-MiniLM-L6-v2 (local, 384 dimensions)
- Similarity metric: cosine similarity
- Supports metadata filtering by ticker, section, and fiscal year

### SQLite (Structured Store)
- **File:** `data/processed/filings.db`
- Two tables: `filing_chunks` and `stock_prices`
- Used for SQL aggregations: price comparisons, volatility calculations, range queries
- Indexed on ticker and section for fast filtering

---

## 4. Hybrid Retrieval

**File:** `src/retrieval/hybrid_retriever.py`

Three-stage pipeline:

```
Query
  |
  +---> BM25 Search (rank-bm25)
  |         Tokenizes query, scores all 100K+ chunks by keyword match
  |
  +---> Vector Search (ChromaDB)
  |         Embeds query, finds top-K chunks by cosine similarity
  |         Supports metadata filters (ticker, section)
  |
  v
Reciprocal Rank Fusion (RRF)
    Merges BM25 and vector results using 1/(60+rank) scoring
    Deduplicates by text prefix
  |
  v
Re-ranking
    Second-pass cosine similarity between query embedding and top merged results
    Final sorted list returned to agent
  |
  v
SQL Aggregation (optional)
    Runs price_comparison or volatility queries on stock_prices table
    Returns structured strings added to analyst context
```

---

## 5. Agent Pipeline

**Files:** `src/agents/`

### Guardrail Check
- **File:** `src/agents/guardrails.py`
- First layer before any agent runs
- Pattern-matches query against blocked terms: manipulation, illegal, insider trading, pump and dump, fraud, money laundering, etc.
- If blocked: returns a clean informational message, logs the block decision, short-circuits the pipeline
- If allowed: passes query to Planner

### Planner Agent
- **File:** `src/agents/planner.py`
- LLM: Cerebras llama3.1-8b
- Input: user query
- Output: structured JSON plan with sub_queries, tickers, sections_needed, aggregations_needed, reasoning_type, complexity
- Robust fallback: if LLM returns malformed JSON, uses original query as single sub-query
- Logs decision to observability layer

### Retriever Agent
- **File:** `src/agents/retriever_agent.py`
- Runs hybrid search for each sub-query from the plan
- Applies ticker and section filters from the plan
- Deduplicates results across sub-queries
- Runs SQL aggregations specified in the plan
- Returns top 20 unique documents and SQL results

### Analyst Agent
- **File:** `src/agents/analyst.py`
- LLM: Cerebras llama3.1-8b
- Input: original query + plan + retrieved documents + SQL results
- Output: structured financial analysis with citations, comparisons, and insights
- Logs answer length to observability layer

### Critic Agent
- **File:** `src/agents/critic.py`
- LLM: Cerebras llama3.1-8b
- Input: original query + analyst answer
- Output: JSON with quality_score (0.0 to 1.0), is_sufficient flag, issues list, refined_query
- If quality_score < 0.6: orchestrator retries with refined_query
- Robust fallback: if LLM returns malformed JSON, accepts answer as sufficient to avoid infinite loops
- Max retries: 2

### Orchestrator
- **File:** `src/agents/orchestrator.py`
- Coordinates the full pipeline: Guardrail → Planner → Retriever → Analyst → Critic → retry if needed
- Returns final structured result with answer, sources, quality_score, doc_count, blocked flag

---

## 6. API Layer

**File:** `src/api/app.py`

Built with FastAPI. The full web UI is embedded directly in the Python file as an HTML string.

Endpoints:

| Method | Path | Description |
|---|---|---|
| GET | / | Full web UI (HTML/CSS/JS) |
| POST | /query | Run full agent pipeline |
| POST | /search | Hybrid search without agent |
| GET | /prices/{ticker} | Stock price series from SQLite |
| GET | /evaluate | Load or run evaluation report |
| GET | /health | Health check |
| GET | /docs | Swagger UI |

Web UI views:
- Company Reports: select a company, view metadata, run AI queries, see results
- Stock Trends: Chart.js price chart with 1Y/2Y/All range selector from real SQLite data
- Risk Factors: cross-company risk analysis with predefined chip queries
- Search Filings: direct hybrid search with ticker and section filters
- Evaluation: runs eval suite and shows Recall@10 and Precision@10 per query
- Query Log: in-memory log of all queries run in the session

---

## 7. Evaluation

**File:** `src/evaluation/eval.py`

Five predefined evaluation queries with known relevant tickers and sections. For each query:
- Runs hybrid search and retrieves top 10 documents
- Computes Recall@10: fraction of relevant tickers found in top 10
- Computes Precision@10: fraction of top 10 that are relevant

Outputs a JSON report at `evaluation/results/eval_report.json` and prints a table using Rich.

---

## 8. Observability

**File:** `src/observability/logger.py`

Every agent run writes a JSONL log at `evaluation/results/run_<timestamp>.jsonl`.

Events logged:
- `query` — original user query and timestamp
- `decision` (guardrail) — allowed or blocked with reason
- `decision` (planner) — full plan JSON
- `retrieval` — doc count, top 5 source metadata, SQL keys used
- `decision` (analyst) — answer character length
- `decision` (critic) — quality score, is_sufficient, issues
- `final_answer` — complete answer, sources, quality score

---

## Component Dependency Map

```
main.py
    |
    +-- sec_pipeline.py ---------> filings.db (SQLite)
    |
    +-- orchestrator.py
            |
            +-- guardrails.py
            |
            +-- planner.py -------> Cerebras API
            |
            +-- retriever_agent.py
            |       |
            |       +-- hybrid_retriever.py
            |               |
            |               +-- ChromaDB (vector)
            |               +-- BM25 index (in-memory)
            |               +-- filings.db (SQL aggregations)
            |
            +-- analyst.py -------> Cerebras API
            |
            +-- critic.py --------> Cerebras API
            |
            +-- logger.py --------> evaluation/results/*.jsonl
            |
            v
        app.py (FastAPI)
            |
            +-- /query endpoint
            +-- /search endpoint
            +-- /prices endpoint
            +-- /evaluate endpoint
```