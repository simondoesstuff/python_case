
import pytest

from rename_py.rename import refactor_source, to_pascal_case, to_snake_case


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

