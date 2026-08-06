from __future__ import annotations

import copy
import math
from datetime import date, timedelta

from src.domain.models import Expense, Goal, GoalContribution, JointSimulationResult, MonthlyRealized


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

    # ── NEW: Budget Variance Analysis ─────────────────────────────

    def calculate_budget_variance(
        self, realized_list: list[MonthlyRealized]
    ) -> dict:
        """Analyse budget vs actual spending for a given month."""
        if not realized_list:
            return {
                "total_budgeted": 0.0,
                "total_actual": 0.0,
                "variance": 0.0,
                "variance_pct": 0.0,
                "items": [],
            }

        total_budgeted = sum(r.budgeted_value for r in realized_list)
        total_actual = sum(r.actual_value for r in realized_list)
        variance = round(total_budgeted - total_actual, 2)
        variance_pct = round((variance / total_budgeted) * 100, 2) if total_budgeted > 0 else 0.0

        items = []
        for r in realized_list:
            item_var = round(r.budgeted_value - r.actual_value, 2)
            items.append(
                {
                    "expense_id": r.expense_id,
                    "budgeted": r.budgeted_value,
                    "actual": r.actual_value,
                    "variance": item_var,
                }
            )

        items.sort(key=lambda x: abs(x["variance"]), reverse=True)

        return {
            "total_budgeted": round(total_budgeted, 2),
            "total_actual": round(total_actual, 2),
            "variance": variance,
            "variance_pct": variance_pct,
            "items": items,
        }

    # ── NEW: Goal Timeline Projection ─────────────────────────────

    def project_goal_timelines(
        self,
        goals: list[Goal],
        avg_monthly_contribution: float,
    ) -> list[dict]:
        """Project completion dates for goals using cascade logic and real avg contribution."""
        if not goals:
            return []

        sorted_goals = sorted(goals, key=lambda g: g.priority)
        today = date.today()
        results = []

        cumulative_months = 0.0

        for goal in sorted_goals:
            remaining = max(0.0, goal.target_value - goal.current_value)

            if remaining <= 0:
                results.append(
                    {
                        "goal_id": goal.id,
                        "goal_name": goal.name,
                        "priority": goal.priority,
                        "remaining": 0.0,
                        "estimated_months": 0,
                        "estimated_date": "—",
                        "status": "CONCLUÍDA",
                    }
                )
                continue

            if avg_monthly_contribution <= 0:
                results.append(
                    {
                        "goal_id": goal.id,
                        "goal_name": goal.name,
                        "priority": goal.priority,
                        "remaining": round(remaining, 2),
                        "estimated_months": -1,
                        "estimated_date": "—",
                        "status": "SEM APORTE",
                    }
                )
                continue

            months_for_this = remaining / avg_monthly_contribution
            cumulative_months += months_for_this
            total_months_ceil = math.ceil(cumulative_months)

            projected_date = today + timedelta(days=total_months_ceil * 30)
            date_str = projected_date.strftime("%m/%Y")

            results.append(
                {
                    "goal_id": goal.id,
                    "goal_name": goal.name,
                    "priority": goal.priority,
                    "remaining": round(remaining, 2),
                    "estimated_months": total_months_ceil,
                    "estimated_date": date_str,
                    "status": "EM ANDAMENTO",
                }
            )

        return results

    # ── NEW: Couple Impact Metrics ────────────────────────────────

    def calculate_couple_impact_metrics(
        self,
        goals: list[Goal],
        contributions: list[GoalContribution],
        deficit_rescued: float = 0.0,
    ) -> dict:
        """Calculate couple impact metrics:
        - reserve_current & reserve_target (% of safety reserve built)
        - goals_completion_pct (total accumulated % of all goals)
        - total_joint_benefit (hidden deficit rescued + accumulated savings)
        """
        safety_goals = [g for g in goals if g.priority == 1 or g.category == "🛡️ Segurança"]
        reserve_current = sum(g.current_value for g in safety_goals)
        reserve_target = sum(g.target_value for g in safety_goals)
        reserve_pct = round((reserve_current / reserve_target * 100), 1) if reserve_target > 0 else 0.0

        total_target = sum(g.target_value for g in goals)
        total_current = sum(g.current_value for g in goals)
        goals_pct = round((total_current / total_target * 100), 1) if total_target > 0 else 0.0

        total_contributions = sum(c.actual_amount for c in contributions)

        return {
            "reserve_current": round(reserve_current, 2),
            "reserve_target": round(reserve_target, 2),
            "reserve_pct": reserve_pct,
            "goals_pct": goals_pct,
            "total_contributions": round(total_contributions, 2),
            "total_current_wealth": round(total_current, 2),
            "joint_benefit": round(deficit_rescued, 2),
        }

    # ── What-If Simulator ─────────────────────────────────────────

    def simulate_what_if(
        self,
        goals: list[Goal],
        current_avg: float,
        extra_amount: float,
    ) -> list[dict]:
        """Simulate goal timelines with an extra monthly contribution.

        Returns a list of dicts per goal with:
        - goal_name, current_months, simulated_months, months_saved, simulated_date
        """
        if not goals or current_avg <= 0:
            return []

        current_timelines = self.project_goal_timelines(goals, current_avg)
        simulated_timelines = self.project_goal_timelines(
            goals, current_avg + extra_amount
        )

        results = []
        sim_map = {t["goal_id"]: t for t in simulated_timelines}

        for curr in current_timelines:
            sim = sim_map.get(curr["goal_id"])
            if not sim or curr["status"] == "CONCLUÍDA":
                continue

            curr_months = curr["estimated_months"] if curr["estimated_months"] > 0 else 0
            sim_months = sim["estimated_months"] if sim["estimated_months"] > 0 else 0
            saved = max(0, curr_months - sim_months)

            results.append({
                "goal_id": curr["goal_id"],
                "goal_name": curr["goal_name"],
                "current_months": curr_months,
                "current_date": curr["estimated_date"],
                "simulated_months": sim_months,
                "simulated_date": sim["estimated_date"],
                "months_saved": saved,
            })

        return results

    # ── Financial Health Thermometer ──────────────────────────────

    def calculate_financial_health(
        self,
        total_income: float,
        shared_cost: float,
        recent_actuals: list[float] | None = None,
        older_actuals: list[float] | None = None,
    ) -> dict:
        """Diagnose financial health of the couple's budget.

        Args:
            total_income: Combined income of both partners.
            shared_cost: Total monthly shared (Bolo Central) cost.
            recent_actuals: Sum of actual Bolo Central spending for the last 3 months.
            older_actuals: Sum of actual Bolo Central spending for the 3 months before that.

        Returns:
            commitment_pct, commitment_status, overload_trend, overload_pct
        """
        commitment_pct = round(
            (shared_cost / total_income * 100), 1
        ) if total_income > 0 else 0.0

        if commitment_pct < 50:
            commitment_status = "🟢 Saudável"
        elif commitment_pct < 65:
            commitment_status = "🟡 Atenção"
        else:
            commitment_status = "🔴 Crítico"

        # Overload trend: compare recent 3-month average vs older 3-month average
        overload_trend = "neutral"
        overload_pct = 0.0

        if recent_actuals and older_actuals:
            recent_avg = sum(recent_actuals) / len(recent_actuals) if recent_actuals else 0
            older_avg = sum(older_actuals) / len(older_actuals) if older_actuals else 0

            if older_avg > 0:
                overload_pct = round(((recent_avg - older_avg) / older_avg) * 100, 1)
                if overload_pct > 5:
                    overload_trend = "rising"
                elif overload_pct < -5:
                    overload_trend = "falling"
                else:
                    overload_trend = "stable"

        return {
            "commitment_pct": commitment_pct,
            "commitment_status": commitment_status,
            "overload_trend": overload_trend,
            "overload_pct": overload_pct,
        }

    # ── Moving Average for Variable Expenses ─────────────────────

    def calculate_moving_average(
        self,
        realized_records: list[MonthlyRealized],
        expense_id: int,
        fallback_value: float,
        min_months: int = 2,
    ) -> tuple[float, bool]:
        """Calculate the moving average of actual spending for a given expense.

        Args:
            realized_records: Historical realized records for this expense.
            expense_id: The expense ID to filter for.
            fallback_value: The registered expense value to use if insufficient history.
            min_months: Minimum number of months of data required to activate averaging.

        Returns:
            (average_value, is_moving_average_active)
        """
        relevant = [
            r for r in realized_records
            if r.expense_id == expense_id and r.actual_value > 0
        ]

        if len(relevant) < min_months:
            return fallback_value, False

        avg = sum(r.actual_value for r in relevant) / len(relevant)
        return round(avg, 2), True
