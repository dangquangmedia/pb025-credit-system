import os
import requests
import streamlit as st

# ============================================
# CẤU HÌNH API BACKEND (trong Docker network)
# ============================================
# Docker Compose đang set: API_BASE_URL=http://api:8000
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


# ============================================
# Fake "DB user" cho demo
# ============================================
USERS = {
    "citizen01": {"password": "citizen123", "role": "citizen"},
    "banker01": {"password": "banker123", "role": "banker"},
    "super01": {"password": "super123", "role": "supervisor"},
}


# ============================================
# Helpers gọi API
# ============================================
def api_post(path: str, json: dict):
    """Gọi POST tới backend, path bắt đầu bằng /"""
    url = f"{API_BASE_URL}{path}"
    try:
        resp = requests.post(url, json=json, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        status = getattr(e.response, "status_code", "N/A")
        st.error(f"API error {status}: {e}")
        return None


def api_get(path: str, params: dict | None = None):
    """Gọi GET tới backend, path bắt đầu bằng /"""
    url = f"{API_BASE_URL}{path}"
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        status = getattr(e.response, "status_code", "N/A")
        st.error(f"API error {status}: {e}")
        return None


# ============================================
# Login
# ============================================
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
            # Streamlit 1.39 dùng st.rerun()
            st.rerun()


# ============================================
# Pages cho từng role
# ============================================
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
        st.success(
            "Đã ghi nhận yêu cầu cấp quyền (demo). "
            "Trong phiên bản thật sẽ ghi vào Consent Ledger / NDOP."
        )

    st.markdown("---")
    st.subheader("2️⃣ Kiểm tra lịch sử yêu cầu gần đây (demo)")
    st.info(
        "Khu vực này demo, chưa kết nối API thật. "
        "Mục đích là cho BGK thấy flow công dân → banker."
    )


def page_banker(username: str):
    st.title("PB-025 – Banking View (Banker Portal)")
    st.caption("Form demo gửi hồ sơ vay cho AI Scoring")

    col1, col2 = st.columns(2)

    with col1:
        loan_product = st.selectbox(
            "Loan Product",
            ["Personal Loan", "Home Loan", "Auto Loan", "Credit Card"],
            index=0,
        )
        tenor = st.number_input(
            "Loan Tenure (Months)", min_value=6, max_value=120, value=36, step=6
        )
        income = st.number_input(
            "Customer Annual Income (VND)",
            min_value=10_000_000,
            value=20_000_000,
            step=1_000_000,
        )

    with col2:
        dti = st.number_input(
            "Debt-To-Income (DTI) %",
            min_value=0.0,
            max_value=100.0,
            value=40.0,
            step=1.0,
        )
        grade = st.selectbox(
            "Current CIC-like Grade", ["A", "B", "C", "D", "E"], index=0
        )
        home = st.selectbox(
            "Home Ownership", ["OWN", "RENT", "MORTGAGE"], index=0
        )
        purpose = st.selectbox(
            "Purpose of Loan",
            ["debt_consolidation", "home_improvement", "business", "education", "other"],
            index=0,
        )

    submitted = st.button("GỬI YÊU CẦU THẨM ĐỊNH")

    if submitted:
        # payload tối giản gửi lên /api/v1/score
        payload = {
            # Demo: loan_amount ≈ annual_income × DTI
            "loan_amount": income * (dti / 100.0),
            "loan_product": loan_product.lower().replace(" ", "_"),
            "loan_tenor_months": int(tenor),
            "loan_purpose": purpose,
        }

        data = api_post("/api/v1/score", payload)
        if not data:
            return

        # Backend trả về: pd_12m (0.32 = 32%), credit_score, risk_band, policy_decision, audit_id
        pd_12m = float(data.get("pd_12m", 0.0)) * 100.0
        credit_score = data.get("credit_score", "N/A")
        risk_band = data.get("risk_band", "N/A")
        policy_decision = data.get("policy_decision", "N/A")
        audit_id = data.get("audit_id", "N/A")

        st.success("Đã nhận kết quả từ AI Scoring")

        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("PD 12 tháng (Probability of Default)", f"{pd_12m:.2f}%")
        with col_b:
            st.metric("Credit Score (demo)", f"{credit_score}")

        st.write("**Risk band:**", risk_band)
        st.write("**Policy decision (gợi ý):**", policy_decision)
        st.write("**Audit ID:**", audit_id)

        # Gợi ý đơn giản dựa trên PD
        if pd_12m < 5:
            st.success("Khuyến nghị: Có thể phê duyệt nhanh (low risk).")
        elif pd_12m < 15:
            st.info(
                "Khuyến nghị: Phê duyệt có điều kiện, kiểm tra thêm CIC & thu nhập."
            )
        elif pd_12m < 30:
            st.warning(
                "Khuyến nghị: Cần xem xét kỹ, nên yêu cầu tài sản bảo đảm / đồng bảo lãnh."
            )
        else:
            st.error("Khuyến nghị: Từ chối hoặc yêu cầu giảm hạn mức.")


def page_supervisor(username: str):
    st.title("PB-025 – Dashboard Giám sát (Supervisor / Regulator Portal)")
    st.caption("Dùng dữ liệu tổng hợp demo từ backend /api/v1/dashboard/summary")

    data = api_get("/api/v1/dashboard/summary")
    if not data:
        return

    stats = data.get("stats", {})
    by_decision = data.get("by_decision", [])
    note = data.get("note", "")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Tổng số hồ sơ", stats.get("total", 0))
    with col2:
        st.metric("APPROVED", stats.get("approved", 0))
    with col3:
        st.metric("REJECTED", stats.get("rejected", 0))

    avg_pd = float(stats.get("avg_pd", 0.0)) * 100.0
    st.metric("Average PD 12m (demo)", f"{avg_pd:.2f}%")

    st.subheader("Phân bố theo quyết định")
    if not by_decision:
        st.info("Chưa có dữ liệu phân bố quyết định.")
    else:
        for row in by_decision:
            decision = row.get("decision", "UNKNOWN")
            count = row.get("count", 0)
            st.write(f"- {decision}: {count} hồ sơ")

    if note:
        st.info(note)


# ============================================
# MAIN
# ============================================
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

    with st.sidebar:
        st.write(f"Xin chào, **{username}**")
        st.write(f"Role: `{role}`")
        # debug: xem API_BASE_URL thực tế trong container
        st.caption(f"API_BASE_URL = {API_BASE_URL}")
        if st.button("Đăng xuất"):
            st.session_state.pop("user", None)
            st.rerun()

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
