from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.models import Expense, Goal, User


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
    ) -> None:
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
