"""Package structure analysis for ultrathink documentation system."""

import ast
import importlib
import inspect
import sys
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Union
import logging

logger = logging.getLogger(__name__)


class PackageAnalyzer:
    """Analyzes Python package structure and extracts metadata for documentation."""

    def __init__(self, package_name: str, source_directory: str):
        """Initialize the package analyzer.

        Args:
            package_name: Name of the package to analyze (e.g., 'gapless_crypto_data')
            source_directory: Path to the source directory (e.g., 'src/gapless_crypto_data')
        """
        self.package_name = package_name
        self.source_directory = Path(source_directory)
        self.package_info = {}
        self.module_tree = {}
        self.public_api = {}

    def analyze_package(self) -> Dict[str, Any]:
        """Perform comprehensive package analysis.

        Returns:
            Dictionary containing complete package analysis results.
        """
        logger.info(f"Starting analysis of package: {self.package_name}")

        try:
            # Import the package to get runtime information
            package = importlib.import_module(self.package_name)

            analysis_result = {
                "package_info": self._extract_package_info(package),
                "module_tree": self._build_module_tree(),
                "public_api": self._extract_public_api(package),
                "file_structure": self._analyze_file_structure(),
                "dependencies": self._extract_dependencies(),
                "metadata": self._extract_metadata(package)
            }

            logger.info("Package analysis completed successfully")
            return analysis_result

        except ImportError as e:
            logger.error(f"Failed to import package {self.package_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Package analysis failed: {e}")
            raise

    def _extract_package_info(self, package) -> Dict[str, Any]:
        """Extract basic package information."""
        info = {
            "name": getattr(package, "__name__", self.package_name),
            "version": getattr(package, "__version__", "unknown"),
            "author": getattr(package, "__author__", "unknown"),
            "email": getattr(package, "__email__", "unknown"),
            "file": getattr(package, "__file__", None),
            "package_dir": str(self.source_directory),
            "docstring": inspect.getdoc(package) or "",
            "all_exports": getattr(package, "__all__", [])
        }

        logger.debug(f"Extracted package info: {info['name']} v{info['version']}")
        return info

    def _build_module_tree(self) -> Dict[str, Any]:
        """Build a tree structure of all modules in the package."""
        module_tree = {}

        if not self.source_directory.exists():
            logger.warning(f"Source directory does not exist: {self.source_directory}")
            return module_tree

        for py_file in self.source_directory.rglob("*.py"):
            if py_file.name.startswith("_") and py_file.name != "__init__.py":
                continue  # Skip private modules

            relative_path = py_file.relative_to(self.source_directory)
            module_path = str(relative_path.with_suffix("")).replace("/", ".")

            # Skip __pycache__ and test files
            if "__pycache__" in str(relative_path) or "test" in py_file.name.lower():
                continue

            module_info = self._analyze_module_file(py_file)
            module_tree[module_path] = module_info

        logger.debug(f"Built module tree with {len(module_tree)} modules")
        return module_tree

    def _analyze_module_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a single Python module file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)

            module_info = {
                "file_path": str(file_path),
                "docstring": ast.get_docstring(tree) or "",
                "classes": [],
                "functions": [],
                "imports": [],
                "constants": [],
                "all_exports": []
            }

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    module_info["classes"].append({
                        "name": node.name,
                        "docstring": ast.get_docstring(node) or "",
                        "line_number": node.lineno,
                        "is_public": not node.name.startswith("_")
                    })
                elif isinstance(node, ast.FunctionDef):
                    module_info["functions"].append({
                        "name": node.name,
                        "docstring": ast.get_docstring(node) or "",
                        "line_number": node.lineno,
                        "is_public": not node.name.startswith("_"),
                        "is_async": isinstance(node, ast.AsyncFunctionDef)
                    })
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        module_info["imports"].append({
                            "module": alias.name,
                            "alias": alias.asname,
                            "type": "import"
                        })
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        module_info["imports"].append({
                            "module": node.module,
                            "name": alias.name,
                            "alias": alias.asname,
                            "type": "from_import"
                        })
                elif isinstance(node, ast.Assign):
                    # Look for __all__ and constants
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            if target.id == "__all__":
                                if isinstance(node.value, ast.List):
                                    module_info["all_exports"] = [
                                        elt.s for elt in node.value.elts
                                        if isinstance(elt, ast.Str)
                                    ]
                            elif target.id.isupper():  # Convention for constants
                                module_info["constants"].append({
                                    "name": target.id,
                                    "line_number": node.lineno
                                })

            return module_info

        except Exception as e:
            logger.warning(f"Failed to analyze module {file_path}: {e}")
            return {
                "file_path": str(file_path),
                "docstring": "",
                "classes": [],
                "functions": [],
                "imports": [],
                "constants": [],
                "all_exports": [],
                "error": str(e)
            }

    def _extract_public_api(self, package) -> Dict[str, Any]:
        """Extract the public API of the package."""
        public_api = {
            "classes": {},
            "functions": {},
            "constants": {},
            "modules": {}
        }

        # Get the __all__ exports if available
        all_exports = getattr(package, "__all__", [])

        # If __all__ is defined, use it to determine public API
        if all_exports:
            for name in all_exports:
                try:
                    obj = getattr(package, name)
                    api_info = self._analyze_api_object(name, obj)

                    if inspect.isclass(obj):
                        public_api["classes"][name] = api_info
                    elif inspect.isfunction(obj):
                        public_api["functions"][name] = api_info
                    elif inspect.ismodule(obj):
                        public_api["modules"][name] = api_info
                    else:
                        public_api["constants"][name] = api_info

                except AttributeError:
                    logger.warning(f"Object {name} in __all__ not found in package")
        else:
            # Fallback: analyze all public attributes
            for name in dir(package):
                if not name.startswith("_"):
                    try:
                        obj = getattr(package, name)
                        api_info = self._analyze_api_object(name, obj)

                        if inspect.isclass(obj):
                            public_api["classes"][name] = api_info
                        elif inspect.isfunction(obj):
                            public_api["functions"][name] = api_info
                        elif inspect.ismodule(obj):
                            public_api["modules"][name] = api_info
                        else:
                            public_api["constants"][name] = api_info

                    except Exception as e:
                        logger.warning(f"Failed to analyze object {name}: {e}")

        logger.debug(f"Extracted public API: {len(public_api['classes'])} classes, "
                    f"{len(public_api['functions'])} functions, "
                    f"{len(public_api['modules'])} modules")

        return public_api

    def _analyze_api_object(self, name: str, obj: Any) -> Dict[str, Any]:
        """Analyze a single API object and extract metadata."""
        api_info = {
            "name": name,
            "type": type(obj).__name__,
            "module": getattr(obj, "__module__", "unknown"),
            "docstring": inspect.getdoc(obj) or "",
            "file": inspect.getfile(obj) if hasattr(obj, "__file__") else None,
            "line_number": None
        }

        try:
            api_info["line_number"] = inspect.getsourcelines(obj)[1]
        except (OSError, TypeError):
            pass

        if inspect.isclass(obj):
            api_info.update(self._analyze_class(obj))
        elif inspect.isfunction(obj):
            api_info.update(self._analyze_function(obj))
        elif inspect.ismodule(obj):
            api_info.update(self._analyze_module(obj))

        return api_info

    def _analyze_class(self, cls) -> Dict[str, Any]:
        """Analyze a class object."""
        class_info = {
            "base_classes": [base.__name__ for base in cls.__bases__],
            "methods": {},
            "properties": {},
            "class_variables": {}
        }

        for name, method in inspect.getmembers(cls):
            if not name.startswith("_"):  # Public methods only
                if inspect.ismethod(method) or inspect.isfunction(method):
                    class_info["methods"][name] = {
                        "docstring": inspect.getdoc(method) or "",
                        "signature": str(inspect.signature(method)) if hasattr(inspect, "signature") else "unknown"
                    }
                elif isinstance(method, property):
                    class_info["properties"][name] = {
                        "docstring": inspect.getdoc(method) or ""
                    }

        return class_info

    def _analyze_function(self, func) -> Dict[str, Any]:
        """Analyze a function object."""
        function_info = {}

        try:
            function_info["signature"] = str(inspect.signature(func))
        except (ValueError, TypeError):
            function_info["signature"] = "unknown"

        try:
            function_info["source_file"] = inspect.getfile(func)
            function_info["source_lines"] = inspect.getsourcelines(func)[1]
        except (OSError, TypeError):
            pass

        return function_info

    def _analyze_module(self, module) -> Dict[str, Any]:
        """Analyze a module object."""
        return {
            "file": getattr(module, "__file__", None),
            "package": getattr(module, "__package__", None),
            "all_exports": getattr(module, "__all__", [])
        }

    def _analyze_file_structure(self) -> Dict[str, Any]:
        """Analyze the physical file structure of the package."""
        structure = {
            "total_files": 0,
            "python_files": 0,
            "directories": 0,
            "file_sizes": {},
            "structure_tree": {}
        }

        if not self.source_directory.exists():
            return structure

        def build_tree(path: Path, current_tree: Dict):
            for item in path.iterdir():
                if item.name.startswith(".") or item.name == "__pycache__":
                    continue

                if item.is_directory():
                    structure["directories"] += 1
                    current_tree[item.name] = {}
                    build_tree(item, current_tree[item.name])
                else:
                    structure["total_files"] += 1
                    if item.suffix == ".py":
                        structure["python_files"] += 1

                    file_size = item.stat().st_size
                    structure["file_sizes"][str(item.relative_to(self.source_directory))] = file_size
                    current_tree[item.name] = {"size": file_size, "type": "file"}

        build_tree(self.source_directory, structure["structure_tree"])
        return structure

    def _extract_dependencies(self) -> Dict[str, List[str]]:
        """Extract package dependencies from imports."""
        dependencies = {
            "standard_library": [],
            "third_party": [],
            "internal": []
        }

        # This is a simplified implementation
        # In practice, you might want to use tools like pipdeptree or analyze setup.py/pyproject.toml

        for module_info in self.module_tree.values():
            for import_info in module_info.get("imports", []):
                module_name = import_info.get("module", "")
                if module_name:
                    if module_name.startswith(self.package_name):
                        dependencies["internal"].append(module_name)
                    elif module_name in sys.stdlib_module_names:
                        dependencies["standard_library"].append(module_name)
                    else:
                        dependencies["third_party"].append(module_name)

        # Remove duplicates and sort
        for key in dependencies:
            dependencies[key] = sorted(list(set(dependencies[key])))

        return dependencies

    def _extract_metadata(self, package) -> Dict[str, Any]:
        """Extract additional metadata about the package."""
        metadata = {
            "analysis_timestamp": None,
            "python_version": sys.version,
            "package_location": str(self.source_directory),
            "has_tests": (self.source_directory.parent / "tests").exists(),
            "has_docs": (self.source_directory.parent / "docs").exists(),
            "has_examples": (self.source_directory.parent / "examples").exists(),
            "total_lines_of_code": 0
        }

        # Count lines of code
        for py_file in self.source_directory.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    metadata["total_lines_of_code"] += len(f.readlines())
            except Exception:
                pass

        import datetime
        metadata["analysis_timestamp"] = datetime.datetime.now().isoformat()

        return metadata