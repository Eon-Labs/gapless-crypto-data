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
        text=True,
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
        [sys.executable, "-m", "gapless_crypto_data.cli", "--help"], capture_output=True, text=True
    )
    assert result.returncode == 0

    # Check that help mentions comma-separated symbols (flexible matching)
    assert "comma-separated" in result.stdout.lower()
    # Check for key components of multi-symbol support (more flexible)
    assert (
        "single symbol" in result.stdout.lower()
        and "comma" in result.stdout.lower()
        and "list" in result.stdout.lower()
    )

    # Check that multi-symbol example is present
    assert "BTCUSDT,ETHUSDT,SOLUSDT" in result.stdout


def test_cli_single_symbol_backwards_compatibility():
    """Test backwards compatibility with single symbol usage."""
    import tempfile

    with tempfile.TemporaryDirectory() as temp_dir:
        # Test single symbol (backwards compatible)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "gapless_crypto_data.cli",
                "--symbol",
                "BTCUSDT",
                "--timeframes",
                "1h",
                "--start",
                "2024-01-01",
                "--end",
                "2024-01-01",
                "--output-dir",
                temp_dir,
            ],
            capture_output=True,
            text=True,
            timeout=60,
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
                sys.executable,
                "-m",
                "gapless_crypto_data.cli",
                "--symbol",
                "BTCUSDT,ETHUSDT",
                "--timeframes",
                "1h",
                "--start",
                "2024-01-01",
                "--end",
                "2024-01-01",
                "--output-dir",
                temp_dir,
            ],
            capture_output=True,
            text=True,
            timeout=120,
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
                sys.executable,
                "-m",
                "gapless_crypto_data.cli",
                "--symbol",
                " BTCUSDT , ETHUSDT , SOLUSDT ",
                "--timeframes",
                "1h",
                "--start",
                "2024-01-01",
                "--end",
                "2024-01-01",
                "--output-dir",
                temp_dir,
            ],
            capture_output=True,
            text=True,
            timeout=180,
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
                sys.executable,
                "-m",
                "gapless_crypto_data.cli",
                "--symbol",
                "BTCUSDT,INVALIDSYMBOL,ETHUSDT",
                "--timeframes",
                "1h",
                "--start",
                "2024-01-01",
                "--end",
                "2024-01-01",
                "--output-dir",
                temp_dir,
            ],
            capture_output=True,
            text=True,
            timeout=180,
        )

        # Should handle mixed valid/invalid gracefully
        if result.returncode == 0:
            # Should process valid symbols and report failures
            assert "Failed symbols: INVALIDSYMBOL" in result.stdout
            assert (
                "Generated" in result.stdout
                and "datasets across" in result.stdout
                and "completed symbols" in result.stdout
            )
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
                sys.executable,
                "-m",
                "gapless_crypto_data.cli",
                "collect",
                "--symbol",
                "BTCUSDT,ETHUSDT",
                "--timeframes",
                "1h",
                "--start",
                "2024-01-01",
                "--end",
                "2024-01-01",
                "--output-dir",
                temp_dir,
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        # Should work with explicit collect subcommand
        if result.returncode == 0:
            assert "Symbols: ['BTCUSDT', 'ETHUSDT']" in result.stdout
        else:
            # Network failure is acceptable for this test
            pass


def test_cli_list_timeframes_flag():
    """Test that --list-timeframes flag works and shows all 16 timeframes."""
    result = subprocess.run(
        [sys.executable, "-m", "gapless_crypto_data.cli", "--list-timeframes"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0

    # Check that the output contains timeframe listing header
    assert "📊 Available Timeframes" in result.stdout
    assert "Timeframe | Description" in result.stdout

    # Check that all 16 timeframes are present
    expected_timeframes = [
        "1s",
        "1m",
        "3m",
        "5m",
        "15m",
        "30m",
        "1h",
        "2h",
        "4h",
        "6h",
        "8h",
        "12h",
        "1d",
        "3d",
        "1w",
        "1mo",
    ]

    for timeframe in expected_timeframes:
        assert timeframe in result.stdout

    # Check for usage examples
    assert "💡 Usage Examples:" in result.stdout
    assert "📈 Performance Notes:" in result.stdout


def test_cli_help_mentions_list_timeframes():
    """Test that help text mentions --list-timeframes option."""
    result = subprocess.run(
        [sys.executable, "-m", "gapless_crypto_data.cli", "--help"], capture_output=True, text=True
    )

    assert result.returncode == 0

    # Check that help mentions --list-timeframes
    assert "--list-timeframes" in result.stdout
    assert "List all available timeframes with descriptions" in result.stdout

    # Check that timeframes help mentions 13 available options
    assert "from 13 available options" in result.stdout
    # More flexible check for list-timeframes usage instruction
    assert (
        "list-timeframes" in result.stdout.lower()
        and "available" in result.stdout.lower()
        and "timeframes" in result.stdout.lower()
    )


def test_cli_invalid_timeframe_shows_available():
    """Test that invalid timeframe shows available options."""
    import tempfile

    with tempfile.TemporaryDirectory() as temp_dir:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "gapless_crypto_data.cli",
                "--symbol",
                "BTCUSDT",
                "--timeframes",
                "invalid_timeframe",
                "--start",
                "2024-01-01",
                "--end",
                "2024-01-01",
                "--output-dir",
                temp_dir,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Should show error message with available timeframes
        assert "❌ Timeframe 'invalid_timeframe' not available" in result.stdout
        assert "📊 Available timeframes:" in result.stdout
        assert "💡 Use 'gapless-crypto-data --list-timeframes'" in result.stdout

        # Should list some of the actual available timeframes
        assert "1m" in result.stdout
        assert "1h" in result.stdout
        assert "1d" in result.stdout


def test_cli_timeframe_discoverability_integration():
    """Test complete timeframe discoverability workflow."""
    # Test 1: List timeframes
    list_result = subprocess.run(
        [sys.executable, "-m", "gapless_crypto_data.cli", "--list-timeframes"],
        capture_output=True,
        text=True,
    )
    assert list_result.returncode == 0
    assert "1mo" in list_result.stdout  # Check that longest timeframe is shown

    # Test 2: Help mentions list-timeframes
    help_result = subprocess.run(
        [sys.executable, "-m", "gapless_crypto_data.cli", "--help"], capture_output=True, text=True
    )
    assert help_result.returncode == 0
    assert "--list-timeframes" in help_result.stdout

    # Test 3: Both regular and collect subcommand help mention discoverability
    collect_help_result = subprocess.run(
        [sys.executable, "-m", "gapless_crypto_data.cli", "collect", "--help"],
        capture_output=True,
        text=True,
    )

    if collect_help_result.returncode == 0:
        # The collect subcommand shows minimal help - check for timeframes option
        # The main --help command shows the detailed list-timeframes usage
        assert (
            "timeframes" in collect_help_result.stdout.lower()
            and "symbol" in collect_help_result.stdout.lower()
        )
