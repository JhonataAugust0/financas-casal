"""Tab: 📊 Resumo — partner financial transparency dashboard."""

from __future__ import annotations

import streamlit as st

from src.domain.financial_calculator import FinancialCalculator
from src.domain.models import Expense, User
from src.ports.repository import FinancialRepository
from src.ui.components.charts import build_reserve_comparison_chart


def _get_partner_emoji(user: User) -> str:
    """Return specific partner emoji based on name or ID."""
    name_lower = user.name.lower()
    if "docinho" in name_lower or user.id == "A":
        return "👩🏿"
    if "gracinha" in name_lower or user.id == "B":
        return "👨🏿"
    return "👤"


def _render_partner_summary(
    repo: FinancialRepository,
    calc: FinancialCalculator,
    user: User,
    expenses: list[Expense],
) -> None:
    """Render a single partner's financial summary card with cost management."""
    emoji = _get_partner_emoji(user)
    
    # ── Separate SHARED (O NOSSO) vs PERSONAL (O MEU) ──
    shared_cost = calc.calculate_monthly_cost_from_expenses(expenses, scope_filter="SHARED")
    personal_cost = calc.calculate_monthly_cost_from_expenses(expenses, scope_filter="PERSONAL")
    free_allowance = user.allowance - personal_cost

    st.markdown(f"### {emoji} {user.name}")
    st.metric("Renda Líquida", f"R$ {user.income:.2f}")
    st.metric("Custo de Vida (🏠 O NOSSO)", f"R$ {shared_cost:.2f}")
    
    # Allowance usage metric (R\$ escaped to prevent KaTeX inline math rendering in delta pill)
    st.metric(
        "Gastos da Mesada (👤 O MEU)",
        f"R$ {personal_cost:.2f}",
        delta=f"R\\$ {free_allowance:.2f} livre do limite de R\\$ {user.allowance:.2f}",
        delta_color="normal" if free_allowance >= 0 else "inverse",
    )

    survival_reserve = calc.calculate_emergency_fund(
        shared_cost, user.multiplier
    )
    maintenance_reserve = calc.calculate_emergency_fund(
        shared_cost + user.allowance, user.multiplier
    )

    st.markdown(f"**Reserva de Paz ({user.multiplier} meses)**")

    chart = build_reserve_comparison_chart(survival_reserve, maintenance_reserve)
    st.altair_chart(chart, use_container_width=True, theme=None)

    st.caption(
        f"**Sobrevivência:** R\\$ {survival_reserve:.2f} "
        f"| **Manutenção:** R\\$ {maintenance_reserve:.2f}"
    )

    with st.expander("📝 Composição de Custos"):
        if expenses:
            shared_items = [e for e in expenses if e.scope == "SHARED"]
            personal_items = [e for e in expenses if e.scope == "PERSONAL"]

            if shared_items:
                st.markdown("#### 🏠 O Nosso")
                for exp in shared_items:
                    _render_expense_row(repo, exp)

            if personal_items:
                if shared_items: st.markdown("---")
                st.markdown("#### 👤 O Meu")
                for exp in personal_items:
                    _render_expense_row(repo, exp)
        else:
            st.caption("Nenhum custo cadastrado.")

        st.write("")
        with st.popover(f"➕ Adicionar Custo para {user.name}", use_container_width=True):
            with st.form(f"add_exp_resumo_{user.id}", clear_on_submit=True):
                st.markdown(f"**Novo Custo ({user.name})**")
                a_name = st.text_input("Nome da Despesa", placeholder="Ex: Terapia, Farmácia, Higiene", key=f"aen_{user.id}")
                
                a_scope = st.radio(
                    "Quem Paga?",
                    [
                        "🏠 O Nosso (Bolo Central)",
                        "👤 O Meu (Mesada Individual)",
                    ],
                    key=f"aes_{user.id}",
                )
                a_type = st.radio("Tipo de Frequência", ["Fixa 📌", "Periódica 🗓️"], key=f"aet_{user.id}")
                a_val = st.number_input("Valor (R$)", min_value=0.0, step=10.0, key=f"aev_{user.id}")
                a_freq = st.number_input(
                    "Periodicidade em Meses",
                    min_value=1,
                    max_value=24,
                    value=12,
                    help="Ex: 12 = Anual, 6 = Semestral, 2 = Bimestral, 1 = Mensal.",
                    key=f"aef_{user.id}",
                )
                
                if st.form_submit_button("Adicionar") and a_name and a_val > 0:
                    is_fixed = "Fixa" in a_type
                    db_type = "FIXED" if is_fixed else "PERIODIC"
                    final_freq = 1 if is_fixed else int(a_freq)
                    db_scope = "SHARED" if "Nosso" in a_scope else "PERSONAL"
                    
                    repo.add_expense(user.id, a_name, db_type, a_val, final_freq, db_scope)
                    st.success("Despesa adicionada com sucesso!")
                    st.rerun()


def _render_expense_row(repo: FinancialRepository, exp: Expense) -> None:
    """Render a single expense row with its edit/delete controls."""
    c_info, c_edit = st.columns([0.82, 0.18])
    with c_info:
        type_str = "Mensal" if exp.type == "FIXED" else f"Periódica ({exp.frequency_months}m)"
        scope_tag = "🏠 NOSSO" if exp.scope == "SHARED" else "👤 MEU"
        st.markdown(
            f"**{exp.name}**: R$ {exp.value:.2f} "
            f"<span style='color: #7A6C68; font-size: 0.8rem;'>({type_str})</span> "
            f"<span style='background-color: #EAE0D5; color: #5C4A4D; padding: 2px 6px; border-radius: 4px; font-size: 0.75rem;'>{scope_tag}</span>",
            unsafe_allow_html=True,
        )
    with c_edit:
        with st.popover("⚙️"):
            with st.form(f"edit_exp_{exp.id}"):
                st.markdown("**Editar Custo**")
                e_name = st.text_input("Nome", value=exp.name, key=f"exn_{exp.id}")
                e_scope = st.radio(
                    "Quem Paga?",
                    [
                        "🏠 O Nosso (Bolo Central)",
                        "👤 O Meu (Mesada Individual)",
                    ],
                    index=0 if exp.scope == "SHARED" else 1,
                    key=f"exs_{exp.id}",
                )
                e_type = st.radio(
                    "Tipo de Frequência",
                    ["Fixa 📌", "Periódica 🗓️"],
                    index=0 if exp.type == "FIXED" else 1,
                    key=f"ext_{exp.id}",
                )
                e_val = st.number_input(
                    "Valor (R$)",
                    value=float(exp.value),
                    step=10.0,
                    key=f"exv_{exp.id}",
                )
                e_freq = st.number_input(
                    "Periodicidade em Meses",
                    min_value=1,
                    max_value=24,
                    value=max(1, exp.frequency_months),
                    help="Ex: 12 = Anual, 6 = Semestral. (Ignorado para custo Mensal)",
                    key=f"exf_{exp.id}",
                )
                if st.form_submit_button("Salvar"):
                    is_fixed = "Fixa" in e_type
                    db_type = "FIXED" if is_fixed else "PERIODIC"
                    final_freq = 1 if is_fixed else int(e_freq)
                    db_scope = "SHARED" if "Nosso" in e_scope else "PERSONAL"
                    
                    repo.update_expense(exp.id, e_name, db_type, e_val, final_freq, db_scope)
                    st.rerun()
            if st.button("❌ Excluir", key=f"exd_{exp.id}"):
                repo.delete_expense(exp.id)
                st.rerun()


def render_resumo_tab(
    repo: FinancialRepository,
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
        _render_partner_summary(repo, calc, user_a, expenses_a)
    with col_b:
        _render_partner_summary(repo, calc, user_b, expenses_b)
