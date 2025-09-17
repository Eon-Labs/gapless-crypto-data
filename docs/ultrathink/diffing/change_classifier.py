"""Change classification system for ultrathink documentation system."""

from typing import Dict, List, Any, Optional, Set
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ChangeType(Enum):
    """Types of API changes."""
    ADDITION = "addition"
    REMOVAL = "removal"
    MODIFICATION = "modification"
    DEPRECATION = "deprecation"
    MOVE = "move"
    RENAME = "rename"


class Severity(Enum):
    """Severity levels for changes."""
    CRITICAL = "critical"    # Will break existing code
    HIGH = "high"           # Likely to break existing code
    MEDIUM = "medium"       # May break existing code
    LOW = "low"            # Unlikely to break existing code
    INFO = "info"          # No breaking impact


class CompatibilityImpact(Enum):
    """Impact on backward compatibility."""
    BREAKING = "breaking"
    COMPATIBLE = "compatible"
    UNKNOWN = "unknown"


class ChangeClassifier:
    """Classifies API changes by type, severity, and compatibility impact."""

    def __init__(self):
        """Initialize the change classifier."""
        self.classification_rules = self._build_classification_rules()

    def classify_changes(self, diff_result: Dict[str, Any]) -> Dict[str, Any]:
        """Classify all changes in a diff result.

        Args:
            diff_result: Result from APIDiffer.compare_versions()

        Returns:
            Enhanced diff result with classifications
        """
        signature_changes = diff_result.get("signature_changes", {})
        api_changes = diff_result.get("api_changes", {})

        classified_changes = {
            "additions": self._classify_additions(signature_changes.get("added", [])),
            "removals": self._classify_removals(signature_changes.get("removed", [])),
            "modifications": self._classify_modifications(
                signature_changes.get("modified", []),
                api_changes
            ),
            "summary": {}
        }

        # Generate classification summary
        classified_changes["summary"] = self._generate_classification_summary(classified_changes)

        # Update original diff result
        diff_result["classified_changes"] = classified_changes
        diff_result["compatibility_impact"] = self._assess_overall_compatibility(classified_changes)

        logger.info("Change classification completed")
        return diff_result

    def _classify_additions(self, added_elements: List[str]) -> List[Dict[str, Any]]:
        """Classify added API elements."""
        classified = []

        for element in added_elements:
            classification = {
                "element": element,
                "change_type": ChangeType.ADDITION.value,
                "severity": Severity.INFO.value,
                "compatibility_impact": CompatibilityImpact.COMPATIBLE.value,
                "description": f"New API element '{element}' added",
                "breaking": False,
                "deprecation_target": None,
                "migration_notes": None
            }

            # Apply specific rules for additions
            classification = self._apply_addition_rules(element, classification)
            classified.append(classification)

        return classified

    def _classify_removals(self, removed_elements: List[str]) -> List[Dict[str, Any]]:
        """Classify removed API elements."""
        classified = []

        for element in removed_elements:
            classification = {
                "element": element,
                "change_type": ChangeType.REMOVAL.value,
                "severity": Severity.CRITICAL.value,
                "compatibility_impact": CompatibilityImpact.BREAKING.value,
                "description": f"API element '{element}' removed",
                "breaking": True,
                "deprecation_target": None,
                "migration_notes": f"Remove usage of '{element}' - no longer available"
            }

            # Apply specific rules for removals
            classification = self._apply_removal_rules(element, classification)
            classified.append(classification)

        return classified

    def _classify_modifications(self, modified_elements: List[str], api_changes: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Classify modified API elements."""
        classified = []

        for element in modified_elements:
            classification = {
                "element": element,
                "change_type": ChangeType.MODIFICATION.value,
                "severity": Severity.MEDIUM.value,
                "compatibility_impact": CompatibilityImpact.UNKNOWN.value,
                "description": f"API element '{element}' modified",
                "breaking": False,
                "deprecation_target": None,
                "migration_notes": None,
                "change_details": {}
            }

            # Analyze specific changes for this element
            change_details = self._analyze_element_changes(element, api_changes)
            classification["change_details"] = change_details

            # Apply modification rules based on change details
            classification = self._apply_modification_rules(element, classification, change_details)
            classified.append(classification)

        return classified

    def _apply_addition_rules(self, element: str, classification: Dict[str, Any]) -> Dict[str, Any]:
        """Apply classification rules for additions."""
        # Most additions are compatible, but there are exceptions

        # Check for potentially problematic additions
        if any(pattern in element.lower() for pattern in ["__init__", "required", "mandatory"]):
            classification["severity"] = Severity.LOW.value
            classification["description"] += " - may require updates to existing usage"

        # Framework-specific additions might require attention
        if any(pattern in element.lower() for pattern in ["abstract", "interface", "protocol"]):
            classification["severity"] = Severity.LOW.value
            classification["description"] += " - new abstract interface"

        return classification

    def _apply_removal_rules(self, element: str, classification: Dict[str, Any]) -> Dict[str, Any]:
        """Apply classification rules for removals."""
        # All removals are breaking, but severity can vary

        # Private or internal elements are less critical
        if element.startswith("_"):
            classification["severity"] = Severity.HIGH.value
            classification["description"] += " (internal/private element)"

        # Deprecated elements are expected removals
        if "deprecated" in element.lower():
            classification["severity"] = Severity.MEDIUM.value
            classification["description"] += " (previously deprecated)"

        # Core API elements are critical
        core_patterns = ["collector", "filler", "data", "csv", "operations"]
        if any(pattern in element.lower() for pattern in core_patterns):
            classification["severity"] = Severity.CRITICAL.value
            classification["description"] += " (core functionality)"

        return classification

    def _apply_modification_rules(self, element: str, classification: Dict[str, Any], change_details: Dict[str, Any]) -> Dict[str, Any]:
        """Apply classification rules for modifications."""
        breaking_indicators = []
        severity_factors = []

        # Analyze parameter changes
        param_changes = change_details.get("parameter_changes", {})
        if param_changes:
            if param_changes.get("removed_parameters"):
                breaking_indicators.append("Parameters removed")
                severity_factors.append(Severity.CRITICAL)

            if param_changes.get("added_parameters"):
                # Check if new parameters have defaults
                breaking_indicators.append("Parameters added")
                severity_factors.append(Severity.MEDIUM)

            modified_params = param_changes.get("modified_parameters", {})
            for param_name, param_changes in modified_params.items():
                if "annotation" in param_changes:
                    breaking_indicators.append(f"Parameter type changed: {param_name}")
                    severity_factors.append(Severity.HIGH)

                if "kind" in param_changes:
                    breaking_indicators.append(f"Parameter kind changed: {param_name}")
                    severity_factors.append(Severity.HIGH)

        # Analyze return type changes
        if change_details.get("return_type_changed"):
            breaking_indicators.append("Return type changed")
            severity_factors.append(Severity.HIGH)

        # Analyze inheritance changes
        inheritance_changes = change_details.get("inheritance_changes", {})
        if inheritance_changes:
            if inheritance_changes.get("removed_bases"):
                breaking_indicators.append("Base classes removed")
                severity_factors.append(Severity.HIGH)

            if inheritance_changes.get("added_bases"):
                breaking_indicators.append("Base classes added")
                severity_factors.append(Severity.LOW)

        # Type changes
        if change_details.get("type_changed"):
            breaking_indicators.append("Element type changed")
            severity_factors.append(Severity.CRITICAL)

        # Module changes
        if change_details.get("module_changed"):
            breaking_indicators.append("Module location changed")
            severity_factors.append(Severity.MEDIUM)

        # Determine overall impact
        if breaking_indicators:
            classification["breaking"] = True
            classification["compatibility_impact"] = CompatibilityImpact.BREAKING.value

            # Use highest severity
            if Severity.CRITICAL in severity_factors:
                classification["severity"] = Severity.CRITICAL.value
            elif Severity.HIGH in severity_factors:
                classification["severity"] = Severity.HIGH.value
            else:
                classification["severity"] = Severity.MEDIUM.value

            classification["description"] += f" - {', '.join(breaking_indicators)}"

            # Generate migration notes
            classification["migration_notes"] = self._generate_migration_notes(element, breaking_indicators, change_details)
        else:
            classification["compatibility_impact"] = CompatibilityImpact.COMPATIBLE.value
            classification["severity"] = Severity.LOW.value
            classification["description"] += " - non-breaking changes"

        return classification

    def _analyze_element_changes(self, element: str, api_changes: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze specific changes for an element."""
        changes = {}

        # Parameter changes
        param_changes = api_changes.get("parameter_changes", {}).get(element)
        if param_changes:
            changes["parameter_changes"] = param_changes

        # Return type changes
        return_changes = api_changes.get("return_type_changes", {}).get(element)
        if return_changes:
            changes["return_type_changed"] = True
            changes["return_type_details"] = return_changes

        # Type changes
        type_changes = api_changes.get("type_changes", {}).get(element)
        if type_changes:
            changes["type_changed"] = True
            changes["type_details"] = type_changes

        # Module changes
        module_changes = api_changes.get("module_changes", {}).get(element)
        if module_changes:
            changes["module_changed"] = True
            changes["module_details"] = module_changes

        # Inheritance changes
        inheritance_changes = api_changes.get("inheritance_changes", {}).get(element)
        if inheritance_changes:
            changes["inheritance_changes"] = inheritance_changes

        return changes

    def _generate_migration_notes(self, element: str, breaking_indicators: List[str], change_details: Dict[str, Any]) -> str:
        """Generate migration notes for breaking changes."""
        notes = [f"Migration required for '{element}':"]

        if "Parameters removed" in breaking_indicators:
            param_changes = change_details.get("parameter_changes", {})
            removed_params = param_changes.get("removed_parameters", [])
            notes.append(f"- Remove parameters: {', '.join(removed_params)}")

        if "Parameters added" in breaking_indicators:
            param_changes = change_details.get("parameter_changes", {})
            added_params = param_changes.get("added_parameters", [])
            notes.append(f"- Add parameters: {', '.join(added_params)}")

        if "Return type changed" in breaking_indicators:
            return_details = change_details.get("return_type_details", {})
            notes.append(f"- Update return type handling: {return_details.get('old')} -> {return_details.get('new')}")

        if "Element type changed" in breaking_indicators:
            type_details = change_details.get("type_details", {})
            notes.append(f"- Element type changed: {type_details.get('old')} -> {type_details.get('new')}")

        if "Module location changed" in breaking_indicators:
            module_details = change_details.get("module_details", {})
            notes.append(f"- Update import: from {module_details.get('old')} to {module_details.get('new')}")

        return "\n".join(notes)

    def _generate_classification_summary(self, classified_changes: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of all classifications."""
        summary = {
            "total_changes": 0,
            "by_type": {},
            "by_severity": {},
            "by_compatibility": {},
            "breaking_changes_count": 0,
            "critical_changes": [],
            "migration_required": []
        }

        all_changes = (
            classified_changes.get("additions", []) +
            classified_changes.get("removals", []) +
            classified_changes.get("modifications", [])
        )

        summary["total_changes"] = len(all_changes)

        for change in all_changes:
            # Count by type
            change_type = change.get("change_type", "unknown")
            summary["by_type"][change_type] = summary["by_type"].get(change_type, 0) + 1

            # Count by severity
            severity = change.get("severity", "unknown")
            summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1

            # Count by compatibility
            compatibility = change.get("compatibility_impact", "unknown")
            summary["by_compatibility"][compatibility] = summary["by_compatibility"].get(compatibility, 0) + 1

            # Track breaking changes
            if change.get("breaking", False):
                summary["breaking_changes_count"] += 1

            # Track critical changes
            if severity == Severity.CRITICAL.value:
                summary["critical_changes"].append(change["element"])

            # Track migration requirements
            if change.get("migration_notes"):
                summary["migration_required"].append(change["element"])

        return summary

    def _assess_overall_compatibility(self, classified_changes: Dict[str, Any]) -> str:
        """Assess overall compatibility impact."""
        summary = classified_changes.get("summary", {})

        if summary.get("breaking_changes_count", 0) > 0:
            return CompatibilityImpact.BREAKING.value
        else:
            return CompatibilityImpact.COMPATIBLE.value

    def _build_classification_rules(self) -> Dict[str, Any]:
        """Build the classification rule set."""
        # This could be expanded to load rules from configuration files
        return {
            "breaking_patterns": [
                "parameter_removal",
                "return_type_change",
                "type_change",
                "signature_change"
            ],
            "severity_mappings": {
                "removal": Severity.CRITICAL,
                "parameter_removal": Severity.CRITICAL,
                "type_change": Severity.CRITICAL,
                "return_type_change": Severity.HIGH,
                "parameter_addition": Severity.MEDIUM,
                "module_change": Severity.MEDIUM,
                "addition": Severity.INFO
            },
            "compatibility_exceptions": [
                # Patterns that might seem breaking but aren't
                "private_element",
                "deprecated_element",
                "internal_api"
            ]
        }

    def suggest_version_bump(self, classified_changes: Dict[str, Any], current_version: str) -> Dict[str, Any]:
        """Suggest appropriate version bump based on changes.

        Args:
            classified_changes: Classified changes from classify_changes()
            current_version: Current version string

        Returns:
            Version bump suggestion with reasoning
        """
        summary = classified_changes.get("summary", {})
        breaking_count = summary.get("breaking_changes_count", 0)
        total_changes = summary.get("total_changes", 0)

        # Semantic versioning rules
        if breaking_count > 0:
            suggested_bump = "major"
            reason = f"Breaking changes detected ({breaking_count} breaking changes)"
        elif summary.get("by_type", {}).get("addition", 0) > 0:
            suggested_bump = "minor"
            reason = f"New features added ({summary['by_type']['addition']} additions)"
        elif total_changes > 0:
            suggested_bump = "patch"
            reason = f"Bug fixes or documentation changes ({total_changes} changes)"
        else:
            suggested_bump = None
            reason = "No changes detected"

        return {
            "current_version": current_version,
            "suggested_bump": suggested_bump,
            "reason": reason,
            "breaking_changes": breaking_count,
            "total_changes": total_changes,
            "critical_changes": len(summary.get("critical_changes", [])),
            "migration_required": len(summary.get("migration_required", []))
        }