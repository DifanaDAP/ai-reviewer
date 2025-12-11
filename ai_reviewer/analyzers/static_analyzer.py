"""
Static Analyzer - checks naming conventions, code style, and anti-patterns.
"""

import re
from typing import Optional

from .base import BaseAnalyzer, ReviewContext
from ..models.feedback import Feedback, Priority, Category
from ..config import ReviewConfig


class StaticAnalyzer(BaseAnalyzer):
    """Analyzes code for style issues, naming conventions, and anti-patterns."""
    
    name = "static"
    description = "Checks naming conventions, code style, and anti-patterns"
    
    # Anti-patterns to check
    ANTI_PATTERNS = {
        "python": [
            {
                "name": "Bare except",
                "regex": r"except\s*:",
                "message": "Bare except clause catches all exceptions including KeyboardInterrupt.",
                "suggestion": "Use specific exceptions: `except Exception:` or `except ValueError:`",
                "priority": "MEDIUM"
            },
            {
                "name": "Mutable default argument",
                "regex": r"def\s+\w+\s*\([^)]*=\s*(\[\]|\{\})\s*[,)]",
                "message": "Mutable default argument can lead to unexpected behavior.",
                "suggestion": "Use None as default: `def func(items=None): items = items or []`",
                "priority": "MEDIUM"
            },
            {
                "name": "Star import",
                "regex": r"from\s+\w+\s+import\s+\*",
                "message": "Star imports pollute the namespace and make code harder to understand.",
                "suggestion": "Import specific names: `from module import name1, name2`",
                "priority": "LOW"
            },
            {
                "name": "TODO without issue",
                "regex": r"#\s*TODO(?!.*#\d+|.*issue|.*ticket)",
                "message": "TODO comment without linked issue.",
                "suggestion": "Link to an issue: `# TODO(#123): description`",
                "priority": "NIT"
            },
            {
                "name": "FIXME in code",
                "regex": r"#\s*FIXME",
                "message": "FIXME comment indicates broken code that should be fixed.",
                "suggestion": "Fix the issue or create a tracked issue for it.",
                "priority": "LOW"
            },
            {
                "name": "Magic number",
                "regex": r"(?<![\w.])\b(?!0|1|2|10|100|1000|True|False)\d{2,}\b(?!\s*[:\]\)])",
                "message": "Magic number found. Consider using a named constant.",
                "suggestion": "Define a constant: `MAX_RETRIES = 5`",
                "priority": "NIT"
            },
            {
                "name": "Print statement",
                "regex": r"^\s*print\s*\(",
                "message": "Print statement found. Consider using logging instead.",
                "suggestion": "Use logging module: `logger.info()` or `logger.debug()`",
                "priority": "NIT"
            },
        ],
        "javascript": [
            {
                "name": "Console.log",
                "regex": r"console\.(log|debug|info)\s*\(",
                "message": "Console statement found. Should be removed before production.",
                "suggestion": "Remove console statements or use a proper logger.",
                "priority": "LOW"
            },
            {
                "name": "var keyword",
                "regex": r"\bvar\s+\w+",
                "message": "Using 'var' instead of 'let' or 'const'.",
                "suggestion": "Use 'const' for constants, 'let' for variables.",
                "priority": "LOW"
            },
            {
                "name": "== comparison",
                "regex": r"[^!=]==[^=]",
                "message": "Using loose equality (==) instead of strict equality (===).",
                "suggestion": "Use strict equality === for type-safe comparison.",
                "priority": "LOW"
            },
            {
                "name": "TODO without issue",
                "regex": r"//\s*TODO(?!.*#\d+|.*issue|.*ticket)",
                "message": "TODO comment without linked issue.",
                "suggestion": "Link to an issue: `// TODO(#123): description`",
                "priority": "NIT"
            },
            {
                "name": "Alert usage",
                "regex": r"\balert\s*\(",
                "message": "Using alert() - should be removed for production.",
                "suggestion": "Use a proper modal/dialog component.",
                "priority": "MEDIUM"
            },
        ],
        "typescript": [
            {
                "name": "Any type",
                "regex": r":\s*any\b",
                "message": "Using 'any' type defeats the purpose of TypeScript.",
                "suggestion": "Use a specific type or 'unknown' if type is truly unknown.",
                "priority": "LOW"
            },
            {
                "name": "Type assertion with as any",
                "regex": r"as\s+any\b",
                "message": "Type assertion to 'any' bypasses type checking.",
                "suggestion": "Use proper type narrowing or a more specific type.",
                "priority": "LOW"
            },
            {
                "name": "Non-null assertion",
                "regex": r"\w+![\.\[]",
                "message": "Non-null assertion (!) can hide potential null errors.",
                "suggestion": "Use optional chaining (?.) or proper null checks.",
                "priority": "NIT"
            },
        ]
    }
    
    # File extension to language mapping
    EXTENSION_MAP = {
        "py": "python",
        "js": "javascript",
        "jsx": "javascript",
        "ts": "typescript",
        "tsx": "typescript",
        "mjs": "javascript",
        "cjs": "javascript",
    }
    
    def analyze(self, context: ReviewContext) -> list[Feedback]:
        """Analyze code for style issues and anti-patterns."""
        feedbacks = []
        config = context.config or ReviewConfig()
        
        for file in context.files:
            if self.should_skip_file(file) or not file.patch:
                continue
            
            language = self.EXTENSION_MAP.get(file.extension)
            if not language:
                continue
            
            # Get added lines from patch
            added_lines = self._extract_added_lines(file.patch)
            
            # Check naming conventions
            naming_feedbacks = self._check_naming(
                file.filename, added_lines, language, config.naming
            )
            feedbacks.extend(naming_feedbacks)
            
            # Check anti-patterns
            pattern_feedbacks = self._check_anti_patterns(
                file.filename, added_lines, language
            )
            feedbacks.extend(pattern_feedbacks)
        
        return feedbacks
    
    def _extract_added_lines(self, patch: str) -> list[tuple[int, str]]:
        """Extract added lines from a patch with line numbers."""
        added_lines = []
        current_line = 0
        
        for line in patch.split('\n'):
            if line.startswith('@@'):
                match = re.match(r'@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@', line)
                if match:
                    current_line = int(match.group(1))
            elif line.startswith('+') and not line.startswith('+++'):
                added_lines.append((current_line, line[1:]))
                current_line += 1
            elif not line.startswith('-'):
                current_line += 1
        
        return added_lines
    
    def _check_naming(
        self,
        filename: str,
        added_lines: list[tuple[int, str]],
        language: str,
        naming_config
    ) -> list[Feedback]:
        """Check naming conventions."""
        feedbacks = []
        
        lang_config = getattr(naming_config, language, {})
        if isinstance(lang_config, dict):
            conventions = lang_config
        else:
            conventions = {}
        
        for line_num, line_content in added_lines:
            # Check class names
            if language == "python":
                class_match = re.search(r"class\s+(\w+)", line_content)
                if class_match and "class" in conventions:
                    name = class_match.group(1)
                    if not re.match(conventions["class"], name):
                        feedbacks.append(Feedback(
                            file=filename,
                            line=line_num,
                            priority=Priority.NIT,
                            category=Category.STYLE,
                            title="Naming Convention",
                            message=f"Class name `{name}` should be PascalCase.",
                            code_snippet=line_content.strip()
                        ))
                
                # Check function names
                func_match = re.search(r"def\s+(\w+)", line_content)
                if func_match and "function" in conventions:
                    name = func_match.group(1)
                    # Skip dunder methods
                    if not (name.startswith("__") and name.endswith("__")):
                        if not re.match(conventions["function"], name):
                            feedbacks.append(Feedback(
                                file=filename,
                                line=line_num,
                                priority=Priority.NIT,
                                category=Category.STYLE,
                                title="Naming Convention",
                                message=f"Function name `{name}` should be snake_case.",
                                code_snippet=line_content.strip()
                            ))
        
        return feedbacks
    
    def _check_anti_patterns(
        self,
        filename: str,
        added_lines: list[tuple[int, str]],
        language: str
    ) -> list[Feedback]:
        """Check for anti-patterns in code."""
        feedbacks = []
        patterns = self.ANTI_PATTERNS.get(language, [])
        
        for line_num, line_content in added_lines:
            for pattern in patterns:
                if re.search(pattern["regex"], line_content):
                    priority = {
                        "HIGH": Priority.HIGH,
                        "MEDIUM": Priority.MEDIUM,
                        "LOW": Priority.LOW,
                        "NIT": Priority.NIT
                    }.get(pattern.get("priority", "LOW"), Priority.LOW)
                    
                    feedbacks.append(Feedback(
                        file=filename,
                        line=line_num,
                        priority=priority,
                        category=Category.STYLE,
                        title=pattern["name"],
                        message=pattern["message"],
                        suggestion=pattern.get("suggestion"),
                        code_snippet=line_content.strip()
                    ))
        
        return feedbacks
