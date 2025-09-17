"""API difference detection for ultrathink documentation system."""

import json
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging
from datetime import datetime

from ..introspection.signature_hasher import SignatureHasher

logger = logging.getLogger(__name__)


class APIDiffer:
    """Detects and analyzes differences between API versions."""

    def __init__(self, storage_directory: str = "docs/ultrathink/storage"):
        """Initialize the API differ.

        Args:
            storage_directory: Directory for storing API snapshots and diffs
        """
        self.storage_dir = Path(storage_directory)
        self.snapshots_dir = self.storage_dir / "api_snapshots"
        self.diffs_dir = self.storage_dir / "api_diffs"

        # Ensure directories exist
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        self.diffs_dir.mkdir(parents=True, exist_ok=True)

        self.hasher = SignatureHasher()

    def create_api_snapshot(self, api_data: Dict[str, Any], version: str) -> str:
        """Create and store an API snapshot for a specific version.

        Args:
            api_data: Complete API data from APIExtractor
            version: Version string (e.g., "2.1.1")

        Returns:
            Path to the created snapshot file
        """
        timestamp = datetime.now().isoformat()

        # Create comprehensive snapshot
        snapshot = {
            "version": version,
            "timestamp": timestamp,
            "api_data": api_data,
            "signature_hashes": self.hasher.hash_api_signature(api_data),
            "metadata": {
                "package_name": api_data.get("package_info", {}).get("name", "unknown"),
                "total_elements": len(api_data.get("public_api", {})),
                "snapshot_format_version": "1.0"
            }
        }

        # Save snapshot
        snapshot_file = self.snapshots_dir / f"api_snapshot_{version}_{timestamp[:10]}.json"
        with open(snapshot_file, 'w', encoding='utf-8') as f:
            json.dump(snapshot, f, indent=2, sort_keys=True)

        logger.info(f"Created API snapshot for version {version}: {snapshot_file}")
        return str(snapshot_file)

    def compare_versions(self, old_version: str, new_version: str) -> Dict[str, Any]:
        """Compare two API versions and generate detailed diff.

        Args:
            old_version: Previous version to compare from
            new_version: New version to compare to

        Returns:
            Comprehensive diff analysis
        """
        old_snapshot = self._load_latest_snapshot(old_version)
        new_snapshot = self._load_latest_snapshot(new_version)

        if not old_snapshot:
            raise ValueError(f"No snapshot found for version {old_version}")
        if not new_snapshot:
            raise ValueError(f"No snapshot found for version {new_version}")

        diff_result = {
            "comparison_info": {
                "old_version": old_version,
                "new_version": new_version,
                "comparison_timestamp": datetime.now().isoformat(),
                "old_snapshot_timestamp": old_snapshot["timestamp"],
                "new_snapshot_timestamp": new_snapshot["timestamp"]
            },
            "signature_changes": self._compare_signatures(old_snapshot, new_snapshot),
            "api_changes": self._compare_api_structures(old_snapshot, new_snapshot),
            "documentation_changes": self._compare_documentation(old_snapshot, new_snapshot),
            "breaking_changes": [],
            "deprecations": [],
            "summary": {}
        }

        # Analyze and classify changes
        diff_result = self._analyze_breaking_changes(diff_result)
        diff_result = self._generate_summary(diff_result)

        # Save diff
        self._save_diff(diff_result, old_version, new_version)

        logger.info(f"API comparison completed: {old_version} -> {new_version}")
        return diff_result

    def _load_latest_snapshot(self, version: str) -> Optional[Dict[str, Any]]:
        """Load the latest snapshot for a given version."""
        pattern = f"api_snapshot_{version}_*.json"
        snapshot_files = list(self.snapshots_dir.glob(pattern))

        if not snapshot_files:
            logger.warning(f"No snapshot found for version {version}")
            return None

        # Get the most recent snapshot for this version
        latest_file = max(snapshot_files, key=lambda f: f.stat().st_mtime)

        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load snapshot {latest_file}: {e}")
            return None

    def _compare_signatures(self, old_snapshot: Dict[str, Any], new_snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """Compare signature hashes between snapshots."""
        old_hashes = old_snapshot.get("signature_hashes", {})
        new_hashes = new_snapshot.get("signature_hashes", {})

        return self.hasher.compare_signatures(old_hashes, new_hashes)

    def _compare_api_structures(self, old_snapshot: Dict[str, Any], new_snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """Compare API structure changes beyond signatures."""
        old_api = old_snapshot.get("api_data", {}).get("public_api", {})
        new_api = new_snapshot.get("api_data", {}).get("public_api", {})

        changes = {
            "type_changes": {},
            "module_changes": {},
            "inheritance_changes": {},
            "parameter_changes": {},
            "return_type_changes": {}
        }

        # Compare common elements for detailed changes
        common_elements = set(old_api.keys()) & set(new_api.keys())

        for element_name in common_elements:
            old_element = old_api[element_name]
            new_element = new_api[element_name]

            # Type changes
            old_type = old_element.get("type", "unknown")
            new_type = new_element.get("type", "unknown")
            if old_type != new_type:
                changes["type_changes"][element_name] = {
                    "old": old_type,
                    "new": new_type
                }

            # Module changes
            old_module = old_element.get("module", "unknown")
            new_module = new_element.get("module", "unknown")
            if old_module != new_module:
                changes["module_changes"][element_name] = {
                    "old": old_module,
                    "new": new_module
                }

            # Class-specific changes
            if old_type == "class" and new_type == "class":
                self._compare_class_changes(element_name, old_element, new_element, changes)

            # Function-specific changes
            elif old_type in ("function", "method") and new_type in ("function", "method"):
                self._compare_function_changes(element_name, old_element, new_element, changes)

        return changes

    def _compare_class_changes(self, class_name: str, old_class: Dict[str, Any], new_class: Dict[str, Any], changes: Dict[str, Any]):
        """Compare changes in class definitions."""
        # Inheritance changes
        old_bases = set(old_class.get("base_classes", []))
        new_bases = set(new_class.get("base_classes", []))

        if old_bases != new_bases:
            changes["inheritance_changes"][class_name] = {
                "added_bases": sorted(new_bases - old_bases),
                "removed_bases": sorted(old_bases - new_bases)
            }

        # Method changes would be handled by signature comparison
        # Additional class-specific analysis could be added here

    def _compare_function_changes(self, func_name: str, old_func: Dict[str, Any], new_func: Dict[str, Any], changes: Dict[str, Any]):
        """Compare changes in function definitions."""
        # Parameter changes (detailed analysis)
        old_params = old_func.get("parameters", {})
        new_params = new_func.get("parameters", {})

        param_changes = {
            "added_parameters": [],
            "removed_parameters": [],
            "modified_parameters": {}
        }

        old_param_names = set(old_params.keys())
        new_param_names = set(new_params.keys())

        param_changes["added_parameters"] = sorted(new_param_names - old_param_names)
        param_changes["removed_parameters"] = sorted(old_param_names - new_param_names)

        # Check for parameter modifications
        common_params = old_param_names & new_param_names
        for param_name in common_params:
            old_param = old_params[param_name]
            new_param = new_params[param_name]

            param_diff = {}
            if old_param.get("annotation") != new_param.get("annotation"):
                param_diff["annotation"] = {
                    "old": old_param.get("annotation"),
                    "new": new_param.get("annotation")
                }
            if old_param.get("default") != new_param.get("default"):
                param_diff["default"] = {
                    "old": old_param.get("default"),
                    "new": new_param.get("default")
                }
            if old_param.get("kind") != new_param.get("kind"):
                param_diff["kind"] = {
                    "old": old_param.get("kind"),
                    "new": new_param.get("kind")
                }

            if param_diff:
                param_changes["modified_parameters"][param_name] = param_diff

        if any(param_changes.values()):
            changes["parameter_changes"][func_name] = param_changes

        # Return type changes
        old_return = old_func.get("return_annotation")
        new_return = new_func.get("return_annotation")
        if old_return != new_return:
            changes["return_type_changes"][func_name] = {
                "old": old_return,
                "new": new_return
            }

    def _compare_documentation(self, old_snapshot: Dict[str, Any], new_snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """Compare documentation changes between versions."""
        old_docs = old_snapshot.get("api_data", {}).get("docstrings", {})
        new_docs = new_snapshot.get("api_data", {}).get("docstrings", {})

        doc_changes = {
            "added_docs": [],
            "removed_docs": [],
            "modified_docs": {},
            "summary_changes": {}
        }

        old_elements = set(old_docs.keys())
        new_elements = set(new_docs.keys())

        doc_changes["added_docs"] = sorted(new_elements - old_elements)
        doc_changes["removed_docs"] = sorted(old_elements - new_elements)

        # Compare existing documentation
        common_elements = old_elements & new_elements
        for element_name in common_elements:
            old_doc = old_docs[element_name]
            new_doc = new_docs[element_name]

            element_changes = {}

            # Compare raw docstring
            old_raw = old_doc.get("raw", "")
            new_raw = new_doc.get("raw", "")
            if old_raw != new_raw:
                element_changes["raw_changed"] = True

            # Compare summary
            old_summary = old_doc.get("summary", "")
            new_summary = new_doc.get("summary", "")
            if old_summary != new_summary:
                element_changes["summary"] = {
                    "old": old_summary,
                    "new": new_summary
                }
                doc_changes["summary_changes"][element_name] = element_changes["summary"]

            # Compare sections
            old_sections = old_doc.get("sections", {})
            new_sections = new_doc.get("sections", {})
            if old_sections != new_sections:
                element_changes["sections_changed"] = True

            if element_changes:
                doc_changes["modified_docs"][element_name] = element_changes

        return doc_changes

    def _analyze_breaking_changes(self, diff_result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze and classify breaking changes."""
        breaking_changes = []
        signature_changes = diff_result.get("signature_changes", {})
        api_changes = diff_result.get("api_changes", {})

        # Removed elements are always breaking
        for removed_element in signature_changes.get("removed", []):
            breaking_changes.append({
                "type": "removal",
                "element": removed_element,
                "severity": "high",
                "description": f"API element '{removed_element}' was removed"
            })

        # Modified signatures can be breaking
        for modified_element in signature_changes.get("modified", []):
            breaking_changes.append({
                "type": "signature_change",
                "element": modified_element,
                "severity": "medium",
                "description": f"API signature for '{modified_element}' was modified"
            })

        # Parameter changes analysis
        param_changes = api_changes.get("parameter_changes", {})
        for func_name, changes in param_changes.items():
            if changes.get("removed_parameters"):
                breaking_changes.append({
                    "type": "parameter_removal",
                    "element": func_name,
                    "severity": "high",
                    "description": f"Parameters removed from '{func_name}': {changes['removed_parameters']}"
                })

            # Required parameter additions can be breaking
            added_params = changes.get("added_parameters", [])
            if added_params:
                # This is simplified - would need to check if parameters have defaults
                breaking_changes.append({
                    "type": "parameter_addition",
                    "element": func_name,
                    "severity": "medium",
                    "description": f"Parameters added to '{func_name}': {added_params}"
                })

        # Type changes
        type_changes = api_changes.get("type_changes", {})
        for element_name, change in type_changes.items():
            breaking_changes.append({
                "type": "type_change",
                "element": element_name,
                "severity": "high",
                "description": f"Type of '{element_name}' changed from {change['old']} to {change['new']}"
            })

        diff_result["breaking_changes"] = breaking_changes
        return diff_result

    def _generate_summary(self, diff_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of all changes."""
        signature_changes = diff_result.get("signature_changes", {})
        breaking_changes = diff_result.get("breaking_changes", [])
        doc_changes = diff_result.get("documentation_changes", {})

        summary = {
            "total_changes": (
                len(signature_changes.get("added", [])) +
                len(signature_changes.get("removed", [])) +
                len(signature_changes.get("modified", []))
            ),
            "api_additions": len(signature_changes.get("added", [])),
            "api_removals": len(signature_changes.get("removed", [])),
            "api_modifications": len(signature_changes.get("modified", [])),
            "breaking_changes_count": len(breaking_changes),
            "documentation_changes": {
                "added": len(doc_changes.get("added_docs", [])),
                "removed": len(doc_changes.get("removed_docs", [])),
                "modified": len(doc_changes.get("modified_docs", {}))
            },
            "severity_analysis": {
                "high": len([bc for bc in breaking_changes if bc.get("severity") == "high"]),
                "medium": len([bc for bc in breaking_changes if bc.get("severity") == "medium"]),
                "low": len([bc for bc in breaking_changes if bc.get("severity") == "low"])
            },
            "compatibility_assessment": "breaking" if breaking_changes else "compatible"
        }

        diff_result["summary"] = summary
        return diff_result

    def _save_diff(self, diff_result: Dict[str, Any], old_version: str, new_version: str):
        """Save the diff result to storage."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        diff_file = self.diffs_dir / f"diff_{old_version}_to_{new_version}_{timestamp}.json"

        with open(diff_file, 'w', encoding='utf-8') as f:
            json.dump(diff_result, f, indent=2, sort_keys=True)

        logger.info(f"Diff saved to {diff_file}")

    def get_version_history(self) -> List[Dict[str, Any]]:
        """Get a list of all available version snapshots."""
        snapshots = []

        for snapshot_file in sorted(self.snapshots_dir.glob("api_snapshot_*.json")):
            try:
                with open(snapshot_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    snapshots.append({
                        "version": data.get("version", "unknown"),
                        "timestamp": data.get("timestamp", "unknown"),
                        "file": str(snapshot_file),
                        "total_elements": data.get("metadata", {}).get("total_elements", 0)
                    })
            except Exception as e:
                logger.warning(f"Failed to read snapshot {snapshot_file}: {e}")

        return snapshots

    def cleanup_old_snapshots(self, retention_days: int = 365):
        """Clean up old snapshots based on retention policy."""
        import time

        cutoff_time = time.time() - (retention_days * 24 * 60 * 60)
        cleaned_count = 0

        for snapshot_file in self.snapshots_dir.glob("api_snapshot_*.json"):
            if snapshot_file.stat().st_mtime < cutoff_time:
                try:
                    snapshot_file.unlink()
                    cleaned_count += 1
                    logger.debug(f"Cleaned up old snapshot: {snapshot_file}")
                except Exception as e:
                    logger.warning(f"Failed to clean up {snapshot_file}: {e}")

        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} old snapshots")

        return cleaned_count