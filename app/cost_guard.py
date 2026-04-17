"""
Cost guard module for VinFast Assistant
Tracks API usage costs and enforces budget limits
"""

import time
import os
from typing import Dict, Tuple


class CostGuard:
    def __init__(self):
        self.daily_budget = float(os.getenv("DAILY_BUDGET_USD", "5.0"))
        self.daily_cost = 0.0
        self.cost_reset_day = time.strftime("%Y-%m-%d")
        self.request_cost_usd = 0.001  # $0.001 per request (mock estimate)

    def check_budget(self) -> bool:
        """
        Check if current request would exceed daily budget
        Returns False if budget would be exceeded
        """
        self._reset_if_new_day()

        if self.daily_cost + self.request_cost_usd > self.daily_budget:
            return False

        return True

    def record_cost(self) -> None:
        """Record the cost of current request"""
        self._reset_if_new_day()
        self.daily_cost += self.request_cost_usd

    def get_budget_status(self) -> Dict:
        """Get current budget status"""
        self._reset_if_new_day()

        return {
            "daily_cost_usd": round(self.daily_cost, 4),
            "daily_budget_usd": self.daily_budget,
            "remaining_budget_usd": round(self.daily_budget - self.daily_cost, 4),
            "budget_used_percent": round(self.daily_cost / self.daily_budget * 100, 1)
            if self.daily_budget > 0
            else 0,
            "reset_day": self.cost_reset_day,
        }

    def _reset_if_new_day(self) -> None:
        """Reset daily cost if it's a new day"""
        today = time.strftime("%Y-%m-%d")
        if today != self.cost_reset_day:
            self.daily_cost = 0.0
            self.cost_reset_day = today


# Global cost guard instance
cost_guard = CostGuard()
