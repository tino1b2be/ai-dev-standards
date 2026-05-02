"""Shared helpers for the assemble-mode test modules.

These helpers build a minimal synthetic repo and target layout under
``tmp_path``. They intentionally live outside ``conftest.py`` to keep the
fixture surface lean.
"""

from __future__ import annotations

from pathlib import Path

import yaml


def build_pack_repo(
    tmp_path: Path,
    pack_name: str = "test-pack",
    *,
    foundational: dict[str, bytes] | None = None,
    files: dict[str, bytes] | None = None,
) -> tuple[Path, Path, dict[str, bytes]]:
    """Build a minimal repo with one pack and return (repo_root, target, sources).

    * ``foundational`` and ``files`` map source-relative paths (e.g.
      ``"tools/kiro/foundational/product.md"``) to byte contents.
    * The manifest is written at
      ``<repo>/packs/<pack_name>/manifest.yaml``.
    * A clean target directory (empty) is created at ``<tmp>/target``.
    * ``sources`` is the merged dict for byte-for-byte comparisons.
    """

    foundational = foundational or {}
    files = files or {}

    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    sources: dict[str, bytes] = {}
    for rel, data in {**foundational, **files}.items():
        abs_path = repo_root / rel
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_bytes(data)
        sources[rel] = data

    pack_dir = repo_root / "packs" / pack_name
    pack_dir.mkdir(parents=True)
    manifest = {
        "name": pack_name,
        "version": "0.1.0",
        "description": "Test pack.",
        "foundational": list(foundational.keys()),
        "files": list(files.keys()),
    }
    (pack_dir / "manifest.yaml").write_text(
        yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8"
    )

    target = tmp_path / "target"
    target.mkdir()

    return repo_root, target, sources


def list_partial_or_backup(target: Path) -> list[Path]:
    """Return any ``.partial-*`` or ``.backup-*`` siblings of ``.kiro/steering/``."""

    kiro = target / ".kiro"
    if not kiro.is_dir():
        return []
    return [
        p
        for p in kiro.iterdir()
        if p.name.startswith("steering.partial-")
        or p.name.startswith("steering.backup-")
    ]
