from __future__ import annotations

import argparse
import zipfile
import shutil
import subprocess
import urllib.request
from pathlib import Path

import yaml


def run(cmd: list[str], cwd: Path) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def clone_repo(url: str, target: Path) -> None:
    if target.exists():
        print(f"skip existing {target}")
        return
    if shutil.which("git") is not None:
        run(["git", "clone", "--depth", "1", url, str(target)], cwd=Path.cwd())
        return
    download_github_zip(url, target)


def download_github_zip(url: str, target: Path) -> None:
    parts = url.rstrip("/").removesuffix(".git").split("/")
    if len(parts) < 2:
        raise RuntimeError(f"cannot infer GitHub owner/repo from {url}")
    owner, repo = parts[-2], parts[-1]
    archive = target.with_suffix(".zip")
    branch = "master"
    for candidate in ["master", "main"]:
        zip_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{candidate}.zip"
        try:
            print(f"git not found; downloading repository zip: {zip_url}")
            urllib.request.urlretrieve(zip_url, archive)
            branch = candidate
            break
        except Exception:
            archive.unlink(missing_ok=True)
    if not archive.exists():
        raise RuntimeError(f"failed to download GitHub zip for {url}")
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(target.parent)
        extracted = target.parent / f"{repo}-{branch}"
        if extracted.exists():
            extracted.rename(target)
    archive.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download public drawing/CAD dataset indexes or repos.")
    parser.add_argument("--config", default="configs/datasets.yaml")
    parser.add_argument("--out", default="data/raw/public")
    parser.add_argument("--id", action="append", help="Dataset id to fetch. Repeatable.")
    args = parser.parse_args()

    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    selected = set(args.id or [])
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    for dataset in config["datasets"]:
        if dataset["type"] != "public":
            continue
        if selected and dataset["id"] not in selected:
            continue
        target = out / dataset["id"]
        source = dataset["source"]
        if source.endswith(".git") or "github.com" in source:
            try:
                clone_repo(source, target)
            except Exception as exc:
                target.mkdir(exist_ok=True)
                (target / "SOURCE.txt").write_text(source + "\n", encoding="utf-8")
                (target / "DOWNLOAD_ERROR.txt").write_text(str(exc) + "\n", encoding="utf-8")
                print(f"recorded source after download failure: {source}")
        else:
            target.mkdir(exist_ok=True)
            (target / "SOURCE.txt").write_text(source + "\n", encoding="utf-8")
            print(f"recorded source for manual/licensed download: {source}")


if __name__ == "__main__":
    main()
