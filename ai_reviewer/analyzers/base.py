"""
Base analyzer class and review context.
"""

from abc import ABC, abstractmethod
from typing import Optional
from pydantic import BaseModel, Field

from ..github.models import PullRequest, PRFile
from ..models.feedback import Feedback
from ..config import ReviewConfig


class ReviewContext(BaseModel):
    """Context for review analysis."""
    pr: PullRequest
    files: list[PRFile] = Field(default_factory=list)
    diff: str = ""
    config: Optional[ReviewConfig] = None
    
    class Config:
        arbitrary_types_allowed = True
    
    def get_files_by_extension(self, *extensions: str) -> list[PRFile]:
        """Get files filtered by extension."""
        return [f for f in self.files if f.extension in extensions]
    
    def get_source_files(self) -> list[PRFile]:
        """Get non-test source files."""
        return [f for f in self.files if not f.is_test_file]
    
    def get_test_files(self) -> list[PRFile]:
        """Get test files."""
        return [f for f in self.files if f.is_test_file]
    
    def has_ui_changes(self) -> bool:
        """Check if PR has UI-related changes."""
        ui_extensions = {"css", "scss", "sass", "less", "html", "jsx", "tsx", "vue", "svelte"}
        return any(f.extension in ui_extensions for f in self.files)


class BaseAnalyzer(ABC):
    """Base class for all analyzers."""
    
    name: str = "base"
    description: str = "Base analyzer"
    
    def __init__(self, config: Optional[ReviewConfig] = None):
        """Initialize analyzer with optional config."""
        self.config = config
    
    @abstractmethod
    def analyze(self, context: ReviewContext) -> list[Feedback]:
        """
        Analyze the PR and return feedback.
        
        Args:
            context: Review context with PR details
            
        Returns:
            List of Feedback objects
        """
        pass
    
    def should_skip_file(self, file: PRFile) -> bool:
        """Check if file should be skipped based on ignore patterns."""
        if not self.config:
            return False
        
        import fnmatch
        for pattern in self.config.ignore:
            if fnmatch.fnmatch(file.filename, pattern):
                return True
        return False
