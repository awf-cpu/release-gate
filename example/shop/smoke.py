"""Smoke check run against the *deployed* release (RELEASE_DIR)."""
import os
import sys

sys.path.insert(0, os.environ["RELEASE_DIR"])
from pricing import discount  # noqa: E402

assert discount(100, 1) == 90.0, "deployed pricing is wrong"
print("smoke ok")
