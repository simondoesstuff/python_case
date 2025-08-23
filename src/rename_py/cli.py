import os
import typer
from .rename import refactor_file

app = typer.Typer()

@app.command()
def main(path: str):
    """
    Refactor a Python file or directory to Pythonic naming conventions.
    """
    if os.path.isfile(path):
        if path.endswith('.py'):
            print(f"Refactoring {path}")
            refactor_file(path)
    elif os.path.isdir(path):
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    print(f"Refactoring {file_path}")
                    refactor_file(file_path)
    else:
        print(f"Error: Path {path} is not a valid file or directory.")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()