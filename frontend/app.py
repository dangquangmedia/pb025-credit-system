import os
import json
import requests
import streamlit as st
import math

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



# ================== BANKER SCORING POLICY (V1) ==================

POLICY_VERSION = "PB025_BANK_V1.0"

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def money_fmt(vnd: float) -> str:
    try:
        return f"{int(vnd):,}".replace(",", ".")
    except:
        return str(vnd)

def dti_calc_simple(annual_income: float, loan_amount: float, tenure_months: int) -> float:
    """
    Demo DTI: xấp xỉ tỷ lệ trả nợ/tháng trên thu nhập/tháng.
    Giả sử trả đều gốc, bỏ qua lãi (đủ cho demo).
    """
    if annual_income <= 0 or tenure_months <= 0:
        return 0.0
    monthly_income = annual_income / 12.0
    monthly_payment = loan_amount / tenure_months
    dti = (monthly_payment / monthly_income) * 100.0
    return clamp(dti, 0.0, 200.0)

def score_cic_grade(grade: str) -> int:
    mapping = {"A": 120, "B": 80, "C": 40, "D": 0, "E": -80}
    return mapping.get(grade, 0)

def score_dti(dti: float) -> int:
    if dti < 30: return 120
    if 30 <= dti < 40: return 60
    if 40 <= dti < 50: return 0
    if 50 <= dti < 60: return -60
    return -120

def score_income(annual_income: float) -> int:
    # annual_income VND
    if annual_income > 500_000_000: return 80
    if 300_000_000 <= annual_income <= 500_000_000: return 50
    if 150_000_000 <= annual_income < 300_000_000: return 20
    return -40

def score_loan_vs_income(annual_income: float, loan_amount: float) -> int:
    if annual_income <= 0:
        return -80
    ratio = loan_amount / annual_income
    if ratio <= 2: return 40
    if 2 < ratio <= 3: return 10
    if 3 < ratio <= 5: return -30
    return -80

def score_home(home: str) -> int:
    mapping = {"OWN": 50, "MORTGAGE": 20, "RENT": -20}
    return mapping.get(home, 0)

def score_tenure(months: int) -> int:
    if 12 <= months <= 36: return 30
    if 36 < months <= 60: return 10
    if months > 60: return -20
    return 0

def score_purpose(purpose: str) -> int:
    mapping = {
        "personal": 20,
        "debt_consolidation": 10,
        "business": 0,
        "speculative": -40,
        "other": 0,
    }
    return mapping.get(purpose, 0)

def score_risk_flags(flags_count: int) -> int:
    if flags_count <= 0: return 20
    if flags_count == 1: return -10
    return -40

def score_to_grade(score: int):
    # 300–850
    if score >= 800: return ("A+", "🟢")
    if score >= 740: return ("A", "🟢")
    if score >= 670: return ("B", "🟡")
    if score >= 580: return ("C", "🟠")
    if score >= 500: return ("D", "🔴")
    return ("E", "🔴")

def score_color(score: int) -> str:
    # CIC-like color mapping
    if score >= 800: return "#16A34A"   # green
    if score >= 740: return "#22C55E"
    if score >= 670: return "#EAB308"   # yellow
    if score >= 580: return "#F97316"   # orange
    if score >= 500: return "#EF4444"   # red
    return "#B91C1C"                    # dark red

def render_score_gauge(score: int):
    score = clamp(score, 300, 850)
    pct = (score - 300) / (850 - 300) * 100.0
    color = score_color(score)

    st.markdown(
        f"""
        <div style="background:white;border-radius:16px;padding:16px;border:1px solid #E5E7EB;">
          <div style="display:flex;justify-content:space-between;align-items:flex-end;">
            <div>
              <div style="font-size:12px;color:#6B7280;">Credit score (CIC-scale)</div>
              <div style="font-size:34px;font-weight:700;line-height:1;">{score}</div>
            </div>
            <div style="font-size:12px;color:#6B7280;text-align:right;">
              <div>Range: 300 – 850</div>
              <div style="margin-top:4px;">
                <span style="display:inline-flex;align-items:center;gap:8px;">
                  <span style="width:10px;height:10px;background:{color};border-radius:999px;display:inline-block;"></span>
                  <span style="font-weight:600;color:#111827;">{score_to_grade(score)[0]}</span>
                </span>
              </div>
            </div>
          </div>

          <div style="margin-top:14px;">
            <div style="position:relative;height:12px;border-radius:999px;overflow:hidden;background:linear-gradient(90deg,#B91C1C,#EF4444,#F97316,#EAB308,#22C55E,#16A34A);">
              <div style="position:absolute;left:{pct}%;top:-6px;transform:translateX(-50%);">
                <div style="width:0;height:0;border-left:7px solid transparent;border-right:7px solid transparent;border-top:10px solid #111827;"></div>
              </div>
            </div>
            <div style="display:flex;justify-content:space-between;font-size:11px;color:#6B7280;margin-top:6px;">
              <span>300</span><span>500</span><span>580</span><span>670</span><span>740</span><span>850</span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

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

def breakdown_table(rows):
    """
    rows: list of dict {
      key, label, weight, value, points, note
    }
    """
    st.markdown(
        """
        <div style="background:white;border-radius:16px;padding:16px;border:1px solid #E5E7EB;">
          <div style="font-weight:700;margin-bottom:6px;">Breakdown (8 tiêu chí)</div>
          <div style="font-size:12px;color:#6B7280;margin-bottom:12px;">
            Policy: <b>PB025_BANK_V1.0</b> • Điểm cộng/trừ hiển thị theo từng tiêu chí để tránh “đổi trọng số mà score không đổi”.
          </div>
        """,
        unsafe_allow_html=True,
    )

    # header
    st.markdown(
        """
        <div style="display:grid;grid-template-columns: 2.4fr 0.8fr 1.0fr 0.9fr;gap:10px;
                    padding:10px 10px;border-radius:12px;background:#F9FAFB;border:1px solid #EEF2F7;
                    font-size:12px;color:#374151;font-weight:700;">
          <div>Tiêu chí</div><div>Trọng số</div><div>Giá trị</div><div>Điểm (+/-)</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for r in rows:
        pts = r["points"]
        pts_color = "#16A34A" if pts > 0 else ("#DC2626" if pts < 0 else "#6B7280")
        st.markdown(
            f"""
            <div style="display:grid;grid-template-columns: 2.4fr 0.8fr 1.0fr 0.9fr;gap:10px;
                        padding:10px 10px;border-bottom:1px solid #F1F5F9;font-size:12px;align-items:center;">
              <div>
                <div style="font-weight:600;color:#111827;">{r["label"]}</div>
                <div style="color:#6B7280;font-size:11px;">{r.get("note","")}</div>
              </div>
              <div style="color:#111827;font-weight:600;">{r["weight"]}</div>
              <div style="color:#111827;">{r["value"]}</div>
              <div style="font-weight:800;color:{pts_color};">{pts:+d}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

def banker_recommendation(score: int, dti: float, consent_ok: bool = True):
    """
    Demo OPA-like decision
    """
    if not consent_ok:
        return ("FALLBACK_REQUIRED", "Consent không hợp lệ → bật Fallback (phi-PII).", "red")

    if score >= 740 and dti < 45:
        return ("APPROVE", "PHÊ DUYỆT • Điều kiện chuẩn.", "green")
    if score >= 670:
        return ("APPROVE_COND", "PHÊ DUYỆT CÓ ĐIỀU KIỆN • Giảm hạn mức 10% / yêu cầu sao kê 6 tháng.", "yellow")
    if score >= 580:
        return ("MANUAL_REVIEW", "CHUYỂN THẨM ĐỊNH THỦ CÔNG (Human-in-the-loop).", "yellow")
    return ("DENY", "TỪ CHỐI / GIẢM HẠN MỨC (rủi ro cao).", "red")


# ================== BANKER VIEW (UI MỚI) ==================

def view_banker_portal():
    # Header
    st.markdown(
        """
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:18px;">
          <div style="width:44px;height:44px;border-radius:999px;
                      background:#0EA5E9;color:white;display:flex;
                      align-items:center;justify-content:center;
                      font-weight:700;font-size:18px;">
            PB
          </div>
          <div>
            <div style="font-size:22px;font-weight:800;">Banking Dashboard — Thẩm định PB-025</div>
            <div style="font-size:12px;color:#6B7280;">
              NDOP → Consent → Scoring → Audit (demo) • Policy version hiển thị rõ để audit/trace thay đổi trọng số.
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_main, tab_fallback = st.tabs(["Yêu cầu mới", "Fallback Mode (No-Consent)"])

    # ================== TAB MAIN ==================
    with tab_main:
        left, right = st.columns([1.15, 1])

        with left:
            st.markdown(
                """
                <div style="background:white;border-radius:16px;padding:16px;border:1px solid #E5E7EB;">
                  <div style="font-weight:800;font-size:16px;margin-bottom:4px;">Tạo yêu cầu thẩm định tín dụng</div>
                  <div style="font-size:12px;color:#6B7280;margin-bottom:12px;">
                    Bước 1: Nhập thông tin • Bước 2: Tính DTI tự động • Bước 3: Chấm điểm & gợi ý quyết định
                  </div>
                """,
                unsafe_allow_html=True,
            )

            c1, c2 = st.columns(2)
            with c1:
                national_id = st.text_input("Số CCCD khách hàng", "012345678900")
                org = st.selectbox("Tổ chức yêu cầu", ["Ngân hàng B (demo)", "Ngân hàng A (demo)", "Ngân hàng C (demo)"])
                purpose = st.selectbox("Mục đích vay", ["personal", "debt_consolidation", "business", "speculative", "other"], index=1)
                home = st.selectbox("Home Ownership", ["OWN", "MORTGAGE", "RENT"], index=0)
            with c2:
                annual_income = st.number_input("Customer Annual Income (VND)", min_value=0, step=1_000_000, value=200_000_000)
                loan_amount = st.number_input("Requested Loan Amount (VND)", min_value=0, step=1_000_000, value=200_000_000)
                tenure = st.number_input("Loan Tenure (Months)", min_value=1, max_value=120, value=36)
                cic_grade = st.selectbox("Current CIC-like Grade", ["A", "B", "C", "D", "E"], index=0)

            # Risk flags (demo)
            st.write("")
            flags = st.multiselect(
                "Risk flags (demo)",
                ["Recent delinquencies", "Income instability", "Fraud watch", "High utilization cluster"],
                default=[],
            )
            flags_count = len(flags)

            # DTI auto
            dti = dti_calc_simple(annual_income, loan_amount, int(tenure))
            st.write("")
            col_dti1, col_dti2 = st.columns([1, 1])
            with col_dti1:
                st.text_input("Debt-To-Income (DTI) % (auto)", value=f"{dti:.2f}", disabled=True)
            with col_dti2:
                ratio = (loan_amount / annual_income) if annual_income > 0 else 999.0
                st.text_input("Loan / Annual Income (auto)", value=f"{ratio:.2f}x", disabled=True)

            st.write("")
            st.caption(f"Policy version: {POLICY_VERSION}")

            st.markdown("</div>", unsafe_allow_html=True)

        # ================== SCORE + BREAKDOWN ==================
        with right:
            base = 500

            p1 = score_cic_grade(cic_grade)
            p2 = score_dti(dti)
            p3 = score_income(annual_income)
            p4 = score_loan_vs_income(annual_income, loan_amount)
            p5 = score_home(home)
            p6 = score_tenure(int(tenure))
            p7 = score_purpose(purpose)
            p8 = score_risk_flags(flags_count)

            raw_total = base + p1 + p2 + p3 + p4 + p5 + p6 + p7 + p8
            final_score = int(clamp(raw_total, 300, 850))
            grade, emoji = score_to_grade(final_score)

            # Render gauge
            render_score_gauge(final_score)

            # Decision
            st.write("")
            decision, decision_text, tone = banker_recommendation(final_score, dti, consent_ok=True)
            wrap_bg = {"green": "#ECFDF5", "yellow": "#FFFBEB", "red": "#FEF2F2"}.get(tone, "#F3F4F6")
            wrap_border = {"green": "#A7F3D0", "yellow": "#FDE68A", "red": "#FECACA"}.get(tone, "#E5E7EB")

            st.markdown(
                f"""
                <div style="background:{wrap_bg};border:1px solid {wrap_border};border-radius:14px;padding:12px;">
                  <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div style="font-weight:800;">Kết luận (AI + Policy — demo)</div>
                    <div style="font-size:12px;color:#6B7280;">Decision: <b>{decision}</b></div>
                  </div>
                  <div style="margin-top:6px;font-size:13px;">{decision_text}</div>
                  <div style="margin-top:8px;font-size:12px;color:#6B7280;">
                    Risk grade: <b>{grade}</b> {emoji} • DTI: <b>{dti:.2f}%</b>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.write("")

            rows = [
                {"label": "Current CIC-like Grade", "weight": "20%", "value": cic_grade, "points": p1,
                 "note": "A:+120 • B:+80 • C:+40 • D:0 • E:-80"},
                {"label": "Debt-To-Income (DTI %)", "weight": "25%", "value": f"{dti:.2f}%", "points": p2,
                 "note": "<30:+120 • 30–40:+60 • 40–50:0 • 50–60:-60 • >60:-120"},
                {"label": "Annual Income (VND)", "weight": "15%", "value": money_fmt(annual_income), "points": p3,
                 "note": ">500tr:+80 • 300–500:+50 • 150–300:+20 • <150:-40"},
                {"label": "Loan Amount vs Income", "weight": "10%", "value": f"{ratio:.2f}x", "points": p4,
                 "note": "≤2x:+40 • 2–3x:+10 • 3–5x:-30 • >5x:-80"},
                {"label": "Home Ownership", "weight": "10%", "value": home, "points": p5,
                 "note": "OWN:+50 • MORTGAGE:+20 • RENT:-20"},
                {"label": "Loan Tenure (Months)", "weight": "8%", "value": str(int(tenure)), "points": p6,
                 "note": "12–36:+30 • 36–60:+10 • >60:-20"},
                {"label": "Loan Purpose", "weight": "7%", "value": purpose, "points": p7,
                 "note": "personal:+20 • debt_consolidation:+10 • business:0 • speculative:-40"},
                {"label": "Stability / Risk Flags", "weight": "5%", "value": f"{flags_count} flag(s)", "points": p8,
                 "note": "0:+20 • 1:-10 • ≥2:-40"},
            ]

            breakdown_table(rows)

            st.write("")
            with st.expander("Xem công thức tính (demo)"):
                st.code(
                    f"""Base=500
Score = clamp( Base
  + CIC({cic_grade})={p1}
  + DTI({dti:.2f}%)={p2}
  + Income({annual_income})={p3}
  + Loan/Income({ratio:.2f}x)={p4}
  + Home({home})={p5}
  + Tenure({int(tenure)})={p6}
  + Purpose({purpose})={p7}
  + RiskFlags({flags_count})={p8}
, 300..850)
= {final_score}""",
                    language="text",
                )

    # ================== TAB FALLBACK ==================
    with tab_fallback:
        st.markdown(
            """
            <div style="background:white;border-radius:16px;padding:16px;border:1px solid #E5E7EB;">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <div style="font-weight:800;font-size:16px;">Banking Dashboard — Fallback Mode (No-Consent)</div>
                <div style="padding:4px 10px;border-radius:999px;background:#F3F4F6;color:#111827;font-size:12px;font-weight:700;">
                  FALLBACK • ACTIVE
                </div>
              </div>
              <div style="font-size:12px;color:#6B7280;margin-top:6px;">
                Consent không hợp lệ → không gọi NDOP/CIC • chỉ dùng tín hiệu phi-PII để hỗ trợ quyết định thủ công.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.write("")
        l1, r1 = st.columns([1.1, 1])
        with l1:
            st.markdown(
                """
                <div style="background:white;border-radius:16px;padding:16px;border:1px solid #E5E7EB;">
                  <div style="font-weight:800;">Tóm tắt yêu cầu</div>
                  <div style="font-size:12px;color:#6B7280;margin-top:6px;">Hồ sơ minh hoạ — không dùng dữ liệu thật</div>
                """,
                unsafe_allow_html=True,
            )
            st.text_input("Số CCCD khách hàng", "012345678900", disabled=True)
            st.text_input("Số tiền vay", "120.000.000", disabled=True)
            st.text_input("Sản phẩm vay", "Vay tiêu dùng", disabled=True)
            st.text_input("Mục đích vay", "Mua đồ gia dụng, chi tiêu gia đình…", disabled=True)
            st.write("")
            pill("Không có consent hợp lệ", "red")
            st.caption("Consent-ID: —  Lý do: Chưa cấp / Hết hạn / Đã thu hồi")
            st.markdown("</div>", unsafe_allow_html=True)

        with r1:
            st.markdown(
                """
                <div style="background:white;border-radius:16px;padding:16px;border:1px solid #E5E7EB;">
                  <div style="font-weight:800;">Kết quả Fallback (phi-PII)</div>
                  <div style="font-size:12px;color:#6B7280;margin-top:6px;">Không xử lý, không lưu PII • chỉ hỗ trợ thẩm định thủ công</div>
                """,
                unsafe_allow_html=True,
            )
            pill("MEDIUM", "yellow")
            st.caption("Confidence: ~60% (demo)")
            st.write("")
            st.markdown(
                """
                **Tín hiệu phi-PII tổng hợp**
                - Thói quen thanh toán tiện ích đều (gián tiếp)  
                - Biến động chi tiêu 3 tháng gần đây ổn định (ẩn danh)  
                - Không có cảnh báo gian lận từ đối tác viễn thông (ẩn danh)
                """,
                unsafe_allow_html=True,
            )
            st.write("")
            cta1, cta2, cta3 = st.columns(3)
            with cta1: st.button("YÊU CẦU BỔ SUNG")
            with cta2: st.button("TIẾP NHẬN SƠ BỘ")
            with cta3: st.button("TỪ CHỐI TẠM THỜI")
            st.markdown("</div>", unsafe_allow_html=True)


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
