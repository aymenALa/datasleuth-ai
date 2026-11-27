"""Design system tokens and scoped CSS styling for DataSleuth AI."""

from __future__ import annotations

import streamlit as st

# Design system tokens (DataSleuth AI Portfolio Cover Palette)
CANVAS_BG = "#050C19"
SIDEBAR_BG = "#081223"
SURFACE_PRIMARY = "#101E31"
SURFACE_ELEVATED = "#15263E"
BORDER_COLOR = "#1E3352"
PRIMARY_ACTION = "#0891B2"
PRIMARY_CYAN = "#22D3EE"
INTERACTIVE_ACCENT = "#38BDF8"
TEXT_PRIMARY = "#F1F5F9"
TEXT_SECONDARY = "#94A3B8"
TEXT_MUTED = "#64748B"
SUCCESS = "#2DD4BF"
WARNING = "#F59E0B"
ERROR = "#F87171"
EVIDENCE_ACCENT = "#818CF8"


def inject_custom_styles(hide_sidebar: bool = False) -> None:
    """Inject scoped CSS matching the DataSleuth AI midnight-cyan design system."""
    sidebar_hide_css = (
        """
        [data-testid="stSidebar"],
        [data-testid="collapsedControl"],
        [data-testid="stSidebarCollapsedControl"] {
            display: none !important;
        }
        """
        if hide_sidebar
        else ""
    )
    st.markdown(
        f"""
        <style>
        {sidebar_hide_css}
        /* Hide unnecessary deployment chrome */
        [data-testid="stAppDeployButton"] {{
            display: none !important;
        }}
        /* Base application styling with subtle background grid & ambient glow */
        .stApp {{
            background-color: {CANVAS_BG};
            background-image:
                radial-gradient(ellipse 80% 45% at 50% -10%, rgba(34, 211, 238, 0.12), transparent 65%),
                linear-gradient(to right, rgba(34, 211, 238, 0.035) 1px, transparent 1px),
                linear-gradient(to bottom, rgba(34, 211, 238, 0.035) 1px, transparent 1px);
            background-size: 100% 100%, 36px 36px, 36px 36px;
            color: {TEXT_PRIMARY};
            font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }}

        /* Main content container */
        .block-container {{
            padding-top: 2.75rem !important;
            padding-bottom: 3.5rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
            max-width: 1360px !important;
            margin-left: auto !important;
            margin-right: auto !important;
        }}

        /* Headings & typography */
        h1 {{
            color: {TEXT_PRIMARY} !important;
            font-size: 2.1rem !important;
            font-weight: 750 !important;
            letter-spacing: -0.03em !important;
            margin-bottom: 0.35rem !important;
        }}
        h2, h3 {{
            color: {TEXT_PRIMARY} !important;
            letter-spacing: -0.02em !important;
            font-weight: 650 !important;
            margin-top: 1.1rem !important;
            margin-bottom: 0.6rem !important;
        }}
        .ds-kicker {{
            color: {PRIMARY_CYAN};
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            margin-bottom: 0.2rem;
        }}
        .ds-subtitle {{
            color: {TEXT_SECONDARY};
            font-size: 0.95rem;
            line-height: 1.45;
            margin-top: -0.25rem;
            margin-bottom: 1.1rem;
        }}

        /* Sidebar styling */
        [data-testid="stSidebar"] {{
            background-color: {SIDEBAR_BG};
            border-right: 1px solid {BORDER_COLOR};
        }}
        [data-testid="stSidebar"] .block-container {{
            padding-top: 1.4rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }}
        .ds-sidebar-brand {{
            font-size: 1.15rem;
            font-weight: 700;
            color: {TEXT_PRIMARY};
            letter-spacing: -0.02em;
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 0.15rem;
        }}
        .ds-sidebar-sub {{
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 0.68rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: {TEXT_SECONDARY};
            margin-bottom: 0.9rem;
        }}

        /* Sidebar Navigation Items */
        [data-testid="stSidebar"] div.stButton {{
            margin: 0 !important;
            margin-bottom: 2px !important;
            width: 100% !important;
        }}
        [data-testid="stSidebar"] div.stButton > button {{
            height: 40px !important;
            min-height: 40px !important;
            max-height: 40px !important;
            width: 100% !important;
            display: flex !important;
            align-items: center !important;
            justify-content: flex-start !important;
            padding: 0 14px !important;
            border-radius: 8px !important;
            font-size: 13.5px !important;
            font-weight: 500 !important;
            text-align: left !important;
            transition: all 0.15s ease-in-out !important;
            cursor: pointer !important;
        }}
        [data-testid="stSidebar"] div.stButton > button > div {{
            width: 100% !important;
            flex: 1 1 100% !important;
            display: flex !important;
            justify-content: flex-start !important;
            align-items: center !important;
            text-align: left !important;
        }}
        [data-testid="stSidebar"] div.stButton > button > div > span {{
            width: 100% !important;
            flex: 1 1 100% !important;
            display: flex !important;
            justify-content: flex-start !important;
            align-items: center !important;
            gap: 10px !important;
        }}
        [data-testid="stSidebar"] div.stButton > button span:has(> span[data-testid="stIconMaterial"]),
        [data-testid="stSidebar"] div.stButton > button span[data-testid="stIconMaterial"] {{
            width: 18px !important;
            min-width: 18px !important;
            max-width: 18px !important;
            height: 18px !important;
            font-size: 18px !important;
            line-height: 18px !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            flex-shrink: 0 !important;
            margin: 0 !important;
        }}
        [data-testid="stSidebar"] div.stButton > button [data-testid="stMarkdownContainer"] {{
            flex: 1 1 auto !important;
            width: 100% !important;
            display: flex !important;
            align-items: center !important;
            justify-content: space-between !important;
        }}
        [data-testid="stSidebar"] div.stButton > button [data-testid="stMarkdownContainer"] > p {{
            font-size: 13.5px !important;
            font-weight: 500 !important;
            line-height: 1.2 !important;
            margin: 0 !important;
            width: 100% !important;
            display: flex !important;
            align-items: center !important;
            justify-content: space-between !important;
        }}
        [data-testid="stSidebar"] div.stButton > button[kind="secondary"] {{
            background: transparent !important;
            border: 1px solid transparent !important;
            color: {TEXT_SECONDARY} !important;
            box-shadow: none !important;
        }}
        [data-testid="stSidebar"] div.stButton > button[kind="secondary"] span,
        [data-testid="stSidebar"] div.stButton > button[kind="secondary"] p {{
            color: {TEXT_SECONDARY} !important;
        }}
        [data-testid="stSidebar"] div.stButton > button[kind="secondary"]:hover {{
            background: rgba(34, 211, 238, 0.06) !important;
            border-color: rgba(34, 211, 238, 0.15) !important;
        }}
        [data-testid="stSidebar"] div.stButton > button[kind="secondary"]:hover span,
        [data-testid="stSidebar"] div.stButton > button[kind="secondary"]:hover p {{
            color: {TEXT_PRIMARY} !important;
        }}
        [data-testid="stSidebar"] div.stButton > button[kind="primary"] {{
            background: linear-gradient(90deg, rgba(34, 211, 238, 0.14), rgba(56, 189, 248, 0.08)) !important;
            border: 1px solid rgba(34, 211, 238, 0.38) !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25) !important;
        }}
        [data-testid="stSidebar"] div.stButton > button[kind="primary"] span,
        [data-testid="stSidebar"] div.stButton > button[kind="primary"] p {{
            color: {PRIMARY_CYAN} !important;
            font-weight: 600 !important;
        }}
        [data-testid="stSidebar"] div.stButton > button:focus-visible {{
            outline: 2px solid {PRIMARY_CYAN} !important;
            outline-offset: 1px !important;
        }}

        /* Streamlit Top Header Bar */
        [data-testid="stHeader"] {{
            background: transparent !important;
            height: 2.5rem !important;
            z-index: 90 !important;
        }}

        /* Status indicator pill */
        .ds-status-pill {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 12px;
            border-radius: 9999px;
            font-size: 0.76rem;
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
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.22);
            transition: border-color 0.15s ease-in-out;
        }}
        [data-testid="stMetric"]:hover {{
            border-color: {PRIMARY_CYAN};
        }}
        [data-testid="stMetricLabel"] {{
            color: {TEXT_SECONDARY} !important;
            font-size: 0.8rem !important;
            font-weight: 500 !important;
        }}
        [data-testid="stMetricValue"] {{
            color: {TEXT_PRIMARY} !important;
            font-size: 1.5rem !important;
            font-weight: 700 !important;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace !important;
        }}

        /* Tabs styling */
        button[data-baseweb="tab"] {{
            color: {TEXT_SECONDARY} !important;
            font-size: 0.88rem !important;
            font-weight: 500 !important;
            padding: 8px 16px !important;
        }}
        button[data-baseweb="tab"][aria-selected="true"] {{
            color: {PRIMARY_CYAN} !important;
            font-weight: 600 !important;
            border-bottom-color: {PRIMARY_CYAN} !important;
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

        /* Primary & Download Buttons */
        .stButton > button[kind="primary"] {{
            background: linear-gradient(135deg, #0891B2, #0284C7) !important;
            border: 1px solid rgba(34, 211, 238, 0.45) !important;
            border-radius: 8px !important;
            color: #FFFFFF !important;
            font-size: 0.92rem !important;
            font-weight: 600 !important;
            padding: 0.5rem 1.15rem !important;
            box-shadow: 0 4px 14px rgba(8, 145, 178, 0.28) !important;
            transition: all 0.15s ease-in-out !important;
        }}
        .stButton > button[kind="primary"]:hover {{
            background: linear-gradient(135deg, #06B6D4, #0EA5E9) !important;
            border-color: {PRIMARY_CYAN} !important;
            box-shadow: 0 6px 18px rgba(34, 211, 238, 0.35) !important;
        }}
        [data-testid="stDownloadButton"] > button {{
            background-color: {SURFACE_ELEVATED} !important;
            border: 1px solid {BORDER_COLOR} !important;
            border-radius: 8px !important;
            color: #E2E8F0 !important;
            font-size: 0.88rem !important;
            font-weight: 600 !important;
            transition: all 0.15s ease-in-out !important;
        }}
        [data-testid="stDownloadButton"] > button:hover {{
            background-color: #1A2F4C !important;
            border-color: {PRIMARY_CYAN} !important;
            color: #FFFFFF !important;
        }}

        /* Badges & tags */
        .ds-badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 0.69rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }}
        .ds-badge-fact {{
            background: rgba(34, 211, 238, 0.12);
            color: {PRIMARY_CYAN};
            border: 1px solid rgba(34, 211, 238, 0.32);
        }}
        .ds-badge-candidate {{
            background: rgba(245, 158, 11, 0.14);
            color: {WARNING};
            border: 1px solid rgba(245, 158, 11, 0.32);
        }}
        .ds-badge-confidence {{
            background: rgba(45, 212, 191, 0.12);
            color: {SUCCESS};
            border: 1px solid rgba(45, 212, 191, 0.3);
        }}
        .ds-col-tag {{
            display: inline-block;
            background: {SURFACE_ELEVATED};
            color: #E2E8F0;
            padding: 2px 7px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 0.8rem;
            border: 1px solid {BORDER_COLOR};
            margin: 2px;
        }}

        /* Cards & Empty States */
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
            border: 1px solid {BORDER_COLOR};
            border-radius: 6px;
            padding: 8px 12px;
        }}
        .ds-recom-label {{
            color: {TEXT_SECONDARY};
            font-size: 0.72rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.04em;
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
            border-left: 3px solid {PRIMARY_CYAN};
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
            color: {PRIMARY_CYAN};
            letter-spacing: 0.03em;
            text-transform: uppercase;
            margin-bottom: 0.75rem;
        }}

        /* ================= LANDING PAGE STYLES ================= */
        .ds-landing-nav {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 12px;
            padding: 0.75rem 1.15rem;
            background: rgba(16, 30, 49, 0.78);
            border: 1px solid {BORDER_COLOR};
            border-radius: 12px;
            backdrop-filter: blur(8px);
            margin-bottom: 2rem;
        }}
        .ds-landing-nav-brand {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .ds-brand-title {{
            display: block;
            font-weight: 700;
            font-size: 1rem;
            color: {TEXT_PRIMARY};
            line-height: 1.1;
        }}
        .ds-brand-tag {{
            display: block;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 0.68rem;
            color: {PRIMARY_CYAN};
        }}
        .ds-landing-nav-links {{
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 18px;
            font-size: 0.85rem;
        }}
        .ds-landing-nav-links a {{
            color: {TEXT_SECONDARY};
            text-decoration: none;
            font-weight: 500;
            transition: color 0.15s ease;
        }}
        .ds-landing-nav-links a:hover {{
            color: {PRIMARY_CYAN};
        }}
        .ds-nav-gh {{
            padding: 5px 11px;
            border: 1px solid {BORDER_COLOR};
            border-radius: 7px;
            background: {SURFACE_ELEVATED};
            color: {TEXT_PRIMARY} !important;
        }}

        .ds-hero {{
            text-align: center;
            max-width: 820px;
            margin: 0 auto 2.25rem auto;
            padding: 0.5rem 0;
        }}
        .ds-hero-badge {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 5px 14px;
            border-radius: 999px;
            background: rgba(34, 211, 238, 0.08);
            border: 1px solid rgba(34, 211, 238, 0.28);
            color: {PRIMARY_CYAN};
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 0.72rem;
            font-weight: 600;
            letter-spacing: 0.08em;
            margin-bottom: 1.15rem;
        }}
        .ds-pulse-dot {{
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: {SUCCESS};
            display: inline-block;
        }}
        .ds-hero-title {{
            font-size: clamp(2.2rem, 5vw, 3.5rem) !important;
            line-height: 1.08 !important;
            font-weight: 800 !important;
            letter-spacing: -0.035em !important;
            color: {TEXT_PRIMARY} !important;
            margin-bottom: 1rem !important;
        }}
        .ds-hero-gradient {{
            background: linear-gradient(95deg, {PRIMARY_CYAN}, {INTERACTIVE_ACCENT}, {SUCCESS});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .ds-hero-subtitle {{
            font-size: 1.05rem;
            line-height: 1.6;
            color: {TEXT_SECONDARY};
            max-width: 660px;
            margin: 0 auto 1.6rem auto;
        }}
        .ds-hero-actions {{
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 12px;
        }}
        .ds-btn-primary {{
            display: inline-flex;
            align-items: center;
            padding: 0.72rem 1.45rem;
            border-radius: 9px;
            background: linear-gradient(135deg, #0891B2, #0284C7);
            border: 1px solid rgba(34, 211, 238, 0.5);
            color: #FFFFFF !important;
            font-weight: 600;
            font-size: 0.92rem;
            text-decoration: none;
            box-shadow: 0 6px 20px rgba(8, 145, 178, 0.3);
        }}
        .ds-btn-secondary {{
            display: inline-flex;
            align-items: center;
            padding: 0.72rem 1.45rem;
            border-radius: 9px;
            background: {SURFACE_PRIMARY};
            border: 1px solid {BORDER_COLOR};
            color: {TEXT_PRIMARY} !important;
            font-weight: 600;
            font-size: 0.92rem;
            text-decoration: none;
        }}

        /* Product Preview */
        .ds-preview-shell {{
            background: {SURFACE_PRIMARY};
            border: 1px solid {BORDER_COLOR};
            border-radius: 14px;
            overflow: hidden;
            box-shadow: 0 18px 45px rgba(0, 0, 0, 0.45);
            margin-bottom: 1.75rem;
        }}
        .ds-preview-topbar {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.65rem 1rem;
            background: #0B1526;
            border-bottom: 1px solid {BORDER_COLOR};
            gap: 8px;
        }}
        .ds-preview-dots {{
            display: flex;
            gap: 6px;
        }}
        .ds-preview-dots span {{
            width: 9px;
            height: 9px;
            border-radius: 50%;
            background: #273D5E;
            display: inline-block;
        }}
        .ds-preview-url {{
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 0.74rem;
            color: {TEXT_SECONDARY};
        }}
        .ds-preview-pill {{
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 0.66rem;
            font-weight: 700;
            color: {PRIMARY_CYAN};
            background: rgba(34, 211, 238, 0.1);
            border: 1px solid rgba(34, 211, 238, 0.25);
            padding: 2px 8px;
            border-radius: 4px;
        }}
        .ds-preview-body {{
            padding: 1.15rem;
        }}
        .ds-preview-kpis {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
            gap: 10px;
            margin-bottom: 12px;
        }}
        .ds-preview-kpi {{
            background: {SURFACE_ELEVATED};
            border: 1px solid {BORDER_COLOR};
            border-radius: 9px;
            padding: 0.75rem 0.9rem;
        }}
        .ds-preview-kpi-label {{
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 0.66rem;
            color: {TEXT_SECONDARY};
            letter-spacing: 0.05em;
        }}
        .ds-preview-kpi-val {{
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 1.35rem;
            font-weight: 700;
            color: {TEXT_PRIMARY};
            margin: 2px 0;
        }}
        .ds-preview-kpi-sub {{
            font-size: 0.73rem;
            color: {TEXT_MUTED};
        }}
        .ds-preview-split {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 12px;
        }}
        .ds-preview-panel {{
            background: #0B1526;
            border: 1px solid {BORDER_COLOR};
            border-radius: 9px;
            padding: 0.9rem;
        }}
        .ds-preview-panel-title {{
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 0.69rem;
            font-weight: 700;
            color: {INTERACTIVE_ACCENT};
            letter-spacing: 0.06em;
            margin-bottom: 8px;
        }}
        .ds-trace-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
            padding: 5px 8px;
            border-radius: 6px;
            background: rgba(16, 30, 49, 0.7);
            margin-bottom: 5px;
            font-size: 0.76rem;
        }}
        .ds-trace-row code {{
            color: {TEXT_PRIMARY};
            flex: 1;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        .ds-trace-step {{
            font-family: monospace;
            color: {TEXT_MUTED};
            font-size: 0.7rem;
        }}
        .ds-trace-ok {{
            font-family: monospace;
            font-size: 0.66rem;
            font-weight: 700;
            color: {SUCCESS};
        }}
        .ds-finding-sample {{
            background: {SURFACE_ELEVATED};
            border: 1px solid {BORDER_COLOR};
            border-radius: 8px;
            padding: 0.85rem;
        }}

        /* Tech Stack Bar */
        .ds-stack-bar {{
            display: flex;
            align-items: center;
            justify-content: center;
            flex-wrap: wrap;
            gap: 8px;
            padding: 0.85rem 1rem;
            background: rgba(16, 30, 49, 0.55);
            border: 1px solid {BORDER_COLOR};
            border-radius: 10px;
            margin-bottom: 2.25rem;
        }}
        .ds-stack-label {{
            font-family: monospace;
            font-size: 0.7rem;
            color: {TEXT_MUTED};
            margin-right: 6px;
        }}
        .ds-stack-pill {{
            font-size: 0.78rem;
            font-weight: 600;
            color: {TEXT_PRIMARY};
            background: {SURFACE_ELEVATED};
            border: 1px solid {BORDER_COLOR};
            padding: 4px 10px;
            border-radius: 6px;
        }}

        /* Section headers */
        .ds-section-head {{
            margin-top: 2.25rem;
            margin-bottom: 1rem;
        }}
        .ds-section-sub {{
            color: {TEXT_SECONDARY};
            font-size: 0.92rem;
            max-width: 720px;
            line-height: 1.5;
        }}

        /* Bento Grid */
        .ds-bento-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 12px;
            margin-bottom: 1.5rem;
        }}
        .ds-bento-card {{
            background: {SURFACE_PRIMARY};
            border: 1px solid {BORDER_COLOR};
            border-radius: 11px;
            padding: 1.1rem 1.2rem;
            transition: border-color 0.15s ease;
        }}
        .ds-bento-card:hover {{
            border-color: {PRIMARY_CYAN};
        }}
        .ds-bento-tag {{
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 0.68rem;
            font-weight: 700;
            color: {PRIMARY_CYAN};
            margin-bottom: 6px;
        }}
        .ds-bento-card h3 {{
            font-size: 1.02rem !important;
            margin: 0 0 6px 0 !important;
            color: {TEXT_PRIMARY} !important;
        }}
        .ds-bento-card p {{
            font-size: 0.84rem;
            color: {TEXT_SECONDARY};
            line-height: 1.5;
            margin: 0;
        }}

        /* Dual-Engine Architecture */
        .ds-arch-grid {{
            display: grid;
            grid-template-columns: 1fr auto 1fr;
            gap: 12px;
            align-items: stretch;
            margin-bottom: 1.5rem;
        }}
        .ds-arch-box {{
            background: {SURFACE_PRIMARY};
            border: 1px solid {BORDER_COLOR};
            border-radius: 11px;
            padding: 1.1rem 1.25rem;
        }}
        .ds-arch-llm {{
            border-top: 3px solid {PRIMARY_CYAN};
        }}
        .ds-arch-py {{
            border-top: 3px solid {SUCCESS};
        }}
        .ds-arch-label {{
            font-family: monospace;
            font-size: 0.69rem;
            font-weight: 700;
            color: {PRIMARY_CYAN};
            margin-bottom: 4px;
        }}
        .ds-arch-py .ds-arch-label {{
            color: {SUCCESS};
        }}
        .ds-arch-box h4 {{
            margin: 0 0 8px 0;
            color: {TEXT_PRIMARY};
            font-size: 1rem;
        }}
        .ds-arch-box ul {{
            margin: 0;
            padding-left: 1.1rem;
            color: {TEXT_SECONDARY};
            font-size: 0.83rem;
            line-height: 1.55;
        }}
        .ds-arch-connector {{
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            gap: 6px;
            font-family: monospace;
            font-size: 0.74rem;
            font-weight: 700;
            color: {PRIMARY_CYAN};
            padding: 0 6px;
        }}

        /* Lifecycle Grid */
        .ds-lifecycle-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin-bottom: 1.5rem;
        }}
        .ds-life-step {{
            background: {SURFACE_PRIMARY};
            border: 1px solid {BORDER_COLOR};
            border-radius: 10px;
            padding: 0.85rem 0.9rem;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }}
        .ds-life-step span {{
            font-family: monospace;
            font-size: 0.72rem;
            font-weight: 700;
            color: {PRIMARY_CYAN};
        }}
        .ds-life-step b {{
            font-size: 0.88rem;
            color: {TEXT_PRIMARY};
        }}
        .ds-life-step small {{
            font-size: 0.75rem;
            color: {TEXT_SECONDARY};
        }}

        /* Reliability Grid */
        .ds-reliability-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 12px;
            margin-bottom: 2rem;
        }}
        .ds-rel-card {{
            background: {SURFACE_PRIMARY};
            border: 1px solid {BORDER_COLOR};
            border-radius: 10px;
            padding: 1rem 1.15rem;
        }}
        .ds-rel-card h4 {{
            margin: 0 0 6px 0;
            color: {TEXT_PRIMARY};
            font-size: 0.95rem;
        }}
        .ds-rel-card p {{
            margin: 0;
            color: {TEXT_SECONDARY};
            font-size: 0.83rem;
            line-height: 1.5;
        }}

        /* Footer */
        .ds-footer {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 12px;
            padding-top: 1.25rem;
            margin-top: 2rem;
            border-top: 1px solid {BORDER_COLOR};
            font-size: 0.82rem;
            color: {TEXT_SECONDARY};
        }}
        .ds-footer-left {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .ds-footer-right {{
            display: flex;
            gap: 16px;
        }}
        .ds-footer-right a {{
            color: {PRIMARY_CYAN};
            text-decoration: none;
            font-weight: 500;
        }}

        /* Responsive overrides */
        @media (max-width: 900px) {{
            .ds-arch-grid {{
                grid-template-columns: 1fr;
            }}
            .ds-arch-connector {{
                flex-direction: row;
                padding: 4px 0;
            }}
        }}
        @media (max-width: 768px) {{
            .block-container {{
                padding-left: 1rem !important;
                padding-right: 1rem !important;
            }}
            h1 {{
                font-size: 1.6rem !important;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
