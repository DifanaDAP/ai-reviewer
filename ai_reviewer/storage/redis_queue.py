"""
Redis queue for async messaging and future vectorization pipeline.
"""

import json
from typing import Optional, Generator
from datetime import datetime
import redis


class RedisQueue:
    """
    Redis queue for publishing review events and managing vectorization queue.
    
    This serves as the bridge between the PR review process and future
    repository review/vectorization systems.
    """
    
    # Channel names
    REVIEW_CHANNEL = "ai_reviewer:reviews"
    VECTORIZATION_QUEUE = "ai_reviewer:vectorization_queue"
    
    def __init__(
        self, 
        host: str = "localhost", 
        port: int = 6379, 
        db: int = 0,
        password: Optional[str] = None
    ):
        """
        Initialize Redis connection.
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Optional Redis password
        """
        self.redis = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True
        )
    
    def publish_review(self, review_data: dict, document_id: str) -> int:
        """
        Publish a review event to the reviews channel.
        
        This notifies any subscribers (like future repository review system)
        that a new review has been completed.
        
        Args:
            review_data: Review result data (will be serialized to JSON)
            document_id: MongoDB document ID for the review
            
        Returns:
            Number of subscribers that received the message
        """
        message = {
            "event": "review_completed",
            "document_id": document_id,
            "pr_number": review_data.get("pr_number"),
            "repo": review_data.get("repo"),
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": review_data.get("metrics", {}),
            "feedback_count": len(review_data.get("feedbacks", [])),
            "status": review_data.get("overall_status", "")
        }
        
        return self.redis.publish(self.REVIEW_CHANNEL, json.dumps(message))
    
    def add_to_vectorization_queue(self, document_id: str, priority: int = 0) -> int:
        """
        Add a document to the vectorization queue.
        
        The repository review system will consume from this queue to
        vectorize review data for AI analysis.
        
        Args:
            document_id: MongoDB document ID to vectorize
            priority: Priority level (higher = more urgent)
            
        Returns:
            Length of queue after adding
        """
        item = {
            "document_id": document_id,
            "priority": priority,
            "queued_at": datetime.utcnow().isoformat()
        }
        
        return self.redis.rpush(self.VECTORIZATION_QUEUE, json.dumps(item))
    
    def get_from_vectorization_queue(self, timeout: int = 0) -> Optional[dict]:
        """
        Get next item from vectorization queue (blocking if timeout > 0).
        
        Args:
            timeout: Seconds to wait for item (0 = non-blocking)
            
        Returns:
            Queue item dict or None if queue is empty
        """
        if timeout > 0:
            result = self.redis.blpop(self.VECTORIZATION_QUEUE, timeout=timeout)
            if result:
                return json.loads(result[1])
        else:
            result = self.redis.lpop(self.VECTORIZATION_QUEUE)
            if result:
                return json.loads(result)
        return None
    
    def get_queue_length(self) -> int:
        """Get the current length of the vectorization queue."""
        return self.redis.llen(self.VECTORIZATION_QUEUE)
    
    def subscribe_reviews(self) -> Generator[dict, None, None]:
        """
        Subscribe to review events.
        
        Yields review event messages as they are published.
        This is intended for the future repository review system.
        
        Yields:
            dict: Review event data
        """
        pubsub = self.redis.pubsub()
        pubsub.subscribe(self.REVIEW_CHANNEL)
        
        for message in pubsub.listen():
            if message["type"] == "message":
                yield json.loads(message["data"])
    
    def ping(self) -> bool:
        """Check if Redis connection is alive."""
        try:
            return self.redis.ping()
        except redis.ConnectionError:
            return False
    
    def close(self) -> None:
        """Close the Redis connection."""
        self.redis.close()
