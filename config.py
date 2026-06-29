# =============================================================================
# config.py — Global configuration for Urban Heat Mitigation Dashboard
# Team Moon | ISRO Bharatiya Antariksh Hackathon 2026
# =============================================================================

# ── Project Metadata ──────────────────────────────────────────────────────────
PROJECT_TITLE       = "AI-Driven Urban Heat Mitigation Dashboard"
PROJECT_SUBTITLE    = "Satellite Remote Sensing + AI/ML Powered Urban Cooling Decision Support System"
TEAM_NAME           = "Team Moon"
HACKATHON_NAME      = "ISRO Bharatiya Antariksh Hackathon 2026"
PILOT_CITY          = "Chhatrapati Sambhajinagar"
VERSION             = "1.0.0-MVP"

# ── Map Settings ──────────────────────────────────────────────────────────────
# Approx. centroid of Chhatrapati Sambhajinagar (Aurangabad), Maharashtra
MAP_CENTER_LAT      = 19.8762
MAP_CENTER_LON      = 75.3433
MAP_ZOOM_START      = 12

# ── Theme & Style ─────────────────────────────────────────────────────────────
PRIMARY_COLOR       = "#E84A5F"     # heat / accent red
SECONDARY_COLOR     = "#2A9D8F"     # cool / green-teal
TERTIARY_COLOR      = "#F4A261"     # warning orange
BACKGROUND_COLOR    = "#0E1117"     # streamlit dark bg
CARD_COLOR          = "#1C2232"     # card surface
TEXT_PRIMARY        = "#FFFFFF"
TEXT_SECONDARY      = "#A0AEC0"

# ── Data Sources ──────────────────────────────────────────────────────────────
DATA_SOURCES = [
    "Landsat 8 (USGS/NASA)",
    "Sentinel-2 (ESA Copernicus)",
    "ECOSTRESS (NASA/JPL)",
    "ERA5 Reanalysis (ECMWF)",
    "CPCB Air Quality Data",
    "OpenStreetMap",
]

# ── ML Models available ────────────────────────────────────────────────────────
ML_MODELS = [
    "Random Forest Regressor",
    "Gradient Boosting Regressor",
    "Ridge Regression (Baseline)",
]

# ── Mitigation Strategies ─────────────────────────────────────────────────────
MITIGATION_STRATEGIES = [
    "All Strategies",
    "Cool Roofs",
    "Tree Plantation",
    "Green Spaces",
    "Reflective Pavement",
    "Green Corridors",
]

# ── DB Connection (PostgreSQL + PostGIS) ──────────────────────────────────────
# Set USE_DB = False to run in full demo/prototype mode (no DB required)
USE_DB = False
DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "database": "urban_heat_db",
    "user":     "postgres",
    "password": "your_password_here",
}

# ── Random Forest Hyperparameters ─────────────────────────────────────────────
RF_PARAMS = {
    "n_estimators":  200,
    "max_depth":     12,
    "min_samples_split": 5,
    "min_samples_leaf":  2,
    "random_state":  42,
    "n_jobs":        -1,
}

# ── Demo KPI Values ───────────────────────────────────────────────────────────
DEMO_KPI = {
    "avg_lst":          38.6,   # °C
    "mean_albedo":      0.153,
    "tree_cover":       21.4,   # %
    "building_density": 46.7,   # %
    "hotspot_count":    23,
    "humidity":         42.0,   # %
    "wind_speed":       3.2,    # m/s
    "risk_index":       7.4,    # /10
    "aqi":              118,    # AQI value
}
