"""Cost guard — $10 USD per month per user."""
import time
import logging
from collections import defaultdict

from fastapi import HTTPException

from app.config import settings

logger = logging.getLogger(__name__)

# In-memory monthly spending tracker
# NOTE: For true statelessness with multiple instances, use Redis.
_monthly_cost: dict[str, float] = defaultdict(float)
_cost_reset_month: dict[str, str] = {}


def _get_month_key() -> str:
    return time.strftime("%Y-%m")


def _reset_if_new_month(user_id: str):
    current_month = _get_month_key()
    if _cost_reset_month.get(user_id) != current_month:
        _monthly_cost[user_id] = 0.0
        _cost_reset_month[user_id] = current_month


def check_and_record_cost(user_id: str, input_tokens: int, output_tokens: int):
    """Check monthly budget and record cost. Raises 402 if exceeded."""
    _reset_if_new_month(user_id)

    # Pricing: $0.15 / 1M input tokens, $0.60 / 1M output tokens (GPT-4o-mini)
    cost = (input_tokens / 1_000_000) * 0.15 + (output_tokens / 1_000_000) * 0.60

    current = _monthly_cost[user_id]
    if current + cost > settings.monthly_budget_usd:
        logger.warning(f"Budget exceeded for user {user_id[:8]}...: ${current:.4f} + ${cost:.4f} > ${settings.monthly_budget_usd}")
        raise HTTPException(
            status_code=402,
            detail=f"Monthly budget exceeded: ${settings.monthly_budget_usd}/month. "
                   f"Used: ${current:.4f}, Requested: ${cost:.4f}",
        )

    _monthly_cost[user_id] += cost
    logger.info(f"Cost recorded for user {user_id[:8]}...: +${cost:.6f} (total: ${_monthly_cost[user_id]:.4f})")
    return cost


def get_monthly_spending(user_id: str) -> dict:
    """Get current monthly spending for a user."""
    _reset_if_new_month(user_id)
    return {
        "user_id": user_id,
        "month": _get_month_key(),
        "spent_usd": round(_monthly_cost[user_id], 4),
        "budget_usd": settings.monthly_budget_usd,
        "remaining_usd": round(settings.monthly_budget_usd - _monthly_cost[user_id], 4),
    }
