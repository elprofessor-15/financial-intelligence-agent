"""
src/agents/planner.py
Query decomposition agent with robust JSON parsing and fallback.
"""

import json
from cerebras.cloud.sdk import Cerebras
from src.observability.logger import AgentLogger


FALLBACK_PLAN = {
    "sub_queries": [],
    "tickers": [],
    "sections_needed": ["risk_factors", "revenue", "business_overview", "md_and_a"],
    "aggregations_needed": [],
    "reasoning_type": "summary",
    "complexity": "simple",
}


class PlannerAgent:
    def __init__(self, logger: AgentLogger):
        self.client = Cerebras()
        self.logger = logger

    def plan(self, query: str) -> dict:
        try:
            response = self.client.chat.completions.create(
                model="llama3.1-8b",
                max_tokens=1000,
                messages=[
                    {
                        "role": "system",
                        "content": """You are a financial intelligence planner. Given a user query about companies,
stocks, or financial filings, decompose it into a structured retrieval and analysis plan.

Respond ONLY with a JSON object with these fields:
{
  "sub_queries": ["specific question 1", "specific question 2"],
  "tickers": ["AAPL", "MSFT"],
  "sections_needed": ["risk_factors", "revenue", "business_overview", "md_and_a"],
  "aggregations_needed": ["price_comparison", "volatility"],
  "reasoning_type": "comparison|trend|risk|summary",
  "complexity": "simple|multi-hop|aggregation"
}
Return only valid JSON. No markdown. No explanation. No extra text.""",
                    },
                    {"role": "user", "content": query},
                ],
            )

            raw = response.choices[0].message.content.strip()

            # Strip markdown fences if present
            if "```" in raw:
                parts = raw.split("```")
                for part in parts:
                    part = part.strip()
                    if part.startswith("json"):
                        part = part[4:].strip()
                    if part.startswith("{"):
                        raw = part
                        break

            # Find JSON object boundaries
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start != -1 and end > start:
                raw = raw[start:end]

            if not raw:
                raise ValueError("Empty response from planner")

            plan = json.loads(raw)

            # Ensure all required keys exist
            for key, default in FALLBACK_PLAN.items():
                if key not in plan:
                    plan[key] = default

            # Ensure sub_queries has the original query as fallback
            if not plan.get("sub_queries"):
                plan["sub_queries"] = [query]

            self.logger.log_decision("planner", query, plan)
            return plan

        except Exception as e:
            # Graceful fallback: use the original query as the single sub-query
            fallback = {**FALLBACK_PLAN, "sub_queries": [query]}
            self.logger.log_decision("planner", query, {"fallback": True, "error": str(e), "plan": fallback})
            return fallback