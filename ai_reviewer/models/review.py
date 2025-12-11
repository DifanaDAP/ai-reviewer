"""
Review result models.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from .feedback import Feedback, Priority


class PRMetrics(BaseModel):
    """Metrics about the PR."""
    files_changed: int = 0
    lines_added: int = 0
    lines_deleted: int = 0
    total_changes: int = 0
    test_files_changed: int = 0
    source_files_changed: int = 0
    
    @property
    def size_category(self) -> str:
        """Categorize PR size."""
        if self.files_changed <= 3 and self.total_changes <= 50:
            return "XS"
        elif self.files_changed <= 5 and self.total_changes <= 150:
            return "S"
        elif self.files_changed <= 10 and self.total_changes <= 300:
            return "M"
        elif self.files_changed <= 20 and self.total_changes <= 500:
            return "L"
        else:
            return "XL"
    
    @property
    def size_emoji(self) -> str:
        """Get emoji for size."""
        return {
            "XS": "🟢",
            "S": "🟢",
            "M": "🟡",
            "L": "🟠",
            "XL": "🔴"
        }[self.size_category]


class ReviewResult(BaseModel):
    """Complete review result."""
    pr_number: int
    pr_title: str
    repo: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metrics: PRMetrics = Field(default_factory=PRMetrics)
    feedbacks: list[Feedback] = Field(default_factory=list)
    summary: str = ""
    positives: list[str] = Field(default_factory=list)
    
    @property
    def high_priority_count(self) -> int:
        """Count of HIGH priority issues."""
        return len([f for f in self.feedbacks if f.priority == Priority.HIGH])
    
    @property
    def medium_priority_count(self) -> int:
        """Count of MEDIUM priority issues."""
        return len([f for f in self.feedbacks if f.priority == Priority.MEDIUM])
    
    @property
    def low_priority_count(self) -> int:
        """Count of LOW priority issues."""
        return len([f for f in self.feedbacks if f.priority == Priority.LOW])
    
    @property
    def nit_count(self) -> int:
        """Count of NIT issues."""
        return len([f for f in self.feedbacks if f.priority == Priority.NIT])
    
    @property
    def overall_status(self) -> str:
        """Overall review status."""
        if self.high_priority_count > 0:
            return "🔴 Changes Requested"
        elif self.medium_priority_count > 0:
            return "🟡 Needs Attention"
        elif self.low_priority_count > 0 or self.nit_count > 0:
            return "🟢 Looking Good"
        else:
            return "✅ Approved"
    
    def get_feedbacks_by_priority(self, priority: Priority) -> list[Feedback]:
        """Get feedbacks filtered by priority."""
        return [f for f in self.feedbacks if f.priority == priority]
    
    def to_markdown(self) -> str:
        """Convert review result to markdown format."""
        lines = []
        
        # Header
        lines.append("## 🤖 AI Code Review")
        lines.append("")
        
        # Summary section
        lines.append("### 📊 Summary")
        lines.append("")
        lines.append(f"| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Files Changed | {self.metrics.files_changed} |")
        lines.append(f"| Lines Added | +{self.metrics.lines_added} |")
        lines.append(f"| Lines Deleted | -{self.metrics.lines_deleted} |")
        lines.append(f"| PR Size | {self.metrics.size_emoji} {self.metrics.size_category} |")
        lines.append(f"| Status | {self.overall_status} |")
        lines.append("")
        
        # Issue counts
        if self.feedbacks:
            lines.append(f"**Issues Found:** 🔴 {self.high_priority_count} HIGH | "
                        f"🟡 {self.medium_priority_count} MEDIUM | "
                        f"🟢 {self.low_priority_count} LOW | "
                        f"💭 {self.nit_count} NIT")
            lines.append("")
        
        # High priority issues
        high_feedbacks = self.get_feedbacks_by_priority(Priority.HIGH)
        if high_feedbacks:
            lines.append("### 🔴 HIGH Priority (Blocking)")
            lines.append("")
            lines.append("| File | Line | Issue |")
            lines.append("|------|------|-------|")
            for fb in high_feedbacks:
                lines.append(fb.to_table_row())
            lines.append("")
            
            # Details
            for fb in high_feedbacks:
                lines.append("<details>")
                lines.append(f"<summary>{fb.title or fb.message[:50]}</summary>")
                lines.append("")
                lines.append(fb.to_markdown())
                lines.append("")
                lines.append("</details>")
                lines.append("")
        
        # Medium priority issues
        medium_feedbacks = self.get_feedbacks_by_priority(Priority.MEDIUM)
        if medium_feedbacks:
            lines.append("### 🟡 MEDIUM Priority")
            lines.append("")
            lines.append("| File | Line | Issue |")
            lines.append("|------|------|-------|")
            for fb in medium_feedbacks:
                lines.append(fb.to_table_row())
            lines.append("")
        
        # Low priority issues
        low_feedbacks = self.get_feedbacks_by_priority(Priority.LOW)
        if low_feedbacks:
            lines.append("### 🟢 LOW Priority (Recommendations)")
            lines.append("")
            lines.append("| File | Line | Issue |")
            lines.append("|------|------|-------|")
            for fb in low_feedbacks:
                lines.append(fb.to_table_row())
            lines.append("")
        
        # Nitpicks
        nit_feedbacks = self.get_feedbacks_by_priority(Priority.NIT)
        if nit_feedbacks:
            lines.append("### 💭 Nitpicks")
            lines.append("")
            for fb in nit_feedbacks:
                location = f"`{fb.file}`" if fb.file else ""
                if fb.line:
                    location += f" (line {fb.line})"
                lines.append(f"- {location}: {fb.message}")
            lines.append("")
        
        # Positives
        if self.positives:
            lines.append("### ✅ What's Good")
            lines.append("")
            for positive in self.positives:
                lines.append(f"- {positive}")
            lines.append("")
        
        # Footer
        lines.append("---")
        lines.append("*Powered by AI Reviewer* 🤖")
        
        return "\n".join(lines)
