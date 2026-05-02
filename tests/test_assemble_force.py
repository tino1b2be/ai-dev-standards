"""Tests for ``run_assemble --force`` success path — R7.2, R7.4.

Pre-populate ``<target>/.kiro/steering/`` with fixtures whose basenames
differ from the manifest, run assemble with ``force=True``, and assert:

* Return code is ``0``.
* Final directory contains exactly the manifest's resolved basenames.
* Pre-existing fixture files are gone.
* No ``.partial-*`` or ``.backup-*`` residue remains.
"""

from __future__ import annotations

from pathlib import Path

from tests._assemble_helpers import build_pack_repo, list_partial_or_backup


def test_force_replaces_existing_non_empty_steering(
    tmp_path: Path, script
) -> None:
    repo_root, target, sources = build_pack_repo(
        tmp_path,
        foundational={
            "tools/kiro/foundational/product.md": b"# product\n",
        },
        files={
            "steering/security.md": b"# security\n",
            "core/languages/python.md": b"# python\n",
        },
    )

    final = target / ".kiro" / "steering"
    final.mkdir(parents=True)
    (final / "old-fixture-1.md").write_bytes(b"stale content 1\n")
    (final / "old-fixture-2.md").write_bytes(b"stale content 2\n")
    (final / "notes.txt").write_bytes(b"unrelated fixture\n")

    rc = script.run_assemble(repo_root, "test-pack", target, force=True)
    assert rc == 0

    expected_basenames = {Path(rel).name for rel in sources}
    actual_basenames = {p.name for p in final.iterdir()}
    assert actual_basenames == expected_basenames

    for rel, data in sources.items():
        assert (final / Path(rel).name).read_bytes() == data

    assert list_partial_or_backup(target) == []
