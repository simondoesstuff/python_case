import ast
import re

def to_snake_case(name: str) -> str:
    """Converts a string to snake_case."""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def to_pascal_case(name: str) -> str:
    """Converts a string to PascalCase."""
    # First, convert camelCase to snake_case
    snake_case_name = to_snake_case(name)
    return ''.join(word.capitalize() for word in snake_case_name.split('_'))

class RenameTransformer(ast.NodeTransformer):
    """
    AST transformer to rename nodes to Pythonic conventions.
    """
    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        node.name = to_pascal_case(node.name)
        self.generic_visit(node)
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        node.name = to_snake_case(node.name)
        for arg in node.args.args:
            arg.arg = to_snake_case(arg.arg)
        self.generic_visit(node)
        return node

    def visit_Name(self, node: ast.Name) -> ast.Name:
        if isinstance(node.ctx, ast.Store):
            node.id = to_snake_case(node.id)
        return node

def refactor_file(file_path: str):
    """
    Refactors a single Python file.
    """
    with open(file_path, 'r') as f:
        source = f.read()
    
    tree = ast.parse(source)
    transformer = RenameTransformer()
    new_tree = transformer.visit(tree)
    ast.fix_missing_locations(new_tree)
    
    new_source = ast.unparse(new_tree)
    
    with open(file_path, 'w') as f:
        f.write(new_source)
