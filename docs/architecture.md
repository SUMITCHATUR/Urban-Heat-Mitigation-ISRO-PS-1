# docs/architecture.md — System Architecture
# AI-Driven Urban Heat Mitigation Dashboard
# Team Moon | ISRO Bharatiya Antariksh Hackathon 2026

## System Architecture

### Data Ingestion Layer

**Sources:**
- Landsat 8 Collection 2 Level-2 (USGS/NASA) — Band 10 LST, Band 4/5 for NDVI
- Sentinel-2 MSI Level-2A (ESA Copernicus) — 10m NDVI, LULC
- ECOSTRESS ECO2LSTE (NASA JPL) — 70m LST at overpass time
- ERA5 Reanalysis (ECMWF) — 0.25° humidity, wind speed, temperature
- CPCB AQI Open API — Station-level air quality
- OpenStreetMap Overpass API — Building footprints, road network

**Processing via Google Earth Engine:**
```javascript
// Example GEE script concept
var lst = landsat8.select('ST_B10')
  .multiply(0.00341802).add(149.0)   // Scale + offset
  .subtract(273.15);                  // K → °C
```

### Feature Engineering

| Feature | Derivation |
|---|---|
| LST (°C) | Landsat B10 thermal infrared → radiance → temperature |
| NDVI | (NIR - Red) / (NIR + Red) from Sentinel-2 B8/B4 |
| Surface Albedo | Shortwave from Landsat B2–B7 weighted sum |
| Building Density | OSM footprints / zone area |
| Road Density | OSM road length / zone area |
| Tree Cover | NLCD / S2 LULC classification |
| Humidity | ERA5 near-surface relative humidity |
| Wind Speed | ERA5 10m wind speed |
| AQI | CPCB station interpolation |

### AI/ML Architecture

```
Input Features (8 variables)
     ↓
StandardScaler (zero-mean, unit-variance)
     ↓
Random Forest Regressor
  n_estimators = 200
  max_depth    = 12
  ─────────────────────────
  200 decision trees → ensemble mean prediction
     ↓
Output: Predicted LST (°C)
```

**Mitigation Simulation:**
Apply feature deltas (e.g., +10% albedo for Cool Roofs) → re-predict LST → compute ΔT.

### Database Architecture

```
PostgreSQL 15 + PostGIS 3.4
├── urban_heat.zones                    (spatial polygons)
├── urban_heat.lst_observations         (time-series LST)
├── urban_heat.environmental_features   (ML feature store)
├── urban_heat.mitigation_recommendations (AI outputs)
└── urban_heat.model_runs               (training logs)
```

### Dashboard Architecture

```
app.py (Streamlit)
├── config.py               — constants & settings
├── utils/data_loader.py    — data ingestion & demo fallback
├── utils/map_utils.py      — Folium map construction
├── utils/model_utils.py    — train / predict / evaluate
└── utils/recommendation_engine.py — strategy scoring
```
