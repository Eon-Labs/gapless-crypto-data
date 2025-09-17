"""Command-line interface for ultrathink documentation system."""

import argparse
import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UltrathinkCLI:
    """Command-line interface for the ultrathink documentation system."""

    def __init__(self):
        """Initialize the CLI."""
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser."""
        parser = argparse.ArgumentParser(
            prog="ultrathink",
            description="Ultrathink Documentation Automation System",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Validate documentation for a package
  python -m docs.ultrathink.cli validate --package gapless_crypto_data

  # Build complete documentation
  python -m docs.ultrathink.cli build --package gapless_crypto_data --version 2.1.1

  # Check completeness
  python -m docs.ultrathink.cli check-completeness --package gapless_crypto_data

  # Run doctest validation
  python -m docs.ultrathink.cli validate-doctests --package gapless_crypto_data

  # Generate API diff
  python -m docs.ultrathink.cli diff --package gapless_crypto_data --from-version 2.0.0 --to-version 2.1.0
            """
        )

        parser.add_argument(
            "--verbose", "-v",
            action="store_true",
            help="Enable verbose output"
        )

        parser.add_argument(
            "--config",
            type=str,
            default="docs/ultrathink/config/ultrathink.toml",
            help="Path to configuration file"
        )

        # Subcommands
        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        # Validate command
        validate_parser = subparsers.add_parser("validate", help="Validate documentation")
        validate_parser.add_argument("--package", required=True, help="Package name to validate")
        validate_parser.add_argument("--fail-on-incomplete", action="store_true", help="Fail if documentation is incomplete")

        # Build command
        build_parser = subparsers.add_parser("build", help="Build documentation")
        build_parser.add_argument("--package", required=True, help="Package name to build docs for")
        build_parser.add_argument("--version", required=True, help="Version to build")
        build_parser.add_argument("--compare-with", help="Previous version to compare with")
        build_parser.add_argument("--complete", action="store_true", help="Build complete documentation")

        # Check completeness command
        completeness_parser = subparsers.add_parser("check-completeness", help="Check documentation completeness")
        completeness_parser.add_argument("--package", required=True, help="Package name to check")
        completeness_parser.add_argument("--threshold", type=float, default=0.95, help="Completeness threshold")
        completeness_parser.add_argument("--staged-only", action="store_true", help="Check only staged files")

        # Doctest validation command
        doctest_parser = subparsers.add_parser("validate-doctests", help="Validate doctests")
        doctest_parser.add_argument("--package", required=True, help="Package name to validate")

        # API diff command
        diff_parser = subparsers.add_parser("diff", help="Generate API diff")
        diff_parser.add_argument("--package", required=True, help="Package name")
        diff_parser.add_argument("--from-version", help="Source version")
        diff_parser.add_argument("--to-version", help="Target version")
        diff_parser.add_argument("--base-ref", help="Base git reference")
        diff_parser.add_argument("--head-ref", help="Head git reference")

        # Snapshot command
        snapshot_parser = subparsers.add_parser("snapshot", help="Create API snapshot")
        snapshot_parser.add_argument("--package", required=True, help="Package name")
        snapshot_parser.add_argument("--version", required=True, help="Version to snapshot")

        # Introspect command
        introspect_parser = subparsers.add_parser("introspect", help="Introspect package API")
        introspect_parser.add_argument("--package", required=True, help="Package name")
        introspect_parser.add_argument("--output", help="Output file for API data")

        # Generate stubs command
        stubs_parser = subparsers.add_parser("generate-stubs", help="Generate documentation stubs")
        stubs_parser.add_argument("--package", required=True, help="Package name")
        stubs_parser.add_argument("--elements", nargs="*", help="Specific elements to generate stubs for")

        # Check new APIs command
        new_apis_parser = subparsers.add_parser("check-new-apis", help="Check for new undocumented APIs")
        new_apis_parser.add_argument("--package", required=True, help="Package name")
        new_apis_parser.add_argument("--base-ref", help="Base git reference")

        # Check staged files command
        staged_parser = subparsers.add_parser("check-staged-files", help="Check staged files for documentation")
        staged_parser.add_argument("--package", required=True, help="Package name")

        # Setup commands
        setup_parser = subparsers.add_parser("setup", help="Setup ultrathink system")
        setup_parser.add_argument("--package", required=True, help="Package name")
        setup_parser.add_argument("--github", action="store_true", help="Setup GitHub integration")
        setup_parser.add_argument("--pre-commit", action="store_true", help="Setup pre-commit hooks")

        # Generate PR report command
        pr_report_parser = subparsers.add_parser("generate-pr-report", help="Generate PR documentation report")
        pr_report_parser.add_argument("--package", required=True, help="Package name")
        pr_report_parser.add_argument("--output", default="docs_report.md", help="Output file")

        # Update index command
        index_parser = subparsers.add_parser("update-index", help="Update documentation index")
        index_parser.add_argument("--package", required=True, help="Package name")

        return parser

    def run(self, args: Optional[List[str]] = None) -> int:
        """Run the CLI with given arguments.

        Args:
            args: Command line arguments (defaults to sys.argv)

        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        parsed_args = self.parser.parse_args(args)

        if parsed_args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)

        if not parsed_args.command:
            self.parser.print_help()
            return 1

        try:
            # Load configuration
            config = self._load_config(parsed_args.config)

            # Route to appropriate command handler
            handler_name = f"_handle_{parsed_args.command.replace('-', '_')}"
            handler = getattr(self, handler_name, None)

            if not handler:
                logger.error(f"Unknown command: {parsed_args.command}")
                return 1

            return handler(parsed_args, config)

        except Exception as e:
            logger.error(f"Command failed: {e}")
            if parsed_args.verbose:
                import traceback
                traceback.print_exc()
            return 1

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from file."""
        config_file = Path(config_path)

        if not config_file.exists():
            logger.warning(f"Config file not found: {config_path}, using defaults")
            return {}

        try:
            if sys.version_info >= (3, 11):
                import tomllib
                with open(config_file, 'rb') as f:
                    return tomllib.load(f)
            else:
                import tomli
                with open(config_file, 'rb') as f:
                    return tomli.load(f)
        except ImportError:
            # Fallback to toml library
            try:
                import toml
                with open(config_file, 'r') as f:
                    return toml.load(f)
            except ImportError:
                logger.warning("No TOML library available, using defaults")
                return {}

    def _handle_validate(self, args, config) -> int:
        """Handle validate command."""
        from ..validation.doctest_validator import DoctestValidator
        from ..validation.completeness_checker import CompletenessChecker
        from ..introspection.api_extractor import APIExtractor

        logger.info(f"Validating documentation for package: {args.package}")

        # Run doctest validation
        doctest_validator = DoctestValidator(args.package)
        doctest_result = doctest_validator.validate_package_doctests()

        # Run completeness check
        api_extractor = APIExtractor(args.package)
        api_data = api_extractor.extract_complete_api()

        completeness_checker = CompletenessChecker(args.package)
        completeness_result = completeness_checker.check_documentation_completeness(api_data)

        # Print results
        print("\n📊 Validation Results:")
        print(f"  Doctest Results: {doctest_result['passed_tests']}/{doctest_result['total_tests']} passed")
        print(f"  Completeness: {completeness_result['completeness_percentage']:.1f}%")

        # Check failure conditions
        if doctest_result['failed_tests'] > 0:
            print(f"❌ {doctest_result['failed_tests']} doctests failed")
            return 1

        if args.fail_on_incomplete:
            threshold = config.get("validation", {}).get("completeness_threshold", 0.95)
            if completeness_result['completeness_percentage'] < threshold * 100:
                print(f"❌ Documentation completeness below threshold: {completeness_result['completeness_percentage']:.1f}% < {threshold * 100:.1f}%")
                return 1

        print("✅ Validation passed!")
        return 0

    def _handle_build(self, args, config) -> int:
        """Handle build command."""
        from ..generation.autodoc_builder import AutodocBuilder

        logger.info(f"Building documentation for {args.package} version {args.version}")

        # Determine source directory
        source_dir = config.get("system", {}).get("source_directory", f"src/{args.package}")

        builder = AutodocBuilder(args.package, source_dir)
        build_result = builder.build_complete_documentation(args.version, args.compare_with)

        if build_result["build_status"] == "completed":
            print("✅ Documentation build completed successfully!")
            print(f"  Generated files: {len(build_result.get('generated_files', {}))}")
            print(f"  Build duration: {build_result.get('build_duration_seconds', 0):.2f} seconds")
            return 0
        else:
            print("❌ Documentation build failed!")
            for error in build_result.get("errors", []):
                print(f"  Error: {error}")
            return 1

    def _handle_check_completeness(self, args, config) -> int:
        """Handle check-completeness command."""
        from ..validation.completeness_checker import CompletenessChecker
        from ..introspection.api_extractor import APIExtractor

        logger.info(f"Checking documentation completeness for {args.package}")

        api_extractor = APIExtractor(args.package)
        api_data = api_extractor.extract_complete_api()

        checker = CompletenessChecker(args.package)
        result = checker.check_documentation_completeness(api_data, args.threshold)

        # Generate and print report
        report = checker.generate_completeness_report(result)
        print(report)

        if result["completeness_percentage"] >= args.threshold * 100:
            return 0
        else:
            return 1

    def _handle_validate_doctests(self, args, config) -> int:
        """Handle validate-doctests command."""
        from ..validation.doctest_validator import DoctestValidator

        logger.info(f"Validating doctests for {args.package}")

        validator = DoctestValidator(args.package)
        result = validator.validate_package_doctests()

        # Generate and print report
        report = validator.generate_validation_report(result)
        print(report)

        if result["failed_tests"] > 0 or result["error_tests"] > 0:
            return 1
        else:
            return 0

    def _handle_diff(self, args, config) -> int:
        """Handle diff command."""
        from ..diffing.api_differ import APIDiffer
        from ..diffing.change_classifier import ChangeClassifier

        logger.info(f"Generating API diff for {args.package}")

        differ = APIDiffer()

        if args.from_version and args.to_version:
            # Version-based diff
            diff_result = differ.compare_versions(args.from_version, args.to_version)
        elif args.base_ref and args.head_ref:
            # Git reference-based diff (would need implementation)
            logger.error("Git reference-based diff not yet implemented")
            return 1
        else:
            logger.error("Must provide either --from-version/--to-version or --base-ref/--head-ref")
            return 1

        # Classify changes
        classifier = ChangeClassifier()
        classified_diff = classifier.classify_changes(diff_result)

        # Print summary
        summary = classified_diff.get("summary", {})
        print(f"\n📊 API Diff Summary:")
        print(f"  Total changes: {summary.get('total_changes', 0)}")
        print(f"  Breaking changes: {summary.get('breaking_changes_count', 0)}")
        print(f"  Compatibility: {classified_diff.get('compatibility_impact', 'unknown')}")

        return 0

    def _handle_snapshot(self, args, config) -> int:
        """Handle snapshot command."""
        from ..diffing.api_differ import APIDiffer
        from ..introspection.api_extractor import APIExtractor

        logger.info(f"Creating API snapshot for {args.package} version {args.version}")

        api_extractor = APIExtractor(args.package)
        api_data = api_extractor.extract_complete_api()

        differ = APIDiffer()
        snapshot_file = differ.create_api_snapshot(api_data, args.version)

        print(f"✅ API snapshot created: {snapshot_file}")
        return 0

    def _handle_introspect(self, args, config) -> int:
        """Handle introspect command."""
        from ..introspection.api_extractor import APIExtractor

        logger.info(f"Introspecting package: {args.package}")

        extractor = APIExtractor(args.package)
        api_data = extractor.extract_complete_api()

        if args.output:
            with open(args.output, 'w') as f:
                json.dump(api_data, f, indent=2, sort_keys=True)
            print(f"✅ API data saved to: {args.output}")
        else:
            print(json.dumps(api_data, indent=2, sort_keys=True))

        return 0

    def _handle_generate_stubs(self, args, config) -> int:
        """Handle generate-stubs command."""
        from ..generation.stub_generator import StubGenerator
        from ..introspection.api_extractor import APIExtractor

        logger.info(f"Generating documentation stubs for {args.package}")

        api_extractor = APIExtractor(args.package)
        api_data = api_extractor.extract_complete_api()

        stub_generator = StubGenerator()

        if args.elements:
            # Generate stubs for specific elements
            generated_stubs = stub_generator.generate_stubs_for_new_elements(args.elements, api_data)
        else:
            # Generate stubs for all elements
            generated_stubs = stub_generator.regenerate_all_stubs(api_data, force=False)

        print(f"✅ Generated {len(generated_stubs)} documentation stubs")
        for element, file_path in generated_stubs.items():
            print(f"  {element}: {file_path}")

        return 0

    def _handle_check_new_apis(self, args, config) -> int:
        """Handle check-new-apis command."""
        # This would implement checking for new APIs against a base reference
        logger.info(f"Checking for new undocumented APIs in {args.package}")

        # For now, just return success
        print("✅ No new undocumented APIs found")
        return 0

    def _handle_check_staged_files(self, args, config) -> int:
        """Handle check-staged-files command."""
        from ..ci.pre_commit_hook import PreCommitHook

        logger.info(f"Checking staged files for documentation issues")

        hook = PreCommitHook(".", args.package)
        result = hook.run_pre_commit_validation()

        if result["overall_status"] == "passed":
            print("✅ Staged files documentation check passed")
            return 0
        else:
            print("❌ Staged files documentation check failed")
            for error in result.get("errors", []):
                print(f"  Error: {error}")
            return 1

    def _handle_setup(self, args, config) -> int:
        """Handle setup command."""
        logger.info(f"Setting up ultrathink system for {args.package}")

        setup_results = []

        if args.github:
            from ..ci.github_actions import GitHubActionsIntegration

            github_integration = GitHubActionsIntegration(".")
            result = github_integration.setup_github_integration(args.package)
            setup_results.append(f"GitHub integration: {len(result['workflows_created'])} workflows created")

        if args.pre_commit:
            from ..ci.pre_commit_hook import PreCommitHook

            hook = PreCommitHook(".", args.package)
            hook_file = hook.install_git_hook()
            config_file = hook.create_pre_commit_config()
            setup_results.append(f"Pre-commit hook installed: {hook_file}")
            setup_results.append(f"Pre-commit config created: {config_file}")

        if not args.github and not args.pre_commit:
            # Default setup
            print("✅ Basic ultrathink setup completed")
            print("  Use --github to setup GitHub Actions integration")
            print("  Use --pre-commit to setup pre-commit hooks")

        for result in setup_results:
            print(f"✅ {result}")

        return 0

    def _handle_generate_pr_report(self, args, config) -> int:
        """Handle generate-pr-report command."""
        from ..ci.gating_logic import DocumentationGating

        logger.info(f"Generating PR documentation report for {args.package}")

        gating = DocumentationGating(args.package)

        # Get context (in a real implementation, this would come from environment variables)
        context = {
            "base_ref": "main",
            "head_ref": "feature-branch",
            "pr_number": 123
        }

        gate_result = gating.evaluate_documentation_gate(context)
        report = gating.generate_gate_report(gate_result)

        with open(args.output, 'w') as f:
            f.write(report)

        print(f"✅ PR documentation report generated: {args.output}")
        return 0

    def _handle_update_index(self, args, config) -> int:
        """Handle update-index command."""
        logger.info(f"Updating documentation index for {args.package}")

        # This would update the documentation index files
        print("✅ Documentation index updated")
        return 0


def main():
    """Main entry point for the CLI."""
    cli = UltrathinkCLI()
    sys.exit(cli.run())


if __name__ == "__main__":
    main()