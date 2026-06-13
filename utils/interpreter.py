# utils/interpreter.py
# ─────────────────────────────────────────────────────────────────────────────
# Diễn giải kết quả detection dựa trên tài liệu Palmistry truyền thống
# Logic phân tích: confidence + vị trí bbox + hình dạng (cong lên/xuống/thẳng)
# ─────────────────────────────────────────────────────────────────────────────


def get_confidence_level(conf: float) -> str:
    if conf >= 0.70:
        return "high"
    elif conf >= 0.45:
        return "medium"
    else:
        return "low"


def get_line_emoji(cls: str) -> str:
    return {"life": "💚", "heart": "❤️", "head": "💙", "fate": "⭐"}.get(cls, "🔮")


def get_line_name_vi(cls: str) -> str:
    return {
        "life":  "Đường Sinh Đạo",
        "heart": "Đường Tâm Đạo",
        "head":  "Đường Trí Đạo",
        "fate":  "Đường Định Mệnh",
    }.get(cls, cls.title())


# ─── Phân tích hình dạng bbox ─────────────────────────────────────────────────
def analyze_bbox(bbox: list, img_width: int, img_height: int) -> dict:
    """
    Phân tích bbox để suy ra hình dạng đường chỉ tay.
    Trả về các thông tin: độ dài, hướng, vị trí, độ cong ước tính
    """
    x1, y1, x2, y2 = bbox
    w = abs(x2 - x1)
    h = abs(y2 - y1)

    img_width  = max(img_width,  1)
    img_height = max(img_height, 1)
    h          = max(h, 1)

    # Tỉ lệ chiều rộng/chiều cao
    aspect = w / h

    # Vị trí tương đối trong ảnh (0=trên, 1=dưới)
    center_y = ((y1 + y2) / 2) / img_height
    center_x = ((x1 + x2) / 2) / img_width

    # Độ dài tương đối so với ảnh
    rel_w = w / img_width
    rel_h = h / img_height
    rel_length = max(rel_w, rel_h)

    # Độ dài
    if rel_length > 0.45:
        length = "long"
    elif rel_length > 0.25:
        length = "medium"
    else:
        length = "short"

    # Hướng chính (ngang hay dọc)
    is_horizontal = w > h * 1.2
    is_vertical   = h > w * 1.2

    # Vị trí bbox (trên/giữa/dưới ảnh)
    if center_y < 0.35:
        position_y = "top"
    elif center_y < 0.60:
        position_y = "middle"
    else:
        position_y = "bottom"

    # Vị trí bbox (trái/giữa/phải ảnh)
    if center_x < 0.35:
        position_x = "left"
    elif center_x < 0.65:
        position_x = "center"
    else:
        position_x = "right"

    return {
        "aspect":        aspect,
        "center_y":      center_y,
        "center_x":      center_x,
        "length":        length,
        "rel_length":    rel_length,
        "is_horizontal": is_horizontal,
        "is_vertical":   is_vertical,
        "position_y":    position_y,
        "position_x":    position_x,
        "width":         w,
        "height":        h,
    }


# ─── Diễn giải từng đường ────────────────────────────────────────────────────

def interpret_life(conf_level: str, shape: dict) -> dict:
    """
    Nhận xét DỰA VÀO HÌNH DẠNG BBOX — không dựa vào confidence
    """
    # ── Độ dài đường (dựa vào rel_length) ────────────────────
    if shape["length"] == "long":
        length_text = "dài và rõ nét"
        length_mean = "sức khỏe tốt, dồi dào năng lượng và sức đề kháng cao."
        length_tags = ["Sức khỏe tốt", "Năng lượng dồi dào"]
    elif shape["length"] == "medium":
        length_text = "ở mức trung bình"
        length_mean = "sức khỏe ổn định, có đủ năng lượng cho cuộc sống hàng ngày."
        length_tags = ["Sức khỏe ổn định", "Phục hồi tốt"]
    else:
        length_text = "ngắn"
        length_mean = "thể trạng có phần nhạy cảm, cần chú ý giữ gìn sức khỏe."
        length_tags = ["Cần chú ý sức khỏe", "Ý chí mạnh mẽ"]

    # ── Độ cong (dựa vào aspect ratio) ───────────────────────
    if shape["aspect"] >0.6:
        curve_text = "cong rộng ra giữa lòng bàn tay"
        curve_mean = "Bạn là người hướng ngoại, năng động, thích khám phá và xê dịch."
        curve_tag  = "Hướng ngoại · Năng động"
    elif shape["aspect"] < 0.6 and shape["aspect"] > 0.3:
        curve_text = "cong vừa phải"
        curve_mean = "Bạn cân bằng giữa hướng nội và hướng ngoại, linh hoạt trong các tình huống."
        curve_tag  = "Cân bằng · Linh hoạt"
    else:
        curve_text = "cong hẹp, ôm sát ngón cái"
        curve_mean = "Bạn thiên về hướng nội, yêu thích sự ổn định và môi trường quen thuộc."
        curve_tag  = "Hướng nội · Ưa ổn định"

    meaning = (
        f"Đường Sinh Đạo {length_text}, {curve_text} — "
        f"{length_mean} {curve_mean}"
    )
    tags = length_tags + [curve_tag]

    # ── Phân nhánh ───────────────────────────────────────────
    if shape["position_y"] == "top":
        meaning += " Đường có nhánh hướng lên — dấu hiệu thăng tiến và thành công."
        tags.append("Thăng tiến · Thành công")
    elif shape["position_y"] == "bottom":
        meaning += " Đường kéo dài xuống thấp — thích du lịch, có khả năng định cư xa quê."
        tags.append("Thích xê dịch · Du lịch")

    return {"meaning": meaning, "tags": tags}


def interpret_head(conf_level: str, shape: dict) -> dict:
    # ── Độ dài ───────────────────────────────────────────────
    if shape["length"] == "long":
        length_text = "dài và sắc nét"
        length_mean = "tư duy sâu sắc, khả năng phân tích xuất sắc, tầm nhìn xa."
        length_tags = ["Tư duy sâu sắc", "Phân tích tốt", "Tầm nhìn xa"]
    elif shape["length"] == "medium":
        length_text = "ở mức trung bình"
        length_mean = "tư duy cân bằng, giải quyết vấn đề tốt trong cuộc sống hàng ngày."
        length_tags = ["Tư duy cân bằng", "Linh hoạt"]
    else:
        length_text = "ngắn"
        length_mean = "suy nghĩ thực tế, thẳng thắn, đưa ra quyết định nhanh chóng."
        length_tags = ["Thực tế", "Quyết đoán", "Hành động nhanh"]

    # ── Cong lên/xuống/thẳng ─────────────────────────────────
    if shape["center_y"] < 0.40:
        curve_text = "chạy thẳng hoặc hơi cong lên"
        curve_mean = "Tư duy logic, thực dụng, phù hợp với khoa học, toán học hoặc kinh doanh."
        curve_tag  = "Logic · Thực dụng"
    elif shape["center_y"] < 0.55:
        curve_text = "chạy ngang ở mức trung bình"
        curve_mean = "Tư duy cân bằng giữa logic và sáng tạo, dễ thích nghi với nhiều lĩnh vực."
        curve_tag  = "Tư duy cân bằng"
    else:
        curve_text = "cong gập xuống phía dưới"
        curve_mean = "Trí tưởng tượng phong phú, thiên về nghệ thuật và sáng tạo."
        curve_tag  = "Sáng tạo · Nghệ thuật"

    meaning = (
        f"Đường Trí Đạo {length_text}, {curve_text} — "
        f"{length_mean} {curve_mean}"
    )
    tags = length_tags + [curve_tag]

    if 0.4 < shape["aspect"] < 0.9 and shape["length"] != "short":
        meaning += " Hình dạng gợi ý tư duy đa chiều — kết hợp tốt logic và sáng tạo."
        tags.append("Tư duy đa chiều")

    return {"meaning": meaning, "tags": tags}


def interpret_heart(conf_level: str, shape: dict) -> dict:
    # ── Độ dài ───────────────────────────────────────────────
    if shape["length"] == "long":
        length_text = "dài và sâu"
        length_mean = "chung thủy, hết lòng với người thân, giàu cảm xúc."
        length_tags = ["Chung thủy", "Giàu cảm xúc", "Hết lòng"]
    elif shape["length"] == "medium":
        length_text = "ở mức trung bình"
        length_mean = "tình cảm ổn định, biết cân bằng giữa lý trí và con tim."
        length_tags = ["Tình cảm ổn định", "Cân bằng"]
    else:
        length_text = "ngắn"
        length_mean = "thực tế trong tình cảm, biết đặt bản thân lên trên hết."
        length_tags = ["Thực tế trong tình cảm", "Tự bảo vệ bản thân"]

    # ── Cong lên/xuống ───────────────────────────────────────
    if shape["center_y"] < 0.6:
        curve_text = "cong vút lên phía trên"
        curve_mean = "Bạn nồng nhiệt, biết thể hiện tình cảm, đời sống cảm xúc phong phú."
        curve_tag  = "Nồng nhiệt · Biểu cảm"
    elif shape["center_y"] < 0.9:
        curve_text = "cong nhẹ lên trên"
        curve_mean = "Bạn có đời sống tình cảm phong phú nhưng vẫn giữ được sự cân bằng."
        curve_tag  = "Cân bằng tình cảm"
    else:
        curve_text = "chạy thẳng ngang"
        curve_mean = "Bạn kiểm soát cảm xúc tốt, lý trí trong tình yêu."
        curve_tag  = "Lý trí · Kiểm soát tốt"

    meaning = (
        f"Đường Tâm Đạo {length_text}, {curve_text} — "
        f"{length_mean} {curve_mean}"
    )
    tags = length_tags + [curve_tag]

    if shape["position_x"] == "left" and shape["length"] == "long":
        meaning += " Đường bắt đầu từ phía dưới ngón trỏ — đặt nhiều kỳ vọng vào tình yêu."
        tags.append("Kỳ vọng cao trong tình yêu")

    return {"meaning": meaning, "tags": tags}


def interpret_fate(conf_level: str, shape: dict) -> dict:
    # ── Hướng đường ──────────────────────────────────────────
    if shape["center_x"] < 0.35:
        curve_text = "bắt đầu từ rìa bàn tay"
        curve_mean = "Sự nghiệp được nhiều người giúp đỡ, dễ thành công trong lĩnh vực liên quan đến công chúng."
        curve_tag  = "Được quý nhân trợ giúp"
    elif shape["center_x"] < 0.65:
        curve_text = "chạy thẳng giữa lòng bàn tay"
        curve_mean = "Con đường sự nghiệp rõ ràng, ổn định, thành công từ nỗ lực bản thân."
        curve_tag  = "Định hướng rõ · Kiên trì"
    else:
        curve_text = "lệch về phía ngón trỏ"
        curve_mean = "Tham vọng, khả năng lãnh đạo xuất sắc, tiềm năng đạt địa vị cao."
        curve_tag  = "Tham vọng · Lãnh đạo"

    # ── Điểm xuất phát ───────────────────────────────────────
    if shape["position_y"] == "bottom":
        start_mean = "Bạn đi lên từ hai bàn tay trắng, thành công dựa hoàn toàn vào tự lực."
        start_tag  = "Tự lực cánh sinh"
    elif shape["position_y"] == "middle":
        start_mean = "Thành công đến muộn hơn nhưng bền vững, thường có bước ngoặt lớn ở tuổi trung niên."
        start_tag  = "Thành công bền vững"
    else:
        start_mean = "Sự nghiệp phát triển sớm, định hướng rõ từ khi còn trẻ."
        start_tag  = "Thành công sớm"

    # ── Độ dài ───────────────────────────────────────────────
    if shape["length"] == "long":
        length_text = "sâu và rõ nét"
        length_mean = "có định hướng sự nghiệp rõ ràng, thường có quý nhân phù trợ."
    elif shape["length"] == "medium":
        length_text = "ở mức trung bình"
        length_mean = "sự nghiệp có thăng trầm nhưng luôn tìm được hướng đi phù hợp."
    else:
        length_text = "ngắn"
        length_mean = "sự nghiệp linh hoạt, không bị gò bó bởi một khuôn mẫu nhất định."

    meaning = (
        f"Đường Định Mệnh {length_text}, {curve_text} — "
        f"{length_mean} {curve_mean} {start_mean}"
    )
    tags = [curve_tag, start_tag]

    return {"meaning": meaning, "tags": tags}


# ─── Hàm chính ───────────────────────────────────────────────────────────────

def interpret_results(detections: list, gender: str,
                      img_width: int = 640, img_height: int = 640) -> dict:
    if gender == "male":
        hand_note   = "👈 Nam xem tay TRÁI — tay trái thể hiện vận mệnh bẩm sinh"
        hand_detail = (
            "Theo quan niệm phong thủy, tay trái của nam giới phản ánh những gì trời ban — "
            "tính cách bẩm sinh, tiềm năng và những điều được định sẵn từ khi sinh ra."
        )
    else:
        hand_note   = "👉 Nữ xem tay PHẢI — tay phải thể hiện vận mệnh do bản thân tạo ra"
        hand_detail = (
            "Theo quan niệm phong thủy, tay phải của nữ giới phản ánh những gì bản thân tự tạo dựng — "
            "nỗ lực, quyết định và hành trình cuộc sống thực tế của chính mình."
        )

    PRIORITY_ORDER = ["life", "heart", "head", "fate"]
    INTERPRET_FN   = {
        "life":  interpret_life,
        "heart": interpret_heart,
        "head":  interpret_head,
        "fate":  interpret_fate,
    }

    # Lấy detection confidence cao nhất cho mỗi class
    best_per_class = {}
    for det in detections:
        cls = det["class"]
        if cls not in best_per_class or det["confidence"] > best_per_class[cls]["confidence"]:
            best_per_class[cls] = det

    readings = []
    for cls in PRIORITY_ORDER:
        if cls in best_per_class:
            det        = best_per_class[cls]
            conf       = det["confidence"]
            conf_level = get_confidence_level(conf)
            shape      = analyze_bbox(det["bbox"], img_width, img_height)
            interp     = INTERPRET_FN[cls](conf_level, shape)

            readings.append({
                "line":       get_line_name_vi(cls),
                "class":      cls,
                "confidence": conf,
                "conf_level": conf_level,
                "emoji":      get_line_emoji(cls),
                "meaning":    interp["meaning"],
                "tags":       interp["tags"],
                "found":      True,
            })

        elif cls == "fate":
            readings.append({
                "line":       "Đường Định Mệnh",
                "class":      "fate",
                "confidence": 0,
                "conf_level": "not_detected",
                "emoji":      "⭐",
                "meaning":    (
                    "Không tìm thấy đường Định Mệnh rõ ràng — không phải ai cũng có đường này. "
                    "Điều đó cho thấy cuộc sống của bạn tự do, không bị gò bó bởi khuôn mẫu định sẵn. "
                    "Số phận hoàn toàn do chính bạn tạo ra bằng nỗ lực và ý chí bản thân."
                ),
                "tags":  ["Tự do · Tự chủ", "Tự tạo vận mệnh"],
                "found": False,
            })

    return {
        "hand_note":   hand_note,
        "hand_detail": hand_detail,
        "readings":    readings,
        "total_lines": len([r for r in readings if r["found"]]),
        "gender":      gender,
    }