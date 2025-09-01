"""Comprehensive edge case tests for underscore-prefixed name handling."""

import pytest
from snake_shift.core import refactor_source
from snake_shift.naming import _is_underscore_prefixed_pascalcase, to_pascal_case


def test_complex_underscore_patterns():
    """Test various complex underscore patterns."""
    test_cases = [
        # (input, expected, description)
        ("___TripleUnderscore", "___TripleUnderscore", "triple underscore preserved as-is"),
        ("_A", "_a", "single char after underscore becomes snake_case"),
        ("__A__", "__A__", "single char in dunder pattern preserved"),  
        ("_A_B", "_a_b", "mixed case gets partial conversion"),
        ("__A_B__", "__A_B__", "mixed case in dunder pattern preserved"),
        ("_123Class", "_123_class", "number prefix with PascalCase becomes snake_case"),
        ("__123Class__", "__123Class__", "number prefix in dunders preserved"),
        ("_ALLCAPS", "_allcaps", "all caps becomes snake_case"),
        ("__ALLCAPS__", "__ALLCAPS__", "all caps in dunders preserved"),
    ]
    
    for original, expected, description in test_cases:
        code = f"{original} = None"
        result = refactor_source(code)
        assert f"{expected} = None" in result, f"{description}: {original} -> expected {expected}, got {result}"


def test_deeply_nested_underscore_classes():
    """Test deeply nested class structures with underscores."""
    test_code = '''
class _OuterClass:
    class _InnerClass:
        class __DeepInnerClass__:
            def __init__(self):
                self._XMLHelper = _XMLParser()
                self.__meta_helper__ = __MetaHelper__()
    
    def create_inner(self):
        return self._InnerClass()
    
    def create_deep_inner(self):
        return self._InnerClass.__DeepInnerClass__()

# Nested access patterns
outer = _OuterClass()
inner = outer._InnerClass()
deep = outer._InnerClass.__DeepInnerClass__()
'''

    result = refactor_source(test_code)
    
    # Verify transformations
    assert "class _OuterClass:" in result
    assert "class _InnerClass:" in result
    assert "class __DeepInnerClass__:" in result
    assert "self._xml_helper = _XMLParser()" in result  # self attributes get renamed
    assert "self.__meta_helper__ = __MetaHelper__()" in result
    assert "outer = _OuterClass()" in result


def test_lambda_and_comprehension_patterns():
    """Test lambda functions and comprehensions with underscore patterns."""
    test_code = '''
# Lambda with underscore-prefixed names
create_parser = lambda _XMLType: _XMLType() if _XMLType else None
create_meta = lambda __MetaType__: __MetaType__() if __MetaType__ else None

# List comprehensions
parsers = [_XMLParser() for _XMLParser in [_XMLParser, _JSONParser]]
meta_objects = [__MetaClass__() for __MetaClass__ in [__FirstMeta__, __SecondMeta__]]

# Dictionary comprehensions  
parser_dict = {_name: _XMLParser() for _name in ['xml', 'json']}
meta_dict = {__name__: __MetaClass__() for __name__ in ['first', 'second']}

# Generator expressions
parser_gen = (_XMLParser() for _XMLParser in parsers if _XMLParser)
meta_gen = (__MetaClass__() for __MetaClass__ in meta_objects if __MetaClass__)
'''

    result = refactor_source(test_code)
    
    # Check key transformations in comprehensions and lambdas
    assert "_XMLType() if _XMLType else None" in result  # Parameters get renamed
    assert "_XMLParser() for _XMLParser in" in result  # Class names normalized
    assert "__MetaClass__() for __MetaClass__ in" in result  # Dunder names preserved
    assert "_name: _XMLParser()" in result


def test_exception_handling_with_underscores():
    """Test exception handling with underscore-prefixed names."""
    test_code = '''
class _CustomException(Exception):
    def __init__(self, _error_message):
        super().__init__(_error_message)
        self._error_code = None

class __SystemException__(Exception):
    pass

try:
    parser = _XMLParser()
    result = parser.parse(_invalid_data)
except _CustomException as _e:
    print(f"Custom error: {_e}")
    raise __SystemException__("System error") from _e
except __SystemException__ as __se__:
    print(f"System error: {__se__}")
finally:
    cleanup_parser = _XMLParser()
    cleanup_parser.cleanup()
'''

    result = refactor_source(test_code)
    
    assert "class _CustomException(Exception):" in result
    assert "class __SystemException__(Exception):" in result
    assert "parser = _XMLParser()" in result
    assert "except _CustomException as _e:" in result
    assert "raise __SystemException__" in result
    assert "cleanup_parser = _XMLParser()" in result


def test_context_managers_with_underscores():
    """Test context managers with underscore-prefixed names."""
    test_code = '''
class _ResourceManager:
    def __enter__(self):
        self._resource = _XMLParser()
        return self._resource
    
    def __exit__(self, _exc_type, _exc_val, _exc_tb):
        if self._resource:
            self._resource.cleanup()

class __MetaContextManager__:
    def __enter__(self):
        return __MetaHelper__()
    
    def __exit__(self, __exc_type__, __exc_val__, __exc_tb__):
        pass

# Usage patterns
with _ResourceManager() as _parser:
    result = _parser.parse(_data)

with __MetaContextManager__() as __meta__:
    __meta__.process()
'''

    result = refactor_source(test_code)
    
    assert "class _ResourceManager:" in result
    assert "class __MetaContextManager__:" in result
    assert "self._resource = _XMLParser()" in result
    assert "return __MetaHelper__()" in result
    assert "with _ResourceManager() as _parser:" in result
    assert "with __MetaContextManager__() as __meta__:" in result


def test_async_patterns_with_underscores():
    """Test async/await patterns with underscore-prefixed names."""
    test_code = '''
import asyncio

class _AsyncProcessor:
    async def process_async(self, _data):
        _helper = _XMLParser()
        return await _helper.parse_async(_data)

class __AsyncMetaProcessor__:
    async def __aenter__(self):
        self.__parser__ = _XMLParser()
        return self.__parser__
    
    async def __aexit__(self, _exc_type, _exc_val, _exc_tb):
        await self.__parser__.cleanup_async()

async def main():
    _processor = _AsyncProcessor()
    result = await _processor.process_async(_test_data)
    
    async with __AsyncMetaProcessor__() as __parser__:
        data = await __parser__.parse_async(_input)
'''

    result = refactor_source(test_code)
    
    assert "class _AsyncProcessor:" in result
    assert "class __AsyncMetaProcessor__:" in result
    assert "_helper = _XMLParser()" in result
    assert "self.__parser__ = _XMLParser()" in result
    assert "_processor = _AsyncProcessor()" in result
    assert "async with __AsyncMetaProcessor__() as __parser__:" in result


def test_property_and_descriptor_patterns():
    """Test property and descriptor patterns with underscores."""
    test_code = '''
class _PropertyHolder:
    def __init__(self):
        self.__xml_parser = _XMLParser()
    
    @property
    def _xml_parser_prop(self):
        return self.__xml_parser
    
    @_xml_parser_prop.setter  
    def _xml_parser_prop(self, _value):
        if isinstance(_value, _XMLParser):
            self.__xml_parser = _value

class __MetaDescriptor__:
    def __get__(self, _instance, _owner):
        return _XMLParser()
    
    def __set__(self, _instance, _value):
        pass

class _ClassWithDescriptor:
    _xml_descriptor = __MetaDescriptor__()

# Usage
holder = _PropertyHolder()
holder._xml_parser_prop = _XMLParser()
descriptor_class = _ClassWithDescriptor()
parser = descriptor_class._xml_descriptor
'''

    result = refactor_source(test_code)
    
    assert "class _PropertyHolder:" in result
    assert "class __MetaDescriptor__:" in result
    assert "class _ClassWithDescriptor:" in result
    assert "self.__xml_parser = _XMLParser()" in result
    assert "return _XMLParser()" in result
    assert "holder._xml_parser_prop = _XMLParser()" in result


def test_metaclass_patterns():
    """Test metaclass patterns with underscores."""
    test_code = '''
class __XMLParserMeta__(type):
    def __new__(cls, _name, _bases, _attrs):
        _attrs['_default_parser'] = _XMLParser
        return super().__new__(cls, _name, _bases, _attrs)

class _BaseXMLClass(metaclass=__XMLParserMeta__):
    def get_parser(self):
        return self._default_parser()

class _ConcreteXMLClass(_BaseXMLClass):
    def __init__(self):
        self._parser_instance = _XMLParser()

# Usage
concrete = _ConcreteXMLClass()
parser = concrete.get_parser()
'''

    result = refactor_source(test_code)
    
    assert "class __XMLParserMeta__(type):" in result
    assert "_attrs['_default_parser'] = _XMLParser" in result
    assert "class _BaseXMLClass(metaclass=__XMLParserMeta__):" in result
    assert "class _ConcreteXMLClass(_BaseXMLClass):" in result
    assert "self._parser_instance = _XMLParser()" in result
    assert "concrete = _ConcreteXMLClass()" in result


def test_naming_function_edge_cases():
    """Test edge cases in the naming functions themselves."""
    # Test _is_underscore_prefixed_pascalcase edge cases
    edge_cases = [
        ("_", False, "single underscore"),
        ("__", False, "double underscore"),  
        ("___", False, "triple underscore"),
        ("_a", False, "single char after underscore - not PascalCase"),
        ("__a", False, "single char after double underscore - not PascalCase"),
        ("_aB", False, "lowercase start - not PascalCase"),
        ("_Ab", True, "minimal valid PascalCase case"),
        ("__Ab__", True, "minimal valid dunder PascalCase case"),
        ("_ABC", False, "all caps after underscore"),
        ("__ABC__", False, "all caps in dunders"),
        ("_a_b", False, "snake_case after underscore"),
        ("__a_b__", False, "snake_case in dunders"),
        ("_Ab_c", False, "mixed case with underscores - not valid PascalCase"),
        ("_123Ab", False, "number prefix"),
        ("_Ab123", True, "number suffix should be valid"),
    ]
    
    for name, expected, description in edge_cases:
        result = _is_underscore_prefixed_pascalcase(name)
        assert result == expected, f"{description}: {name} -> expected {expected}, got {result}"


def test_to_pascal_case_underscore_edge_cases():
    """Test to_pascal_case edge cases with underscores."""
    edge_cases = [
        ("_", "_", "single underscore unchanged"),
        ("__", "__", "double underscore unchanged"),
        ("___", "___", "triple underscore unchanged"),
        ("_a", "_A", "single char should be capitalized"),
        ("__a__", "__A__", "single char in dunders"),
        ("_hello_world", "_HelloWorld", "snake_case to PascalCase"),
        ("__hello_world__", "__HelloWorld__", "snake_case in dunders"),
        ("_XMLParser", "_XMLParser", "acronym preservation"),
        ("__XMLParser__", "__XMLParser__", "acronym in dunders"),
        ("_HTML_Parser", "_HTMLParser", "mixed acronym"),
        ("__HTML_Parser__", "__HTMLParser__", "mixed acronym in dunders"),
        ("____test____", "____Test____", "many underscores"),
        ("_test_", "_Test_", "trailing underscore"),
        ("__test_", "__Test_", "mixed underscore pattern"),
    ]
    
    for original, expected, description in edge_cases:
        result = to_pascal_case(original)
        assert result == expected, f"{description}: {original} -> expected {expected}, got {result}"