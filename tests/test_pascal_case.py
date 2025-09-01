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


def test_underscore_prefixed_pascalcase():
    """Test that underscore-prefixed PascalCase names are handled correctly."""
    test_cases = [
        # (input, expected_output)
        ("_PrivateClass", "_PrivateClass"),  # Already correct
        ("_WeirdCamelCase", "_WeirdCamelCase"),  # Should normalize to proper PascalCase
        ("__DunderClass__", "__DunderClass__"),  # Already correct
        ("__WeirdCamelThing__", "__WeirdCamelThing__"),  # Should normalize
        ("_XMLParser", "_Xmlparser"),  # Should normalize acronyms
        ("__HTTPClient__", "__Httpclient__"),  # Should normalize acronyms
        ("_private_var", "_private_var"),  # Already snake_case, should stay unchanged
        ("__internal_var__", "__internal_var__"),  # Already snake_case, should stay unchanged
    ]
    
    for original, expected in test_cases:
        # Test variable assignment
        code = f"{original} = None"
        result = refactor_source(code)
        assert f"{expected} = None" in result, f"Failed for {original} -> expected {expected}, got {result}"
        
        # Test class definition if it looks like a class name
        if original.strip('_')[0].isupper() and '_' not in original.strip('_'):
            class_code = f"class {original}: pass"
            result = refactor_source(class_code)
            assert f"class {expected}:" in result, f"Class definition failed for {original} -> expected {expected}, got {result}"


def test_underscore_edge_cases():
    """Test edge cases for underscore handling."""
    test_cases = [
        # Edge cases that should remain unchanged
        ("_", "_"),  # Single underscore
        ("__", "__"),  # Double underscore
        ("___", "___"),  # Triple underscore
        ("_a", "_a"),  # Single char after underscore
        ("__a__", "__a__"),  # Single char between dunders
        ("_123", "_123"),  # Number after underscore
    ]
    
    for original, expected in test_cases:
        code = f"{original} = None"
        result = refactor_source(code)
        assert f"{expected} = None" in result, f"Edge case failed for {original} -> expected {expected}, got {result}"


def test_underscore_prefixed_class_definitions():
    """Test that underscore-prefixed class definitions are handled correctly."""
    test_code = '''
class _PrivateBaseClass:
    def __init__(self):
        self._private_var = 1
        self._AnotherPrivateClass = None

class __DunderMetaClass__:
    def create_instance(self):
        return _XMLParser()

class _HTTPClient:
    pass

# Instance creations should also be normalized
client = _HTTPClient()
parser = _XMLParser()
meta = __DunderMetaClass__()
'''
    
    expected_code = '''
class _PrivateBaseClass:
    def __init__(self):
        self._private_var = 1
        self._another_private_class = None

class __DunderMetaClass__:
    def create_instance(self):
        return _Xmlparser()

class _Httpclient:
    pass

# Instance creations should also be normalized
client = _Httpclient()
parser = _Xmlparser()
meta = __DunderMetaClass__()
'''
    
    result = refactor_source(test_code)
    assert result.strip() == expected_code.strip()


def test_mixed_underscore_patterns_integration():
    """Test complex code with mixed underscore patterns."""
    test_code = '''
class RegularClass:
    def __init__(self):
        self._private_method()
        self._PrivateHelper = None
        self.__dunder_attr__ = 42

class _InternalAPI:
    def process_data(self, _input_data, __config__):
        helper = _XMLProcessor()
        return helper.transform(__config__)

class __SingletonMeta__:
    _instance = None
    
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = _InternalAPI()
        return cls._instance

# Usage patterns
api = _InternalAPI()
meta = __SingletonMeta__()
regular = RegularClass()
processor = _XMLProcessor()
'''

    expected_code = '''
class RegularClass:
    def __init__(self):
        self._private_method()
        self._private_helper = None
        self.__dunder_attr__ = 42

class _InternalApi:
    def process_data(self, _input_data, __config__):
        helper = _Xmlprocessor()
        return helper.transform(__config__)

class __SingletonMeta__:
    _instance = None
    
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = _InternalApi()
        return cls._instance

# Usage patterns
api = _InternalApi()
meta = __SingletonMeta__()
regular = RegularClass()
processor = _Xmlprocessor()
'''
    
    result = refactor_source(test_code)
    assert result.strip() == expected_code.strip()


def test_attribute_access_with_underscore_prefixed_names():
    """Test that attribute access works correctly with underscore-prefixed names."""
    test_code = '''
class Container:
    def __init__(self):
        self._PrivateClass = _XMLParser()
        self.__dunder_thing__ = __MetaThing__()
        self._regular_attr = "value"
    
    def get_parser(self):
        return self._PrivateClass.parse_method()
    
    def access_meta(self):
        return self.__dunder_thing__.meta_method()

container = Container()
parser = container._PrivateClass
meta_obj = container.__dunder_thing__
'''

    expected_code = '''
class Container:
    def __init__(self):
        self._private_class = _Xmlparser()
        self.__dunder_thing__ = __MetaThing__()
        self._regular_attr = "value"
    
    def get_parser(self):
        return self._private_class.parse_method()
    
    def access_meta(self):
        return self.__dunder_thing__.meta_method()

container = Container()
parser = container._PrivateClass
meta_obj = container.__dunder_thing__
'''
    
    result = refactor_source(test_code)
    assert result.strip() == expected_code.strip()


def test_function_parameters_with_underscore_prefixes():
    """Test function parameters with underscore prefixes."""
    test_code = '''
def process_data(_InputData, __config__, _processor_class=_XMLProcessor):
    processor = _processor_class()
    return processor.process(_InputData, __config__)

def factory_method(_ClassType, _instance_config):
    if _ClassType == _XMLProcessor:
        return _XMLProcessor(_instance_config)
    elif _ClassType == __MetaProcessor__:
        return __MetaProcessor__(_instance_config)
    return None

# Function calls
result = process_data(_MyData(), __global_config__, _CustomProcessor)
instance = factory_method(_XMLProcessor, _my_config)
'''

    expected_code = '''
def process_data(_input_data, __config__, _processor_class=_Xmlprocessor):
    processor = _processor_class()
    return processor.process(_InputData, __config__)

def factory_method(_class_type, _instance_config):
    if _ClassType == _Xmlprocessor:
        return _Xmlprocessor(_instance_config)
    elif _ClassType == __MetaProcessor__:
        return __MetaProcessor__(_instance_config)
    return None

# Function calls
result = process_data(_MyData(), __global_config__, _CustomProcessor)
instance = factory_method(_Xmlprocessor, _my_config)
'''
    
    result = refactor_source(test_code)
    assert result.strip() == expected_code.strip()


def test_import_and_module_patterns():
    """Test import patterns don't interfere with underscore-prefixed names."""
    test_code = '''
import xml.etree.ElementTree as ET
from typing import Optional
from _internal_module import _HelperClass, __UtilityMeta__

class _XMLParser:
    def __init__(self):
        self._helper = _HelperClass()
        self._et_parser = ET.XMLParser()
    
    def parse_with_helper(self, _xml_data):
        # External library call should not be renamed
        tree = ET.parse(_xml_data)
        # Internal helper should be accessible
        return self._helper.process_tree(tree)

parser = _XMLParser()
helper = _HelperClass()
meta = __UtilityMeta__()
'''

    # Note: We expect external imports to remain unchanged
    # but internal class references should be normalized
    result = refactor_source(test_code)
    
    # Check key transformations occurred
    assert "class _Xmlparser:" in result
    assert "_HelperClass()" in result  # Imported names should stay as-is
    assert "__UtilityMeta__()" in result  # Imported names should stay as-is
    assert "ET.XMLParser()" in result  # External library unchanged
    assert "parser = _Xmlparser()" in result


def test_complex_inheritance_patterns():
    """Test inheritance with underscore-prefixed class names."""
    test_code = '''
class _BaseProcessor:
    pass

class _XMLProcessor(_BaseProcessor):
    def process_xml(self, _xml_input):
        return super().process_data(_xml_input)

class __MetaProcessor__(_BaseProcessor):
    def __init__(self):
        super().__init__()
        self._xml_proc = _XMLProcessor()

# Multiple inheritance
class _CombinedProcessor(_XMLProcessor, __MetaProcessor__):
    pass

# Usage
base = _BaseProcessor()
xml_proc = _XMLProcessor()
meta_proc = __MetaProcessor__()
combined = _CombinedProcessor()
'''

    expected_code = '''
class _BaseProcessor:
    pass

class _Xmlprocessor(_BaseProcessor):
    def process_xml(self, _xml_input):
        return super().process_data(_xml_input)

class __MetaProcessor__(_BaseProcessor):
    def __init__(self):
        super().__init__()
        self._xml_proc = _Xmlprocessor()

# Multiple inheritance
class _CombinedProcessor(_Xmlprocessor, __MetaProcessor__):
    pass

# Usage
base = _BaseProcessor()
xml_proc = _Xmlprocessor()
meta_proc = __MetaProcessor__()
combined = _CombinedProcessor()
'''
    
    result = refactor_source(test_code)
    assert result.strip() == expected_code.strip()


def test_decorator_patterns_with_underscores():
    """Test decorators with underscore-prefixed names."""
    test_code = '''
def _private_decorator(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

class __DecoratorMeta__(type):
    def __new__(cls, name, bases, attrs):
        return super().__new__(cls, name, bases, attrs)

@_private_decorator
class _DecoratedClass:
    @staticmethod
    def static_method(_param):
        return _param

@__DecoratorMeta__
class __MetaDecoratedClass__:
    pass

# Usage
decorated = _DecoratedClass()
meta_decorated = __MetaDecoratedClass__()
'''

    result = refactor_source(test_code)
    
    # Check that decorators and decorated classes are handled correctly
    assert "_private_decorator" in result  # Function decorator should stay snake_case
    assert "class _DecoratedClass:" in result
    assert "__DecoratorMeta__" in result  # Meta class should stay as-is if already correct
    assert "class __MetaDecoratedClass__:" in result
    assert "decorated = _DecoratedClass()" in result
    assert "meta_decorated = __MetaDecoratedClass__()" in result