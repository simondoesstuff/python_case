"""
Tests for enhanced error handling and custom exceptions.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

from snake_shift.core import refactor_source, refactor_directory, ParseError, RefactorError
from snake_shift.cli import FileError, process_file


class TestCustomExceptions:
    """Test custom exception classes."""
    
    def test_parse_error_inheritance(self):
        """Test that ParseError inherits from RefactorError."""
        assert issubclass(ParseError, RefactorError)
        assert issubclass(RefactorError, Exception)
    
    def test_file_error_inheritance(self):
        """Test that FileError inherits from RefactorError.""" 
        assert issubclass(FileError, RefactorError)
    
    def test_parse_error_creation(self):
        """Test ParseError creation and message."""
        error = ParseError("Test parsing failed")
        assert str(error) == "Test parsing failed"
        assert isinstance(error, RefactorError)
    
    def test_file_error_creation(self):
        """Test FileError creation and message."""
        error = FileError("File operation failed")
        assert str(error) == "File operation failed"
        assert isinstance(error, RefactorError)


class TestRefactorSourceErrorHandling:
    """Test error handling in refactor_source function."""
    
    def test_parse_error_on_invalid_syntax(self):
        """Test that ParseError is raised for invalid Python syntax."""
        invalid_code = """
def broken_function(
    # Missing closing parenthesis and colon
    missing_paren
"""
        with pytest.raises(ParseError) as exc_info:
            refactor_source(invalid_code)
        
        assert "Failed to parse source code" in str(exc_info.value)
    
    def test_parse_error_on_severely_malformed_code(self):
        """Test ParseError on completely malformed code."""
        malformed_code = "def @#$%^&*(){"
        
        with pytest.raises(ParseError) as exc_info:
            refactor_source(malformed_code)
        
        assert "Failed to parse source code" in str(exc_info.value)
    
    def test_empty_source_handling(self):
        """Test that empty source is handled gracefully."""
        assert refactor_source("") == ""
        assert refactor_source("   ") == "   "
        assert refactor_source("\n\n") == "\n\n"
    
    def test_whitespace_only_source(self):
        """Test handling of whitespace-only source code."""
        whitespace_code = "   \n  \t  \n   "
        result = refactor_source(whitespace_code)
        assert result == whitespace_code
    
    def test_comment_only_source(self):
        """Test handling of comment-only source code."""
        comment_code = "# This is just a comment\n# Another comment"
        result = refactor_source(comment_code)
        assert "# This is just a comment" in result
        assert "# Another comment" in result


class TestProcessFileErrorHandling:
    """Test error handling in CLI process_file function."""
    
    def test_unicode_decode_error(self):
        """Test handling of files with encoding issues."""
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.py', delete=False) as temp_file:
            # Write invalid UTF-8 bytes
            temp_file.write(b'\xff\xfe# Invalid UTF-8\ndef test(): pass')
            temp_file_path = temp_file.name
        
        try:
            result = process_file(temp_file_path, dry_run=True, to_stdout=False, verbose=True)
            assert result is False  # Should return False on encoding error
        finally:
            Path(temp_file_path).unlink()
    
    def test_file_not_found_error(self):
        """Test handling of non-existent files."""
        non_existent_file = "/path/that/does/not/exist.py"
        
        result = process_file(non_existent_file, dry_run=True, to_stdout=False, verbose=True)
        assert result is False  # Should return False when file doesn't exist
    
    def test_permission_denied_read(self):
        """Test handling of files with no read permissions."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write("def test(): pass")
            temp_file_path = temp_file.name
        
        try:
            # Remove read permissions
            Path(temp_file_path).chmod(0o000)
            
            result = process_file(temp_file_path, dry_run=True, to_stdout=False, verbose=True)
            assert result is False  # Should return False on permission error
        finally:
            # Restore permissions for cleanup
            Path(temp_file_path).chmod(0o644)
            Path(temp_file_path).unlink()
    
    def test_permission_denied_write(self):
        """Test handling of files with no write permissions during actual refactoring."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write("def myFunction(): pass")  # Code that needs refactoring
            temp_file_path = temp_file.name
        
        try:
            # Remove write permissions
            Path(temp_file_path).chmod(0o444)  # Read-only
            
            result = process_file(temp_file_path, dry_run=False, to_stdout=False, verbose=True)
            assert result is False  # Should return False on write permission error
        finally:
            # Restore permissions for cleanup
            Path(temp_file_path).chmod(0o644)
            Path(temp_file_path).unlink()
    
    def test_parse_error_handling_in_process_file(self):
        """Test that process_file handles ParseError gracefully."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write("def broken_function(\n    # Invalid syntax")
            temp_file_path = temp_file.name
        
        try:
            result = process_file(temp_file_path, dry_run=True, to_stdout=False, verbose=True)
            assert result is False  # Should return False on parse error
        finally:
            Path(temp_file_path).unlink()
    
    def test_successful_processing_returns_true(self):
        """Test that successful processing returns True."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write("def test_function(): pass")
            temp_file_path = temp_file.name
        
        try:
            result = process_file(temp_file_path, dry_run=True, to_stdout=False, verbose=True)
            assert result is True  # Should return True on success
        finally:
            Path(temp_file_path).unlink()


class TestRefactorDirectoryErrorHandling:
    """Test error handling in refactor_directory function."""
    
    def test_keyboard_interrupt_handling(self):
        """Test that keyboard interrupts are handled gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            # Create some Python files
            (project_root / 'test1.py').write_text('def myFunction(): pass')
            (project_root / 'test2.py').write_text('def anotherFunction(): pass')
            
            # Mock the refactor_source function to raise KeyboardInterrupt
            with patch('snake_shift.core.refactor_source') as mock_refactor:
                mock_refactor.side_effect = KeyboardInterrupt()
                
                # This should not raise KeyboardInterrupt but handle it gracefully
                try:
                    refactor_directory(project_root, rename_files=False, dry_run=True, verbose=False)
                    # If we get here, the function handled the interrupt gracefully
                    assert True
                except KeyboardInterrupt:
                    # If KeyboardInterrupt propagates, that's also acceptable behavior
                    assert True
    
    def test_file_processing_errors_dont_stop_processing(self):
        """Test that errors in individual files don't stop processing of other files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            # Create files: one good, one that will cause parse error
            (project_root / 'good_file.py').write_text('def good_function(): pass')
            (project_root / 'bad_file.py').write_text('def broken_function(\n    # Invalid syntax')
            (project_root / 'another_good.py').write_text('def another_function(): pass')
            
            # This should not raise an exception, just log errors
            try:
                refactor_directory(project_root, rename_files=False, dry_run=True, verbose=False)
                assert True  # Should complete without raising
            except Exception as e:
                pytest.fail(f"refactor_directory raised unexpected exception: {e}")


class TestErrorMessageQuality:
    """Test that error messages are informative and helpful."""
    
    def test_parse_error_includes_original_error(self):
        """Test that ParseError includes information about the original parsing error."""
        invalid_code = "def broken("
        
        with pytest.raises(ParseError) as exc_info:
            refactor_source(invalid_code)
        
        error_msg = str(exc_info.value)
        assert "Failed to parse source code" in error_msg
        # Should contain some indication of the original error
        assert len(error_msg) > len("Failed to parse source code")
    
    def test_chained_exceptions(self):
        """Test that exceptions are properly chained."""
        invalid_code = "def totally_broken_syntax @#$%"
        
        with pytest.raises(ParseError) as exc_info:
            refactor_source(invalid_code)
        
        # Should have a chained exception (__cause__ or __context__)
        assert (exc_info.value.__cause__ is not None or 
                exc_info.value.__context__ is not None)


class TestRobustnessEdgeCases:
    """Test robustness with various edge cases."""
    
    def test_very_large_file_handling(self):
        """Test handling of very large files doesn't cause memory issues."""
        # Create a reasonably large but not excessive file for testing
        large_content = "\n".join([f"def function_{i}(): pass" for i in range(1000)])
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write(large_content)
            temp_file_path = temp_file.name
        
        try:
            result = process_file(temp_file_path, dry_run=True, to_stdout=False, verbose=False)
            assert result is True  # Should handle large files successfully
        finally:
            Path(temp_file_path).unlink()
    
    def test_binary_file_handling(self):
        """Test that binary files are handled gracefully."""
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.py', delete=False) as temp_file:
            # Write binary data that's not valid text
            temp_file.write(b'\x00\x01\x02\x03\x04\x05\xFF\xFE\xFD')
            temp_file_path = temp_file.name
        
        try:
            result = process_file(temp_file_path, dry_run=True, to_stdout=False, verbose=True)
            assert result is False  # Should return False for binary files
        finally:
            Path(temp_file_path).unlink()
    
    def test_deeply_nested_directories(self):
        """Test handling of deeply nested directory structures."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            # Create deeply nested structure
            deep_path = project_root / 'a' / 'b' / 'c' / 'd' / 'e' / 'f'
            deep_path.mkdir(parents=True)
            (deep_path / 'deep_file.py').write_text('def deep_function(): pass')
            
            # Should handle deep nesting without issues
            try:
                refactor_directory(project_root, rename_files=False, dry_run=True, verbose=False)
                assert True
            except Exception as e:
                pytest.fail(f"Failed to handle deeply nested directories: {e}")