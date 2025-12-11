"""
PR Structure Analyzer - validates PR title, description, and linked issues.
"""

import re
from typing import Optional

from .base import BaseAnalyzer, ReviewContext
from ..models.feedback import Feedback, Priority, Category
from ..config import ReviewConfig


class StructureAnalyzer(BaseAnalyzer):
    """Analyzes PR structure: title, description, linked issues, screenshots."""
    
    name = "structure"
    description = "Validates PR structure and metadata"
    
    def analyze(self, context: ReviewContext) -> list[Feedback]:
        """Analyze PR structure."""
        feedbacks = []
        config = context.config or ReviewConfig()
        pr_config = config.pr_structure
        
        # Check title format
        title_feedback = self._check_title(context.pr.title, pr_config.title_pattern)
        if title_feedback:
            feedbacks.append(title_feedback)
        
        # Check description
        desc_feedbacks = self._check_description(
            context.pr.body,
            pr_config.require_description,
            pr_config.min_description_length
        )
        feedbacks.extend(desc_feedbacks)
        
        # Check linked issues
        if pr_config.require_linked_issue:
            issue_feedback = self._check_linked_issue(context.pr.body)
            if issue_feedback:
                feedbacks.append(issue_feedback)
        
        # Check screenshots for UI changes
        if context.has_ui_changes():
            screenshot_feedback = self._check_screenshots(context.pr.body)
            if screenshot_feedback:
                feedbacks.append(screenshot_feedback)
        
        # Check PR size
        size_feedbacks = self._check_pr_size(context, config.pr_size)
        feedbacks.extend(size_feedbacks)
        
        return feedbacks
    
    def _check_title(self, title: str, pattern: str) -> Optional[Feedback]:
        """Check if title matches the expected pattern."""
        if not pattern:
            return None
        
        if not re.match(pattern, title):
            return Feedback(
                priority=Priority.MEDIUM,
                category=Category.STRUCTURE,
                title="PR Title Format",
                message=f"PR title doesn't follow the conventional format.\n\n"
                       f"**Current:** `{title}`\n\n"
                       f"**Expected format:** `type(scope): description`\n\n"
                       f"**Types:** feat, fix, docs, style, refactor, test, chore",
                suggestion="Example: `feat(auth): add OAuth login support`"
            )
        return None
    
    def _check_description(
        self,
        body: Optional[str],
        require_description: bool,
        min_length: int
    ) -> list[Feedback]:
        """Check PR description quality."""
        feedbacks = []
        
        if not body or not body.strip():
            if require_description:
                feedbacks.append(Feedback(
                    priority=Priority.MEDIUM,
                    category=Category.STRUCTURE,
                    title="Missing PR Description",
                    message="This PR has no description. A good description helps reviewers understand the context and purpose of your changes.",
                    suggestion="Add a description explaining:\n- What changes were made\n- Why these changes were needed\n- How to test the changes"
                ))
        elif len(body.strip()) < min_length:
            feedbacks.append(Feedback(
                priority=Priority.LOW,
                category=Category.STRUCTURE,
                title="Short PR Description",
                message=f"PR description is very short ({len(body.strip())} chars). Consider adding more context.",
                suggestion="Include: context, motivation, testing steps, and any breaking changes."
            ))
        
        return feedbacks
    
    def _check_linked_issue(self, body: Optional[str]) -> Optional[Feedback]:
        """Check if PR links to an issue."""
        if not body:
            return Feedback(
                priority=Priority.LOW,
                category=Category.STRUCTURE,
                title="No Linked Issue",
                message="This PR doesn't appear to link to any issue.",
                suggestion="Link to related issues using: `Closes #123`, `Fixes #456`, or `Relates to #789`"
            )
        
        # Check for issue references
        issue_patterns = [
            r"(close[sd]?|fix(e[sd])?|resolve[sd]?)\s+#\d+",
            r"#\d+",
            r"https://github\.com/[^/]+/[^/]+/issues/\d+"
        ]
        
        for pattern in issue_patterns:
            if re.search(pattern, body, re.IGNORECASE):
                return None
        
        return Feedback(
            priority=Priority.LOW,
            category=Category.STRUCTURE,
            title="No Linked Issue",
            message="This PR doesn't appear to link to any issue.",
            suggestion="Link to related issues using: `Closes #123`, `Fixes #456`, or `Relates to #789`"
        )
    
    def _check_screenshots(self, body: Optional[str]) -> Optional[Feedback]:
        """Check if UI changes include screenshots."""
        if not body:
            return Feedback(
                priority=Priority.MEDIUM,
                category=Category.STRUCTURE,
                title="Missing Screenshots",
                message="This PR includes UI changes but no screenshots were found in the description.",
                suggestion="Add before/after screenshots to help reviewers understand the visual impact."
            )
        
        # Check for image references
        image_patterns = [
            r"!\[.*\]\(.*\)",  # Markdown image
            r"<img\s",         # HTML img tag
            r"\.png|\.jpg|\.jpeg|\.gif|\.webp",  # Image extensions
            r"screenshot|screen shot|screen-shot"  # Keywords
        ]
        
        for pattern in image_patterns:
            if re.search(pattern, body, re.IGNORECASE):
                return None
        
        return Feedback(
            priority=Priority.MEDIUM,
            category=Category.STRUCTURE,
            title="Missing Screenshots",
            message="This PR includes UI changes but no screenshots were found in the description.",
            suggestion="Add before/after screenshots to help reviewers understand the visual impact."
        )
    
    def _check_pr_size(self, context: ReviewContext, size_config) -> list[Feedback]:
        """Check if PR is too large."""
        feedbacks = []
        
        files_changed = len(context.files)
        lines_added = sum(f.additions for f in context.files)
        lines_deleted = sum(f.deletions for f in context.files)
        
        # Check file count
        if files_changed > size_config.max_files:
            feedbacks.append(Feedback(
                priority=Priority.MEDIUM,
                category=Category.STRUCTURE,
                title="Large PR - Many Files",
                message=f"This PR changes **{files_changed} files**, which exceeds the recommended limit of {size_config.max_files}.",
                suggestion="Consider breaking this PR into smaller, focused PRs for easier review."
            ))
        elif files_changed > size_config.max_files * size_config.warning_threshold:
            feedbacks.append(Feedback(
                priority=Priority.LOW,
                category=Category.STRUCTURE,
                title="PR Size Warning",
                message=f"This PR changes {files_changed} files, approaching the limit of {size_config.max_files}.",
                suggestion="Consider if this can be split into smaller PRs."
            ))
        
        # Check lines added
        if lines_added > size_config.max_lines_added:
            feedbacks.append(Feedback(
                priority=Priority.MEDIUM,
                category=Category.STRUCTURE,
                title="Large PR - Many Lines Added",
                message=f"This PR adds **+{lines_added} lines**, which exceeds the recommended limit of {size_config.max_lines_added}.",
                suggestion="Large PRs are harder to review thoroughly. Consider splitting into smaller changes."
            ))
        
        # Check lines deleted
        if lines_deleted > size_config.max_lines_deleted:
            feedbacks.append(Feedback(
                priority=Priority.LOW,
                category=Category.STRUCTURE,
                title="Large Deletion",
                message=f"This PR deletes **{lines_deleted} lines**. Ensure this is intentional.",
                suggestion="Verify that important code or documentation isn't being removed accidentally."
            ))
        
        return feedbacks
