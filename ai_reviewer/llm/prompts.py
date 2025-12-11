"""
Prompt templates for AI code review.
"""

SYSTEM_PROMPT = """You are an expert code reviewer with deep knowledge of software engineering best practices, security, performance, and clean code principles.

Your task is to review code changes (diffs) and provide actionable feedback.

## Your Review Should Cover:
1. **Security Issues** - vulnerabilities, injection risks, authentication problems
2. **Performance Problems** - inefficient algorithms, N+1 queries, memory leaks
3. **Code Quality** - readability, maintainability, SOLID principles
4. **Best Practices** - language-specific idioms, design patterns
5. **Potential Bugs** - logic errors, edge cases, error handling

## Response Format:
Provide your feedback as a JSON array of findings. Each finding should have:
```json
{
  "file": "path/to/file.py",
  "line": 42,
  "priority": "HIGH|MEDIUM|LOW|NIT",
  "category": "security|performance|style|architecture|testing|documentation|best_practice",
  "title": "Short descriptive title",
  "message": "Detailed explanation of the issue",
  "suggestion": "How to fix it (optional)"
}
```

## Priority Levels:
- **HIGH**: Security vulnerabilities, critical bugs, data loss risks - MUST be fixed
- **MEDIUM**: Significant issues that should be addressed but aren't blocking
- **LOW**: Good to fix but minor impact
- **NIT**: Style preferences, minor improvements

## Important Guidelines:
- Focus on substantive issues, not trivial style nitpicks
- Be specific about line numbers when possible
- Provide actionable suggestions
- Praise good patterns when you see them
- Consider the context of the change

If the code looks good overall, say so! Include positive observations about well-written code."""


CODE_REVIEW_PROMPT = """## Pull Request: {pr_title}

### PR Description:
{pr_description}

### Files Changed: {file_count}
### Lines Added: +{lines_added}
### Lines Deleted: -{lines_deleted}

### Diff:
```diff
{diff}
```

Please review these changes and provide your feedback as JSON.

Also provide a brief summary of the overall quality and any positive aspects you noticed.

Response format:
```json
{{
  "summary": "Brief overall assessment",
  "positives": ["Good aspect 1", "Good aspect 2"],
  "findings": [
    {{
      "file": "...",
      "line": 0,
      "priority": "...",
      "category": "...",
      "title": "...",
      "message": "...",
      "suggestion": "..."
    }}
  ]
}}
```"""


SECURITY_FOCUS_PROMPT = """Focus specifically on security issues in this code:

```diff
{diff}
```

Look for:
1. SQL injection vulnerabilities
2. XSS risks
3. Authentication/authorization flaws
4. Hardcoded secrets or credentials
5. Insecure deserialization
6. Path traversal vulnerabilities
7. Improper input validation
8. Sensitive data exposure

Respond with JSON array of security findings only."""


COMPLEXITY_ANALYSIS_PROMPT = """Analyze the complexity and maintainability of this code:

```diff
{diff}
```

Consider:
1. Cyclomatic complexity
2. Function/method length
3. Nesting depth
4. Number of parameters
5. Clear naming and self-documenting code
6. Single responsibility principle

Provide specific, actionable feedback."""


class PromptManager:
    """Manages prompt templates for different types of analysis."""
    
    @staticmethod
    def get_system_prompt() -> str:
        """Get the system prompt for code review."""
        return SYSTEM_PROMPT
    
    @staticmethod
    def get_review_prompt(
        pr_title: str,
        pr_description: str,
        diff: str,
        file_count: int,
        lines_added: int,
        lines_deleted: int
    ) -> str:
        """Get the code review prompt with context."""
        return CODE_REVIEW_PROMPT.format(
            pr_title=pr_title,
            pr_description=pr_description or "No description provided.",
            diff=diff,
            file_count=file_count,
            lines_added=lines_added,
            lines_deleted=lines_deleted
        )
    
    @staticmethod
    def get_security_prompt(diff: str) -> str:
        """Get security-focused analysis prompt."""
        return SECURITY_FOCUS_PROMPT.format(diff=diff)
    
    @staticmethod
    def get_complexity_prompt(diff: str) -> str:
        """Get complexity analysis prompt."""
        return COMPLEXITY_ANALYSIS_PROMPT.format(diff=diff)
