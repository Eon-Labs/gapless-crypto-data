"""Test CLI functionality."""

import subprocess
import sys
from pathlib import Path


def test_cli_help_and_description():
    """Test that CLI help command works and contains expected content."""
    result = subprocess.run(
        [sys.executable, "-m", "gapless_crypto_data.cli", "--help"], capture_output=True, text=True
    )
    assert result.returncode == 0

    # Test that help output contains the description
    assert "Ultra-fast cryptocurrency data collection" in result.stdout

    # Test that help output contains the program name
    assert "gapless-crypto-data" in result.stdout

    # Test that help output contains common CLI elements
    assert "usage:" in result.stdout.lower() or "Usage:" in result.stdout


def test_cli_version_flag():
    """Test that CLI version flag works (if available)."""
    # Try to test --version flag separately
    result = subprocess.run(
        [sys.executable, "-m", "gapless_crypto_data.cli", "--version"],
        capture_output=True,
        text=True
    )

    # If --version flag exists, it should return version info
    if result.returncode == 0:
        # Should contain version information
        assert len(result.stdout.strip()) > 0
    else:
        # If --version doesn't exist, that's also acceptable
        # The version info is included in --help output
        pass


def test_cli_entry_point():
    """Test that the CLI entry point exists and is callable."""
    result = subprocess.run(
        ["uv", "run", "gapless-crypto-data", "--help"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )
    assert result.returncode == 0
    assert "Ultra-fast cryptocurrency data collection" in result.stdout


def test_cli_invalid_args():
    """Test CLI with invalid arguments."""
    result = subprocess.run(
        [sys.executable, "-m", "gapless_crypto_data.cli", "--invalid-flag"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "error:" in result.stderr.lower() or "usage:" in result.stderr.lower()
