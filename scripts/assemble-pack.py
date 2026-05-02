#!/usr/bin/env python3
"""assemble-pack.py — reusable-ai-dev-standards-library assembly script.

Copies a pack's files into a consumer's ``<target>/.kiro/steering/``, validates
pack manifests, syncs the consumer ``steering/`` catalog from ``core/steering/``,
and scans tracked files for sensitive data.

Subcommands:

* ``assemble`` — copy the files named by a pack manifest into a target directory.
* ``validate`` — check every ``packs/*/manifest.yaml`` for well-formedness.
* ``sync-steering`` — regenerate ``steering/<topic>.md`` from ``core/steering/``
  (maintainer-only; supports ``--check`` for CI drift detection).
* ``scan`` — run the sensitive-data regex set over ``git ls-files`` output.
* ``check-all`` — run ``validate`` + ``sync-steering --check`` + ``scan``.

Runtime: Python 3.12+. Dependencies: ``pyyaml`` (stdlib otherwise).

See ``.kiro/specs/reusable-ai-dev-standards-library/design.md`` for the full
specification of each mode. Mode bodies are implemented in Task 5.
"""

from __future__ import annotations

import argparse
import os
import re
import secrets
import shutil
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


# ---------------------------------------------------------------------------
# Front-matter map (Task 4.2)
# ---------------------------------------------------------------------------

STEERING_FRONT_MATTER: dict[str, str] = {
    "core/steering/security.md":       "---\ninclusion: always\n---\n",
    "core/steering/repo-standards.md": "---\ninclusion: always\n---\n",
    "core/steering/cicd.md":           "---\ninclusion: always\n---\n",
    "core/steering/api-standards.md":  "---\ninclusion: always\n---\n",
}

DEFAULT_FRONT_MATTER = "---\ninclusion: always\n---\n"


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class ManifestError(Exception):
    """Raised when a pack manifest fails validation or cannot be parsed."""


class AssembleError(Exception):
    """Raised when an assemble operation fails (I/O, rollback, etc.)."""


# ---------------------------------------------------------------------------
# Pack manifest (Task 4.3)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PackManifest:
    """In-memory representation of a ``packs/<name>/manifest.yaml`` file."""

    name: str
    version: str
    description: str
    foundational: list[str]
    files: list[str]


_REQUIRED_FIELDS: tuple[str, ...] = (
    "name",
    "version",
    "description",
    "foundational",
    "files",
)


def load_manifest(manifest_path: Path) -> PackManifest:
    """Load and validate a pack manifest from ``manifest_path``.

    Parses the YAML file with ``yaml.safe_load`` and enforces the minimal
    schema described in the design document:

    * Top-level value is a mapping.
    * All required fields present: ``name``, ``version``, ``description``,
      ``foundational``, ``files``.
    * No unknown fields.
    * ``name``, ``version``, ``description`` are strings.
    * ``foundational`` and ``files`` are lists of strings.

    Raises :class:`ManifestError` with a descriptive message on any failure.
    """

    if not manifest_path.is_file():
        raise ManifestError(f"manifest not found: {manifest_path}")

    try:
        raw_text = manifest_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ManifestError(
            f"could not read manifest {manifest_path}: {exc}"
        ) from exc

    try:
        data: Any = yaml.safe_load(raw_text)
    except yaml.YAMLError as exc:
        raise ManifestError(f"invalid YAML in {manifest_path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ManifestError(
            f"manifest {manifest_path} must be a YAML mapping at the top level, "
            f"got {type(data).__name__}"
        )

    missing = [field for field in _REQUIRED_FIELDS if field not in data]
    if missing:
        raise ManifestError(
            f"manifest {manifest_path} is missing required field(s): "
            f"{', '.join(missing)}"
        )

    unknown = sorted(set(data.keys()) - set(_REQUIRED_FIELDS))
    if unknown:
        raise ManifestError(
            f"manifest {manifest_path} has unknown field(s): {', '.join(unknown)}"
        )

    for field in ("name", "version", "description"):
        value = data[field]
        if not isinstance(value, str):
            raise ManifestError(
                f"manifest {manifest_path} field '{field}' must be a string, "
                f"got {type(value).__name__}"
            )

    for field in ("foundational", "files"):
        value = data[field]
        if not isinstance(value, list):
            raise ManifestError(
                f"manifest {manifest_path} field '{field}' must be a list, "
                f"got {type(value).__name__}"
            )
        for index, entry in enumerate(value):
            if not isinstance(entry, str):
                raise ManifestError(
                    f"manifest {manifest_path} field '{field}' entry at index "
                    f"{index} must be a string, got {type(entry).__name__}"
                )

    return PackManifest(
        name=data["name"],
        version=data["version"],
        description=data["description"],
        foundational=list(data["foundational"]),
        files=list(data["files"]),
    )


# ---------------------------------------------------------------------------
# Basename collision detection (Task 4.4)
# ---------------------------------------------------------------------------


def detect_basename_collisions(manifest: PackManifest) -> list[tuple[str, str]]:
    """Return pairs of source paths that share a destination basename.

    Every entry in ``foundational`` and ``files`` lands at
    ``<target>/.kiro/steering/<basename>``. If two distinct source paths share
    a basename the destination file would be overwritten, so these pairs are
    reported before any I/O happens.

    For each group of N paths (N > 1) sharing a basename, a single
    representative pair ``(paths[0], paths[1])`` is returned. An empty list
    means no collisions.
    """

    grouped: dict[str, list[str]] = defaultdict(list)
    for source_path in list(manifest.foundational) + list(manifest.files):
        basename = Path(source_path).name
        grouped[basename].append(source_path)

    collisions: list[tuple[str, str]] = []
    for paths in grouped.values():
        if len(paths) > 1:
            collisions.append((paths[0], paths[1]))
    return collisions


# ---------------------------------------------------------------------------
# Staging and backup paths (Task 4.5)
# ---------------------------------------------------------------------------


def build_staging_path(target_kiro_steering: Path) -> Path:
    """Return a sibling staging directory path for atomic-move assembly.

    The returned path is ``<target>/.kiro/steering.partial-<suffix>`` where
    ``<suffix>`` comes from ``secrets.token_hex(4)``. The staging directory is
    a sibling of the final destination so the eventual commit rename stays on
    the same filesystem. The path is *not* created here — callers create it
    when they are ready to stage. ``tempfile`` is deliberately avoided because
    it may land on a different filesystem and break atomicity.
    """

    suffix = secrets.token_hex(4)
    return target_kiro_steering.parent / f"{target_kiro_steering.name}.partial-{suffix}"


def build_backup_path(target_kiro_steering: Path) -> Path:
    """Return a sibling backup directory path used during ``--force`` replacement.

    The returned path is ``<target>/.kiro/steering.backup-<suffix>`` where
    ``<suffix>`` comes from ``secrets.token_hex(4)``. Only created when
    ``assemble --force`` needs to displace a non-empty existing destination.
    Same filesystem as the final destination so the rename-aside is atomic.
    """

    suffix = secrets.token_hex(4)
    return target_kiro_steering.parent / f"{target_kiro_steering.name}.backup-{suffix}"


# ---------------------------------------------------------------------------
# Mode: validate (Task 5.1)
# ---------------------------------------------------------------------------


def run_validate(repo_root: Path) -> int:
    """Validate every ``packs/*/manifest.yaml``.

    Accumulates errors across all packs and prints each on its own line to
    stderr. Returns ``0`` if every manifest is well-formed, consistent with
    its directory name, references only existing files, and has no basename
    collisions; returns ``1`` otherwise.
    """

    packs_dir = repo_root / "packs"
    errors: list[str] = []

    if not packs_dir.is_dir():
        print(f"error: packs directory not found: {packs_dir}", file=sys.stderr)
        return 1

    pack_dirs = sorted(p for p in packs_dir.iterdir() if p.is_dir())
    for pack_dir in pack_dirs:
        manifest_path = pack_dir / "manifest.yaml"
        if not manifest_path.is_file():
            # Empty pack dir (e.g., skeleton before Task 6). Skip silently:
            # validate only flags malformed manifests, not missing ones.
            continue

        try:
            manifest = load_manifest(manifest_path)
        except ManifestError as exc:
            errors.append(str(exc))
            continue

        if manifest.name != pack_dir.name:
            errors.append(
                f"manifest {manifest_path}: name '{manifest.name}' does not "
                f"match pack directory '{pack_dir.name}'"
            )

        for source_path in list(manifest.foundational) + list(manifest.files):
            absolute = repo_root / source_path
            if not absolute.is_file():
                errors.append(
                    f"manifest {manifest_path}: referenced file does not "
                    f"exist: {source_path}"
                )

        for left, right in detect_basename_collisions(manifest):
            errors.append(
                f"manifest {manifest_path}: basename collision between "
                f"'{left}' and '{right}' (both resolve to "
                f"'{Path(left).name}')"
            )

    for message in errors:
        print(f"error: {message}", file=sys.stderr)
    return 0 if not errors else 1


# ---------------------------------------------------------------------------
# Mode: sync-steering (Task 5.2 / 5.3)
# ---------------------------------------------------------------------------


def _expected_steering_bytes(repo_root: Path, core_rel: str) -> bytes:
    """Compute the expected ``steering/<topic>.md`` bytes for a core source."""

    front_matter = STEERING_FRONT_MATTER.get(core_rel, DEFAULT_FRONT_MATTER)
    core_bytes = (repo_root / core_rel).read_bytes()
    return front_matter.encode("utf-8") + b"\n" + core_bytes


def run_sync_steering(repo_root: Path, check: bool) -> int:
    """Regenerate or check ``steering/`` against ``core/steering/``.

    When ``check`` is ``False`` (write path), every ``core/steering/<topic>.md``
    is rendered into ``steering/<topic>.md`` as
    ``front_matter + "\\n" + core_bytes`` (byte-for-byte).

    When ``check`` is ``True``, the expected bytes are computed the same way
    and compared byte-for-byte against what is on disk. Missing or drifted
    files and extras under ``steering/`` without a ``core/steering/``
    counterpart are all reported to stderr; the function returns ``1`` if any
    drift is found and ``0`` otherwise.
    """

    core_steering = repo_root / "core" / "steering"
    consumer_steering = repo_root / "steering"

    if not core_steering.is_dir():
        print(
            f"error: core steering directory not found: {core_steering}",
            file=sys.stderr,
        )
        return 1

    topics = sorted(p for p in core_steering.glob("*.md") if p.is_file())

    if not check:
        consumer_steering.mkdir(parents=True, exist_ok=True)
        for topic_path in topics:
            core_rel = f"core/steering/{topic_path.name}"
            expected = _expected_steering_bytes(repo_root, core_rel)
            (consumer_steering / topic_path.name).write_bytes(expected)
        return 0

    # check mode
    drifts: list[str] = []
    expected_names: set[str] = set()
    for topic_path in topics:
        core_rel = f"core/steering/{topic_path.name}"
        expected = _expected_steering_bytes(repo_root, core_rel)
        consumer_file = consumer_steering / topic_path.name
        expected_names.add(topic_path.name)
        if not consumer_file.is_file():
            drifts.append(
                f"steering/{topic_path.name}: missing (expected from "
                f"{core_rel})"
            )
            continue
        actual = consumer_file.read_bytes()
        if actual != expected:
            drifts.append(
                f"steering/{topic_path.name}: drifted from {core_rel}"
            )

    if consumer_steering.is_dir():
        for entry in sorted(consumer_steering.glob("*.md")):
            if entry.is_file() and entry.name not in expected_names:
                drifts.append(
                    f"steering/{entry.name}: extra file with no "
                    f"core/steering/ counterpart"
                )

    for message in drifts:
        print(message, file=sys.stderr)
    return 0 if not drifts else 1


# ---------------------------------------------------------------------------
# Mode: scan (Task 5.4)
# ---------------------------------------------------------------------------


_SENTINEL_ACCOUNT_ID = "000000000000"

_EMAIL_ALLOWLIST_DOMAINS: frozenset[str] = frozenset(
    {
        "example.com",
        "example.org",
        "example.net",
        "users.noreply.github.com",
    }
)

_GITHUB_HANDLE_ALLOWLIST: frozenset[str] = frozenset(
    {"YOUR_GITHUB_USERNAME", "example", "actions", "github"}
)

_SENSITIVE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "aws_arn_with_account",
        re.compile(r"arn:aws:[^:\s]+:[^:\s]*:(\d{12}):"),
    ),
    (
        "aws_access_key_id",
        re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    ),
    (
        "bare_account_id",
        re.compile(r"\b(\d{12})\b"),
    ),
    (
        "personal_email",
        re.compile(r"\b[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b"),
    ),
    (
        "github_handle",
        re.compile(r"github\.com/([A-Za-z0-9][A-Za-z0-9-]*)/"),
    ),
]

_SCAN_SKIP_PREFIXES: tuple[str, ...] = (
    "scripts/assemble-pack.py",
    ".kiro/specs/",
    "tests/fixtures/",
)


def _match_is_excluded(name: str, match: re.Match[str]) -> bool:
    """Return True if a regex match falls under an exclusion (allowlist / sentinel)."""

    if name == "aws_arn_with_account":
        return match.group(1) == _SENTINEL_ACCOUNT_ID
    if name == "bare_account_id":
        return match.group(1) == _SENTINEL_ACCOUNT_ID
    if name == "personal_email":
        domain = match.group(1).lower()
        if domain in _EMAIL_ALLOWLIST_DOMAINS:
            return True
        if domain.endswith(".example.com"):
            return True
        return False
    if name == "github_handle":
        return match.group(1) in _GITHUB_HANDLE_ALLOWLIST
    return False


def _is_probably_text(path: Path) -> bool:
    """Best-effort binary/text sniff. Reads a small prefix and checks for NULs."""

    try:
        with path.open("rb") as fh:
            chunk = fh.read(8192)
    except OSError:
        return False
    if b"\x00" in chunk:
        return False
    return True


def run_scan(repo_root: Path) -> int:
    """Scan ``git ls-files`` output for sensitive-data patterns.

    Skips this script, ``.kiro/specs/`` content (which documents the patterns
    themselves), and ``tests/fixtures/`` (which may deliberately contain bad
    strings). Emits ``<file>:<line>: pattern <name>`` per match and returns
    ``1`` if any match survives the allowlist.
    """

    try:
        completed = subprocess.run(
            ["git", "ls-files"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        print("error: git not found on PATH", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        print(
            f"error: git ls-files failed ({exc.returncode}): "
            f"{exc.stderr.strip()}",
            file=sys.stderr,
        )
        return 1

    hits: list[str] = []
    for rel in completed.stdout.splitlines():
        rel = rel.strip()
        if not rel:
            continue
        if any(rel == prefix or rel.startswith(prefix) for prefix in _SCAN_SKIP_PREFIXES):
            continue
        absolute = repo_root / rel
        if not absolute.is_file():
            continue
        if not _is_probably_text(absolute):
            continue
        try:
            text = absolute.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            for name, pattern in _SENSITIVE_PATTERNS:
                for match in pattern.finditer(line):
                    if _match_is_excluded(name, match):
                        continue
                    hits.append(f"{rel}:{lineno}: pattern {name}")

    for message in hits:
        print(message, file=sys.stderr)
    return 0 if not hits else 1


# ---------------------------------------------------------------------------
# Mode: assemble (Task 5.5)
# ---------------------------------------------------------------------------


def _assemble_pre_write_plan(
    repo_root: Path, pack_name: str, target: Path, force: bool
) -> tuple[PackManifest, Path, str]:
    """Validate the plan before any I/O.

    Returns ``(manifest, final, state)`` where ``state`` is one of:

    * ``"no-existing"`` — ``final`` does not exist yet.
    * ``"empty-existing"`` — ``final`` exists and is an empty directory.
    * ``"force-non-empty"`` — ``final`` exists, is non-empty, and ``--force``
      was passed.

    Raises :class:`ManifestError` or :class:`AssembleError` on any failure.
    """

    manifest_path = repo_root / "packs" / pack_name / "manifest.yaml"
    manifest = load_manifest(manifest_path)

    missing_sources: list[str] = []
    for source_path in list(manifest.foundational) + list(manifest.files):
        if not (repo_root / source_path).is_file():
            missing_sources.append(source_path)
    if missing_sources:
        raise AssembleError(
            f"manifest {manifest_path} references missing source file(s): "
            f"{', '.join(missing_sources)}"
        )

    collisions = detect_basename_collisions(manifest)
    if collisions:
        left, right = collisions[0]
        raise AssembleError(
            f"manifest {manifest_path}: basename collision between "
            f"'{left}' and '{right}' (both resolve to "
            f"'{Path(left).name}')"
        )

    if not target.exists():
        raise AssembleError(f"target directory does not exist: {target}")
    if not target.is_dir():
        raise AssembleError(f"target is not a directory: {target}")

    final = target / ".kiro" / "steering"
    if not final.exists():
        state = "no-existing"
    elif not final.is_dir():
        raise AssembleError(
            f"destination exists but is not a directory: {final}"
        )
    else:
        try:
            has_any = any(final.iterdir())
        except OSError as exc:
            raise AssembleError(
                f"could not read destination {final}: {exc}"
            ) from exc
        if not has_any:
            state = "empty-existing"
        elif force:
            state = "force-non-empty"
        else:
            raise AssembleError(
                f"{final} is non-empty and --force was not passed"
            )

    return manifest, final, state


def run_assemble(
    repo_root: Path, pack_name: str, target: Path, force: bool
) -> int:
    """Assemble a pack into ``<target>/.kiro/steering/`` atomically.

    Implements the stage-and-atomic-move commit flow from design.md:

    1. Pre-write plan — validate manifest, referenced sources exist, no
       basename collisions, target state matches ``--force`` expectation.
    2. Stage — copy each source into a sibling ``steering.partial-<suffix>``
       directory via :func:`shutil.copy2`.
    3. Commit — one of three branches: no-existing, empty-existing, or
       force-non-empty (with backup-aside, commit, and rollback on failure).

    Returns ``0`` on success, ``1`` on failure. A leftover backup after a
    successful ``--force`` commit is the only non-fatal warning case.
    """

    try:
        manifest, final, state = _assemble_pre_write_plan(
            repo_root, pack_name, target, force
        )
    except (ManifestError, AssembleError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    staging = build_staging_path(final)
    final.parent.mkdir(parents=True, exist_ok=True)

    # Stage
    try:
        staging.mkdir()
        for source_path in list(manifest.foundational) + list(manifest.files):
            src = repo_root / source_path
            dest = staging / Path(source_path).name
            shutil.copy2(src, dest)
    except OSError as exc:
        shutil.rmtree(staging, ignore_errors=True)
        print(
            f"error: staging failed while copying into {staging}: {exc}",
            file=sys.stderr,
        )
        return 1

    # Commit
    if state == "no-existing":
        try:
            os.replace(staging, final)
        except OSError as exc:
            shutil.rmtree(staging, ignore_errors=True)
            print(
                f"error: commit failed for {final}: {exc}",
                file=sys.stderr,
            )
            return 1
        return 0

    if state == "empty-existing":
        try:
            final.rmdir()
            os.replace(staging, final)
        except OSError as exc:
            shutil.rmtree(staging, ignore_errors=True)
            print(
                f"error: commit failed for {final}: {exc}",
                file=sys.stderr,
            )
            return 1
        return 0

    # state == "force-non-empty"
    backup = build_backup_path(final)
    try:
        os.rename(final, backup)
    except OSError as exc:
        shutil.rmtree(staging, ignore_errors=True)
        print(
            f"error: could not move existing {final} aside to {backup}: "
            f"{exc}",
            file=sys.stderr,
        )
        return 1

    try:
        os.replace(staging, final)
    except OSError as commit_exc:
        # Attempt rollback.
        try:
            os.rename(backup, final)
        except OSError as rollback_exc:
            print(
                f"error: commit failed for {final}: {commit_exc}; "
                f"rollback also failed: {rollback_exc}; "
                f"your original contents are preserved at {backup} — "
                f"rename that directory back to {final} manually to recover",
                file=sys.stderr,
            )
            shutil.rmtree(staging, ignore_errors=True)
            return 1
        shutil.rmtree(staging, ignore_errors=True)
        print(
            f"error: commit failed for {final}: {commit_exc}; "
            f"rollback succeeded (original contents restored from {backup})",
            file=sys.stderr,
        )
        return 1

    # Commit succeeded; remove backup. Failure here is a non-fatal warning.
    try:
        shutil.rmtree(backup)
    except OSError as exc:
        print(
            f"warning: assemble succeeded but could not remove backup "
            f"directory {backup}: {exc} (safe to delete manually)",
            file=sys.stderr,
        )
        return 0
    return 0


# ---------------------------------------------------------------------------
# Mode: check-all (Task 5.6)
# ---------------------------------------------------------------------------


def run_check_all(repo_root: Path) -> int:
    """Run ``validate``, ``sync-steering --check``, and ``scan`` in sequence.

    Each phase runs to completion regardless of earlier failures so the
    maintainer sees every problem in one pass. Returns ``0`` only if all
    three phases return ``0``.
    """

    print("=== validate ===", file=sys.stderr)
    validate_rc = run_validate(repo_root)

    print("=== sync-steering --check ===", file=sys.stderr)
    sync_rc = run_sync_steering(repo_root, check=True)

    print("=== scan ===", file=sys.stderr)
    scan_rc = run_scan(repo_root)

    return 0 if (validate_rc == 0 and sync_rc == 0 and scan_rc == 0) else 1


# ---------------------------------------------------------------------------
# CLI (Task 4.1)
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argparse parser with all subcommands."""

    parser = argparse.ArgumentParser(
        prog="assemble-pack.py",
        description=(
            "Assemble and validate ai-dev-standards packs. "
            "See .kiro/specs/reusable-ai-dev-standards-library/design.md."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", metavar="command")

    assemble_parser = subparsers.add_parser(
        "assemble",
        help="Copy the files named by a pack manifest into <target>/.kiro/steering/.",
    )
    assemble_parser.add_argument(
        "--pack",
        required=True,
        help="Name of the pack under packs/ to assemble.",
    )
    assemble_parser.add_argument(
        "--target",
        required=True,
        help="Target project directory (must already exist).",
    )
    assemble_parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing non-empty <target>/.kiro/steering/ directory.",
    )

    subparsers.add_parser(
        "validate",
        help="Validate every packs/*/manifest.yaml.",
    )

    sync_parser = subparsers.add_parser(
        "sync-steering",
        help="Regenerate steering/ from core/steering/ (maintainer-only).",
    )
    sync_parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if steering/ has drifted from core/steering/.",
    )

    subparsers.add_parser(
        "scan",
        help="Scan tracked files for sensitive data.",
    )

    subparsers.add_parser(
        "check-all",
        help="Run validate, then sync-steering --check, then scan.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns the process exit code."""

    parser = build_parser()
    args = parser.parse_args(argv)
    repo_root = Path(__file__).resolve().parent.parent

    try:
        if args.command == "assemble":
            return run_assemble(
                repo_root, args.pack, Path(args.target), args.force
            )
        if args.command == "validate":
            return run_validate(repo_root)
        if args.command == "sync-steering":
            return run_sync_steering(repo_root, args.check)
        if args.command == "scan":
            return run_scan(repo_root)
        if args.command == "check-all":
            return run_check_all(repo_root)
        parser.print_help()
        return 2
    except NotImplementedError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except ManifestError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except AssembleError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
