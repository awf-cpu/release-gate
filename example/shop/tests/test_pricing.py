import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pricing import discount  # noqa: E402


def test_no_discount():
    assert discount(99.99, 9) == 99.99


def test_threshold_is_inclusive():
    assert discount(100, 1) == 90.0


def test_bulk_discount_boundary():
    assert discount(50, 10) == 47.5
    assert discount(50, 9) == 50


def test_both_discounts():
    assert discount(200, 10) == 170.0
