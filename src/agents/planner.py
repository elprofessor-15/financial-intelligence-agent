import json
from cerebras.cloud.sdk import Cerebras
from src.observability.logger import AgentLogger


class PlannerAgent:
    def __init__(self, logger: AgentLogger):
        self.client = Cerebras()
        self.logger = logger

    def plan(self, query: str) -> dict:
        response = self.client.chat.completions.create(
            model="llama-3.1-8b",
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
Return only valid JSON. No markdown. No explanation."""
                },
                {"role": "user", "content": query},
            ],
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()
        plan = json.loads(raw)
        self.logger.log_decision("planner", query, plan)
        return plan