# =============================================================================
# utils/model_utils.py — Random Forest training, prediction, evaluation
# Team Moon | ISRO Bharatiya Antariksh Hackathon 2026
# =============================================================================
import numpy as np
import pandas as pd
import os, sys, pickle

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from config import RF_PARAMS

FEATURE_COLS = [
    "albedo", "ndvi", "building_density", "road_density",
    "tree_cover", "humidity", "wind_speed", "aqi",
]
TARGET_COL = "lst"

FEATURE_LABELS = {
    "albedo":            "Surface Albedo",
    "ndvi":              "NDVI (Vegetation Index)",
    "building_density":  "Building Density",
    "road_density":      "Road Density",
    "tree_cover":        "Tree Cover (%)",
    "humidity":          "Humidity (%)",
    "wind_speed":        "Wind Speed (m/s)",
    "aqi":               "Air Quality Index",
}


# ─────────────────────────────────────────────────────────────────────────────

def _augment_data(df: pd.DataFrame, n_augment: int = 400) -> pd.DataFrame:
    """
    Augment sparse demo data with Gaussian noise to give the model
    a realistic training set.  Labelled as synthetic.
    """
    rng = np.random.default_rng(42)
    rows = []
    for _ in range(n_augment):
        base = df.sample(1, random_state=rng.integers(999)).iloc[0]
        noise = {
            "albedo":            np.clip(base.albedo           + rng.normal(0, 0.015), 0.05, 0.35),
            "ndvi":              np.clip(base.ndvi             + rng.normal(0, 0.03),  0.01, 0.50),
            "building_density":  np.clip(base.building_density + rng.normal(0, 5),    5,    90),
            "road_density":      np.clip(base.road_density     + rng.normal(0, 0.05), 0.05, 0.80),
            "tree_cover":        np.clip(base.tree_cover       + rng.normal(0, 3),    1,    55),
            "humidity":          np.clip(base.humidity         + rng.normal(0, 3),    20,   80),
            "wind_speed":        np.clip(base.wind_speed       + rng.normal(0, 0.4),  0.3,  8),
            "aqi":               np.clip(base.aqi              + rng.normal(0, 10),   40,   250),
        }
        # Physics-inspired LST from features
        lst = (
            base.lst
            - 4.5 * (noise["albedo"] - base.albedo)
            - 3.0 * (noise["ndvi"]   - base.ndvi)
            + 0.12 * (noise["building_density"] - base.building_density)
            - 0.06 * (noise["tree_cover"]       - base.tree_cover)
            - 0.04 * (noise["humidity"]         - base.humidity)
            - 0.25 * (noise["wind_speed"]       - base.wind_speed)
            + rng.normal(0, 0.3)
        )
        rows.append({**noise, TARGET_COL: float(np.clip(lst, 30, 48))})
    return pd.concat([df, pd.DataFrame(rows)], ignore_index=True)


def train_model(hotspot_df: pd.DataFrame, model_name: str = "Random Forest Regressor"):
    """
    Train selected model on hotspot data.
    Returns (model, scaler, metrics_dict, X_test, y_test, y_pred).
    """
    df_aug = _augment_data(hotspot_df)
    X = df_aug[FEATURE_COLS].values
    y = df_aug[TARGET_COL].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42
    )

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s  = scaler.transform(X_test)

    if model_name == "Gradient Boosting Regressor":
        model = GradientBoostingRegressor(
            n_estimators=200, max_depth=5,
            learning_rate=0.08, random_state=42
        )
    elif model_name == "Ridge Regression (Baseline)":
        model = Ridge(alpha=1.0)
    else:  # default: Random Forest
        model = RandomForestRegressor(**RF_PARAMS)

    model.fit(X_train_s, y_train)
    y_pred = model.predict(X_test_s)

    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    mae  = float(mean_absolute_error(y_test, y_pred))
    r2   = float(r2_score(y_test, y_pred))

    metrics = {
        "rmse":             round(rmse, 3),
        "mae":              round(mae, 3),
        "r2":               round(r2, 3),
        "confidence_score": round(min(r2 * 100, 97.5), 1),
        "n_train":          len(X_train),
        "n_test":           len(X_test),
    }
    return model, scaler, metrics, X_test_s, y_test, y_pred


def predict_after_mitigation(
    model,
    scaler,
    hotspot_df: pd.DataFrame,
    strategy: str = "All Strategies",
) -> pd.DataFrame:
    """
    Simulate feature changes under a mitigation strategy and predict new LST.
    Returns hotspot_df with added 'predicted_lst' and 'lst_reduction' columns.
    """
    df = hotspot_df.copy()
    X_orig = scaler.transform(df[FEATURE_COLS].values)
    df["predicted_lst_no_mitigation"] = model.predict(X_orig).round(2)

    # Apply mitigation feature deltas
    if strategy in ("All Strategies", "Cool Roofs"):
        df["albedo"] = np.clip(df["albedo"] + 0.10, 0.05, 0.50)
    if strategy in ("All Strategies", "Tree Plantation", "Green Spaces"):
        df["tree_cover"] = np.clip(df["tree_cover"] + 10, 0, 60)
        df["ndvi"]       = np.clip(df["ndvi"]       + 0.08, 0, 0.70)
    if strategy in ("All Strategies", "Reflective Pavement"):
        df["road_density"] = np.clip(df["road_density"] - 0.05, 0, 1)
        df["albedo"]       = np.clip(df["albedo"]       + 0.05, 0.05, 0.50)
    if strategy in ("All Strategies", "Green Corridors"):
        df["ndvi"]       = np.clip(df["ndvi"] + 0.04, 0, 0.70)
        df["wind_speed"] = np.clip(df["wind_speed"] + 0.3, 0, 10)

    X_mit = scaler.transform(df[FEATURE_COLS].values)
    df["predicted_lst"] = model.predict(X_mit).round(2)
    df["lst_reduction"] = (df["lst"] - df["predicted_lst"]).round(2)
    return df


def get_feature_importances(model, model_name: str) -> pd.DataFrame:
    """Extract feature importance from tree-based models; coefficients for Ridge."""
    try:
        importances = model.feature_importances_
    except AttributeError:
        importances = np.abs(model.coef_)
        importances /= importances.sum()

    df = pd.DataFrame({
        "Feature":    [FEATURE_LABELS[f] for f in FEATURE_COLS],
        "Importance": importances,
        "Feature_Key": FEATURE_COLS,
    }).sort_values("Importance", ascending=False).reset_index(drop=True)
    return df


def save_model(model, scaler, path: str = "models/random_forest_model.pkl"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump({"model": model, "scaler": scaler}, f)


def load_saved_model(path: str = "models/random_forest_model.pkl"):
    if not os.path.exists(path):
        return None, None
    with open(path, "rb") as f:
        obj = pickle.load(f)
    return obj["model"], obj["scaler"]
