import pytest
from rename_py.rename import to_snake_case, to_pascal_case, refactor_file
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

def test_refactor_file(create_test_file):
    original_content = """
class myClass:
    def myFunction(self, myArg):
        myVar = 1
"""
    expected_content = """
class MyClass:

    def my_function(self, my_arg):
        my_var = 1
"""
    test_file = create_test_file(original_content)
    refactor_file(str(test_file))
    with open(test_file, 'r') as f:
        refactored_content = f.read()
    
    # Normalize whitespace for comparison
    normalized_refactored = "\\n".join(line.strip() for line in refactored_content.strip().splitlines())
    normalized_expected = "\\n".join(line.strip() for line in expected_content.strip().splitlines())

    assert normalized_refactored == normalized_expected
