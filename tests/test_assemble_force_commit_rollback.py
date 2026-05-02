"""Tests for ``run_assemble --force`` commit failure with rollback — R7.2, R7.4.

Pre-populate ``<target>/.kiro/steering/`` with fixtures (basenames differ
from the manifest). Monkeypatch ``os.replace`` on the script module to raise
``OSError("commit failed")`` (the commit step). Rollback uses ``os.rename``,
which is left untouched.

Assert:

* Return code is ``1``.
* Fixture contents are byte-for-byte restored.
* No ``.partial-*`` or ``.backup-*`` residue remains.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests._assemble_helpers import build_pack_repo, list_partial_or_backup


def test_commit_failure_rolls_back_fixtures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, script
) -> None:
    repo_root, target, _sources = build_pack_repo(
        tmp_path,
        foundational={"tools/kiro/foundational/product.md": b"# product\n"},
        files={
            "steering/security.md": b"# security\n",
            "core/languages/python.md": b"# python\n",
        },
    )

    final = target / ".kiro" / "steering"
    final.mkdir(parents=True)
    fixtures = {
        "legacy-a.md": b"legacy A\n",
        "legacy-b.md": b"legacy B\n",
    }
    for name, data in fixtures.items():
        (final / name).write_bytes(data)

    def failing_replace(src, dst):
        raise OSError("commit failed")

    monkeypatch.setattr(script.os, "replace", failing_replace)

    rc = script.run_assemble(repo_root, "test-pack", target, force=True)
    assert rc == 1

    # Fixture contents restored byte-for-byte at the original final path.
    assert final.is_dir()
    for name, data in fixtures.items():
        assert (final / name).read_bytes() == data

    # No residue — staging removed and backup renamed back into place.
    assert list_partial_or_backup(target) == []
