"""
Core refactoring functionality for Python code.
"""

import shutil
from pathlib import Path

import libcst as cst
from rich.console import Console
from rich.progress import Progress

from .file_operations import (
    _is_ignored,
    _load_gitignore_patterns,
    collect_file_renames,
)
from .module_detection import ImportAnalyzer
from .transformer import RenameTransformer

console = Console()


class RefactorError(Exception):
    """Base exception for refactoring errors."""

    pass


class ParseError(RefactorError):
    """Exception raised when code cannot be parsed."""

    pass


def refactor_source(source: str) -> str:
    """
    Refactors Python source code using LibCST for better analysis.

    Args:
        source: The Python source code to refactor

    Returns:
        The refactored source code

    Raises:
        ParseError: If the source code cannot be parsed
    """
    if not source.strip():
        return source

    try:
        tree = (
            cst.parse_expression(source)
            if source.strip().startswith("(")
            else cst.parse_module(source)
        )
    except Exception as e:
        try:
            # Fallback to module parsing if expression parsing fails
            tree = cst.parse_module(source)
        except Exception as parse_error:
            raise ParseError(f"Failed to parse source code: {parse_error}") from e

    # First pass: analyze imports to identify external modules
    import_analyzer = ImportAnalyzer()
    tree.visit(import_analyzer)

    # Second pass: transform the code
    transformer = RenameTransformer(
        import_analyzer.external_modules, import_analyzer.internal_aliases
    )
    new_tree = tree.visit(transformer)

    return new_tree.code


def refactor_directory(
    root_path: Path,
    rename_files: bool = False,
    dry_run: bool = True,
    verbose: bool = False,
) -> None:
    """
    Refactor all Python files in a directory and optionally rename files/directories.

    Args:
        root_path: Root directory to refactor
        rename_files: Whether to rename files and directories
        dry_run: Whether to preview changes only
        verbose: Whether to show detailed output
    """
    ignore_patterns = _load_gitignore_patterns(root_path)

    with Progress() as progress:
        if rename_files:
            # First, collect and execute file renames
            console.print("[bold blue]Collecting files to rename...[/bold blue]")
            renames = collect_file_renames(root_path, dry_run)

            if renames:
                console.print(
                    f"[green]Found {len(renames)} files/directories to rename[/green]"
                )

                rename_task = progress.add_task(
                    "[cyan]Renaming files...", total=len(renames)
                )
                for old_path, new_path in renames:
                    if dry_run:
                        console.print(
                            f"[yellow]Would rename:[/yellow] {old_path} → {new_path}"
                        )
                    else:
                        try:
                            if old_path.is_dir():
                                shutil.move(str(old_path), str(new_path))
                            else:
                                old_path.rename(new_path)
                            if verbose:
                                console.print(
                                    f"[green]Renamed:[/green] {old_path} → {new_path}"
                                )
                        except Exception as e:
                            console.print(f"[red]Error renaming {old_path}:[/red] {e}")

                    progress.update(rename_task, advance=1)

                # Update root_path if it was renamed
                if not dry_run:
                    for old_path, new_path in renames:
                        if old_path == root_path:
                            root_path = new_path
                            break
            else:
                console.print("[dim]No files need renaming[/dim]")

        # Then refactor Python file contents
        console.print("[bold blue]Collecting Python files...[/bold blue]")
        python_files = []

        for file_path in root_path.rglob("*.py"):
            # Skip ignored files and hidden files
            if not file_path.name.startswith(".") and not _is_ignored(
                file_path, root_path, ignore_patterns
            ):
                python_files.append(file_path)

        if not python_files:
            console.print("[dim]No Python files found to refactor[/dim]")
            return

        console.print(
            f"[green]Found {len(python_files)} Python files to process[/green]"
        )

        refactor_task = progress.add_task(
            "[magenta]Refactoring files...", total=len(python_files)
        )
        refactored_count = 0
        error_count = 0

        for file_path in python_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    original_content = f.read()

                refactored_content = refactor_source(original_content)

                if original_content != refactored_content:
                    refactored_count += 1
                    if dry_run:
                        if verbose:
                            console.print(
                                f"[yellow]Would refactor:[/yellow] {file_path}"
                            )
                    else:
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(refactored_content)
                        if verbose:
                            console.print(f"[green]Refactored:[/green] {file_path}")

            except ParseError as e:
                error_count += 1
                console.print(f"[red]Parse error in {file_path}:[/red] {e}")
            except Exception as e:
                error_count += 1
                console.print(f"[red]Error processing {file_path}:[/red] {e}")

            progress.update(refactor_task, advance=1)

    # Summary
    if refactored_count > 0:
        action = "Would refactor" if dry_run else "Refactored"
        console.print(f"[bold green]✓ {action} {refactored_count} files[/bold green]")
    else:
        console.print("[dim]No files needed refactoring[/dim]")

    if error_count > 0:
        console.print(f"[bold red]✗ {error_count} errors encountered[/bold red]")

