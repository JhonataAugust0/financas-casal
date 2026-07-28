"""Tab: 📊 Resumo — partner financial transparency dashboard."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.domain.financial_calculator import FinancialCalculator
from src.domain.models import Expense, User
from src.ui.components.charts import build_reserve_comparison_chart


def _render_partner_summary(
    calc: FinancialCalculator,
    user: User,
    expenses: list[Expense],
    monthly_cost: float,
) -> None:
    """Render a single partner's financial summary card."""
    st.markdown(f"### 👤 {user.name}")
    st.metric("Renda Líquida", f"R$ {user.income:.2f}")
    st.metric("Custo de Vida", f"R$ {monthly_cost:.2f}")

    survival_reserve = calc.calculate_emergency_fund(
        monthly_cost, user.multiplier
    )
    maintenance_reserve = calc.calculate_emergency_fund(
        monthly_cost + user.allowance, user.multiplier
    )

    st.markdown(f"**🛡️ Reserva de Paz ({user.multiplier} meses)**")

    chart = build_reserve_comparison_chart(survival_reserve, maintenance_reserve)
    st.altair_chart(chart, use_container_width=True, theme=None)

    st.caption(
        f"**Sobrevivência:** R$ {survival_reserve:.2f} "
        f"| **Manutenção:** R$ {maintenance_reserve:.2f}"
    )

    with st.expander("📝 Composição de Custos"):
        if expenses:
            df = pd.DataFrame(
                [
                    {
                        "Item": e.name,
                        "R$": e.value,
                        "Tipo": "Mensal" if e.type == "FIXED" else "Periódica",
                        "Freq.": e.frequency_months,
                    }
                    for e in expenses
                ]
            )
            st.dataframe(df, hide_index=True, use_container_width=True)
        else:
            st.caption("Nenhum custo.")


def render_resumo_tab(
    calc: FinancialCalculator,
    user_a: User,
    user_b: User,
    expenses_a: list[Expense],
    expenses_b: list[Expense],
    cost_a: float,
    cost_b: float,
) -> None:
    """Render the complete 📊 Resumo tab."""
    st.subheader("Transparência Total")

    col_a, col_b = st.columns(2)
    with col_a:
        _render_partner_summary(calc, user_a, expenses_a, cost_a)
    with col_b:
        _render_partner_summary(calc, user_b, expenses_b, cost_b)
