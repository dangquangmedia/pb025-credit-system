import os
import requests
import streamlit as st

# ==== CẤU HÌNH API GỌI TỚI BACKEND TRONG DOCKER NETWORK ====
# Ép dùng host "api" (tên service trong docker-compose), port 8000
API_BASE_URL = "http://api:8000"

# =============================
# Fake user DB cho demo
# =============================
USERS = {
    "citizen01": {"password": "citizen123", "role": "citizen"},
    "banker01": {"password": "banker123", "role": "banker"},
    "super01": {"password": "super123", "role": "supervisor"},
}

# =============================
# Helpers
# =============================


def api_post(path: str, json: dict):
    """Gọi POST tới backend"""
    url = f"{API_BASE_URL}{path}"
    resp = requests.post(url, json=json, timeout=15)
    resp.raise_for_status()
    return resp.json()


def api_get(path: str, params: dict | None = None):
    """Gọi GET tới backend"""
    url = f"{API_BASE_URL}{path}"
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


# =============================
# Pages cho từng role
# =============================


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
            data = api_post("/api/v1/consent/grant", payload)
            if data:
                st.success(f"Consent đã được cấp: {data['consent_id']}")
                st.session_state["latest_consent_id"] = data["consent_id"]

    st.subheader("2️⃣ Thu hồi consent (Revoke)")
    consent_id = st.session_state.get("latest_consent_id", "")
    consent_id = st.text_input("Consent ID cần thu hồi", consent_id)
    if st.button("THU HỒI CONSENT") and consent_id:
        data = api_post(f"/api/v1/consent/{consent_id}/revoke", {})
        if data:
            st.success(f"Đã thu hồi consent {data['consent_id']} – trạng thái: {data['status']}")

    st.subheader("3️⃣ Tra cứu điểm tín dụng (Credit Score)")
    with st.form("score_form"):
        national_id = st.text_input("Số CCCD cho tra cứu", "012345678901", key="cid_score")
        loan_amount = st.number_input("Số tiền vay (VND)", value=200_000_000, step=10_000_000)
        tenor = st.number_input("Thời hạn vay (tháng)", value=24, min_value=3, max_value=120)
        income = st.number_input("Thu nhập năm (VND)", value=180_000_000, step=10_000_000)
        dti = st.number_input("DTI (%)", value=35.0)
        grade = st.selectbox("Nhóm điểm CIC hiện tại (ước lượng)", ["A", "B", "C", "D", "E", "F", "G"])
        home = st.selectbox("Tình trạng nhà ở", ["OWN", "MORTGAGE", "RENT"])
        purpose = st.selectbox(
            "Mục đích vay",
            ["debt_consolidation", "credit_card", "car", "small_business", "house", "other"],
        )

        submit_score = st.form_submit_button("TÍNH ĐIỂM")

        if submit_score:
            payload = {
                "national_id": national_id,
                "loan_amount": loan_amount,
                "loan_tenor_months": tenor,
                "annual_income": income,
                "dti": dti,
                "grade": grade,
                "home_ownership": home,
                "purpose": purpose,
            }
            data = api_post("/api/v1/score", payload)
            if data:
                st.metric("PD (xác suất vỡ nợ)", f"{data['pd']:.2f}%")
                st.write("Hạng:", data["grade_bucket"])
                st.write("Audit ID:", data["audit_id"])
                with st.expander("Các yếu tố chính (TIẾNG VIỆT)"):
                    for f in data["factors_vi"]:
                        st.write("- ", f)
                with st.expander("Key factors (ENGLISH)"):
                    for f in data["factors_en"]:
                        st.write("- ", f)

    st.subheader("4️⃣ Gửi khiếu nại (Complaint)")
    with st.form("complaint_form"):
        national_id = st.text_input("Số CCCD", "012345678901", key="cid_complain")
        complaint_type = st.text_input("Loại khiếu nại", "Điểm CIC không chính xác")
        desc = st.text_area("Nội dung khiếu nại", "Khoản vay X đã tất toán nhưng hệ thống vẫn hiển thị còn nợ.")
        sub = st.form_submit_button("GỬI KHIẾU NẠI")

        if sub:
            payload = {
                "national_id": national_id,
                "complaint_type": complaint_type,
                "description": desc,
            }
            data = api_post("/api/v1/complaint", payload)
            if data:
                st.success(f"Đã ghi nhận ticket: {data['ticket_id']} – trạng thái {data['status']}")

    st.subheader("5️⃣ Lịch sử khiếu nại")
    national_id = st.text_input("Số CCCD để xem lịch sử", "012345678901", key="cid_history")
    if st.button("XEM LỊCH SỬ KHIẾU NẠI"):
        data = api_get(f"/api/v1/complaint/{national_id}")
        if data is not None:
            if not data:
                st.info("Chưa có khiếu nại nào.")
            else:
                for c in data:
                    st.write("---")
                    st.write(f"Ticket: {c['ticket_id']}")
                    st.write(f"Loại: {c.get('complaint_type')}")
                    st.write(f"Trạng thái: {c['status']}")
                    st.write(f"Nội dung: {c['description']}")
                    st.write(f"Thời gian: {c['created_at']}")


def page_banker(username: str):
    st.title("PB-025 – Dashboard Thẩm định tín dụng (Banker Portal)")
    st.caption("Ngân hàng dùng để gửi hồ sơ và xem kết quả AI scoring")

    with st.form("banker_form"):
        national_id = st.text_input("Customer National ID", "012345678901")
        name = st.text_input("Customer Name (optional)", "Nguyen Van A")
        loan_amount = st.number_input("Desired Loan Amount (VND)", value=300_000_000, step=10_000_000)
        product = st.selectbox("Loan Product", ["Personal Loan", "Car Loan", "Mortgage", "Credit Card"])
        tenor = st.number_input("Loan Tenure (Months)", value=36, min_value=3, max_value=120)
        income = st.number_input("Customer Annual Income (VND)", value=200_000_000, step=10_000_000)
        dti = st.number_input("Debt-To-Income (DTI) %", value=40.0)
        grade = st.selectbox("Current CIC-like Grade", ["A", "B", "C", "D", "E", "F", "G"])
        home = st.selectbox("Home Ownership", ["OWN", "MORTGAGE", "RENT"])
        purpose = st.selectbox(
            "Purpose of Loan",
            ["debt_consolidation", "credit_card", "car", "small_business", "house", "other"],
        )

        submitted = st.form_submit_button("GỬI YÊU CẦU THẨM ĐỊNH")

            if submitted:
                payload = {
                    "national_id": national_id,
                    "loan_amount": loan_amount,
                    "loan_tenor_months": tenor,
                    "annual_income": income,
                    "dti": dti,
                    "grade": grade,
                    "home_ownership": home,
                    "purpose": purpose,
                }
        
                data = api_post("/api/v1/score", payload)
                if not data:
                    return
        
                # API hiện trả về pd_12m dạng 0.32 ~ 32% (demo)
                raw_pd = data.get("pd_12m")
                pd_pct = None
                if raw_pd is not None:
                    # giả sử 0–1 -> %
                    pd_pct = raw_pd * 100 if raw_pd <= 1 else raw_pd
        
                credit_score = data.get("credit_score")
                risk_band = data.get("risk_band")
                policy_decision = data.get("policy_decision")
                audit_id = data.get("audit_id")
        
                st.success("Đã nhận kết quả từ AI Scoring")
        
                if pd_pct is not None:
                    st.metric("PD (Probability of Default)", f"{pd_pct:.2f}%")
        
                if credit_score is not None:
                    st.metric("Credit Score", credit_score)
        
                if risk_band:
                    st.write("Risk band:", risk_band)
        
                if policy_decision:
                    st.write("Quyết định chính sách (demo):", policy_decision)
        
                if audit_id:
                    st.write("Audit ID:", audit_id)
        
                # Gợi ý quyết định dựa trên PD
                if pd_pct is not None:
                    if pd_pct < 5:
                        st.success("Có thể phê duyệt nhanh (low risk).")
                    elif pd_pct < 15:
                        st.info("Nên phê duyệt có điều kiện, kiểm tra thêm CIC & thu nhập.")
                    elif pd_pct < 30:
                        st.warning("Cần xem xét kỹ, nên bổ sung tài sản bảo đảm / đồng bảo lãnh.")
                    else:
                        st.error("Khuyến nghị: Từ chối hoặc yêu cầu giảm hạn mức.")
        
                # Các field factors_* hiện backend demo chưa trả về, tránh KeyError:
                with st.expander("Key factors (VI)"):
                    for f in data.get("factors_vi", []):
                        st.write("- ", f)
        
                with st.expander("Key factors (EN)"):
                    for f in data.get("factors_en", []):
                        st.write("- ", f)

def page_supervisor(username: str):
    st.title("PB-025 – Dashboard Giám sát (Supervisor / Regulator Portal)")
    st.caption("Dùng dữ liệu demo tổng hợp để minh hoạ health của mô hình.")

    data = api_get("/api/v1/dashboard/summary")
    if not data:
        st.error("Không lấy được dữ liệu dashboard từ API.")
        return

    stats = data.get("stats", {})
    by_decision = data.get("by_decision", [])
    note = data.get("note", "")

    total = stats.get("total", 0)
    approved = stats.get("approved", 0)
    rejected = stats.get("rejected", 0)
    avg_pd = stats.get("avg_pd", 0.0)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Tổng hồ sơ", total)
    with col2:
        approve_rate = (approved / total * 100) if total else 0
        st.metric("Tỷ lệ phê duyệt", f"{approve_rate:.1f}%")
    with col3:
        st.metric("PD trung bình", f"{avg_pd*100:.2f}%")

    st.subheader("Phân bố theo quyết định")
    for row in by_decision:
        st.write(f"- {row.get('decision')}: {row.get('count')} hồ sơ")

    if note:
        st.info(note)


# =============================
# Login + routing
# =============================


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
            # Streamlit sẽ tự rerun khi click button,
            # nhưng ta gọi thêm cho chắc.
            st.rerun()



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
        st.error("Role không hợp lệ.")


if __name__ == "__main__":
    main()
