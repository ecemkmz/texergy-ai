import os
import joblib
import pandas as pd
import logging

logger = logging.getLogger(__name__)

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "core", "anomaly_xgb_model.joblib")
FEATURES_PATH = os.path.join(os.path.dirname(__file__), "..", "core", "model_feature_columns.txt")

xgb_model = None
feature_columns = []

def load_model():
    global xgb_model, feature_columns
    if xgb_model is not None:
        return
    
    if os.path.exists(MODEL_PATH) and os.path.exists(FEATURES_PATH):
        xgb_model = joblib.load(MODEL_PATH)
        with open(FEATURES_PATH, "r") as f:
            feature_columns = [line.strip() for line in f.readlines() if line.strip()]
        logger.info("XGBoost model and feature columns loaded successfully.")
    else:
        logger.error(f"Model files not found at {MODEL_PATH} or {FEATURES_PATH}")

# Call it immediately to load at startup
load_model()

def predict_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    if xgb_model is None or not feature_columns:
        logger.warning("Model not loaded. Returning default 0 for anomaly_label.")
        df_out = df.copy()
        df_out["anomaly_label"] = 0
        return df_out

    # Copy to avoid modifying original argument
    df_out = df.copy()

    num_cols = ["machine_speed", "production_time", "output_quantity", "energy_consumption",
                "energy_per_unit", "ambient_temperature", "humidity", "defect_rate",
                "carbon_emission", "energy_cost", "production_efficiency", "quality_score",
                "efficiency_score"]
    
    encode_cols = []
    if "facility_type" in df.columns:
        encode_cols.append("facility_type")
    if "shift" in df.columns:
        encode_cols.append("shift")
        
    if encode_cols:
        X = pd.get_dummies(df_out[num_cols + encode_cols], columns=encode_cols)
    else:
        X = df_out[num_cols].copy()

    # Ensure all expected columns exist and are in the right order
    for col in feature_columns:
        if col not in X.columns:
            X[col] = 0
            
    X = X[feature_columns]
    
    preds = xgb_model.predict(X)
    df_out["anomaly_label"] = preds
    return df_out
