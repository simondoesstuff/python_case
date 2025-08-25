import os
import typer
from .rename import refactor_source
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
    path: str,
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show changes without writing to files."
    ),
    to_stdout: bool = typer.Option(
        False, "--stdout", help="Print the refactored code to stdout."
    ),
):
    """
    Refactor a Python file or directory to Pythonic naming conventions.
    """
    if os.path.isfile(path):
        if path.endswith(".py"):
            process_file(path, dry_run, to_stdout)
        else:
            print(f"Skipping non-Python file: {path}")
    elif os.path.isdir(path):
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    process_file(file_path, dry_run, to_stdout)
    else:
        print(f"Error: Path '{path}' is not a valid file or directory.")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()