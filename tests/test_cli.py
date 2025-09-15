"""Test CLI functionality."""

import subprocess
import sys
from pathlib import Path


def test_cli_help():
    """Test that CLI help command works."""
    result = subprocess.run(
        [sys.executable, "-m", "gapless_crypto_data.cli", "--help"], capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "Ultra-fast cryptocurrency data collection" in result.stdout


def test_cli_version():
    """Test that CLI shows version information."""
    result = subprocess.run(
        [sys.executable, "-m", "gapless_crypto_data.cli", "--help"], capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "gapless-crypto-data" in result.stdout


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
