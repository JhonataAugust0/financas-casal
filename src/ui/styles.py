"""Isolated CSS injection for the Streamlit app."""

import streamlit as st


def inject_custom_css() -> None:
    """Inject the custom CSS theme into the Streamlit page."""
    st.markdown(
        """
    <style>
        .stApp { background-color: #FAF8F5; }

        /* ── Tabs ── */
        .stTabs [data-baseweb="tab-list"] { gap: 16px; flex-wrap: wrap; }
        .stTabs [data-baseweb="tab"] {
            height: 48px; white-space: pre-wrap; background-color: transparent;
            border-radius: 4px 4px 0 0; gap: 4px; padding-top: 8px;
            padding-bottom: 8px; color: #7A6C68; font-size: 0.95rem;
        }
        .stTabs [aria-selected="true"] {
            background-color: transparent; color: #E2858E !important;
            border-bottom-color: #E2858E !important; font-weight: 700;
        }
        [data-testid="stMetricValue"] { color: #597E52; font-weight: 700; }
        [data-testid="stDataFrame"] {
            border-radius: 8px; overflow: hidden;
            border: 1px solid #F0ECE9;
        }

        /* ── Expanders — Globally transparent (no box), with internal spacing ── */
        [data-testid="stExpander"] {
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
            margin-bottom: 12px !important;
        }
        [data-testid="stExpander"] details summary {
            background-color: transparent !important;
            font-size: 1.15rem !important;
            font-weight: 700 !important;
            color: #37352F !important;
            padding: 0.5rem 0.8rem !important;
            margin-bottom: 0px !important;
        }
        [data-testid="stExpander"] details summary:hover {
            color: #E2858E !important;
        }
        [data-testid="stExpander"] details > div {
            padding: 0.4rem 1rem 1rem 1rem !important;
        }

        /* ── Metas Card Wrapper — Bordered expanders ONLY inside metas ── */
        .metas-card-wrapper [data-testid="stExpander"] {
            background-color: #FFFFFF !important;
            border: 1px solid #E2D9CF !important;
            border-radius: 12px !important;
            box-shadow: 0 1px 4px rgba(0,0,0,0.04) !important;
            margin-bottom: 20px !important;
            overflow: hidden !important;
        }
        .metas-card-wrapper [data-testid="stExpander"] details summary {
            padding: 0.7rem 1rem !important;
            font-size: 1.25rem !important;
        }
        .metas-card-wrapper [data-testid="stExpander"] details > div {
            padding: 0.4rem 1.2rem 1.2rem 1.2rem !important;
        }

        /* ── Remove inner form borders inside metas cards ── */
        .metas-card-wrapper [data-testid="stForm"] {
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
        }

        /* ── Seamless expense item separator ── */
        .expense-item-seamless {
            background-color: transparent;
            border-bottom: 1px solid #F0ECE9;
            padding: 10px 0px 6px 0px;
            margin-bottom: 4px;
        }

        /* ── Recurrence badge ── */
        .badge-recurrence {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            background-color: #FEF3C7;
            color: #92400E;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.72rem;
            font-weight: 600;
            white-space: nowrap;
        }

        /* ── Mobile responsiveness adjustments ── */
        @media (max-width: 640px) {
            .stApp { padding-left: 0.5rem; padding-right: 0.5rem; }
            .stTabs [data-baseweb="tab-list"] { gap: 8px; }
            .stTabs [data-baseweb="tab"] { font-size: 0.85rem; height: 42px; padding: 4px 8px; }
            [data-testid="stExpander"] details summary {
                padding: 0.5rem 0.6rem !important;
            }
            [data-testid="stExpander"] details > div {
                padding: 0.3rem 0.6rem 0.8rem 0.6rem !important;
            }
            .metas-card-wrapper [data-testid="stExpander"] details summary {
                font-size: 1.1rem !important;
                padding: 0.5rem 0.8rem !important;
            }
            .metas-card-wrapper [data-testid="stExpander"] details > div {
                padding: 0.3rem 0.8rem 0.8rem 0.8rem !important;
            }
            [data-testid="stPopover"] button {
                width: 100% !important;
                min-height: 40px !important;
            }
            .stButton button {
                border-radius: 8px !important;
            }
        }
    </style>
    """,
        unsafe_allow_html=True,
    )
