"""Tab: ⚖️ Simulador — joint income simulation (Ganha ou Perde)."""

from __future__ import annotations

import streamlit as st

from src.domain.financial_calculator import FinancialCalculator
from src.domain.models import User
from src.ui.components.charts import build_income_distribution_chart


def render_simulador_tab(
    calc: FinancialCalculator,
    user_a: User,
    user_b: User,
    cost_a: float,
    cost_b: float,
) -> None:
    """Render the complete ⚖️ Simulador tab."""
    st.subheader("Simulador de Junção de Rendas")

    current_allowance = user_a.allowance
    st.info(
        f"💡 Baseado no Custo de Vida Compartilhado (🏠 **O NOSSO**) e na mesada igualitária de "
        f"**R\\$ {current_allowance:.2f}** para cada um.\n\n"
        f"*Nota: Gastos pessoais (👤 **O MEU / O SEU**) saem da mesada individual e não inflam o Bolo Central.*"
    )

    # Run simulation
    result = calc.simulate_joint_income(
        income1=user_a.income,
        income2=user_b.income,
        cost1=cost_a,
        cost2=cost_b,
        individual_allowance=current_allowance,
    )

    delta_contribution = result.power_joint - result.power_separated

    # ── Deficit detection (reproducing original math exactly) ──
    disposable_a = user_a.income - cost_a
    disposable_b = user_b.income - cost_b

    real_allowance_a = min(current_allowance, max(0.0, disposable_a))
    real_allowance_b = min(current_allowance, max(0.0, disposable_b))
    total_allowance_separated = real_allowance_a + real_allowance_b

    joint_surplus = (user_a.income + user_b.income) - (cost_a + cost_b)
    total_allowance_joint = min(
        current_allowance * 2, max(0.0, joint_surplus)
    )

    deficit_rescued = total_allowance_joint - total_allowance_separated

    # ── Visual alerts (R\$ escaped to prevent LaTeX math rendering) ──
    if deficit_rescued > 0:
        st.error(
            f"⚠️ **Alerta de Déficit no Modelo Separado!** \n\n"
            f"Matematicamente, um de vocês não consegue pagar o próprio "
            f"custo de vida e tirar os R\\$ {current_allowance:.2f} de mesada "
            f"integral. O aporte de R\\$ {result.power_separated:.2f} do "
            f"cenário separado é uma ilusão que esconde um parceiro no "
            f"vermelho."
        )
        st.success(
            f"🤝 **O Benefício de Juntar:** A conta conjunta sacrifica "
            f"R\\$ {abs(delta_contribution):.2f} do aporte, mas **garante "
            f"R\\$ {deficit_rescued:.2f} a mais em mesada**, resgatando o "
            f"parceiro e garantindo o mesmo padrão de vida para ambos."
        )
    else:
        st.success(
            "⚖️ **Equilíbrio Perfeito:** Ambos conseguem pagar suas contas "
            "e tirar a mesada integral sem ficar no vermelho. Juntar ou "
            "separar as contas tem o mesmo peso financeiro matemático "
            "neste momento."
        )

    st.divider()

    # ── Side-by-side metrics ──
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.metric(
            "Poder de Aporte (JUNTO)",
            f"R$ {result.power_joint:.2f}",
            delta=round(delta_contribution, 2),
        )
    with col_m2:
        st.metric(
            "Mesada Total Garantida (JUNTO)",
            f"R$ {total_allowance_joint:.2f}",
            delta=round(deficit_rescued, 2),
        )

    st.caption(
        f"No modelo SEPARADO: Aporte de R\\$ {result.power_separated:.2f} "
        f"| Mesada Total Realizada de R\\$ {total_allowance_separated:.2f}"
    )

    # ── Stacked bar chart ──
    chart = build_income_distribution_chart(
        power_separated=result.power_separated,
        allowance_separated=total_allowance_separated,
        power_joint=result.power_joint,
        allowance_joint=total_allowance_joint,
        has_deficit=deficit_rescued > 0,
    )
    st.altair_chart(chart, use_container_width=True, theme=None)
