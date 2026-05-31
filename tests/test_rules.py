from pathlib import Path

from cdcopilot.ocr import extract_document
from cdcopilot.rules import load_checklist, review_document


def test_review_flags_missing_standard(tmp_path: Path) -> None:
    drawing = tmp_path / "drawing.txt"
    drawing.write_text("PART 123\nSCALE 1:1\nREV A\nMATERIAL STEEL\n10\nNOTE typical edge break\n", encoding="utf-8")

    checklist = load_checklist(Path("configs/standards.yaml"))
    report = review_document(extract_document(drawing), checklist)

    by_id = {finding.checklist_id: finding for finding in report.findings}
    assert by_id["title_block_standard"].passed is False
    assert by_id["notes_no_ambiguous_language"].passed is False


def test_review_accepts_general_tolerance(tmp_path: Path) -> None:
    drawing = tmp_path / "drawing.txt"
    drawing.write_text(
        "DRAWING STANDARD ISO 1101\nPART 123\nSCALE 1:1\nREV A\nMATERIAL AL\nGENERAL TOLERANCES ISO 2768-mK\n10\n",
        encoding="utf-8",
    )

    checklist = load_checklist(Path("configs/standards.yaml"))
    report = review_document(extract_document(drawing), checklist)

    by_id = {finding.checklist_id: finding for finding in report.findings}
    assert by_id["title_block_standard"].passed is True
    assert by_id["dimensions_have_tolerances"].passed is True
