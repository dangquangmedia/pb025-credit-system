import os

import mlflow
import mlflow.sklearn

from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score


def main():
    # Lấy tracking URI từ biến môi trường (nếu có),hoặc dùng thẳng địa chỉ EC2
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://34.204.202.24:5000")
    mlflow.set_tracking_uri(tracking_uri)

    # Tên experiment sẽ thấy trên UI MLflow
    mlflow.set_experiment("pb025_sanity_check")

    # Dùng dataset có sẵn của sklearn cho nhanh, ko phụ thuộc file CSV bên ngoài
    data = load_breast_cancer()
    X_train, X_test, y_train, y_test = train_test_split(
        data.data, data.target, test_size=0.2, random_state=42
    )

    # Một vài hyper-parameter đơn giản
    n_estimators = 200
    max_depth = 5

    with mlflow.start_run(run_name="rf_baseline"):
        model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=42,
            n_jobs=-1,
        )
        model.fit(X_train, y_train)
        proba = model.predict_proba(X_test)[:, 1]
        auc = roc_auc_score(y_test, proba)

        # Log param + metric
        mlflow.log_param("n_estimators", n_estimators)
        mlflow.log_param("max_depth", max_depth)
        mlflow.log_metric("auc", auc)

        # Log luôn model
        mlflow.sklearn.log_model(model, artifact_path="model")

        print(f"AUC on test set: {auc:.4f}")
        print("Logged to MLflow at:", tracking_uri)


if __name__ == "__main__":
    main()
