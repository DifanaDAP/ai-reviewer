"""
Risk Analyzer - detects security vulnerabilities and performance issues.
"""

import re
from typing import Optional

from .base import BaseAnalyzer, ReviewContext
from ..models.feedback import Feedback, Priority, Category
from ..config import ReviewConfig, SecurityPattern


class RiskAnalyzer(BaseAnalyzer):
    """Analyzes code for security vulnerabilities and performance issues."""
    
    name = "risk"
    description = "Detects security vulnerabilities and performance hotspots"
    
    # Built-in security patterns (in addition to config)
    BUILTIN_PATTERNS = [
        {
            "name": "SQL Injection (String Format)",
            "regex": r'execute\s*\(\s*f["\']|execute\s*\([^)]*%|execute\s*\([^)]*\.format\(',
            "severity": "HIGH",
            "category": "security",
            "message": "Potential SQL injection vulnerability. User input may be directly interpolated into SQL query.",
            "suggestion": "Use parameterized queries: `cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))`"
        },
        {
            "name": "SQL Injection (String Concat)",
            "regex": r'["\']SELECT\s.*["\']\s*\+|["\']INSERT\s.*["\']\s*\+|["\']UPDATE\s.*["\']\s*\+|["\']DELETE\s.*["\']\s*\+',
            "severity": "HIGH",
            "category": "security",
            "message": "Potential SQL injection. SQL query is being built with string concatenation.",
            "suggestion": "Use parameterized queries or an ORM instead of string concatenation."
        },
        {
            "name": "XSS - innerHTML",
            "regex": r'\.innerHTML\s*=(?!\s*["\']["\'])',
            "severity": "HIGH",
            "category": "security",
            "message": "Setting innerHTML with dynamic content can lead to XSS vulnerabilities.",
            "suggestion": "Use textContent for text, or sanitize HTML content before insertion."
        },
        {
            "name": "XSS - dangerouslySetInnerHTML",
            "regex": r'dangerouslySetInnerHTML\s*=\s*\{',
            "severity": "MEDIUM",
            "category": "security",
            "message": "Using dangerouslySetInnerHTML - ensure content is properly sanitized.",
            "suggestion": "Sanitize HTML using DOMPurify or similar library before rendering."
        },
        {
            "name": "Hardcoded Credentials",
            "regex": r'(password|passwd|pwd|secret|api_key|apikey|api_secret|auth_token|access_token)\s*=\s*["\'][^"\']{8,}["\']',
            "severity": "HIGH",
            "category": "security",
            "message": "Possible hardcoded credential or secret detected.",
            "suggestion": "Move secrets to environment variables or a secure vault."
        },
        {
            "name": "Hardcoded AWS Key",
            "regex": r'AKIA[0-9A-Z]{16}',
            "severity": "HIGH",
            "category": "security",
            "message": "Possible AWS Access Key ID detected in code.",
            "suggestion": "Remove hardcoded AWS keys. Use IAM roles or environment variables."
        },
        {
            "name": "Private Key",
            "regex": r'-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----',
            "severity": "HIGH",
            "category": "security",
            "message": "Private key detected in code!",
            "suggestion": "Never commit private keys. Add to .gitignore and use secrets management."
        },
        {
            "name": "Eval Usage",
            "regex": r'\beval\s*\([^)]+\)',
            "severity": "MEDIUM",
            "category": "security",
            "message": "Use of eval() can execute arbitrary code and is a security risk.",
            "suggestion": "Avoid eval(). Use safer alternatives like JSON.parse() or ast.literal_eval()."
        },
        {
            "name": "Exec Usage",
            "regex": r'\bexec\s*\([^)]+\)',
            "severity": "MEDIUM",
            "category": "security",
            "message": "Use of exec() can execute arbitrary code and is a security risk.",
            "suggestion": "Avoid exec(). Consider restructuring code to avoid dynamic code execution."
        },
        {
            "name": "Shell Injection",
            "regex": r'subprocess\.(call|run|Popen)\s*\([^)]*shell\s*=\s*True',
            "severity": "HIGH",
            "category": "security",
            "message": "Using shell=True with subprocess can lead to shell injection.",
            "suggestion": "Use shell=False and pass arguments as a list: subprocess.run(['cmd', 'arg1'])"
        },
        {
            "name": "os.system Usage",
            "regex": r'os\.system\s*\([^)]+\)',
            "severity": "MEDIUM",
            "category": "security",
            "message": "os.system() is vulnerable to shell injection.",
            "suggestion": "Use subprocess.run() with shell=False instead."
        },
        {
            "name": "Pickle Deserialization",
            "regex": r'pickle\.loads?\s*\(',
            "severity": "MEDIUM",
            "category": "security",
            "message": "Pickle deserialization can execute arbitrary code if data is untrusted.",
            "suggestion": "Only unpickle data from trusted sources. Consider using JSON for untrusted data."
        },
        {
            "name": "Debug Mode in Production",
            "regex": r'DEBUG\s*=\s*True|app\.run\([^)]*debug\s*=\s*True',
            "severity": "MEDIUM",
            "category": "security",
            "message": "Debug mode should be disabled in production.",
            "suggestion": "Use environment variable: DEBUG = os.getenv('DEBUG', 'False') == 'True'"
        },
        {
            "name": "Console.log with Sensitive Data",
            "regex": r'console\.log\([^)]*(?:password|secret|token|key|credential)',
            "severity": "LOW",
            "category": "security",
            "message": "Logging potentially sensitive data to console.",
            "suggestion": "Remove or redact sensitive data from logs."
        },
    ]
    
    PERFORMANCE_PATTERNS = [
        {
            "name": "N+1 Query Pattern",
            "regex": r'for\s+\w+\s+in\s+\w+[^:]*:\s*\n\s*.*\.(query|execute|find|get|fetch)',
            "severity": "MEDIUM",
            "category": "performance",
            "message": "Possible N+1 query pattern detected - database query inside a loop.",
            "suggestion": "Fetch all needed data before the loop, or use eager loading/joins."
        },
        {
            "name": "Synchronous File Read in Loop",
            "regex": r'for\s+\w+\s+in\s+\w+[^:]*:\s*\n\s*.*open\s*\(',
            "severity": "LOW",
            "category": "performance",
            "message": "File operations inside a loop can be slow.",
            "suggestion": "Consider batching file operations or using async I/O."
        },
        {
            "name": "Large List Append Loop",
            "regex": r'for\s+\w+\s+in\s+\w+[^:]*:\s*\n\s*\w+\.append\(',
            "severity": "NIT",
            "category": "performance",
            "message": "Building list with append in loop - consider list comprehension.",
            "suggestion": "Use list comprehension: [item for item in iterable]"
        },
        {
            "name": "String Concatenation in Loop",
            "regex": r'for\s+\w+\s+in\s+\w+[^:]*:\s*\n\s*\w+\s*\+=\s*["\']',
            "severity": "LOW",
            "category": "performance",
            "message": "String concatenation in loop is inefficient in Python.",
            "suggestion": "Use ''.join(list_of_strings) instead."
        },
        {
            "name": "Blocking API Call",
            "regex": r'requests\.(get|post|put|delete|patch)\s*\(',
            "severity": "NIT",
            "category": "performance",
            "message": "Synchronous HTTP request detected.",
            "suggestion": "Consider using async HTTP client (httpx, aiohttp) for better concurrency."
        },
    ]
    
    def analyze(self, context: ReviewContext) -> list[Feedback]:
        """Analyze code for security and performance risks."""
        feedbacks = []
        config = context.config or ReviewConfig()
        
        for file in context.files:
            if self.should_skip_file(file) or not file.patch:
                continue
            
            # Analyze the diff patch
            added_lines = self._extract_added_lines(file.patch)
            
            # Security analysis
            security_feedbacks = self._check_security_patterns(
                file.filename, added_lines, config.security.patterns
            )
            feedbacks.extend(security_feedbacks)
            
            # Performance analysis
            perf_feedbacks = self._check_performance_patterns(file.filename, added_lines)
            feedbacks.extend(perf_feedbacks)
        
        return feedbacks
    
    def _extract_added_lines(self, patch: str) -> list[tuple[int, str]]:
        """Extract added lines from a patch with line numbers."""
        added_lines = []
        current_line = 0
        
        for line in patch.split('\n'):
            if line.startswith('@@'):
                # Parse hunk header: @@ -old_start,old_count +new_start,new_count @@
                match = re.match(r'@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@', line)
                if match:
                    current_line = int(match.group(1))
            elif line.startswith('+') and not line.startswith('+++'):
                added_lines.append((current_line, line[1:]))
                current_line += 1
            elif not line.startswith('-'):
                current_line += 1
        
        return added_lines
    
    def _check_security_patterns(
        self,
        filename: str,
        added_lines: list[tuple[int, str]],
        custom_patterns: list[SecurityPattern]
    ) -> list[Feedback]:
        """Check for security vulnerabilities."""
        feedbacks = []
        
        # Combine built-in and custom patterns
        all_patterns = self.BUILTIN_PATTERNS.copy()
        for cp in custom_patterns:
            all_patterns.append({
                "name": cp.name,
                "regex": cp.regex,
                "severity": cp.severity,
                "category": "security",
                "message": cp.description,
                "suggestion": ""
            })
        
        for line_num, line_content in added_lines:
            for pattern in all_patterns:
                if re.search(pattern["regex"], line_content, re.IGNORECASE):
                    priority = {
                        "HIGH": Priority.HIGH,
                        "MEDIUM": Priority.MEDIUM,
                        "LOW": Priority.LOW,
                        "NIT": Priority.NIT
                    }.get(pattern["severity"], Priority.MEDIUM)
                    
                    feedbacks.append(Feedback(
                        file=filename,
                        line=line_num,
                        priority=priority,
                        category=Category.SECURITY,
                        title=pattern["name"],
                        message=pattern.get("message", f"Security issue: {pattern['name']}"),
                        suggestion=pattern.get("suggestion"),
                        code_snippet=line_content.strip()
                    ))
        
        return feedbacks
    
    def _check_performance_patterns(
        self,
        filename: str,
        added_lines: list[tuple[int, str]]
    ) -> list[Feedback]:
        """Check for performance issues."""
        feedbacks = []
        
        # Combine lines for multi-line pattern matching
        combined_content = "\n".join(line for _, line in added_lines)
        
        for pattern in self.PERFORMANCE_PATTERNS:
            matches = list(re.finditer(pattern["regex"], combined_content, re.MULTILINE))
            for match in matches:
                # Find approximate line number
                line_num = combined_content[:match.start()].count('\n') + 1
                actual_line = added_lines[min(line_num - 1, len(added_lines) - 1)][0] if added_lines else 0
                
                priority = {
                    "HIGH": Priority.HIGH,
                    "MEDIUM": Priority.MEDIUM,
                    "LOW": Priority.LOW,
                    "NIT": Priority.NIT
                }.get(pattern["severity"], Priority.LOW)
                
                feedbacks.append(Feedback(
                    file=filename,
                    line=actual_line,
                    priority=priority,
                    category=Category.PERFORMANCE,
                    title=pattern["name"],
                    message=pattern.get("message", f"Performance issue: {pattern['name']}"),
                    suggestion=pattern.get("suggestion"),
                    code_snippet=match.group(0)[:100]
                ))
        
        return feedbacks
