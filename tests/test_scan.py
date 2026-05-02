"""Tests for ``run_scan`` — R8.1, R8.2, R8.3, R8.4.

Builds an ephemeral git repo under ``tmp_path``, ``git add``s fixture files
so ``git ls-files`` returns them, and asserts:

* A repo containing ONLY placeholder / sentinel / allowlisted strings scans
  clean (rc == 0, no stderr hits).
* A repo containing each known-bad string scans dirty (rc == 1, stderr names
  the offending file and pattern).

Skipped if ``git`` is not on ``PATH``.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    shutil.which("git") is None, reason="git not on PATH"
)


GOOD_LINES = [
    "arn:aws:s3:::000000000000:bucket/foo",
    "YOUR_ACCOUNT_ID",
    "000000000000",
    "user@example.com",
    "alerts@api.example.com",
    "github.com/YOUR_GITHUB_USERNAME/project",
]

BAD_CASES: list[tuple[str, str, str]] = [
    (
        "arn.md",
        "arn:aws:lambda:us-east-1:123456789012:function:MyFunc\n",
        "aws_arn_with_account",
    ),
    ("akia.md", "AKIAIOSFODNN7EXAMPLE\n", "aws_access_key_id"),
    ("account.md", "account id 987654321098 follows\n", "bare_account_id"),
    ("email.md", "contact alice@realperson.com\n", "personal_email"),
    ("gh.md", "see github.com/realuser/someproject for details\n", "github_handle"),
]


def _init_repo(repo: Path) -> None:
    subprocess.run(
        ["git", "init", "-q", "-b", "main", str(repo)],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.email", "test@example.com"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.name", "Test"],
        check=True,
        capture_output=True,
    )


def _commit(repo: Path) -> None:
    subprocess.run(
        ["git", "-C", str(repo), "add", "-A"], check=True, capture_output=True
    )
    subprocess.run(
        ["git", "-C", str(repo), "commit", "-q", "-m", "fixture"],
        check=True,
        capture_output=True,
    )


def test_scan_clean_on_only_placeholders(
    tmp_path: Path, script, capsys: pytest.CaptureFixture[str]
) -> None:
    _init_repo(tmp_path)
    (tmp_path / "good.md").write_text(
        "\n".join(GOOD_LINES) + "\n", encoding="utf-8"
    )
    _commit(tmp_path)

    rc = script.run_scan(tmp_path)
    captured = capsys.readouterr()

    assert rc == 0, f"expected clean scan, got stderr:\n{captured.err}"
    assert captured.err == ""


@pytest.mark.parametrize(
    "filename,content,pattern_name", BAD_CASES, ids=[case[2] for case in BAD_CASES]
)
def test_scan_flags_bad_string(
    tmp_path: Path,
    script,
    capsys: pytest.CaptureFixture[str],
    filename: str,
    content: str,
    pattern_name: str,
) -> None:
    _init_repo(tmp_path)
    (tmp_path / filename).write_text(content, encoding="utf-8")
    _commit(tmp_path)

    rc = script.run_scan(tmp_path)
    captured = capsys.readouterr()

    assert rc == 1
    assert filename in captured.err
    assert f"pattern {pattern_name}" in captured.err
