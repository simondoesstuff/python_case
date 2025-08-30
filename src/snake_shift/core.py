"""
Core refactoring functionality for Python code.
"""

from pathlib import Path
import libcst as cst
from .module_detection import ImportAnalyzer
from .transformer import RenameTransformer
from .file_operations import collect_file_renames, execute_file_renames


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


def refactor_directory(root_path: Path, rename_files: bool = False, dry_run: bool = True) -> None:
    """
    Refactor all Python files in a directory and optionally rename files/directories.
    """
    if rename_files:
        # First, collect and execute file renames
        renames = collect_file_renames(root_path, dry_run)
        if renames:
            print(f"Found {len(renames)} files/directories to rename:")
            execute_file_renames(renames, dry_run)
            print()
        
        # Update root_path if it was renamed
        if not dry_run:
            for old_path, new_path in renames:
                if old_path == root_path:
                    root_path = new_path
                    break
    
    # Then refactor Python file contents
    python_files = []
    for file_path in root_path.rglob("*.py"):
        if not file_path.name.startswith('.'):
            python_files.append(file_path)
    
    print(f"Refactoring {len(python_files)} Python files...")
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            refactored_content = refactor_source(original_content)
            
            if original_content != refactored_content:
                if dry_run:
                    print(f"Would refactor: {file_path}")
                else:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(refactored_content)
                    print(f"Refactored: {file_path}")
            
        except Exception as e:
            print(f"Error processing {file_path}: {e}")