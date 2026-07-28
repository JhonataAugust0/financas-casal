"""Isolated CSS injection for the Streamlit app."""

import streamlit as st


def inject_custom_css() -> None:
    """Inject the custom CSS theme into the Streamlit page."""
    st.markdown(
        """
    <style>
        .stApp { background-color: #FAF8F5; }
        .stTabs [data-baseweb="tab-list"] { gap: 24px; }
        .stTabs [data-baseweb="tab"] {
            height: 50px; white-space: pre-wrap; background-color: transparent;
            border-radius: 4px 4px 0 0; gap: 1px; padding-top: 10px;
            padding-bottom: 10px; color: #7A6C68;
        }
        .stTabs [aria-selected="true"] {
            background-color: transparent; color: #E2858E !important;
            border-bottom-color: #E2858E !important;
        }
        [data-testid="stMetricValue"] { color: #597E52; font-weight: 700; }
        [data-testid="stDataFrame"] {
            border-radius: 8px; overflow: hidden;
            border: 1px solid #F0ECE9;
        }

        /* Expander / Notion-style card */
        [data-testid="stExpander"] {
            background-color: #F8F3ED !important;
            border: 1px solid #EAE0D5 !important;
            border-radius: 12px !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.04) !important;
            transition: all 0.2s ease-in-out;
            margin-bottom: 16px;
        }
        [data-testid="stExpander"]:hover {
            box-shadow: 0 4px 8px rgba(0,0,0,0.08) !important;
            border-color: #DCD0C3 !important;
        }
        [data-testid="stExpander"] details summary {
            background-color: transparent !important;
            color: #37352F !important;
            font-size: 1.15rem !important;
            font-weight: 600 !important;
            padding: 1.2rem 1rem !important;
        }
        [data-testid="stExpander"] details summary:hover {
            background-color: #F2EBE1 !important;
            border-radius: 12px !important;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )
