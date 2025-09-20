"""
Integration tests for CLI functionality.

Tests complete end-to-end workflows covering the CLI → collection → file generation chain
where critical integration bugs were discovered during adversarial testing.
"""

import json
import subprocess
import tempfile
from pathlib import Path


class TestCLIIntegration:
    """Test complete CLI workflows to prevent integration regressions."""

    def test_legacy_cli_btcusdt_single_day(self):
        """Test legacy CLI approach (no subcommand) with single symbol, single day."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Run CLI command
            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "gapless-crypto-data",
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
            )

            # Verify successful execution
            assert result.returncode == 0, f"CLI failed with: {result.stderr}"
            assert "ULTRA-FAST SUCCESS" in result.stdout

            # Verify file generation
            csv_file = Path(temp_dir) / "binance_spot_BTCUSDT-1h_20240101-20240101_v2.10.0.csv"
            metadata_file = (
                Path(temp_dir) / "binance_spot_BTCUSDT-1h_20240101-20240101_v2.10.0.metadata.json"
            )

            assert csv_file.exists(), "CSV file not generated"
            assert metadata_file.exists(), "Metadata file not generated"

            # Verify CSV content
            with open(csv_file, "r") as f:
                lines = f.readlines()
                assert len(lines) > 24, "Expected at least 24 data rows + headers"

                # Check header format
                assert lines[0].startswith("# Binance Spot Market Data"), "Invalid header format"

                # Check data columns (11-column format)
                data_line = None
                for line in lines:
                    if not line.startswith("#") and "," in line:
                        data_line = line.strip()
                        break

                assert data_line, "No data rows found"
                columns = data_line.split(",")
                assert len(columns) == 11, f"Expected 11 columns, got {len(columns)}"

            # Verify metadata content
            with open(metadata_file, "r") as f:
                metadata = json.load(f)
                assert metadata["symbol"] == "BTCUSDT"
                assert metadata["timeframe"] == "1h"
                assert metadata["version"] == "v2.10.0"
                assert metadata["gap_analysis"]["total_gaps_detected"] == 0

    def test_subcommand_cli_ethusdt_single_day(self):
        """Test subcommand CLI approach with single symbol, single day."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Run CLI command with subcommand
            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "gapless-crypto-data",
                    "collect",
                    "--symbol",
                    "ETHUSDT",
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
            )

            # Verify successful execution
            assert result.returncode == 0, f"CLI failed with: {result.stderr}"
            assert "ULTRA-FAST SUCCESS" in result.stdout

            # Verify file generation
            csv_file = Path(temp_dir) / "binance_spot_ETHUSDT-1h_20240101-20240101_v2.10.0.csv"
            metadata_file = (
                Path(temp_dir) / "binance_spot_ETHUSDT-1h_20240101-20240101_v2.10.0.metadata.json"
            )

            assert csv_file.exists(), "CSV file not generated"
            assert metadata_file.exists(), "Metadata file not generated"

    def test_multiple_symbols_integration(self):
        """Test CLI with multiple symbols to verify collect_multiple_timeframes integration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Run CLI command with multiple symbols
            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "gapless-crypto-data",
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
            )

            # Verify successful execution
            assert result.returncode == 0, f"CLI failed with: {result.stderr}"
            assert (
                "Generated" in result.stdout
                and "datasets across" in result.stdout
                and "completed symbols" in result.stdout
            )

            # Verify both files were created
            btc_file = Path(temp_dir) / "binance_spot_BTCUSDT-1h_20240101-20240101_v2.10.0.csv"
            eth_file = Path(temp_dir) / "binance_spot_ETHUSDT-1h_20240101-20240101_v2.10.0.csv"

            assert btc_file.exists(), "BTCUSDT CSV file not generated"
            assert eth_file.exists(), "ETHUSDT CSV file not generated"

    def test_multiple_timeframes_integration(self):
        """Test CLI with multiple timeframes to verify timeframe handling."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Run CLI command with multiple timeframes
            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "gapless-crypto-data",
                    "--symbol",
                    "SOLUSDT",
                    "--timeframes",
                    "1h,4h",
                    "--start",
                    "2024-01-01",
                    "--end",
                    "2024-01-01",
                    "--output-dir",
                    temp_dir,
                ],
                capture_output=True,
                text=True,
            )

            # Verify successful execution
            assert result.returncode == 0, f"CLI failed with: {result.stderr}"

            # Verify both timeframe files were created
            h1_file = Path(temp_dir) / "binance_spot_SOLUSDT-1h_20240101-20240101_v2.10.0.csv"
            h4_file = Path(temp_dir) / "binance_spot_SOLUSDT-4h_20240101-20240101_v2.10.0.csv"

            assert h1_file.exists(), "1h CSV file not generated"
            assert h4_file.exists(), "4h CSV file not generated"

    def test_gap_filling_integration(self):
        """Test gap filling CLI integration with actual files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # First, generate a file
            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "gapless-crypto-data",
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
            )

            assert result.returncode == 0, "Data generation failed"

            # Now test gap filling (should find 0 gaps on clean data)
            result = subprocess.run(
                ["uv", "run", "gapless-crypto-data", "fill-gaps", "--directory", temp_dir],
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0, f"Gap filling failed with: {result.stderr}"
            assert "GAP FILLING SUCCESS" in result.stdout
            assert "Processing BTCUSDT 1h data" in result.stdout

    def test_invalid_symbol_error_handling(self):
        """Test error handling with invalid symbol."""
        result = subprocess.run(
            [
                "uv",
                "run",
                "gapless-crypto-data",
                "--symbol",
                "INVALIDTESTINGSYMBOL",
                "--timeframes",
                "1h",
                "--start",
                "2024-01-01",
                "--end",
                "2024-01-01",
            ],
            capture_output=True,
            text=True,
        )

        # Should fail gracefully with exit code 1
        assert result.returncode == 1, "Should fail with invalid symbol"
        assert "FAILED: No datasets generated" in result.stdout
        assert "INVALIDTESTINGSYMBOL" in result.stdout

    def test_invalid_timeframe_error_handling(self):
        """Test error handling with invalid timeframe."""
        result = subprocess.run(
            [
                "uv",
                "run",
                "gapless-crypto-data",
                "--symbol",
                "BTCUSDT",
                "--timeframes",
                "invalidtimeframe",
                "--start",
                "2024-01-01",
                "--end",
                "2024-01-01",
            ],
            capture_output=True,
            text=True,
        )

        # Should fail gracefully
        assert result.returncode == 1, "Should fail with invalid timeframe"

    def test_cli_help_integration(self):
        """Test CLI help functionality."""
        # Test main help
        result = subprocess.run(
            ["uv", "run", "gapless-crypto-data", "--help"], capture_output=True, text=True
        )

        assert result.returncode == 0, "Help command failed"
        assert "Ultra-fast cryptocurrency data collection" in result.stdout
        assert "--symbol" in result.stdout
        assert "--timeframes" in result.stdout

        # Test subcommand help
        result = subprocess.run(
            ["uv", "run", "gapless-crypto-data", "collect", "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, "Collect help command failed"
        assert "--symbol" in result.stdout

        # Test gap filling help
        result = subprocess.run(
            ["uv", "run", "gapless-crypto-data", "fill-gaps", "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, "Fill-gaps help command failed"
        assert "--directory" in result.stdout

    def test_cli_version_integration(self):
        """Test CLI version display."""
        result = subprocess.run(
            ["uv", "run", "gapless-crypto-data", "--version"], capture_output=True, text=True
        )

        assert result.returncode == 0, "Version command failed"
        assert "gapless-crypto-data" in result.stdout

    def test_list_timeframes_integration(self):
        """Test CLI timeframes listing."""
        result = subprocess.run(
            ["uv", "run", "gapless-crypto-data", "--list-timeframes"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, "List timeframes command failed"
        assert "Available Timeframes" in result.stdout
        assert "1m" in result.stdout
        assert "1h" in result.stdout


class TestDataIntegrity:
    """Test data integrity across the complete pipeline."""

    def test_11_column_microstructure_format(self):
        """Verify 11-column microstructure format is maintained end-to-end."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "gapless-crypto-data",
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
            )

            assert result.returncode == 0, "Data generation failed"

            csv_file = Path(temp_dir) / "binance_spot_BTCUSDT-1h_20240101-20240101_v2.10.0.csv"

            with open(csv_file, "r") as f:
                # Find the header line
                header_line = None
                for line in f:
                    if line.startswith("date,"):
                        header_line = line.strip()
                        break

                assert header_line, "Header line not found"
                columns = header_line.split(",")

                expected_columns = [
                    "date",
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                    "close_time",
                    "quote_asset_volume",
                    "number_of_trades",
                    "taker_buy_base_asset_volume",
                    "taker_buy_quote_asset_volume",
                ]

                assert columns == expected_columns, f"Column mismatch: {columns}"

    def test_metadata_completeness(self):
        """Verify metadata contains all required fields."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "gapless-crypto-data",
                    "--symbol",
                    "ETHUSDT",
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
            )

            assert result.returncode == 0, "Data generation failed"

            metadata_file = (
                Path(temp_dir) / "binance_spot_ETHUSDT-1h_20240101-20240101_v2.10.0.metadata.json"
            )

            with open(metadata_file, "r") as f:
                metadata = json.load(f)

                # Verify required top-level fields
                required_fields = [
                    "version",
                    "generator",
                    "generation_timestamp",
                    "data_source",
                    "symbol",
                    "timeframe",
                    "actual_bars",
                    "date_range",
                    "statistics",
                    "data_integrity",
                    "gap_analysis",
                    "compliance",
                ]

                for field in required_fields:
                    assert field in metadata, f"Missing required field: {field}"

                # Verify gap analysis
                assert metadata["gap_analysis"]["total_gaps_detected"] == 0
                assert metadata["gap_analysis"]["data_completeness_score"] == 1.0

                # Verify compliance flags
                assert metadata["compliance"]["zero_magic_numbers"]
                assert metadata["compliance"]["temporal_integrity"]
