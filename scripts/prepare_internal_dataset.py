from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert internal checklist CSV into JSONL training records.")
    parser.add_argument("--csv", required=True, help="CSV with image_or_pdf, checklist_id, pass_fail, reviewer_comment columns.")
    parser.add_argument("--out", default="data/processed/internal_reviews.jsonl")
    args = parser.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with Path(args.csv).open("r", encoding="utf-8-sig", newline="") as f_in, out.open("w", encoding="utf-8") as f_out:
        reader = csv.DictReader(f_in)
        required = {"image_or_pdf", "checklist_id", "pass_fail", "reviewer_comment"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"missing columns: {sorted(missing)}")
        for row in reader:
            record = {
                "image": row["image_or_pdf"],
                "instruction": f"Check drawing item {row['checklist_id']} and cite evidence.",
                "label": row["pass_fail"].strip().lower(),
                "comment": row["reviewer_comment"].strip(),
                "evidence_bbox": row.get("evidence_bbox", "").strip(),
            }
            f_out.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
