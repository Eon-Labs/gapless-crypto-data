"""Automated documentation builder for ultrathink documentation system."""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from ..introspection.package_analyzer import PackageAnalyzer
from ..introspection.api_extractor import APIExtractor
from ..diffing.api_differ import APIDiffer
from ..diffing.change_classifier import ChangeClassifier
from .stub_generator import StubGenerator

logger = logging.getLogger(__name__)


class AutodocBuilder:
    """Builds comprehensive documentation automatically."""

    def __init__(self, package_name: str, source_directory: str, storage_directory: str = "docs/ultrathink/storage"):
        """Initialize the autodoc builder.

        Args:
            package_name: Name of the package to document
            source_directory: Path to the source directory
            storage_directory: Directory for storing documentation artifacts
        """
        self.package_name = package_name
        self.source_directory = source_directory
        self.storage_dir = Path(storage_directory)

        # Initialize components
        self.analyzer = PackageAnalyzer(package_name, source_directory)
        self.extractor = APIExtractor(package_name)
        self.differ = APIDiffer(storage_directory)
        self.classifier = ChangeClassifier()
        self.stub_generator = StubGenerator(
            config_dir="docs/ultrathink/config",
            output_dir=str(self.storage_dir / "generated_docs")
        )

        # Ensure storage directory exists
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def build_complete_documentation(self, version: str, compare_with: Optional[str] = None) -> Dict[str, Any]:
        """Build complete documentation for a version.

        Args:
            version: Version to build documentation for
            compare_with: Optional previous version to compare against

        Returns:
            Dictionary containing build results and metadata
        """
        logger.info(f"Starting complete documentation build for version {version}")
        build_start = datetime.now()

        build_result = {
            "version": version,
            "build_timestamp": build_start.isoformat(),
            "package_name": self.package_name,
            "build_stages": {},
            "generated_files": {},
            "errors": [],
            "warnings": []
        }

        try:
            # Stage 1: Package Analysis
            logger.info("Stage 1: Analyzing package structure...")
            analysis_result = self.analyzer.analyze_package()
            build_result["build_stages"]["analysis"] = {
                "status": "completed",
                "timestamp": datetime.now().isoformat(),
                "details": {
                    "total_modules": len(analysis_result.get("module_tree", {})),
                    "public_api_elements": len(analysis_result.get("public_api", {})),
                    "total_files": analysis_result.get("file_structure", {}).get("python_files", 0)
                }
            }

            # Stage 2: API Extraction
            logger.info("Stage 2: Extracting detailed API information...")
            api_data = self.extractor.extract_complete_api()
            build_result["build_stages"]["api_extraction"] = {
                "status": "completed",
                "timestamp": datetime.now().isoformat(),
                "details": {
                    "extracted_elements": len(api_data.get("public_api", {})),
                    "signatures_extracted": len(api_data.get("signatures", {})),
                    "type_hints_extracted": len(api_data.get("type_hints", {}))
                }
            }

            # Stage 3: Create API Snapshot
            logger.info("Stage 3: Creating API snapshot...")
            snapshot_file = self.differ.create_api_snapshot(api_data, version)
            build_result["build_stages"]["snapshot"] = {
                "status": "completed",
                "timestamp": datetime.now().isoformat(),
                "details": {
                    "snapshot_file": snapshot_file
                }
            }
            build_result["generated_files"]["api_snapshot"] = snapshot_file

            # Stage 4: Change Detection (if comparing)
            if compare_with:
                logger.info(f"Stage 4: Comparing with version {compare_with}...")
                try:
                    diff_result = self.differ.compare_versions(compare_with, version)
                    classified_diff = self.classifier.classify_changes(diff_result)

                    build_result["build_stages"]["change_detection"] = {
                        "status": "completed",
                        "timestamp": datetime.now().isoformat(),
                        "details": {
                            "compared_with": compare_with,
                            "total_changes": classified_diff.get("summary", {}).get("total_changes", 0),
                            "breaking_changes": len(classified_diff.get("breaking_changes", [])),
                            "additions": len(classified_diff.get("signature_changes", {}).get("added", [])),
                            "removals": len(classified_diff.get("signature_changes", {}).get("removed", [])),
                            "modifications": len(classified_diff.get("signature_changes", {}).get("modified", []))
                        }
                    }

                    # Generate stubs only for new elements
                    new_elements = classified_diff.get("signature_changes", {}).get("added", [])
                    if new_elements:
                        logger.info(f"Stage 5: Generating stubs for {len(new_elements)} new elements...")
                        generated_stubs = self.stub_generator.generate_stubs_for_new_elements(new_elements, api_data)
                        build_result["generated_files"]["new_stubs"] = generated_stubs
                        build_result["build_stages"]["stub_generation"] = {
                            "status": "completed",
                            "timestamp": datetime.now().isoformat(),
                            "details": {
                                "new_elements": len(new_elements),
                                "stubs_generated": len(generated_stubs)
                            }
                        }
                    else:
                        build_result["build_stages"]["stub_generation"] = {
                            "status": "skipped",
                            "reason": "No new elements to generate stubs for"
                        }

                    # Save comparison results
                    comparison_file = self._save_comparison_results(version, compare_with, classified_diff)
                    build_result["generated_files"]["comparison_results"] = comparison_file

                except Exception as e:
                    error_msg = f"Change detection failed: {e}"
                    logger.error(error_msg)
                    build_result["errors"].append(error_msg)
                    build_result["build_stages"]["change_detection"] = {
                        "status": "failed",
                        "error": error_msg
                    }

            else:
                # No comparison - generate stubs for all elements
                logger.info("Stage 4: Generating stubs for all API elements...")
                generated_stubs = self.stub_generator.regenerate_all_stubs(api_data, force=False)
                build_result["generated_files"]["all_stubs"] = generated_stubs
                build_result["build_stages"]["stub_generation"] = {
                    "status": "completed",
                    "timestamp": datetime.now().isoformat(),
                    "details": {
                        "total_elements": len(api_data.get("public_api", {})),
                        "stubs_generated": len(generated_stubs)
                    }
                }

            # Stage 6: Generate Summary Documentation
            logger.info("Stage 6: Generating summary documentation...")
            summary_files = self._generate_summary_documentation(version, analysis_result, api_data, build_result)
            build_result["generated_files"]["summary_docs"] = summary_files
            build_result["build_stages"]["summary_generation"] = {
                "status": "completed",
                "timestamp": datetime.now().isoformat(),
                "details": {
                    "summary_files": len(summary_files)
                }
            }

            # Stage 7: Generate Index Files
            logger.info("Stage 7: Generating index and navigation files...")
            index_files = self._generate_index_files(api_data, build_result)
            build_result["generated_files"]["index_files"] = index_files
            build_result["build_stages"]["index_generation"] = {
                "status": "completed",
                "timestamp": datetime.now().isoformat(),
                "details": {
                    "index_files": len(index_files)
                }
            }

            # Calculate build duration
            build_end = datetime.now()
            build_result["build_duration_seconds"] = (build_end - build_start).total_seconds()
            build_result["build_status"] = "completed"

            logger.info(f"Documentation build completed successfully in {build_result['build_duration_seconds']:.2f} seconds")

        except Exception as e:
            error_msg = f"Documentation build failed: {e}"
            logger.error(error_msg)
            build_result["errors"].append(error_msg)
            build_result["build_status"] = "failed"
            build_result["build_duration_seconds"] = (datetime.now() - build_start).total_seconds()

        # Save build results
        build_results_file = self._save_build_results(version, build_result)
        build_result["build_results_file"] = build_results_file

        return build_result

    def _save_comparison_results(self, version: str, compare_with: str, classified_diff: Dict[str, Any]) -> str:
        """Save comparison results to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"comparison_{compare_with}_to_{version}_{timestamp}.json"
        file_path = self.storage_dir / "comparisons" / filename

        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(classified_diff, f, indent=2, sort_keys=True)

        logger.info(f"Saved comparison results to {file_path}")
        return str(file_path)

    def _generate_summary_documentation(self, version: str, analysis_result: Dict[str, Any], api_data: Dict[str, Any], build_result: Dict[str, Any]) -> Dict[str, str]:
        """Generate summary documentation files."""
        summary_files = {}
        summary_dir = self.storage_dir / "generated_docs" / "summaries"
        summary_dir.mkdir(parents=True, exist_ok=True)

        # Package Overview
        overview_content = self._generate_package_overview(version, analysis_result, api_data)
        overview_file = summary_dir / f"package_overview_{version}.md"
        with open(overview_file, 'w', encoding='utf-8') as f:
            f.write(overview_content)
        summary_files["package_overview"] = str(overview_file)

        # API Summary
        api_summary_content = self._generate_api_summary(version, api_data)
        api_summary_file = summary_dir / f"api_summary_{version}.md"
        with open(api_summary_file, 'w', encoding='utf-8') as f:
            f.write(api_summary_content)
        summary_files["api_summary"] = str(api_summary_file)

        # Build Report
        build_report_content = self._generate_build_report(build_result)
        build_report_file = summary_dir / f"build_report_{version}.md"
        with open(build_report_file, 'w', encoding='utf-8') as f:
            f.write(build_report_content)
        summary_files["build_report"] = str(build_report_file)

        return summary_files

    def _generate_package_overview(self, version: str, analysis_result: Dict[str, Any], api_data: Dict[str, Any]) -> str:
        """Generate package overview documentation."""
        package_info = analysis_result.get("package_info", {})
        file_structure = analysis_result.get("file_structure", {})
        dependencies = analysis_result.get("dependencies", {})

        return f"""# {self.package_name} - Package Overview

**Version:** {version}
**Generated:** {datetime.now().isoformat()}

## Package Information

- **Name:** {package_info.get('name', 'unknown')}
- **Version:** {package_info.get('version', 'unknown')}
- **Author:** {package_info.get('author', 'unknown')}
- **Location:** {package_info.get('package_dir', 'unknown')}

## Package Structure

- **Total Files:** {file_structure.get('total_files', 0)}
- **Python Files:** {file_structure.get('python_files', 0)}
- **Directories:** {file_structure.get('directories', 0)}
- **Total Lines of Code:** {analysis_result.get('metadata', {}).get('total_lines_of_code', 0)}

## Public API Summary

- **Total API Elements:** {len(api_data.get('public_api', {}))}
- **Classes:** {len([e for e in api_data.get('public_api', {}).values() if e.get('type') == 'class'])}
- **Functions:** {len([e for e in api_data.get('public_api', {}).values() if e.get('type') == 'function'])}
- **Modules:** {len([e for e in api_data.get('public_api', {}).values() if e.get('type') == 'module'])}

## Dependencies

### Standard Library
{chr(10).join(f"- {dep}" for dep in dependencies.get('standard_library', [])[:10])}
{f"... and {len(dependencies.get('standard_library', [])) - 10} more" if len(dependencies.get('standard_library', [])) > 10 else ""}

### Third Party
{chr(10).join(f"- {dep}" for dep in dependencies.get('third_party', [])[:10])}
{f"... and {len(dependencies.get('third_party', [])) - 10} more" if len(dependencies.get('third_party', [])) > 10 else ""}

### Internal
{chr(10).join(f"- {dep}" for dep in dependencies.get('internal', [])[:10])}
{f"... and {len(dependencies.get('internal', [])) - 10} more" if len(dependencies.get('internal', [])) > 10 else ""}

## Package Description

{package_info.get('docstring', 'No package description available.')}

---
*Generated by Ultrathink Documentation System*
"""

    def _generate_api_summary(self, version: str, api_data: Dict[str, Any]) -> str:
        """Generate API summary documentation."""
        public_api = api_data.get("public_api", {})

        # Organize by type
        by_type = {}
        for name, data in public_api.items():
            element_type = data.get("type", "unknown")
            if element_type not in by_type:
                by_type[element_type] = []
            by_type[element_type].append((name, data))

        content = [f"# {self.package_name} - API Reference"]
        content.append(f"**Version:** {version}")
        content.append(f"**Generated:** {datetime.now().isoformat()}")
        content.append("")

        for element_type, elements in sorted(by_type.items()):
            content.append(f"## {element_type.title()}s")
            content.append("")

            for name, data in sorted(elements):
                content.append(f"### {name}")
                content.append("")

                # Add signature if available
                signature = data.get("signature", "")
                if signature:
                    content.append(f"```python")
                    content.append(f"{name}{signature}")
                    content.append(f"```")
                    content.append("")

                # Add description
                doc = data.get("doc", "")
                if doc:
                    # Get first line as summary
                    summary = doc.split("\n")[0].strip()
                    content.append(summary)
                else:
                    content.append("*No description available*")

                content.append("")

                # Add module info
                module = data.get("module", "")
                if module:
                    content.append(f"**Module:** `{module}`")
                    content.append("")

        content.append("---")
        content.append("*Generated by Ultrathink Documentation System*")

        return "\n".join(content)

    def _generate_build_report(self, build_result: Dict[str, Any]) -> str:
        """Generate build report documentation."""
        content = [f"# Documentation Build Report"]
        content.append(f"**Version:** {build_result.get('version', 'unknown')}")
        content.append(f"**Build Time:** {build_result.get('build_timestamp', 'unknown')}")
        content.append(f"**Duration:** {build_result.get('build_duration_seconds', 0):.2f} seconds")
        content.append(f"**Status:** {build_result.get('build_status', 'unknown')}")
        content.append("")

        # Build stages
        content.append("## Build Stages")
        content.append("")

        for stage_name, stage_data in build_result.get("build_stages", {}).items():
            status = stage_data.get("status", "unknown")
            content.append(f"### {stage_name.replace('_', ' ').title()}")
            content.append(f"**Status:** {status}")

            if status == "completed":
                details = stage_data.get("details", {})
                for key, value in details.items():
                    content.append(f"- **{key.replace('_', ' ').title()}:** {value}")
            elif status == "failed":
                error = stage_data.get("error", "Unknown error")
                content.append(f"**Error:** {error}")
            elif status == "skipped":
                reason = stage_data.get("reason", "Unknown reason")
                content.append(f"**Reason:** {reason}")

            content.append("")

        # Generated files
        content.append("## Generated Files")
        content.append("")

        for file_type, files in build_result.get("generated_files", {}).items():
            content.append(f"### {file_type.replace('_', ' ').title()}")

            if isinstance(files, dict):
                for name, path in files.items():
                    content.append(f"- **{name}:** `{path}`")
            elif isinstance(files, str):
                content.append(f"- `{files}`")

            content.append("")

        # Errors and warnings
        errors = build_result.get("errors", [])
        warnings = build_result.get("warnings", [])

        if errors:
            content.append("## Errors")
            content.append("")
            for error in errors:
                content.append(f"- {error}")
            content.append("")

        if warnings:
            content.append("## Warnings")
            content.append("")
            for warning in warnings:
                content.append(f"- {warning}")
            content.append("")

        content.append("---")
        content.append("*Generated by Ultrathink Documentation System*")

        return "\n".join(content)

    def _generate_index_files(self, api_data: Dict[str, Any], build_result: Dict[str, Any]) -> Dict[str, str]:
        """Generate index and navigation files."""
        index_files = {}
        docs_dir = self.storage_dir / "generated_docs"

        # Main API index
        api_index_content = self._generate_api_index(api_data)
        api_index_file = docs_dir / "api" / "index.md"
        api_index_file.parent.mkdir(parents=True, exist_ok=True)
        with open(api_index_file, 'w', encoding='utf-8') as f:
            f.write(api_index_content)
        index_files["api_index"] = str(api_index_file)

        # Documentation index
        docs_index_content = self._generate_docs_index(build_result)
        docs_index_file = docs_dir / "index.md"
        with open(docs_index_file, 'w', encoding='utf-8') as f:
            f.write(docs_index_content)
        index_files["docs_index"] = str(docs_index_file)

        return index_files

    def _generate_api_index(self, api_data: Dict[str, Any]) -> str:
        """Generate API index file."""
        public_api = api_data.get("public_api", {})

        content = [f"# {self.package_name} API Reference"]
        content.append("")
        content.append("## Available API Elements")
        content.append("")

        # Group by type
        by_type = {}
        for name, data in public_api.items():
            element_type = data.get("type", "unknown")
            if element_type not in by_type:
                by_type[element_type] = []
            by_type[element_type].append(name)

        for element_type, elements in sorted(by_type.items()):
            content.append(f"### {element_type.title()}s")
            content.append("")
            for element in sorted(elements):
                # Create link to stub file
                safe_name = element.replace(".", "_").replace(" ", "_")
                stub_link = f"api_reference/{safe_name}_{element_type}.md"
                content.append(f"- [{element}]({stub_link})")
            content.append("")

        return "\n".join(content)

    def _generate_docs_index(self, build_result: Dict[str, Any]) -> str:
        """Generate main documentation index."""
        version = build_result.get("version", "unknown")

        content = [f"# {self.package_name} Documentation"]
        content.append(f"**Version:** {version}")
        content.append("")

        content.append("## Documentation Sections")
        content.append("")
        content.append("- [API Reference](api/index.md)")
        content.append("- [Package Overview](summaries/package_overview_{}.md)".format(version))
        content.append("- [API Summary](summaries/api_summary_{}.md)".format(version))
        content.append("- [Build Report](summaries/build_report_{}.md)".format(version))
        content.append("")

        content.append("## Quick Links")
        content.append("")

        # Add links to major API elements
        generated_files = build_result.get("generated_files", {})
        stubs = generated_files.get("all_stubs", {}) or generated_files.get("new_stubs", {})

        if stubs:
            content.append("### Recently Generated Documentation")
            for element_name, file_path in list(stubs.items())[:10]:  # Show first 10
                rel_path = Path(file_path).relative_to(self.storage_dir / "generated_docs")
                content.append(f"- [{element_name}]({rel_path})")
            content.append("")

        return "\n".join(content)

    def _save_build_results(self, version: str, build_result: Dict[str, Any]) -> str:
        """Save build results to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"build_results_{version}_{timestamp}.json"
        file_path = self.storage_dir / "build_results" / filename

        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(build_result, f, indent=2, sort_keys=True)

        logger.info(f"Saved build results to {file_path}")
        return str(file_path)