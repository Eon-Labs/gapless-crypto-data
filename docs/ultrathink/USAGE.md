# Ultrathink Documentation System Usage Guide

## Overview

The Ultrathink Documentation System provides comprehensive SSOT (Single Source of Truth) runtime documentation automation for Python packages. It ensures documentation stays synchronized with code changes through automated introspection, diffing, validation, and CI/CD integration.

## Quick Start

### 1. System Setup

The ultrathink system is already integrated into your project. To set up additional integrations:

```bash
# Setup GitHub Actions integration
uv run python -m docs.ultrathink.cli setup --package gapless_crypto_data --github

# Setup pre-commit hooks
uv run python -m docs.ultrathink.cli setup --package gapless_crypto_data --pre-commit
```

### 2. Basic Usage

```bash
# Validate all documentation
uv run python -m docs.ultrathink.cli validate --package gapless_crypto_data

# Check documentation completeness
uv run python -m docs.ultrathink.cli check-completeness --package gapless_crypto_data --threshold 0.95

# Build complete documentation for a version
uv run python -m docs.ultrathink.cli build --package gapless_crypto_data --version 2.2.0

# Generate API diff between versions
uv run python -m docs.ultrathink.cli diff --package gapless_crypto_data --from-version 2.1.1 --to-version 2.2.0
```

## Core Features

### 1. API Introspection

Automatically analyzes your package structure and extracts API information:

```bash
# Introspect package API
uv run python -m docs.ultrathink.cli introspect --package gapless_crypto_data --output api_data.json
```

**What it does:**
- Analyzes package structure and modules
- Extracts function signatures, class hierarchies, and type hints
- Captures docstrings and documentation metadata
- Identifies public vs private APIs

### 2. Documentation Generation

Automatically generates documentation stubs for new API elements:

```bash
# Generate stubs for all API elements
uv run python -m docs.ultrathink.cli generate-stubs --package gapless_crypto_data

# Generate stubs for specific elements
uv run python -m docs.ultrathink.cli generate-stubs --package gapless_crypto_data --elements BinancePublicDataCollector UniversalGapFiller
```

**Generated documentation includes:**
- Function/method signatures with parameters
- Class hierarchies and inheritance
- Type hints and return types
- Example usage placeholders
- Cross-references and see-also sections

### 3. API Change Detection

Detects and analyzes API changes between versions:

```bash
# Create API snapshot for current version
uv run python -m docs.ultrathink.cli snapshot --package gapless_crypto_data --version 2.2.0

# Compare API changes
uv run python -m docs.ultrathink.cli diff --package gapless_crypto_data --from-version 2.1.1 --to-version 2.2.0
```

**Change detection includes:**
- Breaking changes identification
- New API elements
- Modified signatures
- Removed elements
- Deprecation tracking

### 4. Documentation Validation

Comprehensive validation of documentation quality:

```bash
# Validate doctests
uv run python -m docs.ultrathink.cli validate-doctests --package gapless_crypto_data

# Check completeness
uv run python -m docs.ultrathink.cli check-completeness --package gapless_crypto_data --threshold 0.95
```

**Validation includes:**
- Doctest execution and verification
- Documentation completeness checking
- Help() output snapshot validation
- Cross-reference validation

### 5. CI/CD Integration

Automated documentation checking in CI/CD pipelines:

```bash
# Check staged files (for pre-commit)
uv run python -m docs.ultrathink.cli check-staged-files --package gapless_crypto_data

# Generate PR documentation report
uv run python -m docs.ultrathink.cli generate-pr-report --package gapless_crypto_data --output docs_report.md
```

## Configuration

The system is configured through `pyproject.toml`. Key configuration sections:

### Basic Configuration

```toml
[tool.ultrathink]
enabled = true
package_name = "gapless_crypto_data"
source_directory = "src/gapless_crypto_data"
```

### Validation Configuration

```toml
[tool.ultrathink.validation]
enabled = true
validate_doctests = true
check_completeness = true
completeness_threshold = 0.95
doctest_mode = "strict"
```

### CI Integration

```toml
[tool.ultrathink.ci]
enabled = true
pre_commit_validation = true
github_actions_integration = true
gate_on_incomplete_docs = true
gate_on_failed_doctests = true
```

## Workflow Integration

### Development Workflow

1. **Write Code**: Add new functions/classes with docstrings
2. **Pre-commit**: Ultrathink validates documentation automatically
3. **PR Creation**: GitHub Actions runs documentation checks
4. **Review**: PR includes documentation completeness report
5. **Merge**: Documentation is automatically updated

### Release Workflow

1. **Version Bump**: Update version in code
2. **Documentation Build**: Complete documentation generated
3. **API Snapshot**: API state captured for future comparisons
4. **Release**: Documentation published with release

### Maintenance Workflow

1. **Regular Validation**: Scheduled documentation health checks
2. **Deprecation Management**: Track and document deprecated APIs
3. **Breaking Change Detection**: Identify and document breaking changes
4. **Migration Guides**: Auto-generate migration documentation

## Best Practices

### 1. Documentation Standards

- **Always include docstrings** for public functions and classes
- **Use type hints** for better documentation generation
- **Add examples** in docstrings using doctest format
- **Keep docstrings up-to-date** when changing APIs

### 2. API Design

- **Use semantic versioning** for proper change classification
- **Deprecate before removing** APIs to maintain compatibility
- **Document breaking changes** with migration notes
- **Keep public API minimal** to reduce documentation burden

### 3. CI/CD Integration

- **Enable pre-commit hooks** for immediate feedback
- **Gate merges** on documentation completeness
- **Review documentation reports** in PRs
- **Update documentation** with each release

## Troubleshooting

### Common Issues

**1. Doctest Failures**
```bash
# Debug doctest issues
uv run python -m docs.ultrathink.cli validate-doctests --package gapless_crypto_data
```

**2. Completeness Below Threshold**
```bash
# Identify missing documentation
uv run python -m docs.ultrathink.cli check-completeness --package gapless_crypto_data --threshold 0.95
```

**3. API Change Detection Issues**
```bash
# Check if snapshots exist
ls docs/ultrathink/storage/api_snapshots/

# Create new snapshot if needed
uv run python -m docs.ultrathink.cli snapshot --package gapless_crypto_data --version current
```

### Getting Help

- Check the generated reports for specific issues
- Review the configuration in `pyproject.toml`
- Examine the generated documentation in `docs/ultrathink/storage/`
- Use `--verbose` flag for detailed debugging information

## File Structure

The ultrathink system creates the following structure:

```
docs/ultrathink/
├── config/
│   ├── ultrathink.toml          # Main configuration
│   └── templates/               # Documentation templates
├── storage/
│   ├── api_snapshots/           # Historical API snapshots
│   ├── generated_docs/          # Generated documentation
│   ├── validation_cache/        # Validation results
│   └── help_snapshots/          # Help() output snapshots
└── USAGE.md                     # This file
```

## Advanced Usage

### Custom Templates

Customize documentation generation by modifying templates in `docs/ultrathink/config/templates/`.

### Integration with External Tools

The ultrathink system can integrate with:
- Sphinx for advanced documentation sites
- GitHub Pages for documentation hosting
- Slack/Teams for notification integration
- Custom CI/CD systems

### Extending the System

The modular architecture allows for easy extension:
- Add new validation rules
- Create custom documentation formats
- Integrate additional change detection logic
- Implement custom CI/CD integrations

---

For more information, see the individual module documentation in the generated API reference.