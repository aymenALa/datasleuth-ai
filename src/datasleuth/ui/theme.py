"""Design system tokens and scoped CSS styling for DataSleuth AI."""

from __future__ import annotations

import streamlit as st

# Design system tokens
CANVAS_BG = "#0B1120"
SIDEBAR_BG = "#111827"
SURFACE_PRIMARY = "#111827"
SURFACE_ELEVATED = "#162033"
BORDER_COLOR = "#263449"
PRIMARY_ACTION = "#2563EB"
INTERACTIVE_ACCENT = "#38BDF8"
TEXT_PRIMARY = "#F1F5F9"
TEXT_SECONDARY = "#94A3B8"
TEXT_MUTED = "#64748B"
SUCCESS = "#34D399"
WARNING = "#F59E0B"
ERROR = "#F87171"
EVIDENCE_ACCENT = "#818CF8"


def inject_custom_styles() -> None:
    """Inject scoped CSS matching the enterprise analytics design direction."""
    st.markdown(
        f"""
        <style>
        /* Base application styling */
        .stApp {{
            background-color: {CANVAS_BG};
            color: {TEXT_PRIMARY};
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }}

        /* Main content container */
        .block-container {{
            max-width: 1280px;
            padding-top: 1.25rem;
            padding-bottom: 3rem;
            padding-left: 2rem;
            padding-right: 2rem;
        }}

        /* Headings & typography */
        h1 {{
            color: {TEXT_PRIMARY} !important;
            font-size: 2.1rem !important;
            font-weight: 700 !important;
            letter-spacing: -0.03em !important;
            margin-bottom: 0.35rem !important;
        }}
        h2, h3 {{
            color: {TEXT_PRIMARY} !important;
            letter-spacing: -0.02em !important;
            font-weight: 600 !important;
            margin-top: 1.1rem !important;
            margin-bottom: 0.6rem !important;
        }}
        .ds-kicker {{
            color: {INTERACTIVE_ACCENT};
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            margin-bottom: 0.2rem;
        }}
        .ds-subtitle {{
            color: {TEXT_SECONDARY};
            font-size: 0.95rem;
            line-height: 1.4;
            margin-top: -0.3rem;
            margin-bottom: 1.2rem;
        }}

        /* Sidebar styling */
        [data-testid="stSidebar"] {{
            background-color: {SIDEBAR_BG};
            border-right: 1px solid {BORDER_COLOR};
        }}
        [data-testid="stSidebar"] .block-container {{
            padding-top: 1.5rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }}
        .ds-sidebar-brand {{
            font-size: 1.18rem;
            font-weight: 700;
            color: {TEXT_PRIMARY};
            letter-spacing: -0.02em;
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 0.15rem;
        }}
        .ds-sidebar-brand-icon {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 28px;
            height: 28px;
            background: rgba(37, 99, 235, 0.18);
            border: 1px solid rgba(56, 189, 248, 0.35);
            border-radius: 7px;
            color: #38BDF8;
        }}
        .ds-sidebar-sub {{
            font-size: 0.72rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: {TEXT_SECONDARY};
            margin-bottom: 1rem;
        }}

        /* Sidebar Navigation Items - Enterprise Linear/Vercel Button Aesthetic */
        [data-testid="stSidebar"] div.stButton {{
            margin: 0 !important;
            margin-bottom: 2px !important;
            width: 100% !important;
        }}
        [data-testid="stSidebar"] div.stButton > button {{
            height: 42px !important;
            min-height: 42px !important;
            max-height: 42px !important;
            width: 100% !important;
            display: flex !important;
            align-items: center !important;
            justify-content: flex-start !important;
            padding: 0 16px !important;
            border-radius: 7px !important;
            font-size: 14px !important;
            font-weight: 500 !important;
            text-align: left !important;
            transition: all 0.15s ease-in-out !important;
            cursor: pointer !important;
        }}

        /* Force Streamlit button internal flex containers to stretch and left-align */
        [data-testid="stSidebar"] div.stButton > button > div {{
            width: 100% !important;
            max-width: 100% !important;
            flex: 1 1 100% !important;
            display: flex !important;
            justify-content: flex-start !important;
            align-items: center !important;
            text-align: left !important;
        }}
        [data-testid="stSidebar"] div.stButton > button > div > span {{
            width: 100% !important;
            max-width: 100% !important;
            flex: 1 1 100% !important;
            display: flex !important;
            justify-content: flex-start !important;
            align-items: center !important;
            gap: 12px !important;
        }}

        /* Fixed 18px icon container starting at exactly 16px from button edge */
        [data-testid="stSidebar"] div.stButton > button span:has(> span[data-testid="stIconMaterial"]),
        [data-testid="stSidebar"] div.stButton > button span[data-testid="stIconMaterial"] {{
            width: 18px !important;
            min-width: 18px !important;
            max-width: 18px !important;
            height: 18px !important;
            min-height: 18px !important;
            max-height: 18px !important;
            font-size: 18px !important;
            line-height: 18px !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            flex-shrink: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
        }}

        /* Label container: 14px typography, left-aligned label text and right-aligned badge */
        [data-testid="stSidebar"] div.stButton > button [data-testid="stMarkdownContainer"] {{
            flex: 1 1 auto !important;
            width: 100% !important;
            display: flex !important;
            align-items: center !important;
            justify-content: space-between !important;
            text-align: left !important;
        }}
        [data-testid="stSidebar"] div.stButton > button [data-testid="stMarkdownContainer"] > p {{
            font-size: 14px !important;
            font-weight: 500 !important;
            line-height: 1.2 !important;
            margin: 0 !important;
            padding: 0 !important;
            width: 100% !important;
            display: flex !important;
            align-items: center !important;
            justify-content: space-between !important;
            text-align: left !important;
        }}

        /* Inactive Navigation Destination */
        [data-testid="stSidebar"] div.stButton > button[kind="secondary"] {{
            background: transparent !important;
            border: 1px solid transparent !important;
            color: #94A3B8 !important;
            box-shadow: none !important;
        }}
        [data-testid="stSidebar"] div.stButton > button[kind="secondary"] span,
        [data-testid="stSidebar"] div.stButton > button[kind="secondary"] p {{
            color: #94A3B8 !important;
        }}
        /* Inactive Hover State */
        [data-testid="stSidebar"] div.stButton > button[kind="secondary"]:hover {{
            background: rgba(255, 255, 255, 0.05) !important;
            border-color: rgba(255, 255, 255, 0.08) !important;
        }}
        [data-testid="stSidebar"] div.stButton > button[kind="secondary"]:hover span,
        [data-testid="stSidebar"] div.stButton > button[kind="secondary"]:hover p {{
            color: #F1F5F9 !important;
        }}

        /* Active Navigation Destination */
        [data-testid="stSidebar"] div.stButton > button[kind="primary"] {{
            background: rgba(37, 99, 235, 0.16) !important;
            border: 1px solid rgba(56, 189, 248, 0.32) !important;
            box-shadow: 0 1px 4px rgba(0, 0, 0, 0.25) !important;
        }}
        [data-testid="stSidebar"] div.stButton > button[kind="primary"] span,
        [data-testid="stSidebar"] div.stButton > button[kind="primary"] p {{
            color: #38BDF8 !important;
            font-weight: 600 !important;
        }}

        /* Accessible Keyboard Focus Visible */
        [data-testid="stSidebar"] div.stButton > button:focus-visible {{
            outline: 2px solid #38BDF8 !important;
            outline-offset: 1px !important;
        }}

        /* Streamlit Top Header Bar - Non-intrusive */
        [data-testid="stHeader"] {{
            background: transparent !important;
            height: 2.5rem !important;
            z-index: 90 !important;
        }}

        /* Optimized Desktop Content Margins & Reading Width */
        .block-container {{
            padding-top: 3.5rem !important;
            padding-bottom: 3.5rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
            max-width: 1400px !important;
            margin-left: auto !important;
            margin-right: auto !important;
        }}

        /* Status indicator pill */
        .ds-status-pill {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 12px;
            border-radius: 9999px;
            font-size: 0.78rem;
            font-weight: 600;
            letter-spacing: 0.02em;
            user-select: none;
        }}

        /* Metric cards */
        [data-testid="stMetric"] {{
            background: {SURFACE_PRIMARY};
            border: 1px solid {BORDER_COLOR};
            border-radius: 10px;
            padding: 0.85rem 1.15rem;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
            transition: border-color 0.15s ease-in-out;
        }}
        [data-testid="stMetric"]:hover {{
            border-color: #3B82F6;
        }}
        [data-testid="stMetricLabel"] {{
            color: {TEXT_SECONDARY} !important;
            font-size: 0.82rem !important;
            font-weight: 500 !important;
            letter-spacing: 0.02em !important;
        }}
        [data-testid="stMetricValue"] {{
            color: {TEXT_PRIMARY} !important;
            font-size: 1.55rem !important;
            font-weight: 700 !important;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace !important;
        }}

        /* Tabs styling */
        button[data-baseweb="tab"] {{
            color: {TEXT_SECONDARY} !important;
            font-size: 0.88rem !important;
            font-weight: 500 !important;
            padding: 8px 16px !important;
        }}
        button[data-baseweb="tab"][aria-selected="true"] {{
            color: {INTERACTIVE_ACCENT} !important;
            font-weight: 600 !important;
            border-bottom-color: {PRIMARY_ACTION} !important;
        }}

        /* Expanders */
        div[data-testid="stExpander"] {{
            background: {SURFACE_PRIMARY};
            border: 1px solid {BORDER_COLOR};
            border-radius: 10px;
            margin-bottom: 0.6rem;
        }}
        div[data-testid="stExpander"] summary {{
            color: #E2E8F0 !important;
            font-weight: 600 !important;
            font-size: 0.92rem !important;
        }}

        /* Buttons */
        .stButton > button[kind="primary"] {{
            background-color: {PRIMARY_ACTION} !important;
            border: 1px solid #3B82F6 !important;
            border-radius: 8px !important;
            color: #FFFFFF !important;
            font-size: 0.95rem !important;
            font-weight: 600 !important;
            padding: 0.55rem 1.25rem !important;
            box-shadow: 0 2px 6px rgba(37, 99, 235, 0.3) !important;
            transition: all 0.15s ease-in-out !important;
        }}
        .stButton > button[kind="primary"]:hover {{
            background-color: #1D4ED8 !important;
            border-color: #60A5FA !important;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.45) !important;
        }}
        [data-testid="stDownloadButton"] > button {{
            background-color: {SURFACE_ELEVATED} !important;
            border: 1px solid {BORDER_COLOR} !important;
            border-radius: 8px !important;
            color: #E2E8F0 !important;
            font-size: 0.9rem !important;
            font-weight: 600 !important;
            transition: all 0.15s ease-in-out !important;
        }}
        [data-testid="stDownloadButton"] > button:hover {{
            background-color: #1E293B !important;
            border-color: {INTERACTIVE_ACCENT} !important;
            color: #FFFFFF !important;
        }}

        /* Badges & tags */
        .ds-badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.72rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }}
        .ds-badge-fact {{
            background: rgba(56, 189, 248, 0.14);
            color: {INTERACTIVE_ACCENT};
            border: 1px solid rgba(56, 189, 248, 0.3);
        }}
        .ds-badge-candidate {{
            background: rgba(245, 158, 11, 0.14);
            color: {WARNING};
            border: 1px solid rgba(245, 158, 11, 0.3);
        }}
        .ds-badge-confidence {{
            background: rgba(129, 140, 248, 0.14);
            color: {EVIDENCE_ACCENT};
            border: 1px solid rgba(129, 140, 248, 0.3);
        }}
        .ds-col-tag {{
            display: inline-block;
            background: #1E293B;
            color: #E2E8F0;
            padding: 2px 7px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 0.8rem;
            border: 1px solid #334155;
            margin: 2px;
        }}

        /* Clean cards */
        .ds-card {{
            background: {SURFACE_PRIMARY};
            border: 1px solid {BORDER_COLOR};
            border-radius: 10px;
            padding: 1rem 1.25rem;
            margin-bottom: 0.85rem;
        }}
        .ds-empty-state {{
            background: {SURFACE_PRIMARY};
            border: 1px dashed {BORDER_COLOR};
            border-radius: 10px;
            padding: 2.5rem 1.5rem;
            text-align: center;
            margin: 1rem 0;
        }}
        .ds-empty-state-title {{
            font-size: 1.05rem;
            font-weight: 600;
            color: {TEXT_PRIMARY};
            margin-bottom: 0.4rem;
        }}
        .ds-empty-state-desc {{
            font-size: 0.88rem;
            color: {TEXT_SECONDARY};
            max-width: 500px;
            margin: 0 auto;
        }}

        /* Recommendations grid */
        .ds-recom-grid {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 8px;
            margin-top: 8px;
        }}
        @media (min-width: 768px) {{
            .ds-recom-grid {{
                grid-template-columns: 1fr 1fr;
            }}
        }}
        .ds-recom-item {{
            background: {SURFACE_ELEVATED};
            border: 1px solid #202F48;
            border-radius: 6px;
            padding: 8px 12px;
        }}
        .ds-recom-label {{
            color: {TEXT_SECONDARY};
            font-size: 0.74rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.03em;
            margin-bottom: 2px;
        }}
        .ds-recom-val {{
            color: #E2E8F0;
            font-size: 0.86rem;
            line-height: 1.35;
        }}

        /* Model interpretation container */
        .ds-model-interpretation {{
            background: {SURFACE_PRIMARY};
            border: 1px solid {BORDER_COLOR};
            border-left: 3px solid {INTERACTIVE_ACCENT};
            border-radius: 8px;
            padding: 1.2rem 1.4rem;
            margin: 1rem 0;
            color: #E2E8F0;
            font-size: 0.92rem;
            line-height: 1.55;
        }}
        .ds-model-disclaimer {{
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 0.8rem;
            font-weight: 700;
            color: {INTERACTIVE_ACCENT};
            letter-spacing: 0.03em;
            text-transform: uppercase;
            margin-bottom: 0.75rem;
        }}

        /* Responsive overrides */
        @media (max-width: 768px) {{
            .block-container {{
                padding-left: 1rem;
                padding-right: 1rem;
            }}
            h1 {{
                font-size: 1.6rem !important;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
