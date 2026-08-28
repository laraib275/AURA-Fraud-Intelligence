import math
import textwrap
from datetime import datetime
from typing import Any

import altair as alt
import pandas as pd
import requests
import streamlit as st

# ============================================================
# AURA — PRODUCTION FRAUD OPERATIONS UI
# Existing API / investigation flow preserved
# ============================================================

API_URL = "http://127.0.0.1:8000"
PAGE_SIZE = 8


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AURA · Fraud Intelligence",
    page_icon="A",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# SESSION STATE
# ============================================================
if "ai_report" not in st.session_state:
    st.session_state.ai_report = None
    
if "investigations" not in st.session_state:
    st.session_state.investigations = []

if "selected_transaction" not in st.session_state:
    st.session_state.selected_transaction = ""

if "last_report" not in st.session_state:
    st.session_state.last_report = None


# ============================================================
# DESIGN SYSTEM
# ============================================================

def render_html(content: str, unsafe_allow_html: bool = True, **kwargs) -> None:
    """Render HTML without allowing Markdown indentation to create code blocks."""
    # Streamlit's Markdown parser can treat indented HTML lines as preformatted
    # code. Strip indentation from every line while preserving the HTML itself.
    html = "\n".join(
        line.strip()
        for line in textwrap.dedent(content).splitlines()
        if line.strip()
    )
    st.markdown(html, unsafe_allow_html=unsafe_allow_html)


st.markdown(
    """
    <style>

    @import url(
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap'
    );

    :root {
        --bg: #F7F8FB;
        --surface: #FFFFFF;
        --surface-soft: #FBFAFC;
        --border: #E4E7EC;
        --border-strong: #D0D5DD;
        --text: #182230;
        --muted: #667085;
        --subtle: #98A2B3;

        --indigo: #4F46E5;
        --indigo-dark: #3730A3;

        --pink: #DB2777;
        --pink-soft: #FDF2F8;
        --pink-border: #FBCFE8;

        --green: #15803D;
        --green-bg: #ECFDF3;

        --amber: #B54708;
        --amber-bg: #FFFAEB;

        --red: #B42318;
        --red-bg: #FEF3F2;
    }

    html, body, [class*="css"] {
        font-family: "Inter", sans-serif;
    }

    .stApp {
    background:
        radial-gradient(
            circle at 100% 0%,
            rgba(219, 39, 119, 0.08),
            transparent 25%
        ),
        #FFF7FA;
    color: var(--text);
    }



    .block-container {
        max-width: 1450px;
        padding: 1.25rem 1.8rem 3rem;
    }

    div[data-testid="stHeader"] {
        background: transparent;
    }

    /* ========================================================
       SIDEBAR
       ======================================================== */

    section[data-testid="stSidebar"] {
        background: #FFFFFF;
        border-right: 1px solid var(--border);
    }

    section[data-testid="stSidebar"] > div {
        padding-top: 1.15rem;
    }

    .side-brand {
        padding: 0.15rem 0.3rem 1.45rem;
        color: var(--text);
        font-size: 1.18rem;
        font-weight: 750;
        letter-spacing: -0.035em;
    }

    .side-brand span {
        color: var(--pink);
    }

    .side-caption {
        color: #98A2B3;
        font-size: 0.66rem;
        letter-spacing: 0.11em;
        text-transform: uppercase;
        font-weight: 700;
        margin: 0 0 0.55rem;
    }

    .side-note {
        border-top: 1px solid var(--border);
        margin-top: 1.6rem;
        padding-top: 0.9rem;
        color: #98A2B3;
        font-size: 0.69rem;
        line-height: 1.55;
    }

    /* ========================================================
       HEADER
       ======================================================== */

    .app-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 1rem;
        border-bottom: 1px solid var(--border);
        padding-bottom: 0.85rem;
        margin-bottom: 1.5rem;
    }

    .header-title {
        color: var(--text);
        font-size: 1.15rem;
        font-weight: 700;
        letter-spacing: -0.02em;
    }

    .header-copy {
        color: var(--muted);
        font-size: 0.74rem;
        margin-top: 0.18rem;
    }

    .status-inline {
        display: inline-flex;
        align-items: center;
        gap: 0.55rem;
    }

    .online-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.38rem;
        padding: 0.34rem 0.62rem;
        border-radius: 999px;
        background: var(--green-bg);
        color: var(--green);
        border: 1px solid #ABEFC6;
        font-size: 0.67rem;
        font-weight: 700;
    }

    .online-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: #12B76A;
    }

    .header-icon {
        width: 34px;
        height: 34px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border: 1px solid var(--border);
        border-radius: 8px;
        background: #FFFFFF;
        color: #475467;
        font-size: 0.88rem;
    }

    /* ========================================================
       PAGE INTRO
       ======================================================== */

    .page-kicker {
        color: var(--pink);
        font-size: 0.66rem;
        text-transform: uppercase;
        letter-spacing: 0.11em;
        font-weight: 800;
        margin-bottom: 0.35rem;
    }

    .page-title {
        color: var(--text);
        font-size: 2rem;
        line-height: 1.12;
        font-weight: 700;
        letter-spacing: -0.035em;
        margin-bottom: 0.30rem;
    }

    .page-copy {
        color: var(--muted);
        font-size: 0.86rem;
        line-height: 1.55;
        max-width: 760px;
        margin-bottom: 1.2rem;
    }

    /* ========================================================
       CARDS
       ======================================================== */

    .kpi-card,
    .detail-card,
    .panel-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(16, 24, 40, 0.025);
    }

    .kpi-card {
        padding: 0.95rem 1rem;
        min-height: 118px;
        transition: border-color 180ms ease, box-shadow 180ms ease,
                    transform 180ms ease;
    }

    .kpi-card:hover {
        border-color: #D5D9E2;
        box-shadow: 0 5px 14px rgba(16, 24, 40, 0.045);
        transform: translateY(-1px);
    }

    .kpi-label {
        color: #667085;
        font-size: 0.66rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 700;
    }

    .kpi-value {
        color: var(--text);
        font-size: 1.82rem;
        line-height: 1;
        font-weight: 700;
        margin-top: 0.60rem;
        letter-spacing: -0.035em;
    }

    .kpi-note {
        color: #98A2B3;
        font-size: 0.68rem;
        margin-top: 0.40rem;
    }

    .panel-card {
        padding: 1rem 1.05rem;
    }

    .section-head {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        gap: 1rem;
        margin: 1.6rem 0 0.72rem;
    }

    .section-title {
        color: var(--text);
        font-size: 0.96rem;
        font-weight: 700;
    }

    .section-subtitle {
        color: var(--subtle);
        font-size: 0.68rem;
    }

    /* ========================================================
       SEARCH
       ======================================================== */

    .search-shell {
        background: #FFFFFF;
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 0.85rem 0.9rem 0.12rem;
        box-shadow: 0 2px 8px rgba(16, 24, 40, 0.025);
        margin: 0.7rem 0 1rem;
    }

    div[data-testid="stTextInput"] label {
        color: #475467 !important;
        font-size: 0.70rem !important;
        font-weight: 700 !important;
    }

    div[data-testid="stTextInput"] input {
        background: #FFFFFF;
        color: var(--text);
        border: 1px solid var(--border-strong);
        border-radius: 8px;
        min-height: 40px;
    }

    div[data-testid="stTextInput"] input:focus {
        border-color: var(--indigo);
        box-shadow: 0 0 0 2px rgba(79,70,229,0.10);
    }

    .stButton > button {
        background: var(--indigo);
        color: #FFFFFF;
        border: 1px solid var(--indigo);
        border-radius: 8px;
        min-height: 40px;
        font-weight: 700;
        transition: background-color 180ms ease, transform 180ms ease;
    }

    .stButton > button:hover {
        background: var(--indigo-dark);
        border-color: var(--indigo-dark);
        color: #FFFFFF;
        transform: translateY(-1px);
    }

    .stButton > button:focus {
        box-shadow: 0 0 0 3px rgba(79,70,229,0.13);
    }

    /* ========================================================
       STATUS / RISK
       ======================================================== */

    .status-panel {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        border-radius: 10px;
        padding: 0.88rem 1rem;
        margin: 0.9rem 0;
    }

    .status-high {
        background: var(--red-bg);
        border: 1px solid #FECACA;
        border-left: 4px solid #D92D20;
    }

    .status-medium {
        background: var(--amber-bg);
        border: 1px solid #FEDF89;
        border-left: 4px solid #F79009;
    }

    .status-low {
        background: var(--green-bg);
        border: 1px solid #ABEFC6;
        border-left: 4px solid #12B76A;
    }

    .status-title {
        color: var(--text);
        font-size: 0.92rem;
        font-weight: 700;
    }

    .status-copy {
        color: #667085;
        font-size: 0.70rem;
        margin-top: 0.18rem;
    }

    .action-tag {
        white-space: nowrap;
        color: #344054;
        background: rgba(255,255,255,0.78);
        border: 1px solid rgba(16,24,40,0.09);
        border-radius: 7px;
        padding: 0.38rem 0.55rem;
        font-size: 0.66rem;
        font-weight: 700;
    }

    /* ========================================================
       DETAILS / REASONS / FACTORS
       ======================================================== */

    .detail-card {
        padding: 0.9rem;
        min-height: 95px;
    }

    .detail-label {
        color: #98A2B3;
        font-size: 0.64rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 700;
    }

    .detail-value {
        color: #344054;
        font-size: 0.84rem;
        font-weight: 600;
        margin-top: 0.45rem;
        word-break: break-word;
    }

    .reason-row,
    .factor-row {
        border-bottom: 1px solid #EAECF0;
        padding: 0.75rem 0;
    }

    .reason-row:last-child,
    .factor-row:last-child {
        border-bottom: 0;
    }

    .reason-index {
        color: var(--pink);
        font-size: 0.63rem;
        font-weight: 800;
        margin-bottom: 0.14rem;
    }

    .reason-text {
        color: #344054;
        font-size: 0.75rem;
        line-height: 1.48;
    }

    .factor-top {
        display: flex;
        justify-content: space-between;
        gap: 1rem;
        align-items: center;
    }

    .factor-name {
        color: #344054;
        font-size: 0.75rem;
        font-weight: 700;
    }

    .factor-score {
        color: var(--pink);
        font-size: 0.66rem;
        font-weight: 800;
    }

    .factor-meta {
        color: #98A2B3;
        font-size: 0.65rem;
        margin-top: 0.18rem;
    }

    .factor-track {
        height: 5px;
        border-radius: 999px;
        background: #F2F4F7;
        margin-top: 0.44rem;
        overflow: hidden;
    }

    .factor-fill {
        height: 100%;
        border-radius: 999px;
        background: var(--pink);
    }

    /* ========================================================
       MESSAGE / EMPTY
       ======================================================== */

    .success-banner {
        display: flex;
        align-items: center;
        gap: 0.50rem;
        padding: 0.62rem 0.72rem;
        border-radius: 8px;
        background: var(--green-bg);
        border: 1px solid #ABEFC6;
        color: var(--green);
        font-size: 0.70rem;
        font-weight: 700;
        margin-bottom: 0.9rem;
    }

    .success-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: #12B76A;
    }

    .empty-state {
        text-align: center;
        background: #FFFFFF;
        border: 1px dashed var(--border-strong);
        border-radius: 10px;
        padding: 1.6rem 1rem;
    }

    .empty-title {
        color: #344054;
        font-size: 0.84rem;
        font-weight: 700;
    }

    .empty-copy {
        color: #98A2B3;
        font-size: 0.70rem;
        margin-top: 0.25rem;
    }

    /* ========================================================
       FOOTER
       ======================================================== */

    .footer {
        border-top: 1px solid var(--border);
        margin-top: 2.3rem;
        padding-top: 0.85rem;
        color: #98A2B3;
        font-size: 0.65rem;
    }

    @media (max-width: 900px) {
        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }

        .page-title {
            font-size: 1.65rem;
        }

        .app-header {
            align-items: flex-start;
        }
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HELPERS
# ============================================================

def risk_class(risk_band: str) -> str:
    return {
        "HIGH": "status-high",
        "MEDIUM": "status-medium",
        "LOW": "status-low",
    }.get(risk_band, "status-low")


def risk_color(risk_band: str) -> str:
    return {
        "HIGH": "#B42318",
        "MEDIUM": "#B54708",
        "LOW": "#15803D",
    }.get(risk_band, "#344054")


def record_investigation(report: dict[str, Any]) -> None:
    transaction_id = report.get("transaction_id")
    if not transaction_id:
        return

    record = {
        "transaction_id": transaction_id,
        "transaction_time": report.get("transaction_time"),
        "amount": report.get("amount"),
        "fraud_probability": report.get("fraud_probability"),
        "risk_score": report.get("risk_score"),
        "risk_band": report.get("risk_band"),
        "recommended_action": report.get("recommended_action"),
        "investigation_reasons": report.get("investigation_reasons", []),
        "top_risk_factors": report.get("top_risk_factors", []),
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    existing = [
        row
        for row in st.session_state.investigations
        if row["transaction_id"] != transaction_id
    ]

    st.session_state.investigations = [record] + existing


def investigations_df() -> pd.DataFrame:
    rows = []

    for item in st.session_state.investigations:
        reasons = item.get("investigation_reasons", [])
        reason = reasons[0] if reasons else "Model signal"

        rows.append(
            {
                "Transaction ID": item["transaction_id"],
                "Customer": "Not provided by API",
                "Amount": item.get("amount"),
                "Risk Score": item.get("risk_score"),
                "Risk Level": item.get("risk_band", ""),
                "Reason": reason,
                "Status": item.get("recommended_action", ""),
                "Updated": item.get("updated", ""),
            }
        )

    return pd.DataFrame(rows)


def risk_trend_chart(df: pd.DataFrame):
    if df.empty:
        return None

    work = df.copy()
    work["Updated"] = pd.to_datetime(work["Updated"], errors="coerce")
    work = work.sort_values("Updated").reset_index(drop=True)
    work["Sequence"] = range(1, len(work) + 1)

    return (
        alt.Chart(work)
        .mark_line(
            point=True,
            strokeWidth=2.2,
            color="#4F46E5",
        )
        .encode(
            x=alt.X(
                "Sequence:Q",
                title="Investigation",
                axis=alt.Axis(tickMinStep=1),
            ),
            y=alt.Y(
                "Risk Score:Q",
                title="Risk score",
                scale=alt.Scale(domain=[0, 100]),
            ),
            tooltip=[
                alt.Tooltip("Transaction ID:N"),
                alt.Tooltip("Risk Score:Q", format=".1f"),
                alt.Tooltip("Risk Level:N"),
                alt.Tooltip("Updated:N"),
            ],
        )
        .properties(height=260)
    )


def risk_distribution_chart(df: pd.DataFrame):
    if df.empty:
        return None

    dist = (
        df["Risk Level"]
        .value_counts()
        .rename_axis("Risk Level")
        .reset_index(name="Count")
    )

    return (
        alt.Chart(dist)
        .mark_arc(
            innerRadius=55,
            outerRadius=92,
        )
        .encode(
            theta="Count:Q",
            color=alt.Color(
                "Risk Level:N",
                scale=alt.Scale(
                    domain=["HIGH", "MEDIUM", "LOW"],
                    range=["#D92D20", "#F79009", "#12B76A"],
                ),
                legend=alt.Legend(
                    title=None,
                    orient="bottom",
                ),
            ),
            tooltip=[
                alt.Tooltip("Risk Level:N"),
                alt.Tooltip("Count:Q"),
            ],
        )
        .properties(height=260)
    )


def render_investigation(report: dict[str, Any]) -> None:
    risk_band = report.get("risk_band", "LOW")
    status_cls = risk_class(risk_band)
    status_color = risk_color(risk_band)

    k1, k2, k3, k4 = st.columns(4)

    with k1:
        render_html(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Risk Score</div>
                <div class="kpi-value">
                    {float(report.get('risk_score', 0)):.1f}
                </div>
                <div class="kpi-note">out of 100</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with k2:
        render_html(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Model Fraud Score</div>
                <div class="kpi-value" style="color:#4F46E5;">
                    {float(report.get('fraud_probability', 0)):.2%}
                </div>
                <div class="kpi-note">model output</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with k3:
        render_html(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Risk Level</div>
                <div class="kpi-value" style="color:{status_color};">
                    {risk_band}
                </div>
                <div class="kpi-note">current assessment</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with k4:
        render_html(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Amount</div>
                <div class="kpi-value">
                    {float(report.get('amount', 0)):.2f}
                </div>
                <div class="kpi-note">transaction amount</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    render_html(
        f"""
        <div class="status-panel {status_cls}">
            <div>
                <div class="status-title">{risk_band} risk</div>
                <div class="status-copy">
                    {report.get('recommended_action', 'Review transaction')}
                </div>
            </div>

            <div class="action-tag">
                {report.get('recommended_action', 'Review')}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([1, 1], gap="large")

    with left:
        render_html(
            """
            <div class="section-head">
                <div class="section-title">Transaction overview</div>
                <div class="section-subtitle">Source record</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        a, b = st.columns(2)

        with a:
            render_html(
                f"""
                <div class="detail-card">
                    <div class="detail-label">Transaction ID</div>
                    <div class="detail-value">
                        {report.get('transaction_id', '—')}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with b:
            render_html(
                f"""
                <div class="detail-card">
                    <div class="detail-label">Transaction Time</div>
                    <div class="detail-value">
                        {report.get('transaction_time', '—')}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        render_html(
            """
            <div class="section-head">
                <div class="section-title">Why was this flagged?</div>
                <div class="section-subtitle">Investigation signals</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        reasons = report.get("investigation_reasons", [])

        if reasons:
            for i, reason in enumerate(reasons, start=1):
                render_html(
                    f"""
                    <div class="reason-row">
                        <div class="reason-index">{i:02d}</div>
                        <div class="reason-text">{reason}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            render_html(
                """
                <div class="empty-state">
                    <div class="empty-title">
                        No rule-based reasons returned
                    </div>
                    <div class="empty-copy">
                        The model still produced a risk assessment.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with right:
        render_html(
            """
            <div class="section-head">
                <div class="section-title">Risk assessment</div>
                <div class="section-subtitle">Explainable model factors</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        factors = report.get("top_risk_factors", [])

        if factors:
            max_abs = max(
                [abs(float(item.get("shap_value", 0))) for item in factors]
                or [1.0]
            )

            for item in factors:
                shap_value = float(item.get("shap_value", 0))
                width = int(
                    min(
                        100,
                        max(
                            4,
                            abs(shap_value) / max_abs * 100,
                        ),
                    )
                )

                sign = "+" if shap_value >= 0 else ""

                render_html(
                    f"""
                    <div class="factor-row">
                        <div class="factor-top">
                            <div class="factor-name">
                                {item.get('feature', 'Unknown feature')}
                            </div>
                            <div class="factor-score">
                                {sign}{shap_value:.4f}
                            </div>
                        </div>

                        <div class="factor-meta">
                            Observed value: {item.get('value', '—')}
                        </div>

                        <div class="factor-track">
                            <div
                                class="factor-fill"
                                style="width:{width}%"
                            ></div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            render_html(
                """
                <div class="empty-state">
                    <div class="empty-title">
                        No explainability factors returned
                    </div>
                    <div class="empty-copy">
                        SHAP details are not available for this response.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ============================================================
# HEADER — BUILT AS REAL STREAMLIT COLUMNS
# Prevents raw HTML appearing on the right side.
# ============================================================

head_left, head_right = st.columns([5, 2])

with head_left:
    render_html(
        """
        <div class="header-title">Fraud Intelligence</div>
        <div class="header-copy">
            Detection, triage, and explainable transaction investigation
        </div>
        """,
        unsafe_allow_html=True,
    )

with head_right:
    h1, h2 = st.columns([1.55, 0.45])

    with h1:
        render_html(
            """
            <div style="text-align:right; padding-top:0.12rem;">
                <span class="online-badge">
                    <span class="online-dot"></span>
                    System online
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with h2:
        render_html(
            """
            <div
                class="header-icon"
                title="Notifications"
                style="margin-left:auto;"
            >
                ♢
            </div>
            """,
            unsafe_allow_html=True,
        )

render_html(
    "<div style='height:0.15rem;'></div>",
    unsafe_allow_html=True,
)

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    render_html(
        """
        <div class="side-brand">AURA<span>.</span></div>
        <div class="side-caption">Workspace</div>
        """,
        unsafe_allow_html=True,
    )

    page = st.radio(
        "Navigation",
        [
            "Overview",
            "Investigations",
            "Cases",
            "Transactions",
            "Analytics",
            "Alerts",
            "Reports",
            "Settings",
            "Help",
            "Profile",
        ],
        index=1,
        label_visibility="collapsed",
    )

    render_html(
        """
        <div class="side-note">
            Connected to the existing AURA investigation API.
            Queue analytics are based on investigations completed
            in the current dashboard session.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# OVERVIEW
# ============================================================

if page == "Overview":

    render_html(
        '<div class="page-kicker">Overview</div>',
        unsafe_allow_html=True,
    )

    render_html(
        '<div class="page-title">Fraud operations overview</div>',
        unsafe_allow_html=True,
    )

    render_html(
        """
        <div class="page-copy">
            Monitor the investigations handled by AURA and review the
            current risk workload in one place.
        </div>
        """,
        unsafe_allow_html=True,
    )

    df = investigations_df()

    total = len(df)
    high = int((df["Risk Level"] == "HIGH").sum()) if not df.empty else 0
    fraud_rate = (high / total * 100) if total else 0.0
    open_cases = (
        int(df["Risk Level"].isin(["HIGH", "MEDIUM"]).sum())
        if not df.empty
        else 0
    )

    c1, c2, c3, c4 = st.columns(4)

    cards = [
        (
            "Transactions Monitored",
            f"{total:,}",
            "Current dashboard session",
            "#182230",
        ),
        (
            "High-Risk Transactions",
            f"{high:,}",
            "Classified HIGH",
            "#B42318",
        ),
        (
            "Fraud Detection Rate",
            f"{fraud_rate:.1f}%",
            "Share classified HIGH",
            "#4F46E5",
        ),
        (
            "Open Investigations",
            f"{open_cases:,}",
            "HIGH + MEDIUM",
            "#DB2777",
        ),
    ]

    for column, (label, value, note, color) in zip(
        [c1, c2, c3, c4],
        cards,
    ):
        with column:
            render_html(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">{label}</div>
                    <div
                        class="kpi-value"
                        style="color:{color};"
                    >
                        {value}
                    </div>
                    <div class="kpi-note">{note}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    render_html(
        """
        <div class="section-head">
            <div class="section-title">Analytics</div>
            <div class="section-subtitle">
                Current session only
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    chart_left, chart_right = st.columns([1.5, 0.85], gap="large")

    with chart_left:
        render_html(
            """
            <div class="panel-card">
                <div class="section-title">Fraud Risk Trend</div>
                <div class="section-subtitle">
                    Risk score across investigations
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        chart = risk_trend_chart(df)

        if chart is not None:
            st.altair_chart(
                chart,
                use_container_width=True,
            )
        else:
            render_html(
                """
                <div class="empty-state">
                    <div class="empty-title">
                        No trend data yet
                    </div>
                    <div class="empty-copy">
                        Investigate transactions to populate this chart.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with chart_right:
        render_html(
            """
            <div class="panel-card">
                <div class="section-title">Risk Distribution</div>
                <div class="section-subtitle">
                    Current risk levels
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        chart = risk_distribution_chart(df)

        if chart is not None:
            st.altair_chart(
                chart,
                use_container_width=True,
            )
        else:
            render_html(
                """
                <div class="empty-state">
                    <div class="empty-title">
                        No distribution yet
                    </div>
                    <div class="empty-copy">
                        Results appear after investigations.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    render_html(
        """
        <div class="section-head">
            <div class="section-title">Recent Investigations</div>
            <div class="section-subtitle">
                Most recent AURA results
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if df.empty:
        render_html(
            """
            <div class="empty-state">
                <div class="empty-title">No investigations yet</div>
                <div class="empty-copy">
                    Open Investigations and search for a transaction.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        f1, f2, f3 = st.columns([1.25, 0.75, 0.75])

        with f1:
            query = st.text_input(
                "Search",
                placeholder="Transaction ID or reason",
                key="ov_search",
            )

        with f2:
            risk_filter = st.selectbox(
                "Risk",
                ["All", "HIGH", "MEDIUM", "LOW"],
                key="ov_risk",
            )

        with f3:
            sort_option = st.selectbox(
                "Sort",
                ["Updated", "Risk Score", "Amount"],
                key="ov_sort",
            )

        table_df = df.copy()

        if query.strip():
            q = query.strip().lower()
            table_df = table_df[
                table_df["Transaction ID"]
                .astype(str)
                .str.lower()
                .str.contains(q)
                |
                table_df["Reason"]
                .astype(str)
                .str.lower()
                .str.contains(q)
            ]

        if risk_filter != "All":
            table_df = table_df[
                table_df["Risk Level"] == risk_filter
            ]

        table_df = table_df.sort_values(
            sort_option,
            ascending=False,
            na_position="last",
        )

        pages = max(
            1,
            math.ceil(len(table_df) / PAGE_SIZE),
        )

        p = st.number_input(
            "Page",
            min_value=1,
            max_value=pages,
            value=1,
            step=1,
            key="ov_page",
        )

        start = (p - 1) * PAGE_SIZE

        st.dataframe(
            table_df.iloc[start:start + PAGE_SIZE],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Risk Score": st.column_config.NumberColumn(
                    format="%.1f",
                ),
                "Amount": st.column_config.NumberColumn(
                    format="%.2f",
                ),
            },
        )


# ============================================================
# INVESTIGATIONS
# ============================================================

elif page == "Investigations":

    render_html(
        '<div class="page-kicker">Investigations</div>',
        unsafe_allow_html=True,
    )

    render_html(
        '<div class="page-title">Transaction investigation</div>',
        unsafe_allow_html=True,
    )

    render_html(
        """
        <div class="page-copy">
            Search a transaction, review its risk assessment, and understand
            the factors behind the model decision.
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_html(
        '<div class="search-shell">',
        unsafe_allow_html=True,
    )

    with st.form(
        "investigation_form",
        clear_on_submit=False,
    ):
        c1, c2 = st.columns([5, 1.15])

        with c1:
            transaction_id = st.text_input(
                "Transaction ID",
                value=st.session_state.selected_transaction,
                placeholder="Enter transaction ID",
            )

        with c2:
            render_html("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button(
                "Investigate",
                use_container_width=True,
            )

    render_html(
        '</div>',
        unsafe_allow_html=True,
    )

    if submitted:

        if not transaction_id.strip():

            st.warning(
                "Please enter a transaction ID."
            )

        else:

            st.session_state.selected_transaction = (
                transaction_id.strip()
            )

            with st.spinner(
                "Running investigation..."
            ):

                try:

                    response = requests.get(
                        f"{API_URL}/investigate/"
                        f"{transaction_id.strip()}",
                        timeout=60,
                    )

                    if response.status_code == 404:

                        st.error(
                            "Transaction was not found by the investigation API."
                        )

                    elif response.status_code != 200:

                        st.error(
                            f"Investigation API returned "
                            f"{response.status_code}."
                        )

                    else:

                        report = response.json()

                        st.session_state.last_report = report
                        record_investigation(report)


                                                # ====================================================
                        # AI INVESTIGATOR
                        # ====================================================

                        try:
                            ai_response = requests.get(
                                f"{API_URL}/investigate/"
                                f"{transaction_id.strip()}/ai-report",
                                timeout=60,
                            )

                            if ai_response.status_code == 200:
                                st.session_state.ai_report = (
                                    ai_response.json()
                                )
                            else:
                                st.session_state.ai_report = None
                                st.warning(
                                    "AI Investigator report could not be generated."
                                )

                        except requests.exceptions.RequestException:
                            st.session_state.ai_report = None
                            st.warning(
                                "Could not connect to the AI Investigator endpoint."
                            )

                except requests.exceptions.RequestException as exc:

                    st.error(
                        "AURA could not reach the investigation API. "
                        f"Check that FastAPI is running on {API_URL}. "
                        f"Error: {exc}"
                    )

    if st.session_state.last_report:

        render_html(
            """
            <div class="success-banner">
                <span class="success-dot"></span>
                Investigation completed successfully
            </div>
            """,
            unsafe_allow_html=True,
        )

        render_investigation(
            st.session_state.last_report
        )
        

                # ============================================================
        # AURA AI INVESTIGATOR
        # ============================================================

        if st.session_state.get("ai_report"):

            ai = st.session_state.ai_report

            st.markdown(
                """
                <div class="section-label">
                    AI Investigator
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                f"""
                <div class="detail-card">
                    <div class="detail-label">
                        Executive Summary
                    </div>
                    <div class="detail-value">
                        {ai.get("executive_summary", "Not available")}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                """
                <div class="section-label">
                    Risk Interpretation
                </div>
                """,
                unsafe_allow_html=True,
            )

            for item in ai.get(
                "risk_interpretation",
                []
            ):

                st.markdown(
                    f"""
                    <div class="reason-item">
                        {item}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown(
                """
                <div class="section-label">
                    Investigation Evidence
                </div>
                """,
                unsafe_allow_html=True,
            )

            for item in ai.get(
                "evidence",
                []
            ):

                description = item.get(
                    "description",
                    ""
                )

                st.markdown(
                    f"""
                    <div class="reason-item">
                        {description}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown(
                """
                <div class="section-label">
                    Investigator Conclusion
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                f"""
                <div class="detail-card">
                    <div class="detail-value">
                        {
                            ai.get(
                                "investigator_conclusion",
                                "Not available"
                            )
                        }
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                """
                <div class="section-label">
                    Recommended Action
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                f"""
                <div class="reason-item">
                    {ai.get(
                        "recommended_action",
                        "Not available"
                    )}
                </div>
                """,
                unsafe_allow_html=True,
            )

    else:

        render_html(
            """
            <div class="empty-state">
                <div class="empty-title">
                    Ready for an investigation
                </div>
                <div class="empty-copy">
                    Enter a transaction ID above to load its risk
                    assessment, investigation reasons, and explainable
                    model factors.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# TRANSACTIONS
# ============================================================

elif page == "Transactions":

    render_html(
        '<div class="page-kicker">Transactions</div>',
        unsafe_allow_html=True,
    )

    render_html(
        '<div class="page-title">Transaction activity</div>',
        unsafe_allow_html=True,
    )

    render_html(
        """
        <div class="page-copy">
            Transactions investigated through the current dashboard session.
            No customer information is fabricated when it is unavailable from
            the existing API.
        </div>
        """,
        unsafe_allow_html=True,
    )

    df = investigations_df()

    if df.empty:

        render_html(
            """
            <div class="empty-state">
                <div class="empty-title">
                    No transactions to display
                </div>
                <div class="empty-copy">
                    Investigate a transaction first.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    else:

        a, b, c = st.columns([1.3, 0.75, 0.75])

        with a:
            query = st.text_input(
                "Search",
                placeholder="Transaction ID or reason",
                key="tx_query",
            )

        with b:
            risk_filter = st.selectbox(
                "Risk",
                ["All", "HIGH", "MEDIUM", "LOW"],
                key="tx_risk",
            )

        with c:
            sort_option = st.selectbox(
                "Sort",
                ["Updated", "Risk Score", "Amount"],
                key="tx_sort",
            )

        view = df.copy()

        if query.strip():

            q = query.strip().lower()

            view = view[
                view["Transaction ID"]
                .astype(str)
                .str.lower()
                .str.contains(q)
                |
                view["Reason"]
                .astype(str)
                .str.lower()
                .str.contains(q)
            ]

        if risk_filter != "All":
            view = view[
                view["Risk Level"] == risk_filter
            ]

        view = view.sort_values(
            sort_option,
            ascending=False,
            na_position="last",
        )

        pages = max(
            1,
            math.ceil(len(view) / PAGE_SIZE),
        )

        p = st.number_input(
            "Page",
            min_value=1,
            max_value=pages,
            value=1,
            step=1,
            key="tx_page",
        )

        start = (p - 1) * PAGE_SIZE

        st.dataframe(
            view.iloc[start:start + PAGE_SIZE],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Risk Score": st.column_config.NumberColumn(
                    format="%.1f",
                ),
                "Amount": st.column_config.NumberColumn(
                    format="%.2f",
                ),
            },
        )


# ============================================================
# OTHER NAV ITEMS — HONEST PLACEHOLDERS
# ============================================================

else:

    page_copy = {
        "Cases": (
            "Case lifecycle management can be connected here when "
            "case APIs are introduced."
        ),
        "Analytics": (
            "Model and operational analytics can be expanded here "
            "when dedicated analytics endpoints are available."
        ),
        "Alerts": (
            "Alert routing and notification workflows belong here "
            "once alert APIs are available."
        ),
        "Reports": (
            "Scheduled reports and exports can be added here without "
            "changing the existing investigation endpoint."
        ),
        "Settings": (
            "Workspace and API preferences can be configured here."
        ),
        "Help": (
            "Analyst guidance, field definitions, and investigation "
            "playbooks can be surfaced here."
        ),
        "Profile": (
            "User profile and access information can be connected here."
        ),
    }

    render_html(
        f'<div class="page-kicker">{page}</div>',
        unsafe_allow_html=True,
    )

    render_html(
        f'<div class="page-title">{page}</div>',
        unsafe_allow_html=True,
    )

    render_html(
        f"""
        <div class="page-copy">
            {page_copy.get(page, "")}
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_html(
        f"""
        <div class="empty-state">
            <div class="empty-title">
                {page} is ready for the next API-backed workflow
            </div>
            <div class="empty-copy">
                No synthetic production data is being shown here.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# FOOTER
# ============================================================

render_html(
    """
    <div class="footer">
        AURA Fraud Intelligence · Existing FastAPI investigation flow preserved
    </div>
    """,
    unsafe_allow_html=True,
)