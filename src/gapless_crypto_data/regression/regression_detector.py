"""
SOTA regression detection system for cryptocurrency data quality monitoring.

Uses pyod for anomaly detection and statistical methods for drift detection
to ensure data quality and detect regressions in collection processes.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

import numpy as np
import pandas as pd
from pyod.models.ecod import ECOD
from pyod.models.iforest import IForest
from scipy import stats

from ..utils.error_handling import DataCollectionError, get_standard_logger


class RegressionDetector:
    """
    SOTA regression detection using evidently and pyod.

    Monitors data quality, detects drift, and identifies anomalies
    in cryptocurrency data collection processes.
    """

    def __init__(self, anomaly_contamination: float = 0.1, drift_threshold: float = 0.1):
        """
        Initialize regression detector with SOTA algorithms.

        Args:
            anomaly_contamination: Expected proportion of anomalies (0.1 = 10%)
            drift_threshold: Threshold for drift detection (0.1 = 10% change)
        """
        self.anomaly_contamination = anomaly_contamination
        self.drift_threshold = drift_threshold
        self.logger = get_standard_logger("regression_detector")

        # Initialize SOTA anomaly detectors
        self.iforest_detector = IForest(
            contamination=anomaly_contamination, random_state=42, n_estimators=100
        )
        self.ecod_detector = ECOD(contamination=anomaly_contamination)

        # Numerical columns for cryptocurrency OHLCV data
        self.numerical_features = [
            "open",
            "high",
            "low",
            "close",
            "volume",
            "quote_asset_volume",
            "number_of_trades",
            "taker_buy_base_asset_volume",
            "taker_buy_quote_asset_volume",
        ]

    def detect_data_drift(
        self, reference_data: pd.DataFrame, current_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Detect data drift using statistical methods.

        Args:
            reference_data: Historical reference dataset
            current_data: Current dataset to compare

        Returns:
            Dict containing drift detection results

        Raises:
            DataCollectionError: If drift detection fails
        """
        try:
            drift_results = {
                "timestamp": datetime.now().isoformat(),
                "dataset_drift_detected": False,
                "drift_score": 0.0,
                "drifted_columns": [],
                "missing_values_drift": False,
                "summary_stats": {},
                "statistical_tests": {},
                "method": "statistical_drift_detection",
            }

            # Summary statistics
            drift_results["summary_stats"] = {
                "reference_rows": len(reference_data),
                "current_rows": len(current_data),
                "reference_columns": len(reference_data.columns),
                "current_columns": len(current_data.columns),
            }

            # Missing values drift
            ref_missing = reference_data.isnull().sum().sum()
            cur_missing = current_data.isnull().sum().sum()
            drift_results["missing_values_drift"] = abs(cur_missing - ref_missing) > 0

            # Statistical drift detection for numerical columns
            available_cols = [
                col
                for col in self.numerical_features
                if col in reference_data.columns and col in current_data.columns
            ]

            drifted_columns = []
            p_values = {}

            for col in available_cols:
                ref_values = reference_data[col].dropna()
                cur_values = current_data[col].dropna()

                if len(ref_values) > 0 and len(cur_values) > 0:
                    # Kolmogorov-Smirnov test for distribution comparison
                    try:
                        ks_stat, p_value = stats.ks_2samp(ref_values, cur_values)
                        p_values[col] = p_value

                        # Consider drift if p-value < threshold
                        if p_value < self.drift_threshold:
                            drifted_columns.append(col)

                    except Exception as e:
                        self.logger.warning(f"KS test failed for {col}: {e}")
                        p_values[col] = 1.0

            drift_results["drifted_columns"] = drifted_columns
            drift_results["statistical_tests"] = p_values
            drift_results["dataset_drift_detected"] = len(drifted_columns) > 0

            # Calculate drift score as proportion of drifted columns
            if available_cols:
                drift_results["drift_score"] = len(drifted_columns) / len(available_cols)
            else:
                drift_results["drift_score"] = 0.0

            self.logger.info(
                f"Drift detection completed: "
                f"drift={'Yes' if drift_results['dataset_drift_detected'] else 'No'}, "
                f"score={drift_results['drift_score']:.3f}, "
                f"drifted_cols={len(drifted_columns)}/{len(available_cols)}"
            )

            return drift_results

        except Exception as e:
            raise DataCollectionError(
                f"Data drift detection failed: {e}",
                context={
                    "reference_shape": reference_data.shape,
                    "current_shape": current_data.shape,
                    "error": str(e),
                },
            )

    def detect_anomalies(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Detect anomalies using SOTA pyod algorithms.

        Args:
            data: DataFrame with numerical features for anomaly detection

        Returns:
            Dict containing anomaly detection results

        Raises:
            DataCollectionError: If anomaly detection fails
        """
        try:
            # Prepare numerical features
            numerical_cols = ["open", "high", "low", "close", "volume"]
            available_cols = [col for col in numerical_cols if col in data.columns]

            if not available_cols:
                raise DataCollectionError(
                    "No numerical columns available for anomaly detection",
                    context={"available_columns": list(data.columns)},
                )

            X = data[available_cols].values

            # Ensemble anomaly detection using SOTA algorithms
            iforest_scores = self.iforest_detector.fit(X).decision_scores_
            ecod_scores = self.ecod_detector.fit(X).decision_scores_

            # Combine scores using average
            combined_scores = (iforest_scores + ecod_scores) / 2

            # Determine anomaly threshold (95th percentile)
            threshold = np.percentile(combined_scores, 95)
            anomalies = combined_scores > threshold

            anomaly_results = {
                "timestamp": datetime.now().isoformat(),
                "total_records": len(data),
                "anomalies_detected": int(np.sum(anomalies)),
                "anomaly_percentage": float(np.mean(anomalies) * 100),
                "anomaly_threshold": float(threshold),
                "max_anomaly_score": float(np.max(combined_scores)),
                "mean_anomaly_score": float(np.mean(combined_scores)),
                "anomaly_indices": anomalies.nonzero()[0].tolist(),
                "method": "pyod_ensemble_iforest_ecod",
                "features_analyzed": available_cols,
            }

            self.logger.info(
                f"Anomaly detection completed: "
                f"{anomaly_results['anomalies_detected']}/{anomaly_results['total_records']} "
                f"anomalies ({anomaly_results['anomaly_percentage']:.2f}%)"
            )

            return anomaly_results

        except Exception as e:
            raise DataCollectionError(
                f"Anomaly detection failed: {e}",
                context={
                    "data_shape": data.shape,
                    "available_columns": available_cols,
                    "error": str(e),
                },
            )

    def validate_data_quality(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Comprehensive data quality validation for cryptocurrency data.

        Args:
            data: DataFrame to validate

        Returns:
            Dict containing data quality metrics

        Raises:
            DataCollectionError: If validation fails
        """
        try:
            quality_results = {
                "timestamp": datetime.now().isoformat(),
                "total_records": len(data),
                "total_columns": len(data.columns),
                "missing_values": {},
                "duplicate_records": 0,
                "data_types_valid": True,
                "temporal_integrity": True,
                "price_consistency": True,
                "volume_validity": True,
                "quality_score": 0.0,
                "validation_method": "comprehensive_cryptocurrency_validation",
            }

            # Missing values analysis
            missing_counts = data.isnull().sum()
            quality_results["missing_values"] = {
                col: int(count) for col, count in missing_counts.items() if count > 0
            }

            # Duplicate records
            quality_results["duplicate_records"] = int(data.duplicated().sum())

            # Data type validation
            expected_types = {
                "date": ["datetime64", "object"],
                "open": ["float64", "int64"],
                "high": ["float64", "int64"],
                "low": ["float64", "int64"],
                "close": ["float64", "int64"],
                "volume": ["float64", "int64"],
            }

            for col, expected in expected_types.items():
                if col in data.columns:
                    actual_type = str(data[col].dtype)
                    if not any(exp in actual_type for exp in expected):
                        quality_results["data_types_valid"] = False
                        self.logger.warning(f"Invalid data type for {col}: {actual_type}")

            # Temporal integrity (if date column exists)
            if "date" in data.columns:
                try:
                    dates = pd.to_datetime(data["date"])
                    if not dates.is_monotonic_increasing:
                        quality_results["temporal_integrity"] = False
                        self.logger.warning("Temporal integrity violation: dates not monotonic")
                except Exception:
                    quality_results["temporal_integrity"] = False

            # Price consistency validation (high >= low, etc.)
            price_cols = ["open", "high", "low", "close"]
            if all(col in data.columns for col in price_cols):
                # High should be >= Low
                high_low_valid = bool((data["high"] >= data["low"]).all())
                # High should be >= Open and Close
                high_open_valid = bool((data["high"] >= data["open"]).all())
                high_close_valid = bool((data["high"] >= data["close"]).all())
                # Low should be <= Open and Close
                low_open_valid = bool((data["low"] <= data["open"]).all())
                low_close_valid = bool((data["low"] <= data["close"]).all())

                quality_results["price_consistency"] = all(
                    [
                        high_low_valid,
                        high_open_valid,
                        high_close_valid,
                        low_open_valid,
                        low_close_valid,
                    ]
                )

            # Volume validity (non-negative)
            if "volume" in data.columns:
                quality_results["volume_validity"] = bool((data["volume"] >= 0).all())

            # Calculate overall quality score
            quality_factors = [
                quality_results["data_types_valid"],
                quality_results["temporal_integrity"],
                quality_results["price_consistency"],
                quality_results["volume_validity"],
                quality_results["duplicate_records"] == 0,
                len(quality_results["missing_values"]) == 0,
            ]

            quality_results["quality_score"] = sum(quality_factors) / len(quality_factors)

            self.logger.info(
                f"Data quality validation completed: "
                f"score={quality_results['quality_score']:.3f}, "
                f"records={quality_results['total_records']}"
            )

            return quality_results

        except Exception as e:
            raise DataCollectionError(
                f"Data quality validation failed: {e}",
                context={"data_shape": data.shape, "columns": list(data.columns), "error": str(e)},
            )


class DataQualityMonitor:
    """
    SOTA data quality monitoring system for continuous regression detection.

    Combines drift detection, anomaly detection, and quality validation
    for comprehensive monitoring of cryptocurrency data collection.
    """

    def __init__(
        self,
        reference_data_path: Optional[Union[str, Path]] = None,
        anomaly_contamination: float = 0.1,
    ):
        """
        Initialize data quality monitor.

        Args:
            reference_data_path: Path to reference dataset for drift detection
            anomaly_contamination: Expected proportion of anomalies
        """
        self.reference_data_path = Path(reference_data_path) if reference_data_path else None
        self.reference_data = None
        self.detector = RegressionDetector(anomaly_contamination=anomaly_contamination)
        self.logger = get_standard_logger("data_quality_monitor")

        # Load reference data if path provided
        if self.reference_data_path and self.reference_data_path.exists():
            self._load_reference_data()

    def _load_reference_data(self):
        """Load reference data for drift detection."""
        try:
            self.reference_data = pd.read_csv(self.reference_data_path)
            self.logger.info(f"Loaded reference data: {self.reference_data.shape}")
        except Exception as e:
            self.logger.warning(f"Failed to load reference data: {e}")

    def monitor_dataset(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Comprehensive monitoring of dataset quality and regression detection.

        Args:
            data: Dataset to monitor

        Returns:
            Dict containing complete monitoring results

        Raises:
            DataCollectionError: If monitoring fails
        """
        try:
            monitoring_results = {
                "timestamp": datetime.now().isoformat(),
                "dataset_shape": data.shape,
                "monitoring_components": ["quality_validation", "anomaly_detection"],
                "overall_status": "HEALTHY",
                "alerts": [],
                "quality_validation": {},
                "anomaly_detection": {},
                "drift_detection": None,
            }

            # 1. Data quality validation
            try:
                quality_results = self.detector.validate_data_quality(data)
                monitoring_results["quality_validation"] = quality_results

                # Generate alerts for quality issues
                if quality_results["quality_score"] < 0.8:
                    monitoring_results["alerts"].append(
                        {
                            "type": "DATA_QUALITY",
                            "severity": "HIGH",
                            "message": f"Low quality score: {quality_results['quality_score']:.3f}",
                        }
                    )

                if quality_results["missing_values"]:
                    monitoring_results["alerts"].append(
                        {
                            "type": "MISSING_VALUES",
                            "severity": "MEDIUM",
                            "message": f"Missing values detected: {quality_results['missing_values']}",
                        }
                    )

            except Exception as e:
                monitoring_results["alerts"].append(
                    {
                        "type": "QUALITY_VALIDATION_ERROR",
                        "severity": "HIGH",
                        "message": f"Quality validation failed: {e}",
                    }
                )

            # 2. Anomaly detection
            try:
                anomaly_results = self.detector.detect_anomalies(data)
                monitoring_results["anomaly_detection"] = anomaly_results

                # Generate alerts for anomalies
                if anomaly_results["anomaly_percentage"] > 15.0:  # More than 15% anomalies
                    monitoring_results["alerts"].append(
                        {
                            "type": "HIGH_ANOMALY_RATE",
                            "severity": "HIGH",
                            "message": f"High anomaly rate: {anomaly_results['anomaly_percentage']:.2f}%",
                        }
                    )

            except Exception as e:
                monitoring_results["alerts"].append(
                    {
                        "type": "ANOMALY_DETECTION_ERROR",
                        "severity": "MEDIUM",
                        "message": f"Anomaly detection failed: {e}",
                    }
                )

            # 3. Data drift detection (if reference data available)
            if self.reference_data is not None:
                try:
                    monitoring_results["monitoring_components"].append("drift_detection")
                    drift_results = self.detector.detect_data_drift(self.reference_data, data)
                    monitoring_results["drift_detection"] = drift_results

                    # Generate alerts for drift
                    if drift_results["dataset_drift_detected"]:
                        monitoring_results["alerts"].append(
                            {
                                "type": "DATA_DRIFT",
                                "severity": "HIGH",
                                "message": f"Data drift detected: {drift_results['drift_score']:.3f}",
                            }
                        )

                except Exception as e:
                    monitoring_results["alerts"].append(
                        {
                            "type": "DRIFT_DETECTION_ERROR",
                            "severity": "MEDIUM",
                            "message": f"Drift detection failed: {e}",
                        }
                    )

            # Determine overall status
            high_alerts = [
                alert for alert in monitoring_results["alerts"] if alert["severity"] == "HIGH"
            ]
            if high_alerts:
                monitoring_results["overall_status"] = "CRITICAL"
            elif monitoring_results["alerts"]:
                monitoring_results["overall_status"] = "WARNING"

            self.logger.info(
                f"Dataset monitoring completed: "
                f"status={monitoring_results['overall_status']}, "
                f"alerts={len(monitoring_results['alerts'])}"
            )

            return monitoring_results

        except Exception as e:
            raise DataCollectionError(
                f"Dataset monitoring failed: {e}",
                context={
                    "data_shape": data.shape,
                    "reference_available": self.reference_data is not None,
                    "error": str(e),
                },
            )
