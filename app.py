# =============================================================================
# app.py — AI-Driven Urban Heat Mitigation Dashboard
# Team Moon | ISRO Bharatiya Antariksh Hackathon 2026
# Pilot City: Chhatrapati Sambhajinagar
# =============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from streamlit_folium import st_folium
import io
import json
from datetime import date, datetime

# ── Project imports ───────────────────────────────────────────────────────────
from config import (
    PROJECT_TITLE, PROJECT_SUBTITLE, TEAM_NAME, HACKATHON_NAME,
    PILOT_CITY, VERSION, DATA_SOURCES, ML_MODELS, MITIGATION_STRATEGIES,
    PRIMARY_COLOR, SECONDARY_COLOR, TERTIARY_COLOR, CARD_COLOR,
)
from utils.data_loader import (
    load_hotspot_data, load_timeseries_data,
    load_mitigation_table, get_kpi_values,
)
from utils.map_utils import build_heat_map
from utils.model_utils import (
    train_model, predict_after_mitigation,
    get_feature_importances, FEATURE_COLS, FEATURE_LABELS,
)
from utils.recommendation_engine import (
    generate_strategy_report, compute_impact_summary,
)

# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(
    page_title=f"{PROJECT_TITLE} | {PILOT_CITY}",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# GLOBAL CSS
# =============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    color: #E2E8F0;
}

/* ── Main background ── */
.main .block-container { padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1400px; }

/* ── KPI Card ── */
.kpi-card {
    background: linear-gradient(135deg, #1C2232 0%, #141824 100%);
    border: 1px solid #2D3748;
    border-radius: 12px;
    padding: 18px 20px;
    text-align: center;
    margin-bottom: 8px;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    position: relative;
    overflow: hidden;
}
.kpi-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.4);
}
.kpi-card::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: var(--accent, #E84A5F);
    border-radius: 12px 12px 0 0;
}
.kpi-label  { font-size: 11px; font-weight: 500; color: #A0AEC0; text-transform: uppercase; letter-spacing: 0.07em; margin-bottom: 6px; }
.kpi-value  { font-size: 28px; font-weight: 700; color: #F7FAFC; line-height: 1.1; }
.kpi-unit   { font-size: 12px; font-weight: 400; color: #718096; margin-top: 3px; }
.kpi-delta  { font-size: 11px; margin-top: 5px; }

/* ── Section card ── */
.section-card {
    background: #161C2D;
    border: 1px solid #2D3748;
    border-radius: 14px;
    padding: 24px 26px;
    margin-bottom: 20px;
}
.section-title {
    font-size: 15px; font-weight: 600; color: #CBD5E0;
    text-transform: uppercase; letter-spacing: 0.06em;
    border-bottom: 1px solid #2D3748; padding-bottom: 10px; margin-bottom: 16px;
    display: flex; align-items: center; gap: 8px;
}
.section-title span.dot {
    display: inline-block; width: 8px; height: 8px;
    border-radius: 50%; background: #E84A5F;
}

/* ── Header ── */
.dashboard-header {
    background: linear-gradient(135deg, #0F1626 0%, #1A2340 50%, #0F1626 100%);
    border: 1px solid #2D3748;
    border-radius: 16px;
    padding: 28px 32px;
    margin-bottom: 24px;
    position: relative;
    overflow: hidden;
}
.dashboard-header::after {
    content: '';
    position: absolute; top: -40px; right: -40px;
    width: 180px; height: 180px;
    background: radial-gradient(circle, rgba(232,74,95,0.12) 0%, transparent 70%);
    border-radius: 50%;
}
.header-title {
    font-size: 26px; font-weight: 700; color: #FFFFFF;
    line-height: 1.2; margin-bottom: 6px;
}
.header-sub {
    font-size: 13px; color: #90A0B7; font-weight: 400; margin-bottom: 14px;
}
.header-badges { display: flex; gap: 10px; flex-wrap: wrap; }
.badge {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 20px; padding: 4px 12px;
    font-size: 11px; font-weight: 500; color: #CBD5E0;
}
.badge-accent { background: rgba(232,74,95,0.15); border-color: rgba(232,74,95,0.4); color: #FBB6C8; }
.badge-green  { background: rgba(42,157,143,0.15); border-color: rgba(42,157,143,0.4); color: #81E6D9; }

/* ── Metric row ── */
.metric-row { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 20px; }

/* ── Risk badge ── */
.risk-critical { color: #FC8181; font-weight: 700; }
.risk-high     { color: #F6AD55; font-weight: 700; }
.risk-medium   { color: #F6E05E; font-weight: 600; }
.risk-low      { color: #68D391; font-weight: 600; }

/* ── Architecture flow ── */
.arch-flow {
    display: flex; flex-direction: column; align-items: center;
    gap: 0; font-family: 'Inter', sans-serif;
}
.arch-node {
    background: #1C2232; border: 1px solid #3D4F70;
    border-radius: 8px; padding: 10px 24px;
    font-size: 13px; font-weight: 500; color: #CBD5E0;
    min-width: 260px; text-align: center;
}
.arch-arrow { color: #E84A5F; font-size: 20px; line-height: 1.3; }

/* ── Demo badge ── */
.demo-banner {
    background: rgba(244,162,97,0.12); border: 1px solid rgba(244,162,97,0.35);
    border-radius: 8px; padding: 8px 16px; margin-bottom: 16px;
    font-size: 12px; color: #F4A261; font-weight: 500;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] { background: #0D1117 !important; }
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stDateInput label,
section[data-testid="stSidebar"] .stCheckbox label { color: #A0AEC0 !important; font-size: 12px !important; }

/* ── Tables ── */
.stDataFrame { border-radius: 10px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# SESSION STATE — train model once per session
# =============================================================================
@st.cache_data(show_spinner=False)
def get_hotspot_data():
    return load_hotspot_data()


@st.cache_data(show_spinner=False)
def get_timeseries():
    return load_timeseries_data()


@st.cache_resource(show_spinner=False)
def get_trained_model(model_name: str, _df_hash: int):
    hotspot_df = load_hotspot_data()
    return train_model(hotspot_df, model_name)


# =============================================================================
# SIDEBAR
# =============================================================================
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 12px 0 20px;">
        <div style="font-size:32px;">🛰️</div>
        <div style="font-size:14px; font-weight:700; color:#F7FAFC;">Urban Heat AI</div>
        <div style="font-size:10px; color:#718096; margin-top:2px;">Bharatiya Antariksh Hackathon 2026</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**CONTROL PANEL**")

    selected_city = st.selectbox(
        "Pilot City",
        ["Chhatrapati Sambhajinagar", "Pune (Future)", "Nagpur (Future)", "Mumbai (Future)"],
        index=0,
    )
    selected_date = st.date_input(
        "Analysis Date",
        value=date(2025, 5, 15),
        min_value=date(2023, 1, 1),
        max_value=date.today(),
    )
    selected_source = st.selectbox("Data Source", DATA_SOURCES)
    selected_model  = st.selectbox("AI/ML Model",  ML_MODELS)
    selected_strat  = st.selectbox("Mitigation Strategy", MITIGATION_STRATEGIES)

    st.markdown("---")
    st.markdown("**MAP LAYERS**")
    show_hotspots = st.checkbox("Show Heat Hotspots",       value=True)
    show_recs     = st.checkbox("Show Mitigation Zones",    value=True)

    st.markdown("---")
    st.markdown("**THRESHOLDS**")
    lst_threshold = st.slider("LST Alert Threshold (°C)", 34.0, 46.0, 39.0, 0.5)
    risk_filter   = st.multiselect(
        "Filter Risk Levels",
        ["Critical", "High", "Medium", "Low"],
        default=["Critical", "High", "Medium", "Low"],
    )

    st.markdown("---")
    st.markdown(f"""
    <div style="font-size:10px; color:#4A5568; text-align:center; padding-bottom:8px;">
        Version {VERSION}<br>Team Moon · ISRO BAH 2026<br>
        <span style="color:#F4A261;">⚠ Prototype / Demo Data</span>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# DATA + MODEL LOAD
# =============================================================================
hotspot_df   = get_hotspot_data()
timeseries_df = get_timeseries()
kpi           = get_kpi_values()

# Filter by risk
hotspot_filtered = hotspot_df[hotspot_df["risk_level"].isin(risk_filter)].copy()

# Train model
with st.spinner("Running AI model training..."):
    df_hash = len(hotspot_df)
    model, scaler, metrics, X_test, y_test, y_pred = get_trained_model(selected_model, df_hash)

# Mitigation predictions
predicted_df = predict_after_mitigation(model, scaler, hotspot_filtered, selected_strat)
impact       = compute_impact_summary(predicted_df)
feature_imp  = get_feature_importances(model, selected_model)
mitigation_table = load_mitigation_table(hotspot_filtered)
strategy_report  = generate_strategy_report(hotspot_filtered, selected_strat)


# =============================================================================
# ── SECTION 1: HEADER ────────────────────────────────────────────────────────
# =============================================================================
st.markdown(f"""
<div class="dashboard-header">
    <div class="header-title">🛰️ {PROJECT_TITLE}</div>
    <div class="header-sub">{PROJECT_SUBTITLE}</div>
    <div class="header-badges">
        <span class="badge badge-accent">🌡 Pilot: {PILOT_CITY}</span>
        <span class="badge badge-green">🚀 {HACKATHON_NAME}</span>
        <span class="badge">👥 {TEAM_NAME}</span>
        <span class="badge">📅 {selected_date.strftime('%d %b %Y')}</span>
        <span class="badge">📡 {selected_source.split(' ')[0]}</span>
        <span class="badge" style="color:#F4A261; border-color:rgba(244,162,97,0.4);">⚠ Prototype / Demo Data</span>
    </div>
</div>
""", unsafe_allow_html=True)


# =============================================================================
# ── SECTION 2: KPI CARDS ─────────────────────────────────────────────────────
# =============================================================================
def kpi_card(label, value, unit, icon, accent="#E84A5F", delta_text=""):
    delta_html = f'<div class="kpi-delta" style="color:{accent};">{delta_text}</div>' if delta_text else ""
    return f"""
    <div class="kpi-card" style="--accent:{accent};">
        <div style="font-size:22px; margin-bottom:4px;">{icon}</div>
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-unit">{unit}</div>
        {delta_html}
    </div>"""

st.markdown('<div class="section-title"><span class="dot"></span> Real-Time KPI Overview</div>', unsafe_allow_html=True)

cols = st.columns(4)
kpi_data = [
    ("Avg Land Surface Temp",   f"{kpi['avg_lst']}", "°C", "🌡️", "#E84A5F", "▲ +2.4°C vs 5yr avg"),
    ("Mean Surface Albedo",     f"{kpi['mean_albedo']:.3f}", "reflectivity", "#F4A261", "#F4A261", "▼ Low — mitigation needed"),
    ("Tree Cover Density",      f"{kpi['tree_cover']}", "%", "🌳", "#2A9D8F", "▼ Below 30% benchmark"),
    ("Building Density",        f"{kpi['building_density']}", "%", "🏙️", "#9F7AEA", "High density zones"),
]
for i, (label, val, unit, icon, accent, delta) in enumerate(kpi_data):
    with cols[i]:
        st.markdown(kpi_card(label, val, unit, icon, accent, delta), unsafe_allow_html=True)

cols2 = st.columns(4)
kpi_data2 = [
    ("Heat Hotspot Zones",      f"{kpi['hotspot_count']}", "active zones", "🔴", "#E84A5F", f"⚠ {int(kpi['hotspot_count']*0.35)} critical"),
    ("Relative Humidity",       f"{kpi['humidity']}", "%", "💧", "#63B3ED", "Low — exacerbates heat"),
    ("Wind Speed",              f"{kpi['wind_speed']}", "m/s", "🌬️", "#81E6D9", "Moderate ventilation"),
    ("Urban Heat Risk Index",   f"{kpi['risk_index']}", "/ 10", "⚡", "#FC8181", "HIGH — immediate action"),
]
for i, (label, val, unit, icon, accent, delta) in enumerate(kpi_data2):
    with cols2[i]:
        st.markdown(kpi_card(label, val, unit, icon, accent, delta), unsafe_allow_html=True)

st.markdown("")


# =============================================================================
# ── SECTION 3: INTERACTIVE GIS MAP ───────────────────────────────────────────
# =============================================================================
st.markdown('<div class="section-title"><span class="dot"></span> Interactive Urban Heat Map — Chhatrapati Sambhajinagar</div>', unsafe_allow_html=True)
st.markdown("""
<div class="demo-banner">
    ⚠ Prototype / Demo Data — Hotspot locations and LST values are synthetically generated to represent plausible urban heat patterns.
    In production, data streams from Landsat 8 / ECOSTRESS / Sentinel-2 via Google Earth Engine pipeline.
</div>
""", unsafe_allow_html=True)

map_col, info_col = st.columns([3, 1])
with map_col:
    heat_map = build_heat_map(hotspot_filtered, show_hotspots, show_recs)
    st_folium(heat_map, width="100%", height=520, returned_objects=[])

with info_col:
    st.markdown('<div class="section-card" style="padding:16px;">', unsafe_allow_html=True)
    st.markdown("**Zone Summary**")
    risk_counts = hotspot_filtered["risk_level"].value_counts()
    for rl, color in [("Critical","#CC0000"), ("High","#E84A5F"), ("Medium","#F4A261"), ("Low","#2A9D8F")]:
        cnt = risk_counts.get(rl, 0)
        bar = "█" * min(cnt, 12) + "░" * max(0, 12 - cnt)
        st.markdown(f"""
        <div style="margin-bottom:12px;">
            <div style="font-size:11px; color:#A0AEC0; margin-bottom:2px;">{rl}</div>
            <div style="font-size:18px; font-weight:700; color:{color};">{cnt}</div>
            <div style="font-size:10px; font-family:'JetBrains Mono',monospace; color:{color}; opacity:0.7;">{bar}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**Avg Metrics**")
    avg_lst_filt = hotspot_filtered["lst"].mean() if len(hotspot_filtered) else 0
    avg_ndvi     = hotspot_filtered["ndvi"].mean() if len(hotspot_filtered) else 0
    avg_bd       = hotspot_filtered["building_density"].mean() if len(hotspot_filtered) else 0
    for label, val, unit in [
        ("Avg LST",  f"{avg_lst_filt:.1f}", "°C"),
        ("Avg NDVI", f"{avg_ndvi:.3f}", ""),
        ("Avg Bldg", f"{avg_bd:.1f}", "%"),
    ]:
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:6px;">
            <span style="color:#A0AEC0;">{label}</span>
            <span style="font-weight:600;">{val} {unit}</span>
        </div>""", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("")


# =============================================================================
# ── SECTION 4: AI/ML PREDICTION ──────────────────────────────────────────────
# =============================================================================
st.markdown('<div class="section-title"><span class="dot"></span> AI/ML Model — LST Prediction & Mitigation Simulation</div>', unsafe_allow_html=True)

pred_col, metric_col = st.columns([2, 1])

with pred_col:
    st.markdown(f"**Model:** `{selected_model}` &nbsp;|&nbsp; **Strategy Simulated:** `{selected_strat}`")

    avg_before = predicted_df["lst"].mean()
    avg_after  = predicted_df["predicted_lst"].mean()
    avg_reduc  = avg_before - avg_after

    # Prediction scatter
    fig_scatter = go.Figure()
    fig_scatter.add_trace(go.Scatter(
        x=y_test, y=y_pred,
        mode="markers",
        marker=dict(
            color=y_pred, colorscale="RdYlGn_r",
            size=8, opacity=0.75,
            colorbar=dict(title="Pred LST (°C)", thickness=14),
            line=dict(width=0.5, color="#1C2232"),
        ),
        name="Predicted vs Actual",
        hovertemplate="Actual: %{x:.2f}°C<br>Predicted: %{y:.2f}°C<extra></extra>",
    ))
    mn = min(y_test.min(), y_pred.min()) - 0.5
    mx = max(y_test.max(), y_pred.max()) + 0.5
    fig_scatter.add_trace(go.Scatter(
        x=[mn, mx], y=[mn, mx],
        mode="lines", line=dict(color="#4A5568", width=1.5, dash="dash"),
        name="Perfect Prediction", showlegend=True,
    ))
    fig_scatter.update_layout(
        title=dict(text="Actual vs Predicted LST (Test Set)", font=dict(size=13, color="#CBD5E0")),
        xaxis=dict(title="Actual LST (°C)", color="#718096", gridcolor="#2D3748"),
        yaxis=dict(title="Predicted LST (°C)", color="#718096", gridcolor="#2D3748"),
        paper_bgcolor="#161C2D", plot_bgcolor="#161C2D",
        font=dict(family="Inter", color="#A0AEC0"),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
        height=340, margin=dict(l=10, r=10, t=40, b=10),
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

with metric_col:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("**Model Performance**")
    for label, val, color in [
        ("RMSE",            f"{metrics['rmse']} °C", "#F4A261"),
        ("MAE",             f"{metrics['mae']} °C",  "#F4A261"),
        ("R² Score",        f"{metrics['r2']}",      "#2A9D8F"),
        ("Confidence",      f"{metrics['confidence_score']}%", "#68D391"),
        ("Training Samples",f"{metrics['n_train']}",  "#A0AEC0"),
        ("Test Samples",    f"{metrics['n_test']}",   "#A0AEC0"),
    ]:
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;padding:5px 0;
                    border-bottom:1px solid #2D3748;font-size:13px;">
            <span style="color:#718096;">{label}</span>
            <span style="color:{color}; font-weight:600;">{val}</span>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>**Mitigation Impact**")
    for label, val, color in [
        ("Current Avg LST",   f"{avg_before:.2f} °C", "#E84A5F"),
        ("Post-Mitigation",   f"{avg_after:.2f} °C",  "#2A9D8F"),
        ("Est. Reduction",    f"−{avg_reduc:.2f} °C", "#68D391"),
    ]:
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;padding:5px 0;
                    border-bottom:1px solid #2D3748;font-size:13px;">
            <span style="color:#718096;">{label}</span>
            <span style="color:{color}; font-weight:600;">{val}</span>
        </div>""", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# =============================================================================
# ── SECTION 5: FEATURE IMPORTANCE ────────────────────────────────────────────
# =============================================================================
st.markdown('<div class="section-title"><span class="dot"></span> Random Forest Feature Importance</div>', unsafe_allow_html=True)

fi_col, driver_col = st.columns([1, 1])

with fi_col:
    fig_fi = go.Figure(go.Bar(
        x=feature_imp["Importance"],
        y=feature_imp["Feature"],
        orientation="h",
        marker=dict(
            color=feature_imp["Importance"],
            colorscale=[
                [0.0, "#2A9D8F"], [0.4, "#F4A261"], [0.7, "#E84A5F"], [1.0, "#CC0000"]
            ],
            line=dict(width=0),
        ),
        text=[f"{v:.3f}" for v in feature_imp["Importance"]],
        textposition="outside",
        textfont=dict(size=11, color="#A0AEC0"),
        hovertemplate="%{y}: %{x:.4f}<extra></extra>",
    ))
    fig_fi.update_layout(
        title=dict(text="Feature Importance Scores", font=dict(size=13, color="#CBD5E0")),
        xaxis=dict(title="Importance", color="#718096", gridcolor="#2D3748"),
        yaxis=dict(color="#A0AEC0", tickfont=dict(size=11)),
        paper_bgcolor="#161C2D", plot_bgcolor="#161C2D",
        font=dict(family="Inter", color="#A0AEC0"),
        height=340, margin=dict(l=10, r=60, t=40, b=10),
    )
    st.plotly_chart(fig_fi, use_container_width=True)

with driver_col:
    # LST vs Building Density
    fig_bd = px.scatter(
        hotspot_filtered, x="building_density", y="lst",
        color="risk_level",
        color_discrete_map={
            "Critical": "#CC0000", "High": "#E84A5F",
            "Medium": "#F4A261", "Low": "#2A9D8F"
        },
        size="building_density", size_max=18,
        labels={"building_density": "Building Density (%)", "lst": "LST (°C)"},
        title="Building Density vs LST",
        hover_data=["zone", "zone_type"],
    )
    fig_bd.update_layout(
        paper_bgcolor="#161C2D", plot_bgcolor="#161C2D",
        font=dict(family="Inter", color="#A0AEC0"),
        xaxis=dict(gridcolor="#2D3748"), yaxis=dict(gridcolor="#2D3748"),
        height=340, margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
    )
    st.plotly_chart(fig_bd, use_container_width=True)


# =============================================================================
# ── SECTION 6: URBAN HEAT DRIVER ANALYSIS ────────────────────────────────────
# =============================================================================
st.markdown('<div class="section-title"><span class="dot"></span> Urban Heat Driver Analysis</div>', unsafe_allow_html=True)

d1, d2, d3 = st.columns(3)


def _scatter_with_trendline(df, x_col, y_col, title, x_label, y_label):
    """Build a Plotly scatter + numpy linear trendline (no statsmodels needed)."""
    color_map = {"Critical":"#CC0000","High":"#E84A5F","Medium":"#F4A261","Low":"#2A9D8F"}
    fig = go.Figure()
    for risk, color in color_map.items():
        sub = df[df["risk_level"] == risk]
        if sub.empty:
            continue
        fig.add_trace(go.Scatter(
            x=sub[x_col], y=sub[y_col],
            mode="markers",
            marker=dict(color=color, size=8, opacity=0.8, line=dict(width=0.5, color="#1C2232")),
            name=risk,
            hovertemplate=f"{x_label}: %{{x:.3f}}<br>{y_label}: %{{y:.1f}} °C<extra>{risk}</extra>",
        ))
    # Linear trendline via numpy polyfit
    x_vals = df[x_col].values
    y_vals = df[y_col].values
    if len(x_vals) > 2:
        z = np.polyfit(x_vals, y_vals, 1)
        p = np.poly1d(z)
        x_line = np.linspace(x_vals.min(), x_vals.max(), 60)
        fig.add_trace(go.Scatter(
            x=x_line, y=p(x_line),
            mode="lines",
            line=dict(color="rgba(255,255,255,0.45)", width=1.5, dash="dot"),
            name="Trend", showlegend=False,
        ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=13, color="#CBD5E0")),
        xaxis=dict(title=x_label, gridcolor="#2D3748", color="#718096"),
        yaxis=dict(title=y_label, gridcolor="#2D3748", color="#718096"),
        paper_bgcolor="#161C2D", plot_bgcolor="#161C2D",
        font=dict(family="Inter", color="#A0AEC0"),
        height=300, margin=dict(l=5, r=5, t=40, b=5),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=9), title_text=""),
        showlegend=False,
    )
    return fig


with d1:
    fig1 = _scatter_with_trendline(
        hotspot_filtered, "albedo", "lst",
        "Albedo vs LST", "Surface Albedo", "LST (°C)"
    )
    st.plotly_chart(fig1, use_container_width=True)

with d2:
    fig2 = _scatter_with_trendline(
        hotspot_filtered, "ndvi", "lst",
        "NDVI vs LST", "NDVI", "LST (°C)"
    )
    st.plotly_chart(fig2, use_container_width=True)

with d3:
    fig3 = _scatter_with_trendline(
        hotspot_filtered, "tree_cover", "lst",
        "Tree Cover vs LST", "Tree Cover (%)", "LST (°C)"
    )
    st.plotly_chart(fig3, use_container_width=True)

# LST monthly trend
st.markdown("")
fig_ts = go.Figure()
fig_ts.add_trace(go.Scatter(
    x=timeseries_df["month"], y=timeseries_df["max_lst"],
    fill=None, mode="lines", line=dict(width=0),
    showlegend=False, hoverinfo="skip",
))
fig_ts.add_trace(go.Scatter(
    x=timeseries_df["month"], y=timeseries_df["min_lst"],
    fill="tonexty", mode="lines", line=dict(width=0),
    fillcolor="rgba(232,74,95,0.12)", showlegend=False, hoverinfo="skip",
))
fig_ts.add_trace(go.Scatter(
    x=timeseries_df["month"], y=timeseries_df["avg_lst"],
    mode="lines+markers",
    line=dict(color="#E84A5F", width=2.5),
    marker=dict(size=7, color="#E84A5F"),
    name="Avg LST",
    hovertemplate="%{x|%b %Y}: %{y:.2f} °C<extra></extra>",
))
fig_ts.add_hline(
    y=lst_threshold, line_dash="dot", line_color="#F4A261",
    annotation_text=f"Alert threshold: {lst_threshold}°C",
    annotation_font_color="#F4A261",
)
fig_ts.update_layout(
    title=dict(text="Monthly Average LST Trend — 2024 (Prototype Data)", font=dict(size=13, color="#CBD5E0")),
    xaxis=dict(color="#718096", gridcolor="#2D3748"),
    yaxis=dict(title="Avg LST (°C)", color="#718096", gridcolor="#2D3748"),
    paper_bgcolor="#161C2D", plot_bgcolor="#161C2D",
    font=dict(family="Inter", color="#A0AEC0"),
    height=280, margin=dict(l=10, r=10, t=40, b=10),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
)
st.plotly_chart(fig_ts, use_container_width=True)


# =============================================================================
# ── SECTION 7: MITIGATION RECOMMENDATION TABLE ───────────────────────────────
# =============================================================================
st.markdown('<div class="section-title"><span class="dot"></span> Mitigation Recommendation Engine</div>', unsafe_allow_html=True)

# Display mitigation recommendations in a standard table to avoid optional matplotlib dependency.
st.dataframe(
    mitigation_table,
    use_container_width=True,
    height=420,
)


# =============================================================================
# ── SECTION 8: BEFORE vs AFTER IMPACT ────────────────────────────────────────
# =============================================================================
st.markdown('<div class="section-title"><span class="dot"></span> Before vs After Mitigation — Impact Assessment</div>', unsafe_allow_html=True)

imp_cols = st.columns(4)
impact_kpis = [
    ("Current Avg LST",       f"{impact['avg_lst_before']} °C",   "Before mitigation",      "#E84A5F"),
    ("Post-Mitigation LST",   f"{impact['avg_lst_after']} °C",    "AI model projection",    "#2A9D8F"),
    ("Estimated Cooling",     f"−{impact['total_cooling']} °C",   "City-wide average",      "#68D391"),
    ("Hotspot Zones Reduced", f"{impact['hotspots_reduced']}",    f"of {len(hotspot_filtered)} zones","#F6AD55"),
]
for i, (label, val, unit, accent) in enumerate(impact_kpis):
    with imp_cols[i]:
        st.markdown(kpi_card(label, val, unit, "", accent), unsafe_allow_html=True)

imp_cols2 = st.columns(3)
impact_kpis2 = [
    ("People Benefited",       f"{impact['people_benefited']:,}",  "residents",         "#63B3ED"),
    ("Energy Saving (est.)",   f"{impact['energy_saving_MWh']:,.0f}", "MWh / year",     "#F6E05E"),
    ("CO₂ Reduction (est.)",   f"{impact['co2_reduction_tons']:,.0f}", "tonnes CO₂/yr", "#81E6D9"),
]
for i, (label, val, unit, accent) in enumerate(impact_kpis2):
    with imp_cols2[i]:
        st.markdown(kpi_card(label, val, unit, "", accent), unsafe_allow_html=True)

st.markdown("")

# Before/After bar chart
ba_col1, ba_col2 = st.columns(2)
with ba_col1:
    top_zones = predicted_df.nlargest(10, "lst")
    fig_ba = go.Figure()
    fig_ba.add_trace(go.Bar(
        name="Current LST",
        x=top_zones["zone"],
        y=top_zones["lst"],
        marker_color="#E84A5F",
        opacity=0.85,
    ))
    fig_ba.add_trace(go.Bar(
        name="Post-Mitigation LST",
        x=top_zones["zone"],
        y=top_zones["predicted_lst"],
        marker_color="#2A9D8F",
        opacity=0.85,
    ))
    fig_ba.update_layout(
        title=dict(text="Top 10 Hotspots — Before vs After LST", font=dict(size=13, color="#CBD5E0")),
        barmode="group",
        xaxis=dict(color="#718096", gridcolor="#2D3748", tickangle=-30),
        yaxis=dict(title="LST (°C)", color="#718096", gridcolor="#2D3748"),
        paper_bgcolor="#161C2D", plot_bgcolor="#161C2D",
        font=dict(family="Inter", color="#A0AEC0"),
        height=340, margin=dict(l=10, r=10, t=40, b=60),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
    )
    st.plotly_chart(fig_ba, use_container_width=True)

with ba_col2:
    # LST reduction distribution
    fig_reduc = px.histogram(
        predicted_df, x="lst_reduction",
        nbins=14,
        title="Distribution of Estimated LST Reduction",
        labels={"lst_reduction": "LST Reduction (°C)", "count": "Zones"},
        color_discrete_sequence=["#2A9D8F"],
    )
    fig_reduc.update_traces(marker_line_width=0.5, marker_line_color="#0F1626")
    fig_reduc.update_layout(
        paper_bgcolor="#161C2D", plot_bgcolor="#161C2D",
        font=dict(family="Inter", color="#A0AEC0"),
        xaxis=dict(gridcolor="#2D3748"), yaxis=dict(gridcolor="#2D3748"),
        height=340, margin=dict(l=10, r=10, t=40, b=10),
    )
    st.plotly_chart(fig_reduc, use_container_width=True)


# =============================================================================
# ── SECTION 9: MITIGATION STRATEGY DETAILS (Expandable) ──────────────────────
# =============================================================================
st.markdown('<div class="section-title"><span class="dot"></span> Strategic Mitigation Interventions</div>', unsafe_allow_html=True)

strategies_info = {
    "🏠 Cool Roofs": {
        "desc": "Application of high-reflectivity materials to rooftop surfaces reduces absorbed solar radiation, cutting roof temperatures by 10–30°C.",
        "points": [
            "Increase surface albedo from ~0.15 to 0.60–0.80",
            "Reduce indoor cooling energy demand by 15–25%",
            "Most effective in high-density residential and industrial zones",
            "Materials: white elastomeric coatings, cool tiles, reflective membranes",
        ],
        "zones": "Zone A, B, D, G", "impact": "2.0–3.5°C", "timeline": "4–6 months", "color": "#63B3ED",
    },
    "🌳 Tree Plantation": {
        "desc": "Strategic urban forestation along roads, parks, and residential blocks improves shading and evapotranspiration.",
        "points": [
            "Each mature tree cools 1–2°C in its immediate shade zone",
            "Improves NDVI from <0.15 to >0.30 over 3–5 years",
            "Reduces pedestrian heat stress index significantly",
            "Recommended species: Neem, Peepal, Rain Tree, Curry Leaf",
        ],
        "zones": "Zone A, C, E, H", "impact": "1.5–3.0°C", "timeline": "6–12 months", "color": "#68D391",
    },
    "🌿 Green Spaces": {
        "desc": "Development of parks, urban gardens, and vegetated areas in open/peri-urban lands creates urban cooling islands.",
        "points": [
            "Parks >2 ha create measurable cooling effect up to 300m radius",
            "Reduces stormwater runoff and improves air quality",
            "Supports biodiversity and citizen well-being",
            "Compatible with existing open land parcels",
        ],
        "zones": "Zone C, F, I", "impact": "1.0–2.5°C", "timeline": "8–18 months", "color": "#2A9D8F",
    },
    "🛣️ Reflective Pavement": {
        "desc": "High-albedo pavement surfaces in commercial corridors and arterial roads reduce heat absorption from road infrastructure.",
        "points": [
            "Replaces standard asphalt (albedo ~0.05) with light-coloured or permeable pavers",
            "Reduces pavement surface temperature by 5–15°C",
            "Highly effective in commercial zones with wide road profiles",
            "Combines well with roadside tree plantation",
        ],
        "zones": "Zone B, D, G", "impact": "1.0–2.0°C", "timeline": "4–8 months", "color": "#F4A261",
    },
    "🌐 Green Corridors": {
        "desc": "Continuous vegetated pathways linking parks, water bodies, and green patches to improve urban ventilation and cooling distribution.",
        "points": [
            "Connects fragmented vegetation into a coherent cooling network",
            "Improves urban airflow and reduces heat island extent",
            "Supports ecological connectivity and microclimatic regulation",
            "Prioritise alignment with prevailing wind direction (SW–NE in city)",
        ],
        "zones": "City-wide priority corridors", "impact": "0.8–1.5°C", "timeline": "12–24 months", "color": "#9F7AEA",
    },
}

for strat_name, info in strategies_info.items():
    with st.expander(f"{strat_name} &nbsp;·&nbsp; Est. Cooling: {info['impact']}", expanded=False):
        sc1, sc2 = st.columns([3, 1])
        with sc1:
            st.markdown(f"<p style='color:#A0AEC0; font-size:13px; margin-bottom:10px;'>{info['desc']}</p>", unsafe_allow_html=True)
            for pt in info["points"]:
                st.markdown(f"<div style='font-size:12px; color:#CBD5E0; margin-bottom:4px;'>▸ {pt}</div>", unsafe_allow_html=True)
        with sc2:
            st.markdown(f"""
            <div style="background:#1C2232; border:1px solid {info['color']}44; border-radius:10px; padding:14px; text-align:center;">
                <div style="font-size:10px; color:#A0AEC0; margin-bottom:6px;">COOLING POTENTIAL</div>
                <div style="font-size:22px; font-weight:700; color:{info['color']};">{info['impact']}</div>
                <div style="font-size:10px; color:#A0AEC0; margin-top:10px;">TIMELINE</div>
                <div style="font-size:14px; color:#CBD5E0; font-weight:600;">{info['timeline']}</div>
                <div style="font-size:10px; color:#A0AEC0; margin-top:10px;">TARGET ZONES</div>
                <div style="font-size:11px; color:{info['color']};">{info['zones']}</div>
            </div>""", unsafe_allow_html=True)


# =============================================================================
# ── SECTION 10: ARCHITECTURE DIAGRAM ─────────────────────────────────────────
# =============================================================================
st.markdown('<div class="section-title"><span class="dot"></span> System Architecture & Data Pipeline</div>', unsafe_allow_html=True)

arch_col, pipe_col = st.columns([1, 1])

with arch_col:
    arch_nodes = [
        ("🛰️ Satellite Data", "Landsat 8 · Sentinel-2 · ECOSTRESS · ERA5"),
        ("🌍 Google Earth Engine", "Band extraction · LST · NDVI · Albedo"),
        ("🧹 Data Cleaning & Processing", "Spatial joins · Reprojection · Feature engineering"),
        ("🗄️ PostgreSQL + PostGIS", "Spatial database · Raster storage · Query engine"),
        ("🤖 Random Forest AI Model", "LST prediction · Feature importance · Cross-validation"),
        ("💡 Mitigation Recommendation Engine", "Zone scoring · Strategy ranking · Impact estimation"),
        ("📊 Streamlit Dashboard", "Interactive maps · KPI cards · Download reports"),
        ("🏛️ City Planners / Authorities", "Decision support · Action planning · Monitoring"),
    ]
    flow_html = '<div class="arch-flow">'
    for i, (node, sub) in enumerate(arch_nodes):
        flow_html += f"""
        <div class="arch-node">
            <div style="font-weight:600; font-size:13px;">{node}</div>
            <div style="font-size:10px; color:#718096; margin-top:2px;">{sub}</div>
        </div>"""
        if i < len(arch_nodes) - 1:
            flow_html += '<div class="arch-arrow">↓</div>'
    flow_html += "</div>"
    st.markdown(flow_html, unsafe_allow_html=True)

with pipe_col:
    st.markdown("""
    <div class="section-card">
    <div style="font-size:13px; color:#CBD5E0; font-weight:600; margin-bottom:12px;">Data Pipeline Explanation</div>
    <div style="font-size:12px; color:#A0AEC0; line-height:1.7;">
    Satellite and environmental datasets are ingested via <b style="color:#CBD5E0;">Google Earth Engine</b>
    to extract key biophysical variables: Land Surface Temperature (LST), surface albedo,
    Normalized Difference Vegetation Index (NDVI), building and road density, and ERA5
    meteorological reanalysis fields.<br><br>
    These features are stored in a <b style="color:#CBD5E0;">PostgreSQL + PostGIS</b> spatial database
    that enables efficient geo-queries by ward, buffer zone, or administrative boundary.<br><br>
    A <b style="color:#CBD5E0;">Random Forest Regressor</b> trained on this feature set predicts LST
    for any zone under both current and simulated mitigation conditions. Feature importance
    analysis reveals the dominant heat drivers, and the <b style="color:#CBD5E0;">Mitigation
    Recommendation Engine</b> ranks interventions by estimated cooling potential, feasibility,
    and priority score.<br><br>
    All outputs are served through this <b style="color:#CBD5E0;">Streamlit dashboard</b>
    enabling city planners to make evidence-based decisions.
    </div>
    </div>
    <div class="section-card" style="margin-top:12px;">
    <div style="font-size:13px; color:#CBD5E0; font-weight:600; margin-bottom:12px;">Tech Stack</div>
    """, unsafe_allow_html=True)

    tech_items = [
        ("Remote Sensing",  "Landsat 8, Sentinel-2, ECOSTRESS, ERA5"),
        ("Processing",      "Google Earth Engine, Rasterio, GeoPandas"),
        ("AI/ML",           "Scikit-learn · Random Forest Regressor"),
        ("Spatial DB",      "PostgreSQL 15 + PostGIS 3.4"),
        ("Visualization",   "Folium, Plotly, Streamlit"),
        ("Language",        "Python 3.11"),
    ]
    for tech, detail in tech_items:
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;padding:5px 0;
                    border-bottom:1px solid #2D3748;font-size:12px;">
            <span style="color:#718096; width:120px;">{tech}</span>
            <span style="color:#CBD5E0;">{detail}</span>
        </div>""", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# =============================================================================
# ── SECTION 11: DOWNLOAD SECTION ─────────────────────────────────────────────
# =============================================================================
st.markdown('<div class="section-title"><span class="dot"></span> Export Reports & Data</div>', unsafe_allow_html=True)
st.markdown("""
<div class="demo-banner">
    ⚠ All exported files contain prototype/demo data. For production use, connect the PostgreSQL + PostGIS pipeline and replace demo data sources.
</div>
""", unsafe_allow_html=True)

dl1, dl2, dl3, dl4 = st.columns(4)

# ── Hotspot CSV ───────────────────────────────────────────────────────────────
with dl1:
    csv_hotspot = hotspot_filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇ Hotspot Report (CSV)",
        data=csv_hotspot,
        file_name=f"hotspot_report_{PILOT_CITY.replace(' ','_')}_{selected_date}.csv",
        mime="text/csv",
        use_container_width=True,
    )

# ── Mitigation CSV ────────────────────────────────────────────────────────────
with dl2:
    csv_mit = mitigation_table.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇ Mitigation Report (CSV)",
        data=csv_mit,
        file_name=f"mitigation_report_{selected_date}.csv",
        mime="text/csv",
        use_container_width=True,
    )

# ── GeoJSON ───────────────────────────────────────────────────────────────────
with dl3:
    geojson_features = []
    for _, row in hotspot_filtered.iterrows():
        geojson_features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [row["lon"], row["lat"]]},
            "properties": {
                "zone": row["zone"], "lst": row["lst"],
                "risk_level": row["risk_level"],
                "intervention": row["recommended_intervention"],
                "cooling": row["estimated_cooling"],
                "data_note": "Prototype / Demo Data",
            },
        })
    geojson_data = json.dumps(
        {"type": "FeatureCollection", "features": geojson_features}, indent=2
    ).encode("utf-8")
    st.download_button(
        label="⬇ GeoJSON Export",
        data=geojson_data,
        file_name=f"hotspots_{selected_date}.geojson",
        mime="application/json",
        use_container_width=True,
    )

# ── Model Metrics ─────────────────────────────────────────────────────────────
with dl4:
    metrics_export = {
        **metrics,
        "model": selected_model,
        "strategy": selected_strat,
        "city": PILOT_CITY,
        "date": str(selected_date),
        "avg_lst_before": impact["avg_lst_before"],
        "avg_lst_after":  impact["avg_lst_after"],
        "total_cooling":  impact["total_cooling"],
        "data_note":      "Prototype / Demo Data",
    }
    metrics_df = pd.DataFrame([metrics_export])
    st.download_button(
        label="⬇ Model Metrics (CSV)",
        data=metrics_df.to_csv(index=False).encode("utf-8"),
        file_name=f"model_metrics_{selected_date}.csv",
        mime="text/csv",
        use_container_width=True,
    )


# =============================================================================
# ── FOOTER ────────────────────────────────────────────────────────────────────
# =============================================================================
st.markdown("---")
st.markdown(f"""
<div style="text-align:center; padding: 16px 0; font-size:11px; color:#4A5568; font-family:'Inter',sans-serif;">
    <b style="color:#718096;">{PROJECT_TITLE}</b> &nbsp;·&nbsp;
    {TEAM_NAME} &nbsp;·&nbsp; {HACKATHON_NAME} &nbsp;·&nbsp; Version {VERSION}<br>
    <span style="color:#F4A261;">⚠ All data shown is prototype/demo data for hackathon evaluation purposes only.</span><br>
    Data Sources Referenced: Landsat 8 (USGS/NASA) · Sentinel-2 (ESA) · ECOSTRESS (NASA/JPL) · ERA5 (ECMWF) · CPCB · OpenStreetMap
</div>
""", unsafe_allow_html=True)
