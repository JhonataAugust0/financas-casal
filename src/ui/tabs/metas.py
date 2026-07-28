"""Tab: 🎯 Metas — goals, cascade allocation, safety reserve, and timeline projection."""

from __future__ import annotations

from collections import defaultdict
from datetime import date

import streamlit as st

from src.domain.financial_calculator import FinancialCalculator
from src.domain.models import Goal, User
from src.ports.repository import FinancialRepository

_SAFETY_CATEGORY = "🛡️ Segurança"


def _sync_safety_reserve(
    repo: FinancialRepository,
    calc: FinancialCalculator,
    user_a: User,
    user_b: User,
    cost_a: float,
    cost_b: float,
) -> None:
    """Synchronise the mandatory safety goal based on current toggle state."""
    current_allowance = float(user_a.allowance)
    is_maintenance = st.session_state.get("toggle_manutencao", False)

    if is_maintenance:
        target = ((cost_a + current_allowance) * user_a.multiplier) + (
            (cost_b + current_allowance) * user_b.multiplier
        )
    else:
        target = (cost_a * user_a.multiplier) + (cost_b * user_b.multiplier)

    repo.sync_reserva_paz(target, is_maintenance)


def _get_avg_monthly_contribution(repo: FinancialRepository) -> float:
    """Calculate the average monthly contribution from real history."""
    contributions = repo.get_all_contributions(months=6)
    if not contributions:
        return 0.0

    # Aggregate by month
    monthly_totals: dict[str, float] = {}
    for c in contributions:
        monthly_totals[c.month_year] = monthly_totals.get(c.month_year, 0.0) + c.actual_amount

    if not monthly_totals:
        return 0.0

    return sum(monthly_totals.values()) / len(monthly_totals)


def _render_timeline_badge(
    timeline_info: dict | None,
) -> None:
    """Render a timeline projection badge for a goal."""
    if timeline_info is None:
        return

    status = timeline_info["status"]
    if status == "CONCLUÍDA":
        st.markdown(
            "<span style='background-color: #D5E4D4; color: #446943; "
            "padding: 3px 8px; border-radius: 6px; font-size: 0.75rem;'>"
            "✅ Meta Concluída!</span>",
            unsafe_allow_html=True,
        )
    elif status == "SEM APORTE":
        st.markdown(
            "<span style='background-color: #F5D5D5; color: #8B3A3A; "
            "padding: 3px 8px; border-radius: 6px; font-size: 0.75rem;'>"
            "⚠️ Sem aportes registrados</span>",
            unsafe_allow_html=True,
        )
    else:
        months = timeline_info["estimated_months"]
        est_date = timeline_info["estimated_date"]
        remaining = timeline_info["remaining"]
        st.markdown(
            f"<span style='background-color: #E8DFF5; color: #5C4A7A; "
            f"padding: 3px 8px; border-radius: 6px; font-size: 0.75rem;'>"
            f"📅 Previsão: **{est_date}** (~{months} meses · "
            f"R$ {remaining:.2f} restantes)</span>",
            unsafe_allow_html=True,
        )


def _render_goal_item(
    repo: FinancialRepository,
    goal: Goal,
    is_safety: bool,
    timeline_map: dict[int, dict] | None = None,
) -> None:
    """Render a single goal item with progress bar, timeline badge, and optional edit controls."""
    progress = (
        goal.current_value / goal.target_value if goal.target_value > 0 else 0
    )

    col_item, col_edit = st.columns([0.9, 0.1])
    with col_item:
        link_html = (
            f" <a href='{goal.link}' target='_blank'>🔗</a>"
            if goal.link
            else ""
        )
        st.markdown(
            f"<span style='font-size: 0.9rem;'>"
            f"**{goal.name}** (Prio {goal.priority}){link_html}"
            f"</span>",
            unsafe_allow_html=True,
        )
        st.progress(min(progress, 1.0))
        st.markdown(
            f"<p style='text-align: right; font-size: 0.8rem; "
            f"color: #888; margin-top: -10px;'>"
            f"R$ {goal.current_value:.2f} / R$ {goal.target_value:.2f}</p>",
            unsafe_allow_html=True,
        )

        # Timeline projection badge
        if timeline_map and goal.id in timeline_map:
            _render_timeline_badge(timeline_map[goal.id])

    # Lock 2: Protect safety items from edits
    if not is_safety:
        with col_edit:
            with st.popover("⚙️"):
                with st.form(f"ef_{goal.id}"):
                    edit_name = st.text_input(
                        "Nome", value=goal.name, key=f"en_{goal.id}"
                    )
                    edit_link = st.text_input(
                        "Link", value=goal.link, key=f"el_{goal.id}"
                    )
                    ce1, ce2 = st.columns(2)
                    with ce1:
                        edit_target = st.number_input(
                            "Valor",
                            value=float(goal.target_value),
                            step=50.0,
                            key=f"et_{goal.id}",
                        )
                    with ce2:
                        edit_priority = st.number_input(
                            "Prio",
                            value=int(goal.priority),
                            step=1,
                            key=f"ep_{goal.id}",
                        )
                    if st.form_submit_button("Salvar"):
                        repo.update_goal_details(
                            goal.id, edit_name, edit_target, edit_priority, edit_link
                        )
                        st.rerun()
                if st.button("❌ Excluir", key=f"di_{goal.id}"):
                    repo.delete_goal(goal.id)
                    st.rerun()


def _render_subcategory(
    repo: FinancialRepository,
    category: str,
    subcategory: str,
    goals: list[Goal],
    is_safety: bool,
    timeline_map: dict[int, dict] | None = None,
) -> None:
    """Render a subcategory header, its goals, and management controls."""
    sub_target = sum(g.target_value for g in goals)
    sub_current = sum(g.current_value for g in goals)

    st.markdown(
        f"<div style='display: flex; justify-content: space-between; "
        f"align-items: center; margin-top: 24px; margin-bottom: 8px; "
        f"border-bottom: 1px solid #EAE0D5; padding-bottom: 4px;'>"
        f"<h4 style='color: #5C4A4D; font-size: 1.05rem; margin: 0;'>"
        f"📁 {subcategory}</h4>"
        f"<span style='font-size: 0.85rem; color: #7A6C68;'>"
        f"R$ {sub_current:.2f} / R$ {sub_target:.2f}</span></div>",
        unsafe_allow_html=True,
    )

    # Lock 1: Protect safety subcategory from deletion
    if not is_safety:
        _col_spacer, col_delete = st.columns([0.8, 0.2])
        with col_delete:
            with st.popover("🗑️", use_container_width=True):
                if st.button(
                    "Confirmar Exclusão", key=f"dels_{category}_{subcategory}"
                ):
                    repo.delete_subcategory(category, subcategory)
                    st.rerun()

    sorted_goals = sorted(goals, key=lambda g: g.priority)
    for goal in sorted_goals:
        _render_goal_item(repo, goal, is_safety, timeline_map)

    # Lock 3: Prevent adding new items to safety subcategories
    if not is_safety:
        st.write("")
        with st.popover(
            f"➕ Adicionar em {subcategory}", use_container_width=True
        ):
            with st.form(
                f"fa_{category}_{subcategory}", clear_on_submit=True
            ):
                new_name = st.text_input(
                    "Nome", key=f"an_{category}_{subcategory}"
                )
                new_link = st.text_input(
                    "Link", key=f"al_{category}_{subcategory}"
                )
                c1, c2 = st.columns(2)
                with c1:
                    new_target = st.number_input(
                        "R$",
                        min_value=0.0,
                        step=50.0,
                        key=f"at_{category}_{subcategory}",
                    )
                with c2:
                    new_priority = st.number_input(
                        "Prio",
                        min_value=1,
                        step=1,
                        key=f"ap_{category}_{subcategory}",
                    )
                if (
                    st.form_submit_button("Salvar")
                    and new_name
                    and new_target > 0
                ):
                    repo.add_goal(
                        new_name, category, subcategory, new_target, new_priority, new_link
                    )
                    st.rerun()


def _render_category_card(
    repo: FinancialRepository,
    category: str,
    goals: list[Goal],
    timeline_map: dict[int, dict] | None = None,
) -> None:
    """Render a full category expander card with subcategories."""
    is_safety = category == _SAFETY_CATEGORY
    cat_target = sum(g.target_value for g in goals)
    cat_current = sum(g.current_value for g in goals)
    cat_progress = cat_current / cat_target if cat_target > 0 else 0

    with st.expander(f"📄 {category}", expanded=is_safety):
        # Maintenance toggle — ONLY inside safety card
        if is_safety:
            st.toggle(
                "Modo Manutenção na Reserva (Inclui a Mesada)",
                key="toggle_manutencao",
                help=(
                    "Ativado: A meta cresce para cobrir boletos + mesada. "
                    "Desativado: Cobre apenas os boletos básicos."
                ),
            )

        st.markdown(
            f"<div style='display: flex; gap: 8px; margin-bottom: 16px;'>"
            f"<span style='background-color: #D3E0EA; color: #3A5A78; "
            f"padding: 4px 10px; border-radius: 6px; font-size: 0.8rem;'>"
            f"{len(goals)} Itens</span>"
            f"<span style='background-color: #D5E4D4; color: #446943; "
            f"padding: 4px 10px; border-radius: 6px; font-size: 0.8rem;'>"
            f"{(cat_progress * 100):.1f}% Concluído</span></div>",
            unsafe_allow_html=True,
        )
        st.progress(min(cat_progress, 1.0))
        st.markdown(
            f"<p style='text-align: right; font-size: 0.85rem; "
            f"color: #7A6C68; margin-top: -10px;'>"
            f"Total: R$ {cat_current:.2f} / R$ {cat_target:.2f}</p>",
            unsafe_allow_html=True,
        )

        # Group goals by subcategory
        subcategories: dict[str, list[Goal]] = defaultdict(list)
        for goal in goals:
            subcategories[goal.subcategory or "Geral"].append(goal)

        for subcat, sub_goals in subcategories.items():
            _render_subcategory(repo, category, subcat, sub_goals, is_safety, timeline_map)

        # Lock 4: Prevent creating new subcategories in safety card
        if not is_safety:
            st.write("")
            with st.popover(
                f"➕ Criar nova subcategoria em {category}",
                use_container_width=True,
            ):
                with st.form(f"fns_{category}", clear_on_submit=True):
                    ns_sub = st.text_input("Nova Subcategoria")
                    ns_name = st.text_input("Primeiro Item")
                    ns_link = st.text_input("Link")
                    sc1, sc2 = st.columns(2)
                    with sc1:
                        ns_target = st.number_input(
                            "R$", min_value=0.0, step=50.0
                        )
                    with sc2:
                        ns_priority = st.number_input(
                            "Prio", min_value=1, step=1
                        )
                    if (
                        st.form_submit_button("Criar")
                        and ns_sub
                        and ns_name
                        and ns_target > 0
                    ):
                        repo.add_goal(
                            ns_name, category, ns_sub, ns_target, ns_priority, ns_link
                        )
                        st.rerun()


def _render_global_creation_form(repo: FinancialRepository, has_goals: bool) -> None:
    """Global form for creating entirely new category cards."""
    with st.expander(
        "✨ Criar Novo Cartão Principal (Meta Global)", expanded=not has_goals
    ):
        with st.form("fg", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                new_category = st.text_input(
                    "Meta Principal (Cartão)", placeholder="Ex: Viagens"
                )
                new_name = st.text_input("Nome do Item")
            with c2:
                new_subcategory = st.text_input(
                    "Subcategoria", placeholder="Ex: Aéreo"
                )
                new_target = st.number_input("Valor Alvo (R$)", step=100.0)
            new_priority = st.number_input(
                "Prioridade (Não use o 1)", min_value=2, step=1
            )

            if (
                st.form_submit_button("Salvar na Base")
                and new_category
                and new_subcategory
                and new_name
                and new_target > 0
            ):
                if new_category == _SAFETY_CATEGORY:
                    st.error(
                        "Atenção: O nome '🛡️ Segurança' é uma placa "
                        "reservada pelo motor do sistema."
                    )
                else:
                    repo.add_goal(
                        new_name,
                        new_category,
                        new_subcategory,
                        new_target,
                        new_priority,
                    )
                    st.rerun()


def render_metas_tab(
    repo: FinancialRepository,
    calc: FinancialCalculator,
    user_a: User,
    user_b: User,
    cost_a: float,
    cost_b: float,
) -> None:
    """Render the complete 🎯 Metas tab."""
    st.subheader("Aportes")

    # 1. Synchronise safety reserve
    _sync_safety_reserve(repo, calc, user_a, user_b, cost_a, cost_b)

    # 2. Fetch goals
    goals = repo.get_goals()

    # 3. Calculate timeline projections
    avg_contribution = _get_avg_monthly_contribution(repo)
    timeline_map: dict[int, dict] = {}

    if goals and avg_contribution > 0:
        timelines = calc.project_goal_timelines(goals, avg_contribution)
        for t in timelines:
            timeline_map[t["goal_id"]] = t

    # 4. Aporte form
    if goals:
        st.write("")

        # Show average contribution rate info
        if avg_contribution > 0:
            st.info(
                f"📈 Ritmo médio de aporte real: **R\\$ {avg_contribution:.2f}/mês** "
                f"(baseado no histórico). As previsões de data usam este valor."
            )
        else:
            st.info(
                "📈 Ainda não há histórico de aportes. "
                "Faça o primeiro aporte para ativar as previsões de data de conclusão."
            )

        amount = st.number_input(
            "Valor do Aporte Conjunto (R$)", min_value=0.0, step=50.0
        )
        if st.button("Inserir Aporte 🚀"):
            # Run cascade allocation
            old_values = {g.id: g.current_value for g in goals}
            updated = calc.waterfall_allocation(goals, amount)
            repo.update_goals(updated)

            # Record contributions per goal
            current_month = date.today().strftime("%Y-%m")
            for goal in updated:
                actual_fill = goal.current_value - old_values.get(goal.id, goal.current_value)
                if actual_fill > 0:
                    # planned = what cascade computed, actual = same (user confirmed the amount)
                    repo.add_goal_contribution(
                        goal.id, current_month, actual_fill, actual_fill
                    )

            st.success(f"R\\$ {amount:.2f} distribuídos conforme a prioridade!")
            st.rerun()

        st.divider()
        st.markdown("### Painel de Metas")

        # Build ordered category list (safety first)
        categories_map: dict[str, list[Goal]] = defaultdict(list)
        for goal in goals:
            categories_map[goal.category].append(goal)

        ordered_categories = list(categories_map.keys())
        if _SAFETY_CATEGORY in ordered_categories:
            ordered_categories.remove(_SAFETY_CATEGORY)
            ordered_categories.insert(0, _SAFETY_CATEGORY)

        for category in ordered_categories:
            _render_category_card(repo, category, categories_map[category], timeline_map)

    # Global creation form (always visible)
    st.write("")
    _render_global_creation_form(repo, bool(goals))
