"""Tests for ``run_sync_steering`` write path — R2.2, R14.1.

Given a scratch repo root with ``core/steering/<topic>.md``, running
``run_sync_steering(repo_root, check=False)`` writes
``steering/<topic>.md`` equal to
``STEERING_FRONT_MATTER[<topic>].encode() + b"\\n" + core_bytes`` for known
topics, and uses ``DEFAULT_FRONT_MATTER`` for unmapped topics.
"""

from __future__ import annotations

from pathlib import Path


def test_known_topic_uses_mapped_front_matter(tmp_path: Path, script) -> None:
    core_bytes = b"# Security\nBody line one.\nBody line two.\n"
    core_file = tmp_path / "core" / "steering" / "security.md"
    core_file.parent.mkdir(parents=True)
    core_file.write_bytes(core_bytes)

    rc = script.run_sync_steering(tmp_path, check=False)
    assert rc == 0

    generated = (tmp_path / "steering" / "security.md").read_bytes()
    front_matter = script.STEERING_FRONT_MATTER["core/steering/security.md"]
    expected = front_matter.encode("utf-8") + b"\n" + core_bytes
    assert generated == expected


def test_unmapped_topic_uses_default_front_matter(tmp_path: Path, script) -> None:
    core_bytes = b"# Novel topic\nsome body\n"
    core_file = tmp_path / "core" / "steering" / "novel-topic.md"
    core_file.parent.mkdir(parents=True)
    core_file.write_bytes(core_bytes)

    rc = script.run_sync_steering(tmp_path, check=False)
    assert rc == 0

    generated = (tmp_path / "steering" / "novel-topic.md").read_bytes()
    expected = script.DEFAULT_FRONT_MATTER.encode("utf-8") + b"\n" + core_bytes
    assert generated == expected

    # Sanity-check: "novel-topic.md" really is not in the map.
    assert "core/steering/novel-topic.md" not in script.STEERING_FRONT_MATTER
