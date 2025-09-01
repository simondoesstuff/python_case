import os
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich import print as rich_print
import difflib

from .core import refactor_source, refactor_directory, ParseError, RefactorError
from .file_operations import _load_gitignore_patterns, _is_ignored

app = typer.Typer()
console = Console()


class FileError(RefactorError):
    """Exception raised for file operation errors."""
    pass


def process_file(file_path: str, dry_run: bool, to_stdout: bool, verbose: bool = False) -> bool:
    """
    Processes a single file.
    
    Args:
        file_path: Path to the file to process
        dry_run: Whether to preview changes only
        to_stdout: Whether to output to stdout
        verbose: Whether to show detailed output
        
    Returns:
        True if file was processed successfully, False otherwise
    """
    path_obj = Path(file_path)
    
    if not to_stdout and verbose:
        console.print(f"[blue]Processing[/blue] {file_path}")
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            original_source = f.read()
    except UnicodeDecodeError as e:
        console.print(f"[red]Encoding error reading {file_path}:[/red] {e}")
        return False
    except Exception as e:
        console.print(f"[red]Error reading file {file_path}:[/red] {e}")
        return False

    try:
        new_source = refactor_source(original_source)
    except ParseError as e:
        console.print(f"[red]Parse error in {file_path}:[/red] {e}")
        return False
    except Exception as e:
        console.print(f"[red]Error refactoring file {file_path}:[/red] {e}")
        return False

    if to_stdout:
        console.print(new_source)
        return True

    if original_source == new_source:
        if verbose:
            console.print(f"[dim]No changes needed for {file_path}[/dim]")
        return True

    if dry_run:
        console.print(f"[yellow]Changes for {file_path}:[/yellow]")
        diff = difflib.unified_diff(
            original_source.splitlines(keepends=True),
            new_source.splitlines(keepends=True),
            fromfile=f"{file_path} (original)",
            tofile=f"{file_path} (refactored)",
        )
        console.print("".join(diff))
    else:
        if verbose:
            console.print(f"[green]Refactoring[/green] {file_path}")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_source)
        except Exception as e:
            console.print(f"[red]Error writing to file {file_path}:[/red] {e}")
            return False
    
    return True

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
    
    Respects .gitignore patterns and common ignore patterns.
    
    Examples:
        snake-shift my_file.py --dry-run
        snake-shift src/ --rename-files --verbose
        snake-shift project/ --rename-files
    """
    path_obj = Path(path)
    
    if not path_obj.exists():
        console.print(f"[red]Error: Path '{path}' does not exist.[/red]")
        raise typer.Exit(code=1)
    
    if path_obj.is_file():
        if not path.endswith(".py"):
            console.print(f"[red]Error: '{path}' is not a Python file.[/red]")
            raise typer.Exit(code=1)
        
        # Check if file should be ignored (for single files, use parent directory for .gitignore)
        parent_dir = path_obj.parent
        ignore_patterns = _load_gitignore_patterns(parent_dir)
        
        if _is_ignored(path_obj, parent_dir, ignore_patterns):
            console.print(f"[yellow]Skipping ignored file: {path}[/yellow]")
            return
        
        success = process_file(path, dry_run, to_stdout, verbose)
        if not success:
            raise typer.Exit(code=1)
            
    elif path_obj.is_dir():
        if to_stdout:
            console.print("[red]Error: --stdout option is only supported for single files.[/red]")
            raise typer.Exit(code=1)
        
        try:
            refactor_directory(path_obj, rename_files=rename_files, dry_run=dry_run, verbose=verbose)
        except KeyboardInterrupt:
            console.print("\n[yellow]Operation cancelled by user[/yellow]")
            raise typer.Exit(code=1)
        except Exception as e:
            console.print(f"[red]Error processing directory: {e}[/red]")
            raise typer.Exit(code=1)
    else:
        console.print(f"[red]Error: Path '{path}' is not a valid file or directory.[/red]")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()