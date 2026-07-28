"""Tab: 📋 Fechamento — monthly budget vs actual tracking and contribution history."""

from __future__ import annotations

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


def _render_periodic_radar(
    all_expenses: list[Expense],
    realized_obj_map: dict[int, MonthlyRealized],
    user_a: User,
    user_b: User,
    selected_month: str,
) -> dict[int, bool]:
    """Render an interactive 1-click radar for periodic purchases at the top of closing."""
    periodic_expenses = [e for e in all_expenses if e.type == "PERIODIC"]
    if not periodic_expenses:
        return {}

    st.markdown("#### Radar de Compras Periódicas")
    st.caption(
        "Marque com **1 clique** os produtos periódicos que foram comprados neste mês. "
        "O aplicativo preencherá automaticamente o valor cheio do produto no fechamento."
    )

    bought_status: dict[int, bool] = {}

    # Group by owner
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
                # Default checked state: if recorded with budgeted_value > 0 or existing session state
                if toggle_key not in st.session_state:
                    default_checked = (existing_rec.budgeted_value > 0) if existing_rec else False
                    st.session_state[toggle_key] = default_checked

                is_checked = st.toggle(
                    f"🛒 **{exp.name}** (R$ {exp.value:.2f} · a cada {exp.frequency_months}m)",
                    key=toggle_key,
                )
                bought_status[exp.id] = is_checked

                # Sync value to real_key for the form below
                if is_checked:
                    # If recorded had a custom real value (e.g. bought on sale), keep it; otherwise default to full price
                    if existing_rec and existing_rec.actual_value > 0 and existing_rec.budgeted_value > 0:
                        st.session_state[real_key] = float(existing_rec.actual_value)
                    else:
                        st.session_state[real_key] = float(exp.value)
                else:
                    st.session_state[real_key] = 0.0

    st.markdown("---")
    return bought_status


def _render_expense_group_in_form(
    label: str,
    expenses: list[Expense],
    realized_obj_map: dict[int, MonthlyRealized],
    user_a: User,
    user_b: User,
    actual_values: dict[int, float],
    selected_month: str,
    bought_status: dict[int, bool],
) -> None:
    """Render a scope group (🏠 O NOSSO or 👤 O MEU) inside the form."""
    if not expenses:
        return

    st.markdown(f"**{label}**")

    for exp in expenses:
        existing_rec = realized_obj_map.get(exp.id)
        real_key = f"real_{exp.id}_{selected_month}"

        c1, c2, c3, c4 = st.columns([0.35, 0.10, 0.30, 0.25])
        with c1:
            if exp.type == "PERIODIC":
                is_bought = bought_status.get(exp.id, False)
                status_icon = "🛒 Comprado" if is_bought else "💤 Sem compra"
                st.markdown(f"**{exp.name}**")
                st.caption(f"{status_icon} · a cada {exp.frequency_months}m")
            else:
                st.markdown(f"**{exp.name}**")
        with c2:
            emoji = _get_partner_emoji(user_a if exp.user_id == "A" else user_b)
            st.markdown(f"{emoji}")

        with c3:
            if exp.type == "PERIODIC":
                is_bought = bought_status.get(exp.id, False)
                if is_bought:
                    st.markdown(f"**R$ {exp.value:.2f}** *(Valor cheio)*")
                else:
                    st.markdown("R$ 0.00 *(Sem compra)*")
            else:
                st.markdown(f"R$ {exp.value:.2f}")

        with c4:
            # Ensure session state is set
            if real_key not in st.session_state:
                if exp.type == "PERIODIC":
                    is_bought = bought_status.get(exp.id, False)
                    st.session_state[real_key] = float(exp.value) if is_bought else 0.0
                else:
                    st.session_state[real_key] = float(existing_rec.actual_value) if existing_rec else float(exp.value)

            actual_values[exp.id] = st.number_input(
                "Real",
                min_value=0.0,
                step=5.0,
                key=real_key,
                disabled=(exp.type == "PERIODIC" and not bought_status.get(exp.id, False)),
                label_visibility="collapsed",
            )


def _render_budget_vs_actual(
    repo: FinancialRepository,
    calc: FinancialCalculator,
    expenses_a: list[Expense],
    expenses_b: list[Expense],
    user_a: User,
    user_b: User,
) -> None:
    """Section A: Monthly expense closing — budget vs actual values."""
    st.markdown("### Orçado vs. Realizado")

    # Month selector
    today = date.today()
    default_month = today.strftime("%Y-%m")

    col_month, _ = st.columns([0.4, 0.6])
    with col_month:
        selected_month = st.text_input(
            "Mês de Referência (AAAA-MM)",
            value=default_month,
            key="fechamento_month",
            help="Ex: 2026-07 para julho de 2026.",
        )

    # Validate month format
    if len(selected_month) != 7 or selected_month[4] != "-":
        st.warning("Formato inválido. Use AAAA-MM (ex: 2026-07).")
        return

    # Load existing realized data for this month
    existing_realized = repo.get_monthly_realized(selected_month)
    realized_obj_map = {r.expense_id: r for r in existing_realized}

    # Combine and split by scope
    all_expenses = expenses_a + expenses_b
    shared_expenses = [e for e in all_expenses if e.scope == "SHARED"]
    personal_expenses = [e for e in all_expenses if e.scope == "PERSONAL"]

    if not all_expenses:
        st.info("Nenhuma despesa cadastrada. Cadastre despesas na aba 📊 Resumo ou 💰 Orçamento.")
        return

    # ── 1-Click Interactive Radar for Periodic Purchases (Out of form) ──
    bought_status = _render_periodic_radar(
        all_expenses, realized_obj_map, user_a, user_b, selected_month
    )

    # Build form
    with st.form("fechamento_form", clear_on_submit=False):
        st.markdown(f"**Fechamento de {selected_month}**")

        # Header row
        hdr1, hdr2, hdr3, hdr4 = st.columns([0.35, 0.10, 0.30, 0.25])
        with hdr1:
            st.markdown("**Despesa**")
        with hdr2:
            st.markdown("**Dono**")
        with hdr3:
            st.markdown("**Valor Esperado**")
        with hdr4:
            st.markdown("**Gasto Real (R$)**")

        actual_values: dict[int, float] = {}

        # ── 🏠 O NOSSO (Bolo Central) ──
        st.markdown("---")
        _render_expense_group_in_form(
            "🏠 O Nosso — Bolo Central",
            shared_expenses,
            realized_obj_map,
            user_a, user_b,
            actual_values,
            selected_month,
            bought_status,
        )

        # ── 👤 O MEU / O SEU (Mesada) ──
        if personal_expenses:
            st.markdown("---")
            _render_expense_group_in_form(
                "👤 O Meu / O Seu — Mesada Individual",
                personal_expenses,
                realized_obj_map,
                user_a, user_b,
                actual_values,
                selected_month,
                bought_status,
            )

        st.markdown("---")

        if st.form_submit_button("💾 Salvar Fechamento do Mês", use_container_width=True):
            for exp in all_expenses:
                actual = actual_values.get(exp.id, 0.0)
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

    # ── Variance analysis panel ──
    realized_data = repo.get_monthly_realized(selected_month)
    if realized_data:
        st.markdown("---")
        st.markdown(f"### 📊 Diagnóstico de {selected_month}")

        # Build maps for display
        expense_map = {e.id: e for e in all_expenses}
        expense_name_map = {e.id: e.name for e in all_expenses}

        # Split realized by scope
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
            st.markdown("#### 👤 Mesada Individual (O Meu / O Seu)")

            # Split by person
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
                        f"{emoji} {user.name} — Orçado do Mês",
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

                # Per-item breakdown
                for r in user_personal:
                    exp = expense_map.get(r.expense_id)
                    if not exp:
                        continue
                    item_var = r.budgeted_value - r.actual_value
                    icon = "🟢" if item_var >= 0 else "🔴"
                    direction = "economia" if item_var >= 0 else "estouro"
                    type_str = "Periódica" if exp.type == "PERIODIC" else "Mensal"
                    st.markdown(
                        f"  {icon} **{exp.name}** *({type_str})*: Orçado R$ {r.budgeted_value:.2f} → "
                        f"Real R$ {r.actual_value:.2f} "
                        f"*(R$ {abs(item_var):.2f} de {direction})*"
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
                        f"{icon} {scope_icon} **{exp_name}**: Orçado R$ {item['budgeted']:.2f} → "
                        f"Real R$ {item['actual']:.2f} "
                        f"*(R$ {abs(var):.2f} de {direction})*"
                    )


def _render_contribution_history(
    repo: FinancialRepository,
) -> None:
    """Section B: Goal contribution history and average contribution rate."""
    st.markdown("---")
    st.markdown("### 📈 Histórico de Aportes em Metas")
    st.caption(
        "Veja o quanto foi **realmente aportado** a cada mês nas metas do casal, "
        "comparado com o planejado pela Cascata."
    )

    contributions = repo.get_all_contributions(months=12)

    if not contributions:
        st.info(
            "Nenhum aporte registrado ainda. "
            "Faça aportes na aba 🎯 Metas para começar a gerar histórico."
        )
        return

    # Build goals map for names
    goals = repo.get_goals()
    goal_name_map = {g.id: g.name for g in goals}

    # Aggregate by month
    monthly_totals: dict[str, dict[str, float]] = {}
    for c in contributions:
        if c.month_year not in monthly_totals:
            monthly_totals[c.month_year] = {"planned": 0.0, "actual": 0.0}
        monthly_totals[c.month_year]["planned"] += c.planned_amount
        monthly_totals[c.month_year]["actual"] += c.actual_amount

    # Display monthly summary
    sorted_months = sorted(monthly_totals.keys(), reverse=True)

    for month in sorted_months:
        totals = monthly_totals[month]
        with st.expander(f"📅 {month}", expanded=(month == sorted_months[0])):
            cm1, cm2, cm3 = st.columns(3)
            with cm1:
                st.metric("Planejado (Cascata)", f"R$ {totals['planned']:.2f}")
            with cm2:
                st.metric("Aportado (Real)", f"R$ {totals['actual']:.2f}")
            with cm3:
                diff = totals["actual"] - totals["planned"]
                st.metric(
                    "Diferença",
                    f"R$ {abs(diff):.2f}",
                    delta=f"{'acima' if diff >= 0 else 'abaixo'} do planejado",
                    delta_color="normal" if diff >= 0 else "inverse",
                )

            # Per-goal detail
            month_contribs = [c for c in contributions if c.month_year == month]
            for c in month_contribs:
                gname = goal_name_map.get(c.goal_id, f"Meta #{c.goal_id}")
                st.markdown(
                    f"  • **{gname}**: Planejado R$ {c.planned_amount:.2f} → "
                    f"Real R$ {c.actual_amount:.2f}"
                )

    # Average contribution rate
    st.markdown("---")
    if monthly_totals:
        avg_actual = sum(t["actual"] for t in monthly_totals.values()) / len(monthly_totals)
        num_months = len(monthly_totals)
        st.metric(
            f"🎯 Média de Aporte Real Mensal (últimos {num_months} meses)",
            f"R$ {avg_actual:.2f}",
        )
        st.caption(
            "Esta média é usada na aba 🎯 Metas para projetar as datas de conclusão dos objetivos."
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

    _render_budget_vs_actual(repo, calc, expenses_a, expenses_b, user_a, user_b)
    _render_contribution_history(repo)
