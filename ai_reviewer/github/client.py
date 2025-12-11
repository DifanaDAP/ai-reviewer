"""
GitHub API client for interacting with Pull Requests.
"""

import requests
from typing import Optional
from .models import PullRequest, PRFile, Commit, Review, ReviewComment


class GitHubClient:
    """Client for GitHub API operations."""
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, token: str, repo: str):
        """
        Initialize GitHub client.
        
        Args:
            token: GitHub access token
            repo: Repository in format 'owner/repo'
        """
        self.token = token
        self.repo = repo
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
    
    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make an API request."""
        url = f"{self.BASE_URL}{endpoint}"
        response = requests.request(method, url, headers=self.headers, **kwargs)
        response.raise_for_status()
        return response
    
    def get_pull_request(self, pr_number: int) -> PullRequest:
        """
        Get pull request details.
        
        Args:
            pr_number: PR number
            
        Returns:
            PullRequest object with details
        """
        endpoint = f"/repos/{self.repo}/pulls/{pr_number}"
        response = self._request("GET", endpoint)
        data = response.json()
        
        return PullRequest(
            number=data["number"],
            title=data["title"],
            body=data.get("body"),
            state=data["state"],
            base_sha=data["base"]["sha"],
            head_sha=data["head"]["sha"],
            base_ref=data["base"]["ref"],
            head_ref=data["head"]["ref"]
        )
    
    def get_pr_files(self, pr_number: int) -> list[PRFile]:
        """
        Get list of files changed in a PR.
        
        Args:
            pr_number: PR number
            
        Returns:
            List of PRFile objects
        """
        endpoint = f"/repos/{self.repo}/pulls/{pr_number}/files"
        files = []
        page = 1
        
        while True:
            response = self._request("GET", endpoint, params={"page": page, "per_page": 100})
            data = response.json()
            
            if not data:
                break
            
            for file_data in data:
                files.append(PRFile(
                    filename=file_data["filename"],
                    status=file_data["status"],
                    additions=file_data.get("additions", 0),
                    deletions=file_data.get("deletions", 0),
                    changes=file_data.get("changes", 0),
                    patch=file_data.get("patch"),
                    previous_filename=file_data.get("previous_filename")
                ))
            
            page += 1
            if len(data) < 100:
                break
        
        return files
    
    def get_pr_commits(self, pr_number: int) -> list[Commit]:
        """
        Get list of commits in a PR.
        
        Args:
            pr_number: PR number
            
        Returns:
            List of Commit objects
        """
        endpoint = f"/repos/{self.repo}/pulls/{pr_number}/commits"
        response = self._request("GET", endpoint)
        
        commits = []
        for commit_data in response.json():
            commits.append(Commit(
                sha=commit_data["sha"],
                message=commit_data["commit"]["message"],
                author=commit_data["commit"]["author"].get("name")
            ))
        
        return commits
    
    def get_pr_diff(self, pr_number: int) -> str:
        """
        Get the diff/patch for a PR.
        
        Args:
            pr_number: PR number
            
        Returns:
            Diff string
        """
        endpoint = f"/repos/{self.repo}/pulls/{pr_number}"
        headers = {**self.headers, "Accept": "application/vnd.github.v3.diff"}
        url = f"{self.BASE_URL}{endpoint}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    
    def get_file_content(self, path: str, ref: str = "HEAD") -> Optional[str]:
        """
        Get file content at a specific ref.
        
        Args:
            path: File path in repository
            ref: Git ref (branch, tag, or SHA)
            
        Returns:
            File content as string, or None if not found
        """
        endpoint = f"/repos/{self.repo}/contents/{path}"
        try:
            response = self._request("GET", endpoint, params={"ref": ref})
            data = response.json()
            
            if data.get("encoding") == "base64":
                import base64
                return base64.b64decode(data["content"]).decode("utf-8")
            
            return data.get("content")
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise
    
    def post_review(self, pr_number: int, review: Review) -> dict:
        """
        Post a review on a PR.
        
        Args:
            pr_number: PR number
            review: Review object with body and comments
            
        Returns:
            API response data
        """
        endpoint = f"/repos/{self.repo}/pulls/{pr_number}/reviews"
        
        payload = {
            "body": review.body,
            "event": review.event,
            "comments": [
                {
                    "path": c.path,
                    "line": c.line,
                    "body": c.body,
                    "side": c.side
                }
                for c in review.comments
            ]
        }
        
        response = self._request("POST", endpoint, json=payload)
        return response.json()
    
    def post_comment(self, pr_number: int, body: str) -> dict:
        """
        Post a general comment on a PR (not a review).
        
        Args:
            pr_number: PR number
            body: Comment body
            
        Returns:
            API response data
        """
        endpoint = f"/repos/{self.repo}/issues/{pr_number}/comments"
        response = self._request("POST", endpoint, json={"body": body})
        return response.json()
    
    def get_existing_reviews(self, pr_number: int) -> list[dict]:
        """
        Get existing reviews on a PR.
        
        Args:
            pr_number: PR number
            
        Returns:
            List of review data
        """
        endpoint = f"/repos/{self.repo}/pulls/{pr_number}/reviews"
        response = self._request("GET", endpoint)
        return response.json()
