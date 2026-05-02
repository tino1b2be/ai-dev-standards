"""Tests for ``run_sync_steering(..., check=True)`` — R14.1.

Covers the drift-detection mode:

* In-sync repo → ``0``.
* Missing ``steering/<topic>.md`` → ``1``.
* Drifted ``steering/<topic>.md`` → ``1``.
* Extra file under ``steering/`` without a ``core/steering/`` counterpart → ``1``.
"""

from __future__ import annotations

from pathlib import Path


def _expected_bytes(script, rel: str, core_bytes: bytes) -> bytes:
    front = script.STEERING_FRONT_MATTER.get(rel, script.DEFAULT_FRONT_MATTER)
    return front.encode("utf-8") + b"\n" + core_bytes


def _seed_core_topic(tmp_path: Path, topic: str, core_bytes: bytes) -> None:
    core_file = tmp_path / "core" / "steering" / topic
    core_file.parent.mkdir(parents=True, exist_ok=True)
    core_file.write_bytes(core_bytes)


def test_in_sync_returns_zero(tmp_path: Path, script) -> None:
    core_bytes = b"# Security\nbody\n"
    _seed_core_topic(tmp_path, "security.md", core_bytes)

    steering_file = tmp_path / "steering" / "security.md"
    steering_file.parent.mkdir(parents=True)
    steering_file.write_bytes(
        _expected_bytes(script, "core/steering/security.md", core_bytes)
    )

    assert script.run_sync_steering(tmp_path, check=True) == 0


def test_missing_steering_file_returns_one(tmp_path: Path, script) -> None:
    _seed_core_topic(tmp_path, "security.md", b"# Security\n")
    (tmp_path / "steering").mkdir()  # directory exists but file does not

    assert script.run_sync_steering(tmp_path, check=True) == 1


def test_drifted_steering_file_returns_one(tmp_path: Path, script) -> None:
    _seed_core_topic(tmp_path, "security.md", b"# Security\nreal body\n")

    steering_file = tmp_path / "steering" / "security.md"
    steering_file.parent.mkdir(parents=True)
    steering_file.write_bytes(b"---\ninclusion: always\n---\n\n# drifted!\n")

    assert script.run_sync_steering(tmp_path, check=True) == 1


def test_extra_file_under_steering_returns_one(tmp_path: Path, script) -> None:
    core_bytes = b"# Security\n"
    _seed_core_topic(tmp_path, "security.md", core_bytes)

    steering_dir = tmp_path / "steering"
    steering_dir.mkdir()
    # Write the in-sync file so only the extra triggers the failure.
    (steering_dir / "security.md").write_bytes(
        _expected_bytes(script, "core/steering/security.md", core_bytes)
    )
    (steering_dir / "orphan.md").write_bytes(b"---\ninclusion: always\n---\n\n")

    assert script.run_sync_steering(tmp_path, check=True) == 1
