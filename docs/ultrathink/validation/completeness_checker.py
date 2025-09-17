"""Documentation completeness checking for ultrathink documentation system."""

from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
import logging
import re
import json

logger = logging.getLogger(__name__)


class CompletenessChecker:
    """Checks documentation completeness and coverage."""

    def __init__(self, package_name: str, storage_directory: str = "docs/ultrathink/storage"):
        """Initialize the completeness checker.

        Args:
            package_name: Name of the package to check
            storage_directory: Directory containing documentation artifacts
        """
        self.package_name = package_name
        self.storage_dir = Path(storage_directory)
        self.generated_docs_dir = self.storage_dir / "generated_docs"

    def check_documentation_completeness(self, api_data: Dict[str, Any], completeness_threshold: float = 0.95) -> Dict[str, Any]:
        """Check completeness of documentation for all API elements.

        Args:
            api_data: API data from APIExtractor
            completeness_threshold: Minimum completeness percentage required

        Returns:
            Completeness check results
        """
        logger.info(f"Checking documentation completeness for package {self.package_name}")

        completeness_result = {
            "package_name": self.package_name,
            "check_timestamp": datetime.now().isoformat(),
            "completeness_threshold": completeness_threshold,
            "total_elements": 0,
            "documented_elements": 0,
            "undocumented_elements": 0,
            "partially_documented_elements": 0,
            "completeness_percentage": 0.0,
            "element_completeness": {},
            "missing_documentation": {},
            "documentation_quality": {},
            "summary": {},
            "recommendations": []
        }

        try:
            public_api = api_data.get("public_api", {})
            completeness_result["total_elements"] = len(public_api)

            for element_name, element_data in public_api.items():
                # Check completeness for each element
                element_completeness = self._check_element_completeness(element_name, element_data)
                completeness_result["element_completeness"][element_name] = element_completeness

                # Categorize elements
                if element_completeness["completeness_score"] >= completeness_threshold:
                    completeness_result["documented_elements"] += 1
                elif element_completeness["completeness_score"] > 0:
                    completeness_result["partially_documented_elements"] += 1
                else:
                    completeness_result["undocumented_elements"] += 1

                # Track missing documentation
                missing_items = element_completeness.get("missing_items", [])
                if missing_items:
                    completeness_result["missing_documentation"][element_name] = missing_items

                # Track documentation quality issues
                quality_issues = element_completeness.get("quality_issues", [])
                if quality_issues:
                    completeness_result["documentation_quality"][element_name] = quality_issues

            # Calculate overall completeness
            total_elements = completeness_result["total_elements"]
            if total_elements > 0:
                completeness_result["completeness_percentage"] = (
                    completeness_result["documented_elements"] / total_elements * 100
                )

            # Generate summary
            completeness_result["summary"] = self._generate_completeness_summary(completeness_result)

            # Generate recommendations
            completeness_result["recommendations"] = self._generate_completeness_recommendations(completeness_result)

            # Save results
            self._save_completeness_results(completeness_result)

            logger.info(f"Documentation completeness: {completeness_result['completeness_percentage']:.1f}%")

        except Exception as e:
            error_msg = f"Completeness check failed: {e}"
            logger.error(error_msg)
            completeness_result["error"] = error_msg

        return completeness_result

    def _check_element_completeness(self, element_name: str, element_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check completeness for a single API element."""
        element_type = element_data.get("type", "unknown")

        completeness = {
            "element_name": element_name,
            "element_type": element_type,
            "has_docstring": False,
            "has_signature": False,
            "has_stub_file": False,
            "has_examples": False,
            "has_type_hints": False,
            "docstring_quality": {},
            "completeness_score": 0.0,
            "missing_items": [],
            "quality_issues": []
        }

        # Check basic documentation presence
        docstring = element_data.get("doc", "")
        if docstring and docstring.strip():
            completeness["has_docstring"] = True
            completeness["docstring_quality"] = self._analyze_docstring_quality(docstring)
        else:
            completeness["missing_items"].append("docstring")

        # Check signature
        signature = element_data.get("signature", "")
        if signature:
            completeness["has_signature"] = True
        else:
            completeness["missing_items"].append("signature")

        # Check for generated stub file
        stub_file_exists = self._check_stub_file_exists(element_name, element_type)
        completeness["has_stub_file"] = stub_file_exists
        if not stub_file_exists:
            completeness["missing_items"].append("stub_file")

        # Check for examples in docstring or stub
        has_examples = self._check_for_examples(element_name, element_type, docstring)
        completeness["has_examples"] = has_examples
        if not has_examples:
            completeness["missing_items"].append("examples")

        # Check type hints
        has_type_hints = self._check_type_hints(element_data)
        completeness["has_type_hints"] = has_type_hints
        if not has_type_hints:
            completeness["missing_items"].append("type_hints")

        # Element-specific checks
        if element_type == "class":
            completeness = self._check_class_completeness(element_data, completeness)
        elif element_type in ("function", "method"):
            completeness = self._check_function_completeness(element_data, completeness)

        # Calculate completeness score
        completeness["completeness_score"] = self._calculate_completeness_score(completeness)

        return completeness

    def _analyze_docstring_quality(self, docstring: str) -> Dict[str, Any]:
        """Analyze the quality of a docstring."""
        quality = {
            "length": len(docstring),
            "line_count": len(docstring.splitlines()),
            "has_summary": False,
            "has_description": False,
            "has_parameters": False,
            "has_returns": False,
            "has_examples": False,
            "has_raises": False,
            "quality_score": 0.0,
            "issues": []
        }

        lines = docstring.strip().splitlines()
        if not lines:
            quality["issues"].append("empty_docstring")
            return quality

        # Check for summary (first line)
        first_line = lines[0].strip()
        if first_line and not first_line.endswith("TODO"):
            quality["has_summary"] = True
        else:
            quality["issues"].append("missing_or_poor_summary")

        # Check for description (more than just summary)
        if len(lines) > 2:
            quality["has_description"] = True

        # Check for common docstring sections
        docstring_lower = docstring.lower()

        if any(section in docstring_lower for section in ["args:", "arguments:", "parameters:"]):
            quality["has_parameters"] = True

        if any(section in docstring_lower for section in ["returns:", "return:"]):
            quality["has_returns"] = True

        if any(section in docstring_lower for section in ["examples:", "example:"]):
            quality["has_examples"] = True

        if any(section in docstring_lower for section in ["raises:", "except:"]):
            quality["has_raises"] = True

        # Check for quality issues
        if "TODO" in docstring:
            quality["issues"].append("contains_todo")

        if len(first_line) > 100:
            quality["issues"].append("summary_too_long")

        if quality["length"] < 20:
            quality["issues"].append("docstring_too_short")

        # Calculate quality score
        quality_factors = [
            quality["has_summary"],
            quality["has_description"],
            quality["has_parameters"],
            quality["has_returns"],
            quality["has_examples"]
        ]

        quality["quality_score"] = sum(quality_factors) / len(quality_factors)

        return quality

    def _check_stub_file_exists(self, element_name: str, element_type: str) -> bool:
        """Check if a stub file exists for the element."""
        if not self.generated_docs_dir.exists():
            return False

        api_ref_dir = self.generated_docs_dir / "api_reference"
        if not api_ref_dir.exists():
            return False

        # Normalize element name for file system
        safe_name = re.sub(r'[^\w\-_.]', '_', element_name)
        stub_filename = f"{safe_name}_{element_type}.md"
        stub_file = api_ref_dir / stub_filename

        return stub_file.exists()

    def _check_for_examples(self, element_name: str, element_type: str, docstring: str) -> bool:
        """Check if examples exist for the element."""
        # Check in docstring
        if "example" in docstring.lower() or ">>>" in docstring:
            return True

        # Check in stub file
        if self._check_stub_file_exists(element_name, element_type):
            api_ref_dir = self.generated_docs_dir / "api_reference"
            safe_name = re.sub(r'[^\w\-_.]', '_', element_name)
            stub_filename = f"{safe_name}_{element_type}.md"
            stub_file = api_ref_dir / stub_filename

            try:
                with open(stub_file, 'r', encoding='utf-8') as f:
                    stub_content = f.read()

                if "example" in stub_content.lower() or "```python" in stub_content:
                    return True
            except Exception:
                pass

        return False

    def _check_type_hints(self, element_data: Dict[str, Any]) -> bool:
        """Check if type hints are present."""
        element_type = element_data.get("type", "")

        if element_type in ("function", "method"):
            # Check function parameters and return type
            parameters = element_data.get("parameters", {})
            for param_data in parameters.values():
                if param_data.get("annotation"):
                    return True

            if element_data.get("return_annotation"):
                return True

        elif element_type == "class":
            # Check class methods for type hints
            methods = element_data.get("methods", {})
            for method_data in methods.values():
                if method_data.get("signature") and ":" in method_data.get("signature", ""):
                    return True

        return False

    def _check_class_completeness(self, element_data: Dict[str, Any], completeness: Dict[str, Any]) -> Dict[str, Any]:
        """Additional completeness checks for classes."""
        methods = element_data.get("methods", {})
        properties = element_data.get("properties", {})

        # Check if public methods are documented
        undocumented_methods = []
        for method_name, method_data in methods.items():
            if not method_name.startswith("_"):  # Public method
                method_doc = method_data.get("docstring", "")
                if not method_doc or not method_doc.strip():
                    undocumented_methods.append(method_name)

        if undocumented_methods:
            completeness["missing_items"].append(f"method_documentation: {', '.join(undocumented_methods)}")

        # Check if class has __init__ documentation
        if "__init__" in methods:
            init_doc = methods["__init__"].get("docstring", "")
            if not init_doc or not init_doc.strip():
                completeness["missing_items"].append("__init___documentation")

        # Check if properties are documented
        undocumented_properties = []
        for prop_name, prop_data in properties.items():
            prop_doc = prop_data.get("docstring", "")
            if not prop_doc or not prop_doc.strip():
                undocumented_properties.append(prop_name)

        if undocumented_properties:
            completeness["missing_items"].append(f"property_documentation: {', '.join(undocumented_properties)}")

        return completeness

    def _check_function_completeness(self, element_data: Dict[str, Any], completeness: Dict[str, Any]) -> Dict[str, Any]:
        """Additional completeness checks for functions."""
        parameters = element_data.get("parameters", {})
        docstring = element_data.get("doc", "")

        # Check if parameters are documented in docstring
        if parameters:
            param_names = set(parameters.keys())
            # Remove 'self' and 'cls' from consideration
            param_names.discard("self")
            param_names.discard("cls")

            if param_names:
                # Simple check - does docstring mention parameter documentation?
                if not any(section in docstring.lower() for section in ["args:", "arguments:", "parameters:"]):
                    completeness["missing_items"].append("parameter_documentation")

        # Check if return value is documented
        return_annotation = element_data.get("return_annotation")
        if return_annotation and return_annotation not in ("None", "-> None"):
            if not any(section in docstring.lower() for section in ["returns:", "return:"]):
                completeness["missing_items"].append("return_documentation")

        return completeness

    def _calculate_completeness_score(self, completeness: Dict[str, Any]) -> float:
        """Calculate a completeness score for an element."""
        weights = {
            "has_docstring": 0.3,
            "has_signature": 0.1,
            "has_stub_file": 0.2,
            "has_examples": 0.2,
            "has_type_hints": 0.2
        }

        score = 0.0
        for criterion, weight in weights.items():
            if completeness.get(criterion, False):
                score += weight

        # Bonus for docstring quality
        docstring_quality = completeness.get("docstring_quality", {})
        quality_score = docstring_quality.get("quality_score", 0.0)
        score += quality_score * 0.1  # Up to 10% bonus for quality

        # Penalty for quality issues
        quality_issues = completeness.get("quality_issues", [])
        penalty = min(len(quality_issues) * 0.05, 0.2)  # Up to 20% penalty
        score = max(0.0, score - penalty)

        return min(1.0, score)

    def _generate_completeness_summary(self, completeness_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of completeness results."""
        total = completeness_result["total_elements"]
        documented = completeness_result["documented_elements"]
        partially_documented = completeness_result["partially_documented_elements"]
        undocumented = completeness_result["undocumented_elements"]

        return {
            "overall_completeness": completeness_result["completeness_percentage"],
            "meets_threshold": completeness_result["completeness_percentage"] >= completeness_result["completeness_threshold"] * 100,
            "documentation_distribution": {
                "fully_documented": documented,
                "partially_documented": partially_documented,
                "undocumented": undocumented,
                "fully_documented_percentage": (documented / total * 100) if total > 0 else 0,
                "partially_documented_percentage": (partially_documented / total * 100) if total > 0 else 0,
                "undocumented_percentage": (undocumented / total * 100) if total > 0 else 0
            },
            "most_common_missing_items": self._analyze_missing_items(completeness_result),
            "quality_issues_summary": self._analyze_quality_issues(completeness_result)
        }

    def _analyze_missing_items(self, completeness_result: Dict[str, Any]) -> Dict[str, int]:
        """Analyze the most common missing documentation items."""
        missing_counts = {}

        for element_name, missing_items in completeness_result.get("missing_documentation", {}).items():
            for item in missing_items:
                # Extract the base item type (before any colon)
                base_item = item.split(":")[0]
                missing_counts[base_item] = missing_counts.get(base_item, 0) + 1

        # Sort by frequency
        return dict(sorted(missing_counts.items(), key=lambda x: x[1], reverse=True))

    def _analyze_quality_issues(self, completeness_result: Dict[str, Any]) -> Dict[str, int]:
        """Analyze the most common quality issues."""
        issue_counts = {}

        for element_name, quality_issues in completeness_result.get("documentation_quality", {}).items():
            for issue in quality_issues:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1

        return dict(sorted(issue_counts.items(), key=lambda x: x[1], reverse=True))

    def _generate_completeness_recommendations(self, completeness_result: Dict[str, Any]) -> List[str]:
        """Generate recommendations for improving documentation completeness."""
        recommendations = []

        completeness_pct = completeness_result["completeness_percentage"]
        threshold = completeness_result["completeness_threshold"] * 100

        if completeness_pct < threshold:
            recommendations.append(f"Increase documentation completeness from {completeness_pct:.1f}% to at least {threshold:.1f}%")

        # Specific recommendations based on missing items
        missing_items = self._analyze_missing_items(completeness_result)

        if missing_items.get("docstring", 0) > 0:
            recommendations.append(f"Add docstrings to {missing_items['docstring']} elements")

        if missing_items.get("examples", 0) > 0:
            recommendations.append(f"Add examples to {missing_items['examples']} elements")

        if missing_items.get("type_hints", 0) > 0:
            recommendations.append(f"Add type hints to {missing_items['type_hints']} elements")

        if missing_items.get("stub_file", 0) > 0:
            recommendations.append(f"Generate stub files for {missing_items['stub_file']} elements")

        # Quality-based recommendations
        quality_issues = self._analyze_quality_issues(completeness_result)

        if quality_issues.get("contains_todo", 0) > 0:
            recommendations.append(f"Complete TODO items in {quality_issues['contains_todo']} docstrings")

        if quality_issues.get("missing_or_poor_summary", 0) > 0:
            recommendations.append(f"Improve summary lines in {quality_issues['missing_or_poor_summary']} docstrings")

        undocumented = completeness_result["undocumented_elements"]
        if undocumented > 0:
            recommendations.append(f"Prioritize documenting {undocumented} completely undocumented elements")

        return recommendations

    def _save_completeness_results(self, completeness_result: Dict[str, Any]):
        """Save completeness results to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"completeness_check_{timestamp}.json"
        file_path = self.storage_dir / "validation_cache" / filename

        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(completeness_result, f, indent=2, sort_keys=True)

        logger.info(f"Saved completeness results to {file_path}")

    def generate_completeness_report(self, completeness_result: Dict[str, Any]) -> str:
        """Generate a human-readable completeness report."""
        summary = completeness_result.get("summary", {})
        distribution = summary.get("documentation_distribution", {})

        report_lines = [
            f"# Documentation Completeness Report",
            f"",
            f"**Package:** {completeness_result['package_name']}",
            f"**Check Time:** {completeness_result['check_timestamp']}",
            f"**Threshold:** {completeness_result['completeness_threshold'] * 100:.1f}%",
            f"",
            f"## Overall Results",
            f"",
            f"- **Completeness:** {completeness_result['completeness_percentage']:.1f}%",
            f"- **Status:** {'✅ PASSED' if summary.get('meets_threshold', False) else '❌ FAILED'}",
            f"- **Total Elements:** {completeness_result['total_elements']}",
            f"",
            f"## Documentation Distribution",
            f"",
            f"- **Fully Documented:** {distribution.get('fully_documented', 0)} ({distribution.get('fully_documented_percentage', 0):.1f}%)",
            f"- **Partially Documented:** {distribution.get('partially_documented', 0)} ({distribution.get('partially_documented_percentage', 0):.1f}%)",
            f"- **Undocumented:** {distribution.get('undocumented', 0)} ({distribution.get('undocumented_percentage', 0):.1f}%)",
            f""
        ]

        # Missing items analysis
        missing_items = summary.get("most_common_missing_items", {})
        if missing_items:
            report_lines.extend([
                f"## Most Common Missing Items",
                f""
            ])
            for item, count in list(missing_items.items())[:5]:  # Top 5
                report_lines.append(f"- **{item.replace('_', ' ').title()}:** {count} elements")
            report_lines.append("")

        # Quality issues
        quality_issues = summary.get("quality_issues_summary", {})
        if quality_issues:
            report_lines.extend([
                f"## Quality Issues",
                f""
            ])
            for issue, count in list(quality_issues.items())[:5]:  # Top 5
                report_lines.append(f"- **{issue.replace('_', ' ').title()}:** {count} elements")
            report_lines.append("")

        # Recommendations
        recommendations = completeness_result.get("recommendations", [])
        if recommendations:
            report_lines.extend([
                f"## Recommendations",
                f""
            ])
            for i, rec in enumerate(recommendations, 1):
                report_lines.append(f"{i}. {rec}")
            report_lines.append("")

        # Detailed breakdown for worst offenders
        undocumented_elements = [
            name for name, completeness in completeness_result.get("element_completeness", {}).items()
            if completeness.get("completeness_score", 1.0) == 0.0
        ]

        if undocumented_elements:
            report_lines.extend([
                f"## Undocumented Elements",
                f""
            ])
            for element in sorted(undocumented_elements)[:10]:  # Show first 10
                report_lines.append(f"- {element}")

            if len(undocumented_elements) > 10:
                report_lines.append(f"- ... and {len(undocumented_elements) - 10} more")

        return "\n".join(report_lines)