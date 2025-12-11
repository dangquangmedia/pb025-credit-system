# backend/train_pb025_pipeline_mlflow.py
import os
import mlflow
import mlflow.lightgbm
import pandas as pd

# 💡 import lại đúng pipeline thật
from core_pipeline import (
    preprocess_for_lgb,
    train_models,
    metrics_report,
    calculate_psi,
)

# Đường dẫn data thật của PB-025
DATA_PATH = os.path.join("data", "loan_2014_18.csv")

def main():
    # 1) Chọn / tạo experiment cho PB-025
    mlflow.set_experiment("pb025_credit_lgb")

    # 2) Load data thật
    df = pd.read_csv(DATA_PATH)

    # 3) TOÀN BỘ CODE TRAIN THẬT
    with mlflow.start_run(run_name="lgb_pb025_v1"):

        X_train, X_valid, y_train, y_valid, meta = preprocess_for_lgb(df)

        # train_models nên trả ra model LightGBM + params/hyperparams
        lgb_model, train_info = train_models(
            X_train=X_train,
            y_train=y_train,
            X_valid=X_valid,
            y_valid=y_valid,
        )

        # Dự đoán để tính metrics
        y_pred_valid = lgb_model.predict_proba(X_valid)[:, 1]

        # metrics_report trả về dict các metric (AUC, KS, F1,…)
        metrics = metrics_report(y_valid, y_pred_valid)

        # PSI giữa train & valid 
        psi_df = calculate_psi(
            ref_scores=train_info["train_scores"],  
            cur_scores=train_info["valid_scores"],
        )
        psi_value = float(psi_df["PSI"].mean())

        # 4) Log hyperparameters 
        mlflow.log_params({
            "model_type": "lightgbm",
            "n_estimators": lgb_model.n_estimators,
            "learning_rate": lgb_model.learning_rate,
            "num_leaves": lgb_model.num_leaves,
            # thêm các hyperparam quan trọng khác...
        })

        # 5) Log metrics chính
        mlflow.log_metrics({
            "valid_auc":  float(metrics["auc"]),
            "valid_ks":   float(metrics["ks"]),
            "valid_f1":   float(metrics["f1"]),
            "psi_mean":   psi_value,
        })

        # 6) Log PSI và các bảng khác thành artifact
        os.makedirs("mlflow_artifacts", exist_ok=True)
        psi_path = os.path.join("mlflow_artifacts", "psi_valid.csv")
        psi_df.to_csv(psi_path, index=False)
        mlflow.log_artifact(psi_path, artifact_path="diagnostics")

        # Nếu có SHAP, feature importance, confusion matrix,… => lưu file & log_artifact tương tự

        # 7) Log luôn model LightGBM vào MLflow
        #    (signature & input_example em có thể thêm sau)
        mlflow.lightgbm.log_model(
            lgb_model,
            artifact_path="model",
        )

        print("➡️ Finished training & logging LightGBM model to MLflow")


if __name__ == "__main__":
    main()
