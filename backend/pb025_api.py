# backend/pb025_api.py

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
from datetime import datetime
import hashlib
import uuid
import json

app = FastAPI(
    title="PB-025 Scoring API (demo)",
    version="0.1.0",
    description="API chấm điểm tín dụng demo cho PB-025"
)


# ====== SCHEMA REQUEST ======

class ScoreRequest(BaseModel):
    citizen_id: str
    phone_suffix: Optional[str] = None
    request_org: str
    ndop_purpose: str
    loan_amount: float
    loan_product: str
    loan_tenor_months: int
    loan_purpose: str


# ====== CẤU HÌNH LOG ======

AUDIT_LOG_PATH = Path(__file__).parent / "data" / "audit_log.jsonl"


# ====== HEALTHCHECK ======

@app.get("/health")
def health():
    return "OK"


# ====== HÀM TÍNH ĐIỂM DEMO (synthetic) ======

def synthetic_score(req: ScoreRequest) -> dict:
    """
    Tính PD, credit_score, risk_band và policy_decision DEMO.
    Không dùng model thật, chỉ là rule đơn giản cho demo.
    """

    # PD cơ bản ~ 25%
    base_pd = 0.25

    # Vay càng nhiều, PD tăng nhẹ
    amt_factor = min(req.loan_amount / 500_000_000, 1.0) * 0.10  # tối đa +0.10

    # Kỳ hạn càng dài, PD tăng thêm
    tenor_factor = min(max(req.loan_tenor_months / 60, 0.0), 1.0) * 0.05  # tối đa +0.05

    pd_12m = base_pd + amt_factor + tenor_factor
    pd_12m = float(min(max(pd_12m, 0.01), 0.99))  # clamp 1%–99%

    # Mapping PD -> credit_score (giả lập thang 300–900)
    credit_score = int((1.0 - pd_12m) * 900)

    # Phân hạng rủi ro
    if pd_12m < 0.15:
        risk_band = "Hạng 01 – Tốt"
    elif pd_12m < 0.30:
        risk_band = "Hạng 02 – Khá"
    elif pd_12m < 0.50:
        risk_band = "Hạng 03 – Trung bình"
    else:
        risk_band = "Hạng 04 – Rủi ro cao"

    # Quyết định policy demo
    if pd_12m < 0.15:
        policy_decision = "PHÊ DUYỆT"
    elif pd_12m < 0.35:
        policy_decision = "PHÊ DUYỆT có điều kiện (demo)"
    else:
        policy_decision = "TỪ CHỐI (demo)"

    # Hash citizen_id để không lộ PII
    citizen_hash = hashlib.sha256(req.citizen_id.encode("utf-8")).hexdigest()[:12]

    # Tạo audit_id dạng A-YYYYMMDD-XXXXX
    audit_id = "A-" + datetime.utcnow().strftime("%Y%m%d") + "-" + uuid.uuid4().hex[:5].upper()

    return {
        "pd_12m": round(pd_12m, 2),
        "credit_score": credit_score,
        "risk_band": risk_band,
        "policy_decision": policy_decision,
        "citizen_hash": citizen_hash,
        "audit_id": audit_id,
    }


# ====== GHI AUDIT LOG ======

def append_audit_log(req: ScoreRequest, result: dict) -> None:
    """
    Ghi 1 dòng log JSON vào file data/audit_log.jsonl.
    Mỗi dòng = 1 JSON (JSON Lines).
    """

    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    log_entry = {
        "audit_id": result.get("audit_id"),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "actor": "system@pb025",
        "action": "score_apply",
        "citizen_hash": result.get("citizen_hash"),
        "decision": result.get("policy_decision"),
        "request_org": req.request_org,
        "loan_amount": req.loan_amount,
        "loan_tenor_months": req.loan_tenor_months,
        "loan_product": req.loan_product,
        "loan_purpose": req.loan_purpose,
    }

    with AUDIT_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")


# ====== ENDPOINT CHÍNH ======

@app.post("/score/apply")
def score_apply(req: ScoreRequest):
    """
    Endpoint chính cho Banking Dashboard gọi.
    """
    result = synthetic_score(req)
    append_audit_log(req, result)
    return result
