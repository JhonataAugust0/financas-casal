from __future__ import annotations

import sqlite3
from datetime import date, timedelta

from src.domain.models import Expense, Goal, GoalContribution, MonthlyRealized, User
from src.ports.repository import FinancialRepository


class SQLiteRepository(FinancialRepository):
    """SQLite adapter – used as fallback for local development and tests."""

    def __init__(self, db_path: str = "finance_mvp.db") -> None:
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        """Auto-migrate columns and tables if missing in local SQLite database."""
        cursor = self._conn.cursor()

        # Migrate expenses.scope column
        cursor.execute("PRAGMA table_info(expenses)")
        columns = [row["name"] for row in cursor.fetchall()]
        if "scope" not in columns:
            cursor.execute("ALTER TABLE expenses ADD COLUMN scope TEXT DEFAULT 'SHARED'")

        # Create monthly_realized table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS monthly_realized (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                expense_id INTEGER REFERENCES expenses(id) ON DELETE CASCADE,
                month_year TEXT NOT NULL,
                budgeted_value REAL NOT NULL,
                actual_value REAL NOT NULL,
                UNIQUE(expense_id, month_year)
            )
        """)

        # Create goal_contributions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS goal_contributions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id INTEGER REFERENCES goals(id) ON DELETE CASCADE,
                month_year TEXT NOT NULL,
                planned_amount REAL DEFAULT 0.0,
                actual_amount REAL NOT NULL,
                UNIQUE(goal_id, month_year)
            )
        """)

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

    # ── Monthly Realized (Orçado vs. Realizado) ───────────────────
    def get_monthly_realized(self, month_year: str) -> list[MonthlyRealized]:
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT * FROM monthly_realized WHERE month_year=?", (month_year,)
        )
        return [
            MonthlyRealized(
                id=int(row["id"]),
                expense_id=int(row["expense_id"]),
                month_year=row["month_year"],
                budgeted_value=float(row["budgeted_value"]),
                actual_value=float(row["actual_value"]),
            )
            for row in cursor.fetchall()
        ]

    def upsert_monthly_realized(
        self, expense_id: int, month_year: str, budgeted: float, actual: float
    ) -> None:
        self._conn.execute(
            """INSERT INTO monthly_realized (expense_id, month_year, budgeted_value, actual_value)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(expense_id, month_year)
               DO UPDATE SET budgeted_value=excluded.budgeted_value, actual_value=excluded.actual_value""",
            (expense_id, month_year, budgeted, actual),
        )
        self._conn.commit()

    # ── Goal Contributions (Aportes Reais) ────────────────────────
    def get_goal_contributions(self, goal_id: int) -> list[GoalContribution]:
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT * FROM goal_contributions WHERE goal_id=? ORDER BY month_year DESC",
            (goal_id,),
        )
        return [
            GoalContribution(
                id=int(row["id"]),
                goal_id=int(row["goal_id"]),
                month_year=row["month_year"],
                planned_amount=float(row["planned_amount"]),
                actual_amount=float(row["actual_amount"]),
            )
            for row in cursor.fetchall()
        ]

    def get_all_contributions(self, months: int = 6) -> list[GoalContribution]:
        cutoff = (date.today() - timedelta(days=months * 30)).strftime("%Y-%m")
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT * FROM goal_contributions WHERE month_year >= ? ORDER BY month_year DESC",
            (cutoff,),
        )
        return [
            GoalContribution(
                id=int(row["id"]),
                goal_id=int(row["goal_id"]),
                month_year=row["month_year"],
                planned_amount=float(row["planned_amount"]),
                actual_amount=float(row["actual_amount"]),
            )
            for row in cursor.fetchall()
        ]

    def add_goal_contribution(
        self, goal_id: int, month_year: str, planned: float, actual: float
    ) -> None:
        self._conn.execute(
            """INSERT INTO goal_contributions (goal_id, month_year, planned_amount, actual_amount)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(goal_id, month_year)
               DO UPDATE SET planned_amount=planned_amount + excluded.planned_amount,
                             actual_amount=actual_amount + excluded.actual_amount""",
            (goal_id, month_year, planned, actual),
        )
        self._conn.commit()

    def delete_goal_contribution(self, contribution_id: int) -> None:
        self._conn.execute(
            "DELETE FROM goal_contributions WHERE id=?", (contribution_id,)
        )
        self._conn.commit()
