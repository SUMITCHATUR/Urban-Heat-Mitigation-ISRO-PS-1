# =============================================================================
# utils/data_loader.py — Demo data generation + optional DB loader
# Team Moon | ISRO Bharatiya Antariksh Hackathon 2026
# =============================================================================
import numpy as np
import pandas as pd
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from config import DEMO_KPI, DB_CONFIG, USE_DB

# ── Seed for reproducibility ──────────────────────────────────────────────────
RNG = np.random.default_rng(42)


def _clamp(arr, lo, hi):
    return np.clip(arr, lo, hi)


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def load_hotspot_data() -> pd.DataFrame:
    """
    Returns a DataFrame of synthetic urban hotspot zones around
    Chhatrapati Sambhajinagar.  Labelled as prototype/demo data.
    """
    n = 23
    # Scatter points around city centre
    lats = 19.8762 + RNG.uniform(-0.07, 0.07, n)
    lons = 75.3433 + RNG.uniform(-0.09, 0.09, n)

    lst   = _clamp(RNG.normal(38.6, 1.8, n), 34.0, 45.0)
    ndvi  = _clamp(RNG.normal(0.18, 0.07, n), 0.02, 0.45)
    alb   = _clamp(RNG.normal(0.15, 0.04, n), 0.05, 0.35)
    bd    = _clamp(RNG.normal(47, 12, n), 15, 85)
    rd    = _clamp(RNG.normal(0.35, 0.10, n), 0.10, 0.65)
    tc    = _clamp(RNG.normal(21, 8, n), 3, 48)
    hum   = _clamp(RNG.normal(42, 6, n), 25, 70)
    ws    = _clamp(RNG.normal(3.2, 0.8, n), 0.5, 6.5)
    aqi   = _clamp(RNG.normal(118, 25, n), 60, 200).astype(int)

    zone_types = [
        "High Density Residential", "Commercial District", "Industrial Zone",
        "Mixed Use", "Old City Core", "Peri-Urban", "Road Corridor",
        "Institutional", "Sparse Residential",
    ]

    def risk(t):
        if t >= 41:   return "Critical"
        elif t >= 39: return "High"
        elif t >= 37: return "Medium"
        else:         return "Low"

    def mitigation(row):
        """Generate mitigation recommendations based on primary heat drivers."""
        drivers = []
        if row["building_density"] > 55: drivers.append("Cool Roofs")
        if row["ndvi"] < 0.15:           drivers.append("Tree Plantation")
        if row["albedo"] < 0.12:         drivers.append("Reflective Pavement")
        if row["tree_cover"] < 15:       drivers.append("Green Spaces")
        if not drivers:                  drivers.append("Green Corridors")
        return " + ".join(drivers[:2])

    def driver(row):
        """Identify primary heat driver based on environmental thresholds."""
        if row["building_density"] > 55: return "High Building Density"
        if row["ndvi"] < 0.15:           return "Low Vegetation (NDVI)"
        if row["albedo"] < 0.12:         return "Low Surface Albedo"
        return "Sparse Tree Cover"

    zone_names = [f"Zone {chr(65+i)}" for i in range(n)]
    zone_type_arr = [zone_types[i % len(zone_types)] for i in range(n)]

    df = pd.DataFrame({
        "zone":             zone_names,
        "zone_type":        zone_type_arr,
        "lat":              lats,
        "lon":              lons,
        "lst":              lst.round(1),
        "ndvi":             ndvi.round(3),
        "albedo":           alb.round(3),
        "building_density": bd.round(1),
        "road_density":     rd.round(3),
        "tree_cover":       tc.round(1),
        "humidity":         hum.round(1),
        "wind_speed":       ws.round(2),
        "aqi":              aqi,
    })

    df["risk_level"]   = df["lst"].apply(risk)
    df["main_driver"]  = df.apply(driver, axis=1)
    df["recommended_intervention"] = df.apply(mitigation, axis=1)
    est_cool = _clamp(RNG.normal(2.4, 0.7, n), 1.0, 4.5)
    df["estimated_cooling"] = est_cool.round(1)
    df["priority_score"]    = _clamp(
        (df["lst"] - 34) / 11 * 60 +
        (df["building_density"] / 85) * 25 +
        RNG.uniform(0, 15, n), 30, 100
    ).round(0).astype(int)
    months_map = {"Critical": 3, "High": 6, "Medium": 9, "Low": 12}
    df["implementation_time"] = df["risk_level"].map(months_map).apply(
        lambda x: f"{x} months"
    )
    df["data_source"] = "Prototype / Demo Data (Synthetic)"
    return df


def load_timeseries_data() -> pd.DataFrame:
    """Monthly avg LST timeseries for the city (12 months demo)."""
    months = pd.date_range("2024-01-01", periods=12, freq="MS")
    # Realistic seasonal pattern: hot summers (May-Jun), mild winters
    baseline = np.array([30.2, 32.1, 35.8, 38.4, 42.1, 43.5,
                         39.7, 37.2, 36.1, 34.8, 32.4, 29.8])
    lst_vals = _clamp(baseline + RNG.normal(0, 0.4, 12), 28, 46)
    return pd.DataFrame({
        "month":       months,
        "avg_lst":     lst_vals.round(2),
        "min_lst":     (lst_vals - RNG.uniform(2, 4, 12)).round(2),
        "max_lst":     (lst_vals + RNG.uniform(2, 5, 12)).round(2),
        "avg_ndvi":    _clamp(RNG.normal(0.20, 0.04, 12), 0.05, 0.40).round(3),
        "avg_albedo":  _clamp(RNG.normal(0.155, 0.015, 12), 0.08, 0.30).round(3),
    })


def load_mitigation_table(hotspot_df: pd.DataFrame) -> pd.DataFrame:
    """Build the styled mitigation recommendation table from hotspot data."""
    top = hotspot_df.sort_values("priority_score", ascending=False).head(15)
    return top[[
        "zone", "zone_type", "lst", "risk_level", "main_driver",
        "recommended_intervention", "estimated_cooling",
        "priority_score", "implementation_time",
    ]].rename(columns={
        "zone":                    "Zone",
        "zone_type":               "Type",
        "lst":                     "Current LST (°C)",
        "risk_level":              "Risk Level",
        "main_driver":             "Heat Driver",
        "recommended_intervention":"Recommended Intervention",
        "estimated_cooling":       "Est. Cooling (°C)",
        "priority_score":          "Priority Score",
        "implementation_time":     "Timeline",
    }).reset_index(drop=True)


def get_kpi_values() -> dict:
    """Return demo KPI values (fallback from config)."""
    return DEMO_KPI.copy()


def load_from_db():
    """
    Placeholder: connect to PostgreSQL + PostGIS when USE_DB=True.
    Falls back gracefully to demo data.
    """
    if not USE_DB:
        return None
    try:
        import psycopg2
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"[WARN] DB unavailable — using demo data. ({e})")
        return None
