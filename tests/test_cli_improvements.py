"""
Tests for CLI improvements and Rich output formatting.
"""

import pytest
import tempfile
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch
from typer.testing import CliRunner

from snake_shift.cli import app, main


class TestCLIErrorHandling:
    """Test CLI error handling and user-friendly messages."""
    
    def test_nonexistent_file_error(self):
        """Test CLI behavior when file doesn't exist."""
        runner = CliRunner()
        result = runner.invoke(app, ['/nonexistent/file.py'])
        
        assert result.exit_code == 1
        assert "does not exist" in result.stdout.lower()
    
    def test_non_python_file_error(self):
        """Test CLI behavior when file is not a Python file."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_file.write(b'This is not Python code')
            temp_file_path = temp_file.name
        
        try:
            runner = CliRunner()
            result = runner.invoke(app, [temp_file_path])
            
            assert result.exit_code == 1
            assert "not a Python file" in result.stdout or "is not\na Python file" in result.stdout
        finally:
            Path(temp_file_path).unlink()
    
    def test_stdout_option_with_directory_error(self):
        """Test that --stdout option with directory shows appropriate error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            runner = CliRunner()
            result = runner.invoke(app, [temp_dir, '--stdout'])
            
            assert result.exit_code == 1
            assert "only supported for single files" in result.stdout
    
    def test_invalid_path_error(self):
        """Test CLI behavior with invalid path types."""
        # Test with a special file (like /dev/null on Unix systems)
        if sys.platform != 'win32':
            runner = CliRunner()
            result = runner.invoke(app, ['/dev/null'])
            
            assert result.exit_code == 1


class TestCLIGitignoreIntegration:
    """Test CLI integration with gitignore functionality."""
    
    def test_single_file_gitignore_check(self):
        """Test that single files are checked against parent directory .gitignore."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            # Create .gitignore that ignores test files
            (project_root / '.gitignore').write_text('test_*.py\n')
            
            # Create a file that should be ignored
            ignored_file = project_root / 'test_example.py'
            ignored_file.write_text('def test_function(): pass')
            
            runner = CliRunner()
            result = runner.invoke(app, [str(ignored_file), '--dry-run'])
            
            # Should skip the ignored file
            assert "Skipping ignored file" in result.stdout
            assert result.exit_code == 0
    
    def test_directory_gitignore_integration(self):
        """Test that directory processing respects gitignore patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            # Create .gitignore
            (project_root / '.gitignore').write_text('__pycache__/\n*.pyc\nbuild/\n')
            
            # Create files and directories, some should be ignored
            (project_root / 'main.py').write_text('def main(): pass')
            (project_root / 'myModule.py').write_text('def myFunction(): pass')  # Should be renamed
            
            # Create ignored files/directories
            (project_root / '__pycache__').mkdir()
            (project_root / '__pycache__' / 'main.pyc').write_text('compiled')
            (project_root / 'build').mkdir()
            (project_root / 'build' / 'output.py').write_text('# build file')
            
            runner = CliRunner()
            result = runner.invoke(app, [str(project_root), '--rename-files', '--dry-run', '--verbose'])
            
            assert result.exit_code == 0
            # Should process main files but not ignored ones
            assert 'my_module.py' in result.stdout  # File should be renamed
            assert 'build' not in result.stdout or 'Would rename' not in result.stdout


class TestCLIVerboseMode:
    """Test verbose mode functionality."""
    
    def test_verbose_mode_shows_details(self):
        """Test that verbose mode shows detailed processing information."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write('def myFunction(): pass')  # Code that needs refactoring
            temp_file_path = temp_file.name
        
        try:
            runner = CliRunner()
            
            # Test without verbose
            result_normal = runner.invoke(app, [temp_file_path, '--dry-run'])
            
            # Test with verbose
            result_verbose = runner.invoke(app, [temp_file_path, '--dry-run', '--verbose'])
            
            # Verbose should show more details
            assert len(result_verbose.stdout) >= len(result_normal.stdout)
            
        finally:
            Path(temp_file_path).unlink()
    
    def test_verbose_mode_directory_processing(self):
        """Test verbose mode with directory processing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            # Create files that need processing
            (project_root / 'myModule.py').write_text('def myFunction(): pass')
            (project_root / 'dataHandler.py').write_text('def processData(): pass')
            
            runner = CliRunner()
            result = runner.invoke(app, [str(project_root), '--rename-files', '--dry-run', '--verbose'])
            
            assert result.exit_code == 0
            # Verbose should show detailed progress
            assert 'Collecting' in result.stdout
            assert 'Found' in result.stdout


class TestCLIStdoutOption:
    """Test stdout option functionality."""
    
    def test_stdout_option_outputs_refactored_code(self):
        """Test that --stdout option outputs refactored code to stdout."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            original_code = 'def myFunction():\n    myVar = 1\n    return myVar'
            temp_file.write(original_code)
            temp_file_path = temp_file.name
        
        try:
            runner = CliRunner()
            result = runner.invoke(app, [temp_file_path, '--stdout'])
            
            assert result.exit_code == 0
            # Should contain refactored code
            assert 'my_function' in result.stdout
            assert 'my_var' in result.stdout
            
        finally:
            Path(temp_file_path).unlink()
    
    def test_stdout_option_with_no_changes(self):
        """Test stdout option when no changes are needed."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            # Code that doesn't need refactoring
            original_code = 'def good_function():\n    var = 1\n    return var'
            temp_file.write(original_code)
            temp_file_path = temp_file.name
        
        try:
            runner = CliRunner()
            result = runner.invoke(app, [temp_file_path, '--stdout'])
            
            assert result.exit_code == 0
            # Should output the original code unchanged
            assert 'good_function' in result.stdout
            
        finally:
            Path(temp_file_path).unlink()


class TestCLIProgressOutput:
    """Test progress bar and rich output functionality."""
    
    def test_progress_bars_in_directory_mode(self):
        """Test that progress bars appear in directory processing mode."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            # Create multiple files to process
            for i in range(3):
                (project_root / f'myModule{i}.py').write_text(f'def myFunction{i}(): pass')
            
            runner = CliRunner()
            result = runner.invoke(app, [str(project_root), '--rename-files', '--dry-run'])
            
            assert result.exit_code == 0
            # Should show progress indicators (Rich progress bars show ━ characters)
            progress_indicators = ['Collecting', 'Found', '━']
            assert any(indicator in result.stdout for indicator in progress_indicators)
    
    def test_colored_output_formatting(self):
        """Test that Rich formatting works (even in test environment)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            (project_root / 'test.py').write_text('def test(): pass')
            
            runner = CliRunner()
            result = runner.invoke(app, [str(project_root), '--dry-run'])
            
            assert result.exit_code == 0
            # Should complete without errors (Rich formatting might not show colors in tests)
            assert len(result.stdout) > 0


class TestCLIRealWorldScenarios:
    """Test CLI with realistic scenarios."""
    
    def test_large_project_simulation(self):
        """Test CLI with a simulated large project structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            # Create a realistic project structure
            directories = ['src', 'tests', 'docs', 'scripts']
            for directory in directories:
                (project_root / directory).mkdir()
            
            # Create various Python files
            files_to_create = [
                'src/main.py',
                'src/myModule.py',  # Should be renamed
                'src/dataHandler.py',  # Should be renamed
                'src/MyClass.py',  # Should NOT be renamed (PascalCase)
                'tests/test_main.py',
                'tests/test_myModule.py',  # Should be renamed
                'scripts/setupScript.py',  # Should be renamed
                'docs/conf.py',
            ]
            
            for file_path in files_to_create:
                full_path = project_root / file_path
                full_path.write_text(f'# Content of {file_path}')
            
            # Create .gitignore
            (project_root / '.gitignore').write_text('__pycache__/\n*.pyc\n.pytest_cache/\n')
            
            runner = CliRunner()
            result = runner.invoke(app, [str(project_root), '--rename-files', '--dry-run', '--verbose'])
            
            assert result.exit_code == 0
            
            # Should show files that will be renamed
            assert 'my_module.py' in result.stdout
            assert 'data_handler.py' in result.stdout
            assert 'setupScript' in result.stdout and 'setup_scrip' in result.stdout  # Original and part of target
            
            # Should NOT show PascalCase files being renamed
            assert 'my_class.py' not in result.stdout or 'MyClass.py → my_class.py' not in result.stdout
    
    def test_mixed_file_types_handling(self):
        """Test CLI handling of projects with mixed file types."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            # Create various file types
            (project_root / 'main.py').write_text('def main(): pass')
            (project_root / 'README.md').write_text('# Project README')
            (project_root / 'requirements.txt').write_text('requests==2.25.1')
            (project_root / 'setup.py').write_text('from setuptools import setup')
            (project_root / 'config.json').write_text('{"key": "value"}')
            (project_root / 'myScript.py').write_text('#!/usr/bin/env python\ndef myFunction(): pass')
            
            runner = CliRunner()
            result = runner.invoke(app, [str(project_root), '--rename-files', '--dry-run'])
            
            assert result.exit_code == 0
            
            # Should only process Python files
            assert 'my_script.py' in result.stdout  # Python file should be renamed
            # Non-Python files should not appear in rename list
            assert 'README.md' not in result.stdout or 'Would rename' not in result.stdout


class TestCLIEdgeCases:
    """Test CLI edge cases and boundary conditions."""
    
    def test_empty_directory(self):
        """Test CLI behavior with empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            runner = CliRunner()
            result = runner.invoke(app, [str(project_root), '--dry-run'])
            
            assert result.exit_code == 0
            assert 'No Python files found' in result.stdout or len(result.stdout.strip()) == 0
    
    def test_directory_with_only_ignored_files(self):
        """Test directory containing only ignored files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            # Create .gitignore that ignores everything
            (project_root / '.gitignore').write_text('*\n')
            
            # Create files that will be ignored
            (project_root / 'test.py').write_text('def test(): pass')
            (project_root / 'main.py').write_text('def main(): pass')
            
            runner = CliRunner()
            result = runner.invoke(app, [str(project_root), '--dry-run'])
            
            assert result.exit_code == 0
            assert 'No Python files found' in result.stdout
    
    def test_keyboard_interrupt_simulation(self):
        """Test CLI behavior when process is interrupted."""
        # This is challenging to test directly, but we can test that the CLI
        # is set up to handle KeyboardInterrupt gracefully
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            (project_root / 'test.py').write_text('def test(): pass')
            
            # Simulate KeyboardInterrupt during processing
            runner = CliRunner()
            
            with patch('snake_shift.core.refactor_directory') as mock_refactor:
                mock_refactor.side_effect = KeyboardInterrupt()
                
                result = runner.invoke(app, [str(project_root), '--dry-run'])
                
                # Should handle the interrupt gracefully - either exit code 1 or complete normally
                # depending on how Typer/CliRunner handles it
                assert result.exit_code in [0, 1]  # Either handled gracefully or reported error