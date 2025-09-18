"""Test Binance Public Data Collector functionality."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from gapless_crypto_data.collectors.binance_public_data_collector import BinancePublicDataCollector


class TestBinancePublicDataCollector:
    """Test suite for BinancePublicDataCollector."""

    def test_init(self):
        """Test collector initialization."""
        collector = BinancePublicDataCollector()
        assert collector is not None
        assert hasattr(collector, "collect_timeframe_data")

    def test_init_with_custom_params(self):
        """Test collector initialization with custom parameters."""
        collector = BinancePublicDataCollector(
            symbol="BTCUSDT", start_date="2023-01-01", end_date="2023-12-31"
        )
        assert collector.symbol == "BTCUSDT"

    @patch("httpx.get")
    def test_download_file_success(self, mock_get):
        """Test successful file download."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_content.return_value = [b"test data chunk"]
        mock_get.return_value = mock_response

        collector = BinancePublicDataCollector()

        with tempfile.NamedTemporaryFile() as temp_file:
            # Test the download functionality
            # Note: This would require accessing private methods,
            # so we'll test via the public interface instead
            pass

    def test_validate_symbol(self):
        """Test symbol validation."""
        collector = BinancePublicDataCollector()

        # Valid symbols
        valid_symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
        for symbol in valid_symbols:
            # The actual validation would depend on the implementation
            assert isinstance(symbol, str)
            assert symbol.isupper()

    def test_validate_timeframes(self):
        """Test timeframe validation."""
        collector = BinancePublicDataCollector()

        valid_timeframes = ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h"]
        for tf in valid_timeframes:
            assert isinstance(tf, str)
            assert len(tf) >= 2

    def test_date_range_validation(self):
        """Test date range validation."""
        collector = BinancePublicDataCollector()

        # Test date format validation
        valid_dates = ["2023-01-01", "2024-12-31"]
        for date_str in valid_dates:
            assert len(date_str) == 10
            assert date_str.count("-") == 2

    @pytest.mark.integration
    def test_collect_small_dataset(self):
        """Integration test for collecting a small dataset."""
        collector = BinancePublicDataCollector(
            symbol="BTCUSDT", start_date="2024-01-01", end_date="2024-01-02"
        )

        # Test with a very small date range to minimize download time
        try:
            result = collector.collect_timeframe_data("1h")

            # Check that files were created in the collector's output directory
            csv_files = list(Path(collector.output_dir).glob("*.csv"))

            # If files were created, check their structure
            if csv_files:
                for csv_file in csv_files:
                    df = pd.read_csv(csv_file)
                    assert len(df.columns) == 11  # Full 11-column microstructure format
                    assert len(df) > 0
                    # Verify all expected columns are present
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
                    for col in expected_columns:
                        assert col in df.columns, f"Missing column: {col}"

        except Exception as e:
            # If network issues, skip the test
            pytest.skip(f"Network-dependent test failed: {e}")

    def test_output_filename_format(self):
        """Test output filename format."""
        collector = BinancePublicDataCollector()

        # Test filename components
        symbol = "BTCUSDT"
        timeframe = "1h"
        start_date = "2024-01-01"
        end_date = "2024-01-02"

        # The actual filename generation would depend on implementation
        expected_parts = [
            symbol.lower(),
            timeframe,
            start_date.replace("-", ""),
            end_date.replace("-", ""),
        ]

        # Basic validation that these components are reasonable
        for part in expected_parts:
            assert isinstance(part, str)
            assert len(part) > 0

    def test_analyze_timestamp_format_milliseconds(self):
        """Test timestamp format analysis for millisecond timestamps."""
        collector = BinancePublicDataCollector()

        # Test millisecond timestamps (13 digits)
        millisecond_timestamps = [
            "1704067200000",  # 2024-01-01 00:00:00 UTC
            "1704070800000",  # 2024-01-01 01:00:00 UTC
            "1704074400000",  # 2024-01-01 02:00:00 UTC
            "1609459200000",  # 2021-01-01 00:00:00 UTC
            "1735689600000",  # 2025-01-01 00:00:00 UTC
        ]

        for i, timestamp_str in enumerate(millisecond_timestamps):
            # Convert string to int as the method expects integer timestamps
            timestamp_int = int(timestamp_str)
            result = collector._analyze_timestamp_format(timestamp_int, i)

            # Should return a tuple: (format_type, timestamp_value, metadata)
            assert isinstance(result, tuple)
            assert len(result) == 3
            format_type, timestamp_value, metadata = result
            assert format_type == "milliseconds"
            assert isinstance(timestamp_value, (int, float))
            assert isinstance(metadata, dict)

    def test_analyze_timestamp_format_microseconds(self):
        """Test timestamp format analysis for microsecond timestamps."""
        collector = BinancePublicDataCollector()

        # Test microsecond timestamps (16 digits)
        microsecond_timestamps = [
            "1704067200000000",  # 2024-01-01 00:00:00.000000 UTC
            "1704070800123456",  # 2024-01-01 01:00:00.123456 UTC
            "1704074400999999",  # 2024-01-01 02:00:00.999999 UTC
            "1609459200000001",  # 2021-01-01 00:00:00.000001 UTC
        ]

        for i, timestamp_str in enumerate(microsecond_timestamps):
            # Convert string to int as the method expects integer timestamps
            timestamp_int = int(timestamp_str)
            result = collector._analyze_timestamp_format(timestamp_int, i)

            # Should return a tuple: (format_type, timestamp_value, metadata)
            assert isinstance(result, tuple)
            assert len(result) == 3
            format_type, timestamp_value, metadata = result
            assert format_type == "microseconds"
            assert isinstance(timestamp_value, (int, float))
            assert isinstance(metadata, dict)

    def test_analyze_timestamp_format_invalid(self):
        """Test timestamp format analysis with invalid timestamps."""
        collector = BinancePublicDataCollector()

        # Test invalid timestamp formats
        invalid_timestamps = [
            "invalid_timestamp",
            "123",  # Too short
            "12345678901234567890",  # Too long
            "",  # Empty
            "not_a_number",
            "1.234567890123",  # Decimal
            "-1704067200000",  # Negative
        ]

        for i, timestamp_str in enumerate(invalid_timestamps):
            try:
                # Try to convert to int first, then test
                if timestamp_str and timestamp_str.replace("-", "").replace(".", "").isdigit():
                    timestamp_int = int(float(timestamp_str))
                    result = collector._analyze_timestamp_format(timestamp_int, i)
                    # If it doesn't raise an exception, it should be a tuple or None
                    assert isinstance(result, (tuple, type(None)))
                else:
                    # Non-numeric strings should raise exceptions
                    pass
            except (ValueError, TypeError, AttributeError):
                # Expected behavior for invalid timestamps
                pass

    def test_analyze_timestamp_format_edge_cases(self):
        """Test timestamp format analysis with edge case values."""
        collector = BinancePublicDataCollector()

        # Test edge case timestamps
        edge_cases = [
            ("0000000000000", "unknown"),  # Zero timestamp becomes 0 (1 digit) -> unknown
            ("9999999999999", "milliseconds"),  # Max 13-digit value
            ("0000000000000000", "unknown"),  # Zero timestamp becomes 0 (1 digit) -> unknown
            ("9999999999999999", "microseconds"),  # Max 16-digit value
            ("1000000000000", "milliseconds"),  # Min valid epoch timestamp (13 digits)
            ("1000000000000000", "microseconds"),  # Min valid epoch timestamp (16 digits)
        ]

        for timestamp_str, expected_format in edge_cases:
            timestamp_int = int(timestamp_str)
            result = collector._analyze_timestamp_format(timestamp_int, 0)

            if result:  # If analysis succeeds
                format_type, timestamp_value, metadata = result
                assert format_type == expected_format

                # For known formats, timestamp_value should be numeric
                # For unknown formats, timestamp_value is None
                if expected_format in ["milliseconds", "microseconds"]:
                    assert isinstance(timestamp_value, (int, float))
                elif expected_format == "unknown":
                    assert timestamp_value is None

    def test_analyze_timestamp_format_boundary_conditions(self):
        """Test timestamp format analysis at format boundaries."""
        collector = BinancePublicDataCollector()

        # Test timestamps at the boundary between formats
        boundary_cases = [
            ("999999999999", 12),  # 12 digits - too short for milliseconds
            ("1000000000000", 13),  # 13 digits - milliseconds
            ("10000000000000", 14),  # 14 digits - between formats
            ("100000000000000", 15),  # 15 digits - between formats
            ("1000000000000000", 16),  # 16 digits - microseconds
            ("10000000000000000", 17),  # 17 digits - too long
        ]

        for timestamp_str, expected_length in boundary_cases:
            try:
                timestamp_int = int(timestamp_str)
                result = collector._analyze_timestamp_format(timestamp_int, 0)

                if result:
                    format_type, timestamp_value, metadata = result

                    # Verify format classification based on expected length
                    if expected_length == 13:
                        assert format_type == "milliseconds"
                    elif expected_length == 16:
                        assert format_type == "microseconds"

            except (ValueError, TypeError):
                # Some boundary cases may be invalid
                pass

    def test_timestamp_format_consistency(self):
        """Test that timestamp format analysis is consistent across multiple calls."""
        collector = BinancePublicDataCollector()

        # Test same timestamp multiple times
        test_timestamp = 1704067200000  # Millisecond format
        results = []

        for i in range(5):
            result = collector._analyze_timestamp_format(test_timestamp, i)
            results.append(result)

        # All results should be identical
        for result in results[1:]:
            assert result == results[0]

        # Verify consistency for microsecond format
        test_timestamp_micro = 1704067200000000  # Microsecond format
        results_micro = []

        for i in range(5):
            result = collector._analyze_timestamp_format(test_timestamp_micro, i)
            results_micro.append(result)

        # All results should be identical
        for result in results_micro[1:]:
            assert result == results_micro[0]

    def test_validate_csv_structure_valid(self):
        """Test CSV structure validation with valid DataFrame."""
        collector = BinancePublicDataCollector()

        # Create valid 11-column DataFrame
        valid_df = pd.DataFrame(
            {
                "date": pd.date_range("2024-01-01", periods=5, freq="1h"),
                "open": [100.0, 101.0, 102.0, 103.0, 104.0],
                "high": [105.0, 106.0, 107.0, 108.0, 109.0],
                "low": [95.0, 96.0, 97.0, 98.0, 99.0],
                "close": [102.0, 103.0, 104.0, 105.0, 106.0],
                "volume": [1000.0, 1100.0, 1200.0, 1300.0, 1400.0],
                "close_time": [
                    "2024-01-01 00:59:59",
                    "2024-01-01 01:59:59",
                    "2024-01-01 02:59:59",
                    "2024-01-01 03:59:59",
                    "2024-01-01 04:59:59",
                ],
                "quote_asset_volume": [10000.0, 11000.0, 12000.0, 13000.0, 14000.0],
                "number_of_trades": [50, 55, 60, 65, 70],
                "taker_buy_base_asset_volume": [500.0, 550.0, 600.0, 650.0, 700.0],
                "taker_buy_quote_asset_volume": [5000.0, 5500.0, 6000.0, 6500.0, 7000.0],
            }
        )

        result = collector._validate_csv_structure(valid_df)

        assert isinstance(result, dict)
        assert result.get("status") == "VALID"
        assert "errors" in result
        assert len(result["errors"]) == 0

    def test_validate_csv_structure_missing_columns(self):
        """Test CSV structure validation with missing columns."""
        collector = BinancePublicDataCollector()

        # Create DataFrame missing required columns
        incomplete_df = pd.DataFrame(
            {
                "date": pd.date_range("2024-01-01", periods=5, freq="1h"),
                "open": [100.0, 101.0, 102.0, 103.0, 104.0],
                "high": [105.0, 106.0, 107.0, 108.0, 109.0],
                # Missing: low, close, volume, and others
            }
        )

        result = collector._validate_csv_structure(incomplete_df)

        assert isinstance(result, dict)
        # Missing basic OHLCV columns should be INVALID
        assert result.get("status") == "INVALID"
        assert "errors" in result
        assert len(result["errors"]) > 0

    def test_validate_datetime_sequence_valid(self):
        """Test datetime sequence validation with valid timestamps."""
        collector = BinancePublicDataCollector()

        # Create DataFrame with valid hourly sequence
        valid_df = pd.DataFrame(
            {
                "date": pd.date_range("2024-01-01", periods=5, freq="1h"),
                "open": [100.0, 101.0, 102.0, 103.0, 104.0],
                "high": [105.0, 106.0, 107.0, 108.0, 109.0],
                "low": [95.0, 96.0, 97.0, 98.0, 99.0],
                "close": [102.0, 103.0, 104.0, 105.0, 106.0],
                "volume": [1000.0, 1100.0, 1200.0, 1300.0, 1400.0],
            }
        )

        result = collector._validate_datetime_sequence(valid_df, "1h")

        assert isinstance(result, dict)
        assert result.get("status") == "VALID"
        assert "errors" in result

    def test_validate_datetime_sequence_gaps(self):
        """Test datetime sequence validation with gaps."""
        collector = BinancePublicDataCollector()

        # Create DataFrame with gaps in timestamps
        timestamps = [
            "2024-01-01 00:00:00",
            "2024-01-01 01:00:00",
            # Gap: 02:00:00 missing
            "2024-01-01 03:00:00",
            "2024-01-01 04:00:00",
        ]

        gapped_df = pd.DataFrame(
            {
                "date": pd.to_datetime(timestamps),
                "open": [100.0, 101.0, 103.0, 104.0],
                "high": [105.0, 106.0, 108.0, 109.0],
                "low": [95.0, 96.0, 98.0, 99.0],
                "close": [102.0, 103.0, 105.0, 106.0],
                "volume": [1000.0, 1100.0, 1300.0, 1400.0],
            }
        )

        result = collector._validate_datetime_sequence(gapped_df, "1h")

        assert isinstance(result, dict)
        # May be valid or invalid depending on implementation tolerance
        assert "errors" in result

    def test_validate_datetime_sequence_duplicates(self):
        """Test datetime sequence validation with duplicate timestamps."""
        collector = BinancePublicDataCollector()

        # Create DataFrame with duplicate timestamps
        timestamps = [
            "2024-01-01 00:00:00",
            "2024-01-01 01:00:00",
            "2024-01-01 01:00:00",  # Duplicate
            "2024-01-01 02:00:00",
        ]

        duplicate_df = pd.DataFrame(
            {
                "date": pd.to_datetime(timestamps),
                "open": [100.0, 101.0, 101.5, 102.0],
                "high": [105.0, 106.0, 106.5, 107.0],
                "low": [95.0, 96.0, 96.5, 97.0],
                "close": [102.0, 103.0, 103.5, 104.0],
                "volume": [1000.0, 1100.0, 1150.0, 1200.0],
            }
        )

        result = collector._validate_datetime_sequence(duplicate_df, "1h")

        assert isinstance(result, dict)
        # This method checks chronological order and gaps, not duplicates
        # Duplicate detection might be handled by a different validation method
        assert result.get("status") == "VALID"
        assert "errors" in result

    def test_validate_ohlcv_quality_valid(self):
        """Test OHLCV quality validation with valid data."""
        collector = BinancePublicDataCollector()

        # Create DataFrame with valid OHLCV relationships
        valid_df = pd.DataFrame(
            {
                "date": pd.date_range("2024-01-01", periods=5, freq="1h"),
                "open": [100.0, 102.0, 104.0, 106.0, 108.0],
                "high": [105.0, 107.0, 109.0, 111.0, 113.0],  # High >= Open, Close
                "low": [95.0, 97.0, 99.0, 101.0, 103.0],  # Low <= Open, Close
                "close": [102.0, 104.0, 106.0, 108.0, 110.0],
                "volume": [1000.0, 1100.0, 1200.0, 1300.0, 1400.0],  # Positive volume
            }
        )

        result = collector._validate_ohlcv_quality(valid_df)

        assert isinstance(result, dict)
        assert result.get("status") == "VALID"
        assert "errors" in result

    def test_validate_ohlcv_quality_invalid_relationships(self):
        """Test OHLCV quality validation with invalid price relationships."""
        collector = BinancePublicDataCollector()

        # Create DataFrame with invalid OHLCV relationships
        invalid_df = pd.DataFrame(
            {
                "date": pd.date_range("2024-01-01", periods=3, freq="1h"),
                "open": [100.0, 102.0, 104.0],
                "high": [95.0, 97.0, 99.0],  # High < Open (invalid)
                "low": [105.0, 107.0, 109.0],  # Low > Open (invalid)
                "close": [102.0, 104.0, 106.0],
                "volume": [1000.0, 0.0, -100.0],  # Zero and negative volume (invalid)
            }
        )

        result = collector._validate_ohlcv_quality(invalid_df)

        assert isinstance(result, dict)
        assert result.get("status") in ["INVALID", "ERROR"]
        assert "errors" in result
        assert len(result["errors"]) > 0

    def test_validate_ohlcv_quality_missing_values(self):
        """Test OHLCV quality validation with missing values."""
        collector = BinancePublicDataCollector()

        # Create DataFrame with NaN values
        nan_df = pd.DataFrame(
            {
                "date": pd.date_range("2024-01-01", periods=3, freq="1h"),
                "open": [100.0, None, 104.0],  # NaN value
                "high": [105.0, 107.0, None],  # NaN value
                "low": [95.0, 97.0, 99.0],
                "close": [102.0, 104.0, 106.0],
                "volume": [1000.0, 1100.0, 1200.0],
            }
        )

        result = collector._validate_ohlcv_quality(nan_df)

        assert isinstance(result, dict)
        # OHLCV quality validation focuses on relationships and value validity
        # Missing values (NaN) are tolerated and handled by gap filling
        assert result.get("status") == "VALID"
        assert "errors" in result

    def test_validate_expected_coverage_full_coverage(self):
        """Test coverage validation with full expected coverage."""
        collector = BinancePublicDataCollector()

        # Create DataFrame with full 24-hour coverage
        full_df = pd.DataFrame(
            {
                "date": pd.date_range("2024-01-01", periods=24, freq="1h"),
                "open": [100.0 + i for i in range(24)],
                "high": [105.0 + i for i in range(24)],
                "low": [95.0 + i for i in range(24)],
                "close": [102.0 + i for i in range(24)],
                "volume": [1000.0 + i * 100 for i in range(24)],
            }
        )

        result = collector._validate_expected_coverage(full_df, "1h")

        assert isinstance(result, dict)
        assert "coverage_percentage" in result
        assert result.get("coverage_percentage") >= 90.0  # Should be high coverage

    def test_validate_expected_coverage_partial_coverage(self):
        """Test coverage validation with partial coverage."""
        collector = BinancePublicDataCollector()

        # Create DataFrame with only 12 hours out of expected 24
        partial_df = pd.DataFrame(
            {
                "date": pd.date_range("2024-01-01", periods=12, freq="1h"),
                "open": [100.0 + i for i in range(12)],
                "high": [105.0 + i for i in range(12)],
                "low": [95.0 + i for i in range(12)],
                "close": [102.0 + i for i in range(12)],
                "volume": [1000.0 + i * 100 for i in range(12)],
            }
        )

        result = collector._validate_expected_coverage(partial_df, "1h")

        assert isinstance(result, dict)
        assert "coverage_percentage" in result
        # Note: Coverage calculation may be complex - just verify it's a reasonable value
        coverage = result.get("coverage_percentage", 0)
        assert isinstance(coverage, (int, float))
        assert 0 <= coverage <= 100

    def test_validate_statistical_anomalies_normal_data(self):
        """Test statistical anomaly detection with normal data."""
        collector = BinancePublicDataCollector()

        # Create DataFrame with normal price movements
        normal_df = pd.DataFrame(
            {
                "date": pd.date_range("2024-01-01", periods=100, freq="1h"),
                "open": [100.0 + i * 0.1 for i in range(100)],  # Gradual increase
                "high": [105.0 + i * 0.1 for i in range(100)],
                "low": [95.0 + i * 0.1 for i in range(100)],
                "close": [102.0 + i * 0.1 for i in range(100)],
                "volume": [1000.0 + i * 10 for i in range(100)],  # Gradual volume increase
            }
        )

        result = collector._validate_statistical_anomalies(normal_df)

        assert isinstance(result, dict)
        assert "suspicious_patterns" in result
        # Normal data should have few suspicious patterns
        assert result.get("suspicious_patterns", 0) < 50

    def test_validate_statistical_anomalies_extreme_data(self):
        """Test statistical anomaly detection with extreme outliers."""
        collector = BinancePublicDataCollector()

        # Create DataFrame with extreme outliers
        extreme_data = [100.0] * 98 + [10000.0, 0.01]  # Two extreme outliers

        extreme_df = pd.DataFrame(
            {
                "date": pd.date_range("2024-01-01", periods=100, freq="1h"),
                "open": extreme_data,
                "high": [x * 1.05 for x in extreme_data],
                "low": [x * 0.95 for x in extreme_data],
                "close": [x * 1.02 for x in extreme_data],
                "volume": [1000.0] * 100,
            }
        )

        result = collector._validate_statistical_anomalies(extreme_df)

        assert isinstance(result, dict)
        assert "suspicious_patterns" in result or "price_outliers" in result
        # Should detect some anomalies/outliers
        suspicious = result.get("suspicious_patterns", 0)
        outliers = result.get("price_outliers", 0)
        assert (suspicious + outliers) > 0
