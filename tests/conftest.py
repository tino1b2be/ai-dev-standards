"""Shared fixtures for the ``scripts/assemble-pack.py`` test suite.

The script under test has a hyphen in its name, so it is not importable via a
normal ``import`` statement. This conftest loads it once per session under the
attribute name ``assemble_pack`` and exposes it through the ``script`` fixture.

All fixtures here are intentionally tiny. The individual test modules build
their own synthetic repo roots and pack layouts on top of ``tmp_path``.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "assemble-pack.py"


def _load_script_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("assemble_pack", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Register before exec so @dataclass on PyPy/CPython 3.14 can resolve string
    # annotations via sys.modules.get(cls.__module__).__dict__.
    sys.modules["assemble_pack"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def script() -> ModuleType:
    """The loaded ``assemble-pack`` module."""

    return _load_script_module()


@pytest.fixture
def repo_root(tmp_path: Path) -> Path:
    """An empty scratch repo root for tests that need one."""

    return tmp_path


def make_fake_repo(
    root: Path,
    core_files: dict[str, bytes] | None = None,
    packs: dict[str, dict] | None = None,
) -> Path:
    """Build a minimal synthetic repo at ``root``.

    * ``core_files`` maps repo-relative paths (e.g. ``"core/steering/x.md"``)
      to byte contents. Parent directories are created as needed.
    * ``packs`` maps pack name to a manifest dict; each manifest is written to
      ``<root>/packs/<name>/manifest.yaml`` as YAML.

    Returns ``root`` for call-site chaining.
    """

    import yaml  # local import: pyyaml is a runtime dep of the script

    if core_files:
        for rel, data in core_files.items():
            abs_path = root / rel
            abs_path.parent.mkdir(parents=True, exist_ok=True)
            abs_path.write_bytes(data)

    if packs:
        for pack_name, manifest in packs.items():
            pack_dir = root / "packs" / pack_name
            pack_dir.mkdir(parents=True, exist_ok=True)
            (pack_dir / "manifest.yaml").write_text(
                yaml.safe_dump(manifest, sort_keys=False),
                encoding="utf-8",
            )

    return root
