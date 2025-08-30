
import pytest
import tempfile
from pathlib import Path

from snake_shift.rename import (
    refactor_source, to_pascal_case, to_snake_case,
    should_rename_file, get_new_file_path, collect_file_renames,
    refactor_directory
)


def test_to_snake_case():
    assert to_snake_case("HelloWorld") == "hello_world"
    assert to_snake_case("helloWorld") == "hello_world"
    assert to_snake_case("Hello_World") == "hello__world"
    assert to_snake_case("") == ""
    assert to_snake_case("__init__") == "__init__"  # Dunder methods unchanged
    assert to_snake_case("_privateVar") == "_private_var"
    assert to_snake_case("XML_HTTP_Request") == "xml__http__request"


def test_to_pascal_case():
    assert to_pascal_case("hello_world") == "HelloWorld"
    assert to_pascal_case("helloWorld") == "HelloWorld"
    assert to_pascal_case("Hello_World") == "HelloWorld"
    assert to_pascal_case("") == ""
    assert to_pascal_case("__init__") == "Init"


def test_external_library_preservation():
    """Test that external library method calls are not renamed."""
    source = """
import numpy as np
import torch
from pathlib import Path

def my_function():
    arr = np.zeros(10)
    result = torch.randperm(5)  
    path = Path.joinpath('test')
    return arr, result, path
"""

    refactored = refactor_source(source)

    # External library calls should remain unchanged
    assert "np.zeros" in refactored
    assert "torch.randperm" in refactored
    assert "Path.joinpath" in refactored

    # Internal function should be renamed
    assert "my_function" in refactored


def test_internal_code_renaming():
    """Test that internal code is properly renamed."""
    source = """
class myClass:
    def myMethod(self, myParam):
        myVar = 1
        self.myAttribute = myParam
        return myVar
        
def someFunction(anotherParam):
    obj = myClass()
    result = obj.myMethod(anotherParam)
    return result
"""

    refactored = refactor_source(source)

    # Class names should be PascalCase
    assert "class MyClass:" in refactored

    # Method names should be snake_case
    assert "def my_method" in refactored
    assert "def some_function" in refactored

    # Parameters should be snake_case
    assert "my_param" in refactored
    assert "another_param" in refactored

    # Variables should be snake_case
    assert "my_var" in refactored

    # Self attributes should be snake_case
    assert "self.my_attribute" in refactored


def test_mixed_internal_external():
    """Test mixed internal and external code."""
    source = """
import pandas as pd

class DataProcessor:
    def processData(self, inputData):
        df = pd.DataFrame(inputData)
        processedData = df.dropna()
        return processedData
        
    def myHelperMethod(self):
        return "helper"
"""

    refactored = refactor_source(source)

    # External pandas calls should be unchanged
    assert "pd.DataFrame" in refactored
    assert ".dropna()" in refactored

    # Internal code should be renamed
    assert "class DataProcessor:" in refactored
    assert "def process_data" in refactored
    assert "def my_helper_method" in refactored
    assert "input_data" in refactored
    assert "processed_data" in refactored


def test_self_attributes():
    """Test that self attributes are always renamed."""
    source = """
class TestClass:
    def __init__(self, someParam):
        self.myAttribute = someParam
        self.anotherAttr = None
        
    def getMyAttribute(self):
        return self.myAttribute
"""

    refactored = refactor_source(source)

    # Self attributes should always be snake_case
    assert "self.my_attribute" in refactored
    assert "self.another_attr" in refactored


def test_edge_cases():
    """Test edge cases and error conditions."""
    # Empty string
    assert refactor_source("") == ""

    # Just comments
    source = "# This is a comment\n"
    refactored = refactor_source(source)
    assert "# This is a comment" in refactored

    # Only imports
    source = "import os\nfrom typing import Dict"
    refactored = refactor_source(source)
    assert "import os" in refactored
    assert "from typing import Dict" in refactored


@pytest.fixture
def create_test_file(tmp_path):
    def _create_test_file(content):
        test_file = tmp_path / "test_file.py"
        test_file.write_text(content)
        return test_file

    return _create_test_file


def test_refactor_source(create_test_file):
    original_content = """
class myClass:
    def myFunction(self, myArg):
        myVar = 1
"""
    expected_content = """class MyClass:
    def my_function(self, my_arg):
        my_var = 1
"""
    refactored_content = refactor_source(original_content)

    # Normalize whitespace for comparison
    normalized_refactored = "\n".join(
        line.strip() for line in refactored_content.strip().splitlines()
    )
    normalized_expected = "\n".join(
        line.strip() for line in expected_content.strip().splitlines()
    )

    assert normalized_refactored == normalized_expected


def test_refactor_example_file():
    with open("tests/example_code/example.py", "r") as f:
        original_source = f.read()

    with open("tests/example_code/expected_example.py", "r") as f:
        expected_source = f.read()

    refactored_source = refactor_source(original_source)

    assert refactored_source.strip() == expected_source.strip()


def test_complex_external_imports():
    """Test complex import scenarios with aliases."""
    source = """
import numpy as np
import torch.nn as nn
from sklearn.model_selection import train_test_split
from mymodule import myFunction

def process():
    model = nn.Linear(10, 1)
    X_train, X_test = train_test_split([1,2,3])
    result = myFunction()
    return model, X_train, result
"""

    refactored = refactor_source(source)

    # External aliases should be preserved
    assert "nn.Linear" in refactored
    assert "train_test_split" in refactored

    # Internal function calls should be renamed
    assert "my_function()" in refactored


def test_should_rename_file():
    """Test file renaming detection logic."""
    # Should rename camelCase files
    assert should_rename_file(Path("myModule.py"))
    assert should_rename_file(Path("dataHandler.py"))
    assert should_rename_file(Path("myDirectory"))
    
    # Should NOT rename PascalCase files (likely class modules)
    assert not should_rename_file(Path("MyClass.py"))
    assert not should_rename_file(Path("DataProcessor.py"))
    
    # Should NOT rename already snake_case files
    assert not should_rename_file(Path("my_module.py"))
    assert not should_rename_file(Path("data_handler.py"))
    assert not should_rename_file(Path("my_directory"))
    
    # Should NOT rename special files
    assert not should_rename_file(Path("__init__.py"))
    assert not should_rename_file(Path(".gitignore"))
    assert not should_rename_file(Path("setup.py"))
    assert not should_rename_file(Path("README.md"))
    assert not should_rename_file(Path("pyproject.toml"))


def test_get_new_file_path():
    """Test file path generation for renames."""
    # Python files
    assert get_new_file_path(Path("myModule.py")) == Path("my_module.py")
    assert get_new_file_path(Path("dataHandler.py")) == Path("data_handler.py")
    
    # PascalCase files should be preserved  
    assert get_new_file_path(Path("MyClass.py")) == Path("MyClass.py")
    assert get_new_file_path(Path("DataProcessor.py")) == Path("DataProcessor.py")
    
    # Directories
    assert get_new_file_path(Path("myDirectory")) == Path("my_directory")
    assert get_new_file_path(Path("dataUtils")) == Path("data_utils")


@pytest.fixture
def temp_project():
    """Create a temporary project structure for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        
        # Create directory structure
        (project_root / "myPackage").mkdir()
        (project_root / "myPackage" / "subModule").mkdir()
        (project_root / "myPackage" / "MyClassModule").mkdir()
        
        # Create Python files
        files = {
            "myPackage/__init__.py": "from .myModule import MyClass\n",
            "myPackage/myModule.py": "class MyClass:\n    pass\n",
            "myPackage/dataHandler.py": "def processData():\n    pass\n",
            "myPackage/MyClassModule/__init__.py": "",
            "myPackage/MyClassModule/MyClass.py": "class MyClass:\n    pass\n",
            "myPackage/subModule/__init__.py": "",
            "myPackage/subModule/utilsFile.py": "def helperFunction():\n    pass\n",
        }
        
        for file_path, content in files.items():
            full_path = project_root / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
        
        yield project_root


def test_collect_file_renames(temp_project):
    """Test collecting file renames from a project structure."""
    renames = collect_file_renames(temp_project)
    
    # Convert to relative paths for easier testing
    relative_renames = [
        (old.relative_to(temp_project), new.relative_to(temp_project))
        for old, new in renames
    ]
    
    expected_renames = {
        (Path("myPackage"), Path("my_package")),
        (Path("myPackage/myModule.py"), Path("myPackage/my_module.py")),
        (Path("myPackage/dataHandler.py"), Path("myPackage/data_handler.py")),
        (Path("myPackage/subModule"), Path("myPackage/sub_module")),
        (Path("myPackage/subModule/utilsFile.py"), Path("myPackage/subModule/utils_file.py")),
    }
    
    # MyClassModule and MyClass.py should NOT be renamed (PascalCase)
    not_renamed = {
        Path("myPackage/MyClassModule"),
        Path("myPackage/MyClassModule/MyClass.py"),
    }
    
    for old, new in relative_renames:
        assert (old, new) in expected_renames, f"Unexpected rename: {old} -> {new}"
    
    for path in not_renamed:
        assert not any(old == path for old, new in relative_renames), f"Should not rename PascalCase: {path}"


def test_refactor_directory_dry_run(temp_project, capsys):
    """Test directory refactoring in dry-run mode."""
    refactor_directory(temp_project, rename_files=True, dry_run=True)
    
    captured = capsys.readouterr()
    output = captured.out
    
    # Should show file renames
    assert "Would rename:" in output
    assert "my_package" in output
    assert "my_module.py" in output
    
    # Should show file refactoring
    assert "Would refactor:" in output
    
    # Original files should still exist
    assert (temp_project / "myPackage" / "myModule.py").exists()
    assert (temp_project / "myPackage" / "dataHandler.py").exists()


def test_file_renaming_preserves_pascalcase():
    """Test that PascalCase files/dirs are preserved during renaming."""
    # Files that should NOT be renamed
    test_cases = [
        "MyClass.py",
        "DataProcessor.py", 
        "MyModule",
        "ConfigManager.py"
    ]
    
    for case in test_cases:
        path = Path(case)
        assert not should_rename_file(path), f"{case} should not be renamed (PascalCase)"
        assert get_new_file_path(path) == path, f"{case} should keep same path"


def test_file_renaming_converts_camelcase():
    """Test that camelCase files/dirs are converted to snake_case."""
    test_cases = [
        ("myModule.py", "my_module.py"),
        ("dataHandler.py", "data_handler.py"),
        ("utilsFile.py", "utils_file.py"),
        ("myDirectory", "my_directory"),
        ("dataUtils", "data_utils"),
        ("configHelper", "config_helper"),
    ]
    
    for original, expected in test_cases:
        original_path = Path(original)
        expected_path = Path(expected)
        
        assert should_rename_file(original_path), f"{original} should be renamed"
        assert get_new_file_path(original_path) == expected_path, f"{original} -> {expected}"

