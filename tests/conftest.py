"""
Pytest configuration.
"""
import pytest

pytest_plugins = ('pytest_asyncio',)


@pytest.fixture(scope="session")
def anyio_backend():
    """Use asyncio backend for async tests."""
    return "asyncio"
