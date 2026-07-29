from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.models import Expense, Goal, GoalContribution, MonthlyRealized, MonthlySnapshot, User


class FinancialRepository(ABC):
    """Port: defines the contract for any data persistence adapter."""

    # ── Users ──────────────────────────────────────────────────────
    @abstractmethod
    def get_user(self, user_id: str) -> User | None:
        ...

    @abstractmethod
    def update_user_income(self, user_id: str, income: float) -> None:
        ...

    @abstractmethod
    def update_user_allowance(self, user_id: str, allowance: float) -> None:
        ...

    @abstractmethod
    def update_user_multiplier(self, user_id: str, multiplier: int) -> None:
        ...

    # ── Expenses ───────────────────────────────────────────────────
    @abstractmethod
    def get_expenses(self, user_id: str) -> list[Expense]:
        ...

    @abstractmethod
    def add_expense(
        self,
        user_id: str,
        name: str,
        expense_type: str,
        value: float,
        frequency_months: int,
        scope: str = "SHARED",
    ) -> None:
        ...

    @abstractmethod
    def update_expense(
        self,
        expense_id: int,
        name: str,
        expense_type: str,
        value: float,
        frequency_months: int,
        scope: str = "SHARED",
    ) -> None:
        ...

    @abstractmethod
    def delete_expense(self, expense_id: int) -> None:
        ...

    # ── Goals ──────────────────────────────────────────────────────
    @abstractmethod
    def get_goals(self) -> list[Goal]:
        ...

    @abstractmethod
    def update_goals(self, goals: list[Goal]) -> None:
        ...

    @abstractmethod
    def add_goal(
        self,
        name: str,
        category: str,
        subcategory: str,
        target: float,
        priority: int,
        link: str = "",
    ) -> None:
        ...

    @abstractmethod
    def update_goal_details(
        self, goal_id: int, name: str, target: float, priority: int, link: str
    ) -> None:
        ...

    @abstractmethod
    def delete_goal(self, goal_id: int) -> None:
        ...

    @abstractmethod
    def delete_subcategory(self, category: str, subcategory: str) -> None:
        ...

    @abstractmethod
    def sync_reserva_paz(
        self, target_value: float, is_maintenance: bool
    ) -> None:
        """Upsert the mandatory safety goal (🛡️ Segurança).

        When `is_maintenance` is True, the goal name/subcategory change
        to reflect 'Manutenção' mode; otherwise 'Sobrevivência'.
        Priority is always forced to 1.
        """
        ...

    # ── Monthly Realized (Orçado vs. Realizado) ───────────────────
    @abstractmethod
    def get_monthly_realized(self, month_year: str) -> list[MonthlyRealized]:
        """Get all realized expense records for a given month ('YYYY-MM')."""
        ...

    @abstractmethod
    def upsert_monthly_realized(
        self, expense_id: int, month_year: str, budgeted: float, actual: float
    ) -> None:
        """Insert or update a realized expense record for a given month."""
        ...

    # ── Goal Contributions (Aportes Reais) ────────────────────────
    @abstractmethod
    def get_goal_contributions(self, goal_id: int) -> list[GoalContribution]:
        """Get all contribution records for a specific goal."""
        ...

    @abstractmethod
    def get_all_contributions(self, months: int = 6) -> list[GoalContribution]:
        """Get contribution records across all goals for the last N months."""
        ...

    @abstractmethod
    def add_goal_contribution(
        self, goal_id: int, month_year: str, planned: float, actual: float
    ) -> None:
        """Record a contribution (planned vs actual) for a goal in a month."""
        ...

    @abstractmethod
    def delete_goal_contribution(self, contribution_id: int) -> None:
        """Delete a specific contribution record."""
        ...

    # ── Monthly Snapshots (Evolução Patrimonial) ──────────────────
    @abstractmethod
    def save_monthly_snapshot(
        self, month_year: str, reserve_value: float, goals_value: float
    ) -> None:
        """Upsert historical wealth snapshot for a given month ('YYYY-MM')."""
        ...

    @abstractmethod
    def get_wealth_snapshots(self, months: int = 12) -> list[MonthlySnapshot]:
        """Get historical wealth snapshots for the last N months."""
        ...
