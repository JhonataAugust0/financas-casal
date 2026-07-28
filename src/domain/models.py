from __future__ import annotations

from dataclasses import dataclass


@dataclass
class User:
    id: str
    name: str
    income: float = 0.0
    multiplier: int = 9
    allowance: float = 500.0


@dataclass
class Expense:
    id: int
    user_id: str
    name: str
    type: str  # 'FIXED' or 'PERIODIC'
    value: float
    frequency_months: int = 1
    scope: str = "SHARED"  # 'SHARED' ("O NOSSO") or 'PERSONAL' ("O MEU / O SEU")


@dataclass
class Goal:
    id: int
    name: str
    category: str
    subcategory: str
    target_value: float
    current_value: float = 0.0
    priority: int = 1
    link: str = ""


@dataclass
class JointSimulationResult:
    """Result of the joint income simulation (Ganha ou Perde)."""

    power_separated: float
    power_joint: float
    allowance_separated: float
    allowance_joint: float
    deficit_rescued: float  # The hidden benefit of joining finances


@dataclass
class MonthlyRealized:
    """Actual spending for a budgeted expense in a specific month."""

    id: int
    expense_id: int       # FK → Expense
    month_year: str       # 'YYYY-MM'
    budgeted_value: float  # Budget snapshot at time of recording
    actual_value: float   # What was actually paid


@dataclass
class GoalContribution:
    """Record of actual contribution towards a goal in a specific month."""

    id: int
    goal_id: int          # FK → Goal
    month_year: str       # 'YYYY-MM'
    planned_amount: float  # What the cascade suggested
    actual_amount: float  # What was actually contributed
