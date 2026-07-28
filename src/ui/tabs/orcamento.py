"""Tab: 💰 Orçamento — income, allowance, and expense management."""

from __future__ import annotations

import streamlit as st

from src.domain.models import User
from src.ports.repository import FinancialRepository


def render_orcamento_tab(
    repo: FinancialRepository,
    user_a: User,
    user_b: User,
) -> None:
    """Render the complete 💰 Orçamento tab."""
    st.subheader("💰 Definição de Orçamento e Renda")
    st.markdown("Defina quanto entra e o teto da mesada (igual para ambos).")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"#### {user_a.name}")
        new_income_a = st.number_input(
            "Renda Líquida (R$)",
            min_value=0.0,
            value=float(user_a.income),
            step=100.0,
            key="inc_a",
        )
        new_mult_a = st.number_input(
            "Meses de Reserva",
            min_value=1,
            max_value=36,
            value=int(user_a.multiplier),
            step=1,
            key="mult_a",
        )

    with col_b:
        st.markdown(f"#### {user_b.name}")
        new_income_b = st.number_input(
            "Renda Líquida (R$)",
            min_value=0.0,
            value=float(user_b.income),
            step=100.0,
            key="inc_b",
        )
        new_mult_b = st.number_input(
            "Meses de Reserva",
            min_value=1,
            max_value=36,
            value=int(user_b.multiplier),
            step=1,
            key="mult_b",
        )

    st.markdown("---")
    st.markdown("#### 💸 Mesada Igualitária")
    current_allowance = float(user_a.allowance)
    new_allowance = st.number_input(
        "Valor da Mesada (Para CADA UM retirar do caixa)",
        min_value=0.0,
        value=current_allowance,
        step=50.0,
    )

    if st.button("Salvar Orçamento e Configurações"):
        repo.update_user_income("A", new_income_a)
        repo.update_user_income("B", new_income_b)
        repo.update_user_multiplier("A", new_mult_a)
        repo.update_user_multiplier("B", new_mult_b)
        repo.update_user_allowance("A", new_allowance)
        repo.update_user_allowance("B", new_allowance)
        st.success("Configurações atualizadas com sucesso!")
        st.rerun()

    st.divider()

    with st.expander(
        "⚙️ Gerenciar Custo de Vida Autônomo (Despesas Fixas)", expanded=False
    ):
        owner = st.selectbox(
            "Quem é o dono desta despesa?", [user_a.name, user_b.name]
        )
        exp_name = st.text_input(
            "Nome da Despesa", placeholder="Ex: Aluguel, Farmácia"
        )
        exp_type = st.radio(
            "Tipo", ["Fixa (Mensal)", "Periódica (Anual/Semestral)"]
        )
        exp_value = st.number_input("Valor (R$)", min_value=0.0, step=10.0)
        frequency = (
            st.slider("Meses?", 2, 12, 12)
            if "Periódica" in str(exp_type)
            else 1
        )

        if st.button("Adicionar Despesa"):
            if exp_name and exp_value > 0:
                user_id = "A" if owner == user_a.name else "B"
                db_type = "FIXED" if "Fixa" in str(exp_type) else "PERIODIC"
                repo.add_expense(user_id, exp_name, db_type, exp_value, frequency)
                st.success("Despesa adicionada!")
                st.rerun()
