import ast
import re

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

class RenameTransformer(ast.NodeTransformer):
    """
    AST transformer to rename nodes to Pythonic conventions.
    """
    def __init__(self):
        self.renamed_vars = [set()]

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        node.name = to_pascal_case(node.name)
        self.renamed_vars.append(set())
        self.generic_visit(node)
        self.renamed_vars.pop()
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        node.name = to_snake_case(node.name)
        self.renamed_vars.append(set())
        for arg in node.args.args:
            original_arg = arg.arg
            new_arg = to_snake_case(original_arg)
            if original_arg != new_arg:
                self.renamed_vars[-1].add((original_arg, new_arg))
            arg.arg = new_arg
        self.generic_visit(node)
        self.renamed_vars.pop()
        return node

    def visit_Name(self, node: ast.Name) -> ast.Name:
        new_id = to_snake_case(node.id)
        if isinstance(node.ctx, ast.Store):
            if node.id != new_id:
                for scope in self.renamed_vars:
                    scope.add((node.id, new_id))
            node.id = new_id
        elif isinstance(node.ctx, ast.Load):
            for scope in reversed(self.renamed_vars):
                for old, new in scope:
                    if node.id == old:
                        node.id = new
                        break
        return node

    def visit_Attribute(self, node: ast.Attribute) -> ast.Attribute:
        if isinstance(node.value, ast.Name) and node.value.id == 'self':
            node.attr = to_snake_case(node.attr)
        self.generic_visit(node)
        return node

def refactor_source(source: str) -> str:
    """
    Refactors Python source code.
    """
    tree = ast.parse(source)
    transformer = RenameTransformer()
    new_tree = transformer.visit(tree)
    ast.fix_missing_locations(new_tree)
    
    return ast.unparse(new_tree)
