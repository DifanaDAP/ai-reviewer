"""
Feedback models with priority levels and categories.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel


class Priority(str, Enum):
    """Feedback priority levels."""
    HIGH = "HIGH"       # Blocking - must be fixed
    MEDIUM = "MEDIUM"   # Important but not blocking
    LOW = "LOW"         # Recommendation
    NIT = "NIT"         # Nitpick / style suggestion
    
    @property
    def emoji(self) -> str:
        """Get emoji for priority."""
        return {
            Priority.HIGH: "🔴",
            Priority.MEDIUM: "🟡",
            Priority.LOW: "🟢",
            Priority.NIT: "💭"
        }[self]
    
    @property
    def label(self) -> str:
        """Get display label."""
        return f"{self.emoji} {self.value}"


class Category(str, Enum):
    """Feedback categories."""
    SECURITY = "security"
    PERFORMANCE = "performance"
    STYLE = "style"
    ARCHITECTURE = "architecture"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    STRUCTURE = "pr_structure"
    BEST_PRACTICE = "best_practice"
    
    @property
    def emoji(self) -> str:
        """Get emoji for category."""
        return {
            Category.SECURITY: "🔒",
            Category.PERFORMANCE: "⚡",
            Category.STYLE: "🎨",
            Category.ARCHITECTURE: "🏗️",
            Category.TESTING: "🧪",
            Category.DOCUMENTATION: "📚",
            Category.STRUCTURE: "📋",
            Category.BEST_PRACTICE: "✨"
        }[self]
    
    @property
    def label(self) -> str:
        """Get display label."""
        return f"{self.emoji} {self.value.replace('_', ' ').title()}"


class Feedback(BaseModel):
    """Single piece of review feedback."""
    file: Optional[str] = None
    line: Optional[int] = None
    end_line: Optional[int] = None
    priority: Priority = Priority.LOW
    category: Category = Category.BEST_PRACTICE
    title: str = ""
    message: str
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None
    
    def to_markdown(self) -> str:
        """Convert feedback to markdown format."""
        parts = []
        
        # Header with priority and category
        header = f"**{self.priority.label}** | {self.category.label}"
        if self.title:
            header += f" | {self.title}"
        parts.append(header)
        
        # Location
        if self.file:
            location = f"📍 `{self.file}`"
            if self.line:
                location += f" (line {self.line}"
                if self.end_line and self.end_line != self.line:
                    location += f"-{self.end_line}"
                location += ")"
            parts.append(location)
        
        # Message
        parts.append("")
        parts.append(self.message)
        
        # Code snippet
        if self.code_snippet:
            parts.append("")
            parts.append("```")
            parts.append(self.code_snippet)
            parts.append("```")
        
        # Suggestion
        if self.suggestion:
            parts.append("")
            parts.append("💡 **Suggestion:**")
            parts.append(self.suggestion)
        
        return "\n".join(parts)
    
    def to_table_row(self) -> str:
        """Convert to markdown table row."""
        file_col = f"`{self.file}`" if self.file else "-"
        line_col = str(self.line) if self.line else "-"
        message = self.title if self.title else self.message[:60]
        if len(self.message) > 60 and not self.title:
            message += "..."
        return f"| {file_col} | {line_col} | {message} |"
