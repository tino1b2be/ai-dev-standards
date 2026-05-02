"""End-to-end smoke tests for every v1 pack — R6.1, R7.2, R17.4.

Each test invokes the real ``scripts/assemble-pack.py`` as a subprocess
against the real repo contents (``core/``, ``steering/``, ``tools/``,
``packs/``) and asserts:

* Exit code ``0``.
* Every basename declared by the pack manifest is present under
  ``<tmpdir>/.kiro/steering/``.

Unlike the focused unit tests, these exercise the CLI end-to-end: argparse,
script loading, YAML parsing, staging, and commit all run in a real process.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "assemble-pack.py"

V1_PACKS = [
    "aws-serverless-api-python",
    "aws-event-driven-workflow",
    "frontend-web-typescript",
]


def _expected_basenames(pack_name: str) -> set[str]:
    """Return the set of destination basenames declared by a pack's manifest."""

    manifest_path = REPO_ROOT / "packs" / pack_name / "manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    sources: list[str] = list(manifest["foundational"]) + list(manifest["files"])
    return {Path(source).name for source in sources}


@pytest.mark.parametrize("pack_name", V1_PACKS)
def test_pack_assembles_end_to_end(pack_name: str, tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "assemble",
            "--pack",
            pack_name,
            "--target",
            str(tmp_path),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, (
        f"assemble for {pack_name} exited {completed.returncode}\n"
        f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
    )

    steering_dir = tmp_path / ".kiro" / "steering"
    assert steering_dir.is_dir(), (
        f"{steering_dir} was not created by assemble for {pack_name}"
    )

    actual_basenames = {p.name for p in steering_dir.iterdir() if p.is_file()}
    expected_basenames = _expected_basenames(pack_name)
    assert actual_basenames == expected_basenames, (
        f"pack {pack_name}: "
        f"missing={sorted(expected_basenames - actual_basenames)}, "
        f"unexpected={sorted(actual_basenames - expected_basenames)}"
    )
