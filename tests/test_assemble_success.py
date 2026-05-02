"""Tests for ``run_assemble`` success paths — R6.1, R7.2, R17.4.

Covers:

* Minimal synthetic pack assembles into an empty target.
* Every listed source lands at ``<target>/.kiro/steering/<basename>`` with
  byte-for-byte identical content.
* No ``.partial-*`` or ``.backup-*`` residue remains after a success.
* Target with a pre-existing but empty ``.kiro/steering/`` is also a success
  path and preserves byte-for-byte equality.
"""

from __future__ import annotations

from pathlib import Path

from tests._assemble_helpers import build_pack_repo, list_partial_or_backup


def _bytes(tag: str, idx: int) -> bytes:
    return f"# {tag} {idx}\nbody line for {tag} {idx}\n".encode("utf-8")


def _standard_pack(tmp_path: Path):
    return build_pack_repo(
        tmp_path,
        foundational={
            "tools/kiro/foundational/product.md": _bytes("product", 1),
            "tools/kiro/foundational/tech.md": _bytes("tech", 2),
        },
        files={
            "steering/security.md": _bytes("security", 3),
            "core/languages/python.md": _bytes("python", 4),
        },
    )


def test_assemble_into_empty_target_succeeds(tmp_path: Path, script) -> None:
    repo_root, target, sources = _standard_pack(tmp_path)

    rc = script.run_assemble(repo_root, "test-pack", target, force=False)
    assert rc == 0

    final = target / ".kiro" / "steering"
    assert final.is_dir()

    for rel, data in sources.items():
        dest = final / Path(rel).name
        assert dest.is_file(), f"missing {dest}"
        assert dest.read_bytes() == data, f"content drift for {dest}"

    assert list_partial_or_backup(target) == []


def test_assemble_with_pre_existing_empty_steering_succeeds(
    tmp_path: Path, script
) -> None:
    repo_root, target, sources = _standard_pack(tmp_path)

    pre = target / ".kiro" / "steering"
    pre.mkdir(parents=True)

    rc = script.run_assemble(repo_root, "test-pack", target, force=False)
    assert rc == 0

    for rel, data in sources.items():
        dest = pre / Path(rel).name
        assert dest.is_file()
        assert dest.read_bytes() == data

    assert list_partial_or_backup(target) == []
