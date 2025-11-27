"""
PB-025: Chạy full pipeline (LightGBM, PSI, mapping CIC, v.v.) và log vào MLflow.

Giả định bạn đã có các hàm sau trong core_pipeline.py:
- preprocess_for_lgb
- train_models
- metrics_report
- calculate_psi
- prob_to_cic
- map_score_to_rank
- give_advice

Nếu tên / tham số khác, hãy chỉnh phần gọi hàm cho khớp với code thật.
"""

import time
from pathlib import Path

import mlflow
import mlflow.lightgbm
import numpy as np
import pandas as pd

from core_pipeline import (
    preprocess_for_lgb,
    train_models,
    metrics_report,
    calculate_psi,
    prob_to_cic,
    map_score_to_rank,
    give_advice,
)

# ===== CONFIG =====
DATA_PATH = Path("data") / "loan_2014_18.csv"
EXPERIMENT_NAME = "pb025_pipeline_full"
MODEL_NAME = "pb025_lgbm_main"
# ==================


def run_full_pipeline(df: pd.DataFrame):
    """Chạy toàn bộ pipeline và trả kết quả để log MLflow."""

    # 1) Tiền xử lý + tách train/valid
    X_train, X_valid, y_train, y_valid, feature_names = preprocess_for_lgb(df)

    # 2) Train nhiều model (LR, RF, LGBM, …)
    models = train_models(
        X_train=X_train,
        y_train=y_train,
        X_valid=X_valid,
        y_valid=y_valid,
        feature_names=feature_names,
    )

    # Lấy model LightGBM chính
    lgbm = models["lgbm"]

    # 3) Metrics trên tập valid
    metrics = metrics_report(
        models_dict=models,
        X_valid=X_valid,
        y_valid=y_valid,
    )

    # 4) PSI giữa train và valid
    train_score = lgbm.predict_proba(X_train)[:, 1]
    valid_score = lgbm.predict_proba(X_valid)[:, 1]

    psi_table, psi_value = calculate_psi(
        train_score=train_score,
        test_score=valid_score,
        n_bins=10,
    )

    # 5) Mapping PD -> CIC rank + reason code / advice (tuỳ logic bạn)
    valid_pd = valid_score  # xác suất default
    cic_score = prob_to_cic(valid_pd)          # ví dụ: chuẩn hoá ra 300–850
    rank_df = map_score_to_rank(cic_score)     # bucket A/B/C…

    # advice_df = give_advice(... )  # nếu hàm này trả về DataFrame

    return {
        "model": lgbm,
        "metrics": metrics,
        "psi_table": psi_table,
        "psi_value": psi_value,
        "n_train": len(X_train),
        "n_valid": len(X_valid),
        "feature_names": feature_names,
        "rank_df": rank_df,
    }


def main():
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Không tìm thấy dữ liệu: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)

    # Chọn experiment trên MLflow
    mlflow.set_experiment(EXPERIMENT_NAME)

    # Autolog cho LightGBM (log thêm nhiều thông tin)
    mlflow.lightgbm.autolog(log_input_examples=False, log_models=False)

    run_name = f"pb025_pipeline_{time.strftime('%Y%m%d_%H%M%S')}"
    print(f"[INFO] Start MLflow run: {run_name}")

    with mlflow.start_run(run_name=run_name) as run:
        mlflow.log_param("data_path", str(DATA_PATH))

        result = run_full_pipeline(df)

        lgbm = result["model"]
        metrics = result["metrics"]
        psi_table = result["psi_table"]
        psi_value = result["psi_value"]
        rank_df = result["rank_df"]

        # ----- log metrics -----
        for k, v in metrics.items():
            if isinstance(v, (int, float, np.floating)):
                mlflow.log_metric(k, float(v))

        mlflow.log_metric("psi_value", float(psi_value))
        mlflow.log_metric("n_train", result["n_train"])
        mlflow.log_metric("n_valid", result["n_valid"])

        # ----- log PSI table -----
        psi_path = "psi_table.csv"
        psi_table.to_csv(psi_path, index=False)
        mlflow.log_artifact(psi_path, artifact_path="psi")

        # ----- log mapping score/rank -----
        rank_path = "score_rank_mapping.csv"
        rank_df.to_csv(rank_path, index=False)
        mlflow.log_artifact(rank_path, artifact_path="score_mapping")

        # ----- log model -----
        print("[INFO] Logging LightGBM model lên MLflow Registry...")
        mlflow.lightgbm.log_model(
            lgbm,
            artifact_path="model",
            registered_model_name=MODEL_NAME,
        )

        print(f"[INFO] DONE – run id: {run.info.run_id}")


if __name__ == "__main__":
    main()
