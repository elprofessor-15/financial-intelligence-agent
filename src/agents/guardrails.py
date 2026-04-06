"""
src/agents/guardrails.py
Detects and blocks harmful, illegal, or off-topic queries before they reach the agent pipeline.
"""

BLOCKED_PATTERNS = [
    # Market manipulation
    "manipulate", "manipulation", "pump and dump", "pump-and-dump",
    "short squeeze", "insider trading", "front running", "front-running",
    "wash trading", "spoofing", "layering", "cornering the market",
    # Illegal activity
    "illegally", "illegal", "fraud", "money laundering", "launder",
    "evade taxes", "tax evasion", "bribe", "embezzle", "embezzlement",
    "ponzi", "pyramid scheme", "hack", "exploit", "steal",
    # Harmful intent
    "make huge profit illegally", "bypass sec", "avoid regulation",
    "cheat", "deceive investors", "mislead shareholders",
]

ALLOWED_FINANCIAL_KEYWORDS = [
    "revenue", "risk", "filing", "10-k", "sec", "earnings", "stock",
    "price", "trend", "compare", "analysis", "volatility", "sector",
    "business", "overview", "md&a", "management", "annual report",
    "quarterly", "fiscal", "balance sheet", "income statement",
    "cash flow", "dividend", "market cap", "pe ratio", "growth",
    "forecast", "outlook", "strategy", "operations", "segment",
]


def check_query(query: str) -> dict:
    """
    Returns a dict with:
      - allowed: bool
      - reason: str (if blocked)
    """
    q_lower = query.lower()

    # Check blocked patterns
    for pattern in BLOCKED_PATTERNS:
        if pattern in q_lower:
            return {
                "allowed": False,
                "reason": f"This query appears to ask about potentially illegal or unethical financial activity ('{pattern}'). "
                          "This system is designed for legitimate financial research and analysis only. "
                          "Please ask about company filings, revenue trends, risk factors, stock performance, or business analysis."
            }

    # Check if query is way off topic (no financial keywords at all and very short)
    has_financial_context = any(kw in q_lower for kw in ALLOWED_FINANCIAL_KEYWORDS)
    query_words = len(query.split())

    # Very short queries with no financial context
    if query_words < 3:
        return {
            "allowed": False,
            "reason": "Query is too short. Please provide a detailed financial question, for example: 'Compare revenue trends for AAPL and MSFT from 2021 to 2023'."
        }

    return {"allowed": True, "reason": ""}