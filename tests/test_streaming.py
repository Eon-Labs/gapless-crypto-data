"""
Tests for memory-streaming architecture using Polars.

Verifies SOTA streaming capabilities for unlimited dataset processing.
"""

import csv
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import polars as pl
import pytest

from gapless_crypto_data.streaming import StreamingDataProcessor, StreamingGapFiller
from gapless_crypto_data.utils.error_handling import DataCollectionError


class TestStreamingDataProcessor:
    """Test SOTA memory-streaming processor with Polars."""

    def setup_method(self):
        """Setup test fixtures."""
        self.processor = StreamingDataProcessor(chunk_size=5, memory_limit_mb=10)

    def create_test_csv(self, csv_path: Path, rows: int = 20, has_gaps: bool = False) -> Path:
        """Create test CSV file with OHLCV data."""
        csv_file = csv_path if csv_path.suffix else csv_path / "test_data.csv"
        csv_file.parent.mkdir(parents=True, exist_ok=True)

        start_time = datetime(2024, 1, 1)

        with open(csv_file, "w", newline="") as f:
            writer = csv.writer(f)

            # Write header
            writer.writerow(
                [
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
            )

            # Write data rows
            current_time = start_time
            for i in range(rows):
                timestamp = current_time
                close_time = timestamp + timedelta(minutes=1)

                # Increment time for next iteration
                current_time += timedelta(minutes=1)  # 1 minute intervals

                # Create gap if requested (after this row but before next)
                if has_gaps and i == 9:  # After 10th row (0-indexed)
                    current_time += timedelta(minutes=3)  # Add 3-minute gap

                writer.writerow(
                    [
                        timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        100.0 + i,
                        101.0 + i,
                        99.0 + i,
                        100.5 + i,
                        1000.0,
                        close_time.strftime("%Y-%m-%d %H:%M:%S"),
                        100500.0,
                        50,
                        500.0,
                        50250.0,
                    ]
                )

        return csv_file

    def test_stream_csv_chunks(self):
        """Test streaming CSV file in chunks."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            csv_file = self.create_test_csv(temp_path, rows=20)

            # Test streaming chunks
            chunks = list(self.processor.stream_csv_chunks(csv_file))

            # Verify chunks
            assert len(chunks) == 4  # 20 rows / 5 chunk_size = 4 chunks

            total_rows = sum(len(chunk) for chunk in chunks)
            assert total_rows == 20

            # Verify first chunk structure
            first_chunk = chunks[0]
            assert "date" in first_chunk.columns
            assert "open" in first_chunk.columns
            assert "close" in first_chunk.columns
            assert len(first_chunk) == 5

    def test_stream_csv_chunks_file_not_found(self):
        """Test streaming with non-existent file."""
        with pytest.raises(DataCollectionError) as exc_info:
            list(self.processor.stream_csv_chunks("/nonexistent/file.csv"))

        assert "CSV file not found" in str(exc_info.value)

    def test_stream_gap_detection_no_gaps(self):
        """Test gap detection with continuous data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            csv_file = self.create_test_csv(temp_path, rows=20, has_gaps=False)

            # Test gap detection
            result = self.processor.stream_gap_detection(csv_file, "1m")

            # Verify results
            assert result["total_gaps_detected"] == 0
            assert result["total_rows_processed"] == 20
            assert result["data_completeness_score"] == 1.0
            assert result["streaming_method"] == "polars_lazy_evaluation"

    def test_stream_gap_detection_with_gaps(self):
        """Test gap detection with data gaps."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            csv_file = self.create_test_csv(temp_path, rows=20, has_gaps=True)

            # Test gap detection
            result = self.processor.stream_gap_detection(csv_file, "1m")

            # Verify gap detection
            assert result["total_gaps_detected"] == 1
            assert result["total_rows_processed"] == 20
            assert result["data_completeness_score"] < 1.0

            # Verify gap details
            gap_details = result["gaps_details"][0]
            assert gap_details["missing_bars"] == 3  # 3-minute gap in 1-minute data

    def test_stream_csv_merge(self):
        """Test streaming CSV merging."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create multiple CSV files
            csv1 = self.create_test_csv(temp_path / "file1.csv", rows=10)
            csv2 = self.create_test_csv(temp_path / "file2.csv", rows=15)

            output_file = temp_path / "merged.csv"

            # Test merging
            result = self.processor.stream_csv_merge([csv1, csv2], output_file)

            # Verify merge results
            assert result["files_processed"] == 2
            assert result["total_rows_merged"] == 25
            assert result["merge_method"] == "polars_streaming"
            assert result["memory_efficient"] is True

            # Verify output file exists
            assert output_file.exists()

            # Verify merged content
            merged_df = pl.read_csv(str(output_file))
            assert len(merged_df) == 25

    def test_parse_timeframe_minutes(self):
        """Test timeframe parsing to minutes."""
        # Test valid timeframes
        assert self.processor._parse_timeframe_minutes("1m") == 1
        assert self.processor._parse_timeframe_minutes("5m") == 5
        assert self.processor._parse_timeframe_minutes("1h") == 60
        assert self.processor._parse_timeframe_minutes("4h") == 240
        assert self.processor._parse_timeframe_minutes("1d") == 1440

        # Test invalid timeframe
        with pytest.raises(DataCollectionError) as exc_info:
            self.processor._parse_timeframe_minutes("invalid")

        assert "Invalid timeframe format" in str(exc_info.value)


class TestStreamingGapFiller:
    """Test SOTA streaming gap filler."""

    def setup_method(self):
        """Setup test fixtures."""
        self.gap_filler = StreamingGapFiller(chunk_size=5)

    def create_test_csv_with_gaps(self, temp_dir: Path) -> Path:
        """Create test CSV with known gaps."""
        csv_file = temp_dir / "gap_test.csv"

        start_time = datetime(2024, 1, 1)

        with open(csv_file, "w", newline="") as f:
            writer = csv.writer(f)

            # Write header
            writer.writerow(
                [
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
            )

            # Write data with gaps
            timestamps = [
                start_time,
                start_time + timedelta(minutes=1),
                start_time + timedelta(minutes=2),
                # Gap here - missing minute 3 and 4
                start_time + timedelta(minutes=5),
                start_time + timedelta(minutes=6),
            ]

            for i, timestamp in enumerate(timestamps):
                close_time = timestamp + timedelta(minutes=1)
                writer.writerow(
                    [
                        timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        100.0 + i,
                        101.0 + i,
                        99.0 + i,
                        100.5 + i,
                        1000.0,
                        close_time.strftime("%Y-%m-%d %H:%M:%S"),
                        100500.0,
                        50,
                        500.0,
                        50250.0,
                    ]
                )

        return csv_file

    def test_stream_fill_gaps_no_gaps(self):
        """Test streaming gap filling with no gaps."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create CSV without gaps
            processor = StreamingDataProcessor(chunk_size=5)
            csv_file = processor.create_test_csv = (
                lambda p, r=10, g=False: self.create_continuous_csv(p, r)
            )
            csv_file = self.create_continuous_csv(temp_path)

            # Test gap filling
            result = self.gap_filler.stream_fill_gaps(csv_file, "1m")

            # Verify no gaps found
            assert result["gaps_filled"] == 0
            assert result["gaps_remaining"] == 0
            assert result["streaming_processed"] is True

    def test_stream_fill_gaps_with_gaps(self):
        """Test streaming gap filling with gaps detected."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            csv_file = self.create_test_csv_with_gaps(temp_path)

            # Test gap filling
            result = self.gap_filler.stream_fill_gaps(csv_file, "1m")

            # Verify gaps detected
            assert result["gaps_detected"] == 1
            assert result["gaps_remaining"] == 1  # Framework only - actual filling not implemented
            assert result["streaming_processed"] is True
            assert len(result["gap_details"]) == 1

    def create_continuous_csv(self, temp_dir: Path, rows: int = 10) -> Path:
        """Create continuous CSV without gaps."""
        csv_file = temp_dir / "continuous.csv"

        start_time = datetime(2024, 1, 1)

        with open(csv_file, "w", newline="") as f:
            writer = csv.writer(f)

            # Write header
            writer.writerow(
                [
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
            )

            # Write continuous data
            for i in range(rows):
                timestamp = start_time + timedelta(minutes=i)
                close_time = timestamp + timedelta(minutes=1)

                writer.writerow(
                    [
                        timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        100.0 + i,
                        101.0 + i,
                        99.0 + i,
                        100.5 + i,
                        1000.0,
                        close_time.strftime("%Y-%m-%d %H:%M:%S"),
                        100500.0,
                        50,
                        500.0,
                        50250.0,
                    ]
                )

        return csv_file
