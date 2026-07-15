import os
import pandas as pd
import xgboost as xgb
import joblib

def main():
    print("Loading dataset...")
    csv_path = "../texergy_ai_synthetic_dataset_v5.csv"
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return

    df = pd.read_csv(csv_path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    num_cols = ["machine_speed", "production_time", "output_quantity", "energy_consumption",
                "energy_per_unit", "ambient_temperature", "humidity", "defect_rate",
                "carbon_emission", "energy_cost", "production_efficiency", "quality_score",
                "efficiency_score"]
    feature_cols = num_cols + ["facility_type", "shift"]

    # One-hot encoding
    X_all = pd.get_dummies(df[feature_cols], columns=["facility_type", "shift"])
    y_all = df["anomaly_label"]

    # Zaman bazlı split (Train %75)
    sorted_idx = df.sort_values("timestamp").index
    X_sorted, y_sorted = X_all.loc[sorted_idx], y_all.loc[sorted_idx]
    cut = int(len(X_sorted) * 0.75)
    X_train, y_train = X_sorted.iloc[:cut], y_sorted.iloc[:cut]

    print("Training XGBoost model...")
    # Best config from notebook (scale_pos_weight=3 for recall improvement)
    xgb_model = xgb.XGBClassifier(
        n_estimators=100, max_depth=3, learning_rate=0.05, min_child_weight=5,
        subsample=0.8, colsample_bytree=0.8, scale_pos_weight=3,
        eval_metric="logloss", random_state=42,
    )
    xgb_model.fit(X_train, y_train)

    os.makedirs("app/core", exist_ok=True)
    model_path = "app/core/anomaly_xgb_model.joblib"
    features_path = "app/core/model_feature_columns.txt"
    
    joblib.dump(xgb_model, model_path)
    with open(features_path, "w") as f:
        f.write("\n".join(X_all.columns.tolist()))

    print(f"Model exported successfully to {model_path}")

if __name__ == "__main__":
    main()
