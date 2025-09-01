"""Test PascalCase class call renaming functionality."""

import pytest
from snake_shift.core import refactor_source


def test_pascal_case_class_calls():
    """Test that PascalCase class calls are normalized consistently with class definitions."""
    test_code = '''
class HyenaDNA:
    def __init__(self):
        pass

# This should be renamed to match the normalized class name
instance = HyenaDNA()

# Another test case
class XMLParser:
    pass

parser = XMLParser()

# Edge case with mixed case
class HTTPClient:
    pass

client = HTTPClient()
'''
    
    expected = '''
class HyenaDna:
    def __init__(self):
        pass

# This should be renamed to match the normalized class name
instance = HyenaDna()

# Another test case
class Xmlparser:
    pass

parser = Xmlparser()

# Edge case with mixed case
class Httpclient:
    pass

client = Httpclient()
'''
    
    result = refactor_source(test_code)
    assert result.strip() == expected.strip()


def test_pascal_case_normalization_examples():
    """Test specific PascalCase normalization examples."""
    test_cases = [
        ("HyenaDNA", "HyenaDna"),
        ("XMLParser", "Xmlparser"),
        ("HTTPClient", "Httpclient"),
        ("URLValidator", "Urlvalidator"),
        ("JSONData", "Jsondata"),
    ]
    
    for original, expected in test_cases:
        # Test class definition renaming
        class_code = f"class {original}: pass"
        result = refactor_source(class_code)
        assert f"class {expected}:" in result
        
        # Test class call renaming
        call_code = f"instance = {original}()"
        result = refactor_source(call_code)
        assert f"instance = {expected}()" in result