"""
Test Analyzer - checks test coverage and test file changes.
"""

import re
import fnmatch
from typing import Optional

from .base import BaseAnalyzer, ReviewContext
from ..models.feedback import Feedback, Priority, Category
from ..config import ReviewConfig


class TestAnalyzer(BaseAnalyzer):
    """Analyzes test coverage and test file requirements."""
    
    name = "test"
    description = "Checks test coverage for changed files"
    
    # Default test file patterns
    DEFAULT_TEST_PATTERNS = [
        "test_*.py",
        "*_test.py",
        "tests/*.py",
        "**/*test*.py",
        "*.test.js",
        "*.spec.js",
        "*.test.ts",
        "*.spec.ts",
        "*.test.jsx",
        "*.spec.jsx",
        "*.test.tsx",
        "*.spec.tsx",
        "__tests__/*.js",
        "__tests__/*.ts",
    ]
    
    # File patterns that should have tests
    DEFAULT_REQUIRE_TESTS = [
        "src/**/*.py",
        "src/**/*.js",
        "src/**/*.ts",
        "lib/**/*.py",
        "lib/**/*.js",
        "app/**/*.py",
        "app/**/*.js",
    ]
    
    def analyze(self, context: ReviewContext) -> list[Feedback]:
        """Analyze test coverage for changed files."""
        feedbacks = []
        config = context.config or ReviewConfig()
        
        # Get test patterns from config
        test_patterns = config.testing.test_file_patterns or self.DEFAULT_TEST_PATTERNS
        require_tests_for = config.testing.require_tests_for or self.DEFAULT_REQUIRE_TESTS
        
        # Separate source files and test files
        source_files = []
        test_files = []
        
        for file in context.files:
            if self.should_skip_file(file):
                continue
            
            if self._is_test_file(file.filename, test_patterns):
                test_files.append(file)
            elif self._should_have_tests(file.filename, require_tests_for):
                source_files.append(file)
        
        # Check if source files have corresponding tests
        feedback = self._check_test_coverage(source_files, test_files, context.files)
        feedbacks.extend(feedback)
        
        # Check for new source files without new tests
        new_source_feedback = self._check_new_files(source_files, test_files)
        feedbacks.extend(new_source_feedback)
        
        # Calculate test ratio
        ratio_feedback = self._check_test_ratio(source_files, test_files)
        if ratio_feedback:
            feedbacks.append(ratio_feedback)
        
        return feedbacks
    
    def _is_test_file(self, filename: str, patterns: list[str]) -> bool:
        """Check if file is a test file."""
        for pattern in patterns:
            if fnmatch.fnmatch(filename, pattern) or fnmatch.fnmatch(filename.split("/")[-1], pattern):
                return True
        
        # Also check common indicators
        lower_name = filename.lower()
        if any(x in lower_name for x in ["test_", "_test.", ".test.", ".spec.", "/tests/", "/test/", "__tests__"]):
            return True
        
        return False
    
    def _should_have_tests(self, filename: str, patterns: list[str]) -> bool:
        """Check if file should have tests."""
        # Skip non-code files
        code_extensions = {"py", "js", "ts", "jsx", "tsx", "mjs"}
        ext = filename.rsplit(".", 1)[-1] if "." in filename else ""
        if ext not in code_extensions:
            return False
        
        # Skip common non-testable files
        skip_patterns = [
            "**/migrations/*",
            "**/__init__.py",
            "**/setup.py",
            "**/conftest.py",
            "**/config*.py",
            "**/settings*.py",
            "**/constants*.py",
            "**/types.ts",
            "**/index.ts",
            "**/index.js",
        ]
        for pattern in skip_patterns:
            if fnmatch.fnmatch(filename, pattern):
                return False
        
        # Check against patterns
        for pattern in patterns:
            if fnmatch.fnmatch(filename, pattern):
                return True
        
        return False
    
    def _check_test_coverage(
        self,
        source_files,
        test_files,
        all_files
    ) -> list[Feedback]:
        """Check if modified source files have corresponding test changes."""
        feedbacks = []
        test_filenames = {f.filename for f in test_files}
        
        for source in source_files:
            # Generate possible test file names
            possible_tests = self._get_possible_test_files(source.filename)
            
            # Check if any corresponding test was modified
            has_test_changes = any(
                any(fnmatch.fnmatch(test_name, pattern) or test_name in possible_tests 
                    for pattern in possible_tests)
                for test_name in test_filenames
            )
            
            # Check if file has significant changes (not just minor edits)
            if source.additions > 20 and not has_test_changes:
                feedbacks.append(Feedback(
                    file=source.filename,
                    priority=Priority.LOW,
                    category=Category.TESTING,
                    title="Consider Adding Tests",
                    message=f"File has {source.additions} lines added but no corresponding test file was modified.",
                    suggestion="Consider adding or updating tests for this functionality."
                ))
        
        return feedbacks
    
    def _check_new_files(self, source_files, test_files) -> list[Feedback]:
        """Check if new source files have corresponding test files."""
        feedbacks = []
        
        new_source_files = [f for f in source_files if f.status == "added"]
        new_test_files = [f for f in test_files if f.status == "added"]
        
        if new_source_files and not new_test_files:
            file_list = ", ".join(f"`{f.filename}`" for f in new_source_files[:3])
            extra = f" and {len(new_source_files) - 3} more" if len(new_source_files) > 3 else ""
            
            feedbacks.append(Feedback(
                priority=Priority.MEDIUM,
                category=Category.TESTING,
                title="New Files Without Tests",
                message=f"New source files ({file_list}{extra}) were added without corresponding test files.",
                suggestion="Add unit tests for new functionality to maintain test coverage."
            ))
        
        return feedbacks
    
    def _check_test_ratio(self, source_files, test_files) -> Optional[Feedback]:
        """Check the ratio of test changes to source changes."""
        if not source_files:
            return None
        
        source_changes = sum(f.additions + f.deletions for f in source_files)
        test_changes = sum(f.additions + f.deletions for f in test_files)
        
        if source_changes == 0:
            return None
        
        ratio = test_changes / source_changes
        
        # Warn if significant source changes with no test changes
        if source_changes > 50 and test_changes == 0:
            return Feedback(
                priority=Priority.MEDIUM,
                category=Category.TESTING,
                title="No Test Changes",
                message=f"This PR has {source_changes} lines of source code changes but no test changes.",
                suggestion="Consider adding tests to maintain code coverage."
            )
        
        # Note if low test ratio
        if ratio < 0.3 and source_changes > 100:
            return Feedback(
                priority=Priority.LOW,
                category=Category.TESTING,
                title="Low Test Coverage Ratio",
                message=f"Test changes ({test_changes} lines) are significantly less than source changes ({source_changes} lines).",
                suggestion="Consider adding more comprehensive tests for the new functionality."
            )
        
        return None
    
    def _get_possible_test_files(self, source_file: str) -> list[str]:
        """Generate possible test file names for a source file."""
        parts = source_file.rsplit("/", 1)
        if len(parts) == 2:
            dir_path, filename = parts
        else:
            dir_path, filename = "", parts[0]
        
        base_name = filename.rsplit(".", 1)[0]
        ext = filename.rsplit(".", 1)[-1] if "." in filename else ""
        
        patterns = []
        
        if ext == "py":
            patterns = [
                f"test_{base_name}.py",
                f"{base_name}_test.py",
                f"tests/test_{base_name}.py",
                f"tests/{base_name}_test.py",
            ]
        elif ext in ("js", "jsx", "ts", "tsx"):
            patterns = [
                f"{base_name}.test.{ext}",
                f"{base_name}.spec.{ext}",
                f"__tests__/{base_name}.test.{ext}",
                f"__tests__/{base_name}.{ext}",
            ]
        
        return patterns
