from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
import os

REPO_ROOT = Path(os.environ.get('SPS_REPO_ROOT', r"C:\Copilot_projects\SPS"))
TEST_DIR = REPO_ROOT / "testing" / "regression_test"
CATALOG_PATH = TEST_DIR / "regression-test-catalog.md"
MERMAID_PATH = TEST_DIR / "regression-test-dependencies.mmd"
EXCLUDED_TEST_DOCS = {
    "README.md",
    "regression-test-catalog.md",
}


@dataclass(frozen=True)
class TestDocMeta:
    path: str
    title: str
    test_id: str
    catalog_key: str
    summary: str
    dependencies: tuple[str, ...]


@dataclass(frozen=True)
class CatalogEntry:
    catalog_key: str
    dependencies: tuple[str, ...]
    test_id: str
    summary: str
    file_path: str


def to_rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT)).replace("/", "\\")


def section_value(markdown: str, heading: str) -> str | None:
    pattern = rf"^## {re.escape(heading)}\s*$\n+(.*?)(?=^\#\# |\Z)"
    match = re.search(pattern, markdown, flags=re.MULTILINE | re.DOTALL)
    if not match:
        return None
    return match.group(1).strip()


def normalize_inline(text: str) -> str:
    return text.strip().strip("`").strip()


def parse_dependencies(raw: str | None, current_key: str) -> tuple[str, ...]:
    if raw is None:
        return tuple()

    dependencies: list[str] = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped.startswith("-"):
            continue
        value = stripped[1:].strip()
        if value.lower() in {"none", "-"}:
            continue

        key_match = re.search(r"`([^`]+)`", value)
        if key_match:
            dep = normalize_inline(key_match.group(1))
        else:
            dep = normalize_inline(value.split("/", 1)[0])

        if dep and dep != current_key:
            dependencies.append(dep)

    return tuple(dict.fromkeys(dependencies))


def parse_test_doc(path: Path) -> TestDocMeta:
    text = path.read_text(encoding="utf-8")
    title_match = re.search(r"^#\s+(.+)$", text, flags=re.MULTILINE)
    if not title_match:
        raise ValueError(f"{to_rel(path)} is missing a top-level title.")

    test_id = section_value(text, "Test-ID")
    catalog_key = section_value(text, "Catalog Key")
    summary = section_value(text, "Summary")

    if not test_id:
        raise ValueError(f"{to_rel(path)} is missing ## Test-ID.")
    if not catalog_key:
        raise ValueError(f"{to_rel(path)} is missing ## Catalog Key.")
    if not summary:
        raise ValueError(f"{to_rel(path)} is missing ## Summary.")

    normalized_key = normalize_inline(catalog_key.splitlines()[0])
    dependencies = parse_dependencies(section_value(text, "Dependencies"), normalized_key)

    return TestDocMeta(
        path=to_rel(path),
        title=title_match.group(1).strip(),
        test_id=normalize_inline(test_id.splitlines()[0]),
        catalog_key=normalized_key,
        summary=" ".join(summary.split()),
        dependencies=dependencies,
    )


def collect_test_docs() -> list[TestDocMeta]:
    docs: list[TestDocMeta] = []
    for path in sorted(TEST_DIR.glob("*.md"), key=lambda p: p.name.casefold()):
        if path.name in EXCLUDED_TEST_DOCS:
            continue
        text = path.read_text(encoding="utf-8")
        if not text.startswith("# Regressionstest - "):
            continue
        docs.append(parse_test_doc(path))
    return docs


def parse_catalog() -> dict[str, CatalogEntry]:
    text = CATALOG_PATH.read_text(encoding="utf-8")
    entries: dict[str, CatalogEntry] = {}

    for line in text.splitlines():
        if not line.startswith("| `"):
            continue

        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 5:
            continue

        key = normalize_inline(cells[0])
        dependency_cell = cells[1]
        test_id = normalize_inline(cells[2])
        summary = " ".join(cells[3].split())
        file_path = normalize_inline(cells[4])

        dependency_tokens = re.findall(r"\b[A-Z][A-Z0-9_-]*\b", dependency_cell)
        dependencies = tuple(token for token in dependency_tokens if token != key)

        entries[key] = CatalogEntry(
            catalog_key=key,
            dependencies=dependencies,
            test_id=test_id,
            summary=summary,
            file_path=file_path,
        )

    return entries


def parse_mermaid() -> tuple[set[str], set[tuple[str, str]]]:
    text = MERMAID_PATH.read_text(encoding="utf-8")
    nodes = set(re.findall(r"^\s*([A-Z][A-Z0-9_-]*)\s*\[", text, flags=re.MULTILINE))
    edges = {
        (source, target)
        for source, target in re.findall(
            r"^\s*([A-Z][A-Z0-9_-]*)\s*-->\s*([A-Z][A-Z0-9_-]*)\s*$",
            text,
            flags=re.MULTILINE,
        )
    }
    return nodes, edges


def main() -> int:
    errors: list[str] = []
    docs = collect_test_docs()
    catalog = parse_catalog()
    mermaid_nodes, mermaid_edges = parse_mermaid()

    doc_by_key: dict[str, TestDocMeta] = {}
    doc_by_path: dict[str, TestDocMeta] = {}

    for doc in docs:
        if doc.catalog_key in doc_by_key:
            errors.append(
                f"Duplicate Catalog Key '{doc.catalog_key}' in {doc_by_key[doc.catalog_key].path} and {doc.path}."
            )
            continue
        if doc.path in doc_by_path:
            errors.append(f"Duplicate test path '{doc.path}'.")
            continue
        doc_by_key[doc.catalog_key] = doc
        doc_by_path[doc.path] = doc

    for key, doc in doc_by_key.items():
        entry = catalog.get(key)
        if not entry:
            errors.append(f"{doc.path} with Catalog Key '{key}' is missing from regression-test-catalog.md.")
            continue
        if entry.file_path != doc.path:
            errors.append(f"Catalog path mismatch for '{key}': catalog has '{entry.file_path}', doc is '{doc.path}'.")
        if entry.test_id != doc.test_id:
            errors.append(f"Test-ID mismatch for '{key}': catalog '{entry.test_id}' vs doc '{doc.test_id}'.")
        if entry.summary != doc.summary:
            errors.append(f"Summary mismatch for '{key}'.")
        if entry.dependencies != doc.dependencies:
            errors.append(
                f"Dependency mismatch for '{key}': catalog {entry.dependencies or ('-',)} vs doc {doc.dependencies or ('-',)}."
            )

    for key, entry in catalog.items():
        if key not in doc_by_key:
            errors.append(f"Catalog entry '{key}' points to missing regression test metadata doc '{entry.file_path}'.")
        else:
            doc_path = REPO_ROOT / entry.file_path
            if not doc_path.exists():
                errors.append(f"Catalog entry '{key}' points to non-existing file '{entry.file_path}'.")

    expected_nodes = set(catalog.keys())
    expected_edges = {(dep, key) for key, entry in catalog.items() for dep in entry.dependencies}

    missing_nodes = sorted(expected_nodes - mermaid_nodes)
    extra_nodes = sorted(mermaid_nodes - expected_nodes)
    missing_edges = sorted(expected_edges - mermaid_edges)
    extra_edges = sorted(mermaid_edges - expected_edges)

    if missing_nodes:
        errors.append(f"Mermaid file is missing nodes for: {', '.join(missing_nodes)}.")
    if extra_nodes:
        errors.append(f"Mermaid file has extra nodes not present in the catalog: {', '.join(extra_nodes)}.")
    if missing_edges:
        errors.append(
            "Mermaid file is missing edges for: "
            + ", ".join(f"{source}->{target}" for source, target in missing_edges)
            + "."
        )
    if extra_edges:
        errors.append(
            "Mermaid file has extra edges not present in the catalog: "
            + ", ".join(f"{source}->{target}" for source, target in extra_edges)
            + "."
        )

    if errors:
        print("Regression dependency synchronization errors:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(
        "Regression test metadata, catalog, and Mermaid dependencies are synchronized "
        f"({len(doc_by_key)} tests)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
