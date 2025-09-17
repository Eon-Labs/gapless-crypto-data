"""Deprecation management for ultrathink documentation system."""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
import logging
import re

from ..diffing.version_tracker import VersionTracker

logger = logging.getLogger(__name__)


class DeprecationManager:
    """Manages API deprecations and generates deprecation documentation."""

    def __init__(self, storage_directory: str = "docs/ultrathink/storage"):
        """Initialize the deprecation manager.

        Args:
            storage_directory: Directory for storing deprecation data
        """
        self.storage_dir = Path(storage_directory)
        self.deprecations_dir = self.storage_dir / "deprecations"
        self.deprecations_dir.mkdir(parents=True, exist_ok=True)

        self.version_tracker = VersionTracker(storage_directory)

    def analyze_deprecation_candidates(self, diff_result: Dict[str, Any], current_version: str) -> List[Dict[str, Any]]:
        """Analyze API changes to identify deprecation candidates.

        Args:
            diff_result: Result from APIDiffer.compare_versions()
            current_version: Current version string

        Returns:
            List of deprecation candidate information
        """
        candidates = []

        # Elements that were removed (should have been deprecated first)
        removed_elements = diff_result.get("signature_changes", {}).get("removed", [])
        for element in removed_elements:
            candidates.append({
                "element": element,
                "type": "removed_without_deprecation",
                "severity": "high",
                "recommendation": "Should have been deprecated in a previous version",
                "current_version": current_version
            })

        # Elements with breaking changes (candidates for deprecation)
        breaking_changes = diff_result.get("breaking_changes", [])
        for change in breaking_changes:
            if change.get("severity") in ["critical", "high"]:
                candidates.append({
                    "element": change.get("element", "unknown"),
                    "type": "breaking_change_candidate",
                    "severity": "medium",
                    "recommendation": "Consider deprecating current signature and introducing new one",
                    "change_details": change.get("description", ""),
                    "current_version": current_version
                })

        logger.info(f"Identified {len(candidates)} deprecation candidates")
        return candidates

    def create_deprecation_plan(self, candidates: List[Dict[str, Any]], target_major_version: Optional[str] = None) -> Dict[str, Any]:
        """Create a deprecation plan for identified candidates.

        Args:
            candidates: List of deprecation candidates
            target_major_version: Target major version for removal

        Returns:
            Deprecation plan with timeline and recommendations
        """
        current_version_info = self.version_tracker.get_current_version()
        if not current_version_info:
            raise ValueError("No current version found in version tracker")

        current_version = current_version_info["version_string"]
        parsed_current = self.version_tracker.parse_version(current_version)

        # Calculate target removal version
        if not target_major_version:
            target_major_version = f"{parsed_current['major'] + 1}.0.0"

        plan = {
            "plan_created": datetime.now().isoformat(),
            "current_version": current_version,
            "target_removal_version": target_major_version,
            "deprecation_timeline": [],
            "immediate_actions": [],
            "future_actions": [],
            "communication_plan": {},
            "migration_guides": {}
        }

        for candidate in candidates:
            element = candidate["element"]

            if candidate["type"] == "removed_without_deprecation":
                # These are already removed - document the removal
                plan["immediate_actions"].append({
                    "action": "document_removal",
                    "element": element,
                    "description": f"Document that {element} was removed without deprecation warning",
                    "priority": "high"
                })

            elif candidate["type"] == "breaking_change_candidate":
                # These should be deprecated now
                deprecation_version = current_version

                timeline_entry = {
                    "element": element,
                    "deprecation_version": deprecation_version,
                    "removal_version": target_major_version,
                    "reason": candidate.get("change_details", "Breaking change detected"),
                    "alternative": "TBD - needs manual specification",
                    "timeline_phases": [
                        {
                            "phase": "deprecation_warning",
                            "version": deprecation_version,
                            "actions": [
                                "Add deprecation warning to docstring",
                                "Add runtime deprecation warning",
                                "Update documentation with deprecation notice"
                            ]
                        },
                        {
                            "phase": "removal",
                            "version": target_major_version,
                            "actions": [
                                "Remove deprecated element",
                                "Update documentation",
                                "Ensure migration guide is complete"
                            ]
                        }
                    ]
                }

                plan["deprecation_timeline"].append(timeline_entry)

                # Add to immediate actions
                plan["immediate_actions"].append({
                    "action": "add_deprecation_warning",
                    "element": element,
                    "description": f"Add deprecation warning to {element}",
                    "priority": "high"
                })

        # Generate communication plan
        plan["communication_plan"] = self._generate_communication_plan(plan)

        # Save the plan
        plan_file = self._save_deprecation_plan(plan)
        plan["plan_file"] = plan_file

        logger.info(f"Created deprecation plan with {len(plan['deprecation_timeline'])} elements")
        return plan

    def _generate_communication_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Generate communication plan for deprecations."""
        return {
            "changelog_entries": [
                {
                    "version": plan["current_version"],
                    "section": "deprecated",
                    "entries": [
                        f"Deprecated {item['element']}: {item.get('reason', 'TBD')}"
                        for item in plan["deprecation_timeline"]
                    ]
                }
            ],
            "documentation_updates": [
                "Update API reference with deprecation warnings",
                "Create migration guide for deprecated elements",
                "Update examples to use non-deprecated APIs"
            ],
            "release_notes": [
                f"This version deprecates {len(plan['deprecation_timeline'])} API elements",
                f"Deprecated elements will be removed in version {plan['target_removal_version']}"
            ]
        }

    def generate_deprecation_documentation(self, deprecation_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate deprecation documentation files.

        Args:
            deprecation_data: Deprecation data (from database or plan)

        Returns:
            Dictionary mapping documentation type to file path
        """
        docs = {}

        # Deprecation summary
        summary_content = self._generate_deprecation_summary(deprecation_data)
        summary_file = self.deprecations_dir / "deprecation_summary.md"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary_content)
        docs["summary"] = str(summary_file)

        # Migration guide
        migration_content = self._generate_migration_guide(deprecation_data)
        migration_file = self.deprecations_dir / "migration_guide.md"
        with open(migration_file, 'w', encoding='utf-8') as f:
            f.write(migration_content)
        docs["migration_guide"] = str(migration_file)

        # Deprecation timeline
        timeline_content = self._generate_deprecation_timeline(deprecation_data)
        timeline_file = self.deprecations_dir / "deprecation_timeline.md"
        with open(timeline_file, 'w', encoding='utf-8') as f:
            f.write(timeline_content)
        docs["timeline"] = str(timeline_file)

        logger.info(f"Generated {len(docs)} deprecation documentation files")
        return docs

    def _generate_deprecation_summary(self, deprecation_data: Dict[str, Any]) -> str:
        """Generate deprecation summary documentation."""
        if "deprecation_timeline" in deprecation_data:
            # Data from deprecation plan
            timeline = deprecation_data["deprecation_timeline"]
            current_version = deprecation_data.get("current_version", "unknown")
            target_version = deprecation_data.get("target_removal_version", "unknown")
        else:
            # Data from database
            deprecations = self.version_tracker.get_deprecations()
            timeline = deprecations
            current_version = "current"
            target_version = "TBD"

        content = [
            "# Deprecation Summary",
            "",
            f"**Current Version:** {current_version}",
            f"**Target Removal Version:** {target_version}",
            f"**Last Updated:** {datetime.now().isoformat()}",
            "",
            "## Overview",
            "",
            f"This document summarizes {len(timeline)} deprecated API elements and their removal timeline.",
            "",
            "## Deprecated Elements",
            ""
        ]

        # Group by deprecation version
        by_version = {}
        for item in timeline:
            if "deprecation_version" in item:
                version = item["deprecation_version"]
            elif "deprecated_in_version" in item:
                version = item["deprecated_in_version"]
            else:
                version = "unknown"

            if version not in by_version:
                by_version[version] = []
            by_version[version].append(item)

        for version, items in sorted(by_version.items()):
            content.append(f"### Deprecated in Version {version}")
            content.append("")

            for item in items:
                element = item.get("element") or item.get("element_name", "unknown")
                reason = item.get("reason", "No reason specified")
                alternative = item.get("alternative", "No alternative specified")

                content.append(f"#### {element}")
                content.append("")
                content.append(f"**Reason:** {reason}")
                content.append(f"**Alternative:** {alternative}")

                if "removal_version" in item:
                    content.append(f"**Removal Target:** {item['removal_version']}")
                elif "removal_target_version" in item:
                    content.append(f"**Removal Target:** {item['removal_target_version']}")

                content.append("")

        content.extend([
            "## Migration Timeline",
            "",
            "1. **Immediate:** Update code to use non-deprecated alternatives",
            "2. **Before Next Major Version:** Ensure all deprecated API usage is removed",
            "3. **Future Versions:** Deprecated elements will be removed",
            "",
            "---",
            "*Generated by Ultrathink Documentation System*"
        ])

        return "\n".join(content)

    def _generate_migration_guide(self, deprecation_data: Dict[str, Any]) -> str:
        """Generate migration guide documentation."""
        content = [
            "# Migration Guide for Deprecated APIs",
            "",
            f"**Generated:** {datetime.now().isoformat()}",
            "",
            "This guide helps you migrate away from deprecated API elements.",
            "",
            "## Quick Migration Checklist",
            "",
            "- [ ] Identify deprecated API usage in your code",
            "- [ ] Review alternatives for each deprecated element",
            "- [ ] Update code to use new APIs",
            "- [ ] Test thoroughly",
            "- [ ] Update documentation and examples",
            "",
            "## Element-by-Element Migration Guide",
            ""
        ]

        # Get timeline or deprecations
        if "deprecation_timeline" in deprecation_data:
            timeline = deprecation_data["deprecation_timeline"]
        else:
            timeline = self.version_tracker.get_deprecations()

        for item in timeline:
            element = item.get("element") or item.get("element_name", "unknown")
            reason = item.get("reason", "No reason specified")
            alternative = item.get("alternative", "No alternative specified")

            content.extend([
                f"### {element}",
                "",
                f"**Status:** Deprecated",
                f"**Reason:** {reason}",
                "",
                "#### Migration Steps",
                "",
                "1. **Find Usage:**",
                "   ```bash",
                f"   grep -r '{element}' your_project/",
                "   ```",
                "",
                "2. **Replace With:**",
                "   ```python",
                f"   # Old (deprecated)",
                f"   # {element}(...)",
                "   ",
                f"   # New (recommended)",
                f"   # {alternative}",
                "   ```",
                "",
                "3. **Test:** Ensure functionality remains the same",
                "",
                "4. **Verify:** No deprecation warnings in logs",
                ""
            ])

        content.extend([
            "## Common Migration Patterns",
            "",
            "### Pattern 1: Direct Replacement",
            "For simple API renames or moves:",
            "```python",
            "# Find and replace throughout your codebase",
            "# Old: old_function_name",
            "# New: new_function_name",
            "```",
            "",
            "### Pattern 2: Parameter Changes",
            "For functions with changed parameters:",
            "```python",
            "# Old: function(old_param=value)",
            "# New: function(new_param=value)",
            "```",
            "",
            "### Pattern 3: Class Restructuring",
            "For deprecated classes:",
            "```python",
            "# Old: OldClass()",
            "# New: NewClass() or use composition",
            "```",
            "",
            "## Automated Migration Tools",
            "",
            "Consider using these tools to help with migration:",
            "",
            "- `sed` or `awk` for simple find/replace operations",
            "- IDE refactoring tools for more complex changes",
            "- Custom migration scripts for project-specific patterns",
            "",
            "## Getting Help",
            "",
            "If you encounter issues during migration:",
            "",
            "1. Check the documentation for new APIs",
            "2. Look for examples in the repository",
            "3. Open an issue on GitHub",
            "",
            "---",
            "*Generated by Ultrathink Documentation System*"
        ])

        return "\n".join(content)

    def _generate_deprecation_timeline(self, deprecation_data: Dict[str, Any]) -> str:
        """Generate deprecation timeline documentation."""
        content = [
            "# Deprecation Timeline",
            "",
            f"**Generated:** {datetime.now().isoformat()}",
            "",
            "This document shows the timeline for API deprecations and removals.",
            ""
        ]

        # Create timeline view
        if "deprecation_timeline" in deprecation_data:
            timeline = deprecation_data["deprecation_timeline"]

            # Group by version
            by_version = {}
            for item in timeline:
                dep_version = item.get("deprecation_version", "unknown")
                rem_version = item.get("removal_version", "TBD")

                if dep_version not in by_version:
                    by_version[dep_version] = {"deprecated": [], "removed": []}
                by_version[dep_version]["deprecated"].append(item)

                if rem_version != "TBD":
                    if rem_version not in by_version:
                        by_version[rem_version] = {"deprecated": [], "removed": []}
                    by_version[rem_version]["removed"].append(item)

            # Generate timeline
            for version in sorted(by_version.keys()):
                version_data = by_version[version]

                content.append(f"## Version {version}")
                content.append("")

                if version_data["deprecated"]:
                    content.append("### Elements Deprecated")
                    for item in version_data["deprecated"]:
                        element = item.get("element", "unknown")
                        reason = item.get("reason", "No reason")
                        content.append(f"- **{element}**: {reason}")
                    content.append("")

                if version_data["removed"]:
                    content.append("### Elements Removed")
                    for item in version_data["removed"]:
                        element = item.get("element", "unknown")
                        content.append(f"- **{element}**: Removed as planned")
                    content.append("")

        else:
            # Database format
            deprecations = self.version_tracker.get_deprecations()

            content.append("## Current Deprecations")
            content.append("")

            for dep in deprecations:
                element = dep.get("element_name", "unknown")
                dep_version = dep.get("deprecated_in_version", "unknown")
                rem_version = dep.get("removal_target_version", "TBD")
                reason = dep.get("reason", "No reason specified")

                content.extend([
                    f"### {element}",
                    "",
                    f"- **Deprecated in:** {dep_version}",
                    f"- **Removal target:** {rem_version}",
                    f"- **Reason:** {reason}",
                    ""
                ])

        content.extend([
            "## Timeline Legend",
            "",
            "- 🚨 **Deprecated**: Element marked as deprecated, warnings added",
            "- ❌ **Removed**: Element completely removed from API",
            "- 📝 **Planned**: Scheduled for future deprecation/removal",
            "",
            "---",
            "*Generated by Ultrathink Documentation System*"
        ])

        return "\n".join(content)

    def _save_deprecation_plan(self, plan: Dict[str, Any]) -> str:
        """Save deprecation plan to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"deprecation_plan_{timestamp}.json"
        file_path = self.deprecations_dir / filename

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(plan, f, indent=2, sort_keys=True)

        logger.info(f"Saved deprecation plan to {file_path}")
        return str(file_path)

    def get_active_deprecations(self, current_version: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get list of currently active deprecations.

        Args:
            current_version: Current version to check against

        Returns:
            List of active deprecation records
        """
        return self.version_tracker.get_deprecations(current_version)

    def check_removal_candidates(self, current_version: str) -> List[Dict[str, Any]]:
        """Check for deprecations that are ready for removal.

        Args:
            current_version: Current version string

        Returns:
            List of deprecations ready for removal
        """
        deprecations = self.get_active_deprecations(current_version)
        removal_candidates = []

        current_parsed = self.version_tracker.parse_version(current_version)

        for dep in deprecations:
            removal_version = dep.get("removal_target_version")
            if removal_version:
                removal_parsed = self.version_tracker.parse_version(removal_version)

                # Check if current version >= removal target
                if self.version_tracker.compare_versions(current_version, removal_version) >= 0:
                    removal_candidates.append({
                        "element": dep.get("element_name"),
                        "deprecated_in": dep.get("deprecated_in_version"),
                        "removal_target": removal_version,
                        "reason": dep.get("reason"),
                        "alternative": dep.get("alternative"),
                        "ready_for_removal": True
                    })

        logger.info(f"Found {len(removal_candidates)} elements ready for removal")
        return removal_candidates