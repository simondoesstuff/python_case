import pytest
from rename_py.rename import to_snake_case, to_pascal_case, refactor_source
import os

def test_to_snake_case():
    assert to_snake_case("HelloWorld") == "hello_world"
    assert to_snake_case("helloWorld") == "hello_world"
    assert to_snake_case("Hello_World") == "hello__world"

def test_to_pascal_case():
    assert to_pascal_case("hello_world") == "HelloWorld"
    assert to_pascal_case("helloWorld") == "HelloWorld"
    assert to_pascal_case("Hello_World") == "HelloWorld"

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
    normalized_refactored = "\n".join(line.strip() for line in refactored_content.strip().splitlines())
    normalized_expected = "\n".join(line.strip() for line in expected_content.strip().splitlines())

    assert normalized_refactored == normalized_expected

def test_refactor_example_file():
    with open("tests/example.py", "r") as f:
        original_source = f.read()
    
    with open("tests/expected_example.py", "r") as f:
        expected_source = f.read()

    refactored_source = refactor_source(original_source)

    assert refactored_source.strip() == expected_source.strip()