"""
Documentation Analyzer - checks for documentation updates.
"""

import re
from typing import Optional

from .base import BaseAnalyzer, ReviewContext
from ..models.feedback import Feedback, Priority, Category
from ..config import ReviewConfig


class DocAnalyzer(BaseAnalyzer):
    """Analyzes documentation requirements for changed files."""
    
    name = "doc"
    description = "Checks if documentation needs to be updated"
    
    # Files that indicate API changes
    API_PATTERNS = [
        r"api/",
        r"routes/",
        r"endpoints/",
        r"views\.py$",
        r"router\.",
        r"controller\.",
    ]
    
    # Documentation files
    DOC_FILES = [
        "README.md",
        "README.rst",
        "CHANGELOG.md",
        "CHANGELOG.rst",
        "HISTORY.md",
        "HISTORY.rst",
        "docs/",
        "documentation/",
        "API.md",
    ]
    
    def analyze(self, context: ReviewContext) -> list[Feedback]:
        """Analyze documentation requirements."""
        feedbacks = []
        
        changed_filenames = [f.filename for f in context.files]
        
        # Check for API changes without docs
        api_feedback = self._check_api_docs(context.files, changed_filenames)
        if api_feedback:
            feedbacks.append(api_feedback)
        
        # Check for new features without README update
        readme_feedback = self._check_readme(context.files, changed_filenames)
        if readme_feedback:
            feedbacks.append(readme_feedback)
        
        # Check for changelog updates
        changelog_feedback = self._check_changelog(context, changed_filenames)
        if changelog_feedback:
            feedbacks.append(changelog_feedback)
        
        # Check for docstring in new functions
        docstring_feedbacks = self._check_docstrings(context.files)
        feedbacks.extend(docstring_feedbacks)
        
        return feedbacks
    
    def _check_api_docs(self, files, changed_filenames: list[str]) -> Optional[Feedback]:
        """Check if API changes have corresponding documentation updates."""
        has_api_changes = False
        has_doc_changes = False
        
        for filename in changed_filenames:
            # Check for API file patterns
            for pattern in self.API_PATTERNS:
                if re.search(pattern, filename, re.IGNORECASE):
                    has_api_changes = True
                    break
            
            # Check for doc file changes
            for doc_pattern in self.DOC_FILES:
                if doc_pattern in filename.lower():
                    has_doc_changes = True
                    break
        
        if has_api_changes and not has_doc_changes:
            return Feedback(
                priority=Priority.LOW,
                category=Category.DOCUMENTATION,
                title="API Changes Without Documentation",
                message="This PR appears to modify API endpoints but no documentation files were updated.",
                suggestion="Consider updating API documentation (README, API.md, or docs/) to reflect the changes."
            )
        
        return None
    
    def _check_readme(self, files, changed_filenames: list[str]) -> Optional[Feedback]:
        """Check if significant changes warrant README update."""
        # Count new files (potential new features)
        new_files = [f for f in files if f.status == "added" and not f.is_test_file]
        significant_additions = sum(f.additions for f in files if not f.is_test_file) > 200
        
        readme_changed = any("readme" in f.lower() for f in changed_filenames)
        
        if len(new_files) >= 3 and not readme_changed and significant_additions:
            return Feedback(
                priority=Priority.LOW,
                category=Category.DOCUMENTATION,
                title="Consider README Update",
                message=f"This PR adds {len(new_files)} new files with significant code additions. "
                       f"Consider if README needs to be updated.",
                suggestion="Update README if this PR introduces new features, dependencies, or usage patterns."
            )
        
        return None
    
    def _check_changelog(self, context: ReviewContext, changed_filenames: list[str]) -> Optional[Feedback]:
        """Check if PR should update changelog."""
        # Check if this is a significant PR (not just fixes/refactors)
        title = context.pr.title.lower()
        is_feature = any(x in title for x in ["feat", "feature", "add", "new", "implement"])
        is_breaking = any(x in title for x in ["breaking", "major", "deprecate"])
        
        changelog_changed = any("changelog" in f.lower() or "history" in f.lower() for f in changed_filenames)
        
        if (is_feature or is_breaking) and not changelog_changed:
            priority = Priority.MEDIUM if is_breaking else Priority.LOW
            return Feedback(
                priority=priority,
                category=Category.DOCUMENTATION,
                title="Consider CHANGELOG Update",
                message="This PR appears to introduce new features or breaking changes.",
                suggestion="Add an entry to CHANGELOG.md describing the changes."
            )
        
        return None
    
    def _check_docstrings(self, files) -> list[Feedback]:
        """Check for missing docstrings in new Python functions/classes."""
        feedbacks = []
        
        for file in files:
            if file.extension != "py" or not file.patch:
                continue
            
            # Parse the patch to find new function/class definitions
            lines = file.patch.split('\n')
            current_line = 0
            in_new_block = False
            
            for i, line in enumerate(lines):
                if line.startswith('@@'):
                    match = re.match(r'@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@', line)
                    if match:
                        current_line = int(match.group(1))
                    continue
                
                if line.startswith('+') and not line.startswith('+++'):
                    content = line[1:]
                    
                    # Check for new function/class without docstring
                    if re.match(r'\s*(def|class)\s+\w+', content):
                        # Look for docstring in next few lines
                        has_docstring = False
                        for j in range(i + 1, min(i + 4, len(lines))):
                            next_line = lines[j][1:] if lines[j].startswith('+') else lines[j]
                            if '"""' in next_line or "'''" in next_line:
                                has_docstring = True
                                break
                            if next_line.strip() and not next_line.strip().startswith('#'):
                                break
                        
                        if not has_docstring:
                            match = re.match(r'\s*(def|class)\s+(\w+)', content)
                            if match:
                                kind = match.group(1)
                                name = match.group(2)
                                # Skip private methods and dunder methods
                                if not name.startswith('_') or name.startswith('__') and name.endswith('__'):
                                    if not name.startswith('_'):
                                        feedbacks.append(Feedback(
                                            file=file.filename,
                                            line=current_line,
                                            priority=Priority.NIT,
                                            category=Category.DOCUMENTATION,
                                            title="Missing Docstring",
                                            message=f"New {kind} `{name}` is missing a docstring.",
                                            suggestion=f"Add a docstring explaining what this {kind} does."
                                        ))
                    
                    current_line += 1
                elif not line.startswith('-'):
                    current_line += 1
        
        return feedbacks
