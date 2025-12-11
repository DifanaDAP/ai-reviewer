"""
Convention Analyzer - validates project-specific conventions and rules.
"""

import re
import fnmatch
from typing import Optional

from .base import BaseAnalyzer, ReviewContext
from ..models.feedback import Feedback, Priority, Category
from ..config import ReviewConfig


class ConventionAnalyzer(BaseAnalyzer):
    """Analyzes code against project conventions and custom rules."""
    
    name = "convention"
    description = "Validates project-specific conventions"
    
    # Default folder structure expectations
    DEFAULT_STRUCTURE_RULES = {
        "python": {
            "src/**/*.py": "Source files should be in src/",
            "tests/**/*.py": "Test files should be in tests/",
        },
        "javascript": {
            "src/**/*.js": "Source files should be in src/",
            "__tests__/**/*.js": "Test files should be in __tests__/",
        }
    }
    
    # Architecture patterns to flag
    ARCHITECTURE_PATTERNS = [
        {
            "name": "Direct Database Access in Controller",
            "file_pattern": r"(controller|view|handler)\.",
            "code_pattern": r"(cursor\.execute|\.query\(|db\.(find|insert|update|delete))",
            "message": "Direct database access in controller layer violates separation of concerns.",
            "suggestion": "Move database logic to a service or repository layer.",
            "priority": "MEDIUM"
        },
        {
            "name": "Business Logic in Model",
            "file_pattern": r"models?\.",
            "code_pattern": r"(def\s+(?!__)\w+.*\n\s+.*(?:if|for|while|try))",
            "message": "Complex business logic in model file. Models should primarily define structure.",
            "suggestion": "Consider moving complex logic to a service layer.",
            "priority": "LOW"
        },
        {
            "name": "HTTP Request in Service",
            "file_pattern": r"service\.",
            "code_pattern": r"(requests\.(get|post)|fetch\(|axios\.)",
            "message": "HTTP requests in service layer.",
            "suggestion": "Consider creating a dedicated API client class for external requests.",
            "priority": "NIT"
        },
        {
            "name": "Circular Import Risk",
            "file_pattern": r"\.py$",
            "code_pattern": r"from\s+\.{3,}",
            "message": "Deep relative imports may indicate potential circular dependencies.",
            "suggestion": "Consider restructuring to reduce deep imports.",
            "priority": "LOW"
        },
    ]
    
    # File naming conventions
    FILE_NAMING_RULES = {
        "python": {
            r"^[a-z][a-z0-9_]*\.py$": "Python files should be snake_case",
        },
        "javascript": {
            r"^[a-z][a-zA-Z0-9]*\.(js|ts|jsx|tsx)$": "JS/TS files should be camelCase or PascalCase for components",
        }
    }
    
    def analyze(self, context: ReviewContext) -> list[Feedback]:
        """Analyze code against project conventions."""
        feedbacks = []
        
        # Check file naming
        naming_feedbacks = self._check_file_naming(context.files)
        feedbacks.extend(naming_feedbacks)
        
        # Check architecture patterns
        architecture_feedbacks = self._check_architecture(context.files)
        feedbacks.extend(architecture_feedbacks)
        
        # Check for duplicate code patterns
        duplicate_feedbacks = self._check_duplicates(context.files)
        feedbacks.extend(duplicate_feedbacks)
        
        # Check import organization
        import_feedbacks = self._check_imports(context.files)
        feedbacks.extend(import_feedbacks)
        
        return feedbacks
    
    def _check_file_naming(self, files) -> list[Feedback]:
        """Check file naming conventions."""
        feedbacks = []
        
        for file in files:
            if self.should_skip_file(file):
                continue
            
            filename = file.filename.split("/")[-1]
            
            # Skip special files
            if filename.startswith("_") or filename.startswith("."):
                continue
            
            # Check Python files
            if file.extension == "py":
                # Should be snake_case
                if not re.match(r'^[a-z][a-z0-9_]*\.py$', filename):
                    if re.search(r'[A-Z]', filename.replace('.py', '')):
                        feedbacks.append(Feedback(
                            file=file.filename,
                            priority=Priority.NIT,
                            category=Category.STYLE,
                            title="File Naming Convention",
                            message=f"Python file `{filename}` should use snake_case.",
                            suggestion=f"Rename to `{self._to_snake_case(filename)}`"
                        ))
            
            # Check React components
            if file.extension in ("jsx", "tsx"):
                # Should be PascalCase for components
                base_name = filename.rsplit(".", 1)[0]
                if not re.match(r'^[A-Z][a-zA-Z0-9]*$', base_name):
                    if "component" in file.filename.lower() or "components" in file.filename.lower():
                        feedbacks.append(Feedback(
                            file=file.filename,
                            priority=Priority.NIT,
                            category=Category.STYLE,
                            title="Component Naming Convention",
                            message=f"React component file `{filename}` should use PascalCase.",
                            suggestion=f"Rename to `{self._to_pascal_case(base_name)}.{file.extension}`"
                        ))
        
        return feedbacks
    
    def _check_architecture(self, files) -> list[Feedback]:
        """Check for architecture anti-patterns."""
        feedbacks = []
        
        for file in files:
            if self.should_skip_file(file) or not file.patch:
                continue
            
            for pattern in self.ARCHITECTURE_PATTERNS:
                # Check if file matches pattern
                if not re.search(pattern["file_pattern"], file.filename, re.IGNORECASE):
                    continue
                
                # Check code patterns in patch
                if re.search(pattern["code_pattern"], file.patch, re.MULTILINE | re.IGNORECASE):
                    priority = {
                        "HIGH": Priority.HIGH,
                        "MEDIUM": Priority.MEDIUM,
                        "LOW": Priority.LOW,
                        "NIT": Priority.NIT
                    }.get(pattern["priority"], Priority.LOW)
                    
                    feedbacks.append(Feedback(
                        file=file.filename,
                        priority=priority,
                        category=Category.ARCHITECTURE,
                        title=pattern["name"],
                        message=pattern["message"],
                        suggestion=pattern.get("suggestion")
                    ))
        
        return feedbacks
    
    def _check_duplicates(self, files) -> list[Feedback]:
        """Check for potential duplicate/similar code patterns."""
        feedbacks = []
        
        # Collect all function signatures
        function_sigs = {}
        
        for file in files:
            if file.extension not in ("py", "js", "ts") or not file.patch:
                continue
            
            # Extract function names from patch
            func_pattern = r'\+\s*(def|function|const|let|var)\s+(\w+)\s*[\(=]'
            matches = re.findall(func_pattern, file.patch)
            
            for _, func_name in matches:
                if func_name in function_sigs:
                    # Potential duplicate
                    other_file = function_sigs[func_name]
                    if other_file != file.filename:
                        feedbacks.append(Feedback(
                            file=file.filename,
                            priority=Priority.LOW,
                            category=Category.ARCHITECTURE,
                            title="Potential Duplicate Function",
                            message=f"Function `{func_name}` also exists in `{other_file}`.",
                            suggestion="Consider consolidating duplicate logic or renaming for clarity."
                        ))
                else:
                    function_sigs[func_name] = file.filename
        
        return feedbacks
    
    def _check_imports(self, files) -> list[Feedback]:
        """Check import organization."""
        feedbacks = []
        
        for file in files:
            if file.extension != "py" or not file.patch:
                continue
            
            # Check for mixed import styles
            has_regular_import = bool(re.search(r'\+import\s+\w+', file.patch))
            has_from_import = bool(re.search(r'\+from\s+\w+\s+import', file.patch))
            
            # Check for unorganized imports (not grouped)
            import_lines = re.findall(r'\+(?:import|from)\s+[^\n]+', file.patch)
            
            if len(import_lines) > 5:
                # Check if imports from same package are spread out
                packages = []
                for line in import_lines:
                    match = re.search(r'(?:import|from)\s+(\w+)', line)
                    if match:
                        packages.append(match.group(1))
                
                # Check for repeated packages with gaps
                seen_at = {}
                for i, pkg in enumerate(packages):
                    if pkg in seen_at and i - seen_at[pkg] > 1:
                        feedbacks.append(Feedback(
                            file=file.filename,
                            priority=Priority.NIT,
                            category=Category.STYLE,
                            title="Import Organization",
                            message=f"Imports from `{pkg}` are not grouped together.",
                            suggestion="Group imports by package: standard library, third-party, then local."
                        ))
                        break
                    seen_at[pkg] = i
        
        return feedbacks
    
    def _to_snake_case(self, name: str) -> str:
        """Convert name to snake_case."""
        base = name.rsplit(".", 1)[0]
        ext = name.rsplit(".", 1)[1] if "." in name else ""
        
        # Insert underscore before uppercase letters
        result = re.sub(r'([a-z])([A-Z])', r'\1_\2', base)
        result = result.lower()
        
        return f"{result}.{ext}" if ext else result
    
    def _to_pascal_case(self, name: str) -> str:
        """Convert name to PascalCase."""
        # Handle snake_case
        parts = name.split("_")
        return "".join(part.capitalize() for part in parts)
