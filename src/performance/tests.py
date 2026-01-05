"""Performance benchmarking tests for InvenTree using the module."""

import pytest


# Define the function we want to benchmark
def fibonacci(n: int) -> int:
    """Compute the nth Fibonacci number (inefficiently)."""
    if n <= 1:
        return n
    else:
        return fibonacci(n - 2) + fibonacci(n - 1)


# Register a simple benchmark using the pytest marker
@pytest.mark.benchmark
def test_fib_bench():
    """Benchmark the fibonacci function for n=30."""
    result = fibonacci(30)
    assert result == 832040


@pytest.mark.benchmark
@pytest.mark.parametrize('n', [5, 10, 15, 20, 30])
def test_fib_parametrized(n):
    """Benchmark the fibonacci function for various n values."""
    result = fibonacci(n)
    assert result > 0
