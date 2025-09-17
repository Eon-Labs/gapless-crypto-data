"""Version tracking and management for ultrathink documentation system."""

import json
import sqlite3
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta
import logging
import re

logger = logging.getLogger(__name__)


class VersionTracker:
    """Tracks API versions and manages version-related operations."""

    def __init__(self, storage_directory: str = "docs/ultrathink/storage"):
        """Initialize the version tracker.

        Args:
            storage_directory: Directory for storing version tracking data
        """
        self.storage_dir = Path(storage_directory)
        self.db_path = self.storage_dir / "version_tracking.db"
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self._init_database()

    def _init_database(self):
        """Initialize the SQLite database for version tracking."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version_string TEXT UNIQUE NOT NULL,
                    major INTEGER NOT NULL,
                    minor INTEGER NOT NULL,
                    patch INTEGER NOT NULL,
                    pre_release TEXT,
                    build_metadata TEXT,
                    created_timestamp TEXT NOT NULL,
                    snapshot_file TEXT,
                    is_current BOOLEAN DEFAULT FALSE,
                    notes TEXT
                );

                CREATE TABLE IF NOT EXISTS version_changes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_version_id INTEGER,
                    to_version_id INTEGER NOT NULL,
                    change_type TEXT NOT NULL,
                    element_name TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    description TEXT,
                    created_timestamp TEXT NOT NULL,
                    FOREIGN KEY (from_version_id) REFERENCES versions (id),
                    FOREIGN KEY (to_version_id) REFERENCES versions (id)
                );

                CREATE TABLE IF NOT EXISTS deprecations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    element_name TEXT NOT NULL,
                    deprecated_in_version_id INTEGER NOT NULL,
                    removal_target_version_id INTEGER,
                    reason TEXT,
                    alternative TEXT,
                    created_timestamp TEXT NOT NULL,
                    FOREIGN KEY (deprecated_in_version_id) REFERENCES versions (id),
                    FOREIGN KEY (removal_target_version_id) REFERENCES versions (id)
                );

                CREATE INDEX IF NOT EXISTS idx_versions_string ON versions (version_string);
                CREATE INDEX IF NOT EXISTS idx_changes_to_version ON version_changes (to_version_id);
                CREATE INDEX IF NOT EXISTS idx_deprecations_element ON deprecations (element_name);
            """)

    def parse_version(self, version_string: str) -> Dict[str, Any]:
        """Parse a semantic version string.

        Args:
            version_string: Version string (e.g., "2.1.1", "3.0.0-alpha.1")

        Returns:
            Parsed version components
        """
        # Semantic versioning regex pattern
        pattern = r'^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$'

        match = re.match(pattern, version_string)
        if not match:
            # Fallback for non-semver versions
            parts = version_string.split('.')
            return {
                "version_string": version_string,
                "major": int(parts[0]) if len(parts) > 0 and parts[0].isdigit() else 0,
                "minor": int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0,
                "patch": int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0,
                "pre_release": None,
                "build_metadata": None,
                "is_valid_semver": False
            }

        return {
            "version_string": version_string,
            "major": int(match.group("major")),
            "minor": int(match.group("minor")),
            "patch": int(match.group("patch")),
            "pre_release": match.group("prerelease"),
            "build_metadata": match.group("buildmetadata"),
            "is_valid_semver": True
        }

    def register_version(self, version_string: str, snapshot_file: Optional[str] = None, notes: Optional[str] = None) -> int:
        """Register a new version in the tracking system.

        Args:
            version_string: Version string to register
            snapshot_file: Path to the API snapshot file
            notes: Optional notes about this version

        Returns:
            Version ID in the database
        """
        parsed = self.parse_version(version_string)
        timestamp = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            # First, mark all versions as not current
            conn.execute("UPDATE versions SET is_current = FALSE")

            # Insert new version
            cursor = conn.execute("""
                INSERT INTO versions
                (version_string, major, minor, patch, pre_release, build_metadata,
                 created_timestamp, snapshot_file, is_current, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, TRUE, ?)
            """, (
                version_string,
                parsed["major"],
                parsed["minor"],
                parsed["patch"],
                parsed["pre_release"],
                parsed["build_metadata"],
                timestamp,
                snapshot_file,
                notes
            ))

            version_id = cursor.lastrowid
            conn.commit()

        logger.info(f"Registered version {version_string} with ID {version_id}")
        return version_id

    def get_version_info(self, version_string: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific version.

        Args:
            version_string: Version to look up

        Returns:
            Version information or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM versions WHERE version_string = ?
            """, (version_string,))

            row = cursor.fetchone()
            if row:
                return dict(row)

        return None

    def get_current_version(self) -> Optional[Dict[str, Any]]:
        """Get the current version information."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM versions WHERE is_current = TRUE LIMIT 1
            """)

            row = cursor.fetchone()
            if row:
                return dict(row)

        return None

    def get_version_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get version history sorted by semantic version.

        Args:
            limit: Maximum number of versions to return

        Returns:
            List of version information dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM versions
                ORDER BY major DESC, minor DESC, patch DESC, created_timestamp DESC
                LIMIT ?
            """, (limit,))

            return [dict(row) for row in cursor.fetchall()]

    def compare_versions(self, version1: str, version2: str) -> int:
        """Compare two versions using semantic versioning rules.

        Args:
            version1: First version string
            version2: Second version string

        Returns:
            -1 if version1 < version2, 0 if equal, 1 if version1 > version2
        """
        v1 = self.parse_version(version1)
        v2 = self.parse_version(version2)

        # Compare major.minor.patch
        for component in ["major", "minor", "patch"]:
            if v1[component] < v2[component]:
                return -1
            elif v1[component] > v2[component]:
                return 1

        # Handle pre-release versions
        v1_pre = v1["pre_release"]
        v2_pre = v2["pre_release"]

        if v1_pre is None and v2_pre is None:
            return 0
        elif v1_pre is None:
            return 1  # Release version > pre-release
        elif v2_pre is None:
            return -1  # Pre-release < release version
        else:
            # Compare pre-release strings
            if v1_pre < v2_pre:
                return -1
            elif v1_pre > v2_pre:
                return 1
            else:
                return 0

    def get_next_version(self, current_version: str, bump_type: str) -> str:
        """Calculate the next version based on bump type.

        Args:
            current_version: Current version string
            bump_type: 'major', 'minor', 'patch', or 'prerelease'

        Returns:
            Next version string
        """
        parsed = self.parse_version(current_version)

        if bump_type == "major":
            return f"{parsed['major'] + 1}.0.0"
        elif bump_type == "minor":
            return f"{parsed['major']}.{parsed['minor'] + 1}.0"
        elif bump_type == "patch":
            return f"{parsed['major']}.{parsed['minor']}.{parsed['patch'] + 1}"
        elif bump_type == "prerelease":
            if parsed["pre_release"]:
                # Increment existing pre-release
                parts = parsed["pre_release"].split('.')
                if parts[-1].isdigit():
                    parts[-1] = str(int(parts[-1]) + 1)
                else:
                    parts.append("1")
                pre_release = '.'.join(parts)
            else:
                pre_release = "alpha.1"

            return f"{parsed['major']}.{parsed['minor']}.{parsed['patch']}-{pre_release}"
        else:
            raise ValueError(f"Unknown bump type: {bump_type}")

    def record_changes(self, from_version: str, to_version: str, changes: List[Dict[str, Any]]):
        """Record changes between versions.

        Args:
            from_version: Source version
            to_version: Target version
            changes: List of change dictionaries
        """
        from_version_info = self.get_version_info(from_version)
        to_version_info = self.get_version_info(to_version)

        if not from_version_info:
            raise ValueError(f"Source version {from_version} not found")
        if not to_version_info:
            raise ValueError(f"Target version {to_version} not found")

        timestamp = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            for change in changes:
                conn.execute("""
                    INSERT INTO version_changes
                    (from_version_id, to_version_id, change_type, element_name,
                     severity, description, created_timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    from_version_info["id"],
                    to_version_info["id"],
                    change.get("type", "unknown"),
                    change.get("element", "unknown"),
                    change.get("severity", "unknown"),
                    change.get("description", ""),
                    timestamp
                ))

            conn.commit()

        logger.info(f"Recorded {len(changes)} changes from {from_version} to {to_version}")

    def get_changes_between_versions(self, from_version: str, to_version: str) -> List[Dict[str, Any]]:
        """Get all changes between two versions.

        Args:
            from_version: Source version
            to_version: Target version

        Returns:
            List of changes
        """
        from_version_info = self.get_version_info(from_version)
        to_version_info = self.get_version_info(to_version)

        if not from_version_info or not to_version_info:
            return []

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT vc.*, v1.version_string as from_version, v2.version_string as to_version
                FROM version_changes vc
                JOIN versions v1 ON vc.from_version_id = v1.id
                JOIN versions v2 ON vc.to_version_id = v2.id
                WHERE vc.from_version_id = ? AND vc.to_version_id = ?
                ORDER BY vc.created_timestamp
            """, (from_version_info["id"], to_version_info["id"]))

            return [dict(row) for row in cursor.fetchall()]

    def add_deprecation(self, element_name: str, deprecated_in_version: str,
                       reason: Optional[str] = None, alternative: Optional[str] = None,
                       removal_target_version: Optional[str] = None):
        """Add a deprecation record.

        Args:
            element_name: Name of the deprecated element
            deprecated_in_version: Version in which element was deprecated
            reason: Reason for deprecation
            alternative: Suggested alternative
            removal_target_version: Version in which element will be removed
        """
        deprecated_version_info = self.get_version_info(deprecated_in_version)
        if not deprecated_version_info:
            raise ValueError(f"Deprecated version {deprecated_in_version} not found")

        removal_version_id = None
        if removal_target_version:
            removal_version_info = self.get_version_info(removal_target_version)
            if removal_version_info:
                removal_version_id = removal_version_info["id"]

        timestamp = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO deprecations
                (element_name, deprecated_in_version_id, removal_target_version_id,
                 reason, alternative, created_timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                element_name,
                deprecated_version_info["id"],
                removal_version_id,
                reason,
                alternative,
                timestamp
            ))

            conn.commit()

        logger.info(f"Added deprecation for {element_name} in version {deprecated_in_version}")

    def get_deprecations(self, current_version: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all deprecations, optionally filtered by current version.

        Args:
            current_version: Optional version to check deprecations against

        Returns:
            List of deprecation records
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            if current_version:
                current_version_info = self.get_version_info(current_version)
                if not current_version_info:
                    return []

                cursor = conn.execute("""
                    SELECT d.*,
                           v1.version_string as deprecated_in_version,
                           v2.version_string as removal_target_version
                    FROM deprecations d
                    JOIN versions v1 ON d.deprecated_in_version_id = v1.id
                    LEFT JOIN versions v2 ON d.removal_target_version_id = v2.id
                    WHERE v1.major <= ? AND v1.minor <= ? AND v1.patch <= ?
                    ORDER BY d.created_timestamp DESC
                """, (
                    current_version_info["major"],
                    current_version_info["minor"],
                    current_version_info["patch"]
                ))
            else:
                cursor = conn.execute("""
                    SELECT d.*,
                           v1.version_string as deprecated_in_version,
                           v2.version_string as removal_target_version
                    FROM deprecations d
                    JOIN versions v1 ON d.deprecated_in_version_id = v1.id
                    LEFT JOIN versions v2 ON d.removal_target_version_id = v2.id
                    ORDER BY d.created_timestamp DESC
                """)

            return [dict(row) for row in cursor.fetchall()]

    def get_statistics(self) -> Dict[str, Any]:
        """Get tracking statistics.

        Returns:
            Dictionary with various statistics
        """
        with sqlite3.connect(self.db_path) as conn:
            stats = {}

            # Version counts
            cursor = conn.execute("SELECT COUNT(*) as total_versions FROM versions")
            stats["total_versions"] = cursor.fetchone()[0]

            # Change counts
            cursor = conn.execute("SELECT COUNT(*) as total_changes FROM version_changes")
            stats["total_changes"] = cursor.fetchone()[0]

            # Deprecation counts
            cursor = conn.execute("SELECT COUNT(*) as total_deprecations FROM deprecations")
            stats["total_deprecations"] = cursor.fetchone()[0]

            # Recent activity (last 30 days)
            cutoff_date = (datetime.now() - timedelta(days=30)).isoformat()
            cursor = conn.execute("""
                SELECT COUNT(*) as recent_versions
                FROM versions
                WHERE created_timestamp > ?
            """, (cutoff_date,))
            stats["recent_versions"] = cursor.fetchone()[0]

            # Breaking changes by severity
            cursor = conn.execute("""
                SELECT severity, COUNT(*) as count
                FROM version_changes
                GROUP BY severity
            """)
            stats["changes_by_severity"] = {row[0]: row[1] for row in cursor.fetchall()}

            # Current version info
            current = self.get_current_version()
            if current:
                stats["current_version"] = current["version_string"]
            else:
                stats["current_version"] = None

            return stats