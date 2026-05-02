"""Tests for ``run_assemble`` rejecting non-empty target without --force — R7.2, R7.4.

Pre-populate ``<target>/.kiro/steering/`` with a non-empty fixture, run
assemble with ``force=False``, and assert:

* Return code is ``1``.
* Fixture file still present and unmodified.
* No staging (``.partial-*``) or backup (``.backup-*``) directories exist.
"""

from __future__ import annotations

from pathlib import Path

from tests._assemble_helpers import build_pack_repo, list_partial_or_backup


def test_noforce_rejects_non_empty_target(tmp_path: Path, script) -> None:
    repo_root, target, _sources = build_pack_repo(
        tmp_path,
        foundational={"tools/kiro/foundational/product.md": b"# product\n"},
        files={"steering/security.md": b"# security\n"},
    )

    final = target / ".kiro" / "steering"
    final.mkdir(parents=True)
    fixture_path = final / "pre-existing.md"
    fixture_bytes = b"pre-existing content\n"
    fixture_path.write_bytes(fixture_bytes)

    rc = script.run_assemble(repo_root, "test-pack", target, force=False)
    assert rc == 1

    # Fixture is unchanged.
    assert fixture_path.is_file()
    assert fixture_path.read_bytes() == fixture_bytes

    # No residue.
    assert list_partial_or_backup(target) == []
