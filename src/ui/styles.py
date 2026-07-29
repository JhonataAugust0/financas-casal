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

        /* ── Seamless Expander: Nuke ALL box styling with wildcard ── */
        [data-testid="stExpander"],
        [data-testid="stExpander"] > *,
        [data-testid="stExpander"] > * > *,
        [data-testid="stExpander"] details,
        [data-testid="stExpander"] details > * {
            background-color: transparent !important;
            background: transparent !important;
            border: 0 none transparent !important;
            border-radius: 0 !important;
            box-shadow: none !important;
            outline: none !important;
        }
        [data-testid="stExpander"] {
            border-bottom: 1px solid #EAE0D5 !important;
            margin-bottom: 20px;
            padding-bottom: 4px;
        }
        [data-testid="stExpander"]:hover {
            box-shadow: none !important;
        }
        [data-testid="stExpander"] summary,
        [data-testid="stExpander"] details summary,
        [data-testid="stExpander"] details > summary {
            background-color: transparent !important;
            background: transparent !important;
            border: 0 none transparent !important;
            color: #37352F !important;
            font-size: 1.6rem !important;
            font-weight: 700 !important;
            padding: 1.1rem 0rem !important;
            cursor: pointer;
        }
        [data-testid="stExpander"] summary:hover,
        [data-testid="stExpander"] details summary:hover {
            background-color: transparent !important;
            background: transparent !important;
            color: #E2858E !important;
        }

        /* ── Seamless Item Header ── */
        .expense-item-seamless {
            background-color: transparent;
            border-bottom: 1px solid #F0ECE9;
            padding: 6px 0px;
            margin-bottom: 6px;
        }

        /* ── Mobile responsiveness adjustments ── */
        @media (max-width: 640px) {
            .stApp { padding-left: 0.5rem; padding-right: 0.5rem; }
            .stTabs [data-baseweb="tab-list"] { gap: 8px; }
            .stTabs [data-baseweb="tab"] { font-size: 0.85rem; height: 42px; padding: 4px 8px; }
            [data-testid="stExpander"] summary,
            [data-testid="stExpander"] details summary {
                font-size: 1.35rem !important;
                padding: 0.7rem 0rem !important;
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
