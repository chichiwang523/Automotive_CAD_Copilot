# CAD Copilot

CAD Copilot is a starter project for automotive 2D CAD drawing review. It combines OCR/layout extraction, deterministic checklist rules, and a trainable vision-language reviewer for ISO GPS/GD&T style drawing checks.

## What This First Version Covers

- A public standards index in `configs/standards.yaml`.
- Public dataset pointers in `configs/datasets.yaml`.
- A review CLI that works today from OCR text or `.txt` sidecars.
- A JSONL format for your internal reviewed drawings.
- A training entrypoint stub for Qwen2.5-VL/InternVL style supervised fine-tuning.

ISO and ASME standards are copyrighted, so this repository stores identifiers and review focus only. Put licensed internal checklist text in a private config overlay.

## Install

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

For image OCR and model training:

```powershell
python -m pip install -e ".[ocr,train,dev]"
```

## Run A Review

Create or export OCR text next to a drawing, then run:

```powershell
cdcopilot review path\to\drawing.txt --output reports\drawing.review.json
```

The current extractor is intentionally conservative. It accepts text sidecars now, and the next OCR adapter should plug in PaddleOCR, Tesseract, or a document VLM depending on your deployment constraints.

## Frontend Prototype

The MD engineer review UI is in `web/`. It supports drawing upload, checklist upload, Pass/Fail/Open review status, evidence notes, and CSV/JSON export.

Run it locally:

```powershell
python -m http.server 4173 --directory web
```

Open:

```text
http://127.0.0.1:4173
```

Checklist files can be CSV, TSV, or TXT tables. Recommended columns:

```csv
id,standard,checklist,severity
CL-001,ISO 1101,"Feature control frame contains symbol, tolerance value, and datum references.",High
```

## Internal Training Data Format

Prepare a CSV with these columns:

```csv
image_or_pdf,checklist_id,pass_fail,evidence_bbox,reviewer_comment
part_001.pdf,datum_defined_before_use,fail,"120,300,80,40","Datum C is referenced but not defined."
```

Convert it:

```powershell
python scripts\prepare_internal_dataset.py --csv data\raw\internal\reviews.csv
```

Then start from the training recipe:

```powershell
python scripts\train_vision_reviewer.py --train-jsonl data\processed\internal_reviews.jsonl
```

## Recommended Model Architecture

Use a hybrid system, not only one end-to-end model:

1. OCR/layout layer: detects title block, notes, dimensions, feature control frames, surface texture symbols, datums, and balloons.
2. Symbol and entity parser: normalizes GD&T frames, datum references, tolerances, and drawing metadata into structured JSON.
3. Rule engine: deterministic ISO/internal checklist checks with evidence.
4. Vision-language reviewer: handles fuzzy cases, ambiguous notes, visual context, and missing/incorrect annotation patterns.
5. Human review UI: shows the finding, cited evidence, crop/bounding box, checklist item, confidence, and suggested correction.

For a small internal pilot, fine-tune a 7B vision-language model with LoRA on your reviewed drawings. For production, expand to thousands of labeled findings and keep the rule engine as a guardrail.

## Public Data Sources To Evaluate

- TriView2CAD: multi-view CAD drawing research data, useful for layout and projection understanding.
- ABC Dataset: CAD models that can be rendered into synthetic drawings with known geometry.
- DeepCAD: CAD command data useful for synthetic geometry and drafting pretraining.
- USPTO patent drawings: useful only as auxiliary OCR/layout data, not GD&T compliance.

Download public dataset indexes/repos:

```powershell
python scripts\download_datasets.py --id trview2cad --id deepcad
```

Always verify upstream license terms before internal or commercial use.
