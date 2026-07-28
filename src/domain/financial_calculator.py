from __future__ import annotations

import copy

from src.domain.models import Expense, Goal, JointSimulationResult


class FinancialCalculator:
    """Pure domain service: all financial calculations live here."""

    def calculate_monthly_cost(
        self,
        fixed_costs: list[float],
        periodic_costs: list[dict[str, float]],
    ) -> float:
        """Compute total monthly cost from fixed + amortised periodic expenses."""
        total_fixed = sum(fixed_costs)
        total_periodic = sum(
            (item.get("amount", 0.0) / item.get("months", 1.0))
            for item in periodic_costs
            if item.get("months", 1.0) > 0
        )
        return round(total_fixed + total_periodic, 2)

    def calculate_monthly_cost_from_expenses(
        self,
        expenses: list[Expense],
        scope_filter: str | None = "SHARED",
    ) -> float:
        """Compute total monthly cost from Expense domain models.

        If `scope_filter` is 'SHARED' ("O NOSSO"), only shared living expenses are included.
        If `scope_filter` is 'PERSONAL' ("O MEU / O SEU"), only personal allowance expenses are included.
        If `scope_filter` is None, all expenses are included.
        """
        filtered = [
            e for e in expenses if scope_filter is None or e.scope == scope_filter
        ]
        fixed = [e.value for e in filtered if e.type == "FIXED"]
        periodic = [
            {"amount": e.value, "months": e.frequency_months}
            for e in filtered
            if e.type == "PERIODIC"
        ]
        return self.calculate_monthly_cost(fixed, periodic)

    def simulate_joint_income(
        self,
        income1: float,
        income2: float,
        cost1: float,
        cost2: float,
        individual_allowance: float,
    ) -> JointSimulationResult:
        """Compare separated vs. joint income models.

        Detects *hidden deficits* where one partner cannot cover costs
        and still withdraw their full allowance.
        """
        # --- Separated scenario (each on their own) ---
        disposable1 = income1 - cost1
        disposable2 = income2 - cost2

        real_allowance1 = min(individual_allowance, max(0.0, disposable1))
        real_allowance2 = min(individual_allowance, max(0.0, disposable2))
        allowance_separated = real_allowance1 + real_allowance2

        contribution1 = max(0.0, disposable1 - individual_allowance)
        contribution2 = max(0.0, disposable2 - individual_allowance)
        power_separated = contribution1 + contribution2

        # --- Joint scenario (strong covers weak) ---
        total_income = income1 + income2
        total_cost = cost1 + cost2
        surplus = total_income - total_cost

        allowance_joint = min(individual_allowance * 2, max(0.0, surplus))
        power_joint = max(0.0, surplus - (individual_allowance * 2))

        return JointSimulationResult(
            power_separated=round(power_separated, 2),
            power_joint=round(power_joint, 2),
            allowance_separated=round(allowance_separated, 2),
            allowance_joint=round(allowance_joint, 2),
            deficit_rescued=round(allowance_joint - allowance_separated, 2),
        )

    def calculate_emergency_fund(
        self, monthly_cost: float, multiplier: int = 9
    ) -> float:
        """Target value for the peace reserve."""
        return round(monthly_cost * multiplier, 2)

    def waterfall_allocation(
        self, goals: list[Goal], amount: float
    ) -> list[Goal]:
        """Distribute `amount` across goals in strict priority order.

        Priority 1 (Reserva de Paz) is always filled first.
        """
        if not goals or amount <= 0:
            return goals

        allocated = copy.deepcopy(goals)
        allocated.sort(key=lambda g: g.priority)

        balance = amount
        for goal in allocated:
            if balance <= 0:
                break
            shortfall = goal.target_value - goal.current_value
            if shortfall > 0:
                fill = min(balance, shortfall)
                goal.current_value += fill
                balance -= fill

        return allocated
