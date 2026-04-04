from typing import Dict, Any, List
from src.retrieval.hybrid_retriever import HybridRetriever
from src.observability.logger import AgentLogger


class RetrieverAgent:
    def __init__(self, retriever: HybridRetriever, logger: AgentLogger):
        self.retriever = retriever
        self.logger = logger

    def retrieve(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        all_docs = []
        sql_results = {}

        filters = {}
        if plan.get("tickers"):
            filters["ticker"] = plan["tickers"]

        for sub_query in plan.get("sub_queries", []):
            docs = self.retriever.hybrid_search(sub_query, k=8, filters=filters)
            all_docs.extend(docs)

        # deduplicate by text prefix
        seen = set()
        unique_docs = []
        for doc in all_docs:
            key = doc["text"][:80]
            if key not in seen:
                seen.add(key)
                unique_docs.append(doc)

        for agg in plan.get("aggregations_needed", []):
            sql_results[agg] = self.retriever.sql_aggregate(
                agg, plan.get("tickers")
            )

        self.logger.log_retrieval(
            plan.get("sub_queries", []), unique_docs, sql_results
        )

        return {
            "documents": unique_docs[:20],
            "sql_results": sql_results,
            "doc_count": len(unique_docs),
        }