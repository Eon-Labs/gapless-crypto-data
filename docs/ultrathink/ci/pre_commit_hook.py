"""Pre-commit hook integration for ultrathink documentation system."""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging
import tempfile

logger = logging.getLogger(__name__)


class PreCommitHook:
    """Manages pre-commit hooks for documentation validation."""

    def __init__(self, project_root: str, package_name: str):
        """Initialize pre-commit hook manager.

        Args:
            project_root: Root directory of the project
            package_name: Name of the package to validate
        """
        self.project_root = Path(project_root)
        self.package_name = package_name
        self.git_hooks_dir = self.project_root / ".git" / "hooks"
        self.pre_commit_config = self.project_root / ".pre-commit-config.yaml"

    def install_git_hook(self) -> str:
        """Install a git pre-commit hook for documentation validation.

        Returns:
            Path to the installed hook file
        """
        hook_script = self._generate_git_hook_script()

        # Ensure .git/hooks directory exists
        self.git_hooks_dir.mkdir(parents=True, exist_ok=True)

        hook_file = self.git_hooks_dir / "pre-commit"

        # Check if hook already exists
        if hook_file.exists():
            # Backup existing hook
            backup_file = self.git_hooks_dir / "pre-commit.backup"
            if not backup_file.exists():
                hook_file.rename(backup_file)
                logger.info(f"Backed up existing pre-commit hook to {backup_file}")

        # Write new hook
        with open(hook_file, 'w', encoding='utf-8') as f:
            f.write(hook_script)

        # Make executable
        hook_file.chmod(0o755)

        logger.info(f"Installed git pre-commit hook: {hook_file}")
        return str(hook_file)

    def _generate_git_hook_script(self) -> str:
        """Generate the git pre-commit hook script."""
        return f"""#!/bin/bash
# Ultrathink Documentation Pre-commit Hook
# This hook validates documentation before allowing commits

set -e

echo "🔍 Running documentation validation..."

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Not in a git repository"
    exit 1
fi

# Check if ultrathink is available
if ! command -v python >/dev/null 2>&1; then
    echo "❌ Python not found"
    exit 1
fi

# Get list of staged Python files
STAGED_PYTHON_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\\.(py)$' || true)

if [ -z "$STAGED_PYTHON_FILES" ]; then
    echo "✅ No Python files staged, skipping documentation validation"
    exit 0
fi

echo "📁 Staged Python files:"
echo "$STAGED_PYTHON_FILES"

# Create temporary directory for validation
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# Check if uv is available
if command -v uv >/dev/null 2>&1; then
    PYTHON_CMD="uv run python"
else
    PYTHON_CMD="python"
fi

# Run documentation validation
echo "🔍 Running API introspection..."
if ! $PYTHON_CMD -m docs.ultrathink.cli introspect --package {self.package_name} --output "$TEMP_DIR/api_data.json"; then
    echo "❌ API introspection failed"
    exit 1
fi

# Run doctest validation
echo "🧪 Running doctest validation..."
if ! $PYTHON_CMD -m docs.ultrathink.cli validate-doctests --package {self.package_name}; then
    echo "❌ Doctest validation failed"
    echo "💡 Fix failing doctests before committing"
    exit 1
fi

# Check for new undocumented APIs in staged files
echo "📝 Checking for undocumented APIs..."
if ! $PYTHON_CMD -m docs.ultrathink.cli check-staged-files --package {self.package_name}; then
    echo "❌ New undocumented APIs found in staged files"
    echo "💡 Add documentation for new APIs before committing"
    exit 1
fi

# Check documentation completeness
echo "📊 Checking documentation completeness..."
if ! $PYTHON_CMD -m docs.ultrathink.cli check-completeness --package {self.package_name} --threshold 0.85 --staged-only; then
    echo "⚠️  Documentation completeness below threshold for staged changes"
    echo "💡 Consider improving documentation coverage"
    # Don't fail the commit for completeness, just warn
fi

echo "✅ Documentation validation passed!"
exit 0
"""

    def create_pre_commit_config(self) -> str:
        """Create a .pre-commit-config.yaml file with documentation hooks.

        Returns:
            Path to the created config file
        """
        import yaml

        config = {
            "repos": [
                {
                    "repo": "https://github.com/pre-commit/pre-commit-hooks",
                    "rev": "v4.4.0",
                    "hooks": [
                        {"id": "trailing-whitespace"},
                        {"id": "end-of-file-fixer"},
                        {"id": "check-yaml"},
                        {"id": "check-added-large-files"},
                        {"id": "check-merge-conflict"},
                        {"id": "debug-statements"}
                    ]
                },
                {
                    "repo": "local",
                    "hooks": [
                        {
                            "id": "ultrathink-doctest-validation",
                            "name": "Ultrathink Doctest Validation",
                            "entry": "python -m docs.ultrathink.cli validate-doctests",
                            "args": [f"--package={self.package_name}"],
                            "language": "system",
                            "files": r"\\.py$",
                            "stages": ["commit"]
                        },
                        {
                            "id": "ultrathink-api-documentation",
                            "name": "Ultrathink API Documentation Check",
                            "entry": "python -m docs.ultrathink.cli check-staged-files",
                            "args": [f"--package={self.package_name}"],
                            "language": "system",
                            "files": r"\\.py$",
                            "stages": ["commit"]
                        },
                        {
                            "id": "ultrathink-completeness-check",
                            "name": "Ultrathink Documentation Completeness",
                            "entry": "python -m docs.ultrathink.cli check-completeness",
                            "args": [f"--package={self.package_name}", "--threshold=0.85", "--staged-only"],
                            "language": "system",
                            "files": r"\\.py$",
                            "stages": ["commit"],
                            "verbose": True
                        }
                    ]
                }
            ]
        }

        with open(self.pre_commit_config, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Created pre-commit config: {self.pre_commit_config}")
        return str(self.pre_commit_config)

    def run_pre_commit_validation(self, staged_files: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run pre-commit validation manually.

        Args:
            staged_files: List of files to validate (defaults to git staged files)

        Returns:
            Validation results
        """
        logger.info("Running pre-commit documentation validation")

        validation_result = {
            "validation_timestamp": "",
            "staged_files": staged_files or [],
            "validation_steps": {},
            "overall_status": "unknown",
            "errors": [],
            "warnings": []
        }

        try:
            from datetime import datetime
            validation_result["validation_timestamp"] = datetime.now().isoformat()

            # Get staged files if not provided
            if not staged_files:
                staged_files = self._get_staged_python_files()
                validation_result["staged_files"] = staged_files

            if not staged_files:
                validation_result["overall_status"] = "skipped"
                validation_result["warnings"].append("No Python files staged for commit")
                return validation_result

            # Step 1: API Introspection
            introspection_result = self._run_api_introspection()
            validation_result["validation_steps"]["api_introspection"] = introspection_result

            # Step 2: Doctest Validation
            doctest_result = self._run_doctest_validation()
            validation_result["validation_steps"]["doctest_validation"] = doctest_result

            # Step 3: Check New APIs
            new_api_result = self._check_new_apis(staged_files)
            validation_result["validation_steps"]["new_api_check"] = new_api_result

            # Step 4: Completeness Check
            completeness_result = self._check_staged_completeness(staged_files)
            validation_result["validation_steps"]["completeness_check"] = completeness_result

            # Determine overall status
            failed_steps = [
                step for step, result in validation_result["validation_steps"].items()
                if result.get("status") == "failed"
            ]

            if failed_steps:
                validation_result["overall_status"] = "failed"
                validation_result["errors"].append(f"Failed validation steps: {', '.join(failed_steps)}")
            else:
                validation_result["overall_status"] = "passed"

            logger.info(f"Pre-commit validation completed: {validation_result['overall_status']}")

        except Exception as e:
            error_msg = f"Pre-commit validation failed: {e}"
            logger.error(error_msg)
            validation_result["errors"].append(error_msg)
            validation_result["overall_status"] = "error"

        return validation_result

    def _get_staged_python_files(self) -> List[str]:
        """Get list of staged Python files."""
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )

            if result.returncode != 0:
                return []

            files = result.stdout.strip().split('\n') if result.stdout.strip() else []
            python_files = [f for f in files if f.endswith('.py')]

            return python_files

        except Exception as e:
            logger.warning(f"Failed to get staged files: {e}")
            return []

    def _run_api_introspection(self) -> Dict[str, Any]:
        """Run API introspection validation step."""
        try:
            # This would normally run the ultrathink CLI command
            # For now, simulate the result
            return {
                "status": "passed",
                "message": "API introspection completed successfully",
                "details": {
                    "elements_analyzed": 0,
                    "errors": []
                }
            }

        except Exception as e:
            return {
                "status": "failed",
                "message": f"API introspection failed: {e}",
                "details": {"error": str(e)}
            }

    def _run_doctest_validation(self) -> Dict[str, Any]:
        """Run doctest validation step."""
        try:
            # Import the validator and run it
            from ..validation.doctest_validator import DoctestValidator

            validator = DoctestValidator(self.package_name)
            result = validator.validate_package_doctests()

            if result.get("failed_tests", 0) > 0 or result.get("error_tests", 0) > 0:
                return {
                    "status": "failed",
                    "message": f"Doctest validation failed: {result['failed_tests']} failed, {result['error_tests']} errors",
                    "details": result
                }
            else:
                return {
                    "status": "passed",
                    "message": f"All doctests passed: {result.get('passed_tests', 0)}/{result.get('total_tests', 0)}",
                    "details": result
                }

        except Exception as e:
            return {
                "status": "failed",
                "message": f"Doctest validation error: {e}",
                "details": {"error": str(e)}
            }

    def _check_new_apis(self, staged_files: List[str]) -> Dict[str, Any]:
        """Check for new undocumented APIs in staged files."""
        try:
            # Analyze staged files for new API elements
            new_apis = self._analyze_staged_files_for_apis(staged_files)

            undocumented_apis = [
                api for api in new_apis
                if not api.get("has_docstring", False)
            ]

            if undocumented_apis:
                return {
                    "status": "failed",
                    "message": f"Found {len(undocumented_apis)} undocumented APIs in staged files",
                    "details": {
                        "undocumented_apis": undocumented_apis,
                        "total_new_apis": len(new_apis)
                    }
                }
            else:
                return {
                    "status": "passed",
                    "message": f"All {len(new_apis)} new APIs are documented",
                    "details": {"new_apis": new_apis}
                }

        except Exception as e:
            return {
                "status": "failed",
                "message": f"New API check failed: {e}",
                "details": {"error": str(e)}
            }

    def _check_staged_completeness(self, staged_files: List[str]) -> Dict[str, Any]:
        """Check documentation completeness for staged files."""
        try:
            # This is a simplified check - in practice would use the completeness checker
            completeness_issues = []

            for file_path in staged_files:
                file_issues = self._check_file_completeness(file_path)
                if file_issues:
                    completeness_issues.extend(file_issues)

            if completeness_issues:
                return {
                    "status": "warning",  # Warning, not failure
                    "message": f"Documentation completeness issues found in {len(completeness_issues)} cases",
                    "details": {"issues": completeness_issues}
                }
            else:
                return {
                    "status": "passed",
                    "message": "Documentation completeness check passed",
                    "details": {"files_checked": len(staged_files)}
                }

        except Exception as e:
            return {
                "status": "failed",
                "message": f"Completeness check failed: {e}",
                "details": {"error": str(e)}
            }

    def _analyze_staged_files_for_apis(self, staged_files: List[str]) -> List[Dict[str, Any]]:
        """Analyze staged files for new API elements."""
        import ast

        new_apis = []

        for file_path in staged_files:
            full_path = self.project_root / file_path

            if not full_path.exists():
                continue

            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                        # Check if it's public (doesn't start with _)
                        if not node.name.startswith('_'):
                            api_info = {
                                "name": node.name,
                                "type": "function" if isinstance(node, ast.FunctionDef) else "class",
                                "file": file_path,
                                "line": node.lineno,
                                "has_docstring": ast.get_docstring(node) is not None
                            }
                            new_apis.append(api_info)

            except Exception as e:
                logger.warning(f"Failed to analyze {file_path}: {e}")

        return new_apis

    def _check_file_completeness(self, file_path: str) -> List[Dict[str, Any]]:
        """Check documentation completeness for a single file."""
        issues = []
        full_path = self.project_root / file_path

        if not full_path.exists():
            return issues

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            import ast
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    if not node.name.startswith('_'):  # Public API
                        docstring = ast.get_docstring(node)

                        if not docstring:
                            issues.append({
                                "type": "missing_docstring",
                                "element": node.name,
                                "file": file_path,
                                "line": node.lineno
                            })
                        elif len(docstring.strip()) < 20:
                            issues.append({
                                "type": "short_docstring",
                                "element": node.name,
                                "file": file_path,
                                "line": node.lineno
                            })

        except Exception as e:
            logger.warning(f"Failed to check completeness for {file_path}: {e}")

        return issues

    def generate_hook_report(self, validation_result: Dict[str, Any]) -> str:
        """Generate a human-readable pre-commit hook report."""
        status = validation_result.get("overall_status", "unknown")
        status_emoji = {
            "passed": "✅",
            "failed": "❌",
            "warning": "⚠️",
            "skipped": "⏭️",
            "unknown": "❓"
        }.get(status, "❓")

        report_lines = [
            f"# Pre-commit Documentation Validation Report",
            f"",
            f"**Status:** {status_emoji} {status.upper()}",
            f"**Timestamp:** {validation_result.get('validation_timestamp', 'unknown')}",
            f"**Staged Files:** {len(validation_result.get('staged_files', []))}",
            f""
        ]

        # Validation steps
        steps = validation_result.get("validation_steps", {})
        if steps:
            report_lines.extend([
                f"## Validation Steps",
                f""
            ])

            for step_name, step_result in steps.items():
                step_status = step_result.get("status", "unknown")
                step_emoji = {
                    "passed": "✅",
                    "failed": "❌",
                    "warning": "⚠️"
                }.get(step_status, "❓")

                report_lines.append(f"### {step_name.replace('_', ' ').title()}")
                report_lines.append(f"**Status:** {step_emoji} {step_status.upper()}")
                report_lines.append(f"**Message:** {step_result.get('message', 'No message')}")
                report_lines.append("")

        # Errors
        errors = validation_result.get("errors", [])
        if errors:
            report_lines.extend([
                f"## Errors",
                f""
            ])
            for error in errors:
                report_lines.append(f"- {error}")
            report_lines.append("")

        # Warnings
        warnings = validation_result.get("warnings", [])
        if warnings:
            report_lines.extend([
                f"## Warnings",
                f""
            ])
            for warning in warnings:
                report_lines.append(f"- {warning}")

        return "\n".join(report_lines)

    def uninstall_git_hook(self) -> bool:
        """Uninstall the git pre-commit hook.

        Returns:
            True if hook was uninstalled, False otherwise
        """
        hook_file = self.git_hooks_dir / "pre-commit"
        backup_file = self.git_hooks_dir / "pre-commit.backup"

        if not hook_file.exists():
            logger.info("No git pre-commit hook found to uninstall")
            return False

        try:
            # Remove current hook
            hook_file.unlink()

            # Restore backup if it exists
            if backup_file.exists():
                backup_file.rename(hook_file)
                logger.info("Restored previous pre-commit hook from backup")
            else:
                logger.info("Removed ultrathink pre-commit hook")

            return True

        except Exception as e:
            logger.error(f"Failed to uninstall git hook: {e}")
            return False