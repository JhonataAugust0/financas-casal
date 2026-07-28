from __future__ import annotations

import sqlite3

from src.domain.models import Expense, Goal, User
from src.ports.repository import FinancialRepository


class SQLiteRepository(FinancialRepository):
    """SQLite adapter – used as fallback for local development and tests."""

    def __init__(self, db_path: str = "finance_mvp.db") -> None:
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        """Auto-migrate columns if missing in local SQLite database."""
        cursor = self._conn.cursor()
        cursor.execute("PRAGMA table_info(expenses)")
        columns = [row["name"] for row in cursor.fetchall()]
        if "scope" not in columns:
            cursor.execute("ALTER TABLE expenses ADD COLUMN scope TEXT DEFAULT 'SHARED'")
            self._conn.commit()

    # ── Users ──────────────────────────────────────────────────────
    def get_user(self, user_id: str) -> User | None:
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT id, name, income, emergency_multiplier, allowance FROM users WHERE id=?",
            (user_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return User(
            id=row["id"],
            name=row["name"],
            income=float(row["income"]),
            multiplier=int(row["emergency_multiplier"]),
            allowance=float(row["allowance"]) if row["allowance"] is not None else 500.0,
        )

    def update_user_income(self, user_id: str, income: float) -> None:
        self._conn.execute("UPDATE users SET income=? WHERE id=?", (income, user_id))
        self._conn.commit()

    def update_user_allowance(self, user_id: str, allowance: float) -> None:
        self._conn.execute("UPDATE users SET allowance=? WHERE id=?", (allowance, user_id))
        self._conn.commit()

    def update_user_multiplier(self, user_id: str, multiplier: int) -> None:
        self._conn.execute(
            "UPDATE users SET emergency_multiplier=? WHERE id=?", (multiplier, user_id)
        )
        self._conn.commit()

    # ── Expenses ───────────────────────────────────────────────────
    def get_expenses(self, user_id: str) -> list[Expense]:
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM expenses WHERE user_id=?", (user_id,))
        return [
            Expense(
                id=int(row["id"]),
                user_id=row["user_id"],
                name=row["name"],
                type=row["type"],
                value=float(row["value"]),
                frequency_months=int(row["frequency_months"]),
                scope=row["scope"] if ("scope" in row.keys() and row["scope"]) else "SHARED",
            )
            for row in cursor.fetchall()
        ]

    def add_expense(
        self,
        user_id: str,
        name: str,
        expense_type: str,
        value: float,
        frequency_months: int,
        scope: str = "SHARED",
    ) -> None:
        self._conn.execute(
            "INSERT INTO expenses (user_id, name, type, value, frequency_months, scope) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, name, expense_type, value, frequency_months, scope),
        )
        self._conn.commit()

    def update_expense(
        self,
        expense_id: int,
        name: str,
        expense_type: str,
        value: float,
        frequency_months: int,
        scope: str = "SHARED",
    ) -> None:
        self._conn.execute(
            "UPDATE expenses SET name=?, type=?, value=?, frequency_months=?, scope=? WHERE id=?",
            (name, expense_type, value, frequency_months, scope, expense_id),
        )
        self._conn.commit()

    def delete_expense(self, expense_id: int) -> None:
        self._conn.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
        self._conn.commit()

    # ── Goals ──────────────────────────────────────────────────────
    def get_goals(self) -> list[Goal]:
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM goals")
        return [
            Goal(
                id=int(row["id"]),
                name=row["name"],
                category=row["category"],
                subcategory=row["subcategory"] if row["subcategory"] else "Geral",
                target_value=float(row["target_value"]),
                current_value=float(row["current_value"]),
                priority=int(row["priority"]),
                link=row["link"] if row["link"] else "",
            )
            for row in cursor.fetchall()
        ]

    def update_goals(self, goals: list[Goal]) -> None:
        cursor = self._conn.cursor()
        for goal in goals:
            cursor.execute(
                "UPDATE goals SET current_value=? WHERE id=?",
                (goal.current_value, goal.id),
            )
        self._conn.commit()

    def add_goal(
        self,
        name: str,
        category: str,
        subcategory: str,
        target: float,
        priority: int,
        link: str = "",
    ) -> None:
        self._conn.execute(
            "INSERT INTO goals (name, category, subcategory, target_value, current_value, priority, link) VALUES (?, ?, ?, ?, 0.0, ?, ?)",
            (name, category, subcategory, target, priority, link),
        )
        self._conn.commit()

    def update_goal_details(
        self, goal_id: int, name: str, target: float, priority: int, link: str
    ) -> None:
        self._conn.execute(
            "UPDATE goals SET name=?, target_value=?, priority=?, link=? WHERE id=?",
            (name, target, priority, link, goal_id),
        )
        self._conn.commit()

    def delete_goal(self, goal_id: int) -> None:
        self._conn.execute("DELETE FROM goals WHERE id=?", (goal_id,))
        self._conn.commit()

    def delete_subcategory(self, category: str, subcategory: str) -> None:
        self._conn.execute(
            "DELETE FROM goals WHERE category=? AND subcategory=?",
            (category, subcategory),
        )
        self._conn.commit()

    def sync_reserva_paz(
        self, target_value: float, is_maintenance: bool
    ) -> None:
        """Upsert the mandatory 🛡️ Segurança goal.

        Renames and recalculates the safety reserve in real-time based
        on whether maintenance mode is active.
        """
        subcategory_name = (
            "Fundo de Manutenção" if is_maintenance else "Fundo de Sobrevivência"
        )
        item_name = (
            "Reserva de Manutenção" if is_maintenance else "Reserva de Sobrevivência"
        )

        cursor = self._conn.cursor()
        cursor.execute("SELECT id FROM goals WHERE category='🛡️ Segurança'")
        row = cursor.fetchone()

        if row:
            self._conn.execute(
                "UPDATE goals SET name=?, subcategory=?, target_value=?, priority=1 WHERE id=?",
                (item_name, subcategory_name, target_value, row["id"]),
            )
        else:
            self._conn.execute(
                "INSERT INTO goals (name, category, subcategory, target_value, current_value, priority, link) VALUES (?, '🛡️ Segurança', ?, ?, 0.0, 1, '')",
                (item_name, subcategory_name, target_value),
            )
        self._conn.commit()
