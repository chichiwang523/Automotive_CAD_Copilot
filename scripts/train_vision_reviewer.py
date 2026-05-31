from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Training entrypoint placeholder for a vision-language drawing reviewer.")
    parser.add_argument("--train-jsonl", default="data/processed/internal_reviews.jsonl")
    parser.add_argument("--base-model", default="Qwen/Qwen2.5-VL-7B-Instruct")
    parser.add_argument("--out", default="models/cdcopilot-reviewer")
    args = parser.parse_args()

    train_path = Path(args.train_jsonl)
    if not train_path.exists():
        raise FileNotFoundError(
            f"{train_path} does not exist. Run scripts/prepare_internal_dataset.py with your reviewed drawings first."
        )

    print("Training recipe:")
    print(f"  base model: {args.base_model}")
    print(f"  train data: {train_path}")
    print(f"  output dir: {args.out}")
    print("")
    print("Next implementation step: plug this JSONL into a Qwen2.5-VL/InternVL LoRA SFT trainer.")
    print("For production, keep deterministic checklist rules as a guardrail around model predictions.")


if __name__ == "__main__":
    main()
