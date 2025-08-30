import os
import typer
from pathlib import Path
from .core import refactor_source, refactor_directory
import difflib

app = typer.Typer()

def process_file(file_path: str, dry_run: bool, to_stdout: bool):
    """Processes a single file."""
    if not to_stdout:
        print(f"Processing {file_path}...")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            original_source = f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return

    try:
        new_source = refactor_source(original_source)
    except Exception as e:
        print(f"Error refactoring file {file_path}: {e}")
        return

    if to_stdout:
        print(new_source)
        return

    if original_source == new_source:
        print(f"No changes needed for {file_path}")
        return

    if dry_run:
        print(f"Changes for {file_path}:")
        diff = difflib.unified_diff(
            original_source.splitlines(keepends=True),
            new_source.splitlines(keepends=True),
            fromfile=f"{file_path} (original)",
            tofile=f"{file_path} (refactored)",
        )
        print("".join(diff))
    else:
        print(f"Refactoring {file_path}")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_source)
        except Exception as e:
            print(f"Error writing to file {file_path}: {e}")

@app.command()
def main(
    path: str = typer.Argument(help="Path to Python file or directory to refactor"),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n", help="Show changes without writing to files."
    ),
    to_stdout: bool = typer.Option(
        False, "--stdout", help="Print the refactored code to stdout (single files only)."
    ),
    rename_files: bool = typer.Option(
        False, "--rename-files", "-r", help="Also rename files and directories to pythonic conventions."
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed output during processing."
    ),
):
    """
    Refactor Python code to Pythonic naming conventions.
    
    Converts camelCase to snake_case for variables/functions and PascalCase for classes,
    while preserving external library calls and PascalCase imports.
    
    Examples:
        snake-shift my_file.py --dry-run
        snake-shift src/ --rename-files --verbose
        snake-shift project/ --rename-files
    """
    path_obj = Path(path)
    
    if not path_obj.exists():
        print(f"Error: Path '{path}' does not exist.")
        raise typer.Exit(code=1)
    
    if path_obj.is_file():
        if not path.endswith(".py"):
            print(f"Error: '{path}' is not a Python file.")
            raise typer.Exit(code=1)
        process_file(path, dry_run, to_stdout)
    elif path_obj.is_dir():
        if to_stdout:
            print("Error: --stdout option is only supported for single files.")
            raise typer.Exit(code=1)
        if rename_files:
            refactor_directory(path_obj, rename_files=True, dry_run=dry_run)
        else:
            # Use the original file-by-file approach for directories without file renaming
            for root, _, files in os.walk(path):
                for file in files:
                    if file.endswith(".py"):
                        file_path = os.path.join(root, file)
                        process_file(file_path, dry_run, False)
    else:
        print(f"Error: Path '{path}' is not a valid file or directory.")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()