"""
Pytest configuration and shared fixtures for gapless-crypto-data tests.
"""

from pathlib import Path

import pytest


@pytest.fixture
def test_data_dir():
    """Path to test data fixtures directory."""
    return Path(__file__).parent / "fixtures" / "test_data"


@pytest.fixture
def test_data_large_dir():
    """Path to large test data fixtures directory."""
    return Path(__file__).parent / "fixtures" / "test_data_large"


@pytest.fixture
def project_root():
    """Path to project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def sample_data_dir():
    """Path to sample data directory in source."""
    return Path(__file__).parent.parent / "src" / "gapless_crypto_data" / "sample_data"
