"""A small AST mutation tester.

A test suite that still passes after the code was deliberately broken is not
protecting anything. Each mutant runs in a throw-away COPY of the project, so
production files are never touched.
"""
from __future__ import annotations

import ast
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

_CMP = {ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE, ast.GtE: ast.Gt,
        ast.Eq: ast.NotEq, ast.NotEq: ast.Eq}
_BIN = {ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.FloorDiv}


@dataclass
class MutationResult:
    total: int = 0
    killed: int = 0
    survivors: list[str] = field(default_factory=list)

    @property
    def score(self) -> float:
        return 1.0 if self.total == 0 else self.killed / self.total


def _sites(tree: ast.AST):
    """Yield (node, kind) for every mutable site, in a stable order."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare) and type(node.ops[0]) in _CMP:
            yield node, "cmp"
        elif isinstance(node, ast.BinOp) and type(node.op) in _BIN:
            yield node, "bin"
        elif isinstance(node, ast.BoolOp):
            yield node, "bool"
        elif (isinstance(node, ast.Constant) and isinstance(node.value, (int, float))
              and not isinstance(node.value, bool)):
            yield node, "const"


def mutants(source: str):
    """Yield (description, mutated_source), one mutation each."""
    n = sum(1 for _ in _sites(ast.parse(source)))
    for i in range(n):
        tree = ast.parse(source)
        node, kind = list(_sites(tree))[i]
        if kind == "cmp":
            node.ops[0] = _CMP[type(node.ops[0])]()
        elif kind == "bin":
            node.op = _BIN[type(node.op)]()
        elif kind == "bool":
            node.op = ast.Or() if isinstance(node.op, ast.And) else ast.And()
        else:
            node.value = node.value + 1
        yield f"line {node.lineno}: {kind}", ast.unparse(ast.fix_missing_locations(tree))


def tests_pass(project: Path, timeout: int = 120) -> bool:
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider"],
                       cwd=project, capture_output=True, timeout=timeout)
    return r.returncode == 0


def run_mutation(project, targets: list[str]) -> MutationResult:
    project = Path(project)
    result = MutationResult()
    for rel in targets:
        original = (project / rel).read_text(encoding="utf-8")
        for desc, mutated in mutants(original):
            with tempfile.TemporaryDirectory() as tmp:
                sandbox = Path(tmp) / "p"
                shutil.copytree(project, sandbox,
                                ignore=shutil.ignore_patterns(".git", "__pycache__"))
                (sandbox / rel).write_text(mutated, encoding="utf-8")
                result.total += 1
                try:
                    killed = not tests_pass(sandbox, timeout=60)
                except subprocess.TimeoutExpired:
                    killed = True  # a hanging mutant counts as detected
            if killed:
                result.killed += 1
            else:
                result.survivors.append(f"{rel} {desc}")
    return result
