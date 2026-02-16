"""Extract pedigree payloads from QR images, photos, and text-like files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import cv2
import numpy as np
from PIL import Image

from src.pedigree_builder import load_json_payload


def decode_qr_from_image(path: str) -> str:
    image = Image.open(path)
    image_np = np.array(image)
    try:
        from pyzbar.pyzbar import decode

        decoded = decode(image_np)
        if decoded:
            return decoded[0].data.decode("utf-8")
    except Exception:
        pass

    detector = cv2.QRCodeDetector()
    data, _, _ = detector.detectAndDecode(image_np)
    if data:
        return data
    raise ValueError("No QR code detected")


def extract_text_from_image(path: str) -> str:
    image = cv2.imread(path)
    if image is None:
        raise FileNotFoundError(path)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    thresholded = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    try:
        import pytesseract

        text = pytesseract.image_to_string(thresholded)
        if not text.strip():
            raise ValueError("No text recognized via OCR")
        return text
    except Exception as exc:
        raise ValueError(f"OCR extraction failed: {exc}") from exc


def parse_payload_from_text(text: str) -> Dict[str, Any]:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in text payload")
    payload = text[start : end + 1]
    return load_json_payload(payload)


def extract_pedigree_from_upload(file_path: str) -> Dict[str, Any]:
    suffix = Path(file_path).suffix.lower()

    if suffix in {".png", ".jpg", ".jpeg", ".bmp"}:
        try:
            qr_data = decode_qr_from_image(file_path)
            return load_json_payload(qr_data)
        except Exception:
            text = extract_text_from_image(file_path)
            return parse_payload_from_text(text)

    if suffix in {".json", ".txt", ".ged"}:
        text = Path(file_path).read_text(encoding="utf-8")
        if suffix == ".json":
            return load_json_payload(text)
        return parse_payload_from_text(text)

    raise ValueError(f"Unsupported upload type: {suffix}")


def pseudonymize_pedigree(pedigree: Dict[str, Any]) -> Dict[str, Any]:
    anonymized = json.loads(json.dumps(pedigree))
    for person in anonymized.get("people", []):
        person["name"] = f"Person-{person['id']}"
    return anonymized
