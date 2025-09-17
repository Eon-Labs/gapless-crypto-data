"""Help() snapshot validation for ultrathink documentation system."""

import importlib
import io
import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)


class HelpSnapshotter:
    """Captures and validates help() output snapshots for API elements."""

    def __init__(self, package_name: str, storage_directory: str = "docs/ultrathink/storage"):
        """Initialize the help snapshotter.

        Args:
            package_name: Name of the package to snapshot
            storage_directory: Directory for storing snapshots
        """
        self.package_name = package_name
        self.storage_dir = Path(storage_directory)
        self.snapshots_dir = self.storage_dir / "help_snapshots"
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

    def capture_help_snapshots(self, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """Capture help() output for all API elements.

        Args:
            api_data: API data from APIExtractor

        Returns:
            Dictionary containing snapshot results
        """
        logger.info(f"Capturing help() snapshots for package {self.package_name}")

        snapshot_result = {
            "package_name": self.package_name,
            "capture_timestamp": datetime.now().isoformat(),
            "total_elements": 0,
            "captured_snapshots": 0,
            "failed_snapshots": 0,
            "snapshots": {},
            "errors": [],
            "metadata": {}
        }

        try:
            # Import the package
            package = importlib.import_module(self.package_name)

            public_api = api_data.get("public_api", {})
            snapshot_result["total_elements"] = len(public_api)

            for element_name, element_data in public_api.items():
                try:
                    # Get the actual object
                    obj = getattr(package, element_name, None)
                    if obj is None:
                        logger.warning(f"Element {element_name} not found in package")
                        continue

                    # Capture help output
                    help_output = self._capture_help_output(obj)

                    # Create snapshot
                    snapshot = {
                        "element_name": element_name,
                        "element_type": element_data.get("type", "unknown"),
                        "help_output": help_output,
                        "help_hash": self._hash_help_output(help_output),
                        "capture_timestamp": datetime.now().isoformat(),
                        "module": element_data.get("module", "unknown"),
                        "signature": element_data.get("signature", ""),
                        "metadata": {
                            "output_length": len(help_output),
                            "line_count": len(help_output.splitlines()),
                            "contains_docstring": "Help on" in help_output,
                            "contains_signature": "(" in help_output and ")" in help_output
                        }
                    }

                    snapshot_result["snapshots"][element_name] = snapshot
                    snapshot_result["captured_snapshots"] += 1

                    logger.debug(f"Captured help snapshot for {element_name}")

                except Exception as e:
                    error_msg = f"Failed to capture help for {element_name}: {e}"
                    logger.warning(error_msg)
                    snapshot_result["errors"].append(error_msg)
                    snapshot_result["failed_snapshots"] += 1

            # Generate metadata
            snapshot_result["metadata"] = self._generate_snapshot_metadata(snapshot_result)

            # Save snapshots
            snapshot_file = self._save_snapshots(snapshot_result)
            snapshot_result["snapshot_file"] = snapshot_file

            logger.info(f"Captured {snapshot_result['captured_snapshots']}/{snapshot_result['total_elements']} help snapshots")

        except Exception as e:
            error_msg = f"Help snapshot capture failed: {e}"
            logger.error(error_msg)
            snapshot_result["errors"].append(error_msg)

        return snapshot_result

    def _capture_help_output(self, obj: Any) -> str:
        """Capture help() output for an object."""
        # Redirect stdout to capture help output
        old_stdout = sys.stdout
        captured_output = io.StringIO()

        try:
            sys.stdout = captured_output
            help(obj)
            return captured_output.getvalue()
        finally:
            sys.stdout = old_stdout

    def _hash_help_output(self, help_output: str) -> str:
        """Create a hash of help output for change detection."""
        # Normalize the output to ignore insignificant differences
        normalized = self._normalize_help_output(help_output)
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

    def _normalize_help_output(self, help_output: str) -> str:
        """Normalize help output to ignore insignificant differences."""
        # Remove memory addresses
        normalized = re.sub(r'at 0x[0-9a-fA-F]+', 'at 0x...', help_output)

        # Remove file paths that might be environment-specific
        normalized = re.sub(r'file ".*?"', 'file "..."', normalized)

        # Normalize whitespace
        lines = normalized.splitlines()
        normalized_lines = [line.rstrip() for line in lines]

        return '\n'.join(normalized_lines)

    def _generate_snapshot_metadata(self, snapshot_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate metadata about the snapshots."""
        snapshots = snapshot_result.get("snapshots", {})

        metadata = {
            "total_output_length": sum(
                snapshot.get("metadata", {}).get("output_length", 0)
                for snapshot in snapshots.values()
            ),
            "average_output_length": 0,
            "elements_by_type": {},
            "elements_with_docstrings": 0,
            "elements_with_signatures": 0,
            "longest_help_output": {"element": "", "length": 0},
            "shortest_help_output": {"element": "", "length": float('inf')}
        }

        if snapshots:
            metadata["average_output_length"] = metadata["total_output_length"] / len(snapshots)

            for element_name, snapshot in snapshots.items():
                element_type = snapshot.get("element_type", "unknown")
                if element_type not in metadata["elements_by_type"]:
                    metadata["elements_by_type"][element_type] = 0
                metadata["elements_by_type"][element_type] += 1

                snapshot_metadata = snapshot.get("metadata", {})

                if snapshot_metadata.get("contains_docstring", False):
                    metadata["elements_with_docstrings"] += 1

                if snapshot_metadata.get("contains_signature", False):
                    metadata["elements_with_signatures"] += 1

                output_length = snapshot_metadata.get("output_length", 0)
                if output_length > metadata["longest_help_output"]["length"]:
                    metadata["longest_help_output"] = {
                        "element": element_name,
                        "length": output_length
                    }

                if output_length < metadata["shortest_help_output"]["length"]:
                    metadata["shortest_help_output"] = {
                        "element": element_name,
                        "length": output_length
                    }

        # Fix infinite value for JSON serialization
        if metadata["shortest_help_output"]["length"] == float('inf'):
            metadata["shortest_help_output"] = {"element": "", "length": 0}

        return metadata

    def _save_snapshots(self, snapshot_result: Dict[str, Any]) -> str:
        """Save snapshots to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"help_snapshots_{timestamp}.json"
        file_path = self.snapshots_dir / filename

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(snapshot_result, f, indent=2, sort_keys=True)

        logger.info(f"Saved help snapshots to {file_path}")
        return str(file_path)

    def compare_snapshots(self, old_snapshot_file: str, new_snapshot_file: str) -> Dict[str, Any]:
        """Compare two help snapshot files.

        Args:
            old_snapshot_file: Path to older snapshot file
            new_snapshot_file: Path to newer snapshot file

        Returns:
            Comparison result dictionary
        """
        logger.info(f"Comparing help snapshots: {old_snapshot_file} vs {new_snapshot_file}")

        try:
            # Load snapshot files
            with open(old_snapshot_file, 'r', encoding='utf-8') as f:
                old_snapshots = json.load(f)

            with open(new_snapshot_file, 'r', encoding='utf-8') as f:
                new_snapshots = json.load(f)

            comparison_result = {
                "comparison_timestamp": datetime.now().isoformat(),
                "old_snapshot_file": old_snapshot_file,
                "new_snapshot_file": new_snapshot_file,
                "old_snapshot_timestamp": old_snapshots.get("capture_timestamp", "unknown"),
                "new_snapshot_timestamp": new_snapshots.get("capture_timestamp", "unknown"),
                "changes": {
                    "added_elements": [],
                    "removed_elements": [],
                    "modified_elements": [],
                    "unchanged_elements": []
                },
                "detailed_changes": {},
                "summary": {}
            }

            old_elements = set(old_snapshots.get("snapshots", {}).keys())
            new_elements = set(new_snapshots.get("snapshots", {}).keys())

            # Find additions and removals
            comparison_result["changes"]["added_elements"] = sorted(new_elements - old_elements)
            comparison_result["changes"]["removed_elements"] = sorted(old_elements - new_elements)

            # Compare common elements
            common_elements = old_elements & new_elements
            for element_name in common_elements:
                old_snapshot = old_snapshots["snapshots"][element_name]
                new_snapshot = new_snapshots["snapshots"][element_name]

                old_hash = old_snapshot.get("help_hash", "")
                new_hash = new_snapshot.get("help_hash", "")

                if old_hash != new_hash:
                    comparison_result["changes"]["modified_elements"].append(element_name)

                    # Detailed comparison
                    detailed_change = self._compare_element_snapshots(old_snapshot, new_snapshot)
                    comparison_result["detailed_changes"][element_name] = detailed_change
                else:
                    comparison_result["changes"]["unchanged_elements"].append(element_name)

            # Generate summary
            comparison_result["summary"] = self._generate_comparison_summary(comparison_result)

            logger.info(f"Snapshot comparison completed: {len(comparison_result['changes']['modified_elements'])} changes detected")

        except Exception as e:
            error_msg = f"Snapshot comparison failed: {e}"
            logger.error(error_msg)
            comparison_result = {
                "error": error_msg,
                "comparison_timestamp": datetime.now().isoformat()
            }

        return comparison_result

    def _compare_element_snapshots(self, old_snapshot: Dict[str, Any], new_snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """Compare snapshots for a single element."""
        change_details = {
            "element_name": old_snapshot.get("element_name", "unknown"),
            "changes_detected": [],
            "old_hash": old_snapshot.get("help_hash", ""),
            "new_hash": new_snapshot.get("help_hash", ""),
            "change_analysis": {}
        }

        old_output = old_snapshot.get("help_output", "")
        new_output = new_snapshot.get("help_output", "")

        # Analyze different types of changes
        if len(old_output) != len(new_output):
            change_details["changes_detected"].append("output_length_changed")
            change_details["change_analysis"]["length_change"] = {
                "old_length": len(old_output),
                "new_length": len(new_output),
                "difference": len(new_output) - len(old_output)
            }

        # Check for signature changes
        old_signature = self._extract_signature_from_help(old_output)
        new_signature = self._extract_signature_from_help(new_output)

        if old_signature != new_signature:
            change_details["changes_detected"].append("signature_changed")
            change_details["change_analysis"]["signature_change"] = {
                "old_signature": old_signature,
                "new_signature": new_signature
            }

        # Check for docstring changes
        old_docstring = self._extract_docstring_from_help(old_output)
        new_docstring = self._extract_docstring_from_help(new_output)

        if old_docstring != new_docstring:
            change_details["changes_detected"].append("docstring_changed")
            change_details["change_analysis"]["docstring_change"] = {
                "old_length": len(old_docstring),
                "new_length": len(new_docstring),
                "content_changed": True
            }

        # Check for module changes
        old_module = old_snapshot.get("module", "")
        new_module = new_snapshot.get("module", "")

        if old_module != new_module:
            change_details["changes_detected"].append("module_changed")
            change_details["change_analysis"]["module_change"] = {
                "old_module": old_module,
                "new_module": new_module
            }

        return change_details

    def _extract_signature_from_help(self, help_output: str) -> str:
        """Extract function/method signature from help output."""
        lines = help_output.splitlines()

        for line in lines:
            # Look for lines that contain function signatures
            if "(" in line and ")" in line and not line.strip().startswith("Help on"):
                # Clean up the line
                signature_line = line.strip()
                if signature_line.endswith(":"):
                    signature_line = signature_line[:-1]
                return signature_line

        return ""

    def _extract_docstring_from_help(self, help_output: str) -> str:
        """Extract docstring content from help output."""
        lines = help_output.splitlines()
        docstring_lines = []
        in_docstring = False

        for line in lines:
            # Start of docstring is typically after a blank line following the signature
            if not in_docstring and line.strip() == "" and docstring_lines:
                continue

            # Skip header lines
            if line.strip().startswith("Help on") or line.strip().startswith("class") or line.strip().startswith("method"):
                continue

            # Detect end of docstring (methods, attributes, etc.)
            if line.strip().startswith("Methods") or line.strip().startswith("Attributes") or line.strip().startswith("Data"):
                break

            if line.strip():
                in_docstring = True
                docstring_lines.append(line)

        return "\n".join(docstring_lines)

    def _generate_comparison_summary(self, comparison_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of snapshot comparison."""
        changes = comparison_result.get("changes", {})

        return {
            "total_elements_compared": len(changes.get("unchanged_elements", [])) + len(changes.get("modified_elements", [])),
            "total_changes": len(changes.get("added_elements", [])) + len(changes.get("removed_elements", [])) + len(changes.get("modified_elements", [])),
            "additions": len(changes.get("added_elements", [])),
            "removals": len(changes.get("removed_elements", [])),
            "modifications": len(changes.get("modified_elements", [])),
            "unchanged": len(changes.get("unchanged_elements", [])),
            "change_types": self._analyze_change_types(comparison_result.get("detailed_changes", {})),
            "has_breaking_changes": len(changes.get("removed_elements", [])) > 0 or len(changes.get("modified_elements", [])) > 0
        }

    def _analyze_change_types(self, detailed_changes: Dict[str, Any]) -> Dict[str, int]:
        """Analyze types of changes detected."""
        change_type_counts = {
            "signature_changes": 0,
            "docstring_changes": 0,
            "module_changes": 0,
            "output_length_changes": 0
        }

        for element_name, change_details in detailed_changes.items():
            changes_detected = change_details.get("changes_detected", [])

            if "signature_changed" in changes_detected:
                change_type_counts["signature_changes"] += 1

            if "docstring_changed" in changes_detected:
                change_type_counts["docstring_changes"] += 1

            if "module_changed" in changes_detected:
                change_type_counts["module_changes"] += 1

            if "output_length_changed" in changes_detected:
                change_type_counts["output_length_changes"] += 1

        return change_type_counts

    def validate_current_snapshots(self, api_data: Dict[str, Any], reference_snapshot_file: Optional[str] = None) -> Dict[str, Any]:
        """Validate current help() output against reference snapshots.

        Args:
            api_data: Current API data
            reference_snapshot_file: Path to reference snapshot file (defaults to latest)

        Returns:
            Validation result dictionary
        """
        logger.info("Validating current help() snapshots")

        # Capture current snapshots
        current_snapshots = self.capture_help_snapshots(api_data)

        if not reference_snapshot_file:
            # Find the most recent snapshot file
            snapshot_files = list(self.snapshots_dir.glob("help_snapshots_*.json"))
            if len(snapshot_files) < 2:  # Need at least one reference + current
                return {
                    "validation_status": "skipped",
                    "reason": "No reference snapshot found for comparison"
                }

            # Get the second most recent (current is most recent)
            sorted_files = sorted(snapshot_files, key=lambda f: f.stat().st_mtime, reverse=True)
            reference_snapshot_file = str(sorted_files[1])

        # Compare with reference
        comparison_result = self.compare_snapshots(
            reference_snapshot_file,
            current_snapshots["snapshot_file"]
        )

        validation_result = {
            "validation_timestamp": datetime.now().isoformat(),
            "validation_status": "passed" if not comparison_result["summary"]["has_breaking_changes"] else "failed",
            "current_snapshot_file": current_snapshots["snapshot_file"],
            "reference_snapshot_file": reference_snapshot_file,
            "comparison_result": comparison_result,
            "recommendations": []
        }

        # Generate recommendations
        if comparison_result["summary"]["has_breaking_changes"]:
            validation_result["recommendations"].append("Review help() output changes for breaking changes")

        if comparison_result["summary"]["modifications"] > 0:
            validation_result["recommendations"].append("Update documentation to reflect help() output changes")

        logger.info(f"Help snapshot validation completed: {validation_result['validation_status']}")
        return validation_result

    def generate_snapshot_report(self, snapshot_result: Dict[str, Any]) -> str:
        """Generate a human-readable snapshot report."""
        report_lines = [
            f"# Help() Snapshot Report",
            f"",
            f"**Package:** {snapshot_result['package_name']}",
            f"**Capture Time:** {snapshot_result['capture_timestamp']}",
            f"",
            f"## Summary",
            f"",
            f"- **Total Elements:** {snapshot_result['total_elements']}",
            f"- **Captured Snapshots:** {snapshot_result['captured_snapshots']}",
            f"- **Failed Snapshots:** {snapshot_result['failed_snapshots']}",
            f""
        ]

        # Metadata
        metadata = snapshot_result.get("metadata", {})
        if metadata:
            report_lines.extend([
                f"## Snapshot Metadata",
                f"",
                f"- **Total Output Length:** {metadata.get('total_output_length', 0):,} characters",
                f"- **Average Output Length:** {metadata.get('average_output_length', 0):.0f} characters",
                f"- **Elements with Docstrings:** {metadata.get('elements_with_docstrings', 0)}",
                f"- **Elements with Signatures:** {metadata.get('elements_with_signatures', 0)}",
                f""
            ])

            # Longest and shortest
            longest = metadata.get("longest_help_output", {})
            shortest = metadata.get("shortest_help_output", {})

            if longest.get("element"):
                report_lines.append(f"- **Longest Help Output:** {longest['element']} ({longest['length']:,} characters)")

            if shortest.get("element"):
                report_lines.append(f"- **Shortest Help Output:** {shortest['element']} ({shortest['length']:,} characters)")

            report_lines.append("")

        # Elements by type
        elements_by_type = metadata.get("elements_by_type", {})
        if elements_by_type:
            report_lines.extend([
                f"## Elements by Type",
                f""
            ])

            for element_type, count in sorted(elements_by_type.items()):
                report_lines.append(f"- **{element_type.title()}:** {count}")

            report_lines.append("")

        # Errors
        errors = snapshot_result.get("errors", [])
        if errors:
            report_lines.extend([
                f"## Errors",
                f""
            ])
            for error in errors:
                report_lines.append(f"- {error}")

        return "\n".join(report_lines)