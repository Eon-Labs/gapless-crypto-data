"""API extraction for detailed signature and documentation analysis."""

import inspect
import importlib
from typing import Dict, List, Any, Optional, Union, Callable
import ast
import textwrap
import logging

logger = logging.getLogger(__name__)


class APIExtractor:
    """Extracts detailed API information including signatures, type hints, and documentation."""

    def __init__(self, package_name: str):
        """Initialize the API extractor.

        Args:
            package_name: Name of the package to extract API from.
        """
        self.package_name = package_name
        self.package = None

    def extract_complete_api(self) -> Dict[str, Any]:
        """Extract complete API information for the package.

        Returns:
            Dictionary containing detailed API information.
        """
        try:
            self.package = importlib.import_module(self.package_name)
        except ImportError as e:
            logger.error(f"Failed to import package {self.package_name}: {e}")
            raise

        api_data = {
            "package_info": self._extract_package_info(),
            "public_api": self._extract_public_api(),
            "signatures": self._extract_signatures(),
            "type_hints": self._extract_type_hints(),
            "docstrings": self._extract_docstrings(),
            "inheritance": self._extract_inheritance_info(),
            "decorators": self._extract_decorators()
        }

        logger.info(f"API extraction completed for {self.package_name}")
        return api_data

    def _extract_package_info(self) -> Dict[str, Any]:
        """Extract basic package information."""
        return {
            "name": self.package.__name__,
            "version": getattr(self.package, "__version__", "unknown"),
            "file": getattr(self.package, "__file__", None),
            "doc": inspect.getdoc(self.package) or "",
            "all": getattr(self.package, "__all__", [])
        }

    def _extract_public_api(self) -> Dict[str, Dict[str, Any]]:
        """Extract all public API elements with detailed information."""
        public_api = {}

        # Use __all__ if available, otherwise inspect all public attributes
        api_names = getattr(self.package, "__all__", [])
        if not api_names:
            api_names = [name for name in dir(self.package) if not name.startswith("_")]

        for name in api_names:
            try:
                obj = getattr(self.package, name)
                public_api[name] = self._analyze_api_element(name, obj)
            except AttributeError:
                logger.warning(f"API element {name} not found in package")
            except Exception as e:
                logger.warning(f"Failed to analyze API element {name}: {e}")

        return public_api

    def _analyze_api_element(self, name: str, obj: Any) -> Dict[str, Any]:
        """Analyze a single API element in detail."""
        element_info = {
            "name": name,
            "type": self._get_object_type(obj),
            "module": getattr(obj, "__module__", "unknown"),
            "qualname": getattr(obj, "__qualname__", name),
            "doc": inspect.getdoc(obj) or "",
            "signature": None,
            "source_file": None,
            "line_number": None,
            "is_public": not name.startswith("_")
        }

        # Extract source information
        try:
            element_info["source_file"] = inspect.getfile(obj)
            element_info["line_number"] = inspect.getsourcelines(obj)[1]
        except (OSError, TypeError):
            pass

        # Type-specific analysis
        if inspect.isclass(obj):
            element_info.update(self._analyze_class_details(obj))
        elif inspect.isfunction(obj) or inspect.ismethod(obj):
            element_info.update(self._analyze_function_details(obj))
        elif inspect.ismodule(obj):
            element_info.update(self._analyze_module_details(obj))

        return element_info

    def _get_object_type(self, obj: Any) -> str:
        """Determine the specific type of an object."""
        if inspect.isclass(obj):
            return "class"
        elif inspect.isfunction(obj):
            return "function"
        elif inspect.ismethod(obj):
            return "method"
        elif inspect.ismodule(obj):
            return "module"
        elif inspect.isbuiltin(obj):
            return "builtin"
        elif callable(obj):
            return "callable"
        else:
            return "variable"

    def _analyze_class_details(self, cls) -> Dict[str, Any]:
        """Analyze class-specific details."""
        class_info = {
            "base_classes": [base.__name__ for base in cls.__bases__],
            "mro": [c.__name__ for c in cls.__mro__],
            "methods": {},
            "class_methods": {},
            "static_methods": {},
            "properties": {},
            "descriptors": {},
            "class_variables": {}
        }

        for name, member in inspect.getmembers(cls):
            if name.startswith("_"):
                continue

            member_info = {
                "name": name,
                "doc": inspect.getdoc(member) or "",
                "defined_in": self._find_defining_class(cls, name)
            }

            if inspect.ismethod(member):
                if isinstance(inspect.getattr_static(cls, name), classmethod):
                    class_info["class_methods"][name] = member_info
                else:
                    class_info["methods"][name] = member_info
            elif inspect.isfunction(member):
                if isinstance(inspect.getattr_static(cls, name), staticmethod):
                    class_info["static_methods"][name] = member_info
                else:
                    class_info["methods"][name] = member_info
            elif isinstance(member, property):
                class_info["properties"][name] = member_info
            elif hasattr(member, "__get__") or hasattr(member, "__set__"):
                class_info["descriptors"][name] = member_info
            else:
                class_info["class_variables"][name] = member_info

            # Add signature for callable members
            if callable(member):
                try:
                    member_info["signature"] = str(inspect.signature(member))
                except (ValueError, TypeError):
                    member_info["signature"] = "unknown"

        return class_info

    def _analyze_function_details(self, func) -> Dict[str, Any]:
        """Analyze function-specific details."""
        function_info = {
            "is_async": inspect.iscoroutinefunction(func),
            "is_generator": inspect.isgeneratorfunction(func),
            "parameters": {},
            "return_annotation": None,
            "defaults": {},
            "var_positional": None,
            "var_keyword": None
        }

        try:
            sig = inspect.signature(func)
            function_info["signature"] = str(sig)

            # Analyze parameters
            for param_name, param in sig.parameters.items():
                param_info = {
                    "name": param_name,
                    "kind": param.kind.name,
                    "annotation": str(param.annotation) if param.annotation != param.empty else None,
                    "default": str(param.default) if param.default != param.empty else None,
                    "has_default": param.default != param.empty
                }
                function_info["parameters"][param_name] = param_info

                # Track special parameter types
                if param.kind == param.VAR_POSITIONAL:
                    function_info["var_positional"] = param_name
                elif param.kind == param.VAR_KEYWORD:
                    function_info["var_keyword"] = param_name

            # Return annotation
            if sig.return_annotation != sig.empty:
                function_info["return_annotation"] = str(sig.return_annotation)

        except (ValueError, TypeError):
            function_info["signature"] = "unknown"

        return function_info

    def _analyze_module_details(self, module) -> Dict[str, Any]:
        """Analyze module-specific details."""
        return {
            "file": getattr(module, "__file__", None),
            "package": getattr(module, "__package__", None),
            "all": getattr(module, "__all__", []),
            "members": [name for name in dir(module) if not name.startswith("_")]
        }

    def _find_defining_class(self, cls, method_name: str) -> str:
        """Find which class in the MRO defines a particular method."""
        for base_class in cls.__mro__:
            if method_name in base_class.__dict__:
                return base_class.__name__
        return "unknown"

    def _extract_signatures(self) -> Dict[str, str]:
        """Extract function signatures for all callable API elements."""
        signatures = {}

        api_names = getattr(self.package, "__all__", [])
        if not api_names:
            api_names = [name for name in dir(self.package) if not name.startswith("_")]

        for name in api_names:
            try:
                obj = getattr(self.package, name)
                if callable(obj):
                    try:
                        signatures[name] = str(inspect.signature(obj))
                    except (ValueError, TypeError):
                        signatures[name] = "unknown"
            except AttributeError:
                pass

        return signatures

    def _extract_type_hints(self) -> Dict[str, Dict[str, Any]]:
        """Extract type hints for API elements."""
        type_hints = {}

        api_names = getattr(self.package, "__all__", [])
        if not api_names:
            api_names = [name for name in dir(self.package) if not name.startswith("_")]

        for name in api_names:
            try:
                obj = getattr(self.package, name)
                hints = {}

                if hasattr(obj, "__annotations__"):
                    hints["annotations"] = {
                        k: str(v) for k, v in obj.__annotations__.items()
                    }

                if inspect.isfunction(obj) or inspect.ismethod(obj):
                    try:
                        sig = inspect.signature(obj)
                        param_hints = {}
                        for param_name, param in sig.parameters.items():
                            if param.annotation != param.empty:
                                param_hints[param_name] = str(param.annotation)
                        if param_hints:
                            hints["parameter_hints"] = param_hints

                        if sig.return_annotation != sig.empty:
                            hints["return_hint"] = str(sig.return_annotation)
                    except (ValueError, TypeError):
                        pass

                if hints:
                    type_hints[name] = hints

            except AttributeError:
                pass

        return type_hints

    def _extract_docstrings(self) -> Dict[str, Dict[str, str]]:
        """Extract and parse docstrings for API elements."""
        docstrings = {}

        api_names = getattr(self.package, "__all__", [])
        if not api_names:
            api_names = [name for name in dir(self.package) if not name.startswith("_")]

        for name in api_names:
            try:
                obj = getattr(self.package, name)
                doc = inspect.getdoc(obj)
                if doc:
                    docstrings[name] = {
                        "raw": doc,
                        "summary": self._extract_summary(doc),
                        "sections": self._parse_docstring_sections(doc)
                    }
            except AttributeError:
                pass

        return docstrings

    def _extract_summary(self, docstring: str) -> str:
        """Extract summary (first line) from docstring."""
        if not docstring:
            return ""
        lines = docstring.strip().split("\n")
        return lines[0].strip() if lines else ""

    def _parse_docstring_sections(self, docstring: str) -> Dict[str, str]:
        """Parse docstring sections (Args, Returns, etc.)."""
        if not docstring:
            return {}

        sections = {}
        current_section = None
        current_content = []

        lines = docstring.split("\n")
        for line in lines:
            stripped = line.strip()

            # Common docstring section headers
            if stripped.lower() in ["args:", "arguments:", "parameters:"]:
                if current_section:
                    sections[current_section] = "\n".join(current_content)
                current_section = "args"
                current_content = []
            elif stripped.lower() in ["returns:", "return:"]:
                if current_section:
                    sections[current_section] = "\n".join(current_content)
                current_section = "returns"
                current_content = []
            elif stripped.lower() in ["raises:", "except:"]:
                if current_section:
                    sections[current_section] = "\n".join(current_content)
                current_section = "raises"
                current_content = []
            elif stripped.lower() in ["examples:", "example:"]:
                if current_section:
                    sections[current_section] = "\n".join(current_content)
                current_section = "examples"
                current_content = []
            elif stripped.lower() in ["note:", "notes:"]:
                if current_section:
                    sections[current_section] = "\n".join(current_content)
                current_section = "note"
                current_content = []
            elif current_section:
                current_content.append(line)

        # Add the last section
        if current_section and current_content:
            sections[current_section] = "\n".join(current_content)

        return sections

    def _extract_inheritance_info(self) -> Dict[str, Dict[str, Any]]:
        """Extract inheritance information for classes."""
        inheritance = {}

        api_names = getattr(self.package, "__all__", [])
        if not api_names:
            api_names = [name for name in dir(self.package) if not name.startswith("_")]

        for name in api_names:
            try:
                obj = getattr(self.package, name)
                if inspect.isclass(obj):
                    inheritance[name] = {
                        "bases": [base.__name__ for base in obj.__bases__],
                        "mro": [cls.__name__ for cls in obj.__mro__],
                        "subclasses": [sub.__name__ for sub in obj.__subclasses__()]
                    }
            except AttributeError:
                pass

        return inheritance

    def _extract_decorators(self) -> Dict[str, List[str]]:
        """Extract decorator information for functions and methods."""
        decorators = {}

        # This is challenging to extract at runtime
        # We would need to analyze the source code with AST
        # For now, return empty dict - this could be enhanced later

        return decorators