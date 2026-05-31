from __future__ import annotations

import csv
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .ocr import extract_document
from .rules import review_document

app = FastAPI(title="CAD Copilot API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "CAD Copilot"}


@app.post("/review")
async def review(drawing: UploadFile = File(...), checklist: UploadFile = File(...)) -> dict:
    with TemporaryDirectory() as tmp:
        drawing_path = Path(tmp) / drawing.filename
        drawing_path.write_bytes(await drawing.read())
        checklist_items = _read_checklist(await checklist.read())
        document = extract_document(drawing_path)
        report = review_document(document, checklist_items)
        return report.model_dump(mode="json")


def _read_checklist(raw: bytes) -> list[dict]:
    text = raw.decode("utf-8-sig")
    sample = text[:2048]
    dialect = csv.Sniffer().sniff(sample, delimiters=",\t")
    rows = list(csv.DictReader(text.splitlines(), dialect=dialect))
    checklist = []
    for index, row in enumerate(rows, start=1):
        checklist.append(
            {
                "id": row.get("id") or row.get("checklist_id") or f"CL-{index:03d}",
                "severity": (row.get("severity") or "medium").lower(),
                "description": row.get("checklist") or row.get("description") or "",
                "evidence": row.get("evidence") or "",
            }
        )
    return checklist
