"""Tests for ``run_assemble --force`` double-fault — R7.2, R7.4.

The force-non-empty branch calls ``os.rename`` twice:

  1. ``os.rename(final, backup)`` — moves the existing directory aside.
  2. ``os.rename(backup, final)`` — rollback after a failed commit.

The first call must succeed so the backup exists; the second must fail so we
exercise the double-fault path. The test uses a counter-based monkeypatch.

Assert:

* Return code is ``1``.
* Backup directory ``<target>/.kiro/steering.backup-*`` still exists and
  contains the original fixtures byte-for-byte.
* Error message on stderr names the backup path so the user can recover.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests._assemble_helpers import build_pack_repo


def test_commit_and_rollback_both_fail_preserves_backup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    script,
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
        "fixture-a.md": b"fixture A bytes\n",
        "fixture-b.md": b"fixture B bytes\n",
    }
    for name, data in fixtures.items():
        (final / name).write_bytes(data)

    def failing_replace(src, dst):
        raise OSError("commit failed")

    real_rename = script.os.rename
    rename_calls = {"n": 0}

    def flaky_rename(src, dst):
        rename_calls["n"] += 1
        if rename_calls["n"] == 1:
            # Move-aside before the commit: must succeed so backup exists.
            return real_rename(src, dst)
        # Rollback attempt: force a double fault.
        raise OSError("rollback failed")

    monkeypatch.setattr(script.os, "replace", failing_replace)
    monkeypatch.setattr(script.os, "rename", flaky_rename)

    rc = script.run_assemble(repo_root, "test-pack", target, force=True)
    assert rc == 1

    # Backup must survive and contain the original fixtures byte-for-byte.
    kiro = target / ".kiro"
    backups = [p for p in kiro.iterdir() if p.name.startswith("steering.backup-")]
    assert len(backups) == 1, f"expected 1 backup, found {backups}"
    backup = backups[0]
    for name, data in fixtures.items():
        assert (backup / name).read_bytes() == data

    captured = capsys.readouterr()
    assert str(backup) in captured.err
