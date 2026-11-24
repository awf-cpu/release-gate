import argparse
import sys

from .pipeline import run_pipeline


def main() -> int:
    p = argparse.ArgumentParser(prog="release-gate")
    p.add_argument("project")
    p.add_argument("--root", required=True, help="deploy root (releases/ + current.txt)")
    p.add_argument("--mutate", nargs="+", required=True, help="files to mutate, relative to project")
    p.add_argument("--smoke", required=True, help="shell command; RELEASE_DIR points at the new release")
    p.add_argument("--threshold", type=float, default=0.8)
    a = p.parse_args()
    r = run_pipeline(a.project, a.root, a.mutate, a.smoke, a.threshold)
    print("RESULT:", "RELEASED" if r.ok else f"BLOCKED at {r.stage}: {r.reason}")
    for s in r.survivors:
        print("  surviving mutant:", s)
    return 0 if r.ok else 1


if __name__ == "__main__":
    sys.exit(main())
