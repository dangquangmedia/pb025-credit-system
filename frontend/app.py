import os
import requests
import streamlit as st

# ==============================
# CẤU HÌNH API
# ==============================
# Trong Docker, UI sẽ gọi tới service "api" trên port 8000
API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")

# Fake user DB cho demo
USERS = {
    "citizen01": {"password": "citizen123", "role": "citizen"},
    "banker01": {"password": "banker123", "role": "banker"},
    "super01": {"password": "super123", "role": "supervisor"},
}


# ==============================
# Helpers gọi API
# ==============================
def api_post(path: str, json: dict):
    """Gọi POST tới backend"""
    url = f"{API_BASE_URL}{path}"
    try:
        resp = requests.post(url, json=json, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as e:
        try:
            detail = resp.text
        except Exception:
            detail = str(e)
        st.error(f"API error {resp.status_code}: {detail}")
    except Exception as e:
        st.error(f"Không gọi được API: {e}")
    return None


def api_get(path: str, params: dict | None = None):
    """Gọi GET tới backend"""
    url = f"{API_BASE_URL}{path}"
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as e:
        try:
            detail = resp.text
        except Exception:
            detail = str(e)
        st.error(f"API error {resp.status_code}: {detail}")
    except Exception as e:
        st.error(f"Không gọi được API: {e}")
    return None


# ==============================
# Đăng nhập
# ==============================
def login():
    st.title("PB-025 – National Credit Engine Demo")
    st.caption("Đăng nhập để vào đúng giao diện (Citizen / Banker / Supervisor)")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = USERS.get(username)
        if not user or user["password"] != password:
            st.error("Sai username hoặc password.")
        else:
            st.session_state["user"] = {
                "username": username,
                "role": user["role"],
            }
            st.rerun()


# ==============================
# Citizen Portal (demo nhẹ)
# ==============================
def page_citizen(username: str):
    st.title("PB-025 – Cổng công dân (Citizen Portal)")

    st.subheader("1️⃣ Cấp quyền truy xuất dữ liệu tín dụng (Consent)")
    with st.form("consent_form"):
        national_id = st.text_input("Số CCCD/CMND", "012345678901")
        bank_code = st.selectbox("Ngân hàng", ["Bank A", "Bank B (Demo)", "Bank C"])
        scope_credit = st.checkbox("Lịch sử CIC", True)
        scope_utility = st.checkbox("Hóa đơn điện nước", True)
        scope_income = st.checkbox("Thông tin thu nhập", False)
        submitted = st.form_submit_button("GỬI YÊU CẦU CONSENT")

    if submitted:
        payload = {
            "national_id": national_id,
            "bank_code": bank_code,
            "scope_credit_history": scope_credit,
            "scope_utility": scope_utility,
            "scope_income": scope_income,
        }
        # Hiện demo chưa xử lý backend cho citizen → chỉ log thông tin
        st.info("Demo hiện tại mới focus Banking & Supervisor Portal, Citizen Portal chỉ minh họa.")


# ==============================
# Banker Portal
# ==============================
def page_banker(username: str):
    st.title("PB-025 – Banking View (Banker Portal)")
    st.caption("Form demo gửi hồ sơ vay cho AI Scoring")

    col1, col2 = st.columns(2)

    with col1:
        product = st.selectbox("Loan Product", ["Personal Loan", "Mortgage", "Auto Loan"])
        tenor = st.number_input("Loan Tenure (Months)", min_value=6, max_value=120, value=36, step=6)
        income = st.number_input(
            "Customer Annual Income (VND)",
            min_value=10_000_000,
            value=20_000_000,
            step=5_000_000,
        )
        loan_amount = st.number_input(
            "Requested Loan Amount (VND)",
            min_value=10_000_000,
            value=200_000_000,
            step=10_000_000,
        )

    with col2:
        dti = st.number_input("Debt-To-Income (DTI) %", min_value=0.0, max_value=200.0, value=40.0, step=1.0)
        grade = st.selectbox("Current CIC-like Grade", ["A", "B", "C", "D", "E"])
        home = st.selectbox("Home Ownership", ["OWN", "MORTGAGE", "RENT", "OTHER"])
        purpose = st.selectbox(
            "Purpose of Loan",
            ["debt_consolidation", "education", "small_business", "home_improvement", "medical", "other"],
        )

    if st.button("GỬI YÊU CẦU THẨM ĐỊNH"):
        # Payload match với backend /api/v1/score (demo)
        payload = {
            "loan_amount": loan_amount,
            "loan_product": product.lower().replace(" ", "_"),
            "loan_tenor_months": int(tenor),
            "annual_income": income,
            "dti": dti,
            "grade": grade,
            "home_ownership": home,
            "purpose": purpose,
        }

        data = api_post("/api/v1/score", payload)
        if not data:
            return

        st.success("Đã nhận kết quả từ AI Scoring")

        # ---- PD: hỗ trợ cả pd_12m (0.32) hoặc pd (32.0) ----
        pd_value = data.get("pd_12m")
        if pd_value is None:
            pd_value = data.get("pd")

        if pd_value is not None:
            # Nếu backend trả 0.32 → nhân 100; nếu trả 32 → giữ nguyên
            pd_pct = pd_value * 100.0 if pd_value <= 1 else pd_value
            st.metric("PD (Probability of Default)", f"{pd_pct:.2f}%")

        # Credit score
        credit_score = data.get("credit_score")
        if credit_score is not None:
            st.metric("Credit score (demo scale)", f"{credit_score:.0f}")

        # Risk band + policy
        risk_band = data.get("risk_band")
        if risk_band:
            st.write("Risk band:", risk_band)

        policy = data.get("policy_decision")
        if policy:
            st.write("Policy decision:", policy)

        citizen_hash = data.get("citizen_hash")
        audit_id = data.get("audit_id")
        if citizen_hash or audit_id:
            st.caption(f"citizen_hash = {citizen_hash} | audit_id = {audit_id}")

        # Nếu backend sau này có factors_vi / factors_en thì show
        if "factors_vi" in data or "factors_en" in data:
            with st.expander("Key factors (VI)"):
                for f in data.get("factors_vi", []):
                    st.write("- ", f)
            with st.expander("Key factors (EN)"):
                for f in data.get("factors_en", []):
                    st.write("- ", f)


# ==============================
# Supervisor Portal
# ==============================
def page_supervisor(username: str):
    st.title("PB-025 – Dashboard Giám sát (Supervisor / Regulator Portal)")
    st.caption("Dùng dữ liệu demo loan_2014_18 (train) & loan_2019_20 (test)")

    data = api_get("/api/v1/dashboard/summary")
    if not data:
        return

    stats = data.get("stats", {})
    total = stats.get("total", 0)
    approved = stats.get("approved", 0)
    rejected = stats.get("rejected", 0)
    avg_pd = stats.get("avg_pd", 0.0)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Tổng hồ sơ", total)
    col2.metric("Đã phê duyệt", approved)
    col3.metric("Từ chối", rejected)
    col4.metric("PD trung bình", f"{avg_pd * 100:.2f}%")

    by_decision = data.get("by_decision", [])
    if by_decision:
        st.subheader("Phân bố theo quyết định (demo)")
        for row in by_decision:
            st.write(f"- {row.get('decision')}: {row.get('count')} hồ sơ")

    note = data.get("note")
    if note:
        st.info(note)


# ==============================
# MAIN
# ==============================
def main():
    st.set_page_config(
        page_title="PB-025 Credit Demo",
        page_icon="💳",
        layout="wide",
    )

    user = st.session_state.get("user")
    if not user:
        login()
        return

    role = user["role"]
    username = user["username"]

    # Sidebar chung
    with st.sidebar:
        st.write(f"Xin chào, **{username}**")
        st.write(f"Role: `{role}`")
        st.caption(f"API_BASE_URL = {API_BASE_URL}")
        if st.button("Đăng xuất"):
            st.session_state.pop("user")
            st.rerun()

    # Route theo role
    if role == "citizen":
        page_citizen(username)
    elif role == "banker":
        page_banker(username)
    elif role == "supervisor":
        page_supervisor(username)
    else:
        st.error(f"Role không hợp lệ: {role}")


if __name__ == "__main__":
    main()
