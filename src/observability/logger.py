import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

LOG_DIR = Path("evaluation/results")
LOG_DIR.mkdir(parents=True, exist_ok=True)


class AgentLogger:
    def __init__(self):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_path = LOG_DIR / f"run_{ts}.jsonl"
        self.session_start = time.time()

    def _write(self, record: Dict):
        record["timestamp"] = datetime.now().isoformat()
        record["elapsed_s"] = round(time.time() - self.session_start, 2)
        with open(self.log_path, "a") as f:
            f.write(json.dumps(record) + "\n")

    def log_query(self, query: str):
        self._write({"event": "query", "query": query})

    def log_decision(self, agent: str, query: str, decision: Any):
        self._write({"event": "decision", "agent": agent, "query": query, "decision": decision})

    def log_retrieval(self, sub_queries: List, docs: List, sql: Dict):
        self._write({
            "event": "retrieval",
            "sub_queries": sub_queries,
            "doc_count": len(docs),
            "top_sources": [d["metadata"] for d in docs[:5]],
            "sql_keys": list(sql.keys()),
        })

    def log_final(self, result: Dict):
        self._write({"event": "final_answer", **result})