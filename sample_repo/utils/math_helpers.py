def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b


def average(numbers: list) -> float:
    """Compute the average of a list of numbers. Raises ValueError on empty list."""
    if not numbers:
        raise ValueError("Cannot average an empty list")
    return sum(numbers) / len(numbers)
