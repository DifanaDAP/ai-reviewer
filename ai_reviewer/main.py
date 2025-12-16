"""
AI PR Reviewer - Main Entry Point

This module orchestrates the entire code review process:
1. Fetches PR data from GitHub
2. Runs all analyzers (static, structure, risk, test, doc, convention)
3. Uses LLM for additional AI-powered analysis
4. Posts review comments back to GitHub
"""

import os
import sys

# Add parent directory to path when run as standalone script
if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

from ai_reviewer.config import get_config
from ai_reviewer.github.client import GitHubClient
from ai_reviewer.github.models import PullRequest, Review
from ai_reviewer.analyzers.base import ReviewContext
from ai_reviewer.analyzers.static_analyzer import StaticAnalyzer
from ai_reviewer.analyzers.structure_analyzer import StructureAnalyzer
from ai_reviewer.analyzers.risk_analyzer import RiskAnalyzer
from ai_reviewer.analyzers.test_analyzer import TestAnalyzer
from ai_reviewer.analyzers.doc_analyzer import DocAnalyzer
from ai_reviewer.analyzers.convention_analyzer import ConventionAnalyzer
from ai_reviewer.llm.client import LLMClient
from ai_reviewer.models.feedback import Feedback, Priority
from ai_reviewer.models.review import ReviewResult, PRMetrics


def run_review() -> int:
    """
    Main review execution function.
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
    print("🤖 AI PR Reviewer Starting...")
    
    # Load configuration
    config = get_config()
    
    # Validate configuration
    errors = config.validate()
    if errors:
        for error in errors:
            print(f"❌ Configuration Error: {error}")
        return 1
    
    print(f"📋 Reviewing PR #{config.pr_number} in {config.repo}")
    
    try:
        # Initialize GitHub client
        github = GitHubClient(config.github_token, config.repo)
        
        # Fetch PR data
        print("📥 Fetching PR data...")
        pr = github.get_pull_request(config.pr_number)
        pr.title = config.pr_title or pr.title
        pr.body = config.pr_body or pr.body
        
        # Fetch files and diff
        files = github.get_pr_files(config.pr_number)
        diff = github.get_pr_diff(config.pr_number)
        
        print(f"   Found {len(files)} changed files")
        
        # Create review context
        context = ReviewContext(
            pr=pr,
            files=files,
            diff=diff,
            config=config.review
        )
        
        # Run all analyzers
        print("🔍 Running analyzers...")
        all_feedbacks: list[Feedback] = []
        
        analyzers = [
            StructureAnalyzer(config.review),
            StaticAnalyzer(config.review),
            RiskAnalyzer(config.review),
            TestAnalyzer(config.review),
            DocAnalyzer(config.review),
            ConventionAnalyzer(config.review),
        ]
        
        for analyzer in analyzers:
            print(f"   ▸ {analyzer.name} analyzer...")
            feedbacks = analyzer.analyze(context)
            all_feedbacks.extend(feedbacks)
        
        print(f"   Found {len(all_feedbacks)} issues from pattern analysis")
        
        # Run LLM analysis
        print("🧠 Running AI analysis...")
        llm_feedbacks, llm_summary, positives = run_llm_analysis(config, context)
        all_feedbacks.extend(llm_feedbacks)
        
        print(f"   Found {len(llm_feedbacks)} additional issues from AI")
        
        # Deduplicate feedbacks
        all_feedbacks = deduplicate_feedbacks(all_feedbacks)
        
        # Calculate metrics
        metrics = PRMetrics(
            files_changed=len(files),
            lines_added=sum(f.additions for f in files),
            lines_deleted=sum(f.deletions for f in files),
            total_changes=sum(f.additions + f.deletions for f in files),
            test_files_changed=len([f for f in files if f.is_test_file]),
            source_files_changed=len([f for f in files if not f.is_test_file])
        )
        
        # Create review result
        result = ReviewResult(
            pr_number=config.pr_number,
            pr_title=pr.title,
            repo=config.repo,
            metrics=metrics,
            feedbacks=all_feedbacks,
            summary=llm_summary,
            positives=positives,
            diff=diff  # Store diff for future vectorization
        )
        
        # Format and post review
        print("📝 Posting review...")
        review_body = result.to_markdown()
        
        # Determine review event based on findings
        high_count = result.high_priority_count
        if high_count > 0:
            event = "REQUEST_CHANGES"
        else:
            event = "COMMENT"
        
        review = Review(
            body=review_body,
            event=event
        )
        
        github.post_review(config.pr_number, review)
        
        # Save to MongoDB if storage is enabled (v2)
        if config.enable_storage:
            print("💾 Saving review to database...")
            try:
                from ai_reviewer.storage.mongodb import MongoDBClient
                
                # Save to MongoDB
                mongo = MongoDBClient(config.mongodb_uri, config.mongodb_database)
                doc_id = mongo.save_review(result.to_mongo_dict())
                mongo.close()
                
                print(f"   ✅ Saved to MongoDB with ID: {doc_id}")
            except Exception as e:
                print(f"   ⚠️ Storage failed (non-blocking): {e}")
        
        print(f"✅ Review posted successfully!")
        print(f"   📊 {result.overall_status}")
        print(f"   🔴 {result.high_priority_count} HIGH | "
              f"🟡 {result.medium_priority_count} MEDIUM | "
              f"🟢 {result.low_priority_count} LOW | "
              f"💭 {result.nit_count} NIT")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error during review: {e}")
        import traceback
        traceback.print_exc()
        return 1


def run_llm_analysis(config, context: ReviewContext) -> tuple[list[Feedback], str, list[str]]:
    """Run LLM-powered analysis."""
    try:
        llm = LLMClient(config.openai_api_key, config.openai_model)
        
        return llm.analyze_code(
            pr_title=context.pr.title,
            pr_description=context.pr.body or "",
            diff=context.diff,
            file_count=len(context.files),
            lines_added=sum(f.additions for f in context.files),
            lines_deleted=sum(f.deletions for f in context.files),
            max_tokens=config.max_tokens
        )
    except Exception as e:
        print(f"   ⚠️ LLM analysis failed: {e}")
        return [], "", []


def deduplicate_feedbacks(feedbacks: list[Feedback]) -> list[Feedback]:
    """Remove duplicate feedbacks based on file, line, and message."""
    seen = set()
    unique = []
    
    for fb in feedbacks:
        # Create a key for deduplication
        key = (fb.file, fb.line, fb.title, fb.category)
        if key not in seen:
            seen.add(key)
            unique.append(fb)
    
    # Sort by priority (HIGH first) then by file
    priority_order = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2, Priority.NIT: 3}
    unique.sort(key=lambda x: (priority_order.get(x.priority, 4), x.file or ""))
    
    return unique


def main():
    """Main entry point."""
    sys.exit(run_review())


if __name__ == "__main__":
    main()
