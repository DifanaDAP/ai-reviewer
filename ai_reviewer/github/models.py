"""
Data models for GitHub API responses.
"""

from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class PRFile(BaseModel):
    """Represents a file changed in a PR."""
    filename: str
    status: str  # added, removed, modified, renamed
    additions: int = 0
    deletions: int = 0
    changes: int = 0
    patch: Optional[str] = None
    previous_filename: Optional[str] = None
    
    @property
    def extension(self) -> str:
        """Get file extension."""
        parts = self.filename.rsplit(".", 1)
        return parts[1] if len(parts) > 1 else ""
    
    @property
    def is_test_file(self) -> bool:
        """Check if this is a test file."""
        name = self.filename.lower()
        test_indicators = ["test_", "_test.", ".test.", ".spec.", "/tests/", "/test/"]
        return any(indicator in name for indicator in test_indicators)


class Commit(BaseModel):
    """Represents a commit in a PR."""
    sha: str
    message: str
    author: Optional[str] = None
    date: Optional[datetime] = None


class PullRequest(BaseModel):
    """Represents a Pull Request."""
    number: int
    title: str
    body: Optional[str] = None
    state: str = "open"
    base_sha: str = ""
    head_sha: str = ""
    base_ref: str = ""
    head_ref: str = ""
    files: list[PRFile] = Field(default_factory=list)
    commits: list[Commit] = Field(default_factory=list)
    
    @property
    def total_additions(self) -> int:
        """Total lines added."""
        return sum(f.additions for f in self.files)
    
    @property
    def total_deletions(self) -> int:
        """Total lines deleted."""
        return sum(f.deletions for f in self.files)
    
    @property
    def total_changes(self) -> int:
        """Total lines changed."""
        return self.total_additions + self.total_deletions
    
    @property
    def file_count(self) -> int:
        """Number of files changed."""
        return len(self.files)


class ReviewComment(BaseModel):
    """Represents a review comment to post."""
    path: str
    line: int
    body: str
    side: str = "RIGHT"  # LEFT for deletions, RIGHT for additions


class Review(BaseModel):
    """Represents a full review to post."""
    body: str
    event: str = "COMMENT"  # APPROVE, REQUEST_CHANGES, COMMENT
    comments: list[ReviewComment] = Field(default_factory=list)
