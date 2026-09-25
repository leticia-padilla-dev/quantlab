"""Setuptools build hooks for reproducible QuantLab package metadata."""

from __future__ import annotations

from pathlib import Path
import re
import subprocess

from setuptools import setup
from setuptools.command.build_py import build_py as _build_py


_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$", re.IGNORECASE)


def _source_commit_from_clean_checkout(repository_root: Path) -> str:
    """Require both index and worktree to match HEAD; ignore untracked files.

    Keep this dependency-free build check equivalent to the runtime checkout
    check in quantitative_provenance; build isolation cannot import the app.
    """

    try:
        commit = subprocess.check_output(
            ["git", "-C", str(repository_root), "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError(
            "Cannot build QuantLab without a verifiable source commit"
        ) from exc

    for diff_args in (("diff", "--quiet"), ("diff", "--cached", "--quiet")):
        try:
            result = subprocess.run(
                ["git", "-C", str(repository_root), *diff_args],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        except OSError as exc:
            raise RuntimeError(
                "Cannot build QuantLab without a verifiable source commit"
            ) from exc
        if result.returncode == 1:
            raise RuntimeError(
                "Cannot build QuantLab from a checkout with tracked changes"
            )
        if result.returncode != 0:
            raise RuntimeError(
                "Cannot build QuantLab without a verifiable source commit"
            )

    if not _COMMIT_RE.fullmatch(commit):
        raise RuntimeError(
            "QuantLab build source commit is not a full Git SHA"
        )
    return commit.lower()


class BuildPyWithSourceCommit(_build_py):
    """Embed the exact checkout commit into non-editable package builds."""

    def run(self) -> None:
        repository_root = Path(__file__).resolve().parent
        commit = _source_commit_from_clean_checkout(repository_root)
        super().run()
        if _source_commit_from_clean_checkout(repository_root) != commit:
            raise RuntimeError("QuantLab source commit changed during build")

        target = Path(self.build_lib) / "quantlab" / "_build_info.py"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            '"""Generated source identity for this QuantLab build."""\n\n'
            f'SOURCE_GIT_COMMIT = "{commit}"\n',
            encoding="utf-8",
        )


setup(cmdclass={"build_py": BuildPyWithSourceCommit})
