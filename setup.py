"""Setuptools build hooks for reproducible QuantLab package metadata."""

from __future__ import annotations

from pathlib import Path
import re
import subprocess

from setuptools import setup
from setuptools.command.build_py import build_py as _build_py


_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$", re.IGNORECASE)


class BuildPyWithSourceCommit(_build_py):
    """Embed the exact checkout commit into non-editable package builds."""

    def run(self) -> None:
        super().run()
        repository_root = Path(__file__).resolve().parent
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
        if not _COMMIT_RE.fullmatch(commit):
            raise RuntimeError(
                "QuantLab build source commit is not a full Git SHA"
            )

        target = Path(self.build_lib) / "quantlab" / "_build_info.py"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            '"""Generated source identity for this QuantLab build."""\n\n'
            f'SOURCE_GIT_COMMIT = "{commit.lower()}"\n',
            encoding="utf-8",
        )


setup(cmdclass={"build_py": BuildPyWithSourceCommit})
