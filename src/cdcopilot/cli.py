from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from .ocr import extract_document
from .rules import load_checklist, review_document

app = typer.Typer(help="CAD Copilot drawing review CLI")
console = Console()


@app.command()
def review(
    drawing: Path = typer.Argument(..., exists=True, help="Drawing image/PDF or OCR .txt sidecar."),
    standards: Path = typer.Option(Path("configs/standards.yaml"), help="Checklist config."),
    output: Path | None = typer.Option(None, help="Optional JSON report path."),
) -> None:
    document = extract_document(drawing)
    checklist = load_checklist(standards)
    report = review_document(document, checklist)

    table = Table(title=f"CAD Copilot review: {drawing.name}")
    table.add_column("Check")
    table.add_column("Pass")
    table.add_column("Severity")
    table.add_column("Message")
    for finding in report.findings:
        table.add_row(finding.checklist_id, "yes" if finding.passed else "no", finding.severity.value, finding.message)
    console.print(table)

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report.model_dump_json(indent=2), encoding="utf-8")
        console.print(f"Wrote {output}")


@app.command()
def extract(drawing: Path = typer.Argument(..., exists=True)) -> None:
    document = extract_document(drawing)
    console.print(json.dumps(document.model_dump(mode="json"), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    app()
