"""
Tests for gitignore integration functionality.
"""

import pytest
import tempfile
from pathlib import Path
from snake_shift.file_operations import (
    _load_gitignore_patterns, 
    _is_ignored,
    collect_file_renames
)


def test_load_gitignore_patterns_basic():
    """Test basic gitignore pattern loading."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        gitignore_path = project_root / '.gitignore'
        
        # Create a basic .gitignore file
        gitignore_content = """
# Python
__pycache__/
*.pyc
*.pyo

# Virtual environments
.venv
venv/

# IDE
.vscode/
*.swp

# Empty lines and comments should be ignored

# OS
.DS_Store
"""
        gitignore_path.write_text(gitignore_content)
        
        patterns = _load_gitignore_patterns(project_root)
        
        # Should include patterns from .gitignore
        assert '__pycache__' in patterns
        assert '*.pyc' in patterns
        assert '*.pyo' in patterns
        assert '.venv' in patterns
        assert 'venv/' in patterns
        assert '.vscode/' in patterns
        assert '*.swp' in patterns
        assert '.DS_Store' in patterns
        
        # Should also include default patterns
        assert '.git' in patterns
        assert 'build' in patterns
        assert 'dist' in patterns
        
        # Should not include comments or empty lines
        assert '# Python' not in patterns
        assert '# Empty lines and comments should be ignored' not in patterns


def test_load_gitignore_patterns_no_file():
    """Test gitignore pattern loading when no .gitignore file exists."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        
        patterns = _load_gitignore_patterns(project_root)
        
        # Should still include default patterns
        assert '__pycache__' in patterns
        assert '*.pyc' in patterns
        assert '.git' in patterns
        assert '.venv' in patterns
        assert 'build' in patterns


def test_load_gitignore_patterns_malformed_file():
    """Test gitignore pattern loading with malformed/unreadable file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        gitignore_path = project_root / '.gitignore'
        
        # Create an unreadable .gitignore file (simulate permission error)
        gitignore_path.write_text("*.pyc\n__pycache__/")
        gitignore_path.chmod(0o000)  # Remove all permissions
        
        try:
            patterns = _load_gitignore_patterns(project_root)
            
            # Should still work and include default patterns
            assert '__pycache__' in patterns
            assert '*.pyc' in patterns
            assert '.git' in patterns
        finally:
            # Restore permissions for cleanup
            gitignore_path.chmod(0o644)


def test_is_ignored_simple_patterns():
    """Test file ignore checking with simple patterns."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        
        patterns = {
            '*.pyc',
            '__pycache__',
            '.venv',
            'node_modules',
            '*.log'
        }
        
        # Test files that should be ignored
        assert _is_ignored(project_root / 'test.pyc', project_root, patterns)
        assert _is_ignored(project_root / '__pycache__', project_root, patterns)
        assert _is_ignored(project_root / '.venv', project_root, patterns)
        assert _is_ignored(project_root / 'node_modules', project_root, patterns)
        assert _is_ignored(project_root / 'debug.log', project_root, patterns)
        
        # Test files that should NOT be ignored
        assert not _is_ignored(project_root / 'test.py', project_root, patterns)
        assert not _is_ignored(project_root / 'main.py', project_root, patterns)
        assert not _is_ignored(project_root / 'src', project_root, patterns)


def test_is_ignored_nested_patterns():
    """Test file ignore checking with nested directories."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        
        patterns = {
            '__pycache__',
            '*.pyc',
            'build/',
            'dist/*'
        }
        
        # Create nested directory structure
        (project_root / 'src' / '__pycache__').mkdir(parents=True)
        (project_root / 'build' / 'lib').mkdir(parents=True)
        (project_root / 'dist' / 'packages').mkdir(parents=True)
        
        # Test nested __pycache__ directories
        assert _is_ignored(project_root / 'src' / '__pycache__', project_root, patterns)
        assert _is_ignored(project_root / 'src' / '__pycache__' / 'test.pyc', project_root, patterns)
        
        # Test build directory
        assert _is_ignored(project_root / 'build', project_root, patterns)
        assert _is_ignored(project_root / 'build' / 'lib', project_root, patterns)
        
        # Test dist pattern
        assert _is_ignored(project_root / 'dist' / 'packages', project_root, patterns)


def test_is_ignored_complex_patterns():
    """Test file ignore checking with complex gitignore patterns."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        
        patterns = {
            '*.egg-info',
            '.pytest_cache',
            'htmlcov/',
            'docs/_build',
            '*.tar.gz',
            'logs/*.log'
        }
        
        # Test egg-info pattern
        assert _is_ignored(project_root / 'mypackage.egg-info', project_root, patterns)
        assert _is_ignored(project_root / 'dist' / 'mypackage.egg-info', project_root, patterns)
        
        # Test pytest cache
        assert _is_ignored(project_root / '.pytest_cache', project_root, patterns)
        
        # Test specific directory patterns
        assert _is_ignored(project_root / 'htmlcov', project_root, patterns)
        assert _is_ignored(project_root / 'docs' / '_build', project_root, patterns)


def test_collect_file_renames_with_gitignore():
    """Test that collect_file_renames respects gitignore patterns."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        
        # Create .gitignore
        gitignore_content = """
__pycache__/
*.pyc
build/
.venv/
"""
        (project_root / '.gitignore').write_text(gitignore_content)
        
        # Ensure directories exist first
        (project_root / '__pycache__').mkdir(exist_ok=True)
        (project_root / 'build').mkdir(exist_ok=True)
        (project_root / '.venv' / 'lib').mkdir(parents=True, exist_ok=True)
        
        # Create directory structure with files to rename and files to ignore
        (project_root / 'myModule.py').write_text('# test')
        (project_root / 'dataHandler.py').write_text('# test')
        (project_root / '__pycache__' / 'myModule.pyc').write_text('# compiled')
        (project_root / 'build' / 'someFile.py').write_text('# build file')
        (project_root / '.venv' / 'lib' / 'module.py').write_text('# venv file')
        
        renames = collect_file_renames(project_root)
        
        # Should only include files that aren't ignored
        rename_files = {old.name for old, new in renames}
        
        assert 'myModule.py' in rename_files
        assert 'dataHandler.py' in rename_files
        
        # Should NOT include ignored files
        assert 'myModule.pyc' not in rename_files
        assert 'someFile.py' not in rename_files
        assert 'module.py' not in rename_files


@pytest.fixture
def gitignore_project():
    """Create a temporary project with .gitignore for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        
        # Create .gitignore
        gitignore_content = """
# Python
__pycache__/
*.py[cod]
*$py.class
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDEs
.vscode/
.idea/
*.swp
*.swo

# Testing
.pytest_cache/
.coverage
htmlcov/

# OS
.DS_Store
Thumbs.db
"""
        (project_root / '.gitignore').write_text(gitignore_content)
        
        # Create various files and directories
        test_files = {
            'src/main.py': '# main file',
            'src/myModule.py': '# module to rename',
            'tests/test_main.py': '# test file',
            'src/__pycache__/main.cpython-39.pyc': 'compiled',
            'build/lib/mypackage/__init__.py': '# build file',
            '.venv/lib/python3.9/site-packages/requests/__init__.py': '# venv file',
            'dist/mypackage-1.0.0.tar.gz': 'archive',
            '.DS_Store': 'system file',
            'mypackage.egg-info/PKG-INFO': 'package info'
        }
        
        for file_path, content in test_files.items():
            full_path = project_root / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            if not file_path.endswith('.tar.gz') and not file_path.endswith('.DS_Store'):
                full_path.write_text(content)
            else:
                full_path.write_bytes(content.encode())
        
        yield project_root


def test_comprehensive_gitignore_integration(gitignore_project):
    """Test comprehensive gitignore integration with realistic project structure."""
    renames = collect_file_renames(gitignore_project)
    
    # Get all files that would be processed
    processed_files = {old.relative_to(gitignore_project) for old, new in renames}
    
    # Should process source files
    assert Path('src/myModule.py') in processed_files
    
    # Should NOT process ignored files/directories
    ignored_patterns = [
        '__pycache__', 'build/', '.venv/', 'dist/', '.DS_Store', '*.egg-info'
    ]
    
    for old, new in renames:
        rel_path = old.relative_to(gitignore_project)
        path_str = str(rel_path)
        
        # Ensure no ignored patterns are included
        for pattern in ignored_patterns:
            if pattern.endswith('/'):
                assert not any(part == pattern.rstrip('/') for part in rel_path.parts), \
                    f"Should ignore directory {pattern}: {path_str}"
            elif '*' in pattern:
                import fnmatch
                assert not fnmatch.fnmatch(path_str, pattern), \
                    f"Should ignore pattern {pattern}: {path_str}"
            else:
                assert pattern not in path_str, f"Should ignore {pattern}: {path_str}"


def test_edge_cases():
    """Test edge cases for gitignore functionality."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        
        # Test with empty .gitignore
        (project_root / '.gitignore').write_text('')
        patterns = _load_gitignore_patterns(project_root)
        assert len(patterns) > 0  # Should still have default patterns
        
        # Test with only comments and whitespace
        (project_root / '.gitignore').write_text('# Only comments\n\n  \n# More comments')
        patterns = _load_gitignore_patterns(project_root)
        assert '# Only comments' not in patterns
        
        # Test file not relative to root
        other_root = Path(temp_dir) / 'other'
        other_root.mkdir()
        test_file = other_root / 'test.py'
        test_file.write_text('# test')
        
        # Should return False for files not relative to root
        assert not _is_ignored(test_file, project_root, patterns)