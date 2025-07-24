"""Tweet streaming service for the Ear-to-Ground agent."""

import asyncio
import json
import logging
import os
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles

from agents.ear_to_ground.card import AGENT_CARD

logger = logging.getLogger("orbit.ear_to_ground_agent.streaming_service")


class SLIMMessage:
    """Message format compatible with SLIM transport."""
    def __init__(self, payload):
        self.payload = payload
        self.headers = {}
        self.reply_to = None
        self.correlation_id = None  
        self.message_id = None
        
    def serialize(self):
        """Serialize message for SLIM transport."""
        import json
        data = {
            'payload': self.payload,
            'headers': self.headers,
            'reply_to': self.reply_to,
            'correlation_id': self.correlation_id,
            'message_id': self.message_id
        }
        return json.dumps(data).encode('utf-8')


class TweetStreamingService:
    """Service responsible for streaming crisis tweets."""
    
    def __init__(self, transport, broadcast_topic: str):
        self.transport = transport
        self.broadcast_topic = broadcast_topic
        self.tweet_file = os.getenv("ORBIT_TWEET_FILE", "data/tweets_astronomer.json")
        self.tweet_rate = float(os.getenv("TWEET_STREAM_RATE", "1.0"))
        self.tweets: List[Dict[str, Any]] = []
        self._is_running = False
        # Convert agent card to dict following Coffee AGNTCY pattern
        self.agent_card = AGENT_CARD.model_dump(mode="json", exclude_none=True)
        
    async def start(self) -> None:
        """Start the tweet streaming service."""
        if self._is_running:
            logger.warning("Tweet streaming service is already running")
            return
            
        # Wait for server to fully initialize
        await asyncio.sleep(5)
        
        logger.info("Starting tweet streaming service...")
        self._is_running = True
        
        try:
            await self._load_tweets()
            await self._stream_tweets()
        except Exception as e:
            logger.error(f"Error in tweet streaming service: {e}")
            raise
        finally:
            self._is_running = False
            
    async def _load_tweets(self) -> None:
        """Load tweets from JSON file asynchronously."""
        tweet_path = Path(self.tweet_file)
        
        if not tweet_path.exists():
            logger.error(f"Tweet file not found: {self.tweet_file}")
            raise FileNotFoundError(f"Tweet file not found: {self.tweet_file}")
            
        try:
            async with aiofiles.open(tweet_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                self.tweets = json.loads(content)
                
            logger.info(f"Loaded {len(self.tweets)} tweets for streaming")
            
            # Validate tweet structure
            self._validate_tweets()
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing tweet file: {e}")
            raise
        except UnicodeDecodeError as e:
            logger.error(f"Error reading tweet file encoding: {e}")
            raise
            
    def _validate_tweets(self) -> None:
        """Validate tweet data structure."""
        required_fields = {'id', 'text', 'author'}
        
        for i, tweet in enumerate(self.tweets):
            if not isinstance(tweet, dict):
                raise ValueError(f"Tweet {i} is not a dictionary")
                
            missing_fields = required_fields - set(tweet.keys())
            if missing_fields:
                raise ValueError(f"Tweet {i} missing required fields: {missing_fields}")
                
        logger.info(f"Validated {len(self.tweets)} tweets successfully")
            
    async def _stream_tweets(self) -> None:
        """Stream tweets via SLIM transport."""
        for tweet in self.tweets:
            if not self._is_running:
                break
                
            try:
                await self._publish_tweet(tweet)
                
                # Variable delay between tweets (0.8x to 1.5x base rate) 
                delay = self.tweet_rate * random.uniform(0.8, 1.5)
                await asyncio.sleep(delay)
                
            except Exception as e:
                logger.error(f"Error broadcasting tweet {tweet.get('id', 'unknown')}: {e}")
                continue
                
        await self._publish_completion()
        logger.info("Tweet streaming service completed successfully")
        
    async def _publish_tweet(self, tweet: Dict[str, Any]) -> None:
        """Publish a single tweet event."""
        tweet_data = {
            "event_type": "crisis_tweet",
            "agent_id": "ear-to-ground-agent",
            "timestamp": tweet.get("timestamp"),
            "tweet": tweet,
            "source": "ear_to_ground"
        }
        
        # Create SLIM-compatible message
        message = SLIMMessage(payload=tweet_data)
        
        if self.transport:
            await self.transport.publish(
                topic=self.broadcast_topic,
                message=message
            )
            
        logger.info(f"Broadcasted crisis tweet: {tweet['id']} from {tweet['author']}")
        
    async def _publish_completion(self) -> None:
        """Publish stream completion event."""
        completion_data = {
            "event_type": "stream_complete",
            "agent_id": "ear-to-ground-agent",
            "message": "All crisis tweets have been streamed",
            "source": "ear_to_ground"
        }
        
        # Create SLIM-compatible message
        message = SLIMMessage(payload=completion_data)
        
        if self.transport:
            await self.transport.publish(
                topic=self.broadcast_topic,
                message=message
            )
            
    def stop(self) -> None:
        """Stop the streaming service."""
        self._is_running = False
        logger.info("Tweet streaming service stopped")