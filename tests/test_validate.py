"""Tests for ``run_validate`` — R5.3, R7.3, R7.4.

Builds a minimal synthetic repo under ``tmp_path`` (``packs/<name>/manifest.yaml``
plus the referenced source files) and asserts the validate mode returns ``0``
for well-formed manifests and ``1`` with clear stderr messages otherwise.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml


def _write_manifest(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _seed_sources(repo: Path, rels: list[str]) -> None:
    for rel in rels:
        abs_path = repo / rel
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_bytes(f"# {rel}\n".encode("utf-8"))


def _golden_manifest_data(name: str = "my-pack") -> dict:
    return {
        "name": name,
        "version": "0.1.0",
        "description": "Example.",
        "foundational": ["tools/kiro/foundational/product.md"],
        "files": ["steering/security.md"],
    }


def test_golden_manifest_returns_zero(tmp_path: Path, script) -> None:
    data = _golden_manifest_data()
    _seed_sources(tmp_path, data["foundational"] + data["files"])
    _write_manifest(tmp_path / "packs" / data["name"] / "manifest.yaml", data)

    assert script.run_validate(tmp_path) == 0


def test_name_directory_mismatch_fails(
    tmp_path: Path, script, capsys: pytest.CaptureFixture[str]
) -> None:
    data = _golden_manifest_data(name="different-name")
    _seed_sources(tmp_path, data["foundational"] + data["files"])
    # Directory is "actual-dir" but manifest says "different-name".
    _write_manifest(tmp_path / "packs" / "actual-dir" / "manifest.yaml", data)

    rc = script.run_validate(tmp_path)
    captured = capsys.readouterr()

    assert rc == 1
    assert "different-name" in captured.err
    assert "actual-dir" in captured.err


def test_files_entry_missing_source_fails(
    tmp_path: Path, script, capsys: pytest.CaptureFixture[str]
) -> None:
    data = _golden_manifest_data()
    # Seed only the foundational file; the files entry is intentionally missing.
    _seed_sources(tmp_path, data["foundational"])
    _write_manifest(tmp_path / "packs" / data["name"] / "manifest.yaml", data)

    rc = script.run_validate(tmp_path)
    captured = capsys.readouterr()

    assert rc == 1
    assert "steering/security.md" in captured.err
    assert "does not exist" in captured.err


def test_basename_collision_fails(
    tmp_path: Path, script, capsys: pytest.CaptureFixture[str]
) -> None:
    data = {
        "name": "collision-pack",
        "version": "0.1.0",
        "description": "Example.",
        "foundational": [
            "tools/kiro/foundational/product.md",
            "other/product.md",
        ],
        "files": [],
    }
    _seed_sources(tmp_path, data["foundational"])
    _write_manifest(tmp_path / "packs" / data["name"] / "manifest.yaml", data)

    rc = script.run_validate(tmp_path)
    captured = capsys.readouterr()

    assert rc == 1
    assert "basename collision" in captured.err
    assert "tools/kiro/foundational/product.md" in captured.err
    assert "other/product.md" in captured.err


def test_unknown_field_fails(
    tmp_path: Path, script, capsys: pytest.CaptureFixture[str]
) -> None:
    data = _golden_manifest_data()
    data["extra"] = "foo"
    _seed_sources(tmp_path, data["foundational"] + data["files"])
    _write_manifest(tmp_path / "packs" / data["name"] / "manifest.yaml", data)

    rc = script.run_validate(tmp_path)
    captured = capsys.readouterr()

    assert rc == 1
    assert "unknown field" in captured.err
    assert "extra" in captured.err
