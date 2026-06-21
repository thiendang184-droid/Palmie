import streamlit as st
from PIL import Image
import time
import os
import gdown
from utils.predictor import run_inference
from utils.interpreter import interpret_results

# ─── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Palmie - Bói Chỉ Tay AI",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700;900&family=Be+Vietnam+Pro:ital,wght@0,300;0,400;0,500;0,600;0,700;1,300;1,400&display=swap');

    /* ── Reset & Base ── */
    * { box-sizing: border-box; }

    body, .stApp, [class*="st-"], p, span, div, label, input, button, select, textarea {
        font-family: 'Be Vietnam Pro', sans-serif !important;
    }

    .stApp {
        background: #07071a;
        background-image:
            radial-gradient(ellipse 80% 50% at 20% 10%, rgba(120, 40, 200, 0.18) 0%, transparent 60%),
            radial-gradient(ellipse 60% 40% at 80% 90%, rgba(30, 10, 100, 0.25) 0%, transparent 60%),
            radial-gradient(ellipse 40% 60% at 50% 50%, rgba(180, 80, 255, 0.06) 0%, transparent 70%);
        min-height: 100vh;
    }

    /* ── Starfield (CSS only) ── */
    .stApp::before {
        content: '';
        position: fixed;
        inset: 0;
        background-image:
            radial-gradient(1px 1px at 10% 15%, rgba(255,255,255,0.6) 0%, transparent 100%),
            radial-gradient(1px 1px at 25% 40%, rgba(255,255,255,0.4) 0%, transparent 100%),
            radial-gradient(1.5px 1.5px at 40% 8%, rgba(255,255,255,0.5) 0%, transparent 100%),
            radial-gradient(1px 1px at 55% 70%, rgba(255,255,255,0.35) 0%, transparent 100%),
            radial-gradient(1px 1px at 70% 25%, rgba(255,255,255,0.5) 0%, transparent 100%),
            radial-gradient(1.5px 1.5px at 80% 55%, rgba(255,255,255,0.4) 0%, transparent 100%),
            radial-gradient(1px 1px at 90% 10%, rgba(255,255,255,0.6) 0%, transparent 100%),
            radial-gradient(1px 1px at 15% 80%, rgba(255,255,255,0.3) 0%, transparent 100%),
            radial-gradient(1px 1px at 60% 90%, rgba(255,255,255,0.4) 0%, transparent 100%),
            radial-gradient(1.5px 1.5px at 35% 60%, rgba(200,150,255,0.5) 0%, transparent 100%),
            radial-gradient(1px 1px at 85% 75%, rgba(200,150,255,0.4) 0%, transparent 100%),
            radial-gradient(1px 1px at 5%  50%, rgba(255,255,255,0.3) 0%, transparent 100%),
            radial-gradient(1px 1px at 95% 40%, rgba(255,255,255,0.35) 0%, transparent 100%),
            radial-gradient(1.5px 1.5px at 47% 33%, rgba(255,255,255,0.5) 0%, transparent 100%),
            radial-gradient(1px 1px at 73% 88%, rgba(200,150,255,0.3) 0%, transparent 100%);
        pointer-events: none;
        z-index: 0;
    }

    /* ── Main Title ── */
    .main-title-wrap {
        text-align: center;
        padding: 2.5rem 0 0.5rem;
        position: relative;
    }
    .main-title-eyebrow {
        font-family: 'Cinzel', serif;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.45em;
        color: #a78bfa;
        text-transform: uppercase;
        margin-bottom: 0.6rem;
        opacity: 0.8;
    }
    .main-title {
        font-family: 'Cinzel', serif;
        font-size: clamp(2.2rem, 5vw, 3.6rem);
        font-weight: 900;
        letter-spacing: 0.04em;
        line-height: 1.1;
        background: linear-gradient(135deg, #e0c3fc 0%, #c084fc 30%, #f0abfc 55%, #818cf8 80%, #c4b5fd 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0;
        filter: drop-shadow(0 0 30px rgba(192, 132, 252, 0.35));
    }
    .main-title-sub {
        font-family: 'Be Vietnam Pro', sans-serif;
        text-align: center;
        color: #9ca3af;
        font-size: 1rem;
        font-weight: 300;
        letter-spacing: 0.02em;
        margin: 0.6rem 0 0;
    }

    /* ── Orb Divider ── */
    .orb-divider {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1rem;
        margin: 1.5rem 0;
    }
    .orb-divider-line {
        flex: 1;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(192,132,252,0.4), transparent);
    }
    .orb-divider-gem {
        width: 10px; height: 10px;
        background: radial-gradient(circle at 35% 35%, #f0abfc, #7c3aed);
        border-radius: 50%;
        box-shadow: 0 0 12px rgba(192,132,252,0.8), 0 0 24px rgba(192,132,252,0.3);
    }

    /* ── Section Header ── */
    .section-header {
        font-family: 'Cinzel', serif;
        font-size: 1.1rem;
        font-weight: 600;
        color: #d4aaff;
        letter-spacing: 0.08em;
        margin: 0 0 4px;
    }
    .section-sub {
        font-family: 'Be Vietnam Pro', sans-serif;
        color: #6b7280;
        font-size: 0.82rem;
        margin: 0 0 16px;
        letter-spacing: 0.01em;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0f28 0%, #130a2a 100%) !important;
        border-right: 1px solid rgba(120,80,200,0.2) !important;
    }
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {
        font-family: 'Cinzel', serif !important;
        color: #c084fc !important;
        letter-spacing: 0.06em;
    }

    /* ── Cards ── */
    .reading-card {
        background: linear-gradient(135deg, rgba(120,40,200,0.12) 0%, rgba(40,10,80,0.25) 100%);
        border: 1px solid rgba(192,132,252,0.25);
        border-radius: 16px;
        padding: 20px 24px;
        margin: 12px 0;
        backdrop-filter: blur(16px);
        position: relative;
        overflow: hidden;
        transition: border-color 0.3s ease, box-shadow 0.3s ease;
    }
    .reading-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, rgba(192,132,252,0.6), transparent);
    }
    .reading-card:hover {
        border-color: rgba(192,132,252,0.5);
        box-shadow: 0 4px 32px rgba(120,40,200,0.2);
    }
    .reading-card h4 {
        font-family: 'Be Vietnam Pro', sans-serif;
        color: #e0d0ff;
        margin: 0 0 10px 0;
        font-size: 1rem;
        font-weight: 700;
        letter-spacing: 0.01em;
    }
    .reading-card p {
        font-family: 'Be Vietnam Pro', sans-serif;
        color: #d1c7e8;
        margin: 0;
        line-height: 1.75;
        font-size: 0.93rem;
    }

    .reading-card-faded {
        background: rgba(255,255,255,0.02);
        border: 1px dashed rgba(120,80,200,0.2);
        border-radius: 16px;
        padding: 20px 24px;
        margin: 12px 0;
        opacity: 0.55;
    }
    .reading-card-faded h4 {
        font-family: 'Be Vietnam Pro', sans-serif;
        color: #6b7280;
        margin: 0 0 10px 0;
        font-size: 1rem;
        font-weight: 700;
        letter-spacing: 0.01em;
    }
    .reading-card-faded p {
        font-family: 'Be Vietnam Pro', sans-serif;
        color: #4b5563;
        margin: 0;
        line-height: 1.75;
        font-size: 0.93rem;
    }

    /* ── Hand Note ── */
    .hand-note-wrap {
        background: linear-gradient(120deg, rgba(139,92,246,0.15) 0%, rgba(30,10,80,0.3) 100%);
        border-left: 3px solid #9333ea;
        border-radius: 0 12px 12px 0;
        padding: 14px 20px;
        margin: 20px 0 4px;
        position: relative;
    }
    .hand-note-wrap::before {
        content: '✦';
        position: absolute;
        left: -10px;
        top: 50%;
        transform: translateY(-50%);
        color: #9333ea;
        font-size: 14px;
        background: #07071a;
        padding: 2px 3px;
    }
    .hand-note {
        font-family: 'Be Vietnam Pro', sans-serif;
        color: #e9d5ff;
        font-size: 1.05rem;
        font-weight: 700;
        letter-spacing: 0.01em;
        margin: 0;
    }
    .hand-detail {
        font-family: 'Be Vietnam Pro', sans-serif;
        color: #7c6c99;
        font-size: 0.85rem;
        margin: 8px 0 20px 0;
        padding-left: 4px;
        font-style: italic;
    }

    /* ── Badges ── */
    .badge-high   { background: rgba(16,185,129,0.15); color: #6ee7b7; border: 1px solid rgba(16,185,129,0.3); padding: 2px 12px; border-radius: 20px; font-size: 11px; font-weight: 600; font-family: 'Be Vietnam Pro', sans-serif; }
    .badge-medium { background: rgba(245,158,11,0.15); color: #fcd34d; border: 1px solid rgba(245,158,11,0.3); padding: 2px 12px; border-radius: 20px; font-size: 11px; font-weight: 600; font-family: 'Be Vietnam Pro', sans-serif; }
    .badge-low    { background: rgba(239,68,68,0.15);  color: #fca5a5; border: 1px solid rgba(239,68,68,0.3);  padding: 2px 12px; border-radius: 20px; font-size: 11px; font-weight: 600; font-family: 'Be Vietnam Pro', sans-serif; }
    .badge-none   { background: rgba(75,85,99,0.2);    color: #6b7280;  border: 1px solid rgba(75,85,99,0.3);   padding: 2px 12px; border-radius: 20px; font-size: 11px; font-family: 'Be Vietnam Pro', sans-serif; }

    /* ── Tags ── */
    .tag       { display: inline-block; background: rgba(139,92,246,0.15); color: #c4b5fd; border: 1px solid rgba(139,92,246,0.25); padding: 2px 12px; border-radius: 20px; font-size: 11px; margin: 2px 3px 8px 0; font-family: 'Be Vietnam Pro', sans-serif; }
    .tag-faded { display: inline-block; background: rgba(255,255,255,0.04); color: #4b5563; border: 1px solid rgba(255,255,255,0.06); padding: 2px 12px; border-radius: 20px; font-size: 11px; margin: 2px 3px 8px 0; font-family: 'Be Vietnam Pro', sans-serif; }

    /* ── Image Frames ── */
    .image-frame-label {
        font-family: 'Cinzel', serif;
        font-size: 0.78rem;
        letter-spacing: 0.18em;
        color: #7c6c99;
        text-transform: uppercase;
        margin-bottom: 8px;
    }
    [data-testid="stImage"] img {
        border-radius: 16px !important;
        border: 1px solid rgba(139,92,246,0.25) !important;
        box-shadow: 0 8px 40px rgba(80,20,160,0.3), 0 0 0 1px rgba(192,132,252,0.1) !important;
        transition: box-shadow 0.3s ease !important;
    }
    [data-testid="stImage"] img:hover {
        box-shadow: 0 12px 50px rgba(120,40,200,0.45), 0 0 0 1px rgba(192,132,252,0.25) !important;
    }

    /* ── Metric cards ── */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(120,40,200,0.1) 0%, rgba(30,10,80,0.2) 100%);
        border: 1px solid rgba(139,92,246,0.2);
        border-radius: 14px;
        padding: 16px 18px !important;
        backdrop-filter: blur(10px);
    }
    [data-testid="stMetricLabel"] {
        font-family: 'Be Vietnam Pro', sans-serif !important;
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.03em !important;
        color: #a78bfa !important;
    }
    [data-testid="stMetricValue"] {
        font-family: 'Be Vietnam Pro', sans-serif !important;
        font-size: 1.4rem !important;
        font-weight: 600 !important;
        color: #e0d0ff !important;
    }
    [data-testid="stMetricDelta"] {
        font-family: 'Be Vietnam Pro', sans-serif !important;
        font-size: 0.8rem !important;
    }

    /* ── Tabs ── */
    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        background: rgba(30,10,60,0.5) !important;
        border-radius: 14px !important;
        padding: 4px !important;
        border: 1px solid rgba(139,92,246,0.2) !important;
        gap: 4px !important;
    }
    [data-testid="stTabs"] [data-baseweb="tab"] {
        font-family: 'Be Vietnam Pro', sans-serif !important;
        font-size: 0.88rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.02em !important;
        color: #7c6c99 !important;
        border-radius: 10px !important;
        padding: 10px 22px !important;
        border: none !important;
        background: transparent !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="stTabs"] [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(120,40,200,0.4), rgba(80,20,140,0.5)) !important;
        color: #e0d0ff !important;
        box-shadow: 0 2px 12px rgba(120,40,200,0.3) !important;
    }

    /* ── Buttons ── */
    .stDownloadButton > button {
        background: linear-gradient(135deg, rgba(120,40,200,0.3) 0%, rgba(60,20,120,0.4) 100%) !important;
        border: 1px solid rgba(192,132,252,0.35) !important;
        border-radius: 12px !important;
        color: #d4aaff !important;
        font-family: 'Be Vietnam Pro', sans-serif !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
        letter-spacing: 0.04em !important;
        padding: 12px 24px !important;
        transition: all 0.25s ease !important;
        width: 100% !important;
    }
    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, rgba(150,60,230,0.45) 0%, rgba(90,30,160,0.5) 100%) !important;
        border-color: rgba(192,132,252,0.6) !important;
        box-shadow: 0 4px 20px rgba(120,40,200,0.35) !important;
        transform: translateY(-1px) !important;
    }

    /* ── File uploader ── */
    [data-testid="stFileUploader"] {
        background: linear-gradient(135deg, rgba(60,20,120,0.15) 0%, rgba(20,5,50,0.25) 100%) !important;
        border: 2px dashed rgba(139,92,246,0.3) !important;
        border-radius: 16px !important;
        padding: 8px !important;
        transition: border-color 0.3s ease !important;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: rgba(192,132,252,0.5) !important;
    }

    /* ── Info & warning boxes ── */
    [data-testid="stAlert"] {
        background: rgba(30,10,80,0.4) !important;
        border: 1px solid rgba(139,92,246,0.25) !important;
        border-radius: 12px !important;
        font-family: 'Be Vietnam Pro', sans-serif !important;
        color: #c4b5fd !important;
    }

    /* ── Debug box ── */
    .debug-box {
        background: rgba(245,158,11,0.08);
        border: 1px solid rgba(245,158,11,0.25);
        border-radius: 12px;
        padding: 14px 18px;
        margin: 12px 0;
        font-family: 'Courier New', monospace;
        font-size: 12px;
        color: #fcd34d;
        line-height: 1.8;
    }

    /* ── Confidence pct ── */
    .conf-pct {
        font-family: 'Be Vietnam Pro', sans-serif;
        color: #6b7280;
        font-size: 11px;
        font-weight: 400;
        margin-left: 6px;
    }

    /* ── Divider ── */
    hr {
        border: none !important;
        border-top: 1px solid rgba(139,92,246,0.15) !important;
        margin: 1.5rem 0 !important;
    }

    /* ── Spinner ── */
    .stSpinner > div {
        border-color: rgba(192,132,252,0.2) !important;
        border-top-color: #c084fc !important;
    }

    /* ── Slider ── */
    [data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] {
        background: #9333ea !important;
        box-shadow: 0 0 8px rgba(147,51,234,0.6) !important;
    }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #07071a; }
    ::-webkit-scrollbar-thumb { background: rgba(139,92,246,0.4); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(192,132,252,0.6); }

    /* ── Pulse animation for gem ── */
    @keyframes pulse-glow {
        0%  { box-shadow: 0 0 8px rgba(192,132,252,0.6), 0 0 16px rgba(192,132,252,0.2); }
        50% { box-shadow: 0 0 16px rgba(192,132,252,0.9), 0 0 32px rgba(192,132,252,0.4); }
        100%{ box-shadow: 0 0 8px rgba(192,132,252,0.6), 0 0 16px rgba(192,132,252,0.2); }
    }
    .orb-divider-gem { animation: pulse-glow 3s ease-in-out infinite; }

    footer { visibility: hidden; }
    #MainMenu { visibility: hidden; }
    header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ─── Header ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-title-wrap">
    <p class="main-title-eyebrow">✦ Palmistry · AI Oracle ✦</p>
    <h1 class="main-title">Bói Chỉ Tay AI</h1>
    <p class="main-title-sub">Khám phá bí ẩn đường chỉ tay qua trí tuệ nhân tạo</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="orb-divider">
    <div class="orb-divider-line"></div>
    <div class="orb-divider-gem"></div>
    <div class="orb-divider-line"></div>
</div>
""", unsafe_allow_html=True)


# ─── Hàm Tải Model Tự Động ───────────────────────────────────────────────────
@st.cache_resource
def download_models():
    os.makedirs('model', exist_ok=True)

    model1_path = 'model/best_model.pth'
    model2_path = 'model/best_model2.pth'
    model3_path = 'model/best_model3.pth'

    id_model1 = 'https://drive.google.com/file/d/1Zjcwts4QwJnd7myJLXsPB7LK28XUaEqA/view?usp=drive_link'
    id_model2 = 'https://drive.google.com/file/d/1ANdhjIM4O4QPlMy0WJrtw4j50BwP4Xb8/view?usp=drive_link'
    id_model3 = 'https://drive.google.com/file/d/1jbqF1hY_EyjwZHLF_M4tcVviahRCYdUT/view?usp=drive_link'

    if not os.path.exists(model1_path):
        with st.spinner("🔮 Đang khởi tạo Hệ thống AI (Model 1)..."):
            gdown.download(f'https://drive.google.com/uc?id={id_model1}', model1_path, quiet=False)

    if not os.path.exists(model2_path):
        with st.spinner("🔮 Đang khởi tạo Hệ thống AI (Model 2)..."):
            gdown.download(f'https://drive.google.com/uc?id={id_model2}', model2_path, quiet=False)

    if not os.path.exists(model3_path):
        with st.spinner("🔮 Đang khởi tạo Hệ thống AI (Model 3)..."):
            gdown.download(f'https://drive.google.com/uc?id={id_model3}', model3_path, quiet=False)

    return True

_ = download_models()


# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Cài đặt")

    gender = st.radio(
        "👤 Giới tính",
        options=["male", "female"],
        format_func=lambda x: "👨 Nam — xem tay Trái" if x == "male" else "👩 Nữ — xem tay Phải",
    )

    st.divider()
    st.markdown("### 🎯 Ngưỡng nhận diện")
    st.caption("Chỉnh riêng cho từng đường chỉ tay")

    conf_life  = st.slider("💚 Sinh Đạo",   min_value=0.1, max_value=0.9, value=0.50, step=0.05)
    conf_heart = st.slider("❤️ Tâm Đạo",    min_value=0.1, max_value=0.9, value=0.50, step=0.05)
    conf_head  = st.slider("💙 Trí Đạo",    min_value=0.1, max_value=0.9, value=0.50, step=0.05)
    conf_fate  = st.slider("⭐ Định Mệnh",  min_value=0.1, max_value=0.9, value=0.30, step=0.05)

    thresholds = {
        "life":  conf_life,
        "heart": conf_heart,
        "head":  conf_head,
        "fate":  conf_fate,
    }

    st.divider()
    debug_mode = st.toggle("🐛 Debug Mode", value=False)

    st.divider()
    st.markdown("### 📖 Hướng dẫn")
    st.info("""
**Bước 1:** Chọn giới tính
**Bước 2:** Upload ảnh hoặc dùng Camera
**Bước 3:** Xem kết quả phân tích

**Lưu ý chụp ảnh tốt:**
- 🖐️ Mở thẳng lòng bàn tay
- 💡 Đủ ánh sáng, tránh bóng đổ
- 📐 Bàn tay chiếm phần lớn khung hình
- 🎯 Ảnh rõ nét, không bị mờ
    """)

    st.divider()
    st.markdown("### 🔮 4 Đường Chỉ Tay")
    st.markdown("""
- 💚 **Sinh Đạo** — Sức khỏe & sinh khí
- ❤️ **Tâm Đạo** — Tình cảm & cảm xúc
- 💙 **Trí Đạo** — Trí tuệ & tư duy
- ⭐ **Định Mệnh** — Sự nghiệp & con đường đời
    """)


# ─── Hàm hiển thị kết quả ────────────────────────────────────────────────────
def display_results(result: dict, btn_key: str):
    st.divider()

    st.markdown(f"""
    <div class="hand-note-wrap">
        <p class="hand-note">{result["hand_note"]}</p>
    </div>
    <p class="hand-detail">{result["hand_detail"]}</p>
    """, unsafe_allow_html=True)

    if result["total_lines"] == 0:
        st.warning("⚠️ Không phát hiện đường chỉ tay rõ ràng. Hãy thử chụp lại hoặc giảm ngưỡng nhận diện.")
        return

    st.markdown(f"""
    <div class="orb-divider" style="margin: 8px 0 4px;">
        <div class="orb-divider-line"></div>
        <span style="font-family:'Cinzel',serif;font-size:0.78rem;letter-spacing:0.2em;color:#7c6c99;white-space:nowrap;">
            PHÂN TÍCH {result['total_lines']} ĐƯỜNG CHỈ TAY
        </span>
        <div class="orb-divider-line"></div>
    </div>
    """, unsafe_allow_html=True)

    for r in result["readings"]:
        if r["found"]:
            badge_text  = {"high": "Rõ nét", "medium": "Trung bình", "low": "Mờ nhạt"}.get(r["conf_level"], "")
            badge_class = f"badge-{r['conf_level']}"
            tags_html   = "".join(f'<span class="tag">{t}</span>' for t in r["tags"])
            st.markdown(f"""
            <div class="reading-card">
                <h4>
                    {r['emoji']} {r['line']}
                    &nbsp;<span class="{badge_class}">{badge_text}</span>
                    <span class="conf-pct">({r['confidence']:.0%})</span>
                </h4>
                <div style="margin-bottom:12px;">{tags_html}</div>
                <p>{r['meaning']}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            tags_html = "".join(f'<span class="tag-faded">{t}</span>' for t in r["tags"])
            st.markdown(f"""
            <div class="reading-card-faded">
                <h4>
                    {r['emoji']} {r['line']}
                    &nbsp;<span class="badge-none">Không tìm thấy</span>
                </h4>
                <div style="margin-bottom:12px;">{tags_html}</div>
                <p>{r['meaning']}</p>
            </div>
            """, unsafe_allow_html=True)

    st.divider()
    summary  = f"KẾT QUẢ BÓI CHỈ TAY AI\n{'='*40}\n\n"
    summary += f"{result['hand_note']}\n{result['hand_detail']}\n\n"
    summary += f"Phát hiện {result['total_lines']} đường chỉ tay\n\n" + "="*40 + "\n\n"
    for r in result["readings"]:
        tags_str = " · ".join(r["tags"])
        status   = f"({r['confidence']:.0%})" if r["found"] else "(Không tìm thấy)"
        summary += f"{r['emoji']} {r['line']} {status}\nTags: {tags_str}\n{r['meaning']}\n\n" + "-"*40 + "\n\n"

    st.download_button(
        label="💾 Lưu kết quả (.txt)",
        data=summary,
        file_name="ket_qua_boi_tay.txt",
        mime="text/plain",
        use_container_width=True,
        key=btn_key,
    )


# ─── Hàm xử lý ảnh ───────────────────────────────────────────────────────────
def process_image(image: Image.Image, src_key: str):
    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown('<p class="image-frame-label">✦ Ảnh gốc</p>', unsafe_allow_html=True)
        st.image(image, use_container_width=True)

    with st.spinner("🔮 Đang giải mã đường chỉ tay của bạn..."):
        annotated_img, detections, img_w, img_h, debug_info = run_inference(image, thresholds)
        result = interpret_results(detections, gender, img_w, img_h)

    with col2:
        st.markdown('<p class="image-frame-label">✦ Nhận diện AI</p>', unsafe_allow_html=True)
        st.image(annotated_img, use_container_width=True)

    # ── Debug mode ────────────────────────────────────────────
    if debug_mode:
        st.markdown("### 🐛 Debug Info")
        st.markdown(f"""
        <div class="debug-box">
            📐 Ảnh gốc: {img_w} x {img_h} px<br>
            📏 Ratio: {debug_info['ratio']:.4f}<br>
            📦 Resize thành: {debug_info['new_w']} x {debug_info['new_h']}<br>
            ➕ Padding: pad_x={debug_info['pad_x']} pad_y={debug_info['pad_y']}<br>
            🔍 Tổng detection (trước filter): {debug_info['total_raw']}<br>
            ✅ Detection sau filter: {len(detections)}
        </div>
        """, unsafe_allow_html=True)

        if debug_info['raw_boxes']:
            st.markdown("**📦 Raw bbox:**")
            for b in debug_info['raw_boxes']:
                st.code(
                    f"{b['class']} ({b['score']:.0%}) | "
                    f"RAW: [{b['raw_x1']:.0f}, {b['raw_y1']:.0f}, {b['raw_x2']:.0f}, {b['raw_y2']:.0f}] | "
                    f"SCALED: [{b['x1']}, {b['y1']}, {b['x2']}, {b['y2']}]"
                )
        else:
            st.warning("Không có detection nào — thử giảm ngưỡng xuống 0.1")

    # ── Metrics 4 đường ──────────────────────────────────────
    st.markdown("""
    <div class="orb-divider" style="margin: 20px 0 12px;">
        <div class="orb-divider-line"></div>
        <span style="font-family:'Cinzel',serif;font-size:0.75rem;letter-spacing:0.2em;color:#7c6c99;white-space:nowrap;">
            TÓM TẮT NHẬN DIỆN
        </span>
        <div class="orb-divider-line"></div>
    </div>
    """, unsafe_allow_html=True)

    cols      = st.columns(4, gap="small")
    line_info = [
        ("💚", "Sinh Đạo",   "life"),
        ("❤️", "Tâm Đạo",   "heart"),
        ("💙", "Trí Đạo",   "head"),
        ("⭐", "Định Mệnh", "fate"),
    ]
    for col, (emoji, name, cls) in zip(cols, line_info):
        found = any(r["class"] == cls and r["found"] for r in result["readings"])
        conf  = next((r["confidence"] for r in result["readings"] if r["class"] == cls and r["found"]), 0)
        with col:
            if found:
                st.metric(f"{emoji} {name}", f"{conf:.0%}", "✅ Phát hiện")
            else:
                st.metric(f"{emoji} {name}", "—", "❌ Không thấy")

    display_results(result, btn_key=f"download_{src_key}")


# ─── Tabs chính ──────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["  📁  Upload Ảnh  ", "  📷  Camera  "])

with tab1:
    st.markdown('<p class="section-sub">Tải lên ảnh lòng bàn tay rõ nét — JPG, PNG hoặc WEBP</p>', unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "Chọn ảnh bàn tay",
        type=["jpg", "jpeg", "png", "webp"],
        help="Ảnh rõ nét, lòng bàn tay mở thẳng, đủ ánh sáng",
        label_visibility="collapsed",
    )
    if uploaded:
        image = Image.open(uploaded).convert("RGB")
        process_image(image, src_key="upload")

with tab2:
    st.info("📸 Hướng camera vào lòng bàn tay · Giữ tay thẳng · Đảm bảo đủ ánh sáng")
    camera_img = st.camera_input("Chụp ảnh bàn tay", label_visibility="collapsed")
    if camera_img:
        image = Image.open(camera_img).convert("RGB")
        process_image(image, src_key="camera")