from __future__ import annotations

import re
from pathlib import Path

import yaml

from .schemas import DrawingDocument, ReviewFinding, ReviewReport, Severity


AMBIGUOUS_WORDS = re.compile(r"\b(?:typical|approx(?:\.|imately)?|as required|TBD|TBC)\b", re.I)
DATUM_DEF_RE = re.compile(r"\bdatum\s+([A-Z])\b|\[([A-Z])\]", re.I)
DATUM_USE_RE = re.compile(r"\b[A-Z]\b")
STANDARD_RE = re.compile(r"\b(?:ISO|ASME)\s*[- ]?(?:\d{3,5}|Y14\.5)\b", re.I)
TITLE_FIELD_GROUPS = {
    "scale": ["scale"],
    "revision": ["revision", "rev"],
    "material": ["material"],
    "part": ["part"],
}


def load_checklist(path: Path) -> list[dict]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data["default_checklist"]


def review_document(document: DrawingDocument, checklist: list[dict]) -> ReviewReport:
    findings: list[ReviewFinding] = []
    for item in checklist:
        check_id = item["id"]
        severity = Severity(item.get("severity", "medium"))
        passed, message, evidence = _run_check(check_id, document)
        findings.append(
            ReviewFinding(
                checklist_id=check_id,
                passed=passed,
                severity=severity,
                message=message,
                evidence=evidence,
            )
        )
    return ReviewReport(drawing=str(document.source_path), findings=findings)


def _run_check(check_id: str, document: DrawingDocument) -> tuple[bool, str, list[str]]:
    text = document.ocr_text
    title = document.title_block_text or text

    if check_id == "title_block_standard":
        evidence = STANDARD_RE.findall(title)
        return bool(evidence), "governing standard detected" if evidence else "no governing ISO/ASME standard detected", evidence

    if check_id == "title_block_scale_revision":
        lower_title = title.lower()
        found = [field for field, aliases in TITLE_FIELD_GROUPS.items() if any(alias in lower_title for alias in aliases)]
        missing = sorted(set(TITLE_FIELD_GROUPS) - set(found))
        return not missing, "required title-block fields present" if not missing else f"missing title-block fields: {', '.join(missing)}", found

    if check_id == "dimensions_have_tolerances":
        has_general_tolerance = bool(re.search(r"\b(?:ISO\s*2768|general tolerances?|tolerance unless otherwise)\b", text, re.I))
        explicit = [d for d in document.dimensions if "+/-" in d or "+-" in d]
        passed = has_general_tolerance or bool(explicit)
        return passed, "dimension tolerance basis found" if passed else "no explicit or general tolerance basis found", explicit[:20]

    if check_id == "datum_defined_before_use":
        defined = {m.group(1) or m.group(2) for m in DATUM_DEF_RE.finditer(text)}
        used = {m.group(0) for frame in document.gd_t_frames for m in DATUM_USE_RE.finditer(frame)}
        unresolved = sorted(used - defined)
        return not unresolved, "datum references resolved" if not unresolved else f"unresolved datum references: {', '.join(unresolved)}", sorted(defined)

    if check_id == "feature_control_frame_syntax":
        if not document.gd_t_frames:
            return False, "no feature control frames detected", []
        suspicious = [frame for frame in document.gd_t_frames if not re.search(r"\d", frame)]
        return not suspicious, "feature control frames contain numeric tolerances" if not suspicious else "some feature control frames lack numeric tolerances", suspicious[:10]

    if check_id == "surface_texture_syntax":
        return bool(document.surface_texture_notes), "surface texture syntax detected" if document.surface_texture_notes else "no surface texture parameter detected", document.surface_texture_notes[:20]

    if check_id == "notes_no_ambiguous_language":
        evidence = AMBIGUOUS_WORDS.findall(text)
        return not evidence, "no ambiguous note language detected" if not evidence else "ambiguous note language detected", evidence[:20]

    return True, "check not implemented yet", []
