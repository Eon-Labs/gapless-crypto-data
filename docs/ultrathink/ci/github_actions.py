"""GitHub Actions integration for ultrathink documentation system."""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import yaml

logger = logging.getLogger(__name__)


class GitHubActionsIntegration:
    """Manages GitHub Actions integration for documentation automation."""

    def __init__(self, project_root: str):
        """Initialize GitHub Actions integration.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root)
        self.github_dir = self.project_root / ".github"
        self.workflows_dir = self.github_dir / "workflows"

    def create_documentation_workflow(self, package_name: str, enable_gating: bool = True) -> str:
        """Create a GitHub Actions workflow for documentation automation.

        Args:
            package_name: Name of the package
            enable_gating: Whether to enable documentation gating

        Returns:
            Path to the created workflow file
        """
        workflow_config = {
            "name": "Documentation Automation",
            "on": {
                "push": {
                    "branches": ["main", "develop"]
                },
                "pull_request": {
                    "branches": ["main"]
                },
                "workflow_dispatch": {}
            },
            "env": {
                "UV_SYSTEM_PYTHON": 1
            },
            "jobs": {
                "documentation": {
                    "runs-on": "ubuntu-latest",
                    "steps": [
                        {
                            "name": "Checkout code",
                            "uses": "actions/checkout@v4"
                        },
                        {
                            "name": "Set up Python",
                            "uses": "actions/setup-python@v4",
                            "with": {
                                "python-version": "3.12"
                            }
                        },
                        {
                            "name": "Install UV",
                            "run": "curl -LsSf https://astral.sh/uv/install.sh | sh"
                        },
                        {
                            "name": "Add UV to PATH",
                            "run": "echo \"$HOME/.local/bin\" >> $GITHUB_PATH"
                        },
                        {
                            "name": "Install dependencies",
                            "run": "uv venv && source .venv/bin/activate && uv sync --dev"
                        },
                        {
                            "name": "Run ultrathink documentation system",
                            "run": "source .venv/bin/activate && uv run python -m docs.ultrathink.cli validate --package {} --fail-on-incomplete".format(package_name)
                        }
                    ]
                }
            }
        }

        if enable_gating:
            # Add documentation gating job
            workflow_config["jobs"]["documentation-gating"] = {
                "runs-on": "ubuntu-latest",
                "needs": "documentation",
                "if": "github.event_name == 'pull_request'",
                "steps": [
                    {
                        "name": "Checkout code",
                        "uses": "actions/checkout@v4",
                        "with": {
                            "fetch-depth": 0  # Fetch full history for comparison
                        }
                    },
                    {
                        "name": "Set up Python",
                        "uses": "actions/setup-python@v4",
                        "with": {
                            "python-version": "3.12"
                        }
                    },
                    {
                        "name": "Install UV",
                        "run": "curl -LsSf https://astral.sh/uv/install.sh | sh"
                    },
                    {
                        "name": "Add UV to PATH",
                        "run": "echo \"$HOME/.local/bin\" >> $GITHUB_PATH"
                    },
                    {
                        "name": "Install dependencies",
                        "run": "uv venv && source .venv/bin/activate && uv sync --dev"
                    },
                    {
                        "name": "Check documentation completeness",
                        "run": "source .venv/bin/activate && uv run python -m docs.ultrathink.cli check-completeness --package {} --threshold 0.95".format(package_name)
                    },
                    {
                        "name": "Validate API changes",
                        "run": "source .venv/bin/activate && uv run python -m docs.ultrathink.cli diff --package {} --base-ref ${{ github.base_ref }} --head-ref ${{ github.head_ref }}".format(package_name)
                    },
                    {
                        "name": "Check for new undocumented APIs",
                        "run": "source .venv/bin/activate && uv run python -m docs.ultrathink.cli check-new-apis --package {} --base-ref ${{ github.base_ref }}".format(package_name)
                    }
                ]
            }

            # Add comment job for PR feedback
            workflow_config["jobs"]["documentation-feedback"] = {
                "runs-on": "ubuntu-latest",
                "needs": ["documentation", "documentation-gating"],
                "if": "github.event_name == 'pull_request' && (success() || failure())",
                "permissions": {
                    "pull-requests": "write"
                },
                "steps": [
                    {
                        "name": "Checkout code",
                        "uses": "actions/checkout@v4"
                    },
                    {
                        "name": "Set up Python",
                        "uses": "actions/setup-python@v4",
                        "with": {
                            "python-version": "3.12"
                        }
                    },
                    {
                        "name": "Install UV",
                        "run": "curl -LsSf https://astral.sh/uv/install.sh | sh"
                    },
                    {
                        "name": "Add UV to PATH",
                        "run": "echo \"$HOME/.local/bin\" >> $GITHUB_PATH"
                    },
                    {
                        "name": "Install dependencies",
                        "run": "uv venv && source .venv/bin/activate && uv sync --dev"
                    },
                    {
                        "name": "Generate documentation report",
                        "run": "source .venv/bin/activate && uv run python -m docs.ultrathink.cli generate-pr-report --package {} --output docs_report.md".format(package_name)
                    },
                    {
                        "name": "Comment PR with documentation report",
                        "uses": "actions/github-script@v6",
                        "with": {
                            "script": """
                                const fs = require('fs');
                                const reportPath = 'docs_report.md';

                                let report = '## 📚 Documentation Report\\n\\nNo documentation report generated.';
                                if (fs.existsSync(reportPath)) {
                                  report = fs.readFileSync(reportPath, 'utf8');
                                }

                                // Find existing comment
                                const comments = await github.rest.issues.listComments({
                                  owner: context.repo.owner,
                                  repo: context.repo.repo,
                                  issue_number: context.issue.number,
                                });

                                const existingComment = comments.data.find(comment =>
                                  comment.body.includes('📚 Documentation Report')
                                );

                                if (existingComment) {
                                  // Update existing comment
                                  await github.rest.issues.updateComment({
                                    owner: context.repo.owner,
                                    repo: context.repo.repo,
                                    comment_id: existingComment.id,
                                    body: report
                                  });
                                } else {
                                  // Create new comment
                                  await github.rest.issues.createComment({
                                    owner: context.repo.owner,
                                    repo: context.repo.repo,
                                    issue_number: context.issue.number,
                                    body: report
                                  });
                                }
                            """
                        }
                    }
                ]
            }

        # Ensure .github/workflows directory exists
        self.workflows_dir.mkdir(parents=True, exist_ok=True)

        # Write workflow file
        workflow_file = self.workflows_dir / "documentation.yml"
        with open(workflow_file, 'w', encoding='utf-8') as f:
            yaml.dump(workflow_config, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Created documentation workflow: {workflow_file}")
        return str(workflow_file)

    def update_existing_workflow(self, workflow_file: str, package_name: str) -> bool:
        """Update an existing workflow to include documentation steps.

        Args:
            workflow_file: Path to existing workflow file
            package_name: Name of the package

        Returns:
            True if workflow was updated, False otherwise
        """
        workflow_path = Path(workflow_file)
        if not workflow_path.exists():
            logger.warning(f"Workflow file does not exist: {workflow_file}")
            return False

        try:
            # Load existing workflow
            with open(workflow_path, 'r', encoding='utf-8') as f:
                workflow = yaml.safe_load(f)

            # Find the test job (most common pattern)
            jobs = workflow.get("jobs", {})
            target_job = None

            # Look for common job names
            for job_name in ["test", "tests", "ci", "build"]:
                if job_name in jobs:
                    target_job = job_name
                    break

            if not target_job:
                # Use the first job
                if jobs:
                    target_job = list(jobs.keys())[0]
                else:
                    logger.warning("No jobs found in workflow")
                    return False

            # Add documentation steps to the target job
            job_steps = jobs[target_job].get("steps", [])

            # Check if documentation steps already exist
            doc_step_exists = any(
                "ultrathink" in str(step.get("run", "")).lower() or
                "documentation" in str(step.get("name", "")).lower()
                for step in job_steps
            )

            if doc_step_exists:
                logger.info("Documentation steps already exist in workflow")
                return False

            # Add documentation validation step
            doc_step = {
                "name": "Validate documentation",
                "run": f"uv run python -m docs.ultrathink.cli validate --package {package_name}"
            }

            job_steps.append(doc_step)
            jobs[target_job]["steps"] = job_steps

            # Write updated workflow
            with open(workflow_path, 'w', encoding='utf-8') as f:
                yaml.dump(workflow, f, default_flow_style=False, sort_keys=False)

            logger.info(f"Updated workflow with documentation steps: {workflow_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to update workflow {workflow_file}: {e}")
            return False

    def create_release_workflow(self, package_name: str) -> str:
        """Create a workflow for documentation updates on releases.

        Args:
            package_name: Name of the package

        Returns:
            Path to the created workflow file
        """
        workflow_config = {
            "name": "Documentation Release",
            "on": {
                "release": {
                    "types": ["published"]
                },
                "workflow_dispatch": {
                    "inputs": {
                        "version": {
                            "description": "Version to build documentation for",
                            "required": True,
                            "type": "string"
                        }
                    }
                }
            },
            "env": {
                "UV_SYSTEM_PYTHON": 1
            },
            "jobs": {
                "update-documentation": {
                    "runs-on": "ubuntu-latest",
                    "steps": [
                        {
                            "name": "Checkout code",
                            "uses": "actions/checkout@v4"
                        },
                        {
                            "name": "Set up Python",
                            "uses": "actions/setup-python@v4",
                            "with": {
                                "python-version": "3.12"
                            }
                        },
                        {
                            "name": "Install UV",
                            "run": "curl -LsSf https://astral.sh/uv/install.sh | sh"
                        },
                        {
                            "name": "Add UV to PATH",
                            "run": "echo \"$HOME/.local/bin\" >> $GITHUB_PATH"
                        },
                        {
                            "name": "Install dependencies",
                            "run": "uv venv && source .venv/bin/activate && uv sync --dev"
                        },
                        {
                            "name": "Determine version",
                            "id": "version",
                            "run": """
                                if [ "${{ github.event_name }}" = "release" ]; then
                                  VERSION="${{ github.event.release.tag_name }}"
                                else
                                  VERSION="${{ github.event.inputs.version }}"
                                fi
                                echo "version=${VERSION}" >> $GITHUB_OUTPUT
                            """
                        },
                        {
                            "name": "Generate complete documentation",
                            "run": "source .venv/bin/activate && uv run python -m docs.ultrathink.cli build --package {} --version ${{ steps.version.outputs.version }} --complete".format(package_name)
                        },
                        {
                            "name": "Create API snapshot",
                            "run": "source .venv/bin/activate && uv run python -m docs.ultrathink.cli snapshot --package {} --version ${{ steps.version.outputs.version }}".format(package_name)
                        },
                        {
                            "name": "Update documentation index",
                            "run": "source .venv/bin/activate && uv run python -m docs.ultrathink.cli update-index --package {}".format(package_name)
                        },
                        {
                            "name": "Commit documentation updates",
                            "run": """
                                git config --global user.name 'github-actions[bot]'
                                git config --global user.email 'github-actions[bot]@users.noreply.github.com'
                                git add docs/ultrathink/storage/
                                if git diff --staged --quiet; then
                                  echo "No documentation changes to commit"
                                else
                                  git commit -m "📚 Update documentation for version ${{ steps.version.outputs.version }}"
                                  git push
                                fi
                            """
                        }
                    ]
                }
            }
        }

        workflow_file = self.workflows_dir / "documentation-release.yml"
        with open(workflow_file, 'w', encoding='utf-8') as f:
            yaml.dump(workflow_config, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Created documentation release workflow: {workflow_file}")
        return str(workflow_file)

    def setup_github_integration(self, package_name: str, update_existing: bool = True) -> Dict[str, Any]:
        """Set up complete GitHub integration for documentation automation.

        Args:
            package_name: Name of the package
            update_existing: Whether to update existing workflows

        Returns:
            Dictionary with setup results
        """
        setup_result = {
            "package_name": package_name,
            "workflows_created": [],
            "workflows_updated": [],
            "errors": []
        }

        try:
            # Create main documentation workflow
            doc_workflow = self.create_documentation_workflow(package_name, enable_gating=True)
            setup_result["workflows_created"].append(doc_workflow)

            # Create release workflow
            release_workflow = self.create_release_workflow(package_name)
            setup_result["workflows_created"].append(release_workflow)

            # Update existing workflows if requested
            if update_existing:
                existing_workflows = list(self.workflows_dir.glob("*.yml"))
                for workflow_file in existing_workflows:
                    if workflow_file.name not in ["documentation.yml", "documentation-release.yml"]:
                        if self.update_existing_workflow(str(workflow_file), package_name):
                            setup_result["workflows_updated"].append(str(workflow_file))

            logger.info(f"GitHub integration setup completed for {package_name}")

        except Exception as e:
            error_msg = f"GitHub integration setup failed: {e}"
            logger.error(error_msg)
            setup_result["errors"].append(error_msg)

        return setup_result

    def create_dependabot_config(self) -> str:
        """Create Dependabot configuration for keeping actions up to date.

        Returns:
            Path to the created dependabot.yml file
        """
        dependabot_config = {
            "version": 2,
            "updates": [
                {
                    "package-ecosystem": "github-actions",
                    "directory": "/",
                    "schedule": {
                        "interval": "weekly"
                    },
                    "commit-message": {
                        "prefix": "⬆️"
                    }
                }
            ]
        }

        dependabot_file = self.github_dir / "dependabot.yml"
        with open(dependabot_file, 'w', encoding='utf-8') as f:
            yaml.dump(dependabot_config, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Created Dependabot configuration: {dependabot_file}")
        return str(dependabot_file)

    def generate_pr_template(self) -> str:
        """Generate a pull request template with documentation checklist.

        Returns:
            Path to the created PR template file
        """
        pr_template = """## 📋 Pull Request Checklist

### Changes Made
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring

### Documentation Requirements
- [ ] Added/updated docstrings for new/modified functions and classes
- [ ] Added examples for new functionality
- [ ] Updated type hints where applicable
- [ ] Generated stubs for new API elements (if applicable)
- [ ] Documentation build passes without errors
- [ ] All doctests pass

### Testing
- [ ] Added tests for new functionality
- [ ] All existing tests pass
- [ ] Test coverage maintained or improved

### Code Quality
- [ ] Code follows project style guidelines
- [ ] No new linting errors introduced
- [ ] All automated checks pass

### API Changes (if applicable)
- [ ] API changes are backward compatible OR
- [ ] Breaking changes are documented with migration guide
- [ ] Deprecation warnings added for removed functionality
- [ ] Version bump reflects the scope of changes

---

**Documentation Status**: Will be automatically checked by the documentation automation system.
"""

        pr_template_dir = self.github_dir / "PULL_REQUEST_TEMPLATE"
        pr_template_dir.mkdir(exist_ok=True)

        template_file = pr_template_dir / "pull_request_template.md"
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(pr_template)

        logger.info(f"Created PR template: {template_file}")
        return str(template_file)

    def create_issue_templates(self) -> List[str]:
        """Create issue templates for documentation-related issues.

        Returns:
            List of paths to created template files
        """
        templates_dir = self.github_dir / "ISSUE_TEMPLATE"
        templates_dir.mkdir(exist_ok=True)

        template_files = []

        # Documentation bug template
        doc_bug_template = {
            "name": "Documentation Bug",
            "about": "Report a problem with documentation",
            "title": "[DOCS] ",
            "labels": ["documentation", "bug"],
            "body": """
## Documentation Issue

**Page/Section:** (Which documentation page or section has the issue?)

**Issue Description:** (What is wrong with the documentation?)

**Expected:** (What should the documentation say or show?)

**Actual:** (What does it currently say or show?)

**Suggested Fix:** (How should this be corrected?)

**Additional Context:** (Any other relevant information)
"""
        }

        doc_bug_file = templates_dir / "documentation_bug.yml"
        with open(doc_bug_file, 'w', encoding='utf-8') as f:
            yaml.dump(doc_bug_template, f, default_flow_style=False, sort_keys=False)
        template_files.append(str(doc_bug_file))

        # Documentation enhancement template
        doc_enhancement_template = {
            "name": "Documentation Enhancement",
            "about": "Suggest an improvement to documentation",
            "title": "[DOCS] ",
            "labels": ["documentation", "enhancement"],
            "body": """
## Documentation Enhancement Request

**Section:** (Which part of the documentation should be improved?)

**Current State:** (What exists currently?)

**Proposed Enhancement:** (What should be added or changed?)

**Rationale:** (Why would this improvement be helpful?)

**Examples:** (Any examples of how this should look?)

**Priority:** (How important is this enhancement?)
- [ ] Low - Nice to have
- [ ] Medium - Would be helpful
- [ ] High - Important for usability
"""
        }

        doc_enhancement_file = templates_dir / "documentation_enhancement.yml"
        with open(doc_enhancement_file, 'w', encoding='utf-8') as f:
            yaml.dump(doc_enhancement_template, f, default_flow_style=False, sort_keys=False)
        template_files.append(str(doc_enhancement_file))

        logger.info(f"Created issue templates: {template_files}")
        return template_files