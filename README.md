Not yet on pypi

# Snake Shift

[![Tests](https://img.shields.io/badge/tests-95%2F64%20passing-brightgreen)](https://github.com/simondoesstuff/snake_shift)
[![Python](https://img.shields.io/badge/python-3.13%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

A powerful Python refactoring tool that converts camelCase _codebases_ to pythonic naming conventions while intelligently preserving external library calls.

## Features

- **Smart Environment Detection** - Automatically distinguishes between internal and external modules
- **Aggressive Refactoring** - Converts entire codebases while preserving external library APIs
- **File & Directory Renaming** - Renames files and directories to match pythonic conventions
  - Ignores non-code directories.
- **Gitignore Integration** - Respects .gitignore patterns and includes sensible defaults
- **PascalCase Preservation** - Keeps class names and type imports in PascalCase
- **LibCST-Powered** - Uses concrete syntax trees for accurate code transformation
- **Dry Run Support** - Preview changes before applying them

## Quick Start

```bash
# Install the tool
pip install snake-shift

# Preview changes to a single file
snake-shift my_file.py --dry-run

# Refactor code and rename files in a directory
snake-shift src/ --rename-files

# Just refactor code without renaming files
snake-shift project/ --dry-run
```

## Before & After

**Before:**

```python
# myModule.py
import pandas as pd
from myPackage.dataUtils import processData

class myClass:
    def myMethod(self, inputData):
        df = pd.DataFrame(inputData)
        processedData = processData(df.dropna())
        return processedData
```

**After:**

```python
# my_module.py
import pandas as pd
from my_package.data_utils import process_data

class MyClass:
    def my_method(self, input_data):
        df = pd.DataFrame(input_data)  # External library preserved!
        processed_data = process_data(df.dropna())
        return processed_data
```

## How It Works

### 1. Environment-Based Module Detection

Unlike other tools that use hardcoded library lists, snake-shift intelligently detects external modules by:

- Checking if modules are installed in your Python environment
- Identifying standard library modules
- Recognizing common external packages even when not installed
- Treating unknown modules as internal (local code)

### 2. Pythonic Convention Application

- **Classes** ? `PascalCase` (MyClass)
- **Functions & Variables** ? `snake_case` (my_function, my_var)
- **PascalCase Imports** ? Preserved (Dict, Path, MyClass)
- **External Library Calls** ? Untouched (pd.DataFrame, np.zeros)

### 3. File System Organization

With `--rename-files`:

- `myModule.py` ? `my_module.py`
- `dataUtils/` ? `data_utils/`
- `MyClass.py` ? `MyClass.py` (PascalCase preserved)

## Installation

```bash
pip install snake-shift
```

Or install from source:

```bash
git clone https://github.com/simondoesstuff/snake_shift.git
pip install -e .
```

## Usage

### Command Line Interface

```bash
snake-shift [OPTIONS] PATH
```

**Options:**

- `--dry-run, -n` - Show changes without writing to files
- `--rename-files, -r` - Also rename files and directories
- `--stdout` - Print refactored code to stdout (single files only)
- `--verbose, -v` - Show detailed output during processing
- `--help` - Show help message

**Examples:**

```bash
# Preview all changes to a project
snake-shift my_project/ --rename-files --dry-run

# Refactor a single file
snake-shift utils.py

# Refactor directory with file renaming
snake-shift src/ --rename-files --verbose

# Output refactored code to stdout
snake-shift my_script.py --stdout
```

### Python API

```python
from snake_shift import refactor_source, refactor_directory

# Refactor source code string
code = """
def myFunction(inputData):
    return inputData.lower()
"""
refactored = refactor_source(code)
print(refactored)
# Output: def my_function(input_data):\n    return input_data.lower()

# Refactor entire directory
from pathlib import Path
refactor_directory(
    Path("my_project/"),
    rename_files=True,
    dry_run=False
)
```

## What Gets Refactored

### Internal Code (Your Code)

- Variable names: `myVar` $\to$ `my_var`
- Function names: `myFunction` $\to$ `my_function`
- Class names: `myClass` $\to$ `MyClass`
- Module imports: `from myPackage.myModule` $\to$ `from my_package.my_module`
- File names: `myModule.py` $\to$ `my_module.py`
- Directory names: `myPackage/` $\to$ `my_package/`

### External Code (Preserved)

- Library calls: `pd.DataFrame()` stays `pd.DataFrame()`
- Standard library: `os.path.join()` stays `os.path.join()`
- PascalCase imports: `from typing import Dict` stays `Dict`
- External attributes: `model.fit()` stays `model.fit()`

## Contributing

Contributions are welcome!

### Building

```bash
# run tests with,
uv run pytest

# or just set up the environment,
uv sync

# or if you don't have UV,
pip install -r requirements.txt
pytest  # tests
```

## License

MIT Licence

## Acknowledgments

- Built with [LibCST](https://libcst.readthedocs.io/) for accurate Python code transformation
- CLI powered by [Typer](https://typer.tiangolo.com/)
- Inspired by the need for better Python refactoring tools that understand modern codebases
