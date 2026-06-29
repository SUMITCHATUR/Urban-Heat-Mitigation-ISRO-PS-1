# =============================================================================
# utils/recommendation_engine.py — Rule-based + ML mitigation scorer
# Team Moon | ISRO Bharatiya Antariksh Hackathon 2026
# =============================================================================
import pandas as pd
import numpy as np


def _cooling_potential(row: pd.Series, strategy: str) -> float:
    """Estimate additional cooling achievable by a given strategy."""
    cool = 0.0
    if strategy == "Cool Roofs":
        cool += (1 - row["albedo"]) * 4.5
    elif strategy == "Tree Plantation":
        cool += max(0, (40 - row["tree_cover"]) / 40) * 3.5
    elif strategy == "Green Spaces":
        cool += max(0, (0.5 - row["ndvi"]) / 0.5) * 2.8
    elif strategy == "Reflective Pavement":
        cool += row["road_density"] * 2.2
    elif strategy == "Green Corridors":
        cool += (1 - row["ndvi"]) * 1.8
    return round(np.clip(cool, 0.5, 5.0), 2)


def generate_strategy_report(
    hotspot_df: pd.DataFrame,
    selected_strategy: str = "All Strategies",
) -> pd.DataFrame:
    """
    For each hotspot zone, compute per-strategy cooling potential and
    return a ranked recommendation dataframe.
    """
    strategies = [
        "Cool Roofs", "Tree Plantation", "Green Spaces",
        "Reflective Pavement", "Green Corridors",
    ]
    if selected_strategy != "All Strategies":
        strategies = [selected_strategy]

    records = []
    for _, row in hotspot_df.iterrows():
        for strat in strategies:
            cp = _cooling_potential(row, strat)
            feasibility = _feasibility(row, strat)
            records.append({
                "Zone":             row["zone"],
                "Zone Type":        row["zone_type"],
                "Strategy":         strat,
                "Current LST (°C)": row["lst"],
                "Risk Level":       row["risk_level"],
                "Cooling Potential (°C)": cp,
                "Feasibility Score":      feasibility,
                "Priority Score":         row["priority_score"],
                "Implementation Time":    row["implementation_time"],
            })

    df = pd.DataFrame(records)
    df["Composite Score"] = (
        df["Cooling Potential (°C)"] / 5 * 50 +
        df["Feasibility Score"]      / 100 * 30 +
        df["Priority Score"]         / 100 * 20
    ).round(1)
    return df.sort_values("Composite Score", ascending=False).reset_index(drop=True)


def _feasibility(row: pd.Series, strategy: str) -> int:
    """Simple heuristic feasibility score 0–100."""
    score = 50
    if strategy == "Cool Roofs":
        score += int(row["building_density"] * 0.4)
    elif strategy == "Tree Plantation":
        score += int((100 - row["building_density"]) * 0.3)
    elif strategy == "Green Spaces":
        score += int((1 - row["ndvi"]) * 40)
    elif strategy == "Reflective Pavement":
        score += int(row["road_density"] * 60)
    elif strategy == "Green Corridors":
        score += int((100 - row["tree_cover"]) * 0.2)
    return int(np.clip(score, 20, 98))


def compute_impact_summary(predicted_df: pd.DataFrame) -> dict:
    """
    Compute before/after summary statistics.
    predicted_df must have 'lst' and 'predicted_lst' columns.
    """
    avg_before   = predicted_df["lst"].mean()
    avg_after    = predicted_df["predicted_lst"].mean()
    total_cool   = avg_before - avg_after
    reduced      = int((predicted_df["lst_reduction"] > 1.0).sum())
    people_ben   = reduced * 45_000          # demo estimate per zone
    energy_saved = total_cool * 12_000       # MWh demo estimate

    return {
        "avg_lst_before":      round(avg_before, 2),
        "avg_lst_after":       round(avg_after,  2),
        "total_cooling":       round(total_cool,  2),
        "hotspots_reduced":    reduced,
        "people_benefited":    people_ben,
        "energy_saving_MWh":   round(energy_saved, 0),
        "co2_reduction_tons":  round(energy_saved * 0.82, 0),   # demo factor
    }
