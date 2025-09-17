"""API Change Detection and Diffing System for Ultrathink Documentation.

This module provides comprehensive API change detection, version tracking,
and change classification for maintaining synchronized documentation.
"""

from .api_differ import APIDiffer
from .version_tracker import VersionTracker
from .change_classifier import ChangeClassifier

__all__ = [
    "APIDiffer",
    "VersionTracker",
    "ChangeClassifier",
]