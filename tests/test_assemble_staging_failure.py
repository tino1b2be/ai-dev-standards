"""Tests for ``run_assemble`` staging-phase failure — R7.2, R7.4.

Pre-populate ``<target>/.kiro/steering/`` with a fixture set, monkeypatch
``shutil.copy2`` on the script module so the second call raises
``OSError("disk full")``, and assert:

* Return code is ``1``.
* Fixture contents are byte-for-byte unchanged.
* No ``.partial-*`` or ``.backup-*`` residue remains.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests._assemble_helpers import build_pack_repo, list_partial_or_backup


def test_staging_copy_failure_leaves_target_untouched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, script
) -> None:
    repo_root, target, _sources = build_pack_repo(
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
    fixtures = {
        "fixture-a.md": b"fixture A content\n",
        "fixture-b.md": b"fixture B content\n",
    }
    for name, data in fixtures.items():
        (final / name).write_bytes(data)

    original_copy2 = script.shutil.copy2
    call_count = {"n": 0}

    def flaky_copy2(src, dst, *args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 2:
            raise OSError("disk full")
        return original_copy2(src, dst, *args, **kwargs)

    monkeypatch.setattr(script.shutil, "copy2", flaky_copy2)

    rc = script.run_assemble(repo_root, "test-pack", target, force=True)
    assert rc == 1

    # Fixture contents unchanged byte-for-byte.
    for name, data in fixtures.items():
        assert (final / name).read_bytes() == data

    assert list_partial_or_backup(target) == []
