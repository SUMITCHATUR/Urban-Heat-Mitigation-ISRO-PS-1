# =============================================================================
# database/db_connection.py — PostgreSQL + PostGIS connection helper
# Team Moon | ISRO Bharatiya Antariksh Hackathon 2026
# =============================================================================
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from config import DB_CONFIG, USE_DB


def get_connection():
    """
    Returns a psycopg2 connection if USE_DB=True and psycopg2 is available.
    Falls back to None (demo mode) gracefully.
    """
    if not USE_DB:
        return None

    try:
        import psycopg2
        conn = psycopg2.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            dbname=DB_CONFIG["database"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
        )
        print("[INFO] PostgreSQL + PostGIS connection established.")
        return conn
    except ImportError:
        print("[WARN] psycopg2 not installed — running in demo mode.")
        return None
    except Exception as e:
        print(f"[WARN] DB connection failed ({e}) — running in demo mode.")
        return None


def query_hotspots(conn, obs_date: str = None) -> list:
    """
    Fetch hotspot data from PostGIS view.
    Returns list of dicts; falls back to empty list if conn is None.
    """
    if conn is None:
        return []
    try:
        import psycopg2.extras
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        sql = "SELECT * FROM urban_heat.v_hotspot_summary"
        params = []
        if obs_date:
            sql += " WHERE obs_date = %s"
            params.append(obs_date)
        sql += " ORDER BY lst_celsius DESC LIMIT 100;"
        cursor.execute(sql, params)
        return list(cursor.fetchall())
    except Exception as e:
        print(f"[ERROR] query_hotspots: {e}")
        return []


def insert_model_run(conn, metrics: dict):
    """Log a model training run to the database."""
    if conn is None:
        return
    try:
        import json
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO urban_heat.model_runs
                (model_type, n_features, n_train_samples, n_test_samples,
                 rmse, mae, r2_score, hyperparameters)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            metrics.get("model", "RandomForest"),
            len(metrics.get("features", [])),
            metrics.get("n_train", 0),
            metrics.get("n_test", 0),
            metrics.get("rmse", 0),
            metrics.get("mae", 0),
            metrics.get("r2", 0),
            json.dumps(metrics.get("hyperparameters", {})),
        ))
        conn.commit()
        print("[INFO] Model run logged to DB.")
    except Exception as e:
        print(f"[ERROR] insert_model_run: {e}")
        conn.rollback()
