import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# =====================================================================
# 1. Config
# =====================================================================

# Đường dẫn file train/test trong container
DATA_TRAIN_PATH = os.getenv("DATA_TRAIN_PATH", "data/loan_2014_18.csv")
DATA_TEST_PATH = os.getenv("DATA_TEST_PATH", "data/loan_2019_20.csv")

MAX_TRAIN_ROWS = int(os.getenv("MAX_TRAIN_ROWS", "50000"))
MAX_TEST_ROWS = int(os.getenv("MAX_TEST_ROWS", "30000"))

# Những trạng thái loan được coi là "bad"
BAD_STATUSES = {
    "Charged Off",
    "Default",
    "Late (31-120 days)",
    "Late (16-30 days)",
    "In Grace Period",
}

# =====================================================================
# 2. Pydantic models (schema cho API)
# =====================================================================


class ScoreRequest(BaseModel):
    national_id: str
    loan_amount: float
    loan_tenor_months: int
    annual_income: Optional[float] = None
    dti: Optional[float] = None  # debt-to-income
    grade: Optional[str] = None  # A,B,C...
    home_ownership: Optional[str] = None
    purpose: Optional[str] = None


class ScoreResponse(BaseModel):
    score_raw: float       # logit / risk score thô
    pd: float              # PD %
    grade_bucket: str      # Hạng O1/O2/O3/O4
    factors_vi: List[str]
    factors_en: List[str]
    audit_id: str


class ConsentGrantRequest(BaseModel):
    national_id: str
    bank_code: str
    scope_credit_history: bool = True
    scope_utility: bool = True
    scope_income: bool = False


class Consent(BaseModel):
    consent_id: str
    national_id: str
    bank_code: str
    scope_credit_history: bool
    scope_utility: bool
    scope_income: bool
    status: str
    granted_at: datetime
    valid_until: datetime


class ComplaintCreate(BaseModel):
    national_id: str
    complaint_type: Optional[str] = None
    description: str


class Complaint(BaseModel):
    ticket_id: str
    national_id: str
    complaint_type: Optional[str]
    description: str
    created_at: datetime
    status: str


class DashboardSummary(BaseModel):
    train_total: int
    train_bad_rate: float
    test_total: int
    test_bad_rate: float
    grade_breakdown: Dict[str, Dict[str, float]]  # grade -> {count, bad_rate}


# =====================================================================
# 3. In-memory “database” cho demo consent / complaint
# =====================================================================

CONSENTS: Dict[str, List[Consent]] = {}
COMPLAINTS: Dict[str, List[Complaint]] = {}

# =====================================================================
# 4. ML: train model từ dữ liệu thật
# =====================================================================

MODEL: Optional[Pipeline] = None

FEATURE_NUM = [
    "loan_amnt",
    "term_months",
    "int_rate_num",
    "installment",
    "annual_inc",
    "dti",
    "delinq_2yrs",
    "inq_last_6mths",
    "open_acc",
    "pub_rec",
    "revol_bal",
    "revol_util_num",
    "total_acc",
]

FEATURE_CAT = [
    "grade",
    "home_ownership",
    "purpose",
]

DASHBOARD_CACHE: Optional[DashboardSummary] = None


def generate_consent_id() -> str:
    return "CON-" + datetime.utcnow().strftime("%Y%m%d-%H%M%S")


def generate_audit_id() -> str:
    return "A-" + datetime.utcnow().strftime("%Y%m%d-%H%M%S")


def generate_ticket_id() -> str:
    return "TKT-" + datetime.utcnow().strftime("%Y%m%d-%H%M%S")


def _prepare_df_basic(df: pd.DataFrame) -> pd.DataFrame:
    """Chuẩn hóa các cột cần thiết (term, int_rate, revol_util...)."""
    df = df.copy()

    # term: "36 months" -> 36
    if "term" in df.columns:
        df["term_months"] = (
            df["term"].astype(str).str.extract(r"(\d+)").astype(float)
        )
    else:
        df["term_months"] = np.nan

    # int_rate: "7.97%" -> 7.97
    if "int_rate" in df.columns:
        df["int_rate_num"] = (
            df["int_rate"].astype(str)
            .str.replace("%", "", regex=False)
            .astype(float)
        )
    else:
        df["int_rate_num"] = np.nan

    # revol_util: "53.3%" -> 53.3
    if "revol_util" in df.columns:
        df["revol_util_num"] = (
            df["revol_util"].astype(str)
            .str.replace("%", "", regex=False)
            .astype(float)
        )
    else:
        df["revol_util_num"] = np.nan

    return df


def load_and_train_model() -> Pipeline:
    print(f"[ML] Loading train data from {DATA_TRAIN_PATH} ...")
    df = pd.read_csv(DATA_TRAIN_PATH, nrows=MAX_TRAIN_ROWS)
    df = _prepare_df_basic(df)

    # target y: 1 = xấu (bad), 0 = tốt
    df = df[df["loan_status"].notna()]
    df["y_bad"] = df["loan_status"].isin(BAD_STATUSES).astype(int)

    cols_needed = set(FEATURE_NUM + FEATURE_CAT + ["y_bad"])
    df = df[[c for c in df.columns if c in cols_needed]]

    X = df[FEATURE_NUM + FEATURE_CAT]
    y = df["y_bad"]

    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, FEATURE_NUM),
            ("cat", categorical_transformer, FEATURE_CAT),
        ]
    )

    clf = LogisticRegression(
        max_iter=1000,
        class_weight="balanced",
    )

    pipe = Pipeline(
        steps=[
            ("preprocess", preprocessor),
            ("clf", clf),
        ]
    )

    print("[ML] Training model...")
    pipe.fit(X, y)
    print("[ML] Training done.")
    return pipe


def build_dashboard_summary(model: Pipeline) -> DashboardSummary:
    """Tạo summary cho màn hình giám sát (train + test)."""
    print("[ML] Building dashboard summary...")
    df_train = pd.read_csv(DATA_TRAIN_PATH, nrows=MAX_TRAIN_ROWS)
    df_test = pd.read_csv(DATA_TEST_PATH, nrows=MAX_TEST_ROWS)

    def label_bad(df):
        df = df[df["loan_status"].notna()].copy()
        df["y_bad"] = df["loan_status"].isin(BAD_STATUSES).astype(int)
        return df

    df_train = label_bad(df_train)
    df_test = label_bad(df_test)

    train_total = len(df_train)
    test_total = len(df_test)
    train_bad_rate = float(df_train["y_bad"].mean()) if train_total > 0 else 0.0
    test_bad_rate = float(df_test["y_bad"].mean()) if test_total > 0 else 0.0

    grade_breakdown: Dict[str, Dict[str, float]] = {}
    for grade, group in df_train.groupby("grade"):
        grade_breakdown[str(grade)] = {
            "count": int(len(group)),
            "bad_rate": float(group["y_bad"].mean()) if len(group) > 0 else 0.0,
        }

    summary = DashboardSummary(
        train_total=train_total,
        train_bad_rate=train_bad_rate,
        test_total=test_total,
        test_bad_rate=test_bad_rate,
        grade_breakdown=grade_breakdown,
    )
    print("[ML] Dashboard summary ready.")
    return summary


def score_one(req: ScoreRequest, model: Pipeline) -> ScoreResponse:
    """Convert request -> features giống train, dự đoán PD."""
    import math

    row = {
        "loan_amnt": req.loan_amount,
        "term_months": req.loan_tenor_months,
        "int_rate_num": np.nan,
        "installment": np.nan,
        "annual_inc": req.annual_income,
        "dti": req.dti,
        "delinq_2yrs": np.nan,
        "inq_last_6mths": np.nan,
        "open_acc": np.nan,
        "pub_rec": np.nan,
        "revol_bal": np.nan,
        "revol_util_num": np.nan,
        "total_acc": np.nan,
        "grade": req.grade,
        "home_ownership": req.home_ownership,
        "purpose": req.purpose,
    }

    X = pd.DataFrame([row], columns=FEATURE_NUM + FEATURE_CAT)
    proba = model.predict_proba(X)[0]  # [p_good, p_bad]
    pd_bad = float(proba[1]) * 100.0

    # score_raw = logit(p_bad)
    eps = 1e-6
    p = min(max(proba[1], eps), 1 - eps)
    score_raw = float(math.log(p / (1 - p)))

    # Map PD → grade bucket
    if pd_bad < 5:
        grade_bucket = "Hạng 01 - Rất tốt / Grade 01 - Excellent"
    elif pd_bad < 15:
        grade_bucket = "Hạng 02 - Khá / Grade 02 - Very good"
    elif pd_bad < 30:
        grade_bucket = "Hạng 03 - Tốt / Grade 03 - Good"
    else:
        grade_bucket = "Hạng 04 - Rủi ro / Grade 04 - Risky"

    factors_vi: List[str] = []
    factors_en: List[str] = []

    if req.dti is not None and req.dti > 40:
        factors_vi.append("Tỷ lệ nợ / thu nhập (DTI) đang khá cao (> 40%).")
        factors_en.append("Debt-to-income ratio is relatively high (> 40%).")
    else:
        factors_vi.append("Tỷ lệ nợ / thu nhập (DTI) ở mức chấp nhận được.")
        factors_en.append("Debt-to-income ratio is acceptable.")

    if req.loan_amount > 500_000_000:
        factors_vi.append("Quy mô khoản vay lớn, cần xem xét kỹ dòng tiền trả nợ.")
        factors_en.append(
            "Requested loan amount is large; repayment capacity should be carefully reviewed."
        )
    else:
        factors_vi.append("Khoản vay ở mức phổ biến cho khách hàng bán lẻ.")
        factors_en.append("Loan amount is within typical retail range.")

    if req.loan_tenor_months > 36:
        factors_vi.append("Thời hạn vay dài, rủi ro thu nhập dài hạn cao hơn.")
        factors_en.append("Long loan tenure, higher long-term income risk.")
    else:
        factors_vi.append("Thời hạn vay trung bình (≤ 36 tháng).")
        factors_en.append("Medium-term loan tenure (≤ 36 months).")

    return ScoreResponse(
        score_raw=score_raw,
        pd=pd_bad,
        grade_bucket=grade_bucket,
        factors_vi=factors_vi,
        factors_en=factors_en,
        audit_id=generate_audit_id(),
    )


# =====================================================================
# 5. FastAPI app + endpoints
# =====================================================================

app = FastAPI(title="PB-025 Credit Engine Demo API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # demo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Khởi động: train model + build dashboard
MODEL = load_and_train_model()
DASHBOARD_CACHE = build_dashboard_summary(MODEL)


@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.utcnow()}


@app.post("/api/v1/score", response_model=ScoreResponse)
def api_score(request: ScoreRequest):
    if MODEL is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    return score_one(request, MODEL)


@app.post("/api/v1/consent/grant", response_model=Consent)
def grant_consent(req: ConsentGrantRequest):
    consent = Consent(
        consent_id=generate_consent_id(),
        national_id=req.national_id,
        bank_code=req.bank_code,
        scope_credit_history=req.scope_credit_history,
        scope_utility=req.scope_utility,
        scope_income=req.scope_income,
        status="active",
        granted_at=datetime.utcnow(),
        valid_until=datetime.utcnow() + timedelta(days=30),
    )
    CONSENTS.setdefault(req.national_id, []).append(consent)
    return consent


@app.post("/api/v1/consent/{consent_id}/revoke", response_model=Consent)
def revoke_consent(consent_id: str):
    for national_id, lst in CONSENTS.items():
        for c in lst:
            if c.consent_id == consent_id:
                c.status = "revoked"
                return c
    raise HTTPException(status_code=404, detail="Consent not found")


@app.get("/api/v1/consent/{national_id}/latest", response_model=Consent)
def get_latest_consent(national_id: str):
    history = CONSENTS.get(national_id)
    if not history:
        raise HTTPException(status_code=404, detail="No consent found for this national_id")
    return history[-1]


@app.get("/api/v1/consent/{national_id}/history", response_model=List[Consent])
def get_consent_history(national_id: str):
    return CONSENTS.get(national_id, [])


@app.post("/api/v1/complaint", response_model=Complaint)
def create_complaint(req: ComplaintCreate):
    comp = Complaint(
        ticket_id=generate_ticket_id(),
        national_id=req.national_id,
        complaint_type=req.complaint_type,
        description=req.description,
        created_at=datetime.utcnow(),
        status="received",
    )
    COMPLAINTS.setdefault(req.national_id, []).append(comp)
    return comp


@app.get("/api/v1/complaint/{national_id}", response_model=List[Complaint])
def list_complaints(national_id: str):
    return COMPLAINTS.get(national_id, [])


@app.get("/api/v1/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary():
    if DASHBOARD_CACHE is None:
        raise HTTPException(status_code=500, detail="Dashboard not ready")
    return DASHBOARD_CACHE
