"""
Configuration module for AI Reviewer.
Loads settings from environment variables and optional .ai-reviewer.yml file.
"""

import os
import yaml
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


class PRStructureConfig(BaseModel):
    """PR structure validation configuration."""
    title_pattern: str = r"^(feat|fix|docs|style|refactor|test|chore)(\(.+\))?:.+"
    require_description: bool = True
    min_description_length: int = 20
    require_linked_issue: bool = False
    require_screenshot_for: list[str] = Field(default_factory=lambda: ["*.css", "*.html", "*.jsx", "*.tsx", "*.vue"])


class PRSizeConfig(BaseModel):
    """PR size limits configuration."""
    max_files: int = 20
    max_lines_added: int = 500
    max_lines_deleted: int = 300
    warning_threshold: float = 0.7


class TestingConfig(BaseModel):
    """Testing requirements configuration."""
    require_tests_for: list[str] = Field(default_factory=lambda: ["src/**/*.py", "src/**/*.js"])
    test_file_patterns: list[str] = Field(default_factory=lambda: [
        "test_*.py", "*_test.py", "tests/*.py",
        "*.test.js", "*.spec.js", "*.test.ts", "*.spec.ts"
    ])


class SecurityPattern(BaseModel):
    """Security pattern definition."""
    name: str
    regex: str
    severity: str = "HIGH"
    description: str = ""


class SecurityConfig(BaseModel):
    """Security scanning configuration."""
    patterns: list[SecurityPattern] = Field(default_factory=lambda: [
        SecurityPattern(
            name="SQL Injection",
            regex=r'execute\(.*[+%].*\)|f".*SELECT.*\{.*\}"',
            severity="HIGH",
            description="Potential SQL injection vulnerability"
        ),
        SecurityPattern(
            name="XSS Risk",
            regex=r'innerHTML\s*=|dangerouslySetInnerHTML|v-html',
            severity="HIGH",
            description="Potential XSS vulnerability"
        ),
        SecurityPattern(
            name="Hardcoded Secret",
            regex=r'(password|secret|api_key|apikey|token)\s*=\s*["\'][^"\']{8,}["\']',
            severity="HIGH",
            description="Possible hardcoded secret or credential"
        ),
        SecurityPattern(
            name="Eval Usage",
            regex=r'\beval\s*\(|\bexec\s*\(',
            severity="MEDIUM",
            description="Use of eval/exec can be dangerous"
        ),
    ])


class NamingConventionConfig(BaseModel):
    """Naming convention patterns."""
    python: dict[str, str] = Field(default_factory=lambda: {
        "class": r"^[A-Z][a-zA-Z0-9]*$",
        "function": r"^[a-z_][a-z0-9_]*$",
        "constant": r"^[A-Z][A-Z0-9_]*$"
    })
    javascript: dict[str, str] = Field(default_factory=lambda: {
        "class": r"^[A-Z][a-zA-Z0-9]*$",
        "function": r"^[a-z][a-zA-Z0-9]*$",
        "constant": r"^[A-Z][A-Z0-9_]*$"
    })


class ReviewConfig(BaseModel):
    """Main review configuration."""
    pr_structure: PRStructureConfig = Field(default_factory=PRStructureConfig)
    pr_size: PRSizeConfig = Field(default_factory=PRSizeConfig)
    testing: TestingConfig = Field(default_factory=TestingConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    naming: NamingConventionConfig = Field(default_factory=NamingConventionConfig)
    ignore: list[str] = Field(default_factory=lambda: [
        "*.lock", "*.min.js", "*.min.css",
        "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
        "dist/*", "build/*", "node_modules/*", ".git/*"
    ])


class Config:
    """Main configuration class."""
    
    def __init__(self):
        # Environment variables
        self.github_token: str = os.getenv("GITHUB_TOKEN", "")
        self.openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
        self.pr_number: int = int(os.getenv("PR_NUMBER", "0"))
        self.repo: str = os.getenv("REPO", "")
        self.pr_title: str = os.getenv("PR_TITLE", "")
        self.pr_body: str = os.getenv("PR_BODY", "") or ""
        self.base_sha: str = os.getenv("BASE_SHA", "")
        self.head_sha: str = os.getenv("HEAD_SHA", "")
        self.base_ref: str = os.getenv("BASE_REF", "")
        self.head_ref: str = os.getenv("HEAD_REF", "")
        
        # OpenAI settings
        self.openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.max_tokens: int = int(os.getenv("MAX_TOKENS", "4096"))
        
<<<<<<< HEAD
        # Review Behavior
        self.review_comment_lgtm: bool = os.getenv("REVIEW_COMMENT_LGTM", "false").lower() == "true"
        self.review_simple_changes: bool = os.getenv("REVIEW_SIMPLE_CHANGES", "false").lower() == "true"
        
=======
>>>>>>> ee52ae3a3e51986e8037cbbc9acbb4a77ad55d82
        # Storage settings (v2)
        self.enable_storage: bool = os.getenv("ENABLE_STORAGE", "false").lower() == "true"
        self.mongodb_uri: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.mongodb_database: str = os.getenv("MONGODB_DATABASE", "ai_reviewer")
        self.redis_host: str = os.getenv("REDIS_HOST", "localhost")
<<<<<<< HEAD
        self.redis_port: int = int(os.getenv("REDIS_PORT", "6379") or "6379")
=======
        self.redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
>>>>>>> ee52ae3a3e51986e8037cbbc9acbb4a77ad55d82
        self.redis_password: str = os.getenv("REDIS_PASSWORD", "") or None
        
        # Load review configuration
        self.review: ReviewConfig = self._load_review_config()
    
    def _load_review_config(self) -> ReviewConfig:
        """Load review configuration from .ai-reviewer.yml if exists."""
        config_paths = [
            Path(".ai-reviewer.yml"),
            Path(".ai-reviewer.yaml"),
            Path(".github/ai-reviewer.yml"),
        ]
        
        for config_path in config_paths:
            if config_path.exists():
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f) or {}
                    return ReviewConfig(**data)
                except Exception as e:
                    print(f"Warning: Failed to load {config_path}: {e}")
        
        return ReviewConfig()
    
    @property
    def repo_owner(self) -> str:
        """Get repository owner."""
        return self.repo.split("/")[0] if "/" in self.repo else ""
    
    @property
    def repo_name(self) -> str:
        """Get repository name."""
        return self.repo.split("/")[1] if "/" in self.repo else self.repo
    
    def validate(self) -> list[str]:
        """Validate configuration and return list of errors."""
        errors = []
        if not self.github_token:
            errors.append("GITHUB_TOKEN is required")
        if not self.openai_api_key:
            errors.append("OPENAI_API_KEY is required")
        if not self.pr_number:
            errors.append("PR_NUMBER is required")
        if not self.repo:
            errors.append("REPO is required")
        return errors


# Global config instance
config: Optional[Config] = None


def get_config() -> Config:
    """Get or create configuration instance."""
    global config
    if config is None:
        config = Config()
    return config
