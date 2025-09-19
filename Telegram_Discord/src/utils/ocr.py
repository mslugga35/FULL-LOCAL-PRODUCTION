import os
from typing import Optional

try:
    from google.cloud import vision
except Exception:
    vision = None

def ocr_enabled() -> bool:
    return bool(os.getenv("GOOGLE_APPLICATION_CREDENTIALS")) and vision is not None

def extract_text_from_image(file_path: str) -> Optional[str]:
    if not ocr_enabled() or not file_path or not os.path.exists(file_path):
        return None
    client = vision.ImageAnnotatorClient()
    with open(file_path, "rb") as f:
        image = vision.Image(content=f.read())
    resp = client.text_detection(image=image)
    if resp and resp.text_annotations:
        return (resp.text_annotations[0].description or "").strip()
    return None