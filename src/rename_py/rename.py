import re
import sys
import importlib.util
from typing import Set, Dict, List, Optional
import libcst as cst
from libcst import matchers as m


def to_snake_case(name: str) -> str:
    """Converts a string to snake_case."""
    if not name:
        return ""
    
    if name.startswith('__') and name.endswith('__'):
        return name

    leading_underscores = len(name) - len(name.lstrip('_'))
    
    name = name.lstrip('_')
    # Add an underscore before any uppercase letter, except at the start
    s1 = re.sub(r"([A-Z]+)", r"_\1", name)
    # Handle cases where there's an uppercase letter after a lowercase letter or number
    s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1)
    
    return "_" * leading_underscores + s2.lower().lstrip('_')


def to_pascal_case(name: str) -> str:
    """Converts a string to PascalCase."""
    snake_case_name = to_snake_case(name)
    return ''.join(word.capitalize() for word in snake_case_name.split('_'))


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


class RenameTransformer(cst.CSTTransformer):
    """LibCST transformer to rename nodes to Pythonic conventions."""
    
    def __init__(self, external_modules: Set[str], internal_aliases: Dict[str, str]):
        self.external_modules = external_modules
        self.internal_aliases = internal_aliases
        self.renamed_vars: List[Dict[str, str]] = [{}]
        self.class_names: Set[str] = set()
        self.function_names: Set[str] = set()
        self.processed_names: Set[int] = set()  # Track processed node IDs
        
    def visit_ClassDef(self, node: cst.ClassDef) -> cst.ClassDef:
        # Just enter new scope
        self.renamed_vars.append({})
        return node
    
    def leave_ClassDef(self, original_node: cst.ClassDef, updated_node: cst.ClassDef) -> cst.ClassDef:
        original_name = original_node.name.value
        new_name = to_pascal_case(original_name)  # Classes should be PascalCase
        self.class_names.add(new_name)
        self.renamed_vars.pop()
        return updated_node.with_changes(name=cst.Name(new_name))
        
    def visit_FunctionDef(self, node: cst.FunctionDef) -> cst.FunctionDef:
        # Just enter new scope
        self.renamed_vars.append({})
        return node
    
    def leave_FunctionDef(self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef) -> cst.FunctionDef:
        original_name = original_node.name.value
        new_name = to_snake_case(original_name)  # Functions should be snake_case
        self.function_names.add(new_name)
        
        # Rename function parameters
        new_params = []
        if updated_node.params.params:
            for param in updated_node.params.params:
                original_param = param.name.value
                new_param = to_snake_case(original_param)
                if original_param != new_param:
                    self.renamed_vars[-1][original_param] = new_param
                new_params.append(param.with_changes(name=cst.Name(new_param)))
            
        new_params_obj = updated_node.params.with_changes(params=new_params) if new_params else updated_node.params
        self.renamed_vars.pop()
        return updated_node.with_changes(name=cst.Name(new_name), params=new_params_obj)
        
    def leave_Name(self, original_node: cst.Name, updated_node: cst.Name) -> cst.Name:
        # Skip if this name was already processed by a class/function definition
        if id(updated_node) in self.processed_names:
            return updated_node
            
        name = updated_node.value
        
        # Check if this name was renamed in current scope
        for scope in reversed(self.renamed_vars):
            if name in scope:
                return updated_node.with_changes(value=scope[name])
        
        # Don't rename if it's an external module or known class/function
        if (name in self.external_modules or 
            name in self.class_names or 
            name in self.function_names):
            return updated_node
            
        # Rename variables to snake_case
        new_name = to_snake_case(name)
        if name != new_name:
            # Store the rename in current scope for future references
            self.renamed_vars[-1][name] = new_name
            return updated_node.with_changes(value=new_name)
            
        return updated_node
        
    def visit_Attribute(self, node: cst.Attribute) -> Optional[cst.Attribute]:
        # Don't visit children of external library attributes
        if isinstance(node.value, cst.Name):
            obj_name = node.value.value
            if obj_name in self.external_modules:
                return False  # Don't visit children
        return node
        
    def leave_Attribute(self, original_node: cst.Attribute, updated_node: cst.Attribute) -> cst.Attribute:
        attr_name = updated_node.attr.value
        
        # Check if the object is external (don't rename external library attributes)
        if isinstance(updated_node.value, cst.Name):
            obj_name = updated_node.value.value
            if obj_name in self.external_modules:
                return updated_node
        
        # Only rename self attributes to be conservative
        if (isinstance(updated_node.value, cst.Name) and 
            updated_node.value.value == 'self'):
            new_attr = to_snake_case(attr_name)
            return updated_node.with_changes(attr=cst.Name(new_attr))
            
        return updated_node


def refactor_source(source: str) -> str:
    """
    Refactors Python source code using LibCST for better analysis.
    """
    try:
        tree = cst.parse_expression(source) if source.strip().startswith('(') else cst.parse_module(source)
    except Exception:
        # Fallback to module parsing if expression parsing fails
        tree = cst.parse_module(source)
    
    # First pass: analyze imports to identify external modules
    import_analyzer = ImportAnalyzer()
    tree.visit(import_analyzer)
    
    # Second pass: transform the code
    transformer = RenameTransformer(
        import_analyzer.external_modules,
        import_analyzer.internal_aliases
    )
    new_tree = tree.visit(transformer)
    
    return new_tree.code