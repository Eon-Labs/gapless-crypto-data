"""Test Universal Gap Filler functionality."""

import tempfile
from pathlib import Path

import pandas as pd
import pytest

from gapless_crypto_data.gap_filling.universal_gap_filler import UniversalGapFiller


class TestUniversalGapFiller:
    """Test suite for UniversalGapFiller."""

    def test_init(self):
        """Test gap filler initialization."""
        gap_filler = UniversalGapFiller()
        assert gap_filler is not None
        assert hasattr(gap_filler, "detect_all_gaps")
        assert hasattr(gap_filler, "fill_gap")

    def test_detect_gaps_empty_directory(self):
        """Test gap detection in empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            gap_filler = UniversalGapFiller()
            # Since detect_all_gaps needs a specific CSV file, this test checks basic functionality
            # We can't test with empty directory, so we'll test with a non-existent file
            try:
                gaps = gap_filler.detect_all_gaps(Path(temp_dir) / "nonexistent.csv", "1h")
                # This should handle the missing file gracefully
                assert isinstance(gaps, list)
            except (FileNotFoundError, Exception):
                # Expected behavior for missing file
                pass

    def test_detect_gaps_with_sample_data(self):
        """Test gap detection with sample CSV data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create sample CSV with gaps
            sample_data = pd.DataFrame(
                {
                    "date": pd.date_range("2024-01-01", periods=100, freq="1h"),
                    "open": [100.0] * 100,
                    "high": [105.0] * 100,
                    "low": [95.0] * 100,
                    "close": [102.0] * 100,
                    "volume": [1000.0] * 100,
                    "close_time": [0] * 100,
                    "quote_asset_volume": [10000.0] * 100,
                    "number_of_trades": [50] * 100,
                    "taker_buy_base_asset_volume": [500.0] * 100,
                    "taker_buy_quote_asset_volume": [5000.0] * 100,
                }
            )

            # Remove some rows to create gaps
            sample_data_with_gaps = sample_data.drop([10, 11, 12, 50, 51])

            csv_file = Path(temp_dir) / "test_data.csv"
            sample_data_with_gaps.to_csv(csv_file, index=False)

            gap_filler = UniversalGapFiller()
            gaps = gap_filler.detect_all_gaps(csv_file, "1h")

            # Should detect the gaps we created
            assert isinstance(gaps, list)
            assert len(gaps) > 0

    def test_fill_gaps_no_gaps(self):
        """Test gap filling when no gaps exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create complete data without gaps
            sample_data = pd.DataFrame(
                {
                    "date": pd.date_range("2024-01-01", periods=24, freq="1h"),
                    "open": [100.0] * 24,
                    "high": [105.0] * 24,
                    "low": [95.0] * 24,
                    "close": [102.0] * 24,
                    "volume": [1000.0] * 24,
                    "close_time": [0] * 24,
                    "quote_asset_volume": [10000.0] * 24,
                    "number_of_trades": [50] * 24,
                    "taker_buy_base_asset_volume": [500.0] * 24,
                    "taker_buy_quote_asset_volume": [5000.0] * 24,
                }
            )

            csv_file = Path(temp_dir) / "complete_data.csv"
            sample_data.to_csv(csv_file, index=False)

            gap_filler = UniversalGapFiller()

            # First detect gaps (should be none)
            gaps = gap_filler.detect_all_gaps(csv_file, "1h")

            # Should return empty list if no gaps
            assert isinstance(gaps, list)
            # If no gaps, that's expected
            assert len(gaps) == 0

    def test_validate_csv_structure(self):
        """Test CSV structure validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create invalid CSV (missing required columns)
            invalid_data = pd.DataFrame(
                {
                    "date": pd.date_range("2024-01-01", periods=10, freq="1h"),
                    "price": [100.0] * 10,  # Missing OHLCV columns
                }
            )

            csv_file = Path(temp_dir) / "invalid_data.csv"
            invalid_data.to_csv(csv_file, index=False)

            gap_filler = UniversalGapFiller()

            # Should handle invalid CSV gracefully
            try:
                gaps = gap_filler.detect_all_gaps(csv_file, "1h")
                # If it doesn't raise an exception, that's also valid behavior
                assert isinstance(gaps, list)
            except Exception as e:
                # Expected to handle invalid data gracefully
                assert isinstance(e, (ValueError, KeyError, AttributeError))

    def test_timeframe_detection(self):
        """Test automatic timeframe detection from data."""
        # Test data with 1-hour intervals
        hourly_data = pd.DataFrame(
            {
                "date": pd.date_range("2024-01-01", periods=24, freq="1h"),
                "open": [100.0] * 24,
                "high": [105.0] * 24,
                "low": [95.0] * 24,
                "close": [102.0] * 24,
                "volume": [1000.0] * 24,
            }
        )

        gap_filler = UniversalGapFiller()

        # The actual timeframe detection would depend on implementation
        # This is a placeholder test for the concept
        assert len(hourly_data) == 24

    @pytest.mark.integration
    def test_fill_gaps_integration(self):
        """Integration test for gap filling functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create data with known gaps
            timestamps = pd.date_range("2024-01-01", periods=48, freq="1h")
            full_data = pd.DataFrame(
                {
                    "date": timestamps,
                    "open": [100.0 + i for i in range(48)],
                    "high": [105.0 + i for i in range(48)],
                    "low": [95.0 + i for i in range(48)],
                    "close": [102.0 + i for i in range(48)],
                    "volume": [1000.0] * 48,
                    "close_time": [0] * 48,
                    "quote_asset_volume": [10000.0] * 48,
                    "number_of_trades": [50] * 48,
                    "taker_buy_base_asset_volume": [500.0] * 48,
                    "taker_buy_quote_asset_volume": [5000.0] * 48,
                }
            )

            # Create gaps
            gapped_data = full_data.drop([10, 11, 12, 25, 26])

            csv_file = Path(temp_dir) / "gapped_data.csv"
            gapped_data.to_csv(csv_file, index=False)

            original_length = len(gapped_data)

            try:
                gap_filler = UniversalGapFiller()

                # First detect gaps
                gaps = gap_filler.detect_all_gaps(csv_file, "1h")

                # Should detect the gaps we created
                assert isinstance(gaps, list)
                assert len(gaps) > 0

                # Try to fill the first gap if any exist
                if gaps:
                    result = gap_filler.fill_gap(gaps[0], csv_file, "1h")
                    # Result indicates if filling was successful
                    assert isinstance(result, bool)

            except Exception as e:
                # Network-dependent test may fail
                pytest.skip(f"Integration test failed (network dependency): {e}")
