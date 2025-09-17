"""Signature hashing for API change detection in ultrathink documentation system."""

import hashlib
import json
from typing import Dict, Any, List, Set
import logging

logger = logging.getLogger(__name__)


class SignatureHasher:
    """Creates stable hashes of API signatures for change detection."""

    def __init__(self, sensitivity_level: str = "strict"):
        """Initialize the signature hasher.

        Args:
            sensitivity_level: Level of change sensitivity ('strict', 'moderate', 'relaxed')
        """
        self.sensitivity_level = sensitivity_level

    def hash_api_signature(self, api_data: Dict[str, Any]) -> Dict[str, str]:
        """Create hashes for all API elements.

        Args:
            api_data: Complete API data from APIExtractor

        Returns:
            Dictionary mapping API element names to their signature hashes
        """
        signature_hashes = {}

        public_api = api_data.get("public_api", {})

        for element_name, element_data in public_api.items():
            try:
                signature_hash = self._create_element_hash(element_name, element_data)
                signature_hashes[element_name] = signature_hash
                logger.debug(f"Created hash for {element_name}: {signature_hash[:8]}...")
            except Exception as e:
                logger.warning(f"Failed to hash element {element_name}: {e}")
                signature_hashes[element_name] = "error"

        logger.info(f"Generated {len(signature_hashes)} signature hashes")
        return signature_hashes

    def _create_element_hash(self, element_name: str, element_data: Dict[str, Any]) -> str:
        """Create a hash for a single API element.

        Args:
            element_name: Name of the API element
            element_data: Detailed data about the API element

        Returns:
            SHA-256 hash of the element's signature
        """
        # Create a normalized representation for hashing
        hash_data = self._normalize_element_data(element_name, element_data)

        # Convert to JSON string for consistent hashing
        json_str = json.dumps(hash_data, sort_keys=True, separators=(',', ':'))

        # Create SHA-256 hash
        return hashlib.sha256(json_str.encode('utf-8')).hexdigest()

    def _normalize_element_data(self, element_name: str, element_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize element data based on sensitivity level.

        Args:
            element_name: Name of the API element
            element_data: Raw element data

        Returns:
            Normalized data for hashing
        """
        element_type = element_data.get("type", "unknown")

        if element_type == "class":
            return self._normalize_class_data(element_name, element_data)
        elif element_type in ("function", "method"):
            return self._normalize_function_data(element_name, element_data)
        elif element_type == "module":
            return self._normalize_module_data(element_name, element_data)
        else:
            return self._normalize_variable_data(element_name, element_data)

    def _normalize_class_data(self, class_name: str, class_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize class data for hashing."""
        normalized = {
            "name": class_name,
            "type": "class"
        }

        # Always include inheritance information
        if "base_classes" in class_data:
            normalized["base_classes"] = sorted(class_data["base_classes"])

        if "mro" in class_data:
            normalized["mro"] = class_data["mro"]

        # Include method signatures based on sensitivity
        if self.sensitivity_level == "strict":
            # Include all method details
            normalized["methods"] = self._normalize_methods(class_data.get("methods", {}))
            normalized["class_methods"] = self._normalize_methods(class_data.get("class_methods", {}))
            normalized["static_methods"] = self._normalize_methods(class_data.get("static_methods", {}))
            normalized["properties"] = self._normalize_properties(class_data.get("properties", {}))

            # Include docstring in strict mode
            if class_data.get("doc"):
                normalized["doc_summary"] = self._extract_doc_summary(class_data["doc"])

        elif self.sensitivity_level == "moderate":
            # Include method signatures but not documentation
            normalized["method_signatures"] = {
                name: method.get("signature", "unknown")
                for name, method in class_data.get("methods", {}).items()
            }
            normalized["class_method_signatures"] = {
                name: method.get("signature", "unknown")
                for name, method in class_data.get("class_methods", {}).items()
            }
            normalized["static_method_signatures"] = {
                name: method.get("signature", "unknown")
                for name, method in class_data.get("static_methods", {}).items()
            }

        else:  # relaxed
            # Only include method names
            normalized["method_names"] = sorted(class_data.get("methods", {}).keys())
            normalized["class_method_names"] = sorted(class_data.get("class_methods", {}).keys())
            normalized["static_method_names"] = sorted(class_data.get("static_methods", {}).keys())

        return normalized

    def _normalize_function_data(self, func_name: str, func_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize function data for hashing."""
        normalized = {
            "name": func_name,
            "type": func_data.get("type", "function")
        }

        # Always include signature if available
        if "signature" in func_data:
            normalized["signature"] = func_data["signature"]

        # Include parameter details based on sensitivity
        if self.sensitivity_level == "strict":
            if "parameters" in func_data:
                normalized["parameters"] = self._normalize_parameters(func_data["parameters"])

            if "return_annotation" in func_data:
                normalized["return_annotation"] = func_data["return_annotation"]

            if func_data.get("doc"):
                normalized["doc_summary"] = self._extract_doc_summary(func_data["doc"])

            # Include function characteristics
            normalized["is_async"] = func_data.get("is_async", False)
            normalized["is_generator"] = func_data.get("is_generator", False)

        elif self.sensitivity_level == "moderate":
            # Include parameter types but not documentation
            if "parameters" in func_data:
                normalized["parameter_types"] = {
                    name: param.get("annotation", "Any")
                    for name, param in func_data["parameters"].items()
                }

            if "return_annotation" in func_data:
                normalized["return_annotation"] = func_data["return_annotation"]

        # In relaxed mode, only signature is included (already added above)

        return normalized

    def _normalize_module_data(self, module_name: str, module_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize module data for hashing."""
        normalized = {
            "name": module_name,
            "type": "module"
        }

        # Include public API based on sensitivity
        if self.sensitivity_level == "strict":
            if "all" in module_data:
                normalized["all"] = sorted(module_data["all"])
            if "members" in module_data:
                normalized["members"] = sorted(module_data["members"])

            if module_data.get("doc"):
                normalized["doc_summary"] = self._extract_doc_summary(module_data["doc"])

        elif self.sensitivity_level == "moderate":
            if "all" in module_data:
                normalized["all"] = sorted(module_data["all"])

        # In relaxed mode, only name and type are included

        return normalized

    def _normalize_variable_data(self, var_name: str, var_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize variable/constant data for hashing."""
        return {
            "name": var_name,
            "type": var_data.get("type", "variable")
        }

    def _normalize_methods(self, methods: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize method data for hashing."""
        normalized_methods = {}

        for method_name, method_data in methods.items():
            normalized_method = {
                "name": method_name
            }

            if "signature" in method_data:
                normalized_method["signature"] = method_data["signature"]

            if method_data.get("doc"):
                normalized_method["doc_summary"] = self._extract_doc_summary(method_data["doc"])

            normalized_methods[method_name] = normalized_method

        return normalized_methods

    def _normalize_properties(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize property data for hashing."""
        normalized_properties = {}

        for prop_name, prop_data in properties.items():
            normalized_prop = {
                "name": prop_name
            }

            if prop_data.get("doc"):
                normalized_prop["doc_summary"] = self._extract_doc_summary(prop_data["doc"])

            normalized_properties[prop_name] = normalized_prop

        return normalized_properties

    def _normalize_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize parameter data for hashing."""
        normalized_params = {}

        for param_name, param_data in parameters.items():
            normalized_param = {
                "name": param_name,
                "kind": param_data.get("kind", "unknown"),
                "has_default": param_data.get("has_default", False)
            }

            if param_data.get("annotation"):
                normalized_param["annotation"] = param_data["annotation"]

            if param_data.get("default") is not None:
                # Normalize default value representation
                default_val = param_data["default"]
                if isinstance(default_val, str):
                    # Handle string representations of defaults
                    normalized_param["default"] = default_val
                else:
                    normalized_param["default"] = str(default_val)

            normalized_params[param_name] = normalized_param

        return normalized_params

    def _extract_doc_summary(self, docstring: str) -> str:
        """Extract a summary from a docstring for hashing."""
        if not docstring:
            return ""

        # Get the first sentence or first line
        lines = docstring.strip().split('\n')
        first_line = lines[0].strip()

        # Split by sentence-ending punctuation
        import re
        sentences = re.split(r'[.!?]+', first_line)
        return sentences[0].strip() if sentences else first_line

    def compare_signatures(self, old_hashes: Dict[str, str], new_hashes: Dict[str, str]) -> Dict[str, Any]:
        """Compare two sets of signature hashes to detect changes.

        Args:
            old_hashes: Previous signature hashes
            new_hashes: Current signature hashes

        Returns:
            Dictionary describing the changes detected
        """
        changes = {
            "added": [],
            "removed": [],
            "modified": [],
            "unchanged": []
        }

        old_elements = set(old_hashes.keys())
        new_elements = set(new_hashes.keys())

        # Detect additions and removals
        changes["added"] = sorted(new_elements - old_elements)
        changes["removed"] = sorted(old_elements - new_elements)

        # Detect modifications
        common_elements = old_elements & new_elements
        for element in common_elements:
            if old_hashes[element] != new_hashes[element]:
                changes["modified"].append(element)
            else:
                changes["unchanged"].append(element)

        changes["modified"] = sorted(changes["modified"])
        changes["unchanged"] = sorted(changes["unchanged"])

        # Summary statistics
        changes["summary"] = {
            "total_changes": len(changes["added"]) + len(changes["removed"]) + len(changes["modified"]),
            "breaking_changes": len(changes["removed"]) + len(changes["modified"]),
            "non_breaking_changes": len(changes["added"])
        }

        logger.info(f"Change detection completed: {changes['summary']}")
        return changes