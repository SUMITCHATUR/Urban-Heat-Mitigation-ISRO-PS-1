# =============================================================================
# utils/map_utils.py — Folium map builder for heat hotspots & recommendations
# Team Moon | ISRO Bharatiya Antariksh Hackathon 2026
# =============================================================================
import folium
from folium.plugins import HeatMap, MarkerCluster
import pandas as pd
import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from config import MAP_CENTER_LAT, MAP_CENTER_LON, MAP_ZOOM_START


# ── Color helpers ─────────────────────────────────────────────────────────────

def _risk_color(risk: str) -> str:
    return {
        "Critical": "#CC0000",
        "High":     "#E84A5F",
        "Medium":   "#F4A261",
        "Low":      "#2A9D8F",
    }.get(risk, "#888888")


def _circle_radius(lst: float) -> int:
    """Scale circle radius with LST."""
    base = 300
    return int(base + (lst - 34) * 60)


def _popup_html(row: pd.Series) -> str:
    color = _risk_color(row["risk_level"])
    return f"""
    <div style="font-family:Segoe UI,sans-serif; width:240px; padding:4px;">
      <h4 style="margin:0 0 6px; color:{color};">{row['zone']} — {row['zone_type']}</h4>
      <table style="width:100%; font-size:12px; border-collapse:collapse;">
        <tr><td style="padding:2px 4px;"><b>Current LST</b></td>
            <td style="color:{color}; font-weight:700;">{row['lst']} °C</td></tr>
        <tr><td style="padding:2px 4px;"><b>Risk Level</b></td>
            <td style="color:{color}; font-weight:700;">{row['risk_level']}</td></tr>
        <tr><td style="padding:2px 4px;"><b>NDVI</b></td>
            <td>{row['ndvi']}</td></tr>
        <tr><td style="padding:2px 4px;"><b>Albedo</b></td>
            <td>{row['albedo']}</td></tr>
        <tr><td style="padding:2px 4px;"><b>Bldg Density</b></td>
            <td>{row['building_density']} %</td></tr>
        <tr><td style="padding:2px 4px;"><b>Heat Driver</b></td>
            <td>{row['main_driver']}</td></tr>
        <tr style="background:#f0f0f0;">
          <td style="padding:2px 4px;"><b>Intervention</b></td>
          <td><b>{row['recommended_intervention']}</b></td></tr>
        <tr><td style="padding:2px 4px;"><b>Est. Cooling</b></td>
            <td style="color:#2A9D8F; font-weight:700;">−{row['estimated_cooling']} °C</td></tr>
        <tr><td style="padding:2px 4px;"><b>Priority</b></td>
            <td>{row['priority_score']}/100</td></tr>
        <tr><td colspan="2" style="font-size:9px; color:#888; padding-top:4px;">
            ⚠ Prototype / Demo Data</td></tr>
      </table>
    </div>"""


def _legend_html() -> str:
    return """
    <div style="
        position: fixed; bottom: 50px; left: 50px; z-index: 1000;
        background: rgba(14,17,23,0.92); border: 1px solid #444;
        border-radius: 8px; padding: 12px 16px;
        font-family: Segoe UI, sans-serif; font-size: 12px; color: #eee;
        min-width: 190px; box-shadow: 0 4px 16px rgba(0,0,0,0.5);">
      <b style="font-size:13px;">Map Legend</b><br><br>
      <span style="color:#CC0000;">⬤</span>&nbsp; Critical Heat Zone (&gt;41 °C)<br>
      <span style="color:#E84A5F;">⬤</span>&nbsp; High Heat Zone (39–41 °C)<br>
      <span style="color:#F4A261;">⬤</span>&nbsp; Medium Heat Zone (37–39 °C)<br>
      <span style="color:#2A9D8F;">⬤</span>&nbsp; Low Heat Zone (&lt;37 °C)<br>
      <span style="color:#4CAF50;">◆</span>&nbsp; Plantation Zone<br>
      <span style="color:#00BCD4;">◆</span>&nbsp; Cool Roof / Reflective Zone<br>
      <br><span style="font-size:10px; color:#888;">⚠ Prototype / Demo Data</span>
    </div>"""


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def build_heat_map(
    hotspot_df: pd.DataFrame,
    show_hotspots: bool = True,
    show_recommendations: bool = True,
    basemap: str = "CartoDB dark_matter",
) -> folium.Map:
    """
    Build and return a styled Folium map with:
      - Heat intensity circles (color-coded by risk)
      - HeatMap layer (density overlay)
      - Green plantation markers
      - Cool-roof / reflective pavement markers
      - Legend
    """
    m = folium.Map(
        location=[MAP_CENTER_LAT, MAP_CENTER_LON],
        zoom_start=MAP_ZOOM_START,
        tiles=basemap,
        attr="© OpenStreetMap contributors",
    )

    # ── HeatMap layer ─────────────────────────────────────────────────────────
    heat_data = [
        [row["lat"], row["lon"], (row["lst"] - 33) / 12]
        for _, row in hotspot_df.iterrows()
    ]
    HeatMap(
        heat_data,
        radius=30, blur=20, max_zoom=14,
        gradient={"0.3": "#2A9D8F", "0.55": "#F4A261",
                  "0.75": "#E84A5F", "1.0": "#CC0000"},
        name="LST Heatmap",
    ).add_to(m)

    # ── Hotspot circles ───────────────────────────────────────────────────────
    if show_hotspots:
        hotspot_layer = folium.FeatureGroup(name="Heat Hotspots", show=True)
        for _, row in hotspot_df.iterrows():
            folium.CircleMarker(
                location=[row["lat"], row["lon"]],
                radius=_circle_radius(row["lst"]) / 60,
                color=_risk_color(row["risk_level"]),
                fill=True,
                fill_color=_risk_color(row["risk_level"]),
                fill_opacity=0.55,
                weight=1.5,
                popup=folium.Popup(_popup_html(row), max_width=270),
                tooltip=f"{row['zone']} | {row['lst']} °C | {row['risk_level']}",
            ).add_to(hotspot_layer)
        hotspot_layer.add_to(m)

    # ── Recommendation markers ─────────────────────────────────────────────────
    if show_recommendations:
        rec_layer = folium.FeatureGroup(name="Mitigation Zones", show=True)
        for _, row in hotspot_df.iterrows():
            intervention = row["recommended_intervention"]
            if "Tree" in intervention or "Green Space" in intervention:
                icon_color, icon_name, marker_color = "green",  "leaf",      "green"
            elif "Cool Roof" in intervention or "Reflective" in intervention:
                icon_color, icon_name, marker_color = "blue",   "tint",      "cadetblue"
            else:
                icon_color, icon_name, marker_color = "orange", "arrows-alt","orange"

            folium.Marker(
                location=[row["lat"] + 0.003, row["lon"] + 0.003],
                icon=folium.Icon(color=marker_color, icon=icon_name, prefix="fa"),
                tooltip=(
                    f"🌿 {intervention} | "
                    f"Est. Cooling: −{row['estimated_cooling']} °C | "
                    f"Priority: {row['priority_score']}/100"
                ),
            ).add_to(rec_layer)
        rec_layer.add_to(m)

    # ── City boundary placeholder circle ─────────────────────────────────────
    folium.Circle(
        location=[MAP_CENTER_LAT, MAP_CENTER_LON],
        radius=8500,
        color="#444466",
        fill=False,
        weight=1.5,
        dash_array="8 4",
        tooltip="Chhatrapati Sambhajinagar City Boundary (approx.)",
    ).add_to(m)

    # ── Legend ────────────────────────────────────────────────────────────────
    m.get_root().html.add_child(folium.Element(_legend_html()))

    # ── Layer Control ─────────────────────────────────────────────────────────
    folium.LayerControl(collapsed=False).add_to(m)

    return m
