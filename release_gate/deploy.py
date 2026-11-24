"""Atomic, reversible deploys: releases/<id>/ plus a `current.txt` pointer file."""
from __future__ import annotations

import os
import shutil
import time
from pathlib import Path


def _ptr(root: Path) -> Path:
    return root / "current.txt"


def current_release(root) -> str | None:
    p = _ptr(Path(root))
    return p.read_text().strip() if p.exists() else None


def _set_current(root: Path, release: str) -> None:
    tmp = root / "current.txt.tmp"
    tmp.write_text(release)
    os.replace(tmp, _ptr(root))  # atomic on POSIX and Windows


def deploy(project, root) -> tuple[str, str | None]:
    """Copy project to a new release dir and flip the pointer. Returns (new, previous)."""
    root = Path(root)
    (root / "releases").mkdir(parents=True, exist_ok=True)
    previous = current_release(root)
    count = len(list((root / "releases").iterdir()))
    release = time.strftime("%Y%m%d-%H%M%S") + f"-{count:03d}"
    shutil.copytree(project, root / "releases" / release,
                    ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"))
    _set_current(root, release)
    return release, previous


def rollback(root, previous: str | None) -> None:
    root = Path(root)
    if previous is None:
        _ptr(root).unlink(missing_ok=True)
    else:
        _set_current(root, previous)
