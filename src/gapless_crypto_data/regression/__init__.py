"""
Regression detection package for data quality monitoring.

Provides SOTA regression detection using evidently and pyod for comprehensive
data validation, drift detection, and anomaly identification.
"""

from .regression_detector import DataQualityMonitor, RegressionDetector

__all__ = [
    "RegressionDetector",
    "DataQualityMonitor",
]
