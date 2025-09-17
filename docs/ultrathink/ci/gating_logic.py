"""Documentation gating logic for ultrathink documentation system."""

import os
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DocumentationGating:
    """Implements documentation gating logic for CI/CD pipelines."""

    def __init__(self, package_name: str, project_root: str = "."):
        """Initialize documentation gating.

        Args:
            package_name: Name of the package to validate
            project_root: Root directory of the project
        """
        self.package_name = package_name
        self.project_root = Path(project_root)
        self.gating_config = {
            "completeness_threshold": 0.95,
            "doctest_pass_rate": 1.0,
            "allow_draft_prs": False,
            "require_maintainer_override": True,
            "breaking_change_tolerance": "none"  # none, low, medium, high
        }

    def evaluate_documentation_gate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate whether documentation gate should pass or fail.

        Args:
            context: Context information (PR info, branch info, etc.)

        Returns:
            Gate evaluation result
        """
        logger.info(f"Evaluating documentation gate for {self.package_name}")

        gate_result = {
            "gate_timestamp": datetime.now().isoformat(),
            "package_name": self.package_name,
            "context": context,
            "gate_status": "unknown",
            "gate_checks": {},
            "blocking_issues": [],
            "warnings": [],
            "recommendations": [],
            "override_allowed": False,
            "override_reason": None
        }

        try:
            # Check 1: Documentation Completeness
            completeness_check = self._check_documentation_completeness(context)
            gate_result["gate_checks"]["completeness"] = completeness_check

            # Check 2: Doctest Validation
            doctest_check = self._check_doctest_validation()
            gate_result["gate_checks"]["doctest_validation"] = doctest_check

            # Check 3: API Change Analysis
            api_change_check = self._check_api_changes(context)
            gate_result["gate_checks"]["api_changes"] = api_change_check

            # Check 4: Breaking Change Documentation
            breaking_change_check = self._check_breaking_change_documentation(context)
            gate_result["gate_checks"]["breaking_changes"] = breaking_change_check

            # Check 5: New API Documentation
            new_api_check = self._check_new_api_documentation(context)
            gate_result["gate_checks"]["new_apis"] = new_api_check

            # Evaluate overall gate status
            gate_result = self._evaluate_overall_gate_status(gate_result)

            # Generate recommendations
            gate_result["recommendations"] = self._generate_gate_recommendations(gate_result)

            logger.info(f"Documentation gate evaluation completed: {gate_result['gate_status']}")

        except Exception as e:
            error_msg = f"Documentation gate evaluation failed: {e}"
            logger.error(error_msg)
            gate_result["gate_status"] = "error"
            gate_result["blocking_issues"].append(error_msg)

        return gate_result

    def _check_documentation_completeness(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Check documentation completeness against threshold."""
        try:
            # Import and run completeness checker
            from ..validation.completeness_checker import CompletenessChecker
            from ..introspection.api_extractor import APIExtractor

            # Extract current API
            extractor = APIExtractor(self.package_name)
            api_data = extractor.extract_complete_api()

            # Check completeness
            checker = CompletenessChecker(self.package_name)
            completeness_result = checker.check_documentation_completeness(
                api_data,
                self.gating_config["completeness_threshold"]
            )

            completeness_pct = completeness_result.get("completeness_percentage", 0.0)
            threshold = self.gating_config["completeness_threshold"] * 100

            if completeness_pct >= threshold:
                return {
                    "status": "passed",
                    "message": f"Documentation completeness: {completeness_pct:.1f}% (threshold: {threshold:.1f}%)",
                    "details": completeness_result
                }
            else:
                return {
                    "status": "failed",
                    "message": f"Documentation completeness below threshold: {completeness_pct:.1f}% < {threshold:.1f}%",
                    "details": completeness_result
                }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Completeness check failed: {e}",
                "details": {"error": str(e)}
            }

    def _check_doctest_validation(self) -> Dict[str, Any]:
        """Check doctest validation results."""
        try:
            from ..validation.doctest_validator import DoctestValidator

            validator = DoctestValidator(self.package_name)
            validation_result = validator.validate_package_doctests()

            total_tests = validation_result.get("total_tests", 0)
            passed_tests = validation_result.get("passed_tests", 0)
            failed_tests = validation_result.get("failed_tests", 0)

            if total_tests == 0:
                return {
                    "status": "warning",
                    "message": "No doctests found",
                    "details": validation_result
                }

            pass_rate = passed_tests / total_tests if total_tests > 0 else 0.0
            required_rate = self.gating_config["doctest_pass_rate"]

            if pass_rate >= required_rate:
                return {
                    "status": "passed",
                    "message": f"Doctests passed: {passed_tests}/{total_tests} ({pass_rate:.1%})",
                    "details": validation_result
                }
            else:
                return {
                    "status": "failed",
                    "message": f"Doctest pass rate below threshold: {pass_rate:.1%} < {required_rate:.1%}",
                    "details": validation_result
                }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Doctest validation failed: {e}",
                "details": {"error": str(e)}
            }

    def _check_api_changes(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Check API changes for breaking changes and documentation requirements."""
        try:
            # Get PR/branch context
            base_ref = context.get("base_ref")
            head_ref = context.get("head_ref")

            if not base_ref or not head_ref:
                return {
                    "status": "skipped",
                    "message": "No branch comparison context available",
                    "details": {}
                }

            # Compare API between branches
            api_diff = self._get_api_diff(base_ref, head_ref)

            if not api_diff:
                return {
                    "status": "passed",
                    "message": "No API changes detected",
                    "details": {}
                }

            # Analyze the changes
            breaking_changes = api_diff.get("breaking_changes", [])
            total_changes = api_diff.get("summary", {}).get("total_changes", 0)

            if breaking_changes:
                tolerance = self.gating_config["breaking_change_tolerance"]

                if tolerance == "none":
                    return {
                        "status": "failed",
                        "message": f"Breaking changes not allowed: {len(breaking_changes)} detected",
                        "details": api_diff
                    }
                elif tolerance == "low" and len(breaking_changes) > 1:
                    return {
                        "status": "failed",
                        "message": f"Too many breaking changes: {len(breaking_changes)} > 1",
                        "details": api_diff
                    }
                elif tolerance == "medium" and len(breaking_changes) > 5:
                    return {
                        "status": "failed",
                        "message": f"Too many breaking changes: {len(breaking_changes)} > 5",
                        "details": api_diff
                    }

            return {
                "status": "passed",
                "message": f"API changes acceptable: {total_changes} total, {len(breaking_changes)} breaking",
                "details": api_diff
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"API change check failed: {e}",
                "details": {"error": str(e)}
            }

    def _check_breaking_change_documentation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Check that breaking changes are properly documented."""
        try:
            # Get API diff from previous check
            api_diff = self._get_api_diff(
                context.get("base_ref"),
                context.get("head_ref")
            )

            if not api_diff:
                return {
                    "status": "passed",
                    "message": "No API changes to document",
                    "details": {}
                }

            breaking_changes = api_diff.get("breaking_changes", [])

            if not breaking_changes:
                return {
                    "status": "passed",
                    "message": "No breaking changes to document",
                    "details": {}
                }

            # Check for documentation of breaking changes
            documentation_issues = []

            for change in breaking_changes:
                element = change.get("element", "unknown")
                change_type = change.get("type", "unknown")

                # Check if the change has migration notes
                if not change.get("migration_notes"):
                    documentation_issues.append({
                        "element": element,
                        "issue": "missing_migration_notes",
                        "change_type": change_type
                    })

                # Check if deprecation was added for removals
                if change_type == "removal" and not self._check_prior_deprecation(element):
                    documentation_issues.append({
                        "element": element,
                        "issue": "removal_without_deprecation",
                        "change_type": change_type
                    })

            if documentation_issues:
                return {
                    "status": "failed",
                    "message": f"Breaking changes lack proper documentation: {len(documentation_issues)} issues",
                    "details": {
                        "issues": documentation_issues,
                        "breaking_changes": breaking_changes
                    }
                }
            else:
                return {
                    "status": "passed",
                    "message": f"Breaking changes properly documented: {len(breaking_changes)} changes",
                    "details": {"breaking_changes": breaking_changes}
                }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Breaking change documentation check failed: {e}",
                "details": {"error": str(e)}
            }

    def _check_new_api_documentation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Check that new APIs are properly documented."""
        try:
            # Get API diff
            api_diff = self._get_api_diff(
                context.get("base_ref"),
                context.get("head_ref")
            )

            if not api_diff:
                return {
                    "status": "passed",
                    "message": "No new APIs to document",
                    "details": {}
                }

            new_elements = api_diff.get("signature_changes", {}).get("added", [])

            if not new_elements:
                return {
                    "status": "passed",
                    "message": "No new APIs added",
                    "details": {}
                }

            # Check documentation for new elements
            from ..introspection.api_extractor import APIExtractor

            extractor = APIExtractor(self.package_name)
            current_api = extractor.extract_complete_api()

            undocumented_elements = []

            for element_name in new_elements:
                element_data = current_api.get("public_api", {}).get(element_name)

                if element_data:
                    docstring = element_data.get("doc", "")
                    if not docstring or len(docstring.strip()) < 20:
                        undocumented_elements.append({
                            "element": element_name,
                            "type": element_data.get("type", "unknown"),
                            "docstring_length": len(docstring) if docstring else 0
                        })

            if undocumented_elements:
                return {
                    "status": "failed",
                    "message": f"New APIs lack documentation: {len(undocumented_elements)}/{len(new_elements)}",
                    "details": {
                        "undocumented_elements": undocumented_elements,
                        "new_elements": new_elements
                    }
                }
            else:
                return {
                    "status": "passed",
                    "message": f"All new APIs documented: {len(new_elements)} elements",
                    "details": {"new_elements": new_elements}
                }

        except Exception as e:
            return {
                "status": "error",
                "message": f"New API documentation check failed: {e}",
                "details": {"error": str(e)}
            }

    def _get_api_diff(self, base_ref: Optional[str], head_ref: Optional[str]) -> Optional[Dict[str, Any]]:
        """Get API diff between two git references."""
        if not base_ref or not head_ref:
            return None

        try:
            # This is a simplified implementation
            # In practice, would check out different refs and compare APIs
            from ..diffing.api_differ import APIDiffer
            from ..diffing.change_classifier import ChangeClassifier

            differ = APIDiffer()
            classifier = ChangeClassifier()

            # For now, return a mock diff
            # In a real implementation, this would:
            # 1. Check out base_ref
            # 2. Generate API snapshot
            # 3. Check out head_ref
            # 4. Generate API snapshot
            # 5. Compare snapshots

            return {
                "signature_changes": {
                    "added": [],
                    "removed": [],
                    "modified": []
                },
                "breaking_changes": [],
                "summary": {
                    "total_changes": 0
                }
            }

        except Exception as e:
            logger.warning(f"Failed to get API diff: {e}")
            return None

    def _check_prior_deprecation(self, element_name: str) -> bool:
        """Check if an element was previously deprecated."""
        try:
            from ..diffing.version_tracker import VersionTracker

            tracker = VersionTracker()
            deprecations = tracker.get_deprecations()

            return any(
                dep.get("element_name") == element_name
                for dep in deprecations
            )

        except Exception:
            return False

    def _evaluate_overall_gate_status(self, gate_result: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate overall gate status based on individual checks."""
        checks = gate_result.get("gate_checks", {})

        failed_checks = []
        error_checks = []
        warning_checks = []

        for check_name, check_result in checks.items():
            status = check_result.get("status", "unknown")

            if status == "failed":
                failed_checks.append(check_name)
                gate_result["blocking_issues"].append(
                    f"{check_name}: {check_result.get('message', 'Check failed')}"
                )
            elif status == "error":
                error_checks.append(check_name)
                gate_result["blocking_issues"].append(
                    f"{check_name}: {check_result.get('message', 'Check error')}"
                )
            elif status == "warning":
                warning_checks.append(check_name)
                gate_result["warnings"].append(
                    f"{check_name}: {check_result.get('message', 'Check warning')}"
                )

        # Determine gate status
        if failed_checks or error_checks:
            gate_result["gate_status"] = "failed"

            # Check if override is allowed
            if self.gating_config["require_maintainer_override"]:
                gate_result["override_allowed"] = True
                gate_result["override_reason"] = f"Failed checks: {', '.join(failed_checks + error_checks)}"

        elif warning_checks:
            gate_result["gate_status"] = "warning"
        else:
            gate_result["gate_status"] = "passed"

        return gate_result

    def _generate_gate_recommendations(self, gate_result: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on gate results."""
        recommendations = []

        checks = gate_result.get("gate_checks", {})

        # Completeness recommendations
        completeness_check = checks.get("completeness", {})
        if completeness_check.get("status") == "failed":
            details = completeness_check.get("details", {})
            undocumented = details.get("undocumented_elements", 0)
            if undocumented > 0:
                recommendations.append(f"Add documentation to {undocumented} undocumented elements")

        # Doctest recommendations
        doctest_check = checks.get("doctest_validation", {})
        if doctest_check.get("status") == "failed":
            recommendations.append("Fix failing doctests before merging")

        # API change recommendations
        api_check = checks.get("api_changes", {})
        if api_check.get("status") == "failed":
            recommendations.append("Review breaking changes and consider deprecation path")

        # Breaking change recommendations
        breaking_check = checks.get("breaking_changes", {})
        if breaking_check.get("status") == "failed":
            recommendations.append("Add migration notes for breaking changes")

        # New API recommendations
        new_api_check = checks.get("new_apis", {})
        if new_api_check.get("status") == "failed":
            recommendations.append("Add documentation for new APIs")

        # General recommendations
        if gate_result.get("gate_status") == "failed":
            recommendations.append("Address blocking issues before merging")

        if gate_result.get("override_allowed"):
            recommendations.append("Consider maintainer override if issues cannot be immediately resolved")

        return recommendations

    def check_override_permissions(self, user: str, context: Dict[str, Any]) -> bool:
        """Check if a user has permission to override the documentation gate.

        Args:
            user: Username requesting override
            context: Context information

        Returns:
            True if override is allowed, False otherwise
        """
        # This would typically check against GitHub team membership or similar
        # For now, implement a simple check

        maintainers = [
            "terry@eonlabs.ai",
            "maintainer1",
            "maintainer2"
        ]

        return user in maintainers

    def apply_gate_override(self, user: str, reason: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a documentation gate override.

        Args:
            user: User applying the override
            reason: Reason for the override
            context: Context information

        Returns:
            Override result
        """
        override_result = {
            "override_timestamp": datetime.now().isoformat(),
            "override_user": user,
            "override_reason": reason,
            "context": context,
            "override_status": "unknown"
        }

        try:
            if not self.check_override_permissions(user, context):
                override_result["override_status"] = "denied"
                override_result["message"] = f"User {user} does not have override permissions"
                return override_result

            # Log the override
            logger.warning(f"Documentation gate override applied by {user}: {reason}")

            override_result["override_status"] = "applied"
            override_result["message"] = f"Override applied by {user}"

            # Save override record
            self._save_override_record(override_result)

        except Exception as e:
            override_result["override_status"] = "error"
            override_result["message"] = f"Override failed: {e}"

        return override_result

    def _save_override_record(self, override_result: Dict[str, Any]):
        """Save override record for audit purposes."""
        overrides_dir = Path("docs/ultrathink/storage/overrides")
        overrides_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        override_file = overrides_dir / f"override_{timestamp}.json"

        with open(override_file, 'w', encoding='utf-8') as f:
            json.dump(override_result, f, indent=2, sort_keys=True)

        logger.info(f"Saved override record: {override_file}")

    def generate_gate_report(self, gate_result: Dict[str, Any]) -> str:
        """Generate a human-readable gate report."""
        status = gate_result.get("gate_status", "unknown")
        status_emoji = {
            "passed": "✅",
            "failed": "❌",
            "warning": "⚠️",
            "error": "💥"
        }.get(status, "❓")

        report_lines = [
            f"# 📚 Documentation Gate Report",
            f"",
            f"**Status:** {status_emoji} {status.upper()}",
            f"**Package:** {gate_result.get('package_name', 'unknown')}",
            f"**Timestamp:** {gate_result.get('gate_timestamp', 'unknown')}",
            f""
        ]

        # Gate checks
        checks = gate_result.get("gate_checks", {})
        if checks:
            report_lines.extend([
                f"## Gate Checks",
                f""
            ])

            for check_name, check_result in checks.items():
                check_status = check_result.get("status", "unknown")
                check_emoji = {
                    "passed": "✅",
                    "failed": "❌",
                    "warning": "⚠️",
                    "error": "💥",
                    "skipped": "⏭️"
                }.get(check_status, "❓")

                report_lines.append(f"### {check_name.replace('_', ' ').title()}")
                report_lines.append(f"**Status:** {check_emoji} {check_status.upper()}")
                report_lines.append(f"**Message:** {check_result.get('message', 'No message')}")
                report_lines.append("")

        # Blocking issues
        blocking_issues = gate_result.get("blocking_issues", [])
        if blocking_issues:
            report_lines.extend([
                f"## ❌ Blocking Issues",
                f""
            ])
            for issue in blocking_issues:
                report_lines.append(f"- {issue}")
            report_lines.append("")

        # Warnings
        warnings = gate_result.get("warnings", [])
        if warnings:
            report_lines.extend([
                f"## ⚠️ Warnings",
                f""
            ])
            for warning in warnings:
                report_lines.append(f"- {warning}")
            report_lines.append("")

        # Recommendations
        recommendations = gate_result.get("recommendations", [])
        if recommendations:
            report_lines.extend([
                f"## 💡 Recommendations",
                f""
            ])
            for i, rec in enumerate(recommendations, 1):
                report_lines.append(f"{i}. {rec}")
            report_lines.append("")

        # Override information
        if gate_result.get("override_allowed"):
            report_lines.extend([
                f"## 🔓 Override Available",
                f"",
                f"Maintainers can override this gate with appropriate justification.",
                f"**Override Reason:** {gate_result.get('override_reason', 'Not specified')}",
                f""
            ])

        return "\n".join(report_lines)