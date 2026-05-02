"""Tests for ``load_manifest`` — R5.2, R5.6.

Covers every failure mode for the pack manifest schema:

* Valid manifest with all required fields round-trips into a ``PackManifest``.
* Each required field missing individually raises ``ManifestError``.
* Unknown top-level field raises ``ManifestError`` naming the field.
* Malformed YAML raises ``ManifestError``.
* Non-mapping top-level document raises ``ManifestError``.
* Field type mismatches (non-string ``name``, non-list ``foundational``,
  non-string entries inside list fields) all raise ``ManifestError``.
* Missing manifest file raises ``ManifestError``.
"""

from __future__ import annotations

from pathlib import Path

import pytest


def _valid_manifest_text() -> str:
    return (
        "name: my-pack\n"
        "version: 0.1.0\n"
        "description: Example pack.\n"
        "foundational:\n"
        "  - tools/kiro/foundational/product.md\n"
        "files:\n"
        "  - steering/security.md\n"
    )


def test_valid_manifest_parses_all_fields(tmp_path: Path, script) -> None:
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(_valid_manifest_text(), encoding="utf-8")

    result = script.load_manifest(manifest_path)

    assert isinstance(result, script.PackManifest)
    assert result.name == "my-pack"
    assert result.version == "0.1.0"
    assert result.description == "Example pack."
    assert result.foundational == ["tools/kiro/foundational/product.md"]
    assert result.files == ["steering/security.md"]


@pytest.mark.parametrize(
    "missing_field",
    ["name", "version", "description", "foundational", "files"],
)
def test_missing_required_field_raises(
    tmp_path: Path, script, missing_field: str
) -> None:
    import yaml

    data = yaml.safe_load(_valid_manifest_text())
    del data[missing_field]
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(yaml.safe_dump(data), encoding="utf-8")

    with pytest.raises(script.ManifestError) as exc_info:
        script.load_manifest(manifest_path)

    assert "missing required field" in str(exc_info.value)
    assert missing_field in str(exc_info.value)


def test_unknown_field_raises(tmp_path: Path, script) -> None:
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(
        _valid_manifest_text() + "extra: foo\n", encoding="utf-8"
    )

    with pytest.raises(script.ManifestError) as exc_info:
        script.load_manifest(manifest_path)

    message = str(exc_info.value)
    assert "unknown field" in message
    assert "extra" in message


def test_malformed_yaml_raises(tmp_path: Path, script) -> None:
    manifest_path = tmp_path / "manifest.yaml"
    # Unbalanced braces + a leading colon produce a YAML scanner error.
    manifest_path.write_text(": bad\n  indent: {[\n", encoding="utf-8")

    with pytest.raises(script.ManifestError) as exc_info:
        script.load_manifest(manifest_path)

    assert "invalid YAML" in str(exc_info.value)


def test_non_mapping_top_level_raises(tmp_path: Path, script) -> None:
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text("- list\n- items\n", encoding="utf-8")

    with pytest.raises(script.ManifestError) as exc_info:
        script.load_manifest(manifest_path)

    assert "YAML mapping" in str(exc_info.value)


def test_name_must_be_string(tmp_path: Path, script) -> None:
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(
        _valid_manifest_text().replace("name: my-pack", "name: 42"),
        encoding="utf-8",
    )

    with pytest.raises(script.ManifestError) as exc_info:
        script.load_manifest(manifest_path)

    message = str(exc_info.value)
    assert "'name'" in message
    assert "must be a string" in message


def test_foundational_must_be_list(tmp_path: Path, script) -> None:
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(
        "name: my-pack\n"
        "version: 0.1.0\n"
        "description: Example.\n"
        "foundational: not-a-list\n"
        "files:\n"
        "  - steering/security.md\n",
        encoding="utf-8",
    )

    with pytest.raises(script.ManifestError) as exc_info:
        script.load_manifest(manifest_path)

    message = str(exc_info.value)
    assert "'foundational'" in message
    assert "must be a list" in message


def test_files_entry_must_be_string(tmp_path: Path, script) -> None:
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(
        "name: my-pack\n"
        "version: 0.1.0\n"
        "description: Example.\n"
        "foundational: []\n"
        "files:\n"
        "  - 42\n",
        encoding="utf-8",
    )

    with pytest.raises(script.ManifestError) as exc_info:
        script.load_manifest(manifest_path)

    message = str(exc_info.value)
    assert "'files'" in message
    assert "must be a string" in message


def test_missing_manifest_file_raises(tmp_path: Path, script) -> None:
    manifest_path = tmp_path / "does-not-exist.yaml"

    with pytest.raises(script.ManifestError) as exc_info:
        script.load_manifest(manifest_path)

    assert "not found" in str(exc_info.value)
