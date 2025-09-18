"""
Tests for SOTA regression detection system.

Verifies evidently and pyod integration for comprehensive data quality monitoring.
"""

import tempfile
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from gapless_crypto_data.regression import DataQualityMonitor, RegressionDetector
from gapless_crypto_data.utils.error_handling import DataCollectionError


class TestRegressionDetector:
    """Test SOTA regression detection with evidently and pyod."""

    def setup_method(self):
        """Setup test fixtures."""
        self.detector = RegressionDetector(anomaly_contamination=0.1, drift_threshold=0.1)

    def create_ohlcv_data(
        self,
        rows: int = 100,
        start_date: str = "2024-01-01",
        add_anomalies: bool = False,
        drift_factor: float = 1.0,
    ) -> pd.DataFrame:
        """Create realistic OHLCV test data."""
        start_time = pd.to_datetime(start_date)
        dates = pd.date_range(start_time, periods=rows, freq="h")

        # Generate correlated price data
        np.random.seed(42)
        base_price = 50000.0 * drift_factor
        price_changes = np.random.normal(0, 0.01, rows)
        prices = [base_price]

        for change in price_changes[:-1]:
            prices.append(prices[-1] * (1 + change))

        opens = np.array(prices)

        # Generate realistic OHLC from opens
        highs = opens * (1 + np.abs(np.random.normal(0, 0.005, rows)))
        lows = opens * (1 - np.abs(np.random.normal(0, 0.005, rows)))
        closes = opens + np.random.normal(0, opens * 0.002, rows)

        # Ensure OHLC consistency
        highs = np.maximum.reduce([opens, highs, closes])
        lows = np.minimum.reduce([opens, lows, closes])

        # Generate volume data
        volumes = np.random.exponential(1000, rows)

        # Add anomalies if requested
        if add_anomalies:
            anomaly_indices = np.random.choice(rows, size=int(rows * 0.05), replace=False)
            highs[anomaly_indices] *= 2  # Price spikes
            volumes[anomaly_indices] *= 10  # Volume spikes

        data = pd.DataFrame(
            {
                "date": dates,
                "open": opens,
                "high": highs,
                "low": lows,
                "close": closes,
                "volume": volumes,
                "close_time": dates + timedelta(hours=1),
                "quote_asset_volume": volumes * closes,
                "number_of_trades": np.random.poisson(100, rows),
                "taker_buy_base_asset_volume": volumes * 0.6,
                "taker_buy_quote_asset_volume": volumes * closes * 0.6,
            }
        )

        return data

    def test_detect_data_drift_no_drift(self):
        """Test drift detection with similar datasets."""
        reference_data = self.create_ohlcv_data(rows=100)
        current_data = self.create_ohlcv_data(rows=100, start_date="2024-01-05")

        result = self.detector.detect_data_drift(reference_data, current_data)

        # Verify result structure
        assert "timestamp" in result
        assert "dataset_drift_detected" in result
        assert "drift_score" in result
        assert "method" in result
        assert result["method"] == "statistical_drift_detection"

        # With similar data, drift should be minimal
        assert isinstance(result["dataset_drift_detected"], bool)
        assert isinstance(result["drift_score"], (int, float))

    def test_detect_data_drift_with_drift(self):
        """Test drift detection with significantly different datasets."""
        reference_data = self.create_ohlcv_data(rows=100, drift_factor=1.0)
        current_data = self.create_ohlcv_data(rows=100, drift_factor=2.0)  # 2x price levels

        result = self.detector.detect_data_drift(reference_data, current_data)

        # Verify drift detection
        assert result["dataset_drift_detected"] is True
        assert result["drift_score"] > 0
        assert len(result["drifted_columns"]) > 0

    def test_detect_anomalies_clean_data(self):
        """Test anomaly detection with clean data."""
        clean_data = self.create_ohlcv_data(rows=100, add_anomalies=False)

        result = self.detector.detect_anomalies(clean_data)

        # Verify result structure
        assert "timestamp" in result
        assert "total_records" in result
        assert "anomalies_detected" in result
        assert "anomaly_percentage" in result
        assert "method" in result
        assert result["method"] == "pyod_ensemble_iforest_ecod"

        # With clean data, anomaly rate should be low
        assert result["total_records"] == 100
        assert result["anomaly_percentage"] < 20.0  # Less than 20% anomalies

    def test_detect_anomalies_with_anomalies(self):
        """Test anomaly detection with injected anomalies."""
        anomalous_data = self.create_ohlcv_data(rows=100, add_anomalies=True)

        result = self.detector.detect_anomalies(anomalous_data)

        # Verify anomaly detection
        assert result["anomalies_detected"] > 0
        assert result["anomaly_percentage"] > 0
        assert len(result["anomaly_indices"]) == result["anomalies_detected"]

    def test_validate_data_quality_good_data(self):
        """Test data quality validation with good data."""
        good_data = self.create_ohlcv_data(rows=100)

        result = self.detector.validate_data_quality(good_data)

        # Verify result structure
        assert "timestamp" in result
        assert "total_records" in result
        assert "quality_score" in result
        assert "validation_method" in result

        # Good data should have high quality score
        assert result["total_records"] == 100
        assert result["quality_score"] > 0.8
        assert result["data_types_valid"] is True
        assert result["temporal_integrity"] is True
        assert result["price_consistency"] is True
        assert result["volume_validity"] is True

    def test_validate_data_quality_poor_data(self):
        """Test data quality validation with poor data."""
        poor_data = self.create_ohlcv_data(rows=100)

        # Introduce quality issues
        poor_data.loc[10:20, "open"] = np.nan  # Missing values
        poor_data.loc[30, "high"] = poor_data.loc[30, "low"] - 100  # Inconsistent prices
        poor_data.loc[40, "volume"] = -1000  # Invalid volume

        result = self.detector.validate_data_quality(poor_data)

        # Verify quality issues detected
        assert result["quality_score"] < 0.8
        assert len(result["missing_values"]) > 0
        assert result["price_consistency"] is False
        assert result["volume_validity"] is False

    def test_anomaly_detection_no_numerical_columns(self):
        """Test anomaly detection with missing numerical columns."""
        invalid_data = pd.DataFrame(
            {"date": pd.date_range("2024-01-01", periods=10), "symbol": ["BTCUSDT"] * 10}
        )

        with pytest.raises(DataCollectionError) as exc_info:
            self.detector.detect_anomalies(invalid_data)

        assert "No numerical columns available" in str(exc_info.value)


class TestDataQualityMonitor:
    """Test comprehensive data quality monitoring system."""

    def setup_method(self):
        """Setup test fixtures."""
        self.monitor = DataQualityMonitor(anomaly_contamination=0.1)

    def create_reference_data_file(self, temp_dir: Path) -> Path:
        """Create reference data file for testing."""
        reference_file = temp_dir / "reference.csv"

        # Create synthetic reference data
        dates = pd.date_range("2024-01-01", periods=50, freq="h")
        data = pd.DataFrame(
            {
                "date": dates,
                "open": np.random.normal(50000, 1000, 50),
                "high": np.random.normal(50500, 1000, 50),
                "low": np.random.normal(49500, 1000, 50),
                "close": np.random.normal(50000, 1000, 50),
                "volume": np.random.exponential(1000, 50),
            }
        )

        data.to_csv(reference_file, index=False)
        return reference_file

    def test_monitor_dataset_healthy(self):
        """Test monitoring with healthy dataset."""
        # Create healthy test data
        healthy_data = pd.DataFrame(
            {
                "date": pd.date_range("2024-01-01", periods=50),
                "open": np.random.normal(50000, 100, 50),
                "high": np.random.normal(50100, 100, 50),
                "low": np.random.normal(49900, 100, 50),
                "close": np.random.normal(50000, 100, 50),
                "volume": np.random.exponential(1000, 50),
            }
        )

        result = self.monitor.monitor_dataset(healthy_data)

        # Verify monitoring results
        assert "timestamp" in result
        assert "overall_status" in result
        assert "alerts" in result
        assert "quality_validation" in result
        assert "anomaly_detection" in result

        # Healthy data should have good status
        assert result["overall_status"] in ["HEALTHY", "WARNING"]
        assert "quality_validation" in result["monitoring_components"]
        assert "anomaly_detection" in result["monitoring_components"]

    def test_monitor_dataset_with_reference(self):
        """Test monitoring with reference data for drift detection."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            reference_file = self.create_reference_data_file(temp_path)

            # Create monitor with reference data
            monitor = DataQualityMonitor(
                reference_data_path=reference_file, anomaly_contamination=0.1
            )

            # Create current data (similar to reference)
            current_data = pd.DataFrame(
                {
                    "date": pd.date_range("2024-01-10", periods=50),
                    "open": np.random.normal(50000, 100, 50),
                    "high": np.random.normal(50100, 100, 50),
                    "low": np.random.normal(49900, 100, 50),
                    "close": np.random.normal(50000, 100, 50),
                    "volume": np.random.exponential(1000, 50),
                }
            )

            result = monitor.monitor_dataset(current_data)

            # Verify drift detection included
            assert "drift_detection" in result["monitoring_components"]
            assert result["drift_detection"] is not None
            assert "dataset_drift_detected" in result["drift_detection"]

    def test_monitor_dataset_critical_issues(self):
        """Test monitoring with critical data quality issues."""
        # Create problematic data
        problematic_data = pd.DataFrame(
            {
                "date": pd.date_range("2024-01-01", periods=50),
                "open": [np.nan] * 25 + list(np.random.normal(50000, 100, 25)),  # 50% missing
                "high": np.random.normal(50000, 100, 50),
                "low": np.random.normal(50000, 100, 50),
                "close": np.random.normal(50000, 100, 50),
                "volume": [-1000] * 10 + list(np.random.exponential(1000, 40)),  # Invalid volumes
            }
        )

        result = self.monitor.monitor_dataset(problematic_data)

        # Verify critical issues detected
        assert len(result["alerts"]) > 0

        # Check for specific alert types
        alert_types = [alert["type"] for alert in result["alerts"]]
        quality_alerts = [
            alert
            for alert in result["alerts"]
            if alert["type"] in ["DATA_QUALITY", "MISSING_VALUES"]
        ]

        assert len(quality_alerts) > 0

    def test_monitor_empty_dataset(self):
        """Test monitoring with empty dataset."""
        empty_data = pd.DataFrame()

        # Should handle empty data gracefully
        result = self.monitor.monitor_dataset(empty_data)

        # Verify it handles empty data without crashing
        assert "overall_status" in result
        assert "alerts" in result
        assert result["dataset_shape"] == (0, 0)
