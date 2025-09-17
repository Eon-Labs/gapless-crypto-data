"""Documentation stub generation for ultrathink documentation system."""

import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from jinja2 import Environment, FileSystemLoader, Template

logger = logging.getLogger(__name__)


class StubGenerator:
    """Generates documentation stubs for new API elements."""

    def __init__(self, config_dir: str = "docs/ultrathink/config", output_dir: str = "docs/ultrathink/storage/generated_docs"):
        """Initialize the stub generator.

        Args:
            config_dir: Directory containing templates
            output_dir: Directory for generated documentation
        """
        self.config_dir = Path(config_dir)
        self.output_dir = Path(output_dir)
        self.templates_dir = self.config_dir / "templates"

        # Ensure directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.templates_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )

        # Create default templates if they don't exist
        self._ensure_default_templates()

    def generate_stubs_for_new_elements(self, new_elements: List[str], api_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate documentation stubs for new API elements.

        Args:
            new_elements: List of new element names
            api_data: Complete API data for the elements

        Returns:
            Dictionary mapping element names to generated stub file paths
        """
        generated_stubs = {}
        public_api = api_data.get("public_api", {})

        for element_name in new_elements:
            if element_name not in public_api:
                logger.warning(f"Element {element_name} not found in API data")
                continue

            element_data = public_api[element_name]
            element_type = element_data.get("type", "unknown")

            try:
                stub_content = self._generate_element_stub(element_name, element_data, element_type)
                stub_file = self._save_stub(element_name, element_type, stub_content)
                generated_stubs[element_name] = stub_file
                logger.info(f"Generated stub for {element_name}: {stub_file}")
            except Exception as e:
                logger.error(f"Failed to generate stub for {element_name}: {e}")

        return generated_stubs

    def _generate_element_stub(self, element_name: str, element_data: Dict[str, Any], element_type: str) -> str:
        """Generate a documentation stub for a single element."""
        # Select appropriate template
        template_name = self._get_template_name(element_type)
        template = self.jinja_env.get_template(template_name)

        # Prepare template context
        context = self._prepare_template_context(element_name, element_data, element_type)

        # Render template
        return template.render(**context)

    def _get_template_name(self, element_type: str) -> str:
        """Get the appropriate template name for an element type."""
        template_mapping = {
            "class": "class.md.j2",
            "function": "function.md.j2",
            "method": "method.md.j2",
            "module": "module.md.j2",
            "variable": "variable.md.j2",
            "callable": "function.md.j2"
        }

        return template_mapping.get(element_type, "default.md.j2")

    def _prepare_template_context(self, element_name: str, element_data: Dict[str, Any], element_type: str) -> Dict[str, Any]:
        """Prepare the template context for rendering."""
        context = {
            "element_name": element_name,
            "element_type": element_type,
            "timestamp": datetime.now().isoformat(),
            "docstring": element_data.get("doc", ""),
            "module": element_data.get("module", "unknown"),
            "signature": element_data.get("signature", ""),
            "source_file": element_data.get("source_file", ""),
            "line_number": element_data.get("line_number", ""),
        }

        # Type-specific context preparation
        if element_type == "class":
            context.update(self._prepare_class_context(element_data))
        elif element_type in ("function", "method"):
            context.update(self._prepare_function_context(element_data))
        elif element_type == "module":
            context.update(self._prepare_module_context(element_data))

        # Parse docstring sections if available
        context["docstring_sections"] = self._parse_docstring_sections(context["docstring"])

        # Generate examples placeholder
        context["example_placeholder"] = self._generate_example_placeholder(element_name, element_type, element_data)

        return context

    def _prepare_class_context(self, element_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare context specific to classes."""
        return {
            "base_classes": element_data.get("base_classes", []),
            "methods": element_data.get("methods", {}),
            "class_methods": element_data.get("class_methods", {}),
            "static_methods": element_data.get("static_methods", {}),
            "properties": element_data.get("properties", {}),
            "mro": element_data.get("mro", [])
        }

    def _prepare_function_context(self, element_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare context specific to functions/methods."""
        return {
            "parameters": element_data.get("parameters", {}),
            "return_annotation": element_data.get("return_annotation", ""),
            "is_async": element_data.get("is_async", False),
            "is_generator": element_data.get("is_generator", False),
            "var_positional": element_data.get("var_positional", ""),
            "var_keyword": element_data.get("var_keyword", "")
        }

    def _prepare_module_context(self, element_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare context specific to modules."""
        return {
            "file": element_data.get("file", ""),
            "package": element_data.get("package", ""),
            "all_exports": element_data.get("all", []),
            "members": element_data.get("members", [])
        }

    def _parse_docstring_sections(self, docstring: str) -> Dict[str, str]:
        """Parse docstring into sections."""
        if not docstring:
            return {}

        sections = {}
        current_section = "description"
        current_content = []

        lines = docstring.split("\n")
        for line in lines:
            stripped = line.strip()

            # Check for section headers
            if self._is_section_header(stripped):
                # Save previous section
                if current_content:
                    sections[current_section] = "\n".join(current_content).strip()

                # Start new section
                current_section = self._normalize_section_name(stripped)
                current_content = []
            else:
                current_content.append(line)

        # Save final section
        if current_content:
            sections[current_section] = "\n".join(current_content).strip()

        return sections

    def _is_section_header(self, line: str) -> bool:
        """Check if a line is a docstring section header."""
        section_patterns = [
            r"^(args?|arguments?|parameters?):\s*$",
            r"^(returns?|return):\s*$",
            r"^(raises?|except):\s*$",
            r"^(examples?|example):\s*$",
            r"^(notes?|note):\s*$",
            r"^(see also):\s*$",
            r"^(attributes?):\s*$",
            r"^(yields?|yield):\s*$"
        ]

        return any(re.match(pattern, line.lower()) for pattern in section_patterns)

    def _normalize_section_name(self, header: str) -> str:
        """Normalize section header to standard name."""
        header_lower = header.lower().rstrip(":").strip()

        mapping = {
            "args": "args",
            "arguments": "args",
            "parameters": "args",
            "returns": "returns",
            "return": "returns",
            "raises": "raises",
            "except": "raises",
            "examples": "examples",
            "example": "examples",
            "notes": "notes",
            "note": "notes",
            "see also": "see_also",
            "attributes": "attributes",
            "yields": "yields",
            "yield": "yields"
        }

        return mapping.get(header_lower, header_lower)

    def _generate_example_placeholder(self, element_name: str, element_type: str, element_data: Dict[str, Any]) -> str:
        """Generate an example usage placeholder."""
        if element_type == "class":
            return f"""```python
# Create an instance of {element_name}
{element_name.lower()} = {element_name}()

# TODO: Add specific usage examples
```"""

        elif element_type in ("function", "method"):
            signature = element_data.get("signature", "")
            if signature:
                # Extract parameter names from signature
                import re
                param_pattern = r'(\w+)(?:\s*:\s*[^,=]+)?(?:\s*=\s*[^,]+)?'
                params = re.findall(param_pattern, signature)

                # Filter out 'self' and 'cls'
                params = [p for p in params if p not in ('self', 'cls')]

                if params:
                    example_params = ", ".join(f"{p}=..." for p in params[:3])  # Show first 3 params
                    return f"""```python
# Example usage of {element_name}
result = {element_name}({example_params})

# TODO: Add specific usage examples
```"""

        return f"""```python
# Example usage of {element_name}
# TODO: Add specific usage examples
```"""

    def _save_stub(self, element_name: str, element_type: str, content: str) -> str:
        """Save generated stub to file."""
        # Create filename
        safe_name = re.sub(r'[^\w\-_.]', '_', element_name)
        filename = f"{safe_name}_{element_type}.md"

        # Create directory structure
        element_dir = self.output_dir / "api_reference"
        element_dir.mkdir(parents=True, exist_ok=True)

        # Save file
        file_path = element_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return str(file_path)

    def _ensure_default_templates(self):
        """Ensure default templates exist."""
        templates = {
            "class.md.j2": self._get_default_class_template(),
            "function.md.j2": self._get_default_function_template(),
            "method.md.j2": self._get_default_method_template(),
            "module.md.j2": self._get_default_module_template(),
            "variable.md.j2": self._get_default_variable_template(),
            "default.md.j2": self._get_default_generic_template()
        }

        for template_name, template_content in templates.items():
            template_path = self.templates_dir / template_name
            if not template_path.exists():
                with open(template_path, 'w', encoding='utf-8') as f:
                    f.write(template_content)
                logger.info(f"Created default template: {template_path}")

    def _get_default_class_template(self) -> str:
        """Get default class documentation template."""
        return '''# {{ element_name }}

**Type:** Class
**Module:** `{{ module }}`
{% if source_file %}**Source:** {{ source_file }}{% if line_number %}:{{ line_number }}{% endif %}{% endif %}

## Overview

{{ docstring_sections.get('description', docstring) or 'TODO: Add class description' }}

## Class Signature

```python
class {{ element_name }}{% if base_classes %}({{ base_classes | join(', ') }}){% endif %}:
    ...
```

{% if docstring_sections.get('args') %}
## Parameters

{{ docstring_sections.args }}
{% endif %}

{% if methods %}
## Methods

{% for method_name, method_data in methods.items() %}
### {{ method_name }}

{{ method_data.get('docstring', 'TODO: Add method description') }}

{% if method_data.get('signature') %}
```python
{{ method_data.signature }}
```
{% endif %}

{% endfor %}
{% endif %}

{% if properties %}
## Properties

{% for prop_name, prop_data in properties.items() %}
### {{ prop_name }}

{{ prop_data.get('docstring', 'TODO: Add property description') }}

{% endfor %}
{% endif %}

{% if class_methods %}
## Class Methods

{% for method_name, method_data in class_methods.items() %}
### {{ method_name }}

{{ method_data.get('docstring', 'TODO: Add class method description') }}

{% endfor %}
{% endif %}

{% if static_methods %}
## Static Methods

{% for method_name, method_data in static_methods.items() %}
### {{ method_name }}

{{ method_data.get('docstring', 'TODO: Add static method description') }}

{% endfor %}
{% endif %}

## Examples

{{ example_placeholder }}

{% if docstring_sections.get('notes') %}
## Notes

{{ docstring_sections.notes }}
{% endif %}

{% if docstring_sections.get('see_also') %}
## See Also

{{ docstring_sections.see_also }}
{% endif %}

---
*Generated by Ultrathink Documentation System on {{ timestamp }}*
'''

    def _get_default_function_template(self) -> str:
        """Get default function documentation template."""
        return '''# {{ element_name }}

**Type:** {% if is_async %}Async {% endif %}Function
**Module:** `{{ module }}`
{% if source_file %}**Source:** {{ source_file }}{% if line_number %}:{{ line_number }}{% endif %}{% endif %}

## Overview

{{ docstring_sections.get('description', docstring) or 'TODO: Add function description' }}

## Signature

```python
{% if is_async %}async {% endif %}def {{ element_name }}{{ signature }}{% if return_annotation %} -> {{ return_annotation }}{% endif %}:
    ...
```

{% if parameters %}
## Parameters

{% for param_name, param_data in parameters.items() %}
- **{{ param_name }}**{% if param_data.annotation %} (`{{ param_data.annotation }}`){% endif %}{% if param_data.has_default %} = `{{ param_data.default }}`{% endif %}: TODO: Add parameter description
{% endfor %}
{% endif %}

{% if return_annotation %}
## Returns

**`{{ return_annotation }}`**: TODO: Add return description
{% endif %}

{% if docstring_sections.get('raises') %}
## Raises

{{ docstring_sections.raises }}
{% endif %}

## Examples

{{ example_placeholder }}

{% if docstring_sections.get('notes') %}
## Notes

{{ docstring_sections.notes }}
{% endif %}

{% if docstring_sections.get('see_also') %}
## See Also

{{ docstring_sections.see_also }}
{% endif %}

---
*Generated by Ultrathink Documentation System on {{ timestamp }}*
'''

    def _get_default_method_template(self) -> str:
        """Get default method documentation template."""
        # Methods use the same template as functions
        return self._get_default_function_template()

    def _get_default_module_template(self) -> str:
        """Get default module documentation template."""
        return '''# {{ element_name }}

**Type:** Module
**Package:** `{{ package }}`
{% if file %}**File:** {{ file }}{% endif %}

## Overview

{{ docstring_sections.get('description', docstring) or 'TODO: Add module description' }}

{% if all_exports %}
## Public API

The following elements are exported by this module:

{% for export in all_exports %}
- `{{ export }}`
{% endfor %}
{% endif %}

{% if members %}
## Members

{% for member in members %}
- `{{ member }}`
{% endfor %}
{% endif %}

## Examples

```python
# Import the module
from {{ module.split('.')[0] }} import {{ element_name }}

# TODO: Add specific usage examples
```

{% if docstring_sections.get('notes') %}
## Notes

{{ docstring_sections.notes }}
{% endif %}

---
*Generated by Ultrathink Documentation System on {{ timestamp }}*
'''

    def _get_default_variable_template(self) -> str:
        """Get default variable documentation template."""
        return '''# {{ element_name }}

**Type:** Variable/Constant
**Module:** `{{ module }}`
{% if source_file %}**Source:** {{ source_file }}{% if line_number %}:{{ line_number }}{% endif %}{% endif %}

## Overview

{{ docstring or 'TODO: Add variable description' }}

## Usage

```python
from {{ module }} import {{ element_name }}

# TODO: Add usage examples
```

---
*Generated by Ultrathink Documentation System on {{ timestamp }}*
'''

    def _get_default_generic_template(self) -> str:
        """Get default generic documentation template."""
        return '''# {{ element_name }}

**Type:** {{ element_type }}
**Module:** `{{ module }}`
{% if source_file %}**Source:** {{ source_file }}{% if line_number %}:{{ line_number }}{% endif %}{% endif %}

## Overview

{{ docstring or 'TODO: Add description' }}

## Usage

{{ example_placeholder }}

---
*Generated by Ultrathink Documentation System on {{ timestamp }}*
'''

    def regenerate_all_stubs(self, api_data: Dict[str, Any], force: bool = False) -> Dict[str, str]:
        """Regenerate stubs for all API elements.

        Args:
            api_data: Complete API data
            force: Whether to overwrite existing stubs

        Returns:
            Dictionary mapping element names to generated stub file paths
        """
        public_api = api_data.get("public_api", {})
        generated_stubs = {}

        for element_name, element_data in public_api.items():
            element_type = element_data.get("type", "unknown")
            safe_name = re.sub(r'[^\w\-_.]', '_', element_name)
            filename = f"{safe_name}_{element_type}.md"
            file_path = self.output_dir / "api_reference" / filename

            # Skip if file exists and force is False
            if file_path.exists() and not force:
                logger.debug(f"Skipping existing stub: {file_path}")
                continue

            try:
                stub_content = self._generate_element_stub(element_name, element_data, element_type)
                stub_file = self._save_stub(element_name, element_type, stub_content)
                generated_stubs[element_name] = stub_file
                logger.info(f"Generated stub for {element_name}: {stub_file}")
            except Exception as e:
                logger.error(f"Failed to generate stub for {element_name}: {e}")

        return generated_stubs