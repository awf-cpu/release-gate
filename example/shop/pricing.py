def discount(total: float, items: int) -> float:
    """10% off from 100.00, plus 5% off for 10+ items. Never negative."""
    rate = 0.0
    if total >= 100:
        rate += 0.10
    if items >= 10:
        rate += 0.05
    return max(round(total * (1 - rate), 2), 0)
