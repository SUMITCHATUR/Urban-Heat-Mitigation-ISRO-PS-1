# docs/methodology.md — Technical Methodology
# AI-Driven Urban Heat Mitigation Dashboard
# Team Moon | ISRO Bharatiya Antariksh Hackathon 2026

## Methodology

### 1. Urban Heat Island Detection

Urban Heat Islands (UHIs) are identified using Land Surface Temperature (LST)
derived from Landsat 8 Band 10 (Thermal Infrared Sensor). The retrieval follows
NASA USGS Collection 2 Level-2 processing standards:

```
LST (°C) = (DN × 0.00341802 + 149.0) − 273.15
```

Hotspots are defined as zones where LST exceeds the city-wide mean by ≥ 2°C,
validated against ERA5 air temperature to exclude cloud/data artefacts.

### 2. Feature Engineering

Eight biophysical and meteorological predictors are computed per zone per date:

| Feature | Range (Pilot City) | Source |
|---|---|---|
| Surface Albedo | 0.05 – 0.35 | Landsat B2–B7 |
| NDVI | 0.02 – 0.48 | Sentinel-2 B8/B4 |
| Building Density | 10 – 90% | OpenStreetMap |
| Road Density | 0.05 – 0.70 | OpenStreetMap |
| Tree Cover | 3 – 55% | S2 LULC / NLCD |
| Humidity | 25 – 75% | ERA5 |
| Wind Speed | 0.5 – 7.0 m/s | ERA5 |
| AQI | 40 – 250 | CPCB |

### 3. Random Forest Model

A Random Forest Regressor (200 trees, max_depth=12) is trained using
an 80/20 train-test split on augmented zone data. Feature importances
are extracted to identify dominant heat drivers.

**Validation metrics (demo data):**
- RMSE: 1.6 – 2.2 °C
- MAE:  1.1 – 1.7 °C
- R²:   0.82 – 0.90

### 4. Mitigation Simulation

For each strategy, biophysical features are modified by empirically-derived deltas:

| Strategy | Feature Delta |
|---|---|
| Cool Roofs | Albedo + 0.10 |
| Tree Plantation | Tree Cover + 10%, NDVI + 0.08 |
| Green Spaces | Tree Cover + 10%, NDVI + 0.08 |
| Reflective Pavement | Albedo + 0.05, Road Density − 0.05 |
| Green Corridors | NDVI + 0.04, Wind Speed + 0.3 m/s |

Modified features are passed to the trained model to predict post-mitigation LST.
The difference (ΔT = LST_before − LST_after) is the estimated cooling benefit.

### 5. Recommendation Ranking

Each zone × strategy pair is scored by:

```
Composite Score = 
    (Cooling Potential / 5) × 50 +
    (Feasibility Score / 100) × 30 +
    (Priority Score / 100) × 20
```

Top-ranked recommendations are presented to city planners in the dashboard.

### 6. Impact Estimation

| Metric | Estimation Method |
|---|---|
| People Benefited | Zones with ΔT > 1°C × 45,000 persons/zone |
| Energy Saving | ΔT × 12,000 MWh (HVAC cooling demand factor) |
| CO₂ Reduction | Energy Saving × 0.82 tCO₂/MWh (India grid factor) |

> ⚠ All impact estimates use prototype/demo multipliers. Production deployment
> would use ward-level census population and DISCOM energy data.
