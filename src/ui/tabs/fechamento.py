"""Tab: 📋 Fechamento — monthly budget vs actual tracking, couple metrics, and budget diagnostics."""

from __future__ import annotations

import math
from datetime import date

import streamlit as st

from src.domain.financial_calculator import FinancialCalculator
from src.domain.models import Expense, MonthlyRealized, User
from src.ports.repository import FinancialRepository


def _get_partner_emoji(user: User) -> str:
    """Return specific partner emoji based on name or ID."""
    name_lower = user.name.lower()
    if "docinho" in name_lower or user.id == "A":
        return "👩🏿"
    if "gracinha" in name_lower or user.id == "B":
        return "👨🏿"
    return "👤"


def _render_couple_celebration_panel(
    repo: FinancialRepository,
    calc: FinancialCalculator,
    user_a: User,
    user_b: User,
    expenses_a: list[Expense],
    expenses_b: list[Expense],
) -> None:
    """Render top metrics: Reserva de Paz growth, Goals advance %, and joint model savings."""
    goals = repo.get_goals()
    contributions = repo.get_all_contributions(months=12)

    cost_a = calc.calculate_monthly_cost_from_expenses(expenses_a, scope_filter="SHARED")
    cost_b = calc.calculate_monthly_cost_from_expenses(expenses_b, scope_filter="SHARED")
    joint_sim = calc.simulate_joint_income(
        user_a.income, user_b.income, cost_a, cost_b, user_a.allowance
    )

    metrics = calc.calculate_couple_impact_metrics(
        goals, contributions, deficit_rescued=joint_sim.deficit_rescued
    )

    current_month = date.today().strftime("%Y-%m")
    safety_val = metrics["reserve_current"]
    goals_val = max(0.0, metrics["total_current_wealth"] - safety_val)
    repo.save_monthly_snapshot(current_month, safety_val, goals_val)

    st.markdown("### 🏆 Conquistas e Impacto do Casal")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric(
            "Reserva de Paz",
            f"R$ {metrics['reserve_current']:.2f}",
            delta=f"{metrics['reserve_pct']:.1f}% da meta",
        )
    with c2:
        st.metric(
            "Avanço das Metas",
            f"{metrics['goals_pct']:.1f}%",
            delta=f"R\\$ {metrics['total_current_wealth']:.2f} total",
        )
    with c3:
        st.metric(
            "Ganho Compartilhado",
            f"R$ {metrics['joint_benefit']:.2f}/mês",
            delta="déficit individual evitado",
        )

    st.markdown("---")


def _render_periodic_radar(
    all_expenses: list[Expense],
    realized_obj_map: dict[int, MonthlyRealized],
    user_a: User,
    user_b: User,
    selected_month: str,
) -> dict[int, bool]:
    """Render an interactive 1-click radar for periodic purchases inside a seamless collapsible section."""
    periodic_expenses = [e for e in all_expenses if e.type == "PERIODIC"]
    if not periodic_expenses:
        return {}

    bought_status: dict[int, bool] = {}

    with st.expander("Radar de Compras Periódicas", expanded=False):
        st.caption(
            "Marque com **1 clique** os produtos periódicos comprados neste mês. "
            "O sistema ajustará automaticamente o valor cheio no fechamento."
        )

        cols = st.columns(2)
        for idx, user in enumerate([user_a, user_b]):
            emoji = _get_partner_emoji(user)
            user_periodics = [e for e in periodic_expenses if e.user_id == user.id]

            with cols[idx]:
                st.markdown(f"**{emoji} Itens de {user.name}**")
                if not user_periodics:
                    st.caption("Nenhum item periódico.")
                    continue

                for exp in user_periodics:
                    toggle_key = f"toggle_p_{exp.id}_{selected_month}"
                    real_key = f"real_{exp.id}_{selected_month}"

                    existing_rec = realized_obj_map.get(exp.id)
                    if toggle_key not in st.session_state:
                        default_checked = (existing_rec.budgeted_value > 0) if existing_rec else False
                        st.session_state[toggle_key] = default_checked

                    is_checked = st.toggle(
                        f"🛒 **{exp.name}** (R$ {exp.value:.2f} · {exp.frequency_months}m)",
                        key=toggle_key,
                    )
                    bought_status[exp.id] = is_checked

                    if is_checked:
                        if existing_rec and existing_rec.actual_value > 0 and existing_rec.budgeted_value > 0:
                            st.session_state[real_key] = float(existing_rec.actual_value)
                        else:
                            st.session_state[real_key] = float(exp.value)
                    else:
                        st.session_state[real_key] = 0.0

    return bought_status


def _render_budget_vs_actual(
    repo: FinancialRepository,
    calc: FinancialCalculator,
    expenses_a: list[Expense],
    expenses_b: list[Expense],
    user_a: User,
    user_b: User,
) -> None:
    """Section A: Monthly expense closing with 5-item collapsible card pagination."""
    st.markdown("### Orçado vs. Realizado")

    today = date.today()
    default_month = today.strftime("%Y-%m")

    col_month, _ = st.columns([0.5, 0.5])
    with col_month:
        selected_month = st.text_input(
            "Mês de Referência (AAAA-MM)",
            value=default_month,
            key="fechamento_month",
            help="Ex: 2026-07 para julho de 2026.",
        )

    if len(selected_month) != 7 or selected_month[4] != "-":
        st.warning("Formato inválido. Use AAAA-MM (ex: 2026-07).")
        return

    existing_realized = repo.get_monthly_realized(selected_month)
    realized_obj_map = {r.expense_id: r for r in existing_realized}

    all_expenses = expenses_a + expenses_b

    if not all_expenses:
        st.info("Nenhuma despesa cadastrada. Cadastre despesas na aba 📊 Resumo ou 💰 Orçamento.")
        return

    # Collapsible Radar de Compras Periódicas (Seamless)
    bought_status = _render_periodic_radar(
        all_expenses, realized_obj_map, user_a, user_b, selected_month
    )

    # ── Collapsible Paginated Expenses (5 Items per Page) ──
    ITEMS_PER_PAGE = 5
    total_pages = max(1, math.ceil(len(all_expenses) / ITEMS_PER_PAGE))
    page_key = f"fechamento_page_{selected_month}"
    if page_key not in st.session_state or st.session_state[page_key] > total_pages:
        st.session_state[page_key] = 1

    actual_values: dict[int, float] = {}

    with st.expander("📝 Preenchimento de Despesas do Mês", expanded=True):
        # Pagination Bar
        nav_prev, nav_label, nav_next = st.columns([0.3, 0.4, 0.3])
        with nav_prev:
            if st.button("◀ Anterior", disabled=(st.session_state[page_key] <= 1), use_container_width=True):
                st.session_state[page_key] -= 1
                st.rerun()
        with nav_label:
            st.markdown(
                f"<p style='text-align:center; font-weight:600; margin-top:8px; color:#5C4A4D;'>"
                f"Página {st.session_state[page_key]} de {total_pages}</p>",
                unsafe_allow_html=True,
            )
        with nav_next:
            if st.button("Próxima ▶", disabled=(st.session_state[page_key] >= total_pages), use_container_width=True):
                st.session_state[page_key] += 1
                st.rerun()

        start_idx = (st.session_state[page_key] - 1) * ITEMS_PER_PAGE
        page_expenses = all_expenses[start_idx : start_idx + ITEMS_PER_PAGE]

        with st.form(f"fechamento_form_p{st.session_state[page_key]}", clear_on_submit=False):
            for exp in page_expenses:
                existing_rec = realized_obj_map.get(exp.id)
                real_key = f"real_{exp.id}_{selected_month}"
                emoji = _get_partner_emoji(user_a if exp.user_id == "A" else user_b)
                scope_icon = "🏠 O NOSSO" if exp.scope == "SHARED" else "👤 O MEU"

                if exp.type == "PERIODIC":
                    is_bought = bought_status.get(exp.id, False)
                    expected_str = f"R$ {exp.value:.2f} (Cheio)" if is_bought else "R$ 0.00 (Sem compra)"
                    type_desc = f"Periódica ({exp.frequency_months}m)"
                else:
                    expected_str = f"R$ {exp.value:.2f}"
                    type_desc = "Mensal Fixa"

                # Seamless Item Header Layout (Seamless with page background)
                st.markdown(
                    f"<div class='expense-item-seamless'>"
                    f"<div style='display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; gap: 4px;'>"
                    f"<span>{emoji} <strong>{exp.name}</strong> <small style='color:#7A6C68;'>({type_desc})</small></span>"
                    f"<span style='font-size:0.75rem; background-color:#EAE0D5; color:#5C4A4D; padding:2px 6px; border-radius:4px;'>{scope_icon}</span>"
                    f"</div>"
                    f"<div style='font-size:0.85rem; color:#5C4A4D; margin-top:2px;'>"
                    f"Valor Esperado: <strong>{expected_str}</strong></div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

                if real_key not in st.session_state:
                    if exp.type == "PERIODIC":
                        is_bought = bought_status.get(exp.id, False)
                        st.session_state[real_key] = float(exp.value) if is_bought else 0.0
                    else:
                        st.session_state[real_key] = float(existing_rec.actual_value) if existing_rec else float(exp.value)

                actual_values[exp.id] = st.number_input(
                    f"Gasto Real (R$) — {exp.name}",
                    min_value=0.0,
                    step=5.0,
                    key=real_key,
                    disabled=(exp.type == "PERIODIC" and not bought_status.get(exp.id, False)),
                )

            if st.form_submit_button("💾 Salvar Fechamento do Mês", use_container_width=True):
                for exp in all_expenses:
                    real_key = f"real_{exp.id}_{selected_month}"
                    if real_key in st.session_state:
                        actual = float(st.session_state[real_key])
                    elif exp.id in actual_values:
                        actual = actual_values[exp.id]
                    else:
                        existing_rec = realized_obj_map.get(exp.id)
                        actual = existing_rec.actual_value if existing_rec else (exp.value if exp.type == "FIXED" else 0.0)

                    if exp.type == "FIXED":
                        budgeted = exp.value
                    else:
                        is_bought = bought_status.get(exp.id, False)
                        budgeted = exp.value if is_bought else 0.0
                        if not is_bought:
                            actual = 0.0

                    repo.upsert_monthly_realized(exp.id, selected_month, budgeted, actual)

                st.success(f"✅ Fechamento de {selected_month} salvo com sucesso!")
                st.rerun()

    # ── Collapsible Variance Analysis Panel ──
    realized_data = repo.get_monthly_realized(selected_month)
    if realized_data:
        with st.expander(f"📊 Diagnóstico Mensal de {selected_month}", expanded=True):
            expense_map = {e.id: e for e in all_expenses}
            expense_name_map = {e.id: e.name for e in all_expenses}

            shared_realized = [r for r in realized_data if expense_map.get(r.expense_id) and expense_map[r.expense_id].scope == "SHARED"]
            personal_realized = [r for r in realized_data if expense_map.get(r.expense_id) and expense_map[r.expense_id].scope == "PERSONAL"]

            # ── 🏠 Bolo Central diagnostics ──
            if shared_realized:
                shared_analysis = calc.calculate_budget_variance(shared_realized)

                st.markdown("#### 🏠 Bolo Central (O Nosso)")
                m1, m2, m3 = st.columns(3)
                with m1:
                    st.metric("Orçado no Mês", f"R$ {shared_analysis['total_budgeted']:.2f}")
                with m2:
                    st.metric("Real", f"R$ {shared_analysis['total_actual']:.2f}")
                with m3:
                    var = shared_analysis["variance"]
                    is_eco = var >= 0
                    st.metric(
                        "Economia 🟢" if is_eco else "Estouro 🔴",
                        f"R$ {abs(var):.2f}",
                        delta=f"{shared_analysis['variance_pct']:.1f}%",
                        delta_color="normal" if is_eco else "inverse",
                    )

                if is_eco and var > 0:
                    st.caption(
                        f"💡 A economia de R\\$ {var:.2f} no Bolo Central pode ser redirecionada para aportes!"
                    )

            # ── 👤 Mesada diagnostics (per person) ──
            if personal_realized:
                st.markdown("---")
                st.markdown("#### 👤 Mesada Individual (O Meu / O Seu)")

                for user in [user_a, user_b]:
                    emoji = _get_partner_emoji(user)
                    user_personal = [
                        r for r in personal_realized
                        if expense_map.get(r.expense_id) and expense_map[r.expense_id].user_id == user.id
                    ]
                    if not user_personal:
                        continue

                    total_personal_actual = sum(r.actual_value for r in user_personal)
                    total_personal_budgeted = sum(r.budgeted_value for r in user_personal)
                    mesada_remaining = user.allowance - total_personal_actual

                    pc1, pc2, pc3 = st.columns(3)
                    with pc1:
                        st.metric(
                            f"{emoji} {user.name} — Orçado",
                            f"R$ {total_personal_budgeted:.2f}",
                        )
                    with pc2:
                        st.metric(
                            "Gasto Real",
                            f"R$ {total_personal_actual:.2f}",
                        )
                    with pc3:
                        st.metric(
                            "Mesada Livre",
                            f"R$ {mesada_remaining:.2f}",
                            delta=f"de R\\$ {user.allowance:.2f}",
                            delta_color="normal" if mesada_remaining >= 0 else "inverse",
                        )

                    if mesada_remaining < 0:
                        st.warning(
                            f"⚠️ {user.name} estourou a mesada em R\\$ {abs(mesada_remaining):.2f} "
                            f"neste mês! Considere reduzir gastos pessoais ou ajustar o teto."
                        )

                    for r in user_personal:
                        exp = expense_map.get(r.expense_id)
                        if not exp:
                            continue
                        item_var = r.budgeted_value - r.actual_value
                        icon = "🟢" if item_var >= 0 else "🔴"
                        direction = "economia" if item_var >= 0 else "estouro"
                        type_str = "Periódica" if exp.type == "PERIODIC" else "Mensal"
                        st.markdown(
                            f"  {icon} **{exp.name}** *({type_str})*: Orçado R\\$ {r.budgeted_value:.2f} → "
                            f"Real R\\$ {r.actual_value:.2f} "
                            f"*(R\\$ {abs(item_var):.2f} de {direction})*"
                        )

            # ── Global top deviations ──
            if realized_data:
                full_analysis = calc.calculate_budget_variance(realized_data)
                if full_analysis["items"]:
                    st.markdown("---")
                    st.markdown("#### 🔍 Top 5 Maiores Desvios (Geral)")
                    top_items = full_analysis["items"][:5]
                    for item in top_items:
                        exp_name = expense_name_map.get(item["expense_id"], f"ID {item['expense_id']}")
                        exp = expense_map.get(item["expense_id"])
                        scope_icon = "🏠" if (exp and exp.scope == "SHARED") else "👤"
                        var = item["variance"]
                        icon = "🟢" if var >= 0 else "🔴"
                        direction = "economia" if var >= 0 else "estouro"
                        st.markdown(
                            f"{icon} {scope_icon} **{exp_name}**: Orçado R\\$ {item['budgeted']:.2f} → "
                            f"Real R\\$ {item['actual']:.2f} "
                            f"*(R\\$ {abs(item_var):.2f} de {direction})*"
                        )


def render_fechamento_tab(
    repo: FinancialRepository,
    calc: FinancialCalculator,
    user_a: User,
    user_b: User,
    expenses_a: list[Expense],
    expenses_b: list[Expense],
) -> None:
    """Render the complete 📋 Fechamento tab."""
    st.subheader("Fechamento Mensal")

    _render_couple_celebration_panel(repo, calc, user_a, user_b, expenses_a, expenses_b)
    _render_budget_vs_actual(repo, calc, expenses_a, expenses_b, user_a, user_b)
