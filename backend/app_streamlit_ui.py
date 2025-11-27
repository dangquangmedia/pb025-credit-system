import json
import hashlib
from datetime import datetime
import pandas as pd
import numpy as np
import requests
import streamlit as st
from pathlib import Path
# =========================
# CONFIG CHUNG
# =========================

st.set_page_config(
    page_title="PB-025 UI Demo",
    layout="wide",
    initial_sidebar_state="expanded",
)


def load_custom_css():
    """Tô màu CSS cho UI đẹp hơn, nhưng giữ nguyên layout."""
    st.markdown(
        """
        <style>
        /* Nền tổng thể */
        .stApp {
            background-color: #f3f4f6;
            font-family: "Inter", system-ui, -apple-system, BlinkMacSystemFont,
                         "Segoe UI", sans-serif;
        }

        /* Sidebar tối màu */
        section[data-testid="stSidebar"] {
            background-color: #111827;
        }
        section[data-testid="stSidebar"] * {
            color: #e5e7eb !important;
        }
        section[data-testid="stSidebar"] .stRadio label div {
            font-size: 0.9rem;
        }

        /* Tiêu đề chính */
        h1 {
            font-weight: 800 !important;
            letter-spacing: 0.02em;
        }

        /* Caption dưới title */
        .pb-caption {
            margin-bottom: 1.5rem;
        }
        .pb-caption p {
            font-size: 0.85rem;
            color: #6b7280 !important;
            margin-bottom: 0;
        }

        /* Button đẹp hơn */
        .stButton>button {
            border-radius: 999px;
            padding: 0.45rem 1.4rem;
            font-weight: 600;
            border: 0px;
            background: linear-gradient(90deg, #2563eb, #4f46e5);
            color: #ffffff;
        }
        .stButton>button:hover {
            box-shadow: 0 8px 18px rgba(37, 99, 235, 0.35);
            transform: translateY(-1px);
        }

        /* Các card / alert bo tròn hơn */
        .stAlert {
            border-radius: 0.75rem;
        }

        /* JSON debug box nhỏ lại 1 chút */
        pre {
            font-size: 0.8rem;
            border-radius: 0.75rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_main_header():
    """Header chung cho mọi màn hình."""
    st.title("PB-025 Demo UI")
    st.markdown(
        """
        <div class="pb-caption">
            <p>
                Demo mode • Một phần dữ liệu lấy từ API <code>/score/apply</code> (nếu cấu hình) •
                AI rủi ro cao có giám sát con người • Tuân thủ định hướng PDPL 2025 &amp; Dự thảo Luật AI
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================
# API CONFIG
# =========================

# Test local với FastAPI port 8000
API_BASE_URL = "http://localhost:8000"


def api_post(path: str, payload: dict):
    """
    Gọi POST tới API backend.
    path: vd "/score/apply" hoặc "score/apply".
    Trả về (data, error) trong đó error là string nếu lỗi.
    """
    base = API_BASE_URL.rstrip("/")
    if not path.startswith("/"):
        path = "/" + path
    url = base + path

    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json(), None
    except Exception as ex:
        return None, f"Gọi API {path} thất bại: {ex}"


# =========================
# MÀN HÌNH 1 – CÔNG DÂN (DSAP)
# =========================

def view_citizen():
    render_main_header()

    st.header("PB-025 — Cổng Công Dân (DSAP)")
    st.caption("Cấp quyền truy xuất dữ liệu tín dụng an toàn • Minh bạch • Có thể thu hồi ngay")

    st.subheader("1. Cấp quyền (Consent)")
    col1, col2 = st.columns(2)

    with col1:
        citizen_id = st.text_input("Số CCCD/CMND", "012345678901")
        request_org = st.selectbox(
            "Tổ chức yêu cầu",
            ["Ngân hàng A (demo)", "Ngân hàng B (demo)"],
        )
        purpose = st.selectbox(
            "Mục đích xử lý",
            [
                "Đánh giá khả năng cấp tín dụng cá nhân",
                "Thẩm định mở thẻ tín dụng",
                "Gia hạn / cơ cấu lại nợ",
            ],
        )
    with col2:
        st.markdown("**Phạm vi dữ liệu (mock)**")
        scope_cic = st.checkbox("Dữ liệu CIC (lịch sử khoản vay, tình trạng nợ)", value=True)
        scope_utility = st.checkbox("Dữ liệu điện / nước / viễn thông", value=True)
        scope_tax = st.checkbox("Dữ liệu TNCN (thuế) (mock)", value=False)
        agree = st.checkbox("Tôi đồng ý PB-025 truy xuất dữ liệu trên", value=True)

    scope = {
        "cic": scope_cic,
        "utility": scope_utility,
        "tax": scope_tax,
    }

    consent_event = {
        "citizen_id": citizen_id,
        "request_org": request_org,
        "purpose": purpose,
        "scope": scope,
        "agree": agree,
        "created_at": datetime.utcnow().isoformat() + "Z",
    }

    st.subheader("2. Log consent (demo)")
    st.code(json.dumps(consent_event, indent=4, ensure_ascii=False), language="json")

    st.info(
        "Demo mode: sự kiện consent này chỉ hiển thị trên UI, "
        "chưa ghi vào bất kỳ ledger thật nào."
    )

    st.subheader("3. Thu hồi consent (demo)")
    st.text_input("Nhập lại số CCCD/CMND để thu hồi", value=citizen_id)
    st.button("Thu hồi consent (demo)")


# =========================
# MÀN HÌNH 2 – BANKING DASHBOARD
# =========================

def banking_new_request_body():
    """Form tạo yêu cầu thẩm định – trả về payload gửi API."""

    st.subheader("Tạo yêu cầu thẩm định tín dụng")

    col_id, col_phone = st.columns([3, 1.2])
    with col_id:
        citizen_id = st.text_input("Số CCCD khách hàng", "012345678901")
    with col_phone:
        phone_suffix = st.text_input("4 số cuối điện thoại", "1234")

    col_org, col_purpose = st.columns(2)
    with col_org:
        request_org = st.selectbox(
            "Tổ chức yêu cầu",
            ["Ngân hàng A (demo)", "Ngân hàng B (demo)"],
            index=1,
        )
    with col_purpose:
        ndop_purpose = st.selectbox(
            "Mục đích truy vấn NDOP/CIC",
            ["Chấm điểm tín dụng cá nhân", "Thẩm định mở thẻ tín dụng"],
        )

    col_amount, col_tenor = st.columns(2)
    with col_amount:
        loan_amount = st.number_input(
            "Số tiền vay mong muốn (VND)",
            min_value=10_000_000.0,
            max_value=5_000_000_000.0,
            value=200_000_000.0,
            step=10_000_000.0,
        )
    with col_tenor:
        loan_tenor_months = st.number_input(
            "Thời hạn vay (tháng)",
            min_value=6,
            max_value=120,
            value=36,
            step=6,
        )

    col_product, _ = st.columns([2, 1])
    with col_product:
        loan_product = st.selectbox(
            "Sản phẩm vay",
            ["Vay tiêu dùng", "Vay mua nhà", "Vay mua ô tô"],
        )

    loan_purpose = st.text_area(
        "Mục đích vay",
        "Mua đồ gia dụng, chi tiêu gia đình (mô phỏng)",
    )

    payload = {
        "citizen_id": citizen_id,
        "phone_suffix": phone_suffix,
        "request_org": request_org,
        "ndop_purpose": ndop_purpose,
        "loan_amount": loan_amount,
        "loan_product": loan_product,
        "loan_tenor_months": int(loan_tenor_months),
        "loan_purpose": loan_purpose,
    }

    return payload


def banking_fallback_body():
    st.subheader("Fallback (No-consent)")
    st.caption("Từ chối tạm thời, chuyển sang kênh fallback an toàn với PDPL 2025")

    st.info(
        "Trường hợp khách hàng KHÔNG cấp consent, hệ thống sẽ không truy xuất CIC/NDOP.\n\n"
        "- Có thể dùng mô hình sandbox, rule-based hoặc yêu cầu hồ sơ bổ sung.\n"
        "- Màn hình này chỉ demo UI, chưa gọi API thật."
    )


def view_banking():
    render_main_header()
    st.header("Banking Dashboard – Thẩm định PB-025")

    tab_new, tab_fallback = st.tabs(["Yêu cầu mới", "Fallback (No-consent)"])

    # ---------- TAB YÊU CẦU MỚI ----------
    with tab_new:
        col_left, col_right = st.columns([1.4, 1])

        with col_left:
            payload = banking_new_request_body()

            st.markdown("### Trạng thái consent & phạm vi dữ liệu")
            with st.container():
                st.success(
                    "Consent: **ĐÃ XÁC THỰC (giả lập) qua Cổng công dân / VNeID (mock)**\n\n"
                    "- Consent-ID: CONS-20251118-00912 • Hiệu lực đến ngày 18/11/2026\n"
                    "- Phạm vi (mock): CIC 5 năm • Điện lực 12 tháng • Viễn thông 6 tháng\n"
                    "- Dùng cho chấm điểm demo"
                )

            st.markdown("### Payload gửi sang API (debug)")
            st.code(
                json.dumps(payload, indent=4, ensure_ascii=False),
                language="json",
            )

            if st.button("GỬI YÊU CẦU THẨM ĐỊNH (DEMO)", key="btn_banking_apply"):
                result, err = api_post("/score/apply", payload)
                if err:
                    st.error(f"Lỗi gọi API /score/apply: {err}")
                else:
                    st.success("Gọi API /score/apply thành công")
                    st.code(json.dumps(result, indent=4, ensure_ascii=False), language="json")

        with col_right:
            st.markdown("### Khuyến nghị (Policy Engine – mô phỏng)")
            st.success("PHÊ DUYỆT có điều kiện • Giảm hạn mức 10% • Yêu cầu sao kê lương 6 tháng")

            st.markdown("### Các yếu tố ảnh hưởng (Top 5 – SHAP, synthetic)")
            st.markdown(
                """
                - Tỷ lệ sử dụng tín dụng hơi cao  
                - Không có nợ xấu 12 tháng (tích cực)  
                - Lịch sử tín dụng > 36 tháng  
                - Số tài khoản đang vay nhỏ hơn mức đồng đẳng  
                - DTI ở mức chấp nhận được  
                """
            )

            st.markdown("### Độ ổn định mô hình & nguồn dữ liệu (synthetic)")
            st.markdown(
                """
                - Model: LGBM_v3.1 • AUC (train synthetic): ~0.93  
                - PSI (shadow test): 0.06 • ECE (calibration): 0.01  
                - Không dùng dữ liệu CIC/NDOP thật  
                """
            )

            st.markdown("### Thông tin kiểm toán (Audit & Trace – demo)")
            st.markdown(
                """
                - Audit-ID: A-20251118-00012  
                - Model: LGBM_v3.1  
                - Policy: PB-025_POLICY_V1  
                - Dataset: LC_SYNTHETIC_2025  
                - Trace: NCE_PIPELINE_SAMPLE#112992  
                """
            )

    # ---------- TAB FALLBACK ----------
    with tab_fallback:
        banking_fallback_body()


# =========================
# MÀN HÌNH 3 – NHÀ NƯỚC GIÁM SÁT
# =========================

def view_regulator():
    """Màn hình dành cho Nhà nước giám sát (demo)."""

    # PHẦN HEADER (giữ nguyên style hiện tại)
    st.subheader("Nhà nước giám sát")
    st.caption(
        "Màn hình giám sát, thanh tra & báo cáo tuân thủ (demo)"
    )

    # THÔNG ĐIỆP DEMO NHƯ CŨ
    st.info(
        "Demo: hiển thị số lượng yêu cầu thẩm định, "
        "tỷ lệ phê duyệt / từ chối, log truy cập, và các cảnh báo drift mô hình."
    )

    # ====== KHỐI 1: TỔNG QUAN YÊU CẦU THẨM ĐỊNH (DEMO) ======
    st.markdown("### Tổng quan yêu cầu thẩm định (demo)")

    col1, col2, col3 = st.columns(3)
    col1.metric("Tổng số yêu cầu", "1 250", "▲ 12%")
    col2.metric("Tỷ lệ phê duyệt", "72%", "▲ 5%")
    col3.metric("Tỷ lệ từ chối", "18%", "▼ 3%")

    # ====== KHỐI 2: HIỆU NĂNG MÔ HÌNH & ỔN ĐỊNH DỮ LIỆU ======
    st.markdown("### Hiệu năng mô hình & ổn định dữ liệu (demo)")

    col4, col5, col6 = st.columns(3)
    col4.metric("AUC (train)", "0.93")
    col5.metric("PSI (shadow test)", "0.06")
    col6.metric("ECE (calibration)", "0.01")

    st.caption(
        "Các chỉ số trên là synthetic, minh họa mô hình PB-025 đã được "
        "kiểm tra hiệu năng và drift theo chuẩn ngân hàng."
    )

    # ====== KHỐI 3: BIỂU ĐỒ TỶ LỆ PHÊ DUYỆT & DRIFT (DEMO) ======
    st.markdown("### Tỷ lệ phê duyệt & drift dữ liệu theo thời gian (demo)")

    # Tạo dữ liệu giả lập ổn định (không random mỗi lần để đỡ nhấp nháy)
    months = pd.date_range("2025-01-01", periods=12, freq="M")
    approval_rate = np.array([0.70, 0.71, 0.69, 0.72, 0.73, 0.71,
                              0.74, 0.75, 0.73, 0.72, 0.71, 0.72])
    psi_values = np.array([0.02, 0.03, 0.02, 0.04, 0.05, 0.04,
                           0.06, 0.07, 0.06, 0.05, 0.04, 0.05])

    df_reg = pd.DataFrame(
        {
            "month": months,
            "approval_rate": approval_rate * 100,  # %
            "psi": psi_values,
        }
    ).set_index("month")

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("**Tỷ lệ phê duyệt theo tháng (%)**")
        st.line_chart(df_reg[["approval_rate"]])

    with col_right:
        st.markdown("**Chỉ số drift PSI theo tháng**")
        st.line_chart(df_reg[["psi"]])

    st.caption(
        "- Approval rate: tỷ lệ hồ sơ được phê duyệt mỗi tháng.\n"
        "- PSI: Population Stability Index, dùng để giám sát drift phân phối dữ liệu."
    )



# =========================
# MÀN HÌNH 4 – AUDIT LOG VIEWER
# =========================

def view_logs():
    """Màn hình Audit Log Viewer – đọc log từ file JSONL do API ghi ra."""

    st.subheader("PB-025 — Audit Log Viewer")
    st.caption(
        "Xem lại mọi hành động chấm điểm, policy, consent "
        "• Immutable • Không thể sửa / xóa (demo)."
    )

    st.info(
        "Demo mode: phần này chỉ hiển thị dữ liệu synthetic được ghi bởi API "
        "`/score/apply`, chưa nối với audit ledger thật."
    )

    log_path = Path(__file__).parent / "data" / "audit_log.jsonl"

    if not log_path.exists():
        st.warning(
            "Chưa có bản ghi nào. Hãy vào **Banking Dashboard** và gửi "
            "ít nhất 1 yêu cầu thẩm định để tạo audit log."
        )
        return

    records = []
    with log_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except Exception:
                # Nếu có dòng lỗi format thì bỏ qua, tránh crash demo
                continue

    if not records:
        st.warning("File audit_log.jsonl trống hoặc không đọc được.")
        return

    df = pd.DataFrame(records)

    # Sắp xếp theo thời gian mới nhất
    if "timestamp" in df.columns:
        df = df.sort_values("timestamp", ascending=False)

    st.markdown("### Danh sách audit log gần nhất")

    st.dataframe(
        df.head(20),
        use_container_width=True,
        height=400,
    )

    # Hiển thị chi tiết 1 bản ghi (dòng mới nhất)
    st.markdown("### Chi tiết bản ghi mới nhất")
    latest = df.iloc[0].to_dict()
    st.json(latest, expanded=True)



# =========================
# MAIN
# =========================

def main():
    load_custom_css()

    # Sidebar: chỉ 1 cụm radio, không lặp
    st.sidebar.title("PB-025 Demo UI")
    choice = st.sidebar.radio(
        "Chọn màn hình",
        ["Công dân (DSAP)", "Banking Dashboard", "Nhà nước giám sát", "Audit Log Viewer"],
    )

    if choice == "Công dân (DSAP)":
        view_citizen()
    elif choice == "Banking Dashboard":
        view_banking()
    elif choice == "Nhà nước giám sát":
        view_regulator()
    elif choice == "Audit Log Viewer":
        view_logs()


if __name__ == "__main__":
    main()
