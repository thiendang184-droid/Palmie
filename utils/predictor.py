# utils/predictor.py
import torch
from torchvision import transforms
from torchvision.models.detection import fasterrcnn_resnet50_fpn
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from PIL import Image, ImageDraw
import torchvision.transforms.functional as F

_model   = None
_classes = None
_device  = None

CLASS_COLORS = {
    "life":  (34,  197, 94),
    "heart": (239, 68,  68),
    "head":  (59,  130, 246),
    "fate":  (234, 179, 8),
}


def load_model(model_path: str = "model/best_model2.pth"):
    global _model, _classes, _device
    if _model is None:
        _device  = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        ckpt     = torch.load(model_path, map_location=_device)
        _classes = ckpt["classes"]
        _model   = fasterrcnn_resnet50_fpn(weights=None)
        in_features = _model.roi_heads.box_predictor.cls_score.in_features
        _model.roi_heads.box_predictor = FastRCNNPredictor(in_features, len(_classes))
        _model.load_state_dict(ckpt["model"])
        _model.to(_device)
        _model.eval()
    return _model, _classes, _device


def letterbox(image: Image.Image, target: int = 640):
   
    orig_w, orig_h = image.size
    ratio  = target / max(orig_w, orig_h)
    new_w  = int(orig_w * ratio)
    new_h  = int(orig_h * ratio)
    pad_x  = (target - new_w) // 2
    pad_y  = (target - new_h) // 2

    resized = image.resize((new_w, new_h), Image.BILINEAR)
    padded  = Image.new("RGB", (target, target), (114, 114, 114))
    padded.paste(resized, (pad_x, pad_y))

    return padded, ratio, pad_x, pad_y


def run_inference(image: Image.Image, thresholds: dict = None):
    if thresholds is None:
        thresholds = DEFAULT_THRESHOLDS

    model, classes, device = load_model()
    orig_w, orig_h = image.size

    padded, ratio, pad_x, pad_y = letterbox(image, target=640)

    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        ),
    ])

    img_tensor = transform(padded).unsqueeze(0).to(device)

    with torch.no_grad():
        outputs = model(img_tensor)[0]

    # ── Gom tất cả detection theo class ──────────────────────
    # Chưa filter, gom hết trước
    all_detections = {}   # {"life": [{"score":0.8, "box":[...]}, ...], ...}

    raw_boxes = []

    for box, label, score in zip(outputs["boxes"], outputs["labels"], outputs["scores"]):
        score    = float(score)
        label_id = int(label)
        cls_name = classes[label_id]

        if cls_name == "__background__":
            continue

        raw_x1, raw_y1, raw_x2, raw_y2 = box.tolist()

        x1 = max(0,      int((raw_x1 - pad_x) / ratio))
        y1 = max(0,      int((raw_y1 - pad_y) / ratio))
        x2 = min(orig_w, int((raw_x2 - pad_x) / ratio))
        y2 = min(orig_h, int((raw_y2 - pad_y) / ratio))

        raw_boxes.append({
            "class":  cls_name, "score": score,
            "raw_x1": raw_x1,   "raw_y1": raw_y1,
            "raw_x2": raw_x2,   "raw_y2": raw_y2,
            "x1": x1, "y1": y1, "x2": x2, "y2": y2,
        })

        # Kiểm tra ngưỡng từng class
        class_threshold = thresholds.get(cls_name, 0.4)
        if score < class_threshold:
            continue
        if x2 <= x1 or y2 <= y1:
            continue

        if cls_name not in all_detections:
            all_detections[cls_name] = []

        all_detections[cls_name].append({
            "score": score,
            "bbox":  [x1, y1, x2, y2],
        })

    # ── Chỉ lấy 1 detection tốt nhất cho mỗi class ──────────
    # Dùng NMS: lấy bbox có score cao nhất sau khi lọc overlap
    best_per_class = {}
    for cls_name, dets in all_detections.items():
        if not dets:
            continue

        # Sắp xếp theo score giảm dần
        dets_sorted = sorted(dets, key=lambda x: x["score"], reverse=True)

        # Lấy cái tốt nhất
        best = dets_sorted[0]

        # Nếu có nhiều detection cùng class → NMS lọc overlap
        if len(dets_sorted) > 1:
            best_box   = torch.tensor([best["bbox"]], dtype=torch.float32)
            other_boxes = torch.tensor(
                [d["bbox"] for d in dets_sorted[1:]],
                dtype=torch.float32
            )
            all_boxes  = torch.cat([best_box, other_boxes], dim=0)
            scores     = torch.tensor(
                [d["score"] for d in dets_sorted],
                dtype=torch.float32
            )
            # IoU threshold 0.3 — overlap > 30% thì bỏ
            keep = torch.ops.torchvision.nms(all_boxes, scores, iou_threshold=0.3)
            # Chỉ lấy cái đầu tiên (score cao nhất sau NMS)
            best = dets_sorted[int(keep[0])]

        best_per_class[cls_name] = best

    # ── Vẽ bbox lên ảnh gốc ──────────────────────────────────
    annotated  = image.copy()
    draw       = ImageDraw.Draw(annotated)
    detections = []

    for cls_name, det in best_per_class.items():
        x1, y1, x2, y2 = det["bbox"]
        score           = det["score"]

        color = CLASS_COLORS.get(cls_name, (255, 255, 255))
        draw.rectangle([x1, y1, x2, y2], outline=color, width=3)

        label_text = f"{cls_name} {score:.0%}"
        text_w     = len(label_text) * 8
        draw.rectangle([x1, max(0, y1 - 20), x1 + text_w, y1], fill=color)
        draw.text((x1 + 3, max(0, y1 - 18)), label_text, fill=(0, 0, 0))

        detections.append({
            "class":      cls_name,
            "confidence": score,
            "bbox":       [x1, y1, x2, y2],
        })

    debug_info = {
        "ratio":     ratio,
        "new_w":     int(orig_w * ratio),
        "new_h":     int(orig_h * ratio),
        "pad_x":     pad_x,
        "pad_y":     pad_y,
        "total_raw": len(raw_boxes),
        "raw_boxes": raw_boxes,
    }

    return annotated, detections, orig_w, orig_h, debug_info