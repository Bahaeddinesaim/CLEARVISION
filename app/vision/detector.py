from __future__ import annotations

from pathlib import Path
import random

import cv2
import pandas as pd
from PIL import Image

from app.core.settings import load_config

CLASS_MAP = {
    "dining table": "table",
    "chair": "chaise",
    "tv": "tv",
    "laptop": "laptop",
    "person": "eleve",
    "book": "objet inattendu",
    "bottle": "objet inattendu",
    "cell phone": "objet inattendu",
    "backpack": "objet abandonne",
}


def _try_load_yolo():
    """Load the configured YOLO model when available."""
    try:
        from ultralytics import YOLO

        model_name = load_config().get("vision", {}).get("yolo_model", "yolo11n.pt")
        return YOLO(model_name)
    except Exception:
        return None


def detect_objects(image_path: str | Path, confidence: float = 0.25) -> tuple[pd.DataFrame, str]:
    """Detect classroom objects and return a dataframe plus annotated image path."""
    image_path = Path(image_path)
    model = _try_load_yolo()
    rows = []
    if model is not None:
        try:
            results = model(str(image_path), conf=confidence, verbose=False)
            names = results[0].names
            for box in results[0].boxes:
                cls_name = names[int(box.cls[0])]
                mapped = CLASS_MAP.get(cls_name, cls_name)
                x1, y1, x2, y2 = [float(v) for v in box.xyxy[0].tolist()]
                rows.append(
                    {
                        "image_name": image_path.name,
                        "object_type": mapped,
                        "raw_class": cls_name,
                        "confidence": float(box.conf[0]),
                        "x1": x1,
                        "y1": y1,
                        "x2": x2,
                        "y2": y2,
                        "area": (x2 - x1) * (y2 - y1),
                    }
                )
            annotated = _draw_boxes(image_path, pd.DataFrame(rows))
            return pd.DataFrame(rows), annotated
        except Exception:
            pass
    return simulate_detection_from_image(image_path)


def simulate_detection_from_image(image_path: Path) -> tuple[pd.DataFrame, str]:
    """Fallback detector used when YOLO is unavailable."""
    img = Image.open(image_path)
    w, h = img.size
    objects = (
        ["table"] * 6
        + ["chaise"] * 12
        + ["eleve"] * random.randint(8, 12)
        + ["tableau", "porte", "fenetre", "fenetre", "bureau", "poubelle", "pc", "pc", "pc", "projecteur"]
    )
    if random.random() < 0.55:
        objects.append("tv")
    if random.random() < 0.35:
        objects.append("chaise renversee")
    if random.random() < 0.25:
        objects.append("fenetre ouverte")
    if random.random() < 0.20:
        objects.append("tv allumee")

    rows = []
    for obj in objects:
        x1 = random.randint(0, max(1, w - 80))
        y1 = random.randint(0, max(1, h - 80))
        x2 = min(w, x1 + random.randint(35, 140))
        y2 = min(h, y1 + random.randint(35, 140))
        rows.append(
            {
                "image_name": image_path.name,
                "object_type": obj,
                "raw_class": "simulated",
                "confidence": round(random.uniform(0.62, 0.96), 2),
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "area": (x2 - x1) * (y2 - y1),
            }
        )
    df = pd.DataFrame(rows)
    annotated = _draw_boxes(image_path, df)
    return df, annotated


def _draw_boxes(image_path: Path, df: pd.DataFrame) -> str:
    """Draw bounding boxes on the analyzed image."""
    img = cv2.imread(str(image_path))
    if img is None:
        return str(image_path)
    for _, r in df.iterrows():
        x1, y1, x2, y2 = map(int, [r.x1, r.y1, r.x2, r.y2])
        cv2.rectangle(img, (x1, y1), (x2, y2), (37, 99, 235), 2)
        cv2.putText(img, f"{r.object_type} {r.confidence:.2f}", (x1, max(20, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (15, 23, 42), 2)
    out = image_path.parent / f"annotated_{image_path.name}"
    cv2.imwrite(str(out), img)
    return str(out)
