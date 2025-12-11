"""
LLM Client for AI-powered code review.
"""

import json
import re
from typing import Optional
from openai import OpenAI

from .prompts import PromptManager
from ..models.feedback import Feedback, Priority, Category


class LLMClient:
    """Client for LLM-based code analysis."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """
        Initialize LLM client.
        
        Args:
            api_key: OpenAI API key
            model: Model to use (default: gpt-4o-mini)
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def analyze_code(
        self,
        pr_title: str,
        pr_description: str,
        diff: str,
        file_count: int,
        lines_added: int,
        lines_deleted: int,
        max_tokens: int = 4096
    ) -> tuple[list[Feedback], str, list[str]]:
        """
        Analyze code changes using LLM.
        
        Args:
            pr_title: PR title
            pr_description: PR description
            diff: Code diff
            file_count: Number of files changed
            lines_added: Lines added
            lines_deleted: Lines deleted
            max_tokens: Max response tokens
            
        Returns:
            Tuple of (feedbacks, summary, positives)
        """
        # Truncate diff if too long (keep under ~8000 chars for context)
        if len(diff) > 15000:
            diff = self._truncate_diff(diff, 15000)
        
        system_prompt = PromptManager.get_system_prompt()
        user_prompt = PromptManager.get_review_prompt(
            pr_title=pr_title,
            pr_description=pr_description,
            diff=diff,
            file_count=file_count,
            lines_added=lines_added,
            lines_deleted=lines_deleted
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.3,  # Lower temperature for more consistent output
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            return self._parse_response(content)
            
        except Exception as e:
            print(f"LLM analysis error: {e}")
            return [], f"AI analysis failed: {str(e)}", []
    
    def _truncate_diff(self, diff: str, max_length: int) -> str:
        """Truncate diff while trying to keep complete hunks."""
        if len(diff) <= max_length:
            return diff
        
        lines = diff.split('\n')
        result = []
        current_length = 0
        
        for line in lines:
            if current_length + len(line) + 1 > max_length:
                result.append("\n... (diff truncated for length) ...")
                break
            result.append(line)
            current_length += len(line) + 1
        
        return '\n'.join(result)
    
    def _parse_response(self, content: str) -> tuple[list[Feedback], str, list[str]]:
        """Parse LLM response into structured feedback."""
        feedbacks = []
        summary = ""
        positives = []
        
        try:
            # Extract JSON from response
            data = json.loads(content)
            
            summary = data.get("summary", "")
            positives = data.get("positives", [])
            findings = data.get("findings", [])
            
            for finding in findings:
                try:
                    priority = self._parse_priority(finding.get("priority", "LOW"))
                    category = self._parse_category(finding.get("category", "best_practice"))
                    
                    feedback = Feedback(
                        file=finding.get("file"),
                        line=finding.get("line"),
                        priority=priority,
                        category=category,
                        title=finding.get("title", ""),
                        message=finding.get("message", ""),
                        suggestion=finding.get("suggestion")
                    )
                    feedbacks.append(feedback)
                except Exception as e:
                    print(f"Error parsing finding: {e}")
                    continue
            
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
            if json_match:
                return self._parse_response(json_match.group(1))
            
            # Fallback: treat entire response as summary
            summary = content
        
        return feedbacks, summary, positives
    
    def _parse_priority(self, priority_str: str) -> Priority:
        """Parse priority string to enum."""
        priority_map = {
            "high": Priority.HIGH,
            "medium": Priority.MEDIUM,
            "low": Priority.LOW,
            "nit": Priority.NIT,
        }
        return priority_map.get(priority_str.lower(), Priority.LOW)
    
    def _parse_category(self, category_str: str) -> Category:
        """Parse category string to enum."""
        category_map = {
            "security": Category.SECURITY,
            "performance": Category.PERFORMANCE,
            "style": Category.STYLE,
            "architecture": Category.ARCHITECTURE,
            "testing": Category.TESTING,
            "documentation": Category.DOCUMENTATION,
            "pr_structure": Category.STRUCTURE,
            "best_practice": Category.BEST_PRACTICE,
        }
        return category_map.get(category_str.lower(), Category.BEST_PRACTICE)
