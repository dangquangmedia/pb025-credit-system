from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import math
import hashlib
import uuid

app = FastAPI(
    title="PB-025 Scoring API (demo)",
    version="0.1.0",
    description="Demo API chấm điểm tín dụng cho PB-025",
)


# ==========
#  Models
# ==========

class ScoreRequest(BaseModel):
    national_id: Optional[str] = None
    loan_amount: float
    loan_tenor_months: int = 36
    annual_income: Optional[float] = None
    dti: Optional[float] = None
    grade: Optional[str] = None
    home_ownership: Optional[str] = None
    purpose: Optional[str] = None


# ==========
#  Helpers
# ==========

def _hash_citizen(national_id: Optional[str]) -> str:
    if not national_id:
        national_id = "anonymous"
    h = hashlib.sha256(national_id.encode("utf-8")).hexdigest()
    # rút gọn cho dễ nhìn
    return h[:12]


def _synthetic_score(req: ScoreRequest) -> Dict[str, Any]:
    amount = float(req.loan_amount)
    tenor = int(req.loan_tenor_months or 36)

    # DTI – dùng income nếu có, fallback sang dti %
    if req.annual_income and req.annual_income > 0:
        dti = amount / req.annual_income
    elif req.dti:
        dti = float(req.dti) / 100.0
    else:
        dti = 0.4  # default 40%

    # baseline PD ~ hàm của amount + dti + tenor
    base_pd = 0.05 + 0.0000000003 * amount
    base_pd += max(dti - 0.3, 0) * 0.4
    if tenor > 36:
        base_pd += (tenor - 36) * 0.001

    grade_factor = {
        "A": -0.03,
        "B": -0.01,
        "C": 0.02,
        "D": 0.05,
        "E": 0.08,
    }.get((req.grade or "C").upper(), 0.0)

    base_pd += grade_factor
    base_pd = max(0.005, min(base_pd, 0.7))

    # logit + credit score demo 300–900
    odds = base_pd / (1 - base_pd)
    logit = math.log(odds)
    credit_score = 800 - logit * 120
    credit_score = max(300, min(900, credit_score))

    # risk band
    if base_pd < 0.03:
        band = "A"
    elif base_pd < 0.06:
        band = "B"
    elif base_pd < 0.12:
        band = "C"
    elif base_pd < 0.25:
        band = "D"
    else:
        band = "E"

    # policy demo
    if band in ("A", "B"):
        policy = "PHÊ DUYỆT (demo)"
    elif band == "C":
        policy = "PHÊ DUYỆT có điều kiện (demo)"
    elif band == "D":
        policy = "XEM XÉT THÊM – YÊU CẦU TÀI SẢN BẢO ĐẢM (demo)"
    else:
        policy = "TỪ CHỐI / GIẢM HẠN MỨC (demo)"

    # factors tiếng Việt
    factors_vi = []
    if dti > 0.6:
        factors_vi.append("DTI cao (>60%) – rủi ro gánh nặng nợ.")
    if amount > 500_000_000:
        factors_vi.append("Khoản vay lớn – cần thẩm định bổ sung.")
    if (req.grade or "").upper() in ("D", "E"):
        factors_vi.append("CIC-like grade thấp (D/E).")
    if not factors_vi:
        factors_vi.append("Hồ sơ nằm trong ngưỡng rủi ro chấp nhận được.")

    # factors tiếng Anh
    factors_en = [
        "High DTI (>60%) – debt burden risk." if dti > 0.6 else "",
        "Large exposure amount – require extra checks."
        if amount > 500_000_000
        else "",
        "Low CIC-like grade (D/E)." if (req.grade or "").upper() in ("D", "E") else "",
    ]
    factors_en = [f for f in factors_en if f] or ["Risk level acceptable for demo."]

    citizen_hash = _hash_citizen(req.national_id)
    audit_id = f"A-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"

    # trả cả field old + new để UI dùng thoải mái
    result = {
        "citizen_hash": citizen_hash,
        "audit_id": audit_id,
        "pd_12m": round(base_pd, 4),          # PD dạng tỷ lệ
        "pd": round(base_pd * 100, 2),        # PD dạng %
        "score_raw": round(logit, 4),
        "credit_score": int(round(credit_score)),
        "grade_bucket": band,
        "policy_decision": policy,
        "factors_vi": factors_vi,
        "factors_en": factors_en,
        "model_version": "demo-2025-11",
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }
    return result


# ==========
#  Endpoints
# ==========

@app.get("/health")
def health() -> str:
    return "OK"


@app.post("/api/v1/score")
def score_endpoint(req: ScoreRequest):
    """Endpoint chính cho Banker Portal."""
    return _synthetic_score(req)


@app.get("/api/v1/dashboard/summary")
def dashboard_summary():
    """Synthetic summary cho Supervisor Dashboard."""
    train_total = 1_000_000
    test_total = 200_000
    train_bad_rate = 0.06
    test_bad_rate = 0.065

    grade_breakdown = {
        "A": {"count": 250_000, "bad_rate": 0.01},
        "B": {"count": 300_000, "bad_rate": 0.03},
        "C": {"count": 250_000, "bad_rate": 0.07},
        "D": {"count": 150_000, "bad_rate": 0.15},
        "E": {"count": 50_000, "bad_rate": 0.30},
    }

    return {
        "train_total": train_total,
        "test_total": test_total,
        "train_bad_rate": train_bad_rate,
        "test_bad_rate": test_bad_rate,
        "grade_breakdown": grade_breakdown,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "note": "Synthetic summary cho PB-025 demo – thay bằng metric thật khi có dữ liệu.",
    }
