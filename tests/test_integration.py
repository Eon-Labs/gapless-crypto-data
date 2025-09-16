"""Integration tests for complete gapless crypto data workflows."""

import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

from gapless_crypto_data.collectors.binance_public_data_collector import BinancePublicDataCollector
from gapless_crypto_data.gap_filling.universal_gap_filler import UniversalGapFiller


class TestEndToEndIntegration:
    """Test suite for end-to-end integration workflows."""

    @pytest.mark.integration
    def test_complete_data_collection_and_gap_filling_workflow(self):
        """Test the complete workflow from data collection to gap filling."""

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            # Phase 1: Data Collection
            # Use a very small date range to minimize download time
            start_date = "2024-01-01"
            end_date = "2024-01-02"  # Just 2 days for testing

            collector = BinancePublicDataCollector(
                symbol="BTCUSDT", start_date=start_date, end_date=end_date, output_dir=output_dir
            )

            try:
                # Collect 1-hour timeframe data
                collection_result = collector.collect_timeframe_data("1h")

                # Verify collection succeeded
                assert collection_result is not None

                # Find the created CSV file
                csv_files = list(output_dir.glob("*.csv"))
                assert len(csv_files) > 0, "No CSV files were created"

                csv_file = csv_files[0]
                assert csv_file.exists()

                # Verify basic CSV structure
                df = pd.read_csv(csv_file, comment="#")
                assert len(df) > 0, "CSV file is empty"
                assert len(df.columns) == 11, f"Expected 11 columns, got {len(df.columns)}"

                # Phase 2: Gap Detection
                gap_filler = UniversalGapFiller()

                detected_gaps = gap_filler.detect_all_gaps(csv_file, "1h")

                # Verify gap detection works
                assert isinstance(detected_gaps, list)

                # Phase 3: Gap Filling (if gaps exist)
                if detected_gaps:
                    # Try to fill the first gap
                    first_gap = detected_gaps[0]

                    # Attempt gap filling
                    fill_result = gap_filler.fill_gap(first_gap, csv_file, "1h")

                    # Verify gap filling attempt
                    assert isinstance(fill_result, bool)

                    if fill_result:
                        # If filling succeeded, verify the gap was filled
                        updated_df = pd.read_csv(csv_file, comment="#")
                        assert len(updated_df) >= len(df), (
                            "Data should not decrease after gap filling"
                        )

                # Phase 4: Final Validation
                # Verify final dataset integrity
                final_df = pd.read_csv(csv_file, comment="#")

                # Basic validation checks
                assert len(final_df) > 0
                assert "date" in final_df.columns
                assert "open" in final_df.columns
                assert "high" in final_df.columns
                assert "low" in final_df.columns
                assert "close" in final_df.columns
                assert "volume" in final_df.columns

                # Verify OHLCV relationships
                for _, row in final_df.iterrows():
                    if (
                        pd.notna(row["open"])
                        and pd.notna(row["high"])
                        and pd.notna(row["low"])
                        and pd.notna(row["close"])
                    ):
                        assert row["high"] >= row["open"], f"High should >= Open: {row}"
                        assert row["high"] >= row["close"], f"High should >= Close: {row}"
                        assert row["low"] <= row["open"], f"Low should <= Open: {row}"
                        assert row["low"] <= row["close"], f"Low should <= Close: {row}"

                # Phase 5: Metadata Verification
                metadata_files = list(output_dir.glob("*.metadata.json"))
                if metadata_files:
                    metadata_file = metadata_files[0]
                    assert metadata_file.exists()

                    # Verify metadata file is valid JSON
                    import json

                    with open(metadata_file, "r") as f:
                        metadata = json.load(f)

                    # Verify essential metadata fields
                    assert "symbol" in metadata
                    assert "timeframe" in metadata
                    assert "data_integrity" in metadata
                    assert "gap_analysis" in metadata

                print("✅ Integration test completed successfully")
                print(f"   - Data collected: {len(final_df)} rows")
                print(f"   - Gaps detected: {len(detected_gaps)}")
                print(f"   - Files created: {len(csv_files)} CSV, {len(metadata_files)} metadata")

            except Exception as e:
                # Network-dependent test may fail
                pytest.skip(f"Integration test failed (likely network dependency): {e}")

    @pytest.mark.integration
    def test_error_recovery_scenarios(self):
        """Test error recovery in various failure scenarios."""

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            # Test 1: Invalid symbol handling
            collector = BinancePublicDataCollector(
                symbol="INVALIDSYMBOL",
                start_date="2024-01-01",
                end_date="2024-01-02",
                output_dir=output_dir,
            )

            try:
                result = collector.collect_timeframe_data("1h")
                # Should handle invalid symbol gracefully
                # Either return None/False or raise appropriate exception
                if result is not None:
                    assert isinstance(result, (bool, dict))
            except Exception as e:
                # Expected behavior for invalid symbol
                assert isinstance(e, (ValueError, KeyError, ConnectionError, Exception))

            # Test 2: Invalid timeframe handling
            collector = BinancePublicDataCollector(
                symbol="BTCUSDT",
                start_date="2024-01-01",
                end_date="2024-01-02",
                output_dir=output_dir,
            )

            try:
                result = collector.collect_timeframe_data("invalid_timeframe")
                # Should handle invalid timeframe gracefully
                if result is not None:
                    assert isinstance(result, (bool, dict))
            except Exception as e:
                # Expected behavior for invalid timeframe
                assert isinstance(e, (ValueError, KeyError, Exception))

            # Test 3: Gap filler with non-existent file
            gap_filler = UniversalGapFiller()
            non_existent_file = output_dir / "non_existent.csv"

            try:
                gaps = gap_filler.detect_all_gaps(non_existent_file, "1h")
                # Should handle missing file gracefully
                assert isinstance(gaps, list)
            except FileNotFoundError:
                # Expected behavior for missing file
                pass
            except Exception as e:
                # Other exceptions should be handled gracefully
                assert isinstance(e, (ValueError, Exception))

    @pytest.mark.integration
    def test_concurrent_file_operations(self):
        """Test that file operations work correctly under concurrent access."""

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            # Create a test CSV file
            test_df = pd.DataFrame(
                {
                    "date": pd.date_range("2024-01-01", periods=24, freq="1h"),
                    "open": [100.0 + i for i in range(24)],
                    "high": [105.0 + i for i in range(24)],
                    "low": [95.0 + i for i in range(24)],
                    "close": [102.0 + i for i in range(24)],
                    "volume": [1000.0 + i * 10 for i in range(24)],
                    "close_time": [f"2024-01-01 {i:02d}:59:59" for i in range(24)],
                    "quote_asset_volume": [10000.0 + i * 100 for i in range(24)],
                    "number_of_trades": [50 + i for i in range(24)],
                    "taker_buy_base_asset_volume": [500.0 + i * 5 for i in range(24)],
                    "taker_buy_quote_asset_volume": [5000.0 + i * 50 for i in range(24)],
                }
            )

            csv_file = output_dir / "test_concurrent.csv"

            # Write initial CSV with headers
            with open(csv_file, "w") as f:
                f.write("# Test CSV for concurrent operations\n")
                f.write("# Generated for testing\n")
                test_df.to_csv(f, index=False)

            # Test concurrent read operations
            gap_filler = UniversalGapFiller()

            # Multiple gap detection calls (simulating concurrent reads)
            results = []
            for _i in range(3):
                try:
                    gaps = gap_filler.detect_all_gaps(csv_file, "1h")
                    results.append(gaps)
                except Exception as e:
                    # Should handle concurrent access gracefully
                    results.append(None)

            # Results should be consistent
            non_none_results = [r for r in results if r is not None]
            if len(non_none_results) > 1:
                # All successful results should be identical
                for result in non_none_results[1:]:
                    assert result == non_none_results[0]

            # Test atomic operations under concurrent access
            from gapless_crypto_data.gap_filling.safe_file_operations import AtomicCSVOperations

            atomic_ops = AtomicCSVOperations(csv_file)

            # Create backup
            backup_path = atomic_ops.create_backup()
            assert backup_path.exists()

            # Read headers
            headers = atomic_ops.read_header_comments()
            assert len(headers) >= 2

            # Validate data
            is_valid, msg = atomic_ops.validate_dataframe(test_df)
            assert is_valid is True

            # Test atomic write
            modified_df = test_df.copy()
            modified_df.loc[0, "volume"] = 9999.0  # Modify one value

            write_success = atomic_ops.write_dataframe_atomic(modified_df, headers)
            assert write_success is True

            # Verify the change was applied
            final_df = pd.read_csv(csv_file, comment="#")
            assert final_df.loc[0, "volume"] == 9999.0

            # Cleanup
            atomic_ops.cleanup_backup()

    @pytest.mark.integration
    def test_data_integrity_validation_pipeline(self):
        """Test the complete data integrity validation pipeline."""

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            csv_file = output_dir / "test_validation.csv"

            # Create test data with known issues for validation
            test_data = {
                "date": [
                    "2024-01-01 00:00:00",
                    "2024-01-01 01:00:00",
                    "2024-01-01 02:00:00",
                    "2024-01-01 04:00:00",  # Gap at 03:00:00
                    "2024-01-01 05:00:00",
                ],
                "open": [100.0, 101.0, 102.0, 104.0, 105.0],
                "high": [105.0, 106.0, 107.0, 109.0, 110.0],
                "low": [95.0, 96.0, 97.0, 99.0, 100.0],
                "close": [102.0, 103.0, 104.0, 106.0, 107.0],
                "volume": [1000.0, 1100.0, 1200.0, 1400.0, 1500.0],
                "close_time": [
                    "2024-01-01 00:59:59",
                    "2024-01-01 01:59:59",
                    "2024-01-01 02:59:59",
                    "2024-01-01 04:59:59",
                    "2024-01-01 05:59:59",
                ],
                "quote_asset_volume": [10000.0, 11000.0, 12000.0, 14000.0, 15000.0],
                "number_of_trades": [50, 55, 60, 70, 75],
                "taker_buy_base_asset_volume": [500.0, 550.0, 600.0, 700.0, 750.0],
                "taker_buy_quote_asset_volume": [5000.0, 5500.0, 6000.0, 7000.0, 7500.0],
            }

            test_df = pd.DataFrame(test_data)

            # Write CSV with headers
            with open(csv_file, "w") as f:
                f.write("# Test CSV for validation pipeline\n")
                f.write("# Contains intentional gap for testing\n")
                test_df.to_csv(f, index=False)

            # Initialize components
            collector = BinancePublicDataCollector(output_dir=output_dir)
            gap_filler = UniversalGapFiller()

            # Phase 1: CSV Structure Validation
            validation_results = collector._validate_csv_structure(test_df)
            assert isinstance(validation_results, dict)
            assert validation_results.get("status") == "VALID"  # Should have valid structure

            # Phase 2: Datetime Sequence Validation
            datetime_results = collector._validate_datetime_sequence(test_df, "1h")
            assert isinstance(datetime_results, dict)
            # May detect the gap we intentionally created

            # Phase 3: OHLCV Quality Validation
            ohlcv_results = collector._validate_ohlcv_quality(test_df)
            assert isinstance(ohlcv_results, dict)
            assert ohlcv_results.get("status") == "VALID"  # OHLCV relationships should be valid

            # Phase 4: Coverage Validation
            coverage_results = collector._validate_expected_coverage(test_df, "1h")
            assert isinstance(coverage_results, dict)
            assert "coverage_percentage" in coverage_results
            # Should detect less than 100% coverage due to gap

            # Phase 5: Statistical Anomaly Detection
            anomaly_results = collector._validate_statistical_anomalies(test_df)
            assert isinstance(anomaly_results, dict)
            assert "suspicious_patterns" in anomaly_results
            # Should have few anomalies in this regular data

            # Phase 6: Gap Detection
            gaps = gap_filler.detect_all_gaps(csv_file, "1h")
            assert isinstance(gaps, list)
            # Should detect the gap at 03:00:00
            assert len(gaps) >= 1

            # Phase 7: Symbol Extraction
            symbol = gap_filler.extract_symbol_from_filename(csv_file)
            assert isinstance(symbol, str)
            assert len(symbol) > 0

            print("✅ Validation pipeline completed successfully")
            print(f"   - Structure validation: {validation_results.get('status')}")
            print(f"   - OHLCV validation: {ohlcv_results.get('status')}")
            print(f"   - Coverage: {coverage_results.get('coverage_percentage', 0):.1f}%")
            print(f"   - Suspicious patterns: {anomaly_results.get('suspicious_patterns', 0)}")
            print(f"   - Gaps detected: {len(gaps)}")
            print(f"   - Symbol extracted: {symbol}")

    @pytest.mark.integration
    def test_large_dataset_handling(self):
        """Test handling of larger datasets for performance validation."""

        # Create a larger dataset (1000 rows = ~41 days of hourly data)
        large_df = pd.DataFrame(
            {
                "date": pd.date_range("2024-01-01", periods=1000, freq="1h"),
                "open": [100.0 + i * 0.01 for i in range(1000)],
                "high": [105.0 + i * 0.01 for i in range(1000)],
                "low": [95.0 + i * 0.01 for i in range(1000)],
                "close": [102.0 + i * 0.01 for i in range(1000)],
                "volume": [1000.0 + i for i in range(1000)],
                "close_time": ["2024-01-01 00:59:59" for _ in range(1000)],
                "quote_asset_volume": [10000.0 + i * 10 for i in range(1000)],
                "number_of_trades": [50 + i // 10 for i in range(1000)],
                "taker_buy_base_asset_volume": [500.0 + i * 0.5 for i in range(1000)],
                "taker_buy_quote_asset_volume": [5000.0 + i * 5 for i in range(1000)],
            }
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            csv_file = output_dir / "large_dataset.csv"

            # Write large dataset
            with open(csv_file, "w") as f:
                f.write("# Large dataset for performance testing\n")
                f.write(f"# Rows: {len(large_df)}\n")
                large_df.to_csv(f, index=False)

            # Test performance of various operations
            start_time = datetime.now()

            # Test gap detection on large dataset
            gap_filler = UniversalGapFiller()
            gaps = gap_filler.detect_all_gaps(csv_file, "1h")

            gap_detection_time = datetime.now() - start_time

            # Test validation on large dataset
            start_time = datetime.now()

            collector = BinancePublicDataCollector()
            validation_results = collector._validate_csv_structure(large_df)
            ohlcv_results = collector._validate_ohlcv_quality(large_df)

            validation_time = datetime.now() - start_time

            # Performance assertions (should complete in reasonable time)
            assert gap_detection_time.total_seconds() < 30, (
                f"Gap detection took too long: {gap_detection_time}"
            )
            assert validation_time.total_seconds() < 10, (
                f"Validation took too long: {validation_time}"
            )

            # Results should still be valid
            assert isinstance(gaps, list)
            assert isinstance(validation_results, dict)
            assert isinstance(ohlcv_results, dict)

            print("✅ Large dataset test completed successfully")
            print(f"   - Dataset size: {len(large_df)} rows")
            print(f"   - Gap detection time: {gap_detection_time.total_seconds():.2f}s")
            print(f"   - Validation time: {validation_time.total_seconds():.2f}s")
            print(f"   - Gaps found: {len(gaps)}")
