import streamlit as st
from PIL import Image
import time
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
    .stApp { background: linear-gradient(135deg, #0d0d2b 0%, #1a0533 100%); }
    .main-title {
        text-align: center; font-size: 3rem; font-weight: 800;
        background: linear-gradient(90deg, #c084fc, #f0abfc, #818cf8);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .sub-title { text-align: center; color: #a78bfa; font-size: 1.1rem; margin-top: 4px; }
    .hand-note {
        background: linear-gradient(90deg, rgba(192,132,252,0.2), rgba(129,140,248,0.2));
        border-left: 4px solid #c084fc; border-radius: 8px;
        padding: 12px 18px; color: #f0abfc; font-size: 1.1rem;
        font-weight: 600; margin: 16px 0 6px 0;
    }
    .hand-detail { color: #9ca3af; font-size: 0.9rem; margin: 0 0 16px 0; padding-left: 4px; font-style: italic; }
    .reading-card {
        background: rgba(255,255,255,0.05); border: 1px solid rgba(180,120,255,0.3);
        border-radius: 12px; padding: 16px 20px; margin: 10px 0; backdrop-filter: blur(10px);
    }
    .reading-card h4 { color: #d4aaff; margin: 0 0 8px 0; font-size: 1.05rem; }
    .reading-card p  { color: #e8e0f0; margin: 0; line-height: 1.7; font-size: 0.95rem; }
    .reading-card-faded {
        background: rgba(255,255,255,0.02); border: 1px dashed rgba(180,120,255,0.2);
        border-radius: 12px; padding: 16px 20px; margin: 10px 0; opacity: 0.65;
    }
    .reading-card-faded h4 { color: #9ca3af; margin: 0 0 8px 0; font-size: 1.05rem; }
    .reading-card-faded p  { color: #9ca3af; margin: 0; line-height: 1.7; font-size: 0.95rem; }
    .badge-high   { background:#1a4a2a; color:#5dff8f; padding:2px 10px; border-radius:20px; font-size:11px; font-weight:600; }
    .badge-medium { background:#3a3a10; color:#ffd700; padding:2px 10px; border-radius:20px; font-size:11px; font-weight:600; }
    .badge-low    { background:#3a1020; color:#ff8fa0; padding:2px 10px; border-radius:20px; font-size:11px; font-weight:600; }
    .badge-none   { background:#2a2a2a; color:#888888; padding:2px 10px; border-radius:20px; font-size:11px; }
    .tag       { display:inline-block; background:rgba(192,132,252,0.15); color:#d4aaff; padding:2px 10px; border-radius:20px; font-size:11px; margin:2px 2px 6px 0; }
    .tag-faded { display:inline-block; background:rgba(255,255,255,0.05); color:#666; padding:2px 10px; border-radius:20px; font-size:11px; margin:2px 2px 6px 0; }
    .debug-box { background:rgba(255,200,0,0.1); border:1px solid rgba(255,200,0,0.3); border-radius:8px; padding:12px; margin:10px 0; font-family:monospace; font-size:12px; color:#ffd700; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ─── Header ──────────────────────────────────────────────────────────────────
st.markdown('<h1 class="main-title">Bói Chỉ Tay AI</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Khám phá bí ẩn đường chỉ tay bằng trí tuệ nhân tạo</p>', unsafe_allow_html=True)
st.divider()

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

    conf_life = st.slider(
        "💚 Sinh Đạo",
        min_value=0.1, max_value=0.9,
        value=0.50, step=0.05,
    )
    conf_heart = st.slider(
        "❤️ Tâm Đạo",
        min_value=0.1, max_value=0.9,
        value=0.50, step=0.05,
    )
    conf_head = st.slider(
        "💙 Trí Đạo",
        min_value=0.1, max_value=0.9,
        value=0.50, step=0.05,
    )
    conf_fate = st.slider(
        "⭐ Định Mệnh",
        min_value=0.1, max_value=0.9,
        value=0.30, step=0.05,
    )

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
def display_results(result: dict):
    st.divider()
    st.markdown(f'<div class="hand-note">{result["hand_note"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<p class="hand-detail">{result["hand_detail"]}</p>', unsafe_allow_html=True)

    if result["total_lines"] == 0:
        st.warning("⚠️ Không phát hiện đường chỉ tay rõ ràng. Hãy thử chụp lại hoặc giảm ngưỡng nhận diện.")
        return

    st.markdown(f"### 🔮 Phân tích {result['total_lines']} đường chỉ tay")

    for r in result["readings"]:
        if r["found"]:
            badge_text  = {"high": "Rõ nét", "medium": "Trung bình", "low": "Mờ nhạt"}.get(r["conf_level"], "")
            badge_class = f"badge-{r['conf_level']}"
            tags_html   = "".join(f'<span class="tag">{t}</span>' for t in r["tags"])
            st.markdown(f"""
            <div class="reading-card">
                <h4>{r['emoji']} {r['line']}
                    &nbsp;<span class="{badge_class}">{badge_text}</span>
                    &nbsp;<span style="color:#6b7280;font-size:12px;font-weight:400;">({r['confidence']:.0%})</span>
                </h4>
                <div style="margin-bottom:10px;">{tags_html}</div>
                <p>{r['meaning']}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            tags_html = "".join(f'<span class="tag-faded">{t}</span>' for t in r["tags"])
            st.markdown(f"""
            <div class="reading-card-faded">
                <h4>{r['emoji']} {r['line']}
                    &nbsp;<span class="badge-none">Không tìm thấy</span>
                </h4>
                <div style="margin-bottom:10px;">{tags_html}</div>
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
        label="💾 Tải kết quả (.txt)", data=summary,
        file_name="ket_qua_boi_tay.txt", mime="text/plain",
        use_container_width=True,
    )


# ─── Hàm xử lý ảnh ───────────────────────────────────────────────────────────
def process_image(image: Image.Image):
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**🖼️ Ảnh gốc**")
        st.image(image, use_container_width=True)

    with st.spinner("🔮 Đang phân tích đường chỉ tay..."):
        annotated_img, detections, img_w, img_h, debug_info = run_inference(
            image, thresholds
        )
        result = interpret_results(detections, gender, img_w, img_h)

    with col2:
        st.markdown("**🎯 Kết quả nhận diện**")
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
    st.divider()
    cols      = st.columns(4)
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

    display_results(result)


# ─── Tabs chính ──────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["📁 Upload Ảnh", "📷 Camera Realtime"])

with tab1:
    uploaded = st.file_uploader(
        "Chọn ảnh bàn tay (JPG, PNG, WEBP)",
        type=["jpg", "jpeg", "png", "webp"],
        help="Ảnh rõ nét, lòng bàn tay mở thẳng, đủ ánh sáng",
    )
    if uploaded:
        image = Image.open(uploaded).convert("RGB")
        process_image(image)

with tab2:
    st.info("📸 Hướng camera vào lòng bàn tay, giữ tay thẳng và đủ ánh sáng")
    camera_img = st.camera_input("Chụp ảnh bàn tay")
    if camera_img:
        image = Image.open(camera_img).convert("RGB")
        process_image(image)