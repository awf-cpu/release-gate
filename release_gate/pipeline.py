from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from .deploy import deploy, rollback
from .mutate import run_mutation, tests_pass


@dataclass
class GateResult:
    ok: bool
    stage: str                      # last stage reached
    reason: str = ""
    release: str | None = None
    mutation_score: float | None = None
    survivors: list[str] = field(default_factory=list)
    rolled_back: bool = False


def run_pipeline(project, root, mutate_targets, smoke_cmd, threshold=0.8, log=print) -> GateResult:
    project, root = Path(project), Path(root)

    log("[1/4] tests")
    if not tests_pass(project):
        return GateResult(False, "tests", "test suite failed")

    log(f"[2/4] mutation testing (threshold {threshold:.0%})")
    mut = run_mutation(project, mutate_targets)
    log(f"      killed {mut.killed}/{mut.total} = {mut.score:.0%}")
    if mut.score < threshold:
        return GateResult(False, "mutation",
                          f"mutation score {mut.score:.0%} below {threshold:.0%}",
                          mutation_score=mut.score, survivors=mut.survivors)

    log("[3/4] deploy (atomic)")
    release, previous = deploy(project, root)

    log("[4/4] smoke check")
    env = dict(os.environ, RELEASE_DIR=str(root / "releases" / release))
    smoke = subprocess.run(smoke_cmd, shell=True, env=env, capture_output=True,
                           text=True, timeout=60)
    if smoke.returncode != 0:
        rollback(root, previous)
        log(f"      smoke FAILED, rolled back to {previous}")
        return GateResult(False, "smoke", "smoke check failed; rolled back", release=release,
                          mutation_score=mut.score, rolled_back=True)
    return GateResult(True, "done", release=release, mutation_score=mut.score)
