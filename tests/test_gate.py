import shutil
import sys
from pathlib import Path

from release_gate import current_release, run_pipeline

EXAMPLE = Path(__file__).resolve().parents[1] / "example" / "shop"
QUIET = lambda *_: None  # noqa: E731


def make(tmp_path):
    proj = tmp_path / "shop"
    shutil.copytree(EXAMPLE, proj)
    return proj


def smoke_cmd(proj):
    return f'"{sys.executable}" "{proj / "smoke.py"}"'


def test_good_release_ships(tmp_path):
    proj, root = make(tmp_path), tmp_path / "deploy"
    r = run_pipeline(proj, root, ["pricing.py"], smoke_cmd(proj), threshold=0.8, log=QUIET)
    assert r.ok and r.mutation_score >= 0.8
    assert current_release(root) == r.release


def test_weak_tests_are_blocked_by_mutation_score(tmp_path):
    proj, root = make(tmp_path), tmp_path / "deploy"
    # A suite that passes but cannot notice boundary or arithmetic changes.
    (proj / "tests" / "test_pricing.py").write_text(
        "import sys\nfrom pathlib import Path\n"
        "sys.path.insert(0, str(Path(__file__).resolve().parents[1]))\n"
        "from pricing import discount\n\n\ndef test_runs():\n    assert discount(1, 1) == 1\n")
    r = run_pipeline(proj, root, ["pricing.py"], smoke_cmd(proj), threshold=0.8, log=QUIET)
    assert not r.ok and r.stage == "mutation" and r.survivors
    assert current_release(root) is None  # nothing was deployed


def test_failed_smoke_rolls_back_to_previous(tmp_path):
    proj, root = make(tmp_path), tmp_path / "deploy"
    first = run_pipeline(proj, root, ["pricing.py"], smoke_cmd(proj), log=QUIET)
    assert first.ok
    bad_smoke = f'"{sys.executable}" -c "import sys; sys.exit(1)"'
    second = run_pipeline(proj, root, ["pricing.py"], bad_smoke, log=QUIET)
    assert not second.ok and second.rolled_back
    assert current_release(root) == first.release


def test_failing_tests_stop_the_pipeline(tmp_path):
    proj, root = make(tmp_path), tmp_path / "deploy"
    (proj / "pricing.py").write_text("def discount(t, i):\n    return 0\n")
    r = run_pipeline(proj, root, ["pricing.py"], smoke_cmd(proj), log=QUIET)
    assert not r.ok and r.stage == "tests"
