# Ultrathink Documentation Automation System

## Overview

The ultrathink system provides SSOT (Single Source of Truth) runtime documentation for gapless-crypto-data, ensuring documentation stays synchronized with code changes through automated introspection, diffing, and validation.

## Architecture

```
docs/ultrathink/
├── config/                     # Configuration and templates
├── introspection/              # Package analysis and API extraction
├── diffing/                    # Change detection and version tracking
├── generation/                 # Documentation stub generation
├── validation/                 # Doctest and completeness validation
├── ci/                         # CI/CD integration scripts
├── storage/                    # Documentation storage and cache
└── cli/                        # Command-line interface
```

## Core Features

### 1. **Auto-introspection**
- Analyzes package structure and extracts public API
- Generates function/class signatures with metadata
- Tracks inheritance hierarchies and dependencies

### 2. **API Diffing**
- Detects additions, removals, and modifications between versions
- Classifies changes (breaking, non-breaking, deprecation)
- Maintains historical API snapshots

### 3. **Stub Generation**
- Auto-generates documentation stubs for new symbols
- Templates for different symbol types (functions, classes, modules)
- Intelligent placement based on package structure

### 4. **Validation System**
- Validates all doctests in generated documentation
- Captures and validates help() output snapshots
- Ensures documentation completeness and accuracy

### 5. **CI Integration**
- Pre-commit hooks for documentation validation
- GitHub Actions integration with gating logic
- Blocks merges until documentation is complete and synchronized

## Quick Start

```bash
# Setup ultrathink system
uv run python -m docs.ultrathink.cli setup

# Generate documentation for current API
uv run python -m docs.ultrathink.cli generate

# Validate existing documentation
uv run python -m docs.ultrathink.cli validate

# Check for API changes since last version
uv run python -m docs.ultrathink.cli diff --since=2.1.1
```

## Integration Points

- **pyproject.toml**: Configuration through `[tool.ultrathink]` section
- **GitHub Actions**: Extends existing CI/CD pipeline
- **Pre-commit**: Integrates with existing pre-commit hooks
- **Package Structure**: Follows src/gapless_crypto_data/ organization

## Configuration

Configuration is managed through `config/ultrathink.toml` with overrides in `pyproject.toml`:

```toml
[tool.ultrathink]
enabled = true
api_introspection = true
doctest_validation = true
ci_gating = true
output_format = ["markdown", "rst"]
```