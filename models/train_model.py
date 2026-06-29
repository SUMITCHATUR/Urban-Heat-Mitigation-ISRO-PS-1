# =============================================================================
# models/train_model.py — Standalone training script (run from CLI)
# Team Moon | ISRO Bharatiya Antariksh Hackathon 2026
#
# Usage:
#   python models/train_model.py
#   python models/train_model.py --model gbr --output models/gbr_model.pkl
# =============================================================================

import argparse
import os
import sys
import json

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from utils.data_loader  import load_hotspot_data
from utils.model_utils  import train_model, save_model, get_feature_importances


def main():
    parser = argparse.ArgumentParser(
        description="Train LST prediction model — Urban Heat Mitigation | Team Moon"
    )
    parser.add_argument(
        "--model",
        choices=["rf", "gbr", "ridge"],
        default="rf",
        help="Model to train: rf=RandomForest, gbr=GradientBoosting, ridge=Ridge",
    )
    parser.add_argument(
        "--output",
        default="models/random_forest_model.pkl",
        help="Path to save the trained model pickle.",
    )
    args = parser.parse_args()

    model_map = {
        "rf":    "Random Forest Regressor",
        "gbr":   "Gradient Boosting Regressor",
        "ridge": "Ridge Regression (Baseline)",
    }
    model_name = model_map[args.model]

    print(f"[INFO] Loading demo hotspot data...")
    hotspot_df = load_hotspot_data()
    print(f"[INFO] Dataset: {len(hotspot_df)} zones")

    print(f"[INFO] Training: {model_name}")
    model, scaler, metrics, X_test, y_test, y_pred = train_model(hotspot_df, model_name)

    print("\n── Model Performance ────────────────────────")
    print(f"  RMSE           : {metrics['rmse']:.4f} °C")
    print(f"  MAE            : {metrics['mae']:.4f} °C")
    print(f"  R² Score       : {metrics['r2']:.4f}")
    print(f"  Confidence     : {metrics['confidence_score']} %")
    print(f"  Train samples  : {metrics['n_train']}")
    print(f"  Test samples   : {metrics['n_test']}")

    feat_imp = get_feature_importances(model, model_name)
    print("\n── Feature Importance ───────────────────────")
    for _, row in feat_imp.iterrows():
        bar = "█" * int(row["Importance"] * 40)
        print(f"  {row['Feature']:<30} {row['Importance']:.4f}  {bar}")

    save_model(model, scaler, args.output)
    print(f"\n[INFO] Model saved to: {args.output}")

    # Save metrics JSON
    metrics_path = args.output.replace(".pkl", "_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump({**metrics, "model": model_name}, f, indent=2)
    print(f"[INFO] Metrics saved to: {metrics_path}")
    print("\n[DONE] Training complete. ✓")


if __name__ == "__main__":
    main()
