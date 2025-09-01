"""
Naming convention utilities for Python refactoring.
"""

import re


def _snake_to_pascal_preserving_acronyms(original_name: str) -> str:
    """Convert directly from original name to PascalCase preserving adjacent capitals."""
    if not original_name:
        return ""
    
    # Split the original name while preserving adjacent capitals
    # First, split lowercase/digits from uppercase: parseXMLData -> parse_XMLData  
    s1 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", original_name)
    # Then split consecutive uppercase letters from following lowercase: XMLParser -> XML_Parser
    s2 = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s1)
    
    # Now we have segments like ['XML', 'Parser'] or ['Hyena', 'DNA']
    # Convert each segment appropriately
    parts = s2.split('_')
    pascal_parts = []
    
    for part in parts:
        if part:
            if part.isupper() and len(part) > 1:
                # This is an acronym, keep it uppercase
                pascal_parts.append(part)
            else:
                # Regular word, capitalize it
                pascal_parts.append(part.capitalize())
    
    return ''.join(pascal_parts)


def _is_pascalcase(name: str) -> bool:
    """Check if a name follows PascalCase convention (likely a class/type)."""
    if not name or len(name) < 2:
        return False
    return name[0].isupper() and not name.isupper() and '_' not in name


def _is_underscore_prefixed_pascalcase(name: str) -> bool:
    """Check if a name is PascalCase with underscore prefix/suffix (e.g., _PrivateClass, __DunderThing__)."""
    if not name or len(name) < 3:  # At least one underscore + 2 chars for PascalCase
        return False
    
    # Extract the core name without leading/trailing underscores
    core_name = name.strip('_')
    
    # Must have at least one leading underscore and a core name
    if not core_name or not name.startswith('_'):
        return False
    
    # The core name should be PascalCase
    return len(core_name) >= 2 and core_name[0].isupper() and not core_name.isupper() and '_' not in core_name


def to_snake_case(name: str) -> str:
    """Converts a string to snake_case."""
    if not name:
        return ""
    
    if name.startswith('__') and name.endswith('__'):
        return name

    leading_underscores = len(name) - len(name.lstrip('_'))
    
    name = name.lstrip('_')
    # Handle consecutive uppercase letters as single units, but split them from lowercase letters
    # First, split lowercase/digits from uppercase: parseXMLData -> parse_XMLData
    s1 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    # Then split consecutive uppercase letters from following lowercase: XMLParser -> XML_Parser
    s2 = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s1)
    
    return "_" * leading_underscores + s2.lower().lstrip('_')


def to_pascal_case(name: str) -> str:
    """Converts a string to PascalCase, preserving underscore prefixes/suffixes."""
    if not name:
        return ""
    
    # Handle underscore-prefixed/suffixed names
    if name.startswith('_') or name.endswith('_'):
        # Count leading and trailing underscores
        leading_underscores = len(name) - len(name.lstrip('_'))
        trailing_underscores = len(name) - len(name.rstrip('_'))
        
        # Extract the core name
        core_name = name.strip('_')
        
        if not core_name:
            return name  # All underscores, return as-is
        
        # Convert core name to PascalCase
        pascal_case_core = _snake_to_pascal_preserving_acronyms(core_name)
        
        # Reconstruct with original underscore pattern
        return '_' * leading_underscores + pascal_case_core + '_' * trailing_underscores
    
    # Standard case - no underscore prefixes/suffixes
    return _snake_to_pascal_preserving_acronyms(name)