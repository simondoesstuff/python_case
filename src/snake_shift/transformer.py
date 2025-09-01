"""
LibCST transformer for renaming Python code to Pythonic conventions.
"""

from typing import Set, Dict, List, Optional
import libcst as cst
from .naming import to_snake_case, to_pascal_case, _is_pascalcase


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
        
        # Handle PascalCase names - assume they're class calls and normalize them
        if name and name[0].isupper():
            new_name = to_pascal_case(name)
            if name != new_name:
                # Store the rename in current scope for future references
                self.renamed_vars[-1][name] = new_name
                return updated_node.with_changes(value=new_name)
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