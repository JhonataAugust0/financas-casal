"""Streamlit entrypoint — clean orchestrator with dependency injection."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure project root is in sys.path when running via streamlit run src/ui/main.py
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from src.domain.financial_calculator import FinancialCalculator
from src.domain.models import Expense
from src.ports.repository import FinancialRepository
from src.ui.styles import inject_custom_css
from src.ui.tabs.metas import render_metas_tab
from src.ui.tabs.orcamento import render_orcamento_tab
from src.ui.tabs.resumo import render_resumo_tab
from src.ui.tabs.simulador import render_simulador_tab


def _resolve_repository() -> FinancialRepository:
    """Factory: pick the data adapter based on environment config."""
    adapter = os.environ.get("ADAPTER", "sqlite").lower()
    if adapter == "supabase":
        from src.adapters.supabase_repository import SupabaseRepository
        return SupabaseRepository()
    from src.adapters.sqlite_repository import SQLiteRepository
    return SQLiteRepository()


def _compute_monthly_cost(
    calc: FinancialCalculator, expenses: list[Expense]
) -> float:
    """Derive monthly cost from a list of expenses."""
    fixed = [e.value for e in expenses if e.type == "FIXED"]
    periodic = [
        {"amount": e.value, "months": e.frequency_months}
        for e in expenses
        if e.type == "PERIODIC"
    ]
    return calc.calculate_monthly_cost(fixed, periodic)


def main() -> None:
    """Application entry point."""
    st.set_page_config(page_title="Finanças em Parceria", layout="centered")
    inject_custom_css()

    repo = _resolve_repository()
    calc = FinancialCalculator()

    st.title("🌱 Nossa Vida Financeira")

    tab_resumo, tab_orcamento, tab_metas, tab_simulador = st.tabs(
        ["📊 Resumo", "💰 Orçamento", "🎯 Metas", "⚖️ Modelos de Gestão de Renda"]
    )

    # ── Shared data (fetched once) ──
    user_a = repo.get_user("A")
    user_b = repo.get_user("B")
    if user_a is None or user_b is None:
        st.error("Dados dos usuários não encontrados no banco de dados.")
        return

    expenses_a = repo.get_expenses("A")
    expenses_b = repo.get_expenses("B")
    cost_a = _compute_monthly_cost(calc, expenses_a)
    cost_b = _compute_monthly_cost(calc, expenses_b)

    # ── Delegate to tabs ──
    with tab_resumo:
        render_resumo_tab(calc, user_a, user_b, expenses_a, expenses_b, cost_a, cost_b)

    with tab_orcamento:
        render_orcamento_tab(repo, user_a, user_b)

    with tab_metas:
        render_metas_tab(repo, calc, user_a, user_b, cost_a, cost_b)

    with tab_simulador:
        render_simulador_tab(calc, user_a, user_b, cost_a, cost_b)


if __name__ == "__main__":
    main()
