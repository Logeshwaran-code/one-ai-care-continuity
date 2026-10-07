"""Pluggable OCR. Output is ALWAYS a list of candidates the user must confirm (never auto-saved)."""
import io
from dataclasses import dataclass
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
        from PIL import Image

        img = Image.open(io.BytesIO(image_bytes))
        data = pytesseract.image_to_data(img, lang="eng", output_type=pytesseract.Output.DICT)
        words = [(w, float(c)) for w, c in zip(data["text"], data["conf"], strict=False) if w.strip() and float(c) >= 0]
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
