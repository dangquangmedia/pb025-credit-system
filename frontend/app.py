import os
import requests
import streamlit as st

# Host API trong docker-compose: api:8000
API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")

# Fake user DB
USERS = {
    "citizen01": {"password": "citizen123", "role": "citizen"},
    "banker01": {"password": "banker123", "role": "banker"},
    "super01": {"password": "super123", "role": "supervisor"},
}


# =========================
#  Helpers gọi API backend
# =========================

def api_post(path: str, json: dict):
    url = f"{API_BASE_URL}{path}"
    try:
        resp = requests.post(url, json=json, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return None


def api_get(path: str):
    url = f"{API_BASE_URL}{path}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return None


# =========================
#  Citizen Portal
# =========================

def page_citizen(username: str):
    st.title("PB-025 – Cổng công dân (Citizen Portal)")
    st.caption("Form demo gửi yêu cầu cấp quyền truy xuất dữ liệu tín dụng.")

    with st.form("consent_form"):
        national_id = st.text_input("Số CCCD/CMND", "012345678901")
        bank_code = st.selectbox("Ngân hàng", ["Bank A", "Bank B (Demo)", "Bank C"])
        scope_credit = st.checkbox("Lịch sử CIC", True)
        scope_utility = st.checkbox("Hóa đơn điện nước", True)
        scope_income = st.checkbox("Thông tin thu nhập", False)
        submitted = st.form_submit_button("GỬI YÊU CẦU CONSENT")

    if submitted:
        st.success("Demo: Yêu cầu consent đã được ghi nhận (offline).")
        st.json(
            {
                "national_id": national_id,
                "bank_code": bank_code,
                "scope_credit": scope_credit,
                "scope_utility": scope_utility,
                "scope_income": scope_income,
            }
        )
        st.info("Trong bản MVP này chưa gọi API thật cho consent – chỉ minh họa luồng UI.")


# =========================
#  Banker Portal
# =========================

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
        amount = st.number_input(
            "Requested Loan Amount (VND)",
            min_value=10_000_000,
            value=200_000_000,
            step=10_000_000,
        )

    with col2:
        dti = st.number_input(
            "Debt-To-Income (DTI) %",
            min_value=5.0,
            max_value=95.0,
            value=40.0,
            step=1.0,
        )
        grade = st.selectbox("Current CIC-like Grade", ["A", "B", "C", "D", "E"], index=0)
        home = st.selectbox("Home Ownership", ["OWN", "MORTGAGE", "RENT"])
        purpose = st.selectbox(
            "Purpose of Loan",
            ["debt_consolidation", "small_business", "education", "home_improvement"],
            index=0,
        )

    if st.button("GỬI YÊU CẦU THẨM ĐỊNH"):
        payload = {
            "national_id": f"demo-{username}",
            "loan_amount": float(amount),
            "loan_tenor_months": int(tenor),
            "annual_income": float(income),
            "dti": float(dti),
            "grade": grade,
            "home_ownership": home,
            "purpose": purpose,
        }
        data = api_post("/api/v1/score", payload)
        if not data:
            return

        st.success("Đã nhận kết quả từ AI Scoring")

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("PD 12M (%)", f"{data['pd']:.2f}")
        with col_b:
            st.metric("Credit score (demo)", data["credit_score"])
        with col_c:
            st.metric("Risk band", data["grade_bucket"])

        st.write("Policy decision (demo):")
        st.info(data["policy_decision"])
        st.caption(f"Audit ID: {data['audit_id']} – Model: {data['model_version']}")

        with st.expander("Key factors (VI)"):
            for f in data.get("factors_vi", []):
                st.write("- ", f)

        with st.expander("Key factors (EN)"):
            for f in data.get("factors_en", []):
                st.write("- ", f)


# =========================
#  Supervisor Portal
# =========================

def page_supervisor(username: str):
    st.title("PB-025 – Dashboard Giám sát (Supervisor / Regulator Portal)")
    st.caption("Dùng synthetic stats để minh hoạ – không phải dữ liệu thật.")

    data = api_get("/api/v1/dashboard/summary")
    if not data:
        return

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Tập Train")
        st.metric("Số khoản vay", data["train_total"])
        st.metric("Bad rate", f"{data['train_bad_rate'] * 100:.2f}%")
    with col2:
        st.subheader("Tập Test")
        st.metric("Số khoản vay", data["test_total"])
        st.metric("Bad rate", f"{data['test_bad_rate'] * 100:.2f}%")

    st.subheader("Phân bố theo Grade (Train)")
    grade_bd = data.get("grade_breakdown", {})
    if not grade_bd:
        st.info("Không có dữ liệu grade.")
    else:
        for g, info in grade_bd.items():
            st.write(
                f"Grade {g}: {info['count']} khoản vay – bad rate ~ {info['bad_rate']*100:.1f}%"
            )

    st.caption(data.get("note", ""))


# =========================
#  Main
# =========================

def main():
    st.set_page_config(
        page_title="PB-025 Credit Demo",
        page_icon="💳",
        layout="wide",
    )

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.role = None

    st.sidebar.title("PB-025 Demo Login")

    if not st.session_state.logged_in:
        username = st.sidebar.selectbox("User", list(USERS.keys()))
        password = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Đăng nhập"):
            if USERS.get(username) and USERS[username]["password"] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = USERS[username]["role"]
                st.rerun()
            else:
                st.sidebar.error("Sai user hoặc password.")
        st.sidebar.caption(f"API_BASE_URL = {API_BASE_URL}")
        st.info("Đăng nhập để xem giao diện Citizen / Banker / Supervisor.")
        return

    if st.sidebar.button("Đăng xuất"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.role = None
        st.rerun()

    st.sidebar.write(f"Xin chào, **{st.session_state.username}**")
    st.sidebar.write(f"Role: `{st.session_state.role}`")
    st.sidebar.caption(f"API_BASE_URL = {API_BASE_URL}")

    role = st.session_state.role
    if role == "citizen":
        page_citizen(st.session_state.username)
    elif role == "banker":
        page_banker(st.session_state.username)
    elif role == "supervisor":
        page_supervisor(st.session_state.username)
    else:
        st.error("Role không hợp lệ.")


if __name__ == "__main__":
    main()
