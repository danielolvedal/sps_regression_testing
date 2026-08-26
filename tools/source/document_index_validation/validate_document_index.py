from __future__ import annotations

import re
import sys
from pathlib import Path


REPO_ROOT = Path(r"C:\Copilot_projects\SPS")
INDEX_PATH = REPO_ROOT / "dokument_index" / "index.md"
TRACKED_EXTENSIONS = {".md", ".mmd", ".txt", ".json", ".pdf", ".docx", ".xlsx"}
EXCLUDED_DIRS = {"tmp"}
EXCLUDED_PATHS = {
    Path(r"manuals\user_manuals"),
    Path(r"manuals\client_manuals"),
    Path(r"test_reports"),
}


def to_rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT)).replace("/", "\\")


def should_track(path: Path) -> bool:
    rel = path.relative_to(REPO_ROOT)
    if any(part in EXCLUDED_DIRS for part in rel.parts):
        return False
    if any(rel == excluded or excluded in rel.parents for excluded in EXCLUDED_PATHS):
        return False
    return path.is_file() and path.suffix.lower() in TRACKED_EXTENSIONS


def collect_repo_documents() -> list[str]:
    return sorted(
        [to_rel(path) for path in REPO_ROOT.rglob("*") if should_track(path)],
        key=str.casefold,
    )


def collect_indexed_paths(index_text: str) -> set[str]:
    matches = re.findall(r"`([^`]+)`", index_text)
    return {match for match in matches if "\\" in match or match.endswith(".md")}


def main() -> int:
    index_text = INDEX_PATH.read_text(encoding="utf-8")
    repo_docs = collect_repo_documents()
    indexed = collect_indexed_paths(index_text)
    missing = [path for path in repo_docs if path not in indexed]

    if missing:
        print("Missing documents/data files in dokument_index\\index.md:")
        for path in missing:
            print(f"- {path}")
        return 1

    print(f"All tracked documentation/data files are indexed ({len(repo_docs)} files).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
