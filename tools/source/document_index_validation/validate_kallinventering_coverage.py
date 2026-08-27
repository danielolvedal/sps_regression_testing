from __future__ import annotations

import fnmatch
import re
import sys
from pathlib import Path
import os

REPO_ROOT = Path(os.environ.get('SPS_REPO_ROOT', r"C:\Copilot_projects\SPS"))
RAW_DATA_DIR = REPO_ROOT / "raw_data"
INVENTORY_PATH = REPO_ROOT / "syntetisk_data" / "common" / "kallinventering.md"
TRACKED_EXTENSIONS = {".md", ".txt", ".json", ".pdf", ".docx", ".xlsx"}
ANALYSIS_PREFIXES = ("Uppdaterad", "Analyserad - ingen ytterligare påverkan")


def to_rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT)).replace("/", "\\")


def should_track(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in TRACKED_EXTENSIONS


def collect_raw_data_files() -> list[str]:
    return sorted(
        [to_rel(path) for path in RAW_DATA_DIR.rglob("*") if should_track(path)],
        key=str.casefold,
    )


def extract_source_patterns(text: str) -> list[str]:
    match = re.search(r"## Källor\s*(.*?)(?:\n## |\Z)", text, flags=re.DOTALL)
    if not match:
        raise ValueError("Hittade ingen '## Källor'-sektion i kallinventering.md.")

    section = match.group(1)
    patterns = sorted(
        {value for value in re.findall(r"`(raw_data\\[^`]+)`", section)},
        key=str.casefold,
    )
    if not patterns:
        raise ValueError("Hittade inga raw_data-referenser i '## Källor'-sektionen.")
    return patterns


def extract_table_rows(text: str) -> list[list[str]]:
    match = re.search(r"## Data, objekt och regler\s*(.*?)(?:\n## |\Z)", text, flags=re.DOTALL)
    if not match:
        raise ValueError("Hittade ingen '## Data, objekt och regler'-sektion i kallinventering.md.")

    rows: list[list[str]] = []
    for line in match.group(1).splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if not cells or cells[0] == "Källa" or set("".join(cells)) <= {"-", " ", ":"}:
            continue
        rows.append(cells)
    return rows


def matches(pattern: str, candidate: str) -> bool:
    return fnmatch.fnmatchcase(candidate.casefold(), pattern.casefold())


def normalize_source_pattern(value: str) -> str:
    source = value.strip().strip("`")
    if not source.startswith("raw_data\\"):
        source = f"raw_data\\{source}"
    return source


def extract_doc_paths(cell: str) -> list[str]:
    return sorted(set(re.findall(r"(syntetisk_data\\[^`\s|]+\.md)", cell)), key=str.casefold)


def doc_mentions_source(doc_text: str, source_pattern: str, matched_raw_files: list[str]) -> bool:
    if source_pattern in doc_text:
        return True
    return any(raw_file in doc_text for raw_file in matched_raw_files)


def main() -> int:
    inventory_text = INVENTORY_PATH.read_text(encoding="utf-8")
    raw_files = collect_raw_data_files()
    patterns = extract_source_patterns(inventory_text)
    table_rows = extract_table_rows(inventory_text)

    missing = [
        raw_file
        for raw_file in raw_files
        if not any(matches(pattern, raw_file) for pattern in patterns)
    ]
    stale = [
        pattern
        for pattern in patterns
        if not any(matches(pattern, raw_file) for raw_file in raw_files)
    ]
    traceability_errors: list[str] = []

    row_map: list[tuple[str, list[str], str, str]] = []
    for row in table_rows:
        if len(row) < 6:
            traceability_errors.append(
                "Tabellen i 'Data, objekt och regler' måste ha sex kolumner: "
                "Källa, Huvudvärde, Begränsning, Rekommenderad användning, "
                "Påverkade syntetiska dokument, Analysutfall."
            )
            continue

        source_pattern = normalize_source_pattern(row[0])
        impacted_docs_cell = row[4]
        analysis_cell = row[5]
        matched_raw_files = [raw_file for raw_file in raw_files if matches(source_pattern, raw_file)]
        if not matched_raw_files:
            continue
        row_map.append((source_pattern, matched_raw_files, impacted_docs_cell, analysis_cell))

        if not any(analysis_cell.startswith(prefix) for prefix in ANALYSIS_PREFIXES):
            traceability_errors.append(
                f"{source_pattern}: Analysutfall måste börja med "
                "'Uppdaterad' eller 'Analyserad - ingen ytterligare påverkan'."
            )

        impacted_docs = extract_doc_paths(impacted_docs_cell)
        if analysis_cell.startswith("Uppdaterad"):
            if not impacted_docs:
                traceability_errors.append(
                    f"{source_pattern}: markerad som Uppdaterad men saknar spårade syntetiska dokument."
                )
            for doc_path in impacted_docs:
                doc_file = REPO_ROOT / doc_path
                if not doc_file.is_file():
                    traceability_errors.append(f"{source_pattern}: utpekat dokument saknas: {doc_path}")
                    continue
                doc_text = doc_file.read_text(encoding="utf-8")
                if not doc_mentions_source(doc_text, source_pattern, matched_raw_files):
                    traceability_errors.append(
                        f"{source_pattern}: {doc_path} refererar inte till källan i dokumenttexten."
                    )
        elif not impacted_docs_cell.lower().startswith("ingen ytterligare påverkan"):
            traceability_errors.append(
                f"{source_pattern}: Påverkade syntetiska dokument måste ange dokumentvägar eller börja med "
                "'Ingen ytterligare påverkan'."
            )

    for raw_file in raw_files:
        if not any(raw_file in matched for _, matched, _, _ in row_map):
            traceability_errors.append(
                f"{raw_file}: saknar rad i tabellen 'Data, objekt och regler' för påverkan/analys."
            )

    if missing or stale or traceability_errors:
        if missing:
            print("raw_data-filer som saknas i syntetisk_data\\common\\kallinventering.md:")
            for path in missing:
                print(f"- {path}")
        if stale:
            if missing:
                print()
            print("Källreferenser i kallinventering.md som inte matchar någon raw_data-fil:")
            for pattern in stale:
                print(f"- {pattern}")
        if traceability_errors:
            if missing or stale:
                print()
            print("Spårbarhets-/påverkansfel i kallinventering.md:")
            for error in traceability_errors:
                print(f"- {error}")
        return 1

    print(
        "All tracked raw_data files are covered and traceable via kallinventering.md "
        f"({len(raw_files)} files, {len(patterns)} source entries, {len(table_rows)} analysis rows)."
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ValueError as exc:
        print(str(exc))
        sys.exit(1)
