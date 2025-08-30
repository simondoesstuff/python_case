"""
File and directory operations for Python refactoring.
"""

import os
from pathlib import Path
from typing import List, Tuple
from .naming import to_snake_case, _is_pascalcase


def should_rename_file(file_path: Path) -> bool:
    """Check if a file/directory should be renamed based on naming conventions."""
    name = file_path.name
    
    # Skip special files and directories
    if name.startswith('.') or name.startswith('__'):
        return False
    
    # Skip common config files
    skip_files = {
        'pyproject.toml', 'setup.py', 'requirements.txt', 'README.md',
        'LICENSE', 'MANIFEST.in', 'Dockerfile', 'docker-compose.yml'
    }
    if name in skip_files:
        return False
    
    # For Python files, check the name without extension
    if file_path.suffix == '.py':
        base_name = file_path.stem
        if base_name != to_snake_case(base_name) and not _is_pascalcase(base_name):
            return True
    
    # For directories (or potential directories - no suffix), check if they need snake_case conversion
    elif not file_path.suffix:  # No file extension means it's likely a directory
        if name != to_snake_case(name) and not _is_pascalcase(name):
            return True
    
    return False


def get_new_file_path(file_path: Path) -> Path:
    """Get the new path for a file/directory after renaming."""
    if file_path.suffix == '.py':
        # Python files: convert to snake_case unless PascalCase (likely a class module)
        base_name = file_path.stem
        if _is_pascalcase(base_name):
            new_name = base_name  # Keep PascalCase for class modules
        else:
            new_name = to_snake_case(base_name)
        return file_path.parent / f"{new_name}.py"
    else:
        # Directories: preserve PascalCase, otherwise convert to snake_case
        name = file_path.name
        if _is_pascalcase(name):
            new_name = name  # Keep PascalCase directories
        else:
            new_name = to_snake_case(name)
        return file_path.parent / new_name


def collect_file_renames(root_path: Path, dry_run: bool = True) -> List[Tuple[Path, Path]]:
    """
    Collect all file/directory renames needed in a directory tree.
    Returns list of (old_path, new_path) tuples.
    """
    renames = []
    
    # Walk directory tree bottom-up to handle nested renames properly
    for dirpath, dirnames, filenames in os.walk(root_path, topdown=False):
        current_dir = Path(dirpath)
        
        # Check files first
        for filename in filenames:
            file_path = current_dir / filename
            if should_rename_file(file_path):
                new_path = get_new_file_path(file_path)
                if file_path != new_path:
                    renames.append((file_path, new_path))
        
        # Check directories
        for dirname in dirnames:
            dir_path = current_dir / dirname
            if should_rename_file(dir_path):
                new_path = get_new_file_path(dir_path)
                if dir_path != new_path:
                    renames.append((dir_path, new_path))
    
    return renames


def execute_file_renames(renames: List[Tuple[Path, Path]], dry_run: bool = True) -> None:
    """Execute the file/directory renames."""
    for old_path, new_path in renames:
        if dry_run:
            print(f"Would rename: {old_path} → {new_path}")
        else:
            try:
                old_path.rename(new_path)
                print(f"Renamed: {old_path} → {new_path}")
            except Exception as e:
                print(f"Error renaming {old_path}: {e}")