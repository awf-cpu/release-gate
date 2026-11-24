# release-gate

[![CI](https://github.com/awf-cpu/release-gate/actions/workflows/ci.yml/badge.svg)](https://github.com/awf-cpu/release-gate/actions/workflows/ci.yml)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

A small **deploy gate** that only ships a release if the tests pass **and the tests are good enough to matter**, then deploys atomically, runs a smoke check against what was actually deployed, and **rolls back automatically** if that check fails. Zero runtime dependencies.

## The business problem

"Tests are green" is a weak signal: a suite that still passes after the code was deliberately broken protects nothing. And a bad release that reaches production should be undone in seconds, by a script, not by someone awake at 3 a.m.

## The four stages

1. **Tests** must pass.
2. **Mutation testing**: an AST mutator flips comparisons (`>=` to `>`), arithmetic, boolean operators and constants, one change at a time, and re-runs the suite on each mutant. If too many mutants survive (default: below 80% killed), the release is blocked and the survivors are listed. Mutants run in a throw-away copy of the project, never in the real files.
3. **Atomic deploy**: copy to `releases/<id>/`, flip a `current.txt` pointer with an atomic replace. Previous releases stay on disk.
4. **Smoke check** (any shell command, with `RELEASE_DIR` set to the new release). Non-zero exit means the pointer goes back to the previous release.

## Try it

```bash
pip install pytest
python -m release_gate example/shop --root /tmp/deploy \
    --mutate pricing.py --smoke "python example/shop/smoke.py"
```

```
[1/4] tests
[2/4] mutation testing (threshold 80%)
      killed 10/12 = 83%
[3/4] deploy (atomic)
[4/4] smoke check
RESULT: RELEASED
```

The test suite (`pytest -q`) demonstrates the three failure paths: weak tests blocked by the mutation score, a failing smoke check rolled back to the previous release, and a failing suite stopping the pipeline before anything is deployed.

## Scope and honesty

Educational scale: Python source only, a handful of mutation operators, a pointer-file deploy. The ideas (mutation score as a gate, mutants in a sandbox copy, smoke against the deployed artifact, automatic rollback) are the part that transfers to real pipelines.

MIT licensed. Built by André Feix · [LinkedIn](https://www.linkedin.com/in/andrefeix)
