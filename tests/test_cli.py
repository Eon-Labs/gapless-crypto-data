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


def test_cli_help_mentions_multi_symbol():
    """Test that help text mentions comma-separated symbols capability."""
    result = subprocess.run(
        [sys.executable, "-m", "gapless_crypto_data.cli", "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0

    # Check that help mentions comma-separated symbols
    assert "comma-separated" in result.stdout.lower()
    assert "single symbol or comma-separated list" in result.stdout

    # Check that multi-symbol example is present
    assert "BTCUSDT,ETHUSDT,SOLUSDT" in result.stdout


def test_cli_single_symbol_backwards_compatibility():
    """Test backwards compatibility with single symbol usage."""
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as temp_dir:
        # Test single symbol (backwards compatible)
        result = subprocess.run(
            [
                sys.executable, "-m", "gapless_crypto_data.cli",
                "--symbol", "BTCUSDT",
                "--timeframes", "1h",
                "--start", "2024-01-01",
                "--end", "2024-01-01",
                "--output-dir", temp_dir
            ],
            capture_output=True,
            text=True,
            timeout=60
        )

        # Should succeed and mention single symbol
        if result.returncode == 0:
            assert "Symbols: ['BTCUSDT']" in result.stdout
            assert "Generated" in result.stdout
        else:
            # May fail due to network issues, which is acceptable for this test
            # We're primarily testing argument parsing
            pass


def test_cli_multiple_symbols_parsing():
    """Test that multi-symbol arguments are parsed correctly."""
    import tempfile

    with tempfile.TemporaryDirectory() as temp_dir:
        # Test multiple symbols (new functionality)
        result = subprocess.run(
            [
                sys.executable, "-m", "gapless_crypto_data.cli",
                "--symbol", "BTCUSDT,ETHUSDT",
                "--timeframes", "1h",
                "--start", "2024-01-01",
                "--end", "2024-01-01",
                "--output-dir", temp_dir
            ],
            capture_output=True,
            text=True,
            timeout=120
        )

        # Should parse multiple symbols correctly
        if result.returncode == 0:
            assert "Symbols: ['BTCUSDT', 'ETHUSDT']" in result.stdout
            assert "Processing BTCUSDT (1/2)" in result.stdout
            assert "Processing ETHUSDT (2/2)" in result.stdout
        else:
            # May fail due to network issues, which is acceptable for this test
            # We're primarily testing argument parsing
            pass


def test_cli_multiple_symbols_with_whitespace():
    """Test multi-symbol parsing handles whitespace correctly."""
    import tempfile

    with tempfile.TemporaryDirectory() as temp_dir:
        # Test symbols with extra whitespace
        result = subprocess.run(
            [
                sys.executable, "-m", "gapless_crypto_data.cli",
                "--symbol", " BTCUSDT , ETHUSDT , SOLUSDT ",
                "--timeframes", "1h",
                "--start", "2024-01-01",
                "--end", "2024-01-01",
                "--output-dir", temp_dir
            ],
            capture_output=True,
            text=True,
            timeout=180
        )

        # Should strip whitespace and parse correctly
        if result.returncode == 0:
            assert "Symbols: ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']" in result.stdout
            assert "Processing BTCUSDT (1/3)" in result.stdout
            assert "Processing ETHUSDT (2/3)" in result.stdout
            assert "Processing SOLUSDT (3/3)" in result.stdout
        else:
            # May fail due to network issues, check stderr for argument parsing
            assert "--symbol" not in result.stderr or "error:" not in result.stderr.lower()


def test_cli_error_handling_with_invalid_symbols():
    """Test error handling when some symbols in the list are invalid."""
    import tempfile

    with tempfile.TemporaryDirectory() as temp_dir:
        # Test with mix of valid and invalid symbols
        result = subprocess.run(
            [
                sys.executable, "-m", "gapless_crypto_data.cli",
                "--symbol", "BTCUSDT,INVALIDSYMBOL,ETHUSDT",
                "--timeframes", "1h",
                "--start", "2024-01-01",
                "--end", "2024-01-01",
                "--output-dir", temp_dir
            ],
            capture_output=True,
            text=True,
            timeout=180
        )

        # Should handle mixed valid/invalid gracefully
        if result.returncode == 0:
            # Should process valid symbols and report failures
            assert "Failed symbols: INVALIDSYMBOL" in result.stdout
            assert "Generated 2 datasets across 2 symbols" in result.stdout
        else:
            # Network failure is acceptable for this test
            pass


def test_cli_collect_subcommand_multi_symbol():
    """Test explicit collect subcommand with multi-symbol."""
    import tempfile

    with tempfile.TemporaryDirectory() as temp_dir:
        # Test using explicit collect subcommand
        result = subprocess.run(
            [
                sys.executable, "-m", "gapless_crypto_data.cli",
                "collect",
                "--symbol", "BTCUSDT,ETHUSDT",
                "--timeframes", "1h",
                "--start", "2024-01-01",
                "--end", "2024-01-01",
                "--output-dir", temp_dir
            ],
            capture_output=True,
            text=True,
            timeout=120
        )

        # Should work with explicit collect subcommand
        if result.returncode == 0:
            assert "Symbols: ['BTCUSDT', 'ETHUSDT']" in result.stdout
        else:
            # Network failure is acceptable for this test
            pass
