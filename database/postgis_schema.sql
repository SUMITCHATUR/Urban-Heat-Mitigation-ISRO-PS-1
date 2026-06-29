-- =============================================================================
-- database/postgis_schema.sql
-- PostGIS Schema for Urban Heat Mitigation Database
-- Team Moon | ISRO Bharatiya Antariksh Hackathon 2026
-- =============================================================================

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_raster;

-- =============================================================================
-- SCHEMA
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS urban_heat;

-- =============================================================================
-- TABLE: urban_heat.zones
-- Spatial administrative / analysis zones
-- =============================================================================
CREATE TABLE IF NOT EXISTS urban_heat.zones (
    zone_id          SERIAL PRIMARY KEY,
    zone_name        VARCHAR(50)  NOT NULL,
    zone_type        VARCHAR(100),
    city             VARCHAR(100) DEFAULT 'Chhatrapati Sambhajinagar',
    ward_no          INTEGER,
    area_sqkm        NUMERIC(8,4),
    population_est   INTEGER,
    geom             GEOMETRY(Polygon, 4326),   -- WGS84
    created_at       TIMESTAMP DEFAULT NOW(),
    updated_at       TIMESTAMP DEFAULT NOW()
);

-- Spatial index
CREATE INDEX IF NOT EXISTS idx_zones_geom ON urban_heat.zones USING GIST(geom);

-- =============================================================================
-- TABLE: urban_heat.lst_observations
-- Land Surface Temperature observations per zone per date
-- =============================================================================
CREATE TABLE IF NOT EXISTS urban_heat.lst_observations (
    obs_id           SERIAL PRIMARY KEY,
    zone_id          INTEGER REFERENCES urban_heat.zones(zone_id),
    obs_date         DATE NOT NULL,
    lst_celsius      NUMERIC(5,2),
    lst_kelvin       NUMERIC(7,2),
    satellite_source VARCHAR(50),    -- Landsat8, Sentinel2, ECOSTRESS
    cloud_cover_pct  NUMERIC(5,2),
    qa_flag          SMALLINT DEFAULT 0,
    geom             GEOMETRY(Point, 4326),
    created_at       TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_lst_zone      ON urban_heat.lst_observations(zone_id);
CREATE INDEX IF NOT EXISTS idx_lst_date      ON urban_heat.lst_observations(obs_date);
CREATE INDEX IF NOT EXISTS idx_lst_geom      ON urban_heat.lst_observations USING GIST(geom);

-- =============================================================================
-- TABLE: urban_heat.environmental_features
-- Per-zone environmental feature vector for ML model
-- =============================================================================
CREATE TABLE IF NOT EXISTS urban_heat.environmental_features (
    feat_id            SERIAL PRIMARY KEY,
    zone_id            INTEGER REFERENCES urban_heat.zones(zone_id),
    obs_date           DATE NOT NULL,
    ndvi               NUMERIC(6,4),
    evi                NUMERIC(6,4),
    savi               NUMERIC(6,4),
    surface_albedo     NUMERIC(6,4),
    building_density   NUMERIC(5,2),
    road_density       NUMERIC(6,4),
    tree_cover_pct     NUMERIC(5,2),
    impervious_surface NUMERIC(5,2),
    humidity_pct       NUMERIC(5,2),
    wind_speed_ms      NUMERIC(5,2),
    wind_direction_deg NUMERIC(5,1),
    aqi                INTEGER,
    data_source        VARCHAR(100),
    created_at         TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_feat_zone ON urban_heat.environmental_features(zone_id);
CREATE INDEX IF NOT EXISTS idx_feat_date ON urban_heat.environmental_features(obs_date);

-- =============================================================================
-- TABLE: urban_heat.mitigation_recommendations
-- AI-generated mitigation strategy per zone
-- =============================================================================
CREATE TABLE IF NOT EXISTS urban_heat.mitigation_recommendations (
    rec_id             SERIAL PRIMARY KEY,
    zone_id            INTEGER REFERENCES urban_heat.zones(zone_id),
    generated_date     DATE DEFAULT CURRENT_DATE,
    model_version      VARCHAR(30),
    predicted_lst      NUMERIC(5,2),
    current_lst        NUMERIC(5,2),
    lst_reduction      NUMERIC(5,2),
    risk_level         VARCHAR(20),
    main_driver        VARCHAR(100),
    strategy           VARCHAR(100),
    estimated_cooling  NUMERIC(4,2),
    priority_score     INTEGER,
    feasibility_score  INTEGER,
    implementation_mo  INTEGER,
    notes              TEXT,
    created_at         TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rec_zone ON urban_heat.mitigation_recommendations(zone_id);
CREATE INDEX IF NOT EXISTS idx_rec_date ON urban_heat.mitigation_recommendations(generated_date);

-- =============================================================================
-- TABLE: urban_heat.model_runs
-- Log of ML model training runs
-- =============================================================================
CREATE TABLE IF NOT EXISTS urban_heat.model_runs (
    run_id           SERIAL PRIMARY KEY,
    run_timestamp    TIMESTAMP DEFAULT NOW(),
    model_type       VARCHAR(50),
    n_features       INTEGER,
    n_train_samples  INTEGER,
    n_test_samples   INTEGER,
    rmse             NUMERIC(6,4),
    mae              NUMERIC(6,4),
    r2_score         NUMERIC(6,4),
    hyperparameters  JSONB,
    notes            TEXT
);

-- =============================================================================
-- VIEW: urban_heat.v_hotspot_summary
-- =============================================================================
CREATE OR REPLACE VIEW urban_heat.v_hotspot_summary AS
SELECT
    z.zone_name,
    z.zone_type,
    z.city,
    lo.obs_date,
    lo.lst_celsius,
    ef.ndvi,
    ef.surface_albedo,
    ef.building_density,
    ef.tree_cover_pct,
    ef.humidity_pct,
    ef.wind_speed_ms,
    ef.aqi,
    mr.risk_level,
    mr.strategy,
    mr.estimated_cooling,
    mr.priority_score,
    ST_AsGeoJSON(z.geom)::json AS geometry
FROM urban_heat.zones z
LEFT JOIN urban_heat.lst_observations       lo ON lo.zone_id = z.zone_id
LEFT JOIN urban_heat.environmental_features ef ON ef.zone_id = z.zone_id AND ef.obs_date = lo.obs_date
LEFT JOIN urban_heat.mitigation_recommendations mr ON mr.zone_id = z.zone_id AND mr.generated_date = lo.obs_date
WHERE lo.qa_flag = 0;

-- =============================================================================
-- DEMO DATA INSERT (Prototype — remove in production)
-- =============================================================================
INSERT INTO urban_heat.zones (zone_name, zone_type, ward_no, area_sqkm)
VALUES
  ('Zone A', 'High Density Residential', 1, 2.14),
  ('Zone B', 'Commercial District',      2, 1.87),
  ('Zone C', 'Open/Peri-Urban',          3, 3.40),
  ('Zone D', 'Industrial Zone',          4, 2.90),
  ('Zone E', 'Mixed Use',                5, 1.62)
ON CONFLICT DO NOTHING;
