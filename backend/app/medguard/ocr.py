"""Pluggable OCR. Output is ALWAYS a list of candidates the user must confirm (never auto-saved)."""
import io
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from app.config import settings
from app.medguard.engine import KnowledgeBase, Resolution, get_kb


@dataclass
class OcrResult:
    text: str
    confidence: float  # 0-1 mean word confidence


class OcrProvider(Protocol):
    name: str

    def read(self, image_bytes: bytes) -> OcrResult: ...


class NoopOcr:
    name = "none"

    def read(self, image_bytes: bytes) -> OcrResult:
        raise RuntimeError("OCR is not enabled. Set OCR_PROVIDER=tesseract (Docker image includes it) or paste the text.")


class TesseractOcr:
    name = "tesseract"

    def read(self, image_bytes: bytes) -> OcrResult:
        import pytesseract  # lazy: optional dependency
        from PIL import Image, ImageEnhance, ImageFilter, ImageOps

        if not shutil.which("tesseract") and not Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe").exists():
            raise RuntimeError("Tesseract OCR is not installed. Install it or upload a PDF/text document.")
        if not shutil.which("tesseract"):
            pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        scale = 2 if max(img.size) < 2400 else 1
        if scale > 1:
            img = img.resize((img.width * scale, img.height * scale))
        gray = ImageOps.grayscale(img)
        enhanced = ImageEnhance.Contrast(gray).enhance(1.8).filter(ImageFilter.SHARPEN)
        variants = (img, enhanced, enhanced.point(lambda pixel: 255 if pixel > 180 else 0))
        best_words: list[tuple[str, float]] = []
        for variant in variants:
            for psm in (6, 11):
                data = pytesseract.image_to_data(variant, lang="eng", config=f"--psm {psm}", output_type=pytesseract.Output.DICT)
                words = [(w.strip(), float(c)) for w, c in zip(data["text"], data["conf"], strict=False) if w.strip() and float(c) >= 0]
                if len(words) > len(best_words):
                    best_words = words
        words = best_words
        conf = (sum(c for _, c in words) / len(words) / 100) if words else 0.0
        return OcrResult(" ".join(w for w, _ in words), round(conf, 2))


def get_provider() -> OcrProvider:
    return TesseractOcr() if settings.ocr_provider == "tesseract" else NoopOcr()


def extract_candidates(text: str, ocr_confidence: float = 1.0, kb: KnowledgeBase | None = None) -> list[Resolution]:
    """Split OCR/pasted text into lines and resolve each to a candidate medicine."""
    kb = kb or get_kb()
    seen: set[str] = set()
    out: list[Resolution] = []
    for line in [ln for chunk in text.splitlines() for ln in chunk.split(",")]:
        res = kb.resolve(line)
        if res.product_key and res.product_key not in seen:
            seen.add(res.product_key)
            res.confidence = round(res.confidence * ocr_confidence, 2)
            out.append(res)
    return out
