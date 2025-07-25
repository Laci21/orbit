"""Tweet streaming service for the Ear-to-Ground agent."""

import asyncio
import json
import logging
import os
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles
import aiohttp

from agents.ear_to_ground.card import AGENT_CARD

logger = logging.getLogger("orbit.ear_to_ground_agent.streaming_service")




class TweetStreamingService:
    """Service responsible for streaming crisis tweets and calling agents directly."""
    
    def __init__(self, transport, broadcast_topic: Optional[str]):
        self.transport = transport
        self.broadcast_topic = broadcast_topic
        self.tweet_file = os.getenv("ORBIT_TWEET_FILE", "data/tweets_astronomer.json")
        self.tweet_rate = float(os.getenv("TWEET_STREAM_RATE", "1.0"))
        self.tweets: List[Dict[str, Any]] = []
        self._is_running = False
        # Convert agent card to dict following Coffee AGNTCY pattern
        self.agent_card = AGENT_CARD.model_dump(mode="json", exclude_none=True)
        
        # Agent endpoints for direct A2A calls
        self.sentiment_analyst_endpoint = os.getenv("SENTIMENT_ANALYST_URL", "http://sentiment-analyst:9002")
        self.fact_checker_endpoint = os.getenv("FACT_CHECKER_URL", "http://fact-checker:9004")
        
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
        """Process a single tweet by calling agents directly via A2A."""
        crisis_id = tweet.get("id", "unknown")
        
        logger.info(f"Processing crisis: {crisis_id} from {tweet['author']}")
        
        # Call agents directly via A2A (no SLIM broadcasting)
        await self._call_agents_directly(tweet, crisis_id)
        
    async def _publish_completion(self) -> None:
        """Log stream completion (no SLIM broadcasting)."""
        logger.info("All crisis tweets have been processed - no broadcasts sent")
            
    async def _call_agents_directly(self, tweet: Dict[str, Any], crisis_id: str) -> None:
        """Call sentiment analyst and fact checker agents directly via A2A."""
        try:
            # Prepare crisis data for analysis
            crisis_data = {
                "crisis_id": crisis_id,
                "text": tweet.get("text", ""),
                "content": tweet.get("text", ""),  # Fallback field name
                "author": tweet.get("author", ""),
                "timestamp": tweet.get("timestamp", ""),
                "source": "social_media",
                "platform": "twitter"
            }
            
            # Create tasks to call both agents in parallel
            tasks = []
            
            # Call sentiment analyst
            sentiment_task = asyncio.create_task(
                self._call_sentiment_analyst(crisis_data)
            )
            tasks.append(sentiment_task)
            
            # Call fact checker
            fact_checker_task = asyncio.create_task(
                self._call_fact_checker(crisis_data)
            )
            tasks.append(fact_checker_task)
            
            # Wait for all agent calls to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Log results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Agent call {i} failed: {result}")
                else:
                    logger.info(f"Agent call {i} completed successfully")
                    
        except Exception as e:
            logger.error(f"Error calling agents directly: {e}")
    
    async def _call_sentiment_analyst(self, crisis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Call the sentiment analyst agent directly via A2A following lungo pattern."""
        try:
            # Simple prompt with crisis content (following lungo pattern)
            prompt = f"Please analyze the sentiment of this crisis content: {crisis_data['text']}"
            
            # JSON-RPC request payload for A2A communication
            request_payload = {
                "jsonrpc": "2.0",
                "method": "message/send",
                "params": {
                    "message": {
                        "messageId": f"crisis-{crisis_data['crisis_id']}-sentiment",
                        "role": "user",
                        "parts": [
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                },
                "id": 1
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.sentiment_analyst_endpoint}/",
                    json=request_payload,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Sentiment analyst called successfully for crisis {crisis_data['crisis_id']}")
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"Sentiment analyst call failed: {response.status} - {error_text}")
                        return {"error": f"HTTP {response.status}: {error_text}"}
                        
        except asyncio.TimeoutError:
            logger.error("Sentiment analyst call timed out")
            return {"error": "Request timed out"}
        except Exception as e:
            logger.error(f"Error calling sentiment analyst: {e}")
            return {"error": str(e)}
    
    async def _call_fact_checker(self, crisis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Call the fact checker agent directly via A2A following lungo pattern."""
        try:
            # Simple prompt with crisis content for fact checking
            prompt = f"Please verify the claims in this crisis content: {crisis_data['text']}"
            
            # JSON-RPC request payload for A2A communication
            request_payload = {
                "jsonrpc": "2.0",
                "method": "message/send",
                "params": {
                    "message": {
                        "messageId": f"crisis-{crisis_data['crisis_id']}-factcheck",
                        "role": "user",
                        "parts": [
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                },
                "id": 1
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.fact_checker_endpoint}/",
                    json=request_payload,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Fact checker called successfully for crisis {crisis_data['crisis_id']}")
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"Fact checker call failed: {response.status} - {error_text}")
                        return {"error": f"HTTP {response.status}: {error_text}"}
                        
        except asyncio.TimeoutError:
            logger.error("Fact checker call timed out")
            return {"error": "Request timed out"}
        except Exception as e:
            logger.error(f"Error calling fact checker: {e}")
            return {"error": str(e)}
    
    def stop(self) -> None:
        """Stop the streaming service."""
        self._is_running = False
        logger.info("Tweet streaming service stopped")