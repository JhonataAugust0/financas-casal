"""Reusable Altair chart builders — pure functions, no Streamlit calls."""

from __future__ import annotations

import altair as alt
import pandas as pd


def build_reserve_comparison_chart(
    survival_value: float,
    maintenance_value: float,
) -> alt.Chart:
    """Horizontal bar chart comparing Survival vs. Maintenance reserve targets."""
    df = pd.DataFrame(
        {
            "Modo": ["1. Sobrevivência", "2. Manutenção"],
            "Valor": [survival_value, maintenance_value],
        }
    )

    return (
        alt.Chart(df)
        .mark_bar(
            size=28,
            cornerRadiusTopRight=4,
            cornerRadiusBottomRight=4,
        )
        .encode(
            x=alt.X("Valor:Q", axis=None),
            y=alt.Y(
                "Modo:N",
                title=None,
                sort="x",
                axis=alt.Axis(
                    labelPadding=5,
                    labelColor="#7A6C68",
                    labelLimit=300,
                    labelFontSize=12,
                ),
            ),
            color=alt.Color(
                "Modo:N",
                scale=alt.Scale(range=["#E2B897", "#88B09F"]),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("Modo:N", title="Cenário"),
                alt.Tooltip("Valor:Q", title="Valor Alvo (R$)", format=",.2f"),
            ],
        )
        .properties(height=130)
        .configure(background="transparent")
        .configure_view(strokeWidth=0)
    )


def build_income_distribution_chart(
    power_separated: float,
    allowance_separated: float,
    power_joint: float,
    allowance_joint: float,
    has_deficit: bool,
) -> alt.Chart:
    """Stacked bar chart: separated vs. joint income distribution."""
    label_sep = (
        "1. Separado (Déficit Oculto)" if has_deficit else "1. Separado"
    )
    label_jun = "2. Junto (Conta Conjunta)"

    chart_data = pd.DataFrame(
        [
            {
                "Cenário": label_sep,
                "Destino do Dinheiro": "1. Poder de Aporte",
                "Valor (R$)": power_separated,
            },
            {
                "Cenário": label_sep,
                "Destino do Dinheiro": "2. Mesadas Garantidas",
                "Valor (R$)": allowance_separated,
            },
            {
                "Cenário": label_jun,
                "Destino do Dinheiro": "1. Poder de Aporte",
                "Valor (R$)": power_joint,
            },
            {
                "Cenário": label_jun,
                "Destino do Dinheiro": "2. Mesadas Garantidas",
                "Valor (R$)": allowance_joint,
            },
        ]
    )

    return (
        alt.Chart(chart_data)
        .mark_bar(size=40, cornerRadiusTopRight=2, cornerRadiusBottomRight=2)
        .encode(
            x=alt.X(
                "sum(Valor (R$)):Q",
                title="Distribuição do Dinheiro (O valor total do casal é o mesmo)",
                axis=alt.Axis(grid=False),
            ),
            y=alt.Y(
                "Cenário:N",
                title=None,
                axis=alt.Axis(labelAngle=0, labelPadding=10),
            ),
            color=alt.Color(
                "Destino do Dinheiro:N",
                scale=alt.Scale(range=["#88B09F", "#E2B897"]),
                legend=alt.Legend(orient="bottom", title=None),
            ),
            tooltip=["Cenário", "Destino do Dinheiro", "Valor (R$)"],
        )
        .properties(height=250)
        .configure(background="transparent")
        .configure_view(strokeWidth=0)
        .configure_axis(
            labelColor="#7A6C68",
            titleColor="#7A6C68",
            domainColor="#D7CFCB",
            tickColor="#D7CFCB",
        )
    )
