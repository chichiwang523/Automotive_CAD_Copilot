from __future__ import annotations

import re
from pathlib import Path

from .schemas import DrawingDocument


DIMENSION_RE = re.compile(r"\b(?:R|M|SR|S?O|DIA)?\s*\d+(?:[.,]\d+)?\s*(?:(?:\+/-|\+-)\s*\d+(?:[.,]\d+)?)?", re.I)
SURFACE_RE = re.compile(r"\bR[azq]\s*\d+(?:[.,]\d+)?\b", re.I)
GDT_RE = re.compile(r"(?:\||FLATNESS|POSITION|PROFILE|PARALLEL|PERPENDICULAR|RUNOUT|CONCENTRIC|SYMMETRY).{0,80}", re.I)


def load_text_sidecar(path: Path) -> str:
    """Load OCR text from a .txt sidecar when image OCR is unavailable."""
    sidecar = path.with_suffix(".txt")
    if sidecar.exists():
        return sidecar.read_text(encoding="utf-8", errors="ignore")
    if path.suffix.lower() == ".txt":
        return path.read_text(encoding="utf-8", errors="ignore")
    return ""


def extract_document(path: Path) -> DrawingDocument:
    text = load_text_sidecar(path)
    normalized = re.sub(r"[ \t]+", " ", text)
    lines = [line.strip() for line in normalized.splitlines() if line.strip()]

    title_lines = [
        line for line in lines
        if any(key in line.lower() for key in ["scale", "revision", "rev", "material", "part", "drawing", "iso"])
    ]
    notes = [line for line in lines if line.lower().startswith(("note", "notes", "general"))]

    return DrawingDocument(
        source_path=path,
        ocr_text=normalized,
        title_block_text="\n".join(title_lines[-20:]),
        notes=notes,
        dimensions=DIMENSION_RE.findall(normalized),
        gd_t_frames=GDT_RE.findall(normalized),
        surface_texture_notes=SURFACE_RE.findall(normalized),
    )
