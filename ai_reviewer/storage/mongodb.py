"""
MongoDB client for storing PR review documents.
"""

from datetime import datetime
from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection


class MongoDBClient:
    """
    MongoDB client for storing and retrieving PR review documents.
    
    Documents are stored in the 'reviews' collection with full review data
    including feedbacks, metrics, and diff content for future vectorization.
    """
    
    def __init__(self, connection_string: str, database_name: str = "ai_reviewer"):
        """
        Initialize MongoDB client.
        
        Args:
            connection_string: MongoDB connection URI
            database_name: Database name to use
        """
        self.client: MongoClient = MongoClient(connection_string)
        self.db: Database = self.client[database_name]
        self.reviews: Collection = self.db["reviews"]
        
        # Create indexes for efficient queries
        self._ensure_indexes()
    
    def _ensure_indexes(self) -> None:
        """Create indexes for common query patterns."""
        self.reviews.create_index("pr_number")
        self.reviews.create_index("repo")
        self.reviews.create_index("timestamp")
        self.reviews.create_index([("repo", 1), ("pr_number", 1)])
    
    def save_review(self, review_data: dict) -> str:
        """
        Save a review result to MongoDB.
        
        Args:
            review_data: Dictionary containing review result data
            
        Returns:
            str: The inserted document's ObjectId as string
        """
        # Add metadata
        review_data["_created_at"] = datetime.utcnow()
        review_data["_version"] = "2.0"
        
        # Insert document
        result = self.reviews.insert_one(review_data)
        return str(result.inserted_id)
    
    def get_review(self, pr_number: int, repo: str) -> Optional[dict]:
        """
        Get the latest review for a specific PR.
        
        Args:
            pr_number: PR number
            repo: Repository in format 'owner/repo'
            
        Returns:
            Review document or None if not found
        """
        return self.reviews.find_one(
            {"pr_number": pr_number, "repo": repo},
            sort=[("timestamp", -1)]
        )
    
    def get_reviews_by_repo(self, repo: str, limit: int = 100) -> list[dict]:
        """
        Get all reviews for a repository.
        
        Args:
            repo: Repository in format 'owner/repo'
            limit: Maximum number of reviews to return
            
        Returns:
            List of review documents
        """
        cursor = self.reviews.find(
            {"repo": repo}
        ).sort("timestamp", -1).limit(limit)
        return list(cursor)
    
    def get_reviews_by_date_range(
        self, 
        start: datetime, 
        end: datetime,
        repo: Optional[str] = None
    ) -> list[dict]:
        """
        Get reviews within a date range.
        
        Args:
            start: Start datetime
            end: End datetime
            repo: Optional repository filter
            
        Returns:
            List of review documents
        """
        query = {"timestamp": {"$gte": start, "$lte": end}}
        if repo:
            query["repo"] = repo
            
        cursor = self.reviews.find(query).sort("timestamp", -1)
        return list(cursor)
    
    def get_review_by_id(self, document_id: str) -> Optional[dict]:
        """
        Get a review by its MongoDB ObjectId.
        
        Args:
            document_id: ObjectId as string
            
        Returns:
            Review document or None if not found
        """
        from bson import ObjectId
        return self.reviews.find_one({"_id": ObjectId(document_id)})
    
    def get_reviews_pending_vectorization(self, limit: int = 50) -> list[dict]:
        """
        Get reviews that haven't been vectorized yet.
        
        Args:
            limit: Maximum number of reviews to return
            
        Returns:
            List of review documents pending vectorization
        """
        cursor = self.reviews.find(
            {"vectorized": {"$ne": True}}
        ).sort("timestamp", -1).limit(limit)
        return list(cursor)
    
    def mark_as_vectorized(self, document_id: str) -> bool:
        """
        Mark a review as vectorized.
        
        Args:
            document_id: ObjectId as string
            
        Returns:
            True if update was successful
        """
        from bson import ObjectId
        result = self.reviews.update_one(
            {"_id": ObjectId(document_id)},
            {"$set": {"vectorized": True, "vectorized_at": datetime.utcnow()}}
        )
        return result.modified_count > 0
    
    def close(self) -> None:
        """Close the MongoDB connection."""
        self.client.close()
