from __future__ import annotations

import os
from datetime import date, timedelta

from supabase import Client, create_client

from src.domain.models import Expense, Goal, GoalContribution, MonthlyRealized, MonthlySnapshot, User
from src.ports.repository import FinancialRepository


class SupabaseRepository(FinancialRepository):
    """Supabase/PostgreSQL adapter – production data layer."""

    def __init__(
        self,
        url: str | None = None,
        key: str | None = None,
    ) -> None:
        supabase_url = url or os.environ.get("SUPABASE_URL", "")
        supabase_key = key or os.environ.get("SUPABASE_KEY", "")
        if not supabase_url or not supabase_key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_KEY must be provided or set in environment."
            )
        self._client: Client = create_client(supabase_url, supabase_key)

    # ── helpers ────────────────────────────────────────────────────
    def _row_to_user(self, row: dict) -> User:
        return User(
            id=row["id"],
            name=row["name"],
            income=float(row.get("income", 0.0)),
            multiplier=int(row.get("emergency_multiplier", 9)),
            allowance=float(row.get("allowance", 500.0) or 500.0),
        )

    def _row_to_expense(self, row: dict) -> Expense:
        return Expense(
            id=int(row["id"]),
            user_id=row["user_id"],
            name=row["name"],
            type=row["type"],
            value=float(row["value"]),
            frequency_months=int(row.get("frequency_months", 1)),
            scope=row.get("scope") or "SHARED",
        )

    def _row_to_goal(self, row: dict) -> Goal:
        return Goal(
            id=int(row["id"]),
            name=row["name"],
            category=row["category"],
            subcategory=row.get("subcategory") or "Geral",
            target_value=float(row["target_value"]),
            current_value=float(row.get("current_value", 0.0)),
            priority=int(row["priority"]),
            link=row.get("link") or "",
        )

    def _row_to_monthly_realized(self, row: dict) -> MonthlyRealized:
        return MonthlyRealized(
            id=int(row["id"]),
            expense_id=int(row["expense_id"]),
            month_year=row["month_year"],
            budgeted_value=float(row["budgeted_value"]),
            actual_value=float(row["actual_value"]),
        )

    def _row_to_goal_contribution(self, row: dict) -> GoalContribution:
        return GoalContribution(
            id=int(row["id"]),
            goal_id=int(row["goal_id"]),
            month_year=row["month_year"],
            planned_amount=float(row.get("planned_amount", 0.0)),
            actual_amount=float(row["actual_amount"]),
        )

    def _row_to_monthly_snapshot(self, row: dict) -> MonthlySnapshot:
        return MonthlySnapshot(
            id=int(row["id"]),
            month_year=row["month_year"],
            reserve_value=float(row.get("reserve_value", 0.0)),
            goals_value=float(row.get("goals_value", 0.0)),
            total_wealth=float(row.get("total_wealth", 0.0)),
        )

    # ── Users ──────────────────────────────────────────────────────
    def get_user(self, user_id: str) -> User | None:
        response = (
            self._client.table("users")
            .select("*")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )
        if not response or not response.data:
            return None
        return self._row_to_user(response.data[0])

    def update_user_income(self, user_id: str, income: float) -> None:
        self._client.table("users").update({"income": income}).eq(
            "id", user_id
        ).execute()

    def update_user_allowance(self, user_id: str, allowance: float) -> None:
        self._client.table("users").update({"allowance": allowance}).eq(
            "id", user_id
        ).execute()

    def update_user_multiplier(self, user_id: str, multiplier: int) -> None:
        self._client.table("users").update(
            {"emergency_multiplier": multiplier}
        ).eq("id", user_id).execute()

    # ── Expenses ───────────────────────────────────────────────────
    def get_expenses(self, user_id: str) -> list[Expense]:
        response = (
            self._client.table("expenses")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )
        data = response.data if (response and response.data) else []
        return [self._row_to_expense(r) for r in data]

    def add_expense(
        self,
        user_id: str,
        name: str,
        expense_type: str,
        value: float,
        frequency_months: int,
        scope: str = "SHARED",
    ) -> None:
        self._client.table("expenses").insert(
            {
                "user_id": user_id,
                "name": name,
                "type": expense_type,
                "value": value,
                "frequency_months": frequency_months,
                "scope": scope,
            }
        ).execute()

    def update_expense(
        self,
        expense_id: int,
        name: str,
        expense_type: str,
        value: float,
        frequency_months: int,
        scope: str = "SHARED",
    ) -> None:
        self._client.table("expenses").update(
            {
                "name": name,
                "type": expense_type,
                "value": value,
                "frequency_months": frequency_months,
                "scope": scope,
            }
        ).eq("id", expense_id).execute()

    def delete_expense(self, expense_id: int) -> None:
        self._client.table("expenses").delete().eq("id", expense_id).execute()

    # ── Goals ──────────────────────────────────────────────────────
    def get_goals(self) -> list[Goal]:
        response = self._client.table("goals").select("*").execute()
        data = response.data if (response and response.data) else []
        return [self._row_to_goal(r) for r in data]

    def update_goals(self, goals: list[Goal]) -> None:
        for goal in goals:
            self._client.table("goals").update(
                {"current_value": goal.current_value}
            ).eq("id", goal.id).execute()

    def add_goal(
        self,
        name: str,
        category: str,
        subcategory: str,
        target: float,
        priority: int,
        link: str = "",
    ) -> None:
        self._client.table("goals").insert(
            {
                "name": name,
                "category": category,
                "subcategory": subcategory,
                "target_value": target,
                "current_value": 0.0,
                "priority": priority,
                "link": link,
            }
        ).execute()

    def update_goal_details(
        self, goal_id: int, name: str, target: float, priority: int, link: str
    ) -> None:
        self._client.table("goals").update(
            {
                "name": name,
                "target_value": target,
                "priority": priority,
                "link": link,
            }
        ).eq("id", goal_id).execute()

    def delete_goal(self, goal_id: int) -> None:
        self._client.table("goals").delete().eq("id", goal_id).execute()

    def delete_subcategory(self, category: str, subcategory: str) -> None:
        self._client.table("goals").delete().eq("category", category).eq(
            "subcategory", subcategory
        ).execute()

    def sync_reserva_paz(
        self, target_value: float, is_maintenance: bool
    ) -> None:
        subcategory_name = (
            "Fundo de Manutenção"
            if is_maintenance
            else "Fundo de Sobrevivência"
        )
        item_name = (
            "Reserva de Manutenção"
            if is_maintenance
            else "Reserva de Sobrevivência"
        )

        response = (
            self._client.table("goals")
            .select("id")
            .eq("category", "🛡️ Segurança")
            .limit(1)
            .execute()
        )

        if response and response.data and len(response.data) > 0:
            goal_id = response.data[0]["id"]
            self._client.table("goals").update(
                {
                    "name": item_name,
                    "subcategory": subcategory_name,
                    "target_value": target_value,
                    "priority": 1,
                }
            ).eq("id", goal_id).execute()
        else:
            self._client.table("goals").insert(
                {
                    "name": item_name,
                    "category": "🛡️ Segurança",
                    "subcategory": subcategory_name,
                    "target_value": target_value,
                    "current_value": 0.0,
                    "priority": 1,
                    "link": "",
                }
            ).execute()

    # ── Monthly Realized (Orçado vs. Realizado) ───────────────────
    def get_monthly_realized(self, month_year: str) -> list[MonthlyRealized]:
        response = (
            self._client.table("monthly_realized")
            .select("*")
            .eq("month_year", month_year)
            .execute()
        )
        data = response.data if (response and response.data) else []
        return [self._row_to_monthly_realized(r) for r in data]

    def upsert_monthly_realized(
        self, expense_id: int, month_year: str, budgeted: float, actual: float
    ) -> None:
        self._client.table("monthly_realized").upsert(
            {
                "expense_id": expense_id,
                "month_year": month_year,
                "budgeted_value": budgeted,
                "actual_value": actual,
            },
            on_conflict="expense_id,month_year",
        ).execute()

    # ── Goal Contributions (Aportes Reais) ────────────────────────
    def get_goal_contributions(self, goal_id: int) -> list[GoalContribution]:
        response = (
            self._client.table("goal_contributions")
            .select("*")
            .eq("goal_id", goal_id)
            .order("month_year", desc=True)
            .execute()
        )
        data = response.data if (response and response.data) else []
        return [self._row_to_goal_contribution(r) for r in data]

    def get_all_contributions(self, months: int = 6) -> list[GoalContribution]:
        cutoff = (date.today() - timedelta(days=months * 30)).strftime("%Y-%m")
        response = (
            self._client.table("goal_contributions")
            .select("*")
            .gte("month_year", cutoff)
            .order("month_year", desc=True)
            .execute()
        )
        data = response.data if (response and response.data) else []
        return [self._row_to_goal_contribution(r) for r in data]

    def add_goal_contribution(
        self, goal_id: int, month_year: str, planned: float, actual: float
    ) -> None:
        response = (
            self._client.table("goal_contributions")
            .select("id,planned_amount,actual_amount")
            .eq("goal_id", goal_id)
            .eq("month_year", month_year)
            .limit(1)
            .execute()
        )
        if response and response.data and len(response.data) > 0:
            existing = response.data[0]
            self._client.table("goal_contributions").update(
                {
                    "planned_amount": float(existing["planned_amount"]) + planned,
                    "actual_amount": float(existing["actual_amount"]) + actual,
                }
            ).eq("id", existing["id"]).execute()
        else:
            self._client.table("goal_contributions").insert(
                {
                    "goal_id": goal_id,
                    "month_year": month_year,
                    "planned_amount": planned,
                    "actual_amount": actual,
                }
            ).execute()

    def delete_goal_contribution(self, contribution_id: int) -> None:
        self._client.table("goal_contributions").delete().eq(
            "id", contribution_id
        ).execute()

    # ── Monthly Snapshots (Evolução Patrimonial) ──────────────────
    def save_monthly_snapshot(
        self, month_year: str, reserve_value: float, goals_value: float
    ) -> None:
        total_wealth = reserve_value + goals_value
        self._client.table("monthly_snapshots").upsert(
            {
                "month_year": month_year,
                "reserve_value": reserve_value,
                "goals_value": goals_value,
                "total_wealth": total_wealth,
            },
            on_conflict="month_year",
        ).execute()

    def get_wealth_snapshots(self, months: int = 12) -> list[MonthlySnapshot]:
        cutoff = (date.today() - timedelta(days=months * 30)).strftime("%Y-%m")
        response = (
            self._client.table("monthly_snapshots")
            .select("*")
            .gte("month_year", cutoff)
            .order("month_year")
            .execute()
        )
        data = response.data if (response and response.data) else []
        return [self._row_to_monthly_snapshot(r) for r in data]
