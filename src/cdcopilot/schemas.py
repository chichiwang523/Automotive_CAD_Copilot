from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class BBox(BaseModel):
    x: float
    y: float
    width: float
    height: float


class OcrToken(BaseModel):
    text: str
    confidence: float = 0.0
    bbox: BBox | None = None


class DrawingDocument(BaseModel):
    source_path: Path
    ocr_text: str = ""
    tokens: list[OcrToken] = Field(default_factory=list)
    title_block_text: str = ""
    notes: list[str] = Field(default_factory=list)
    dimensions: list[str] = Field(default_factory=list)
    gd_t_frames: list[str] = Field(default_factory=list)
    surface_texture_notes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReviewFinding(BaseModel):
    checklist_id: str
    passed: bool
    severity: Severity
    message: str
    evidence: list[str] = Field(default_factory=list)


class ReviewReport(BaseModel):
    drawing: str
    findings: list[ReviewFinding]

    @property
    def passed(self) -> bool:
        return all(f.passed for f in self.findings)
