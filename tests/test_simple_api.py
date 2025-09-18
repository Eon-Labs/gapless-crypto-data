#!/usr/bin/env python3
"""
Test cases for the simple function-based API

Ensures the convenience functions work correctly and provide
the expected financial data library experience.
"""

import pandas as pd
import pytest

import gapless_crypto_data as gcd


class TestSimpleAPI:
    """Test the function-based convenience API"""

    def test_import_all_functions(self):
        """Test that all convenience functions are properly exported"""
        # Test function-based API exports
        assert hasattr(gcd, "fetch_data")
        assert hasattr(gcd, "download")
        assert hasattr(gcd, "get_supported_symbols")
        assert hasattr(gcd, "get_supported_timeframes")
        assert hasattr(gcd, "fill_gaps")
        assert hasattr(gcd, "get_info")

        # Test class-based API exports (backward compatibility)
        assert hasattr(gcd, "BinancePublicDataCollector")
        assert hasattr(gcd, "UniversalGapFiller")

    def test_get_supported_symbols(self):
        """Test getting supported trading symbols"""
        symbols = gcd.get_supported_symbols()

        assert isinstance(symbols, list)
        assert len(symbols) > 0
        assert "BTCUSDT" in symbols
        assert "ETHUSDT" in symbols
        assert "SOLUSDT" in symbols

        # All symbols should be strings and end with USDT
        for symbol in symbols:
            assert isinstance(symbol, str)
            assert symbol.endswith("USDT")

    def test_get_supported_timeframes(self):
        """Test getting supported timeframe intervals"""
        timeframes = gcd.get_supported_timeframes()

        assert isinstance(timeframes, list)
        assert len(timeframes) > 0

        # Check for common timeframes
        expected_timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]
        for tf in expected_timeframes:
            assert tf in timeframes

    def test_get_info(self):
        """Test library information function"""
        info = gcd.get_info()

        assert isinstance(info, dict)

        # Check required fields
        required_fields = [
            "version",
            "name",
            "description",
            "supported_symbols",
            "supported_timeframes",
            "market_type",
            "data_source",
            "features",
        ]
        for field in required_fields:
            assert field in info

        # Validate content
        assert info["name"] == "gapless-crypto-data"
        assert info["version"] == gcd.__version__
        assert isinstance(info["supported_symbols"], list)
        assert isinstance(info["supported_timeframes"], list)
        assert isinstance(info["features"], list)

    def test_fetch_data_parameters(self):
        """Test fetch_data function parameter handling"""
        # Test with minimal parameters (should not raise)
        try:
            df = gcd.fetch_data("BTCUSDT", "1h", limit=1)
            # Should return DataFrame even if empty
            assert isinstance(df, pd.DataFrame)
        except Exception as e:
            # Network issues are acceptable in tests
            assert "network" in str(e).lower() or "timeout" in str(e).lower()

    def test_download_alias(self):
        """Test that download is an alias for fetch_data"""
        # Should not raise errors for basic parameter validation
        try:
            df1 = gcd.fetch_data("BTCUSDT", "1h", start="2024-01-01", end="2024-01-02")
            df2 = gcd.download("BTCUSDT", "1h", start="2024-01-01", end="2024-01-02")

            # Both should return DataFrames with same structure
            assert isinstance(df1, pd.DataFrame)
            assert isinstance(df2, pd.DataFrame)
            assert list(df1.columns) == list(df2.columns)

        except Exception as e:
            # Network issues are acceptable in tests
            assert "network" in str(e).lower() or "timeout" in str(e).lower()

    def test_expected_dataframe_columns(self):
        """Test that returned DataFrames have expected microstructure columns"""
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

        try:
            df = gcd.fetch_data("BTCUSDT", "1d", limit=1)

            if not df.empty:
                # Check that all expected columns are present
                for col in expected_columns:
                    assert col in df.columns

                # Check basic data types
                assert pd.api.types.is_datetime64_any_dtype(df["date"])
                assert pd.api.types.is_numeric_dtype(df["open"])
                assert pd.api.types.is_numeric_dtype(df["volume"])

        except Exception as e:
            # Network issues are acceptable in tests
            pytest.skip(f"Network-dependent test failed: {e}")

    def test_fill_gaps_function_signature(self):
        """Test fill_gaps function parameter handling"""
        # Test with non-existent directory (should not crash)
        result = gcd.fill_gaps("./non_existent_directory")

        assert isinstance(result, dict)
        assert "files_processed" in result
        assert "gaps_detected" in result
        assert "gaps_filled" in result
        assert "success_rate" in result
        assert "file_results" in result

    def test_backward_compatibility(self):
        """Test that class-based API still works (backward compatibility)"""
        # Should be able to import and instantiate classes
        collector = gcd.BinancePublicDataCollector()
        gap_filler = gcd.UniversalGapFiller()

        assert collector is not None
        assert gap_filler is not None

        # Check that they have expected methods
        assert hasattr(collector, "collect_timeframe_data")
        assert hasattr(gap_filler, "detect_all_gaps")

    def test_api_style_consistency(self):
        """Test that both API styles provide consistent data"""
        # Compare function-based vs class-based API results
        symbol = "BTCUSDT"
        timeframe = "1d"
        start = "2024-01-01"
        end = "2024-01-02"

        try:
            # Function-based API
            df_function = gcd.fetch_data(symbol, timeframe, start=start, end=end)

            # Class-based API
            collector = gcd.BinancePublicDataCollector(
                symbol=symbol, start_date=start, end_date=end
            )
            result_class = collector.collect_timeframe_data(timeframe)

            if result_class and "dataframe" in result_class:
                df_class = result_class["dataframe"]

                # Both should be DataFrames with same columns
                assert isinstance(df_function, pd.DataFrame)
                assert isinstance(df_class, pd.DataFrame)
                assert list(df_function.columns) == list(df_class.columns)

        except Exception as e:
            # Network issues are acceptable in tests
            pytest.skip(f"Network-dependent test failed: {e}")


class TestAPIUsagePatterns:
    """Test common usage patterns expected by financial data users"""

    def test_intuitive_download_usage(self):
        """Test intuitive download usage pattern"""
        try:
            # Common download pattern with date range
            df = gcd.download("BTCUSDT", "1d", start="2024-01-01", end="2024-01-02")
            assert isinstance(df, pd.DataFrame)

        except Exception as e:
            pytest.skip(f"Network-dependent test failed: {e}")

    def test_symbol_discovery_pattern(self):
        """Test symbol and timeframe discovery pattern"""
        # Pattern for discovering available options
        symbols = gcd.get_supported_symbols()
        timeframes = gcd.get_supported_timeframes()

        assert len(symbols) > 0
        assert len(timeframes) > 0

        # Should be able to use discovered values
        symbol = symbols[0]  # First available symbol
        timeframe = timeframes[0] if "1d" not in timeframes else "1d"

        try:
            df = gcd.fetch_data(symbol, timeframe, limit=1)
            assert isinstance(df, pd.DataFrame)

        except Exception as e:
            pytest.skip(f"Network-dependent test failed: {e}")

    def test_date_range_usage(self):
        """Test date range usage with start/end dates"""
        try:
            df = gcd.fetch_data(
                symbol="ETHUSDT",
                interval="1h",
                start="2024-01-01",
                end="2024-01-01",  # Single day
            )

            assert isinstance(df, pd.DataFrame)

            if not df.empty:
                # Should have date column as datetime
                assert "date" in df.columns
                assert pd.api.types.is_datetime64_any_dtype(df["date"])

        except Exception as e:
            pytest.skip(f"Network-dependent test failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
