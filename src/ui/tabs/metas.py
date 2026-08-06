"""Tab: 🎯 Metas — goals, cascade allocation, timeline projection, contribution history, and wealth evolution."""

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

    monthly_totals: dict[str, float] = {}
    for c in contributions:
        monthly_totals[c.month_year] = monthly_totals.get(c.month_year, 0.0) + c.actual_amount

    if not monthly_totals:
        return 0.0

    return sum(monthly_totals.values()) / len(monthly_totals)


def _render_timeline_badge(
    timeline_info: dict | None,
    simulated_info: dict | None = None,
) -> None:
    """Render a clean timeline projection card spanning 100% width for perfect alignment."""
    if timeline_info is None:
        return

    status = timeline_info["status"]
    if status == "CONCLUÍDA":
        st.markdown(
            "<div style='background-color: #D5E4D4; border-left: 4px solid #446943; color: #2D472C; "
            "padding: 6px 12px; border-radius: 6px; font-size: 0.85rem; font-weight: 600; margin-top: 6px; width: 100%; box-sizing: border-box;'>"
            "✅ Meta Concluída com Sucesso!</div>",
            unsafe_allow_html=True,
        )
    elif status == "SEM APORTE":
        st.markdown(
            "<div style='background-color: #FDF2F2; border-left: 4px solid #E53E3E; color: #9B2C2C; "
            "padding: 6px 12px; border-radius: 6px; font-size: 0.85rem; font-weight: 600; margin-top: 6px; width: 100%; box-sizing: border-box;'>"
            "⚠️ Sem aportes suficientes para projetar conclusão</div>",
            unsafe_allow_html=True,
        )
    else:
        if simulated_info and simulated_info.get("months_saved", 0) > 0:
            sim_date = simulated_info["simulated_date"]
            sim_months = simulated_info["simulated_months"]
            saved = simulated_info["months_saved"]
            month_label = "MÊS" if saved == 1 else "MESES"
            st.markdown(
                f"<div style='background: linear-gradient(135deg, #ECFDF5 0%, #D1FAE5 100%); border-left: 4px solid #10B981; color: #065F46; "
                f"padding: 8px 12px; border-radius: 8px; font-size: 0.88rem; font-weight: 600; margin-top: 6px; width: 100%; box-sizing: border-box; "
                f"display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 4px;'>"
                f"<span>🚀 <strong>Nova Previsão: {sim_date}</strong> <small style='color: #047857;'>({sim_months}m restantes)</small></span>"
                f"<span style='background-color: #059669; color: #FFFFFF; padding: 3px 10px; border-radius: 12px; font-size: 0.78rem; font-weight: 700;'>"
                f"⚡ {saved} {month_label} MAIS RÁPIDO!</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
        else:
            months = timeline_info["estimated_months"]
            est_date = timeline_info["estimated_date"]
            remaining = timeline_info["remaining"]
            st.markdown(
                f"<div style='background: linear-gradient(135deg, #F3E8FF 0%, #E9D5FF 100%); border-left: 4px solid #8B5CF6; color: #4C1D95; "
                f"padding: 8px 12px; border-radius: 8px; font-size: 0.88rem; font-weight: 600; margin-top: 6px; width: 100%; box-sizing: border-box; "
                f"display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 4px;'>"
                f"<span>📅 <strong>Conclusão Prevista: {est_date}</strong> <small style='color: #6B21A8;'>({months}m restantes)</small></span>"
                f"<span style='font-size:0.82rem; color: #5B21B6;'>Faltam R$ {remaining:.2f}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )


def _render_goal_item(
    repo: FinancialRepository,
    goal: Goal,
    is_safety: bool,
    timeline_map: dict[int, dict] | None = None,
    simulated_map: dict[int, dict] | None = None,
) -> None:
    """Render a single goal item with unified ⚙️ popover containing edit + delete."""
    progress = (
        goal.current_value / goal.target_value if goal.target_value > 0 else 0
    )

    c_title, c_edit, c_del = st.columns([0.82, 0.09, 0.09])
    with c_title:
        link_html = f" <a href='{goal.link}' target='_blank'>🔗</a>" if goal.link else ""
        st.markdown(
            f"<div style='display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; gap: 4px; width: 100%; box-sizing: border-box;'>"
            f"<span style='font-size: 1rem; line-height: 1.4;'><strong>{goal.name}</strong> "
            f"<small style='color: #9B8E8A;'>(Prio {goal.priority})</small>{link_html}</span>"
            f"<span style='font-size: 0.9rem; color: #37352F; font-weight: 700; white-space: nowrap;'>R$ {goal.current_value:.2f} / R$ {goal.target_value:.2f}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    if not is_safety:
        with c_edit:
            with st.popover("⚙️", use_container_width=True):
                st.markdown("**Editar Meta**")
                with st.form(f"ef_{goal.id}"):
                    edit_name = st.text_input("Nome", value=goal.name, key=f"en_{goal.id}")
                    edit_link = st.text_input("Link", value=goal.link, key=f"el_{goal.id}")
                    ce1, ce2 = st.columns(2)
                    with ce1:
                        edit_target = st.number_input("Valor", value=float(goal.target_value), step=50.0, key=f"et_{goal.id}")
                    with ce2:
                        edit_priority = st.number_input("Prio", value=int(goal.priority), step=1, key=f"ep_{goal.id}")
                    if st.form_submit_button("Salvar"):
                        repo.update_goal_details(goal.id, edit_name, edit_target, edit_priority, edit_link)
                        st.rerun()
        with c_del:
            with st.popover("🗑️", use_container_width=True):
                st.markdown(f"**Excluir '{goal.name}'?**")
                if st.button("Confirmar", key=f"di_{goal.id}", use_container_width=True):
                    repo.delete_goal(goal.id)
                    st.rerun()

    st.progress(min(progress, 1.0))

    if timeline_map and goal.id in timeline_map:
        sim_info = simulated_map.get(goal.id) if simulated_map else None
        _render_timeline_badge(timeline_map[goal.id], sim_info)

    st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)


def _render_subcategory(
    repo: FinancialRepository,
    category: str,
    subcategory: str,
    goals: list[Goal],
    is_safety: bool,
    timeline_map: dict[int, dict] | None = None,
    simulated_map: dict[int, dict] | None = None,
) -> None:
    """Render clean subcategory header with inline delete button."""
    if not is_safety:
        col_sub_title, col_sub_del = st.columns([0.91, 0.09])
        with col_sub_title:
            st.markdown(
                f"<div style='margin-top: 14px; margin-bottom: 8px; border-bottom: 1px solid #EAE0D5; padding-bottom: 4px;'>"
                f"<h4 style='color: #5C4A4D; font-size: 1.08rem; margin: 0;'>"
                f"📁 {subcategory}</h4></div>",
                unsafe_allow_html=True,
            )
        with col_sub_del:
            st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)
            with st.popover("🗑️", use_container_width=True):
                st.markdown(f"**Excluir '{subcategory}'?**")
                st.caption("Todos os itens desta subcategoria serão removidos.")
                if st.button("Confirmar Exclusão", key=f"dels_{category}_{subcategory}"):
                    repo.delete_subcategory(category, subcategory)
                    st.rerun()
    else:
        st.markdown(
            f"<div style='margin-top: 14px; margin-bottom: 8px; border-bottom: 1px solid #EAE0D5; padding-bottom: 4px;'>"
            f"<h4 style='color: #5C4A4D; font-size: 1.08rem; margin: 0;'>"
            f"📁 {subcategory}</h4></div>",
            unsafe_allow_html=True,
        )

    sorted_goals = sorted(goals, key=lambda g: g.priority)
    for goal in sorted_goals:
        _render_goal_item(repo, goal, is_safety, timeline_map, simulated_map)

    if not is_safety:
        with st.popover(f"➕ Adicionar em {subcategory}", use_container_width=True):
            with st.form(f"fa_{category}_{subcategory}", clear_on_submit=True):
                new_name = st.text_input("Nome", key=f"an_{category}_{subcategory}")
                new_link = st.text_input("Link", key=f"al_{category}_{subcategory}")
                c1, c2 = st.columns(2)
                with c1:
                    new_target = st.number_input("R$", min_value=0.0, step=50.0, key=f"at_{category}_{subcategory}")
                with c2:
                    new_priority = st.number_input("Prio", min_value=1, step=1, key=f"ap_{category}_{subcategory}")
                if st.form_submit_button("Salvar") and new_name and new_target > 0:
                    repo.add_goal(new_name, category, subcategory, new_target, new_priority, new_link)
                    st.rerun()


def _render_category_card(
    repo: FinancialRepository,
    category: str,
    goals: list[Goal],
    timeline_map: dict[int, dict] | None = None,
    simulated_map: dict[int, dict] | None = None,
) -> None:
    """Render a single clean card box for each goal category."""
    is_safety = category == _SAFETY_CATEGORY
    cat_target = sum(g.target_value for g in goals)
    cat_current = sum(g.current_value for g in goals)
    cat_progress = cat_current / cat_target if cat_target > 0 else 0

    with st.expander(f"📄 {category}", expanded=is_safety):
        if is_safety:
            st.toggle(
                "Modo Manutenção na Reserva (Inclui a Mesada)",
                key="toggle_manutencao",
                help=(
                    "Ativado: A meta cresce para cobrir boletos + mesada. "
                    "Desativado: Cobre apenas os boletos básicos."
                ),
            )

        # Header row above main category progress bar, matching 0.82 column ratio for exact right alignment with items!
        col_cat_info, _col_cat_empty = st.columns([0.82, 0.18])
        with col_cat_info:
            st.markdown(
                f"<div style='display: flex; justify-content: space-between; align-items: center; margin-top: 2px; margin-bottom: 6px; width: 100%; box-sizing: border-box;'>"
                f"<div style='display: flex; gap: 8px; flex-wrap: wrap;'>"
                f"<span style='background-color: #D3E0EA; color: #3A5A78; padding: 3px 8px; border-radius: 6px; font-size: 0.8rem;'>{len(goals)} Itens</span>"
                f"<span style='background-color: #D5E4D4; color: #446943; padding: 3px 8px; border-radius: 6px; font-size: 0.8rem;'>{(cat_progress * 100):.1f}% Concluído</span>"
                f"</div>"
                f"<span style='font-size: 0.9rem; color: #37352F; font-weight: 700; white-space: nowrap;'>R$ {cat_current:.2f} / R$ {cat_target:.2f}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

        st.progress(min(cat_progress, 1.0))

        subcategories: dict[str, list[Goal]] = defaultdict(list)
        for goal in goals:
            subcategories[goal.subcategory or "Geral"].append(goal)

        for subcat, sub_goals in subcategories.items():
            _render_subcategory(repo, category, subcat, sub_goals, is_safety, timeline_map, simulated_map)

        if not is_safety:
            st.write("")
            with st.popover(f"➕ Criar nova subcategoria em {category}", use_container_width=True):
                with st.form(f"fns_{category}", clear_on_submit=True):
                    ns_sub = st.text_input("Nova Subcategoria")
                    ns_name = st.text_input("Primeiro Item")
                    ns_link = st.text_input("Link")
                    sc1, sc2 = st.columns(2)
                    with sc1:
                        ns_target = st.number_input("R$", min_value=0.0, step=50.0)
                    with sc2:
                        ns_priority = st.number_input("Prio", min_value=1, step=1)
                    if st.form_submit_button("Criar") and ns_sub and ns_name and ns_target > 0:
                        repo.add_goal(ns_name, category, ns_sub, ns_target, ns_priority, ns_link)
                        st.rerun()


def _render_global_creation_form(repo: FinancialRepository, has_goals: bool) -> None:
    """Global form for creating entirely new category cards — no inner borders."""
    with st.expander(
        "✨ Criar Novo Cartão Principal (Meta Global)", expanded=not has_goals
    ):
        # Form fields without nesting st.form (the wrapper expander IS the visual container)
        c1, c2 = st.columns(2)
        with c1:
            new_category = st.text_input(
                "Meta Principal (Cartão)", placeholder="Ex: Viagens", key="gc_cat"
            )
            new_name = st.text_input("Nome do Item", key="gc_name")
        with c2:
            new_subcategory = st.text_input(
                "Subcategoria", placeholder="Ex: Aéreo", key="gc_sub"
            )
            new_target = st.number_input("Valor Alvo (R$)", step=100.0, key="gc_target")
        new_priority = st.number_input(
            "Prioridade (Não use o 1)", min_value=2, step=1, key="gc_prio"
        )

        if st.button("💾 Salvar na Base", use_container_width=True, key="gc_save"):
            if new_category and new_subcategory and new_name and new_target > 0:
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
            else:
                st.warning("Preencha todos os campos obrigatórios: Meta Principal, Subcategoria, Nome e Valor > 0.")




def _render_contribution_history(
    repo: FinancialRepository,
) -> None:
    """Section: Goal contribution history and average contribution rate."""
    st.markdown("---")
    st.markdown("### Histórico de Aportes em Metas")
    st.caption(
        "Acompanhe o quanto foi **realmente aportado** a cada mês nas metas do casal, "
        "comparado com o planejado pela Cascata."
    )

    contributions = repo.get_all_contributions(months=12)

    if not contributions:
        st.info(
            "Nenhum aporte registrado ainda. "
            "Faça aportes no formulário acima para começar a gerar histórico."
        )
        return

    goals = repo.get_goals()
    goal_name_map = {g.id: g.name for g in goals}

    monthly_totals: dict[str, dict[str, float]] = {}
    for c in contributions:
        if c.month_year not in monthly_totals:
            monthly_totals[c.month_year] = {"planned": 0.0, "actual": 0.0}
        monthly_totals[c.month_year]["planned"] += c.planned_amount
        monthly_totals[c.month_year]["actual"] += c.actual_amount

    sorted_months = sorted(monthly_totals.keys(), reverse=True)

    for month in sorted_months:
        totals = monthly_totals[month]
        with st.expander(f"📅 Aportes de {month}", expanded=(month == sorted_months[0])):
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

            month_contribs = [c for c in contributions if c.month_year == month]
            for c in month_contribs:
                gname = goal_name_map.get(c.goal_id, f"Meta #{c.goal_id}")
                st.markdown(
                    f"  • **{gname}**: Planejado R$ {c.planned_amount:.2f} → "
                    f"Real R$ {c.actual_amount:.2f}"
                )

    if monthly_totals:
        avg_actual = sum(t["actual"] for t in monthly_totals.values()) / len(monthly_totals)
        num_months = len(monthly_totals)
        st.markdown("---")
        st.metric(
            f"Média de Aporte Real Mensal (últimos {num_months} meses)",
            f"R\\$ {avg_actual:.2f}",
        )
        st.caption(
            "Esta média é usada acima para projetar as datas de conclusão dos objetivos."
        )


def render_metas_tab(
    repo: FinancialRepository,
    calc: FinancialCalculator,
    user_a: User,
    user_b: User,
    cost_a: float,
    cost_b: float,
) -> None:
    """Render the complete 🎯 Metas tab."""
    st.subheader("Metas e Aportes")

    _sync_safety_reserve(repo, calc, user_a, user_b, cost_a, cost_b)

    goals = repo.get_goals()

    avg_contribution = _get_avg_monthly_contribution(repo)
    timeline_map: dict[int, dict] = {}

    if goals and avg_contribution > 0:
        timelines = calc.project_goal_timelines(goals, avg_contribution)
        for t in timelines:
            timeline_map[t["goal_id"]] = t

    if goals:
        st.write("")

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
        if st.button("Inserir Aporte 🚀", use_container_width=True):
            old_values = {g.id: g.current_value for g in goals}
            updated = calc.waterfall_allocation(goals, amount)
            repo.update_goals(updated)

            current_month = date.today().strftime("%Y-%m")
            for goal in updated:
                actual_fill = goal.current_value - old_values.get(goal.id, goal.current_value)
                if actual_fill > 0:
                    repo.add_goal_contribution(
                        goal.id, current_month, actual_fill, actual_fill
                    )

            st.success(f"R\\$ {amount:.2f} distribuídos conforme a prioridade!")
            st.rerun()

        st.divider()

        # ── Clean Interactive "E se?" Simulator ──
        simulated_map: dict[int, dict] = {}
        if avg_contribution > 0:
            st.markdown("### Simulador \"E se?\"")
            st.caption("Arraste o slider para simular a aceleração das metas ao aumentar o aporte mensal:")

            extra_sim = st.slider(
                "Aporte Extra Simulado (R$/mês)",
                min_value=0,
                max_value=2000,
                value=300,
                step=50,
                key="what_if_slider",
                help="Arraste para ver a antecipação de meses na conclusão das metas.",
            )

            if extra_sim > 0:
                simulations = calc.simulate_what_if(goals, avg_contribution, float(extra_sim))
                for sim in simulations:
                    simulated_map[sim["goal_id"]] = sim

                st.info(
                    f"⚡ **Aportando +R\\$ {extra_sim:.2f}/mês** (total R\\$ {(avg_contribution + extra_sim):.2f}/mês): "
                    f"As previsões nos cartões abaixo foram recalculadas em tempo real!"
                )

            st.divider()

        st.markdown("### Painel de Metas")

        # ── Wrap in metas-card-wrapper for scoped CSS borders ──
        st.markdown("<div class='metas-card-wrapper'>", unsafe_allow_html=True)

        categories_map: dict[str, list[Goal]] = defaultdict(list)
        for goal in goals:
            categories_map[goal.category].append(goal)

        ordered_categories = list(categories_map.keys())
        if _SAFETY_CATEGORY in ordered_categories:
            ordered_categories.remove(_SAFETY_CATEGORY)
            ordered_categories.insert(0, _SAFETY_CATEGORY)

        for category in ordered_categories:
            _render_category_card(repo, category, categories_map[category], timeline_map, simulated_map)

        st.write("")
        _render_global_creation_form(repo, bool(goals))

        st.markdown("</div>", unsafe_allow_html=True)

    else:
        # No goals yet — show creation form inside wrapper too
        st.markdown("<div class='metas-card-wrapper'>", unsafe_allow_html=True)
        _render_global_creation_form(repo, False)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── History ──
    _render_contribution_history(repo)
