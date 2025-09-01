"""
Naming convention utilities for Python refactoring.
"""

import re


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
    # Add an underscore before any uppercase letter, except at the start
    s1 = re.sub(r"([A-Z]+)", r"_\1", name)
    # Handle cases where there's an uppercase letter after a lowercase letter or number
    s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1)
    
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
        snake_case_core = to_snake_case(core_name)
        pascal_case_core = ''.join(word.capitalize() for word in snake_case_core.split('_'))
        
        # Reconstruct with original underscore pattern
        return '_' * leading_underscores + pascal_case_core + '_' * trailing_underscores
    
    # Standard case - no underscore prefixes/suffixes
    snake_case_name = to_snake_case(name)
    return ''.join(word.capitalize() for word in snake_case_name.split('_'))