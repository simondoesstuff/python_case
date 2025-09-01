
import pytest
import tempfile
from pathlib import Path

from snake_shift.core import refactor_source, refactor_directory
from snake_shift.naming import to_pascal_case, to_snake_case, _is_underscore_prefixed_pascalcase
from snake_shift.file_operations import (
    should_rename_file, get_new_file_path, collect_file_renames, execute_file_renames
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
    assert to_pascal_case("__init__") == "__Init__"
    
    # Test underscore-prefixed cases
    assert to_pascal_case("_private_class") == "_PrivateClass"
    assert to_pascal_case("_WeirdCamelCase") == "_WeirdCamelCase"  
    assert to_pascal_case("__dunder_class__") == "__DunderClass__"
    assert to_pascal_case("_XMLParser") == "_Xmlparser"
    assert to_pascal_case("__HTTPClient__") == "__Httpclient__"


def test_is_underscore_prefixed_pascalcase():
    """Test the helper function for detecting underscore-prefixed PascalCase."""
    # Should return True for underscore-prefixed PascalCase
    assert _is_underscore_prefixed_pascalcase("_PrivateClass") == True
    assert _is_underscore_prefixed_pascalcase("__DunderClass__") == True
    assert _is_underscore_prefixed_pascalcase("_XMLParser") == True
    assert _is_underscore_prefixed_pascalcase("__HTTPClient__") == True
    
    # Should return False for regular PascalCase
    assert _is_underscore_prefixed_pascalcase("PrivateClass") == False
    assert _is_underscore_prefixed_pascalcase("XMLParser") == False
    
    # Should return False for snake_case
    assert _is_underscore_prefixed_pascalcase("_private_var") == False
    assert _is_underscore_prefixed_pascalcase("__internal_var__") == False
    assert _is_underscore_prefixed_pascalcase("regular_var") == False
    
    # Should return False for edge cases
    assert _is_underscore_prefixed_pascalcase("_") == False
    assert _is_underscore_prefixed_pascalcase("__") == False
    assert _is_underscore_prefixed_pascalcase("_a") == False
    assert _is_underscore_prefixed_pascalcase("__a__") == False
    assert _is_underscore_prefixed_pascalcase("") == False
    assert _is_underscore_prefixed_pascalcase("_123") == False


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
    
    # Convert to sets for easier testing
    relative_rename_set = set(relative_renames)
    
    # With the simplified algorithm, we get basic renames only.
    # Directory renames automatically move their contents.
    expected_renames = {
        # Deepest items first
        (Path("myPackage/subModule/utilsFile.py"), Path("myPackage/subModule/utils_file.py")),
        (Path("myPackage/subModule"), Path("myPackage/sub_module")),
        (Path("myPackage/MyClassModule"), Path("myPackage/my_class_module")),  # PascalCase directories now renamed
        (Path("myPackage"), Path("my_package")),
        (Path("myPackage/dataHandler.py"), Path("myPackage/data_handler.py")),
        (Path("myPackage/myModule.py"), Path("myPackage/my_module.py")),
    }
    
    # Check that we have the expected number of renames
    assert len(relative_renames) == len(expected_renames), f"Expected {len(expected_renames)} renames, got {len(relative_renames)}"
    
    # Check that all expected renames are present
    for expected_rename in expected_renames:
        assert expected_rename in relative_rename_set, f"Expected rename not found: {expected_rename[0]} -> {expected_rename[1]}"
    
    # PascalCase files should NOT be renamed by themselves, but may appear if parent directories are renamed
    # Since our new logic renames directories first, files don't need explicit renaming for directory moves


def test_refactor_directory_dry_run(temp_project, capsys):
    """Test directory refactoring in dry-run mode."""
    refactor_directory(temp_project, rename_files=True, dry_run=True)
    
    captured = capsys.readouterr()
    output = captured.out
    
    # Should show file renames with new Rich output format
    assert "Would rename:" in output
    assert "my_package" in output
    # my_module might be split across lines in the output due to long paths
    assert "my_modul" in output or "my_module" in output
    
    # Should show summary
    assert "Would refactor" in output or "No files needed refactoring" in output
    
    # Original files should still exist
    assert (temp_project / "myPackage" / "myModule.py").exists()
    assert (temp_project / "myPackage" / "dataHandler.py").exists()


def test_file_renaming_preserves_pascalcase_files_only():
    """Test that PascalCase files are preserved, but PascalCase directories are renamed."""
    # PascalCase FILES should NOT be renamed (likely class modules)
    pascalcase_files = [
        "MyClass.py",
        "DataProcessor.py", 
        "ConfigManager.py"
    ]
    
    for case in pascalcase_files:
        path = Path(case)
        assert not should_rename_file(path), f"{case} should not be renamed (PascalCase file)"
        assert get_new_file_path(path) == path, f"{case} should keep same path"
    
    # PascalCase DIRECTORIES should be renamed to snake_case
    pascalcase_dirs = [
        ("MyModule", "my_module"),
        ("DataUtils", "data_utils"),
        ("ConfigHelper", "config_helper"),
    ]
    
    for original, expected in pascalcase_dirs:
        path = Path(original)
        assert should_rename_file(path), f"{original} should be renamed (PascalCase directory)"
        assert get_new_file_path(path) == Path(expected), f"{original} -> {expected}"


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


def test_nested_directory_and_file_renaming():
    """Test that both nested directories and files are correctly renamed."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        
        # Create nested structure: moduleModule/fileThingy.py
        nested_dir = temp_root / "moduleModule"
        nested_dir.mkdir()
        test_file = nested_dir / "fileThingy.py"
        test_file.write_text("print('test')")
        
        # Collect renames
        renames = collect_file_renames(temp_root)
        
        # Convert to relative paths for easier testing
        relative_renames = [
            (old.relative_to(temp_root), new.relative_to(temp_root))
            for old, new in renames
        ]
        
        # Expected renames (with simplified algorithm - basic renames only)
        expected_renames = {
            (Path("moduleModule/fileThingy.py"), Path("moduleModule/file_thingy.py")),
            (Path("moduleModule"), Path("module_module")),
        }
        
        assert len(relative_renames) == 2, f"Expected 2 renames, got {len(relative_renames)}"
        
        for old_rel, new_rel in relative_renames:
            assert (old_rel, new_rel) in expected_renames, f"Unexpected rename: {old_rel} -> {new_rel}"
        
        # Specifically test the file rename includes updated directory path
        file_renames = [(old, new) for old, new in relative_renames if old.suffix == '.py']
        assert len(file_renames) == 1, "Should have exactly one file rename"
        
        old_file, new_file = file_renames[0]
        assert old_file == Path("moduleModule/fileThingy.py")
        assert new_file == Path("moduleModule/file_thingy.py"), f"File rename should be basic rename, got {new_file}"
        
        # Now test that actual filesystem execution produces the correct final result
        execute_file_renames(renames, dry_run=False)
        
        # Verify the final filesystem state is correct
        final_file = temp_root / "module_module" / "file_thingy.py"
        assert final_file.exists(), "Final file should exist at module_module/file_thingy.py"
        assert final_file.read_text() == "print('test')", "File content should be preserved"
        
        # Verify original structure is gone
        assert not (temp_root / "moduleModule").exists(), "Original directory should be gone"


def test_filesystem_simple_file_rename():
    """Test actual filesystem renaming of a simple file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        
        # Create a file that needs renaming
        original_file = temp_root / "myModule.py"
        original_content = "def myFunction():\n    return 'hello'"
        original_file.write_text(original_content)
        
        # Verify original file exists
        assert original_file.exists()
        assert original_file.read_text() == original_content
        
        # Collect and execute renames
        renames = collect_file_renames(temp_root)
        execute_file_renames(renames, dry_run=False)
        
        # Verify rename occurred
        expected_file = temp_root / "my_module.py"
        assert expected_file.exists(), "Renamed file should exist"
        assert not original_file.exists(), "Original file should no longer exist"
        assert expected_file.read_text() == original_content, "File content should be preserved"


def test_filesystem_directory_rename():
    """Test actual filesystem renaming of a directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        
        # Create a directory that needs renaming
        original_dir = temp_root / "myPackage"
        original_dir.mkdir()
        
        # Create a file inside the directory
        original_file = original_dir / "helper.py"
        original_content = "def helper(): pass"
        original_file.write_text(original_content)
        
        # Verify original structure
        assert original_dir.exists()
        assert original_file.exists()
        
        # Collect and execute renames
        renames = collect_file_renames(temp_root)
        execute_file_renames(renames, dry_run=False)
        
        # Verify rename occurred
        expected_dir = temp_root / "my_package" 
        expected_file = expected_dir / "helper.py"
        
        assert expected_dir.exists(), "Renamed directory should exist"
        assert expected_file.exists(), "File inside renamed directory should exist"
        assert not original_dir.exists(), "Original directory should no longer exist"
        assert expected_file.read_text() == original_content, "File content should be preserved"


def test_filesystem_nested_complex_rename():
    """Test actual filesystem renaming of complex nested structure."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        
        # Create complex nested structure
        structure = {
            "MyProject/utils/dataHandler.py": "def process_data(): pass",
            "MyProject/utils/configManager.py": "class Config: pass",
            "MyProject/modules/myModule/handler.py": "def handle(): pass",
            "MyProject/modules/myModule/__init__.py": "from .handler import handle",
            "MyProject/modules/PascalModule/MyClass.py": "class MyClass: pass",  # PascalCase file should be preserved
            "MyProject/modules/PascalModule/__init__.py": "",
            "MyProject/__init__.py": "",
        }
        
        # Create all files and directories
        for file_path, content in structure.items():
            full_path = temp_root / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
        
        # Verify original structure exists
        assert (temp_root / "MyProject").exists()
        assert (temp_root / "MyProject/utils/dataHandler.py").exists()
        assert (temp_root / "MyProject/modules/PascalModule/MyClass.py").exists()
        
        # Collect and execute renames  
        renames = collect_file_renames(temp_root)
        execute_file_renames(renames, dry_run=False)
        
        # Verify expected final structure
        expected_structure = {
            "my_project/utils/data_handler.py": "def process_data(): pass",
            "my_project/utils/config_manager.py": "class Config: pass", 
            "my_project/modules/my_module/handler.py": "def handle(): pass",
            "my_project/modules/my_module/__init__.py": "from .handler import handle",
            "my_project/modules/pascal_module/MyClass.py": "class MyClass: pass",  # File preserved, dir renamed
            "my_project/modules/pascal_module/__init__.py": "",
            "my_project/__init__.py": "",
        }
        
        # Check that all expected files exist with correct content
        for file_path, expected_content in expected_structure.items():
            full_path = temp_root / file_path
            assert full_path.exists(), f"Expected file {file_path} should exist"
            assert full_path.read_text() == expected_content, f"Content mismatch for {file_path}"
        
        # Verify original structure is gone
        assert not (temp_root / "MyProject").exists(), "Original MyProject directory should be gone"
        assert not (temp_root / "MyProject/modules/PascalModule").exists(), "Original PascalModule directory should be gone"


def test_filesystem_rename_ordering():
    """Test that filesystem renames execute in correct order (deepest first)."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        
        # Create deeply nested structure with camelCase names to avoid case-insensitive filesystem issues
        deep_structure = temp_root / "FirstLevel" / "SecondLevel" / "ThirdLevel" / "FourthLevel" 
        deep_structure.mkdir(parents=True)
        
        # Create files at each level
        (temp_root / "FirstLevel" / "fileFirst.py").write_text("# File First")
        (temp_root / "FirstLevel" / "SecondLevel" / "fileSecond.py").write_text("# File Second")
        (temp_root / "FirstLevel" / "SecondLevel" / "ThirdLevel" / "fileThird.py").write_text("# File Third")
        (temp_root / "FirstLevel" / "SecondLevel" / "ThirdLevel" / "FourthLevel" / "fileFourth.py").write_text("# File Fourth")
        
        # Collect renames (should be ordered deepest first)
        renames = collect_file_renames(temp_root)
        
        # Verify ordering: directories should be deepest first
        dir_renames = [(old, new) for old, new in renames if not old.suffix]
        dir_depths = [len(old.relative_to(temp_root).parts) for old, new in dir_renames]
        
        # Should be in descending depth order
        assert dir_depths == sorted(dir_depths, reverse=True), f"Directory renames not in deepest-first order: {dir_depths}"
        
        # Execute renames
        execute_file_renames(renames, dry_run=False)
        
        # Verify final structure: FirstLevel -> first_level, etc.
        expected_files = [
            "first_level/file_first.py",
            "first_level/second_level/file_second.py", 
            "first_level/second_level/third_level/file_third.py",
            "first_level/second_level/third_level/fourth_level/file_fourth.py"
        ]
        
        for file_path in expected_files:
            full_path = temp_root / file_path
            assert full_path.exists(), f"Expected file {file_path} should exist after rename"
        
        # Verify original structure is gone (use a file to test since directories might have case-insensitive issues)
        assert not (temp_root / "FirstLevel" / "fileFirst.py").exists(), "Original file structure should be gone"
        assert (temp_root / "first_level" / "file_first.py").exists(), "New file structure should exist"


def test_filesystem_mixed_pascalcase_camelcase():
    """Test filesystem rename of mixed PascalCase and camelCase items."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        
        # Create mixed structure
        files_and_dirs = {
            "MyClass.py": "class MyClass: pass",  # PascalCase file - preserve
            "myFunction.py": "def my_function(): pass",  # camelCase file - rename
            "DataProcessor.py": "class DataProcessor: pass",  # PascalCase file - preserve
            "helperUtils.py": "def helper(): pass",  # camelCase file - rename
        }
        
        dirs = ["PascalDir", "camelDir", "MyModule"]  # All dirs should be renamed
        
        # Create directories and files
        for dir_name in dirs:
            (temp_root / dir_name).mkdir()
            
        for file_name, content in files_and_dirs.items():
            (temp_root / file_name).write_text(content)
            
        # Also create files inside directories
        (temp_root / "PascalDir" / "MyHandler.py").write_text("class MyHandler: pass")  # Preserve
        (temp_root / "camelDir" / "myFile.py").write_text("# my file")  # Rename
        (temp_root / "MyModule" / "ConfigClass.py").write_text("class ConfigClass: pass")  # Preserve
        
        # Execute renames
        renames = collect_file_renames(temp_root) 
        execute_file_renames(renames, dry_run=False)
        
        # Verify results
        
        # PascalCase files should be preserved (but may have moved due to directory renames)
        assert (temp_root / "MyClass.py").exists()
        assert (temp_root / "DataProcessor.py").exists()
        assert (temp_root / "pascal_dir" / "MyHandler.py").exists()  # Dir renamed, file preserved
        assert (temp_root / "my_module" / "ConfigClass.py").exists()  # Dir renamed, file preserved
        
        # camelCase files should be renamed
        assert (temp_root / "my_function.py").exists()
        assert (temp_root / "helper_utils.py").exists()
        assert (temp_root / "camel_dir" / "my_file.py").exists()
        
        # All directories should be renamed to snake_case
        assert (temp_root / "pascal_dir").exists()
        assert (temp_root / "camel_dir").exists() 
        assert (temp_root / "my_module").exists()
        
        # Original directories should be gone
        assert not (temp_root / "PascalDir").exists()
        assert not (temp_root / "camelDir").exists()
        assert not (temp_root / "MyModule").exists()
        
        # Original camelCase files should be gone
        assert not (temp_root / "myFunction.py").exists()
        assert not (temp_root / "helperUtils.py").exists()


def test_filesystem_directory_with_no_python_files():
    """Test that directories without Python files are not renamed."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        
        # Create directories with no Python files
        (temp_root / "camelCaseDir").mkdir()
        (temp_root / "camelCaseDir" / "README.md").write_text("# Documentation")
        (temp_root / "camelCaseDir" / "config.json").write_text('{"key": "value"}')
        
        (temp_root / "anotherCamelDir").mkdir()
        (temp_root / "anotherCamelDir" / "data.txt").write_text("some data")
        
        # Create a directory that DOES have Python files
        (temp_root / "pythonDir").mkdir()
        (temp_root / "pythonDir" / "module.py").write_text("def func(): pass")
        
        # Collect renames
        renames = collect_file_renames(temp_root)
        
        # Convert to relative paths for easier testing
        relative_renames = [
            (old.relative_to(temp_root), new.relative_to(temp_root))
            for old, new in renames
        ]
        
        # Only directories with Python files should be renamed
        expected_renames = {(Path("pythonDir"), Path("python_dir"))}
        
        relative_rename_set = set(relative_renames)
        assert relative_rename_set == expected_renames, f"Expected {expected_renames}, got {relative_rename_set}"
        
        # Execute renames
        execute_file_renames(renames, dry_run=False)
        
        # Verify: directories without Python files should remain unchanged
        assert (temp_root / "camelCaseDir").exists(), "Directory without Python files should not be renamed"
        assert (temp_root / "anotherCamelDir").exists(), "Directory without Python files should not be renamed"
        
        # Directory with Python files should be renamed
        assert not (temp_root / "pythonDir").exists(), "Original directory with Python files should be gone"
        assert (temp_root / "python_dir").exists(), "Directory with Python files should be renamed"
        assert (temp_root / "python_dir" / "module.py").exists(), "Python file should be moved with directory"


def test_filesystem_non_empty_directory_rename():
    """Test that non-empty directories can be renamed (using shutil.move)."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        
        # Create a complex non-empty directory structure
        complex_dir = temp_root / "myComplexModule"
        complex_dir.mkdir()
        
        # Add subdirectories and files
        (complex_dir / "subdir").mkdir()
        (complex_dir / "subdir" / "deep").mkdir()
        (complex_dir / "main.py").write_text("def main(): pass")
        (complex_dir / "subdir" / "helper.py").write_text("def helper(): pass") 
        (complex_dir / "subdir" / "deep" / "utils.py").write_text("def utils(): pass")
        (complex_dir / "README.md").write_text("# Complex Module")
        (complex_dir / "config.json").write_text('{"settings": {}}')
        
        # Verify complex structure exists
        assert (complex_dir / "main.py").exists()
        assert (complex_dir / "subdir" / "helper.py").exists()
        assert (complex_dir / "subdir" / "deep" / "utils.py").exists()
        assert (complex_dir / "README.md").exists()
        
        # Collect and execute renames
        renames = collect_file_renames(temp_root)
        execute_file_renames(renames, dry_run=False)
        
        # Verify the entire structure moved successfully
        new_complex_dir = temp_root / "my_complex_module"
        assert new_complex_dir.exists(), "Renamed directory should exist"
        assert not complex_dir.exists(), "Original directory should be gone"
        
        # Verify all nested content was moved
        assert (new_complex_dir / "main.py").exists(), "Nested Python file should be moved"
        assert (new_complex_dir / "subdir" / "helper.py").exists(), "Deeply nested Python file should be moved"
        assert (new_complex_dir / "subdir" / "deep" / "utils.py").exists(), "Very deeply nested Python file should be moved"
        assert (new_complex_dir / "README.md").exists(), "Non-Python file should be moved"
        assert (new_complex_dir / "config.json").exists(), "Config file should be moved"
        
        # Verify content is preserved
        assert (new_complex_dir / "main.py").read_text() == "def main(): pass"
        assert (new_complex_dir / "subdir" / "helper.py").read_text() == "def helper(): pass"
        assert (new_complex_dir / "README.md").read_text() == "# Complex Module"


def test_filesystem_mixed_directories_python_filtering():
    """Test mixed scenario: some directories have Python files, others don't.""" 
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        
        # Directory 1: Has Python files - should be renamed
        (temp_root / "myPackage").mkdir()
        (temp_root / "myPackage" / "__init__.py").write_text("")
        (temp_root / "myPackage" / "module.py").write_text("def func(): pass")
        
        # Directory 2: Only has non-Python files - should NOT be renamed  
        (temp_root / "myDocs").mkdir()
        (temp_root / "myDocs" / "README.md").write_text("# Docs")
        (temp_root / "myDocs" / "guide.txt").write_text("User guide")
        
        # Directory 3: Mixed content but no Python files in subdirs - should NOT be renamed
        (temp_root / "myAssets").mkdir()  
        (temp_root / "myAssets" / "images").mkdir()
        (temp_root / "myAssets" / "images" / "logo.png").write_text("fake png data")
        (temp_root / "myAssets" / "styles.css").write_text("body { margin: 0; }")
        
        # Directory 4: Has Python files in subdirectory - should be renamed
        (temp_root / "myProject").mkdir()
        (temp_root / "myProject" / "src").mkdir()
        (temp_root / "myProject" / "src" / "main.py").write_text("if __name__ == '__main__': pass")
        (temp_root / "myProject" / "Dockerfile").write_text("FROM python:3.9")
        
        # Collect renames
        renames = collect_file_renames(temp_root)
        
        # Convert to relative paths
        relative_renames = [
            (old.relative_to(temp_root), new.relative_to(temp_root))
            for old, new in renames
        ]
        
        # Only directories with Python files should be in the renames
        expected_directories_to_rename = {"myPackage", "myProject"}
        
        # Extract directory names from renames
        renamed_dirs = {str(old) for old, new in relative_renames if not old.suffix}
        
        assert renamed_dirs == expected_directories_to_rename, f"Expected to rename {expected_directories_to_rename}, got {renamed_dirs}"
        
        # Execute renames
        execute_file_renames(renames, dry_run=False)
        
        # Verify results
        assert (temp_root / "my_package").exists(), "Directory with Python files should be renamed"
        assert (temp_root / "my_project").exists(), "Directory with nested Python files should be renamed"
        assert (temp_root / "myDocs").exists(), "Directory without Python files should not be renamed"
        assert (temp_root / "myAssets").exists(), "Directory without Python files should not be renamed"
        
        # Verify Python files moved correctly
        assert (temp_root / "my_package" / "module.py").exists()
        assert (temp_root / "my_project" / "src" / "main.py").exists()
        
        # Verify non-Python content in unchanged directories
        assert (temp_root / "myDocs" / "README.md").exists()
        assert (temp_root / "myAssets" / "styles.css").exists()

