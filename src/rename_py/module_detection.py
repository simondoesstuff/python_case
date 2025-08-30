"""
Module detection utilities for distinguishing external vs internal modules.
"""

import sys
import importlib.util
from typing import Set, Dict
import libcst as cst


def _get_module_name_from_node(node) -> str:
    """Extract module name string from CST node."""
    if isinstance(node, cst.Name):
        return node.value
    elif isinstance(node, cst.Attribute):
        parts = []
        current = node
        while isinstance(current, cst.Attribute):
            parts.append(current.attr.value)
            current = current.value
        if isinstance(current, cst.Name):
            parts.append(current.value)
        return '.'.join(reversed(parts))
    else:
        return ""


def _is_external_module(module_name: str) -> bool:
    """Check if a module is external (installed/standard library) vs internal (local)."""
    if not module_name:
        return False
        
    root_module = module_name.split('.')[0]
    
    # Check if module is in sys.modules (already loaded)
    if root_module in sys.modules:
        module = sys.modules[root_module]
        # Built-in modules don't have __file__
        if not hasattr(module, '__file__') or module.__file__ is None:
            return True
        # Check if it's in standard library (python install dir) or site-packages
        if module.__file__:
            file_path = module.__file__
            if ('site-packages' in file_path or 'dist-packages' in file_path or
                '/lib/python' in file_path or '\\lib\\python' in file_path):
                return True
    
    # Try to find module spec
    try:
        spec = importlib.util.find_spec(root_module)
        if spec is not None and spec.origin:
            # Built-in modules
            if spec.origin == 'built-in':
                return True
            # Check if it's in standard library or site-packages
            if (spec.origin and ('site-packages' in spec.origin or 
                                'dist-packages' in spec.origin or
                                '/lib/python' in spec.origin or
                                '\\lib\\python' in spec.origin)):
                return True
        elif spec is None:
            # Module not found - could be internal (local) or external (uninstalled)
            # Be conservative and assume it's internal unless it matches known patterns
            common_external = {
                'numpy', 'torch', 'tensorflow', 'sklearn', 'pandas', 'matplotlib',
                'scipy', 'keras', 'cv2', 'PIL', 'requests', 'flask', 'django',
                'boto3', 'pymongo', 'sqlalchemy', 'redis', 'celery', 'click',
                'typer', 'fastapi', 'pydantic'
            }
            if root_module in common_external:
                return True
    except (ImportError, ModuleNotFoundError, ValueError):
        # If we can't find the module, assume it might be external
        return True
    
    return False


class ImportAnalyzer(cst.CSTVisitor):
    """Analyzes imports to distinguish internal vs external modules."""
    
    def __init__(self):
        self.external_modules: Set[str] = set()
        self.internal_aliases: Dict[str, str] = {}
        self.relative_imports: Set[str] = set()
        
    def visit_ImportFrom(self, node: cst.ImportFrom) -> None:
        if node.module is None:
            return
            
        # Handle relative imports (internal)
        if node.relative:
            module_name = _get_module_name_from_node(node.module) if node.module else ""
            self.relative_imports.add(module_name)
            if node.names and not isinstance(node.names, cst.ImportStar):
                for alias in node.names:
                    if isinstance(alias, cst.ImportAlias):
                        imported_name = alias.name.value
                        alias_name = alias.asname.name.value if alias.asname else imported_name
                        self.internal_aliases[alias_name] = imported_name
        else:
            # Check if module is external using environment detection
            module_name = _get_module_name_from_node(node.module)
            root_module = module_name.split('.')[0]
            
            if _is_external_module(root_module):
                self.external_modules.add(root_module)
                # Add imported names from external modules as external
                if node.names and not isinstance(node.names, cst.ImportStar):
                    for alias in node.names:
                        if isinstance(alias, cst.ImportAlias):
                            imported_name = alias.name.value
                            alias_name = alias.asname.name.value if alias.asname else imported_name
                            self.external_modules.add(alias_name)
    
    def visit_Import(self, node: cst.Import) -> None:
        for alias in node.names:
            if isinstance(alias, cst.ImportAlias):
                module_name = _get_module_name_from_node(alias.name)
                root_module = module_name.split('.')[0]
                
                if _is_external_module(root_module):
                    alias_name = alias.asname.name.value if alias.asname else root_module
                    self.external_modules.add(alias_name)