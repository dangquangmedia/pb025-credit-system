import os
import json
import requests
import streamlit as st

# ================== CONFIG CƠ BẢN ==================

st.set_page_config(
    page_title="PB-025 Credit Demo",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_BASE_URL = os.environ.get("API_BASE_URL", "http://api:8000")


# ================== TIỆN ÍCH CHUNG ==================


def call_api(path: str, payload: dict | None = None):
    """Khung gọi API chung – hiện tại đang trả demo nếu lỗi."""
    url = f"{API_BASE_URL.rstrip('/')}/{path.lstrip('/')}"
    try:
        if payload is None:
            r = requests.get(url, timeout=5)
        else:
            r = requests.post(url, json=payload, timeout=5)
        r.raise_for_status()
        return r.json(), None
    except Exception as e:
        # Demo mode: trả mock data + lỗi để không phá UI
        return None, str(e)


def pill(text: str, tone: str = "green"):
    colors = {
        "green": ("#DCFCE7", "#16A34A"),
        "red": ("#FEE2E2", "#DC2626"),
        "yellow": ("#FEF9C3", "#CA8A04"),
        "blue": ("#DBEAFE", "#2563EB"),
        "gray": ("#E5E7EB", "#4B5563"),
    }
    bg, fg = colors.get(tone, colors["gray"])
    st.markdown(
        f"""
        <span style="
            display:inline-flex;
            align-items:center;
            padding:2px 10px;
            border-radius:999px;
            font-size:11px;
            font-weight:600;
            background:{bg};
            color:{fg};
        ">{text}</span>
        """,
        unsafe_allow_html=True,
    )


def card(title: str, body, subtitle: str | None = None):
    st.markdown(
        """
        <div style="background:white;border-radius:16px;
                    padding:20px;border:1px solid #E5E7EB;
                    box-shadow:0 1px 2px rgba(15,23,42,0.04);">
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div style="font-size:15px;font-weight:600;margin-bottom:6px;">{title}</div>',
        unsafe_allow_html=True,
    )
    if subtitle:
        st.markdown(
            f'<div style="font-size:12px;color:#6B7280;margin-bottom:10px;">{subtitle}</div>',
            unsafe_allow_html=True,
        )
    body()
    st.markdown("</div>", unsafe_allow_html=True)


# ================== LOGIN DEMO ==================


USERS = {
    "citizen01": "citizen",
    "banker01": "banker",
    "super01": "supervisor",
}


def login_view():
    st.markdown(
        "<h2 style='margin-bottom:0.5rem;'>PB-025 Demo Login</h2>",
        unsafe_allow_html=True,
    )
    st.write("Dùng tài khoản demo để vào từng vai trò:")

    cols = st.columns(3)
    with cols[0]:
        st.markdown("**Citizen (DSAP)**")
        st.code("citizen01", language="bash")
    with cols[1]:
        st.markdown("**Banker (Thẩm định)**")
        st.code("banker01", language="bash")
    with cols[2]:
        st.markdown("**Supervisor / Regulator**")
        st.code("super01", language="bash")

    st.markdown("---")

    username = st.text_input("Username", "")
    if st.button("Đăng nhập", type="primary"):
        role = USERS.get(username)
        if role is None:
            st.error("Tài khoản không hợp lệ (dùng citizen01 / banker01 / super01).")
        else:
            st.session_state["username"] = username
            st.session_state["role"] = role
            st.experimental_rerun()


def sidebar_info():
    with st.sidebar:
        st.markdown("### PB-025 Demo Login")
        if "username" in st.session_state:
            st.write(f"Xin chào, **{st.session_state['username']}**")
            role = st.session_state.get("role", "?")
            pill(role, "green")
        st.write("")
        st.caption(f"API_BASE_URL = `{API_BASE_URL}`")

        if "username" in st.session_state:
            if st.button("Đăng xuất"):
                st.session_state.clear()
                st.experimental_rerun()


# ================== CITIZEN PORTAL ==================


def view_citizen_portal():
    """Gộp 2 hình: Cổng Công Dân (Consent DSAP) + Cổng Quyền Dữ Liệu & Điểm Tín Dụng."""
    sidebar_info()

    st.markdown(
        """
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:18px;">
          <div style="width:44px;height:44px;border-radius:999px;
                      background:#2563EB;color:white;display:flex;
                      align-items:center;justify-content:center;
                      font-weight:600;font-size:18px;">
            PB
          </div>
          <div>
            <div style="font-size:20px;font-weight:600;">PB-025 — Cổng Công Dân (DSAP)</div>
            <div style="font-size:12px;color:#6B7280;">
              Cấp quyền truy xuất dữ liệu tín dụng • Cổng quyền dữ liệu &amp; điểm tín dụng • Tuân thủ Luật 91/2025
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab1, tab2 = st.tabs(["1. Cấp quyền (Consent)", "2. Tra cứu điểm & Khiếu nại"])

    # ------ TAB 1: CONSENT DSAP ------
    with tab1:
        col_left, col_right = st.columns([1.3, 1])

        with col_left:
            def body_left():
                cccd = st.text_input("Số CCCD/CMND", "012345678901")
                bank = st.selectbox("Tổ chức yêu cầu", ["Ngân hàng A (Demo)", "Ngân hàng B (Demo)", "Ngân hàng C (Demo)"])
                purpose = st.text_input(
                    "Mục đích xử lý", "Đánh giá khả năng cấp tín dụng cá nhân"
                )

                st.write("**Phạm vi dữ liệu**")
                colc1, colc2 = st.columns(2)
                with colc1:
                    scope_cic = st.checkbox("Dữ liệu CIC", True)
                    scope_util = st.checkbox("Dữ liệu điện / nước / viễn thông", True)
                with colc2:
                    st.checkbox("Dữ liệu thu nhập (demo – chưa bật)", False, disabled=True)

                st.info(
                    "Hệ thống AI chấm điểm tín dụng thuộc nhóm *AI rủi ro cao* (theo dự thảo Luật AI). "
                    "Bạn có quyền thu hồi consent bất kỳ lúc nào.",
                    icon="⚠️",
                )

                if st.button("GỬI YÊU CẦU OTP VNeID"):
                    payload = {
                        "national_id": cccd,
                        "bank_code": bank,
                        "scope_credit": scope_cic,
                        "scope_utility": scope_util,
                    }
                    # Kêu API thật ở đây nếu muốn
                    _data, err = call_api("/api/v1/consent-request-demo", payload)
                    if err:
                        st.warning(
                            "Demo: yêu cầu consent đã được ghi nhận (offline). "
                            f"(API lỗi: {err})"
                        )
                    else:
                        st.success("Yêu cầu consent đã được ghi nhận.")

            card(
                "Cấp quyền truy xuất dữ liệu tín dụng",
                body_left,
                "Xác nhận thông tin & phạm vi dữ liệu bạn cho PB-025 xử lý.",
            )

        with col_right:
            def body_status():
                st.markdown(
                    """
                    **Consent hiện tại**

                    CCCD: ***1234  
                    consent_id: `CON-20251118-00045` • Issuer: Ngân hàng B (demo)
                    """
                )
                pill("Đang hiệu lực", "green")
                st.caption("Hạn hiệu lực: 18/12/2025")

                if st.button("THU HỒI CONSENT", type="secondary"):
                    st.warning("Demo: Thu hồi consent (mock).")

            card("Consent hiện tại", body_status)

            def body_hist():
                st.markdown("##### Lịch sử consent")
                data = [
                    ("18/11/2025 09:21", "Ngân hàng B (Demo)", "Mới", "Đang hiệu lực"),
                    ("10/10/2025 14:02", "Ngân hàng A (Demo)", "Mới", "Đã hết hạn"),
                ]
                st.write("")
                st.markdown(
                    "<div style='font-size:12px;'>",
                    unsafe_allow_html=True,
                )
                st.table(
                    {
                        "Thời gian": [d[0] for d in data],
                        "Ngân hàng": [d[1] for d in data],
                        "Loại": [d[2] for d in data],
                        "Trạng thái": [d[3] for d in data],
                    }
                )
                st.markdown("</div>", unsafe_allow_html=True)

            card("Lịch sử consent", body_hist)

    # ------ TAB 2: CỔNG QUYỀN DỮ LIỆU & ĐIỂM TÍN DỤNG ------
    with tab2:
        col_top_left, col_top_right = st.columns(2)

        with col_top_left:
            def body_query():
                colq1, colq2 = st.columns(2)
                with colq1:
                    q_cccd = st.text_input("Số CCCD", "012345678901")
                with colq2:
                    q_phone = st.text_input("4 số cuối điện thoại", "1234")
                if st.button("TRA CỨU"):
                    payload = {"national_id": q_cccd, "phone_last4": q_phone}
                    _data, err = call_api("/api/v1/score-lookup-demo", payload)
                    if err:
                        st.info(
                            "Demo: dữ liệu tra cứu được hiển thị ở panel bên cạnh. "
                            f"(API lỗi: {err})"
                        )

            card("Cổng Quyền Dữ Liệu & Điểm Tín Dụng", body_query)

        with col_top_right:
            def body_score():
                st.markdown("##### Kết quả điểm tín dụng (demo)")
                colk1, colk2 = st.columns([1, 1.5])
                with colk1:
                    st.caption("Điểm tín dụng")
                    st.markdown("<div style='font-size:32px;font-weight:600;'>621</div>",
                                unsafe_allow_html=True)
                with colk2:
                    pill("Hạng 03 – Tốt", "yellow")
                st.write("")
                st.caption("Những yếu tố chính")
                st.markdown(
                    """
                    - Không có nợ xấu 12 tháng  
                    - Tỷ lệ sử dụng tín dụng hơi cao  
                    - Lịch sử tín dụng dài &gt; 3 năm
                    """,
                    unsafe_allow_html=True,
                )

            card("Kết quả điểm tín dụng", body_score)

        st.write("")
        # Khiếu nại
        def body_complaint():
            colc1, colc2, colc3 = st.columns([1, 2, 1])
            with colc1:
                complaint_type = st.selectbox(
                    "Loại khiếu nại",
                    ["CIC sai thông tin", "Điểm tín dụng không hợp lý", "Khác"],
                )
            with colc2:
                detail = st.text_area(
                    "Mô tả chi tiết",
                    "Khoản vay 50 triệu tại Ngân hàng X đã tất toán nhưng vẫn hiển thị đang nợ...",
                )
            with colc3:
                st.write("File đính kèm")
                st.file_uploader("Upload PDF/JPG", type=["pdf", "jpg", "jpeg"], label_visibility="collapsed")

            if st.button("GỬI KHIẾU NẠI"):
                payload = {"type": complaint_type, "detail": detail}
                _data, err = call_api("/api/v1/complaint-demo", payload)
                if err:
                    st.success(
                        "Khiếu nại đã được ghi nhận — TKT-20251118-00392 (Xử lý ≤ 72 giờ) – demo."
                    )
                else:
                    st.success("Khiếu nại đã được ghi nhận (demo).")

        card("Gửi khiếu nại kết quả", body_complaint)

    st.caption(
        "Demo mode • Không dùng dữ liệu thật • Tuân thủ Luật Dữ Liệu Cá Nhân 91/2025/QH15",
    )


# ================== BANKER PORTAL ==================


def view_banker_portal():
    sidebar_info()

    st.markdown(
        """
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:18px;">
          <div style="width:44px;height:44px;border-radius:999px;
                      background:#0EA5E9;color:white;display:flex;
                      align-items:center;justify-content:center;
                      font-weight:600;font-size:18px;">
            PB
          </div>
          <div>
            <div style="font-size:20px;font-weight:600;">Banking Dashboard – Thẩm định PB-025</div>
            <div style="font-size:12px;color:#6B7280;">
              Kết nối NDOP (mô phỏng) • CIC (mô phỏng) • AI Scoring • Human Oversight • Audit Trail
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_main, tab_fallback = st.tabs(["Thẩm định PB-025", "Fallback Mode / No-Consent"])

    # ---- TAB CHÍNH ----
    with tab_main:
        col_left, col_right = st.columns([1.1, 1])

        with col_left:
            def body_form():
                loan_product = st.selectbox(
                    "Sản phẩm vay",
                    ["Vay tiêu dùng", "Vay mua nhà", "Vay mua ô tô"],
                    index=0,
                )
                col_row1 = st.columns(2)
                with col_row1[0]:
                    loan_amount = st.number_input(
                        "Số tiền vay mong muốn (VND)", 0, step=1_000_000, value=200_000_000
                    )
                with col_row1[1]:
                    tenure = st.number_input("Thời hạn vay (tháng)", 1, 120, 36)

                col_row2 = st.columns(2)
                with col_row2[0]:
                    income = st.number_input(
                        "Thu nhập bình quân năm (VND)", 0, step=1_000_000, value=200_000_000
                    )
                with col_row2[1]:
                    dti = st.number_input("Debt-To-Income (DTI) %", 0.0, 200.0, 40.0, 0.1)

                col_row3 = st.columns(2)
                with col_row3[0]:
                    grade = st.selectbox(
                        "Điểm CIC hiện tại (mock)", ["A", "B", "C", "D", "E"], index=0
                    )
                with col_row3[1]:
                    home = st.selectbox("Hình thức nhà ở", ["OWN", "RENT"], index=0)

                purpose = st.selectbox(
                    "Mục đích vay",
                    ["debt_consolidation", "home_improvement", "education", "other"],
                    index=0,
                )

                if st.button("GỬI YÊU CẦU THẨM ĐỊNH"):
                    payload = {
                        "loan_product": loan_product,
                        "loan_amount": loan_amount,
                        "tenor_months": tenure,
                        "annual_income": income,
                        "dti": dti,
                        "cic_grade": grade,
                        "home_ownership": home,
                        "purpose": purpose,
                    }
                    # gọi API thật nếu muốn – hiện demo dùng giá trị cố định
                    _data, err = call_api("/api/v1/score-demo", payload)
                    if err:
                        st.session_state["demo_score"] = {
                            "pd_12m": 0.28,
                            "score": 621,
                            "band": "Hạng 03 – Tốt",
                            "decision": "PHÊ DUYỆT có điều kiện (demo)",
                        }
                        st.info(
                            "Demo: Đã nhận kết quả từ AI Scoring (mock). "
                            f"(API lỗi: {err})"
                        )
                    else:
                        # bạn map _data -> demo_score theo schema thật ở đây
                        st.session_state["demo_score"] = {
                            "pd_12m": _data.get("pd_12m", 0.28),
                            "score": _data.get("score", 621),
                            "band": _data.get("band", "Hạng 03 – Tốt"),
                            "decision": _data.get("decision", "PHÊ DUYỆT (demo)"),
                        }
                        st.success("Đã nhận kết quả từ AI Scoring (demo).")

            card(
                "Tạo yêu cầu thẩm định tín dụng",
                body_form,
                "Form demo gửi hồ sơ vay cho AI Scoring.",
            )

        with col_right:
            def body_result():
                data = st.session_state.get(
                    "demo_score",
                    {
                        "pd_12m": 0.28,
                        "score": 621,
                        "band": "Hạng 03 – Tốt",
                        "decision": "PHÊ DUYỆT có điều kiện (demo)",
                    },
                )
                st.markdown("##### Kết quả chấm điểm tín dụng (AI + OPA – demo)")
                colr1, colr2, colr3 = st.columns(3)
                with colr1:
                    st.caption("PD (vỡ nợ 12 tháng – demo)")
                    st.markdown(
                        f"<div style='font-size:28px;font-weight:600;'>{data['pd_12m']*100:.1f}%</div>",
                        unsafe_allow_html=True,
                    )
                with colr2:
                    st.caption("Điểm tín dụng (CIC-scale – demo)")
                    st.markdown(
                        f"<div style='font-size:28px;font-weight:600;'>{data['score']}</div>",
                        unsafe_allow_html=True,
                    )
                with colr3:
                    st.caption("Phân hạng rủi ro")
                    pill(data["band"], "yellow")

                st.write("")
                st.caption("Khuyến nghị (Policy Engine – mô phỏng):")
                st.markdown(
                    "- Đề xuất: **PHÊ DUYỆT có điều kiện** • Giảm hạn mức 10% • Yêu cầu sao kê lương 6 tháng.",
                    unsafe_allow_html=True,
                )

                st.write("")
                st.caption("Các yếu tố ảnh hưởng (Top 5 – SHAP, synthetic):")
                st.markdown(
                    """
                    - Tỷ lệ sử dụng tín dụng hơi cao  
                    - Không có nợ xấu 12 tháng (tích cực)  
                    - Lịch sử tín dụng &gt; 36 tháng  
                    - DTI ở mức chấp nhận được  
                    - Thói quen thanh toán đúng hạn
                    """,
                    unsafe_allow_html=True,
                )

            card("Kết quả thẩm định", body_result)

    # ---- TAB FALLBACK ----
    with tab_fallback:
        col_f1, col_f2 = st.columns([1.1, 1])

        with col_f1:
            def body_summary():
                st.markdown("##### Tóm tắt yêu cầu (demo)")
                st.text_input("Số CCCD khách hàng", "012345678901")
                st.text_input("Số tiền vay", "120.000.000")
                st.selectbox("Sản phẩm vay", ["Vay tiêu dùng"])
                st.text_input("Mục đích vay", "Mua đồ gia dụng, chi tiêu gia đình…")

                st.write("")
                st.caption("Trạng thái consent")
                pill("Không có consent hợp lệ", "red")
                st.caption("Consent-ID: — Lý do: Chưa cấp / Hết hạn / Đã thu hồi")

                st.info(
                    "Hướng dẫn: Yêu cầu khách hàng cấp/khôi phục consent trên Cổng DSAP "
                    "hoặc đánh giá sơ bộ hồ sơ bằng mô hình fallback (phi-PII).",
                    icon="ℹ️",
                )

            card(
                "Banking Dashboard — Fallback Mode (No-Consent)",
                body_summary,
                "Không gọi NDOP/CIC • Không xử lý PII • Mô hình Fallback phi-PII.",
            )

        with col_f2:
            def body_fb_result():
                st.markdown("##### Kết quả Fallback Model (phi-PII)")
                colx1, colx2 = st.columns(2)
                with colx1:
                    st.caption("Fallback Risk Level")
                    pill("MEDIUM", "yellow")
                with colx2:
                    st.caption("Confidence")
                    st.markdown(
                        "<div style='font-size:20px;font-weight:600;'>≈ 60%</div>",
                        unsafe_allow_html=True,
                    )

                st.write("")
                st.caption("Các yếu tố phi-PII được sử dụng:")
                st.markdown(
                    """
                    - Lịch sử quan hệ tín dụng (ẩn danh hoá)  
                    - Hành vi giao dịch tài chính phi-PII (tổng hợp)  
                    - Mẫu hành vi chi tiêu (không truy vết cá nhân)  
                    - Điểm rủi ro nhóm (cluster risk)
                    """,
                    unsafe_allow_html=True,
                )

                st.write("")
                st.caption("Ghi chú tuân thủ:")
                st.markdown(
                    """
                    - Không truy xuất NDOP/CIC khi thiếu consent  
                    - Không xử lý, không lưu PII  
                    - Mọi hành vi được ghi vào Audit Ledger (immutable)
                    """,
                    unsafe_allow_html=True,
                )

                st.write("")
                st.caption("Hành động của thẩm định viên:")
                colb1, colb2, colb3 = st.columns(3)
                with colb1:
                    st.button("YÊU CẦU BỔ SUNG")
                with colb2:
                    st.button("TIẾP NHẬN SƠ BỘ")
                with colb3:
                    st.button("TỪ CHỐI TẠM THỜI")

            card("Kết quả Fallback (phi-PII)", body_fb_result)


# ================== SUPERVISOR / GOVERNANCE PORTAL ==================


def view_supervisor_portal():
    sidebar_info()

    st.markdown(
        """
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:18px;">
          <div style="width:44px;height:44px;border-radius:999px;
                      background:#4F46E5;color:white;display:flex;
                      align-items:center;justify-content:center;
                      font-weight:600;font-size:18px;">
            MG
          </div>
          <div>
            <div style="font-size:20px;font-weight:600;">PB-025 — Monitoring &amp; AI Governance Dashboard</div>
            <div style="font-size:12px;color:#6B7280;">
              Demo giám sát hệ thống • AI drift • Consent • NDOP/CIC API (mock) • OPA Policy • Audit Logs
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_mon, tab_audit = st.tabs(["Monitoring & Governance", "Audit Log Viewer"])

    with tab_mon:
        # hàng KPI
        c1, c2, c3, c4 = st.columns(4)

        def kpi(label, value, sub=None):
            with st.container():
                card(
                    "",
                    lambda: (
                        st.caption(label),
                        st.markdown(
                            f"<div style='font-size:22px;font-weight:600;'>{value}</div>",
                            unsafe_allow_html=True,
                        ),
                        (sub and st.caption(sub)) or None,
                    ),
                )

        with c1:
            kpi("Tổng số yêu cầu hôm nay (demo)", "1,284", "Scoring + consent + policy check")
        with c2:
            kpi("Latency trung bình (demo)", "732 ms", "NDOP/CIC → AI → OPA")
        with c3:
            kpi("Consent hợp lệ / tổng (mô phỏng)", "98.4%", "Yêu cầu có consent ACTIVE")
        with c4:
            kpi("NDOP/CIC API Health (mock)", "OK", "Error rate thấp • Không timeout")

        st.write("")
        c_mid1, c_mid2 = st.columns([2, 1])

        with c_mid1:
            def body_drift():
                st.caption(
                    "AI Drift Monitoring & Model Lifecycle (synthetic) • Theo dõi PSI / KS / ECE cho mô hình LGBM_v1.0.0."
                )
                st.write("")
                colm = st.columns(3)
                with colm[0]:
                    pill("PSI (demo): 0.06", "green")
                with colm[1]:
                    pill("ECE (demo): 0.01", "green")
                with colm[2]:
                    pill("KS (demo): 0.23", "green")

                st.write("")
                st.markdown(
                    """
                    - Model: **LGBM_v1.0.0** (train trên dữ liệu synthetic)  
                    - Train (mock): 12/10/2025 • Calibration (mock): 13/10/2025  
                    - Ngưỡng drift (demo): PSI ≤ 0.10 • ECE ≤ 0.02  
                    - Lần retrain dự kiến (demo): Q1/2026
                    """
                )
                st.info(
                    "Biểu đồ drift theo thời gian (PSI / ECE / KS từng tháng) sẽ được gắn từ hệ thống monitoring thật (Prometheus/Grafana, CloudWatch...).",
                    icon="📈",
                )

            card("AI Drift Monitoring & Model Lifecycle (synthetic)", body_drift)

        with c_mid2:
            def body_ndop():
                st.caption("NDOP/CIC API Health & Traffic (mô phỏng)")
                pill("NDOP: OK (mock)", "green")
                pill("CIC: OK (mock)", "green")
                st.write("")
                st.markdown(
                    """
                    - Throughput (synthetic): **48 req/s**  
                    - Error rate (demo): **0.12%**  
                    - Timeouts (mock): **3**  
                    - Retry (demo): **0.9%**  
                    - Circuit breaker: **Chưa kích hoạt**
                    """
                )

            card("NDOP/CIC API Health & Traffic", body_ndop)

        st.write("")
        c_bot1, c_bot2 = st.columns([2, 1])

        with c_bot1:
            def body_audit_list():
                st.caption("Audit Log (10 bản ghi mới nhất – demo)")
                data = [
                    ("18/11/25 09:21", "Ngân hàng B (demo)", "Scoring", "A-20251118-00012"),
                    ("18/11/25 09:20", "Ngân hàng A (demo)", "Consent check", "A-20251118-00011"),
                    ("18/11/25 09:18", "Ngân hàng C (demo)", "Policy deny", "A-20251118-00010"),
                ]
                st.table(
                    {
                        "Thời gian": [d[0] for d in data],
                        "Tổ chức": [d[1] for d in data],
                        "Loại": [d[2] for d in data],
                        "Mã Audit (mock)": [d[3] for d in data],
                    }
                )
                st.button("Xem toàn bộ Audit Log (demo)")

            card("Audit Log (10 bản ghi mới nhất – demo)", body_audit_list)

        with c_bot2:
            def body_policy():
                st.caption("OPA Policy Governance (demo)")
                st.markdown(
                    """
                    - Quyết định OPA hôm nay (mô phỏng): **1,284**  
                    - Allow (demo): **1,213** • Deny (demo): **71**  

                    **Top rules kích hoạt (mock):**
                    - `CREDIT_AGE_RULE`: 32 lần (demo)  
                    - `MAX_DTI_POLICY`: 28 lần (demo)  
                    - `FALLBACK_MODE_POLICY`: 7 lần (demo)
                    """
                )

            card("OPA Policy Governance", body_policy)

            def body_revoke():
                st.caption("Consent Revoke Monitor (mô phỏng)")
                st.markdown(
                    """
                    - Thu hồi hôm nay (demo): **14**  
                    - 7 ngày gần nhất (demo): **132**  
                    - Tỷ lệ revoke trên tổng (demo): **1.3%**  
                    - Alert: **OFF (mock)**
                    """
                )
                st.button("Bật cảnh báo khi tỷ lệ revoke tăng cao (demo)")

            card("Consent Revoke Monitor", body_revoke)

    # ---- TAB AUDIT VIEWER ----
    with tab_audit:
        st.markdown(
            "<h4>PB-025 — Audit Log Viewer (Demo)</h4>",
            unsafe_allow_html=True,
        )
        col_a1, col_a2 = st.columns([1.2, 1])

        with col_a1:
            def body_summary():
                st.caption("Thông tin tóm tắt (demo)")
                st.markdown(
                    """
                    - Thời gian (mock): **18/11/2025 09:21:34**  
                    - Ngân hàng: **Ngân hàng B (Demo)**  
                    - Loại yêu cầu: **Thẩm định tín dụng (mô phỏng)**  
                    - Kết quả AI (demo): **PD: 28.0% • Score: 621**  
                    - Phân hạng rủi ro: **Risk Tier: Medium (demo)**
                    """
                )

            card("Thông tin tóm tắt", body_summary)

            def body_shap():
                st.caption("Explainability Snapshot (SHAP – demo)")
                st.markdown(
                    """
                    1. `credit_utilization` (+12.3% PD)  
                    2. `no_bad_debt_12m` (−8.2% PD)  
                    3. `history_length` (−5.1% PD)  
                    4. `open_accounts` (+3.4% PD)
                    """
                )
                st.caption("Latency Breakdown (demo)")
                st.markdown(
                    """
                    - NDOP (demo): **210 ms**  
                    - CIC (demo): **188 ms**  
                    - Feature prepare (demo): **52 ms**  
                    - Model infer (demo): **18 ms**  
                    - OPA: **6 ms**  
                    - **Tổng**: ~732 ms
                    """
                )

            card("Explainability Snapshot & Latency", body_shap)

        with col_a2:
            def body_ledger():
                st.caption("Ledger & Merkle Proof (demo)")
                st.markdown(
                    """
                    - `ledger_block` (synthetic): **128833 (demo)**  
                    - `merkle_root` (mock): `0xab9c...ff31`  
                    - `consistency_proof`: **OK (verifiable demo)**  
                    - `signed_by`: **PB025_Authority (demo)**
                    """
                )
                st.button("Xem Merkle Proof (Mock Data)")

            card("Ledger & Merkle Proof", body_ledger)

            def body_json():
                st.caption("Chi tiết Audit Log (dạng JSON – mock)")
                audit_json = {
                    "audit_id": "A-20251118-00012",
                    "timestamp": "2025-11-18T09:21:34Z",
                    "actor": {"type": "bank_client", "org": "Bank_B_demo"},
                    "consent": {
                        "consent_id": "CON-20251118-00045",
                        "status": "valid_demo",
                    },
                    "decision": {
                        "ai_pd": 0.28,
                        "ai_score": 621,
                        "opa_outcome": "MANUAL_REVIEW",
                    },
                    "pii": "<never_processed_in_log>",
                }
                st.code(json.dumps(audit_json, indent=2, ensure_ascii=False), language="json")

            card("Chi tiết Audit Log (JSON)", body_json)


# ================== MAIN ==================


def main():
    if "role" not in st.session_state:
        login_view()
        return

    role = st.session_state["role"]

    if role == "citizen":
        view_citizen_portal()
    elif role == "banker":
        view_banker_portal()
    else:
        view_supervisor_portal()


if __name__ == "__main__":
    main()
